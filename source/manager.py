import os
import time
import datetime
import io
import PIL.Image
import random
import re
import threading

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QSize, QRect, QRectF, QCoreApplication
from PyQt5.QtGui import QImage, QPainter, QColor, QFont, QTextOption
from PyQt5.QtQml import qmlRegisterUncreatableType

import parameters
from misc import encodeImage, decodeImage
from tabs.basic.basic_input import BasicInputRole

def writeLog(line):
    with open("saving.log", "a", encoding='utf-8') as log:
        log.write(line)

class OutputWriterSignals(QObject):
    done = pyqtSignal(str)

class OutputWriter(threading.Thread):
    def __init__(self, img, metadata, outputs, folder, log=False):
        super().__init__()
        self.signals = OutputWriterSignals()
        self.log = log

        if self.log: writeLog(f"START {datetime.datetime.now()}\n")

        m = PIL.PngImagePlugin.PngInfo()
        if metadata:
            m.add_text("parameters", parameters.formatParameters(metadata))
            recipe = parameters.formatRecipe(metadata)
            if recipe:
                m.add_text("recipe", recipe)

        if self.log: writeLog(f"METADATA\n")

        self.img = img.copy()
        self.metadata = m

        folder = os.path.join(outputs, folder)
        os.makedirs(folder, exist_ok=True)

        idx = parameters.getIndex(folder)
        filename = f"{idx:08d}-" + datetime.datetime.now().strftime("%m%d%H%M")
        
        self.tmp = os.path.join(folder, f"{filename}.tmp")
        self.file = os.path.join(folder, f"{filename}.png")
        
        if self.log: writeLog(f"FILE {self.file}\n")

        open(self.tmp, 'a').close()

        if self.log: writeLog(f"TMP\n")
        
    def run(self):
        if type(self.img) == QImage:
            if self.log: writeLog(f"ENCODE 1\n")
            self.img = encodeImage(self.img)

        if type(self.img) == bytes:
            if self.log: writeLog(f"ENCODE 2\n")
            self.img = PIL.Image.open(io.BytesIO(self.img))

        if self.log: writeLog(f"SAVE\n")

        self.img.save(self.tmp, format="PNG", pnginfo=self.metadata)

        if self.log: writeLog(f"REPLACE\n")
        os.replace(self.tmp, self.file)
        self.signals.done.emit(self.file)

def writeImage(img, metadata, outputs, folder):

    writeLog(f"START {datetime.datetime.now()}\n")

    m = PIL.PngImagePlugin.PngInfo()
    if metadata:
        m.add_text("parameters", parameters.formatParameters(metadata))
        recipe = parameters.formatRecipe(metadata)
        if recipe:
            m.add_text("recipe", recipe)

    writeLog(f"METADATA\n")

    folder = os.path.join(outputs, folder)
    os.makedirs(folder, exist_ok=True)

    idx = parameters.getIndex(folder)
    filename = f"{idx:08d}-" + datetime.datetime.now().strftime("%m%d%H%M")
    tmp = os.path.join(folder, f"{filename}.tmp")
    file = os.path.join(folder, f"{filename}.png")

    writeLog(f"FILE {file}\n")

    if type(img) == QImage:
        writeLog(f"ENCODE 1\n")
        img = encodeImage(img)

    if type(img) == bytes:
        writeLog(f"ENCODE 2\n")
        img = PIL.Image.open(io.BytesIO(img))

    writeLog(f"SAVE\n")
    
    img.save(tmp, format="PNG", pnginfo=m)

    writeLog(f"REPLACE\n")

    os.replace(tmp, file)

    writeLog("DONE\n")

    return file

class BuilderRunnable(threading.Thread):
    def __init__(self, manager, inputs):
        super().__init__()
        self.manager = manager
        self.inputs = inputs
        self.results = None
        self.done = False
        self.daemon = True
    
    def run(self):
        self.results = self.manager.parseInputs(self.inputs)
        self.done = True

