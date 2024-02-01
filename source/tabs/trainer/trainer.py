import os
import glob
import PIL.Image
import math
import json
import difflib
import numpy as np

from parameters import VariantMap
from misc import encodeImage

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QPointF, QThread
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterUncreatableType

def constant_schedule(current_step, total_steps, warmup):
    warmup_steps = total_steps * warmup
    if current_step < warmup_steps:
        return float(current_step) / float(max(1.0, warmup_steps))
    return 1.0

def linear_schedule(current_step, total_steps, warmup):
    warmup_steps = total_steps * warmup
    if current_step < warmup_steps:
        return float(current_step) / float(max(1, warmup_steps))
    return max(0.0, float(total_steps - current_step) / float(max(1, total_steps - warmup_steps)))

def cosine_schedule(current_step, total_steps, restarts, warmup):
    warmup_steps = total_steps * warmup
    if current_step < warmup_steps:
        return float(current_step) / float(max(1, warmup_steps))
    progress = float(current_step - warmup_steps) / float(max(1, total_steps - warmup_steps))
    if progress >= 1.0:
        return 0.0
    return max(0.0, 0.5 * (1.0 + math.cos(math.pi * ((float(restarts) * progress) % 1.0))))

def rdp(points, epsilon):
    d_max = -1.0
    index = 0
    last = len(points) - 1
    p1 = points[0]
    p2 = points[last]
    x21 = p2[0] - p1[0]
    y21 = p2[1] - p1[1]
    
    for i, p in enumerate(points[1:last]):
        d = abs(y21*p[0] - x21*p[1] + p2[0]*p1[1] - p2[1]*p1[0])
        if d > d_max:
            index = i + 1
            d_max = d
            
    if d_max > epsilon:
        return rdp(points[:index+1], epsilon) + rdp(points[index:], epsilon)[1:]
    
    return [points[0], points[last]]

def format_float(x, p=2):
    return format(x, f'.{p}f').rstrip('0').rstrip('.')

