from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QSize, QUrl, QMimeData, QByteArray, QThreadPool, Qt, QRect, QRunnable, QMutex
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtGui import QImage, QDrag, QPixmap, QColor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from enum import Enum

import parameters
import re
from misc import MimeData, SyntaxHighlighter, encode_image
from canvas.shared import PILtoQImage, QImagetoPIL, CanvasWrapper
from canvas.canvas import Canvas
import sql
import time
import io
import datetime
import math
import os

import PIL.Image
import PIL.PngImagePlugin

MIME_BASIC_INPUT = "application/x-qd-basic-input"
MIME_BASIC_DIVIDER = "application/x-qd-basic-divider"

SUGGESTION_BLOCK_REGEX = lambda spaces: r'(?=\n|,|(?<!lora|rnet):|\||\[|\]|\(|\)'+ ('|\s)' if spaces else r')')

class BasicInputRole(Enum):
    IMAGE = 1
    MASK = 2
    SUBPROMPT = 3
    CONTROL = 4

INPUT_ID = 1

class BasicInput(QObject):
    updated = pyqtSignal()
    linkedUpdated = pyqtSignal()
    extentUpdated = pyqtSignal()
    def __init__(self, basic, image=QImage(), role=BasicInputRole.IMAGE):
        global INPUT_ID
        super().__init__(basic)
        self.basic = basic
        self._original_crop = None
        self._original = image.copy()
        self._image = image
        self._role = role
        self._linked = None
        self._dragging = False
        self._extent = QRect()
        self._extentWarning = False
        self._mode = ""
        self._settings = parameters.VariantMap(self, {
            "mode": "", "CN_strength":1.0, "CN_preprocessors": [], "CN_preprocessor": "", "CN_bools": ["False", "True"],
            "CN_bool": "False", "CN_bool_label": "", "CN_slider_a": 0.0, "CN_slider_a_label": "", "CN_slider_b": 0.0, "CN_slider_b_label": ""
            })
        self._settings.updated.connect(self.onSettingsUpdated)
        self._id = INPUT_ID
        INPUT_ID += 1

        self._artifacts = {}
        self._artifactNames = []
        self._display = None

        self._areas = []

        self._offset = 0.5

        basic.parameters._values.updated.connect(self.updateImage)

    def updateImage(self):
        if self._image and not self._image.isNull():
            if self._linked and self._linked.image and not self._linked.image.isNull():
                bg = self._linked.image
                self.resizeImage(bg.size())
            else:
                if self._role == BasicInputRole.IMAGE and self.basic.hasMask(self):
                    self._image = self._original
                    self._original_crop = None
                else:
                    w,h = self.basic.parameters.values.get("width"),  self.basic.parameters.values.get("height")
                    self.resizeImage(QSize(int(w),int(h)))

        self.updateExtent()
        self.updated.emit()

    def resizeImage(self, out_z):
        in_z = self._original.size()
        
        ar = out_z.width()/out_z.height()

        rh = in_z.height()/out_z.height()
        rw = in_z.width()/out_z.width()

        w, h = in_z.width(), in_z.height()

        if out_z.width() * rh > in_z.width():
            h = math.ceil(w / ar)
        elif out_z.height() * rw > in_z.height():
            w = math.ceil(h * ar)

        dx = int((in_z.width()-w)*self._offset)
        dy = int((in_z.height()-h)*self._offset)
        self._original_crop = self._original.copy(dx, dy, w, h)
        self._image = self._original_crop.scaled(out_z, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    @pyqtSlot(QUrl)
    def saveImage(self, file):
        file = file.toLocalFile()
        if not "." in file.rsplit(os.path.sep,1)[-1]:
            file = file + ".png"
        try:
            self.display.save(file)
        except Exception:
            pass

    def setLinked(self, linked):
        prevLinked = self._linked
        self._linked = linked
        if prevLinked:
            prevLinked.updated.disconnect(self.updateImage)
            prevLinked.updateLinked()
        if self._linked:
            self._linked.updated.connect(self.updateImage)
            self._linked.updateLinked()
        self.updateLinked()

    @pyqtSlot()
    def updateLinked(self):
        self.updateImage()
        self.linkedUpdated.emit()
    
    @pyqtProperty(int, notify=updated)
    def role(self):
        return self._role.value

    @role.setter
    def role(self, role):
        self._role = BasicInputRole(role)
        if self._role != BasicInputRole.CONTROL:
            self._settings.set("mode", "")
        self.updated.emit()
        self.parent().updated.emit()

    @pyqtProperty(QImage, notify=updated)
    def image(self):
        return self._image
    
    @pyqtProperty(int, notify=updated)
    def width(self):
        return self._image.width()
    
    @pyqtProperty(int, notify=updated)
    def height(self):
        return self._image.height()
    
    @pyqtProperty(float, notify=updated)
    def offset(self):
        return self._offset
    
    @offset.setter
    def offset(self, offset):
        #if self._role == BasicInputRole.IMAGE:
        self._offset = max(0.0, min(1.0, offset))
        self.updateImage()

    @pyqtProperty(bool, notify=updated)
    def offsetDirection(self):
        rw = self._image.width() / self._original.width()
        rh = self._image.height() / self._original.height()
        return rw > rh
    
    @pyqtProperty(int, notify=updated)
    def originalWidth(self):
        return self._original.width()
    
    @pyqtProperty(int, notify=updated)
    def originalHeight(self):
        return self._original.height()

    @pyqtProperty(bool, notify=updated)
    def empty(self):
        return self._image.isNull()

    @pyqtProperty(bool, notify=linkedUpdated)
    def linked(self):
        return self._linked != None
    
    @pyqtProperty(bool, notify=linkedUpdated)
    def linkedTo(self):
        i = self.basic._inputs.index(self) + 1
        if i >= len(self.basic._inputs):
            return False
        return self.basic._inputs[i]._linked != None

    @pyqtProperty(QImage, notify=linkedUpdated)
    def linkedImage(self):
        if not self._linked:
            return QImage()
        return self._linked._image
    
    @pyqtProperty(int, notify=linkedUpdated)
    def linkedWidth(self):
        if not self._linked or not self._linked._image.width():
            return int(self.basic.parameters.values.get("width"))
        return self._linked._image.width()
    
    @pyqtProperty(int, notify=linkedUpdated)
    def linkedHeight(self):
        if not self._linked or not self._linked._image.height():
            return int(self.basic.parameters.values.get("height"))
        return self._linked._image.height()
        
    @pyqtProperty(str, notify=updated)
    def size(self):
        if self._image.isNull():
            return ""
        o = self._original_crop or self._original
        return f"{o.width()}x{o.height()}"
    
    @pyqtProperty(QRect, notify=extentUpdated)
    def extent(self):
        return self._extent
    
    @pyqtProperty(bool, notify=extentUpdated)
    def extentWarning(self):
        return self._extentWarning
    
    @pyqtProperty(parameters.VariantMap, notify=updated)
    def settings(self):
        return self._settings
    
    @pyqtSlot(str)
    def onSettingsUpdated(self, key):
        if key == "mode":
            value = self._settings.get("mode")
            self._mode = value

            self._settings.set("CN_preprocessors", self.basic._parameters._values.get("CN_preprocessors"))
            self._settings.set("CN_preprocessor", value)

            if self._display:
                self.annotate()
            else:
                self.setArtifacts({})
            self.updated.emit()
            self.parent().updated.emit()
        if key == "CN_preprocessor":
            value = self._settings.get("CN_preprocessor")
            settings = {
                "CN_bool_label": "", "CN_slider_a_label": "", "CN_slider_b_label": ""
            }
            if value == "Canny":
                settings = {
                    "CN_bool_label": "",
                    "CN_slider_a": 0.4, "CN_slider_a_label": "Lower threshold",
                    "CN_slider_b": 0.8, "CN_slider_b_label": "Upper threshold"
                }
            if value == "Mlsd":
                settings = {
                    "CN_bool_label": "",
                    "CN_slider_a": 0.1, "CN_slider_a_label": "Score threshold",
                    "CN_slider_b": 0.1, "CN_slider_b_label": "Distance threshold"
                }
            if value == "Pose":
                settings = {
                    "CN_bool": "False", "CN_bool_label": "Hands and Face",
                    "CN_slider_a_label": "", "CN_slider_b_label": ""
                }
            for k,v in settings.items():
                self._settings.set(k,v)

    @pyqtProperty(str, notify=updated)
    def mode(self):
        return self._mode

    @pyqtSlot()
    def annotate(self):
        self.basic.annotate(self)

    def getCNArgs(self):
        args = []
        if self._settings.get("CN_slider_a_label"):
            args += [self._settings.get("CN_slider_a")]
        if self._settings.get("CN_slider_b_label"):
            args += [self._settings.get("CN_slider_b")]
        if self._settings.get("CN_bool_label"):
            args += [self._settings.get("CN_bool") == "True"]
        return args
    
    def setArtifacts(self, artifacts):
        self._artifacts = artifacts
        self._artifactNames = list(self._artifacts.keys())
        if self._artifactNames:
            self._display = self._artifactNames[-1]
        else:
            self._display = None
        self.updated.emit()
    
    @pyqtProperty(QImage, notify=updated)
    def display(self):
        if not self._display:
            return self._image
        return self._artifacts[self._display]
    
    @pyqtProperty(str, notify=updated)
    def displayName(self):
        return ["", "Image", "Mask", "Subprompts", "Control"][self._role.value]
    
    @pyqtProperty(str, notify=updated)
    def displayIndex(self):
        if not self._artifacts:
            return ""
        if not self._display:
            return f"1 of {len(self._artifactNames)+1}"
        else:
            idx = self._artifactNames.index(self._display)
            return f"{idx+2} of {len(self._artifactNames)+1}"

    @pyqtSlot()
    def nextDisplay(self):
        if not self._display:
            if self._artifactNames:
                self._display = self._artifactNames[0]
        else:
            idx = self._artifactNames.index(self._display) + 1
            if idx < len(self._artifactNames):
                self._display = self._artifactNames[idx]
            else:
                self._display = None
        self.updated.emit()
    
    @pyqtSlot()
    def prevDisplay(self):
        if not self._display:
            if self._artifactNames:
                self._display = self._artifactNames[-1]
        else:
            idx = self._artifactNames.index(self._display) - 1
            if idx >= 0:
                self._display = self._artifactNames[idx]
            else:
                self._display = None
        self.updated.emit()

    @pyqtSlot()
    def resetDisplay(self):
        self._display = None
        self.updated.emit()

    def checkAnnotation(self):
        if self._display and self._role == BasicInputRole.CONTROL:
            self.annotate()
        else:
            self.setArtifacts({})

    def getAreas(self):
        out = []
        for a in self._areas:
            size = self._image.size()
            a = a.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            dx = int((a.width()-size.width())*self._offset)
            dy = int((a.height()-size.height())*self._offset)
            a = a.copy(dx, dy, size.width(), size.height())
            out += [a]
        return out

    @pyqtSlot(QUrl)
    def setImageFile(self, path):
        self._image = QImage(path.toLocalFile())
        self._original = self._image.copy()
        self.updateImage()
        self.checkAnnotation()

    @pyqtSlot()
    def setImageCanvas(self):
        w,h = 0,0
        if self._linked:
            w,h = self._linked._image.size().width(),  self._linked._image.size().height()
        if not w or not w:
            w,h = self.basic.parameters.values.get("width"),  self.basic.parameters.values.get("height")
        self._image = QImage(QSize(int(w),int(h)), QImage.Format_ARGB32_Premultiplied)
        self._image.fill(0)
        self._original = self._image.copy()
        self.updateImage()
        self.checkAnnotation()

    @pyqtSlot(MimeData, int)
    def setImageDrop(self, mimeData, index):
        mimeData = mimeData.mimeData
        found = False
        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
            if source != index:
                source = self.basic._inputs[source]
                if not source._display:
                    self._image = source._original
                    self._offset = source._offset
                else:
                    self._image = source.display
                found = True
        else:
            source = mimeData.imageData()
            if source and not source.isNull():
                self._image = source
                found = True
            else:
                for url in mimeData.urls():
                    if url.isLocalFile():
                        self._image = QImage(url.toLocalFile())
                        found = True
                        break
                    elif url.scheme() == "http" or url.scheme() == "https":
                        if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                            self.basic.download(url, index)
                            break

        if found:
            self._original = self._image.copy()
            self.updateImage()
            self.checkAnnotation()

    @pyqtSlot(QImage)
    def setImageData(self, data):
        self._image = data

        self._original = self._image.copy()
        self.updateImage()
        self.checkAnnotation()

    def updateExtent(self):
        if self._role != BasicInputRole.MASK or not self._image or self._image.isNull():
            self._extent = QRect()
            self.updated.emit()
            return
                
        img = QImagetoPIL(self._image)
        bound = img.getbbox()
        if bound == None:
            self._extent = QRect()
            self.extentUpdated.emit()
            return

        source = (self._image.width(), self._image.height())
        padding = self.parent()._parameters._values.get("padding")
        working = (self.parent()._parameters._values.get("width"), self.parent()._parameters._values.get("height"))
        
        x1,y1,x2,y2 = parameters.get_extent(bound, padding, source, working)
        self._extent = QRect(x1,y1,x2-x1,y2-y1)
        self._extentWarning = (x2-x1) > working[0] or (y2-y1) > working[1]
        self.extentUpdated.emit()

    @pyqtSlot()
    def clearImage(self):
        self._image = QImage()
        self.updateImage()

    def getMimeData(self, index):
        mimeData = QMimeData()
        mimeData.setData(MIME_BASIC_INPUT, QByteArray(f"{index}".encode()))
        mimeData.setImageData(self._image)
        return mimeData

    @pyqtSlot(int)
    def drag(self, index):
        if self._dragging:
            return
        self._dragging = True
        drag = QDrag(self)
        drag.setMimeData(self.getMimeData(index))
        drag.exec()
        self._dragging = False

    @pyqtSlot(int)
    def copy(self, index):
        QApplication.clipboard().setMimeData(self.getMimeData(index))

class BasicOutput(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, image=QImage()):
        super().__init__(parent)
        self.basic = parent
        self._image = image
        self._metadata = None
        self._artifacts = {}
        self._artifactNames = []
        self._display = None
        self._file = ""
        self._parameters = ""
        self._dragging = False
        self._ready = False

    def setResult(self, image, metadata):
        self._image = image
        self._metadata = metadata
        self._file = metadata["file"]
        self._parameters = parameters.format_parameters(self._metadata)
        self._image.setText("parameters", self._parameters)
        self._ready = True
        self.updated.emit()

    def setPreview(self, image):
        self._image = image
        self.updated.emit()

    def setArtifacts(self, artifacts):
        self._artifacts = artifacts
        self._artifactNames = list(self._artifacts.keys())
        self._display = None
        self.updated.emit()

    @pyqtSlot(QUrl)
    def saveImage(self, file):
        file = file.toLocalFile()
        if not "." in file.rsplit(os.path.sep,1)[-1]:
            file = file + ".png"
        try:
            self.display.save(file)
        except Exception:
            pass

    @pyqtProperty(bool, notify=updated)
    def ready(self):
        return self._ready

    @pyqtProperty(QImage, notify=updated)
    def image(self):
        return self._image
    
    @pyqtProperty(QImage, notify=updated)
    def display(self):
        if not self._display:
            return self._image
        return self._artifacts[self._display]
    
    @pyqtProperty(str, notify=updated)
    def displayName(self):
        return self._display
    
    @pyqtProperty(str, notify=updated)
    def displayIndex(self):
        if not self._artifacts:
            return ""
        if not self._display:
            return f"1 of {len(self._artifactNames)+1}"
        else:
            idx = self._artifactNames.index(self._display)
            return f"{idx+2} of {len(self._artifactNames)+1}"

    @pyqtSlot()
    def nextDisplay(self):
        if not self._display:
            if self._artifactNames:
                self._display = self._artifactNames[0]
        else:
            idx = self._artifactNames.index(self._display) + 1
            if idx < len(self._artifactNames):
                self._display = self._artifactNames[idx]
            else:
                self._display = None
        self.updated.emit()
    
    @pyqtSlot()
    def prevDisplay(self):
        if not self._display:
            if self._artifactNames:
                self._display = self._artifactNames[-1]
        else:
            idx = self._artifactNames.index(self._display) - 1
            if idx >= 0:
                self._display = self._artifactNames[idx]
            else:
                self._display = None
        self.updated.emit()

    @pyqtProperty(str, notify=updated)
    def file(self):
        return self._file
    
    @pyqtProperty(str, notify=updated)
    def mode(self):
        if not self._metadata:
            return ""
        return self._metadata["mode"]
    
    @pyqtProperty(int, notify=updated)
    def width(self):
        return self.display.width()
    
    @pyqtProperty(int, notify=updated)
    def height(self):
        return self.display.height()

    @pyqtProperty(bool, notify=updated)
    def empty(self):
        return self._image.isNull()
        
    @pyqtProperty(str, notify=updated)
    def size(self):
        if self._image.isNull():
            return ""
        return f"{self._image.width()}x{self._image.height()}"

    @pyqtProperty(str, notify=updated)
    def parameters(self):
        return self._parameters

    @pyqtSlot()
    def drag(self):
        if not self._display:
            self.basic.gui.dragFiles([self._file])
        else:
            self.basic.gui.dragImage(self.display)

    @pyqtSlot()
    def copy(self):
        if not self._display:
            self.basic.gui.copyFiles([self._file])
        else:
            self.basic.gui.copyImage(self.display)

    @pyqtProperty(list, notify=updated)
    def artifacts(self):
        return list(self._artifacts.keys())

    @pyqtSlot(str, result=QImage)
    def artifact(self, name):
        return self._artifacts[name]

class BasicImageWriter(QRunnable):
    guard = QMutex()
    def __init__(self, img, metadata, outputs, subfolder=""):
        super(BasicImageWriter, self).__init__()
        self.setAutoDelete(True)

        if not BasicImageWriter.guard.tryLock(5000):
            BasicImageWriter.guard.unlock()
            BasicImageWriter.guard.lock()

        m = PIL.PngImagePlugin.PngInfo()
        m.add_text("parameters", parameters.format_parameters(metadata))

        if not subfolder:
            subfolder = metadata["mode"]

        folder = os.path.join(outputs, subfolder)
        os.makedirs(folder, exist_ok=True)

        idx = parameters.get_index(folder)
        name = f"{idx:08d}-" + datetime.datetime.now().strftime("%m%d%H%M")

        self.img = img
        self.tmp = os.path.join(folder, f"{name}.tmp")
        self.real = os.path.join(folder, f"{name}.png")
        self.metadata = m

        metadata["file"] = self.real

    @pyqtSlot()
    def run(self):
        if type(self.img) == QImage:
            self.img = encode_image(self.img)

        if type(self.img) == bytes:
            self.img = PIL.Image.open(io.BytesIO(self.img))

        self.img.save(self.tmp, format="PNG", pnginfo=self.metadata)
        os.replace(self.tmp, self.real)

        BasicImageWriter.guard.unlock()

class Basic(QObject):
    updated = pyqtSignal()
    suggestionsUpdated = pyqtSignal()
    results = pyqtSignal()
    pastedText = pyqtSignal(str)
    pastedImage = pyqtSignal(QImage)
    openedUpdated = pyqtSignal()
    startBuildModel = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.pool = QThreadPool.globalInstance()
        self.priority = 0
        self.name = "Generate"
        self._parameters = parameters.Parameters(parent)
        self._inputs = []
        self._outputs = {}
        self._links = {}
        self._ids = []
        self._forever = False
        self._remaining = 0
        self._requests = []
        self._mapping = {}
        self._annotations = {}
        self._folders = {}

        self._openedIndex = -1
        self._openedArea = ""

        self._collection = []
        self._collectionDetails = {}
        self._dictionary = {}
        self._dictionaryDetails = {}

        self._suggestions = []
        self._vocab = {}

        self._replyIndex = None

        self.updated.connect(self.link)
        self.gui.result.connect(self.result)
        self.gui.reset.connect(self.reset)
        self.gui.networkReply.connect(self.onNetworkReply)
        self.gui.optionsUpdated.connect(self.optionsUpdated)

        qmlRegisterSingletonType(Basic, "gui", 1, 0, "BASIC", lambda qml, js: self)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE outputs(id INTEGER);")
        self.conn.enableNotifications("outputs")

    def buildRequest(self):
        if self._remaining != 0 and self._requests:
            return self._requests[self._remaining-1]

        order = []
        images = []
        masks = []
        areas = []
        controls = []

        mapped_masks = {}
        mapped_areas = {}

        if self._inputs:
            for i in self._inputs:
                if not i._image or i._image.isNull():
                    continue
                if i._role == BasicInputRole.IMAGE:
                    order += [i]
                    images += [encode_image(i._original_crop or i._original)]
                if i._role == BasicInputRole.MASK:
                    masks += [encode_image(i._image)]
                    if i._linked:
                        mapped_masks[i._linked] = masks[-1]
                if i._role == BasicInputRole.SUBPROMPT:
                    if not i._areas:
                        areas += [[encode_image(a) for a in i.getAreas()]]
                        if i._linked:
                            mapped_areas[i._linked] = areas[-1]
                if i._role == BasicInputRole.CONTROL:
                    model = i._settings.get("mode").lower()
                    opts = {
                        "scale": i._settings.get("CN_strength"),
                        "annotator": i._settings.get("CN_preprocessor").lower(),
                        "args": i.getCNArgs()
                    }
                    controls += [(model, opts, encode_image(i._original_crop or i._original))]

        batch_size = int(self._parameters._values.get("batch_size"))
        batch_count = int(self._parameters._values.get("batch_count"))
        total = max(len(order), batch_count * batch_size)

        output_folder = self._parameters._values.get("batch_size")

        if order:
            masks = []
            areas = []
            
            for i in order:
                if i in mapped_masks:
                    masks += [mapped_masks[i]]
                elif mapped_masks:
                    masks += [None]

                if i in mapped_areas:
                    areas += [mapped_areas[i]]
                elif mapped_areas:
                    areas += [[]]

        def get_portion(data, start, amount):
            if not data:
                return []
            out = []
            for i in range(amount):
                out += [data[(start+i)%len(data)]]
            return out

        self._requests = []
        i = 0
        while total > 0:
            size = min(total, batch_size)
            batch_images = get_portion(images, i, size)
            batch_masks = get_portion(masks, i, size)
            batch_areas = get_portion(areas, i, size)

            i += batch_size
            total -= batch_size
            
            self._requests += [self._parameters.buildRequest(size, batch_images, batch_masks, batch_areas, controls)]
        
        self._remaining = len(self._requests)

        return self._requests[self._remaining-1]

    @pyqtSlot()
    def generate(self, user=True):
        if not self._ids:
            if user:
                self._remaining = 0
                self._requests = None
                self._folders = {}
            request = self.buildRequest()
            id = self.gui.makeRequest(request)
            self._folders[id] = self._parameters._values.get("output_folder")
            self._ids += [id]
            self.updated.emit()

    @pyqtSlot(int, str)
    def result(self, id, name):
        results = self.gui._results[id]

        if id in self._annotations:
            img = results["result"][0]
            id = self._annotations[id]
            for i in self._inputs:
                if i._id == id:
                    i.setArtifacts({"Annotated":img})
        if not id in self._ids:
            return
        if not id in self._mapping:
            self._mapping[id] = (time.time_ns() // 1000000) % (2**31 - 1)

        if "result" in results and "metadata" in results:
            for i in range(len(results["result"])):
                folder = self._folders[id]
                writer = BasicImageWriter(results["result"][i], results["metadata"][i], self.gui.outputDirectory(), folder)
                self.pool.start(writer)

        out = self._mapping[id]
        if not out in self._outputs:
            sticky = self.isSticky()
            available = self.gui._results[id]
            if "result" in available:
                initial = available["result"]
            elif "preview" in available:
                initial = available["preview"]
            else:
                return
            for i in range(len(initial)-1, -1, -1):
                self._outputs[out] = BasicOutput(self, initial[i])
                q = QSqlQuery(self.conn.db)
                q.prepare("INSERT INTO outputs(id) VALUES (:id);")
                q.bindValue(":id", out)
                self.conn.doQuery(q)
                out += 1
                if sticky and "result" in available:
                    self.stick()

            if "metadata" in available:
                out = self._mapping[id]
                for i in range(len(initial)-1, -1, -1):
                    self._outputs[out].setResult(available["result"][i], available["metadata"][i])
                    out += 1
            
        if name == "preview":
            previews = self.gui._results[id]["preview"]
            out = self._mapping[id]
            for i in range(len(previews)-1, -1, -1):
                self._outputs[out].setPreview(previews[i])
                out += 1

        if name == "result": 
            self._ids.remove(id)
            sticky = self.isSticky()
            results = self.gui._results[id]["result"]
            metadata = self.gui._results[id]["metadata"]
            artifacts = {k:v for k,v in self.gui._results[id].items() if not k in {"result", "metadata", "preview"}}
            self.gui._results = {}
            out = self._mapping[id]
            for i in range(len(results)-1, -1, -1):
                if not self._outputs[out]._ready:
                    self._outputs[out].setResult(results[i], metadata[i])
                self._outputs[out].setArtifacts({k:v[i%len(v)] for k,v in artifacts.items() if v[i%len(v)]})
                out += 1
            if sticky:
                self.stick()

            self._remaining = max(0, self._remaining-1)
            if self._remaining > 0 or self._forever:
                self.generate(user=False)
            else:
                self._requests = []

            self.updated.emit()
            self.results.emit()
        
    @pyqtSlot(int)
    def reset(self, id):
        if id in self._mapping:
            out = self._mapping[id]
            while out in self._outputs:
                self.deleteOutput(out)
                if self._openedIndex == out:
                    self.right()
                out += 1

        self._ids = []

    @pyqtSlot()
    def cancel(self):
        if self._ids:
            self._remaining = 0
            self._requests = None
            self.gui.cancelRequest(self._ids.pop())
            self.updated.emit()

    @pyqtProperty(bool, notify=updated)
    def forever(self):
        return self._forever

    @forever.setter
    def forever(self, forever):
        self._forever = forever
        self.updated.emit()

    @pyqtProperty(int, notify=updated)
    def remaining(self):
        if self._requests and len(self._requests) <= 1:
            return 0
        return int(self._remaining)

    @pyqtProperty(parameters.Parameters, notify=updated)
    def parameters(self):
        return self._parameters

    @pyqtProperty(list, notify=updated)
    def inputs(self):
        return self._inputs

    @pyqtSlot(int, result=BasicOutput)
    def outputs(self, id):
        if id in self._outputs:
            return self._outputs[id]

    @pyqtSlot()
    def addImage(self):
        self._inputs += [BasicInput(self, QImage(), BasicInputRole.IMAGE)]
        self.updated.emit()

    @pyqtSlot()
    def addMask(self):
        self._inputs += [BasicInput(self, QImage(), BasicInputRole.MASK)]
        self.updated.emit()

    @pyqtSlot()
    def addSubprompt(self):
        self._inputs += [BasicInput(self, QImage(), BasicInputRole.SUBPROMPT)]
        self.updated.emit()

    @pyqtSlot(str)
    def addControl(self, mode):
        i = BasicInput(self, QImage(), BasicInputRole.CONTROL)
        i._settings.set("mode", mode)
        self._inputs += [i]
        self.updated.emit()

    @pyqtSlot()
    def link(self):
        for i in range(len(self._inputs)):
            curr = self._inputs[i]
            if not curr._linked in self._inputs:
                curr.setLinked(None)
        for i in range(len(self._inputs)):
            curr = self._inputs[i]
            if i == 0 or curr._role == BasicInputRole.IMAGE:
                continue
            prev = self._inputs[i-1]
            if prev._role == BasicInputRole.IMAGE:
                curr.setLinked(prev)
                continue
            if prev._linked:
                if not any([p._linked == prev._linked and p._role == curr._role and p != curr for p in self._inputs]):
                    if curr._role != BasicInputRole.IMAGE and prev._role != BasicInputRole.IMAGE:
                        curr.setLinked(prev._linked)
                        continue
            curr.setLinked(None)
        for i in range(len(self._inputs)):
            self._inputs[i].updateLinked()

    def hasMask(self, input):
        for i in range(len(self._inputs)):
            curr = self._inputs[i]
            if curr._linked == input and curr._role == BasicInputRole.MASK:
                return True
        return False

    def moveItem(self, source, destination):
        i = self._inputs.pop(source)
        if source < destination:
            destination -= 1
        self._inputs.insert(destination, i)
        self.updated.emit()

    def swapItem(self, source, destination):
        a = self._inputs[source]
        b = self._inputs[destination]
        self._inputs[source] = b
        self._inputs[destination] = a
        self.updated.emit()

    @pyqtSlot(str)
    def importImage(self, file):
        source = QImage(file)
        self._inputs.append(BasicInput(self, source, BasicInputRole.IMAGE))
        self.updated.emit()

    @pyqtSlot(MimeData, int)
    def addDrop(self, mimeData, index):
        mimeData = mimeData.mimeData
        if index == -1:
            index = len(self._inputs)

        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
            destination = index
            self.moveItem(source, destination)
        else:
            done = False
            for url in mimeData.urls():
                if url.isLocalFile():
                    source = QImage(url.toLocalFile())
                    self._inputs.insert(index, BasicInput(self, source, BasicInputRole.IMAGE))
                    done = True
                elif url.scheme() == "http" or url.scheme() == "https":
                    if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                        self.download(url, index)
            
            source = mimeData.imageData()
            if not done and source and not source.isNull():
                self._inputs.insert(index, BasicInput(self, source, BasicInputRole.IMAGE))
                
        self.updated.emit()

    @pyqtSlot(MimeData)
    def sizeDrop(self, mimeData):
        mimeData = mimeData.mimeData
        width,height = None,None
        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
            if self._inputs[source]._role == BasicInputRole.IMAGE:
                width,height = self._inputs[source]._original.width(), self._inputs[source]._original.height()
            else:
                width,height = self._inputs[source].width, self._inputs[source].height
        else:
            source = mimeData.imageData()
            if source and not source.isNull():
                width, height = source.width(), source.height()
            for url in mimeData.urls():
                if url.isLocalFile():
                    source = QImage(url.toLocalFile())
                    width, height = source.width(), source.height()
                    break

        if width and height:
            self._parameters._values.set("width", width)
            self._parameters._values.set("height", height)

    @pyqtSlot(MimeData)
    def seedDrop(self, mimeData):
        mimedata = mimeData.mimeData
        for url in mimedata.urls():
            if url.isLocalFile():
                image = QImage(url.toLocalFile())
                self.pastedImage.emit(image)
                params = parameters.get_parameters(image)
                if params:
                    try:
                        seed = parameters.parse_parameters(params)["seed"]
                        self._parameters._values.set("seed", int(seed))
                    except Exception:
                        pass
            
    @pyqtSlot(int)
    def deleteInput(self, index):
        self._inputs.pop(index)
        self.updated.emit()

        if self._openedIndex == index and self._openedArea == "input":
            if index > len(self._inputs):
                index -= 1
            self.open(index, "input")

    @pyqtSlot(int)
    def deleteOutput(self, id):
        if not id in self._outputs:
            return
        del self._outputs[id]
        self.updated.emit()
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM outputs WHERE id = :id;")
        q.bindValue(":id", id)
        self.conn.doQuery(q)
    
   
    @pyqtSlot(int)
    def deleteOutputAfter(self, id):
        for i in list(self._outputs.keys()):
            if i < id:
                del self._outputs[i]
        
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM outputs WHERE id < :idx;")
        q.bindValue(":idx", id)
        self.conn.doQuery(q)
        self.updated.emit()

    @pyqtProperty(int, notify=openedUpdated)
    def openedIndex(self):
        return self._openedIndex

    @pyqtProperty(str, notify=openedUpdated)
    def openedArea(self):
        return self._openedArea
    
    @pyqtSlot(int, str)
    def open(self, index, area):
        change = False
        if area == "input" and index < len(self._inputs) and index >= 0:
            change = True
        if area == "output" and index in self._outputs:
            change = True
        if change:
            self._openedIndex = index
            self._openedArea = area
            self.openedUpdated.emit()
    
    @pyqtSlot()
    def close(self):
        self._openedIndex = -1
        self._openedArea = ""
        self.openedUpdated.emit()

    @pyqtSlot()
    def delete(self):
        if self._openedIndex == -1:
            return
        
        if self._openedArea == "output":
            idx = self.outputIDToIndex(self._openedIndex)
            self.deleteOutput(self._openedIndex)
            if len(self._outputs) == 0:
                self.close()
                return
            id = self.outputIndexToID(idx-1)
            if id in self._outputs:
                self._openedIndex = id
                self.openedUpdated.emit()
                return
            id = self.outputIndexToID(idx)
            if id in self._outputs:
                self._openedIndex = id
                self.openedUpdated.emit()
                return

        
        if self._openedArea == "input":
            self.deleteInput(self._openedIndex)
            if len(self._inputs) == 0:
                self.close()
                return
            idx = self._openedIndex-1
            if idx >= 0:
                self._openedIndex = idx
                self.openedUpdated.emit()
    @pyqtSlot()
    def right(self):
        if self._openedIndex == -1:
            return
        
        if self._openedArea == "output":
            idx = self.outputIDToIndex(self._openedIndex) + 1
            id = self.outputIndexToID(idx)
            if id in self._outputs:
                self._openedIndex = id
                self.openedUpdated.emit()
        
        if self._openedArea == "input":
            idx = self._openedIndex + 1
            if idx < len(self._inputs):
                self._openedIndex = idx
                self.openedUpdated.emit()

    @pyqtSlot()
    def left(self):
        if self._openedIndex == -1:
            return
        
        if self._openedArea == "output":
            idx = self.outputIDToIndex(self._openedIndex) - 1
            id = self.outputIndexToID(idx)
            if id in self._outputs:
                self._openedIndex = id
                self.openedUpdated.emit()
        
        if self._openedArea == "input":
            idx = self._openedIndex - 1
            if idx >= 0:
                self._openedIndex = idx
                self.openedUpdated.emit()

    @pyqtSlot()
    def stick(self):
        if self._openedArea == "output":
            id = self.outputIndexToID(0)
            if id in self._outputs:
                self._openedIndex = id
                self.openedUpdated.emit()

    @pyqtSlot(int, result=int)
    def outputIDToIndex(self, id):
        outputs = sorted(list(self._outputs.keys()), reverse=True)
        for i, p in enumerate(outputs):
            if p == id:
                return i
        return -1

    @pyqtSlot(int, result=int)
    def outputIndexToID(self, idx):
        outputs = sorted(list(self._outputs.keys()), reverse=True)
        if idx >= 0 and idx < len(outputs):
            return outputs[idx]
        return -1

    def isSticky(self):
        if self._openedIndex == -1 or self._openedArea != "output":
            return False
        if not self._openedIndex in self._outputs:
            return True
        idx = self.outputIDToIndex(self._openedIndex)
        if idx == 0:
            return True
        if idx == 1 and not self._outputs[self.outputIndexToID(0)].ready:
            return True
        
    @pyqtSlot()
    def pasteClipboard(self):
        mimedata = QApplication.clipboard().mimeData()
        self.pasteMimedata(mimedata)

    @pyqtSlot(MimeData)
    def pasteDrop(self, mimedata):
        self.pasteMimedata(mimedata._mimeData)

    @pyqtSlot(str)
    def pasteText(self, params):
        self.pastedText.emit(params)
        
    def pasteMimedata(self, mimedata):
        if mimedata.hasText():
            self.pastedText.emit(mimedata.text())

        image = None
        if mimedata.hasImage():
            image = mimedata.imageData()
        
        urls = mimedata.urls()
        if mimedata.hasText():
            url = QUrl.fromUserInput(mimedata.text())
            if url.isValid():
                urls += [url]

        for url in urls:
            if url.isLocalFile():
                image = QImage(url.toLocalFile())
            elif url.scheme() == "http" or url.scheme() == "https":
                if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                    self.download(url, None)

        if image and not image.isNull():
            self.pastedImage.emit(image)
            params = parameters.get_parameters(image)
            if params:
                self.pastedText.emit(params)
        

    def download(self, url, index):
        self.gui.makeNetworkRequest(QNetworkRequest(url))
        self._replyIndex = index

    @pyqtSlot(QNetworkReply)
    def onNetworkReply(self, reply):
        image = QImage()
        image.loadFromData(reply.readAll())
        if not image.isNull():
            if self._replyIndex == None:
                self.pastedImage.emit(image)
                params = parameters.get_parameters(image)
                if params:
                    self.pastedText.emit(params)
            else:
                if self._replyIndex == -1:
                    self._replyIndex = len(self._inputs)
                if len(self._inputs) <= self._replyIndex:
                    self._inputs.insert(self._replyIndex, BasicInput(self, image, BasicInputRole.IMAGE))
                else:
                    self._inputs[self._replyIndex].setImageData(image)
        self.updated.emit()
        self._replyIndex = None

    @pyqtSlot(int, str)
    def copyItem(self, index, area):
        if area == "input":
            mimeData = QMimeData()
            mimeData.setImageData(self._inputs[index]._image)
            QApplication.clipboard().setMimeData(mimeData)
        else:
            self.gui.copyFiles([self._outputs[index]._file])

    @pyqtSlot(int, str)
    def pasteItem(self, index, area):
        if area == "input":
            inputs = []
            mimedata = QApplication.clipboard().mimeData()
            if mimedata.hasImage():
                image = mimedata.imageData()
                if image and not image.isNull():
                    inputs += [image]
            elif mimedata.hasUrls():
                for url in mimedata.urls():
                    if url.isLocalFile():
                        image = QImage(url.toLocalFile())
                        inputs += [image]
                    elif url.scheme() == "http" or url.scheme() == "https":
                        if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                            self.download(url, index)
            elif mimedata.hasText():
                url = QUrl.fromUserInput(mimedata.text())
                if url.isValid():
                    if url.isLocalFile():
                        image = QImage(url.toLocalFile())
                        inputs += [image]
                    elif url.scheme() == "http" or url.scheme() == "https":
                        if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                            self.download(url, index)

            if index == -1:
                for i in inputs[::-1]:
                    self._inputs.insert(len(self._inputs), BasicInput(self, i))
            elif inputs and index >= 0 and index < len(self._inputs):
                self._inputs[index].setImageData(inputs[0])

            self.updated.emit()

    @pyqtSlot(list)
    def importParameters(self, params):
        self._parameters.importParameters(params)

    @pyqtSlot(str)
    def buildModel(self, filename):
        unet = self._parameters._values.get("UNET")
        vae = self._parameters._values.get("VAE")
        clip = self._parameters._values.get("CLIP")

        device = self._parameters._values.get("device")

        request = {"type":"manage", "data":{"operation": "build", "unet":unet, "vae":vae, "clip":clip, "file":filename, "device_name": device}}

        if self._parameters._values.get("network_mode") == "Static":
            request["data"]["prompt"] = self._parameters.buildPrompts(1)

        self.gui.makeRequest(request)    

    @pyqtSlot(CanvasWrapper, BasicInput)
    def setupCanvas(self, wrapper, target):
        canvas = wrapper.canvas
        if target._role == BasicInputRole.MASK:
            canvas.setupMask(target.image, QSize(target.linkedWidth, target.linkedHeight))
            return
        if target._role == BasicInputRole.SUBPROMPT:
            if target._linked and target._linked._role == BasicInputRole.IMAGE:
                z = target.linkedImage.size()
            else:
                w,h = self.parameters.values.get("width"),  self.parameters.values.get("height")
                z = QSize(int(w),int(h))

            layerCount = len(self._parameters.subprompts)
            canvas.setupSubprompt(layerCount, target._areas, z)
    
    @pyqtSlot(CanvasWrapper, BasicInput)
    def syncCanvas(self, wrapper, target):
        if target == None:
            return
        canvas = wrapper.canvas
        if target._role == BasicInputRole.MASK:
            target.setImageData(canvas.getImage())
            return
        if target._role == BasicInputRole.SUBPROMPT:
            layers = canvas.getImages()
            if len(layers) <= len(target._areas):
                target._areas[:len(layers)] = layers
            else:
                target._areas = layers
            im = canvas.getDisplay()
            target.setImageData(im)

    @pyqtSlot(CanvasWrapper, int, BasicInput)
    def syncSubprompt(self, wrapper, active, target):
        canvas = wrapper.canvas
        layerCount = len(self._parameters.subprompts)

        areas = target._areas
        if len(target._areas) >= layerCount:
            areas = target._areas[:layerCount]

        canvas.syncSubprompt(layerCount, active, areas)

    @pyqtSlot(BasicInput)
    def closeSubprompt(self, target):
        layerCount = len(self._parameters.subprompts)
        if len(target._areas) > layerCount:
            target._areas = target._areas[:layerCount]

    def annotate(self, input):
        annotator = input._settings.get("CN_preprocessor").lower()
        args = input.getCNArgs()

        request = self._parameters.buildAnnotateRequest(annotator, args, encode_image(input._image))
        id = self.gui.makeRequest(request)
        self._annotations[id] = input._id

    @pyqtSlot()
    def dividerDrag(self):
        mimeData = QMimeData()
        mimeData.setData(MIME_BASIC_DIVIDER, QByteArray(f"DIVIDER".encode()))
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.exec()

    @pyqtSlot(MimeData)
    def dividerDrop(self, mimeData):
        mimeData = mimeData.mimeData
        if MIME_BASIC_DIVIDER in mimeData.formats():
            self.gui.config.set("swap", not self.gui.config.get("swap", False))
    
    @pyqtSlot()
    def doBuildModel(self):
        self.startBuildModel.emit()

    @pyqtProperty(list, notify=suggestionsUpdated)
    def suggestions(self):
        return self._suggestions
    
    def suggestionBlocks(self, text, pos):
        spaces = self.gui.config.get("autocomplete_words", False)

        blank = lambda m: '#' * len(m.group())
        safe = re.sub(r'__.+?__|<.+?>', blank, text)
        safe_blocks = re.split(SUGGESTION_BLOCK_REGEX(spaces), safe)

        blocks = []
        i = 0
        for b in safe_blocks:
            blocks += [text[i:i+len(b)]]
            i += len(b)

        i = 0
        before, after = "", ""
        for block in blocks:
            if pos <= i + len(block):
                before, after = block[:pos-i], block[pos-i:]
                break
            i += len(block)
        if before and before[0] in "\n,:|[]()":
            before = before[1:]
        return before, after

    def beforePos(self, text, pos):
        before, _ = self.suggestionBlocks(text, pos)

        while before and before[0] in "\n\t, ":
            before = before[1:]

        return before, pos-len(before)
    
    def afterPos(self, text, pos):
        _, after = self.suggestionBlocks(text, pos)

        if after:
            after = after.split("<",1)[0]

        return after, pos+len(after)
    
    def getSuggestions(self, text):
        text = text.lower().strip()
        if not text:
            return {}
        staging = {}

        for p,_ in self._collection:
            pl = p.lower()
            dl = self.suggestionDisplay(p).lower()
            if pl == text or dl == text:
                return {}
            if text in pl or text in dl:
                i = 1 - (len(text)/len(pl))
            else:
                continue
            staging[p] = i
        
        for t in self._dictionary:
            tl = t.lower()

            i = -1
            try:
                i = tl.index(text)
            except: pass

            if i == 0:
                i = 1 - (len(text.split()[0])/len(tl.split()[0]))
            elif i > 0:
                i = 1 - (len(text)/len(tl))
            else:
                continue
            staging[t] = i
        
        return staging

    @pyqtSlot(str, int)
    def updateSuggestions(self, text, pos):
        self._suggestions = []

        sensitivity = self.gui.config.get("autocomplete")
        self.vocabSync()

        before, _ = self.beforePos(text, pos)
        if before and sensitivity and len(before) >= sensitivity:
            staging = self.getSuggestions(before.lower())
            if staging:
                key = lambda k: (staging[k], self._dictionary[k] if k in self._dictionary else 0)
                self._suggestions = sorted(staging.keys(), key=key)
                if len(self._suggestions) > 10:
                    self._suggestions = self._suggestions[:10]

        self.suggestionsUpdated.emit()

    @pyqtSlot(str, result=str)
    def suggestionDetail(self, text):
        if text in self._collectionDetails:
            return self._collectionDetails[text]
        if text in self._dictionaryDetails:
            return self._dictionaryDetails[text]
        return ""
    
    @pyqtSlot(str, result=str)
    def suggestionDisplay(self, text):
        if text in self._collectionDetails:
            detail = self._collectionDetails[text]
            if detail == "LoRA":
                return f"<lora:{text}>"
            if detail == "HN":
                return f"<hypernet:{text}>"
            if detail == "Wild":
                return f"__{text}__"
        return text
    
    @pyqtSlot(str, int, result=str)
    def suggestionCompletion(self, text, start):
        if not text:
            return text
        if text in self._collectionDetails:
            return self.suggestionDisplay(text)
        elif self.gui.config.get("autocomplete_single", False):
            words = text.split()
            if len(words) == 1:
                return words[0]
            if len(words[0]) == start:
                return words[0] + " " + words[1]
            return words[0]
        return text

    @pyqtSlot(str, result=QColor)
    def suggestionColor(self, text):
        if text in self._collectionDetails:
            return {
                "TI": QColor("#ffd893"),
                "LoRA": QColor("#f9c7ff"),
                "HN": QColor("#c7fff6"),
                "Wild": QColor("#c7ffd2")
            }.get(self._collectionDetails[text], QColor("#cccccc"))
        return QColor("#cccccc")

    @pyqtSlot(str, int, result=int)
    def suggestionStart(self, text, pos):
        text, start = self.beforePos(text, pos)
        return start
    
    @pyqtSlot(str, int, result=int)
    def suggestionEnd(self, text, pos):
        text, end = self.afterPos(text, pos)
        return end
    
    def vocabSync(self):
        vocab = self.gui.config.get("vocab", [])
        if all([v in self._vocab for v in vocab]):
            return

        self._vocab = {k:v for k,v in self._vocab.items() if k in vocab}
        for k in vocab:
            if not k in self._vocab:
                p = k
                if not os.path.isabs(p):
                    p = os.path.join(self.gui.modelDirectory(), k)
                if os.path.exists(p):
                    with open(p, "r", encoding="utf-8") as f:
                        self._vocab[k] = f.readlines()
                else:
                    self.vocabRemove(k)

        self._dictionary = {}
        self._dictionaryDetails = {}
        for k in self._vocab:
            total = len(self._vocab[k])
            for i, line in enumerate(self._vocab[k]):
                line = line.strip()
                tag, order = line, int(((i+1)/total)*1000000)
                if "," in line:
                    tag, deco = line.split(",",1)[0].strip(), line.rsplit(",",1)[-1].strip()
                    self._dictionaryDetails[tag] = deco
                self._dictionary[tag] = order

    @pyqtSlot(str)
    def vocabAdd(self, file):
        vocab = self.gui.config.get("vocab", []) + [file]
        self.gui.config.set("vocab", vocab)
    
    @pyqtSlot(str)
    def vocabRemove(self, file):
        vocab = [v for v in self.gui.config.get("vocab", []) if not v == file]
        self.gui.config.set("vocab", vocab)

    @pyqtSlot()
    def optionsUpdated(self):
        self._collection = []
        if "TI" in self.gui._options:
            self._collection += [(self.gui.modelName(n), "TI") for n in self.gui._options["TI"]]
        if "LoRA" in self.gui._options:
            self._collection += [(self.gui.modelName(n), "LoRA") for n in self.gui._options["LoRA"]]
        if "HN" in self.gui._options:
            self._collection += [(self.gui.modelName(n), "HN") for n in self.gui._options["HN"]]
        self._collection += [(n, "Wild") for n in self.gui.wildcards._wildcards.keys()]
        self._collectionDetails = {k:v for k,v in self._collection}