class RequestManager(QObject):
    updated = pyqtSignal()
    artifact = pyqtSignal(int, QImage, str)
    result = pyqtSignal(int, QImage, object, str, bool)

    def __init__(self, parent=None, modifyRequest=None):
        super().__init__(parent)
        self.gui = parent
        self.parameters = None

        self.requests = []
        self.count = 0
        self.seed = 0
        
        self.ids = []
        self.mapping = {}

        self.annotations = {}

        self.folders = {}
        self.filenames = {}

        self.writers = {}

        self.monitoring = False

        self.modifyRequest = modifyRequest

        self.setGrid(None)

    def setGrid(self, grid, labels = []):
        self.grid = grid
        self.grid_size = None
        self.grid_ids = []
        self.grid_image = None
        self.grid_images = {}
        self.grid_id = None
        self.grid_labels = labels
        self.grid_metadata = None
        self.grid_save_all = False

    def setRequests(self, requests):
        if self.parameters:
            folder = self.parameters._values.get("output_folder")
            for i in range(len(requests)):
                if folder and not "folder" in requests[i]:
                    requests[i]["folder"] = folder

        self.requests = requests
        self.count = len(requests)
        self.updated.emit()

    def makeRequest(self, request=None):
        if not request:
            request = self.requests.pop()
            self.updated.emit()
        
        filename = self.finalizeRequest(request)

        folder = ""
        if "folder" in request:
            folder = request["folder"]
            del request["folder"]

        id = self.gui.makeRequest(request)

        self.folders[id] = folder or request["type"]
        self.filenames[id] = filename if folder else ""
        self.ids += [id]
        return id
    
    def makeAnnotationRequest(self, request, input_id):
        self.setGrid(None)
        id = self.makeRequest(request)
        self.annotations[id] = input_id

    def cancelRequest(self):
        self.setRequests([])
        if self.ids:
            self.gui.cancelRequest(self.ids.pop())
            return True
        return False

    def finalizeRequest(self, request):
        data = request["data"]
        filename = None
        for k in ["image", "mask", "cn_image", "area"]:
            for i in range(len(data.get(k, []))):
                if not data[k][i]:
                    continue
                if type(data[k][i]) == str:
                    if not filename:
                        filename = data[k][i]
                    data[k][i] = encodeImage(QImage(data[k][i]))
                elif type(data[k][i]) == list:
                    for j in range(len(data[k][i])):
                        if type(data[k][i][j]) == str:
                            if not filename:
                                filename = data[k][i][j]
                            data[k][i][j] = encodeImage(QImage(data[k][i][j]))
        if filename:
            filename = filename.rsplit(os.path.sep, 1)[-1].rsplit(".", 1)[0]

        return filename
    
    @pyqtProperty(int, notify=updated)
    def remaining(self):
        if self.count > 1:
            return len(self.requests) + 1
        return 0
    
    def parseInputs(self, inputs):
        found = {}
        links = {}
        controls = {}

        segmentation = []
        
        if inputs:
            for i in inputs:
                data = []
                if i._role == BasicInputRole.IMAGE:
                    if i._image and not i._image.isNull():
                        data += [encodeImage(i._originalCrop or i._original)]
                    if i._files:
                        for f in i._files[::-1]:
                            data += [i.getFilePath(f)]
                    if data:
                        found[i] = data
                if i._role == BasicInputRole.MASK or (i._role == BasicInputRole.CONTROL and i._control_mode == "Inpaint"):
                    if i._linked:
                        links[i] = i._linked
                        if i._image and not i._image.isNull():
                            data += [encodeImage(i._image)]
                        if i._files:
                            for f in i._files[::-1]:
                                data += [i.getFilePath(f)]
                        if data:
                            found[i] = data
                            data = []
                if i._role == BasicInputRole.SUBPROMPT:
                    if i._linked:
                        links[i] = i._linked
                    if i._image and not i._image.isNull():
                        data += [[encodeImage(a) for a in i.getAreas()]]
                    if data:
                        found[i] = data
                if i._role == BasicInputRole.CONTROL:
                    model = i._control_settings.get("mode")
                    opts = {
                        "scale": i._control_settings.get("strength"),
                        "annotator": i._control_settings.get("preprocessor"),
                        "args": i.getControlArgs(),
                        "guess": i.getControlGuess()
                    }
                    k = i
                    if model == "Inpaint" and i._linked:
                        k = i._linked
                    if k._image and not k._image.isNull():
                        data += [(model, opts, encodeImage(k._image or k._original))]
                    if k._files:
                        for f in k._files[::-1]:
                            data += [(model, opts, k.getFilePath(f))]
                    if data:
                        controls[i] = data
                if i._role == BasicInputRole.SEGMENTATION:
                    opts = i.getSegmentationArgs()
                    if i._image and not i._image.isNull():
                        data += [(encodeImage(i._originalCrop or i._original), opts)]
                    if i._files:
                        for f in i._files[::-1]:
                            data += [(i.getFilePath(f), opts)]
                    if data:
                        segmentation += data

        return found, links, controls, segmentation
    
    def buildRequests(self, parameters, inputs):
        self.parameters = parameters

        builder = BuilderRunnable(self, inputs)
        builder.start()

        while not builder.done:
            QCoreApplication.processEvents()
            time.sleep(1/60)

        found, links, controls, segmentation = builder.results
        
        self.setGrid(None)

        if segmentation:
            requests = self.buildSegmentationRequests(segmentation)
        else:
            batches = self.buildBatches(found, links, controls)
            requests = self.buildStandardRequests(batches)

        if self.modifyRequest:
            for i in range(len(requests)):
                requests[i] = self.modifyRequest(requests[i])

        self.setRequests(requests)
            
    def buildSegmentationRequests(self, segmentation):
        requests = []
        for img, opts in segmentation:
            request = {
                "type": "segmentation",
                "data": {
                    "image": [img],
                    "seg_opts": [opts],
                    "device": self.parameters._values.get("device")
                }
            }
            requests += [request]
        
        return requests

    def buildBatches(self, found, links, controls, single=False):
        images, masks, areas = [], [], []
        used = []
        for k in found:
            if k in used:
                continue
            linked = [k] + [i for i in links if links[i] == k]
            size = max([len(found[i]) for i in linked])
            for z in range(size):
                img, msk, are = None, None, []
                for j in linked:
                    data = found[j][z % len(found[j])]
                    if j._role == BasicInputRole.IMAGE:
                        img = data
                    if j._role == BasicInputRole.MASK or (j._role == BasicInputRole.CONTROL and j._control_mode == "Inpaint"):
                        msk = data
                    if j._role == BasicInputRole.SUBPROMPT:
                        are = data
                if msk and not img:
                    continue
                images += [img]
                masks += [msk]
                areas += [are]
            used += linked

        batch_size = int(self.parameters._values.get("batch_size"))
        batch_count = int(self.parameters._values.get("batch_count"))

        total = max([len(controls[k]) for k in controls]) if controls else 0
        total = max(len(images), batch_count * batch_size, total)

        if single:
            batch_size = 1
            batch_count = 1
            total = 1

        def get_portion(data, start, amount):
            if not data:
                return []
            out = []
            for i in range(amount):
                out += [data[(start+i)%len(data)]]
            return out

        i = 0
        ci = 0

        batches = []
        while total > 0:
            size = min(total, batch_size)
            batch_images = get_portion(images, i, size)
            batch_masks = get_portion(masks, i, size)
            batch_areas = get_portion(areas, i, size)
            batch_control = [controls[k][ci%len(controls[k])] for k in controls]

            if any([b == None for b in batch_images]):
                batch_images, batch_masks = [], []

            i += batch_size
            total -= batch_size
            ci += 1
            
            batches += [(size, batch_images, batch_masks, batch_areas, batch_control)]
        
        return batches

    def buildStandardRequests(self, batches):
        requests = []

        seed = int(self.parameters._values.get("seed"))
        subseed = int(self.parameters._values.get("subseed"))
        if seed == -1:
            seed = random.randrange(2147483646)
        if subseed == -1:
            subseed = random.randrange(2147483646)

        for size, images, masks, areas, control in batches:
            request = self.parameters.buildRequest(size, seed, images, masks, areas, control)

            if "seed" in request["data"]:
                request["data"]["seed"] = seed
                seed += size

            if "subseed" in request["data"]:
                request["data"]["subseed"] = subseed
                subseed += size
                        
            requests += [request]

        return requests

    def buildGridRequests(self, parameters, inputs, grid):
        self.parameters = parameters

        found, links, controls, _ = self.parseInputs(inputs)
        base = self.buildBatches(found, links, controls, single=True)[0]

        (lx, x), (ly, y) = grid
        grid = [x, y]
        labels = [lx, ly]
        self.setGrid(grid, labels)

        self.grid_save_all = self.gui.config.get("grid_save_all")

        requests = []
        
        seed = int(parameters._values.get("seed"))
        subseed = int(parameters._values.get("subseed"))
        if seed == -1:
            seed = random.randrange(2147483646)
        if subseed == -1:
            subseed = random.randrange(2147483646)

        for iy in y:
            for ix in x:
                elementParams = parameters.copy()
                elementParams._values.set("seed", seed)
                elementParams._values.set("subseed", subseed)

                prompts = {k:parameters._values.get(k) for k in ["prompt", "negative_prompt"]}

                modifyParams = {}
                for k, v in list(ix.items()) + list(iy.items()):
                    if k == "modify":
                        for kk, vv in v.items():
                            modifyParams[kk] = vv
                    elif k == "replace":
                        match, string = v
                        for t in {"prompt", "negative_prompt"}:
                            if match:
                                prompts[t] = re.sub(match, string, prompts[t])
                            elif t == "prompt":
                                prompts[t] = string
                            elementParams._values.set(t, prompts[t])
                    else:
                        elementParams._values.set(k, v)

                
                size, b_i, b_m, b_a, b_c = base
                sd = int(elementParams._values.get("seed"))

                request = elementParams.buildRequest(size, sd, b_i, b_m, b_a, b_c)
                if self.modifyRequest:
                    request = self.modifyRequest(request, modifyParams)

                requests += [request]

        data = requests[0]["data"]
        w, h, factor = data["width"], data["height"], data.get("hr_factor",1)

        if requests[0]["type"] == "img2img" and "mask" in requests[0]["data"]:
            img = decodeImage(requests[0]["data"]["image"][0])
            self.grid_size = (img.width(), img.height())
        else:
            self.grid_size = (int(w*factor), int(h*factor))

        if not parameters._values.get("output_folder"):
            for i in range(len(requests)):
                requests[i]["folder"] = "grid"

        self.setRequests(requests[::-1])

    def handleResult(self, id, name):
        if not id in self.ids:
            if not (self.monitoring and name == "result"):
                return

        if not self.requests and name == "result":
            self.count = 0
            self.updated.emit()

        if not id in self.mapping:
            self.mapping[id] = (time.time_ns() // 1000000) % (2**31 - 1)

        if self.grid != None:
            if self.grid_id == None:
                self.grid_id = id
            self.gridResult(id, self.mapping[self.grid_id], name)
        else:
            self.normalResult(id, self.mapping[id], name)

    def doSave(self, image, metadata, folder):
        if self.gui.debugMode() == 1:
            return writeImage(image, metadata, self.gui.outputDirectory(), folder)
        else:
            log = self.gui.debugMode() == 2
            writer = OutputWriter(image, metadata, self.gui.outputDirectory(), folder, log)
            writer.signals.done.connect(self.onSave)
            self.writers[writer.file] = writer
            writer.start()
            return writer.file

    @pyqtSlot(str)
    def onSave(self, file):
        if file in self.writers:
            del self.writers[file]

    def normalResult(self, id, out, name):
        if name == "preview":
            previews = self.gui._results[id]["preview"]
            out = self.mapping[id]
            for i in range(len(previews)-1, -1, -1):
                self.artifact.emit(out, previews[i], "preview")
                out += 1

        if name == "result":
            if id in self.ids:
                self.ids.remove(id)
            results = self.gui._results[id]["result"]
            metadata = self.gui._results[id].get("metadata", None)
            artifacts = {k:v for k,v in self.gui._results[id].items() if not k in {"result", "metadata", "preview"}}

            out = self.mapping[id]

            if id in self.annotations:
                self.artifact.emit(self.annotations[id], results[0], "Annotated")
                del self.annotations[id]
                return

            for i in range(len(results)-1, -1, -1):
                result = results[i]
                meta = metadata[i] if metadata else None

                folder = self.folders.get(id, "monitor")
                file = self.doSave(result, meta, folder)

                last = i==0

                self.result.emit(out, result, meta, file, last)

                for k, v in artifacts.items():
                    vv = v[i%len(v)]
                    if vv:
                        self.artifact.emit(out, vv, k)    

                out += 1

    def gridResult(self, id, out, name):
        available = self.gui._results[id]
        if "result" in available:
            images = available["result"]
        elif "preview" in available:
            images = available["preview"]
        else:
            return
        
        metadata = available.get("metadata", None)
        if "metadata" in available and not self.grid_metadata:
            self.grid_metadata = metadata[0]
        
        for i in range(len(images)-1, -1, -1):
            if not id + i in self.grid_ids:
                self.grid_ids += [id + i]
            self.grid_images[id + i] = images[i]

        x, y = self.grid
        lx, ly = self.grid_labels
        cx, cy = len(x) or 1, len(y) or 1

        w, h = self.grid_size

        pw, ph = 200, 60
        if cx == 1 and cy == 1:
            pw, ph = 0, 60
            if ly[0]:
                lx[0] = ly[0]
        elif cx == 1:
            pw, ph = 200, 0
        elif cy == 1:
            pw, ph = 0, 60

        font = QFont("Cantarell", 30)
        small_font = QFont("Cantarell", 20)
        tiny_font = QFont("Cantarell", 15)

        def drawText(painter, text, bound):
            if not text:
                return
            opt = QTextOption()
            opt.setAlignment(Qt.AlignCenter)
            opt.setWrapMode(QTextOption.WordWrap)
            
            painter.setFont(font)
            text_bound = painter.boundingRect(bound, text, opt)
            if not bound.contains(text_bound):
                painter.setFont(small_font)
                text_bound = painter.boundingRect(bound, text, opt)
                if not bound.contains(text_bound):
                    painter.setFont(tiny_font)
                    opt.setWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
            else:
                painter.setFont(font)
            painter.drawText(bound, text, opt)


        def drawLabel(painter, positions, labels):
            px, py = positions
            lx, ly = labels
            b = 1
            drawText(painter, lx, QRectF(px, 0, w, ph).adjusted(b,b,-b,-b))
            drawText(painter, ly, QRectF(0, py, pw, h).adjusted(b,b,-b,-b))

        positions = []
        labels = []
        for iy in range(cy):
            for ix in range(cx):
                positions += [(int(pw + ix*w), int(ph + iy*h))]
                labels += [(lx[ix], ly[iy] if ly else "")]

        if not self.grid_image:
            gw, gh = int(pw + w*cx), int(ph + h*cy)
            self.grid_image = QImage(QSize(gw, gh), QImage.Format_ARGB32_Premultiplied)
            self.grid_image.fill(QColor.fromRgb(255, 255, 255))

            painter = QPainter(self.grid_image)
            painter.setRenderHint(QPainter.TextAntialiasing, True)
            for i in range(len(positions)):
                drawLabel(painter, positions[i], labels[i])

            painter.end()

        painter = QPainter(self.grid_image)

        id = self.grid_ids[-1]
        image = self.grid_images[id]
        px, py = positions[len(self.grid_ids)-1]
        painter.drawImage(QRect(px,py,w,h), image)

        painter.end()

        if name == "result":
            if id in self.ids:
                self.ids.remove(id)

            if self.grid_save_all:
                folder = self.folders.get(self.grid_id, "grid")
                file = self.doSave(image, metadata[0], folder)

            if len(self.grid_ids) == cx*cy:
                folder = self.folders.get(self.grid_id, "grid")
                file = self.doSave(self.grid_image, self.grid_metadata, folder)
                self.result.emit(out, self.grid_image, self.grid_metadata, file, True)
            else:
                if self.requests:
                    self.makeRequest()
        else:
            self.artifact.emit(out, self.grid_image, "preview")

def registerTypes():
    qmlRegisterUncreatableType(RequestManager, "gui", 1, 0, "RequestManager", "Not a QML type")