def format_timestamp(seconds):
    minutes = int(seconds//60)
    seconds = int(seconds%60)
    return f"{minutes:02d}:{seconds:02d}"

class DatasetUploader(QThread):
    def __init__(self, trainer, request, pairs):
        super().__init__()
        self.trainer = trainer
        self.gui = trainer.gui
        self.request = request
        self.pairs = pairs
        self.image_size = request["data"]["image_size"]
        self.pending = 0
        self.stopping = False

    def run(self):
        for i, (img, prompt) in enumerate(self.pairs):
            img = PIL.Image.open(img)
            img.thumbnail((self.image_size, self.image_size), PIL.Image.Resampling.LANCZOS)
            request = {
                "type": "train_upload",
                "data": {
                    "image": [encodeImage(img)],
                    "prompt": [prompt],
                    "index": i
                }
            }
            self.gui.makeRequest(request)
            self.pending += 1
            while self.pending > 10 and not self.stopping:
                QThread.msleep(10)
            if self.stopping:
                return
            
        while self.pending > 0 and not self.stopping:
            QThread.msleep(10)
        if self.stopping:
            return
        
        self.trainer._id = self.gui.makeRequest(self.request)

    @pyqtSlot()
    def completed(self):
        self.pending -= 1

    @pyqtSlot()
    def stop(self):
        self.stopping = True

class Trainer(QObject):
    updated = pyqtSignal()
    imageChanged = pyqtSignal()
    folderChanged = pyqtSignal()
    foldersChanged = pyqtSignal()
    chartChanged = pyqtSignal()
    statusChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.name = "Train"
        self.gui = parent
        self.hidden = True

        self._default = {
            "type": "LoRA",
            "types": ["LoRA", "LoCon"],
            "name": "",
            "lora_rank": 32,
            "lora_alpha": 16,
            "lora_conv_rank": 16,
            "lora_conv_alpha": 8,
            "base_model": "",
            "clip_skip": 1,
            "steps": 5000,
            "optimizer": "AdamW",
            "optimizers": ["AdamW"],
            "learning_rate": 0.0001,
            "learning_schedule": "Cosine",
            "learning_schedules": ["Constant", "Linear", "Cosine"],
            "restarts": 2,
            "warmup": 0.1,
            "image_size": 512,
            "batch_size": 4,
            "shuffle": "Enabled",
            "prediction_type": "Epsilon",
            "prediction_types": ["Epsilon", "V"],
            "attention": "Default",
            "attentions": ["Default", "Efficient", "Math"],
            "enabled_disabled": ["Enabled", "Disabled"]
        }
        self._read_only = ["types", "optimizers", "learning_schedules", "prediction_types", "attentions", "enabled_disabled"]
        self._parameters = VariantMap(self, self._default.copy(), strict=True)
        self._parameters.updated.connect(self.parametersUpdated)

        self.reset()

        qmlRegisterSingletonType(Trainer, "gui", 1, 0, "TRAINER", lambda qml, js: self)
        self.gui.optionsUpdated.connect(self.optionsUpdated)
        self.gui.response.connect(self.onResponse)

    @pyqtProperty(VariantMap, notify=updated)
    def parameters(self):
        return self._parameters
    
    @pyqtSlot()
    def reset(self):
        for k, v in self._default.items():
            if not k in self._read_only:
                self._parameters.set(k, v)
        self.optionsUpdated()

        self._folders = []
        self._images = {}
        self._prompts = {}
        self._prompt_files = {}
        self._sizes = {}

        self._opened_folder = ""
        self._opened_images = {}

        self.resetCurrent()

    def resetCurrent(self):
        self._id = None
        self.uploader = None

        self._total = 0
        self._loss = []
        self._loss_plot = []
        self._epoch = 0
        self._epoch_marks = []

        self._progress = 0
        self._stage_label = "Idle"
        self._progress_label = "- / -"
        self._remaining_label = "-:- | -:-"

        self._lr_current = None
        self._lr_control = False
        self._loss_current_position = None
        self._loss_current_point = None
        self._loss_current_value = None
        self._loss_control = False

        self.updated.emit()
        self.imageChanged.emit()
        self.folderChanged.emit()
        self.foldersChanged.emit()
        self.chartChanged.emit()
        self.statusChanged.emit()

    def getGenerateParameters(self):
        basic = [t for t in self.gui.tabs if t.name == "Generate"][0]
        return basic._parameters
    
    @pyqtSlot()
    def optionsUpdated(self):
        available = self.gui._options.get("UNET", [])
        current = self._parameters.get("base_model")

        if not available and current:
            self._parameters.set("base_model", "")
        if available and not current:
            self._parameters.set("base_model", available[0])

    @pyqtSlot(str)
    def parametersUpdated(self, key):
        if key in {"learning_rate", "learning_schedule", "restarts", "warmup"}:
            self.chartChanged.emit()

    @pyqtProperty(list, notify=foldersChanged)
    def folders(self):
        return self._folders
    
    @pyqtSlot(str, result=list)
    def images(self, folder):
        if not folder in self._images:
            return []
        return self._images[folder]
    
    @pyqtProperty(str, notify=folderChanged)
    def currentFolder(self):
        return self._opened_folder
    
    @currentFolder.setter
    def currentFolder(self, folder):
        if self._opened_folder == folder:
            return
        self._opened_folder = folder
        self.folderChanged.emit()
        self.imageChanged.emit()

    @pyqtProperty(list, notify=folderChanged)
    def currentImages(self):
        if not self._opened_folder in self._images:
            return []
        return self._images[self._opened_folder]
    
    @pyqtProperty(str, notify=imageChanged)
    def currentImage(self):
        if not self._opened_folder in self._opened_images:
            return ""
        return self._opened_images[self._opened_folder]
    
    @currentImage.setter
    def currentImage(self, image):
        if self._opened_images[self._opened_folder] == image:
            return
        self._opened_images[self._opened_folder] = image
        self.imageChanged.emit()
    
    @pyqtProperty(int, notify=imageChanged)
    def currentImageWidth(self):
        current = self.currentImage 
        if not current in self._sizes:
            return 0
        return self._sizes[current][0]
    
    @pyqtProperty(int, notify=imageChanged)
    def currentImageHeight(self):
        current = self.currentImage
        if not current in self._sizes:
            return 0
        return self._sizes[current][1]
    
    @pyqtProperty(str, notify=imageChanged)
    def currentPrompt(self):
        current = self.currentImage
        if not current in self._prompts:
            return ""
        return self._prompts[current]
    
    @pyqtSlot(QUrl)
    def addFolder(self, folder):
        if type(folder) == QUrl:
            folder = folder.toLocalFile()
        
        for e in ["png", "jpg", "jpeg"]:
            for file in glob.glob(os.path.join(folder, "*."+e)):
                try:
                    with PIL.Image.open(file) as img:
                        w,h = img.size
                except:
                    pass
                
                possible = [
                    file + ".txt",
                    file.rsplit(".",1)[0] + ".txt"
                ]
                
                for text_file in possible:
                    if os.path.exists(text_file):
                        with open(text_file, "r") as f:
                            self._prompt_files[file] = text_file
                            self._prompts[file] = f.read()
                            break
                else:
                    self._prompt_files[file] = ""
                    self._prompts[file] = ""

                if not folder in self._folders:
                    self._folders += [folder]
                    self._images[folder] = []
                    self._opened_images[folder] = file

                self._images[folder] += [file]
                self._sizes[file] = (w,h)

        if not self._opened_folder and folder in self._folders:
            self.currentFolder = folder

        self.foldersChanged.emit()

    @pyqtSlot()
    def deleteFolder(self):
        folder = self.currentFolder
        files = self._images[folder]
        for file in files:
            del self._sizes[file]
            del self._prompt_files[file]
            del self._prompts[file]
        del self._images[folder]
        del self._opened_images[folder]

        idx = self._folders.index(folder)
        self._folders.remove(folder)

        if self._folders:
            idx = min(len(self._folders)-1, max(0, idx-1))
            self.currentFolder = self._folders[idx]
        else:
            self.currentFolder = ""
        
        self.foldersChanged.emit()
    
    def buildConfig(self):
        parameters = {k:v for k,v in self._parameters._map.items() if not k in self._read_only}
        parameters["base_model"] = self.gui.modelName(parameters["base_model"])
        
        config = {
            "parameters": parameters,
            "folders": self._folders
        }

        return config

    @pyqtSlot(QUrl)
    def saveConfig(self, file):
        file = file.toLocalFile()
        config = self.buildConfig()

        try:
            with open(file, 'w', encoding="utf-8") as f:
                json.dump(config, f, indent=4)
        except Exception:
            return
        
    @pyqtSlot(QUrl)
    def loadConfig(self, file):
        file = file.toLocalFile()
        config = {}

        try:
            if file.endswith(".json"):
                try:
                    with open(file, 'r', encoding="utf-8") as f:
                        config = json.load(f)
                except:
                    return
            
            for k,v in config["parameters"].items():
                if k == "base_model":
                    v = self.closestModel(v)
                self._parameters.set(k, v)

            for f in config["folders"]:
                self.addFolder(f)
        except:
            return
        
    def closestModel(self, name):
        models = self.gui._options.get("UNET", [])

        if not models:
            return ''
        
        name = name.lower()
        best = models[0]
        score = 0

        for m in models:
            m_name = self.gui.modelName(m).lower()
            m_score = difflib.SequenceMatcher(a=m_name, b=name).ratio()
            if m_score > score:
                best = m
                score = m_score
        
        return best

    def getLearningRatePoint(self, x, steps, schedule, warmup, restarts=None):
        if schedule == "Constant":
            y = constant_schedule(x, steps, warmup)
        elif schedule == "Linear":
            y = linear_schedule(x, steps, warmup)
        elif schedule == "Cosine":
            y = cosine_schedule(x, steps, restarts, warmup)
        return QPointF(x/steps, y)


    @pyqtProperty(list, notify=chartChanged)
    def learningRatePoints(self):
        points = []

        schedule = self._parameters.get("learning_schedule")
        restarts = self._parameters.get("restarts")
        warmup = self._parameters.get("warmup")

        steps = 200

        for x in range(steps):
            p = self.getLearningRatePoint(x, steps, schedule, warmup, restarts)
            points += [p]

        return points
    
    @pyqtProperty(str, notify=statusChanged)
    def learningRateMax(self):
        return format_float(self._parameters.get("learning_rate"), 5)
    
    @pyqtProperty(str, notify=statusChanged)
    def learningRateMin(self):
        return format_float(0.0, 5)
    
    @pyqtProperty(str, notify=statusChanged)
    def learningRateCurrentValue(self):
        if self._lr_current:
            return format_float(self._lr_current.y() * self._parameters.get("learning_rate"), 7)
        return "-"

    @pyqtProperty(QPointF, notify=statusChanged)
    def learningRateCurrentPoint(self):
        if self._lr_current:
            return self._lr_current
        return QPointF(0,0)
    
    @pyqtSlot(float)
    def setLearningRateCurrent(self, position):
        schedule = self._parameters.get("learning_schedule")
        restarts = self._parameters.get("restarts")
        warmup = self._parameters.get("warmup")

        steps = self._total or 200

        if position >= 0:
            x = int(position * steps)
            self._lr_control = True
        else:
            x = int(self.trainingProgress * steps)
            self._lr_control = False
        
        self._lr_current = self.getLearningRatePoint(x, steps, schedule, warmup, restarts)
        self.statusChanged.emit()
    
    def getLossFactors(self):
        if self._loss_plot:
            xm = max([x for x,y in self._loss_plot]) or 1
            yy = sorted([y for x,y in self._loss_plot])
            ys, ym = 1.1*(max(yy)-min(yy)), sum(yy)/len(yy)
            return xm, ys or 1, ym
        return 1, 1, 0

    @pyqtProperty(list, notify=chartChanged)
    def lossPoints(self):
        points = []

        if self._loss_plot:
            xm, ys, ym = self.getLossFactors()
            for x, y in self._loss_plot:
                points += [QPointF(x/xm, (y-ym)/(ys or 1) + 0.5)]

        return points
    
    @pyqtProperty(str, notify=statusChanged)
    def lossMax(self):
        if not self._loss:
            return "-"
        return format_float(max(self._loss), 4)
    
    @pyqtProperty(str, notify=statusChanged)
    def lossMin(self):
        if not self._loss:
            return "-"
        return format_float(min(self._loss), 4)
    
    @pyqtProperty(str, notify=statusChanged)
    def lossCurrentValue(self):
        if not self._loss or not self._loss_current_value:
            return "-"
        return format_float(self._loss_current_value, 4)

    @pyqtProperty(QPointF, notify=statusChanged)
    def lossCurrentPoint(self):
        if not self._loss or not self._loss_current_point:
            return QPointF(0,0)
        return self._loss_current_point
    
    @pyqtSlot(float)
    def setLossCurrent(self, position):
        if not self._loss:
            return
        
        xm, ys, ym = self.getLossFactors()

        if position >= 0:
            x = int(position * (len(self._loss)-1))
            y = self._loss[x]
            self._loss_current_point = QPointF(x/xm, (y-ym)/(ys or 1) + 0.5)
            self._loss_current_position = position
            self._loss_control = True
        else:
            x = (len(self._loss)-1)
            y = self._loss[x]
            self._loss_current_position = 1.0
            self._loss_control = False
        
        self._loss_current_value = y
        self._loss_current_point = QPointF(x/xm, (y-ym)/(ys or 1) + 0.5)

        self.statusChanged.emit()
    
    @pyqtProperty(list, notify=statusChanged)
    def epochMarks(self):
        return self._epoch_marks

    @pyqtProperty(float, notify=statusChanged)
    def trainingProgress(self):
        if self._stage_label == "Training":
            return self._progress
        return 0.0
    
    @pyqtProperty(float, notify=statusChanged)
    def progress(self):
        return self._progress
    
    @pyqtProperty(str, notify=statusChanged)
    def progressLabel(self):
        return self._progress_label
    
    @pyqtProperty(str, notify=statusChanged)
    def remainingLabel(self):
        return self._remaining_label
    
    @pyqtProperty(str, notify=statusChanged)
    def stageLabel(self):
        return self._stage_label

    @pyqtSlot()
    def train(self):
        self.resetCurrent()

        data = {k:v for k,v in self._parameters._map.items() if not k in self._read_only}
        data["folders"] = self._folders

        parameters = self.getGenerateParameters()
        data["device"] = parameters._values.get("device")

        data["shuffle"] = data["shuffle"] == "Enabled"

        request = {"type":"train_lora", "data": data}

        if self.gui.isRemote:
            del request["data"]["folders"]
            pairs = []
            for folder in self._folders:
                for file in self._images[folder]:
                    prompt = self._prompts.get(file, "")
                    pairs += [(file, prompt)]
            self.uploader = DatasetUploader(self, request, pairs)
            self.uploader.start()
            self._stage_label = "Uploading"
            self._total = len(pairs)
            self._progress_label = f"0 / {self._total}"
        else:
            self._id = self.gui.makeRequest(request)
            self._stage_label = "Preparing"
        self.statusChanged.emit()
    
    def computePlot(self, points, required):
        SCALE = 100
        if len(points) > required:
            points = [(x*SCALE, y) for x,y in points]
            points = rdp(points, 1)
            points = [(x/SCALE, y) for x,y in points]
        return points

    def updateProgress(self, data):
        stage = data["stage"]
        current = data["current"]
        total = data["total"]

        elapsed = data["elapsed"]
        remaining = data["remaining"]
        rate = data["rate"]

        self._progress = (current) / total
        self._stage_label = stage
        self._progress_label = f"{current} / {total}"
        self._remaining_label = f"{format_timestamp(elapsed)} | {format_timestamp(remaining)}"

        if stage == "Training":
            epoch = data["epoch"]
            losses = data["losses"]
            if not self._loss:
                self._total = total
                self._epoch = epoch
                self._loss = []

                epoch_length = epoch/total
                self._epoch_marks = [x*epoch_length for x in range(math.ceil(total/epoch))]

            self._loss += losses
            self._loss_plot = self.computePlot([(x, y) for x, y in enumerate(self._loss)], 50)

            if not self._lr_control:
                self.setLearningRateCurrent(-1)
            if not self._loss_control:
                self.setLossCurrent(-1)
            else:
                self.setLossCurrent(self._loss_current_position)
            
            self.chartChanged.emit()
        
        self.statusChanged.emit()

    @pyqtSlot(int, object)
    def onResponse(self, id, response):
        type = response.get("type", "")
        data = response.get("data", {})

        if type == "training_status":
            self._stage_label = data["message"]
            self.statusChanged.emit()

        if type == "training_progress":
            self.updateProgress(data)

        if type == "training_upload":
            if self.uploader:
                self.uploader.completed()
                self._progress = (data['index']+1) / self._total
                self._progress_label = f"{data['index']+1} / {self._total}"
                if self._progress == 1:
                    self._progress = 0
                    self._stage_label = "Preparing"
                    self._progress_label = f"- / -"
                self.statusChanged.emit()

        if id == self._id and type in {"aborted", "errored"}:
            self.resetCurrent()
            if self.uploader:
                self.uploader.stop()

    @pyqtSlot()
    def stop(self):
        if self._id:
            self.gui.makeRequest({"type":"cancel", "data":{"id": self._id}})