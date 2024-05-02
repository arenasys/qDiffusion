from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QSize, QUrl, QMimeData, QByteArray
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterUncreatableType
from PyQt5.QtGui import QImage, QDrag, QCursor
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply

import parameters
import re
from misc import MimeData, encodeImage
from canvas.shared import CanvasWrapper
import sql
import time
import io
import datetime
import os

# this file is imported at the root
from tabs.basic.basic_input import BasicInput, MIME_BASIC_INPUT
from tabs.basic.basic_output import BasicOutput
from tabs.basic.basic_pose import Pose, PoseNode, PoseEdge

import misc
import manager
from manager import InputRole
import parameters

MIME_BASIC_DIVIDER = "application/x-qd-basic-divider"

class Basic(QObject):
    updated = pyqtSignal()
    managersUpdated = pyqtSignal()
    pastedText = pyqtSignal(str)
    pastedImage = pyqtSignal(QImage)
    openedUpdated = pyqtSignal()
    startBuildModel = pyqtSignal()
    typeUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.priority = 0
        self.name = "Generate"
        self._parameters = parameters.Parameters(parent)
        self._manager = manager.RequestManager(self.gui)
        self._detailers = manager.DetailerManager(self.gui)
        self._grid = misc.GridManager(self._parameters, self._manager, self)

        self._inputs = []
        self._outputs = {}
        self._links = {}

        self._forever = False

        self._opened_index = -1
        self._opened_area = ""

        self._suggestions = misc.SuggestionManager(self.gui)
        self._suggestions.setPromptSources()

        self._reply_index = None
        self._reply_id = None

        self.updated.connect(self.link)
        self.gui.response.connect(self.handleResponse)
        self.gui.result.connect(self.handleResult)
        self.gui.reset.connect(self.handleReset)
        self.gui.network.finished.connect(self.onNetworkReply)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE outputs(id INTEGER);")
        self.conn.enableNotifications("outputs")

        self._manager.result.connect(self.onResult)
        self._manager.artifact.connect(self.onArtifact)
        self._manager.finished.connect(self.onFinished)

        qmlRegisterSingletonType(Basic, "gui", 1, 0, "BASIC", lambda qml, js: self)
        qmlRegisterUncreatableType(Pose, "gui", 1, 0, "Pose", "Not a QML type")
        qmlRegisterUncreatableType(PoseNode, "gui", 1, 0, "PoseNode", "Not a QML type")
        qmlRegisterUncreatableType(PoseEdge, "gui", 1, 0, "PoseEdge", "Not a QML type")

    @pyqtSlot()
    def generate(self, user=True):
        if user:
            self._manager.cancelRequest()
            self.gui.clearCancelled()
        elif self.gui.isCancelled():
            return
        self.gui.setSending()
        if user or not self._manager.requests:
            self._manager.buildRequests(self._parameters, self._inputs)
        self._manager.makeRequest()
        self.updated.emit()
        
    @pyqtSlot(int, str)
    def handleResult(self, id, name):
        self._manager.handleResult(id, name)

    def createOutput(self, id, image):
        self._outputs[id] = BasicOutput(self, image)
        q = QSqlQuery(self.conn.db)
        q.prepare("INSERT INTO outputs(id) VALUES (:id);")
        q.bindValue(":id", id)
        self.conn.doQuery(q)

    @pyqtSlot(int, QImage, object, str)
    def onResult(self, id, image, metadata, filename):
        sticky = self.isSticky()

        if not id in self._outputs:
            self.createOutput(id, image)

        self._outputs[id].setResult(image, metadata, filename)

        if sticky:
            self.stick(id)
        
    @pyqtSlot(int, object, str)
    def onArtifact(self, id, data, name):
        if name == "annotated":
            match = [i for i in self._inputs if i._id == id]
            if match and not match[0].isPose:
                match[0].setArtifacts({"Annotated":data})
            return
        
        if name == "pose":
            match = [i for i in self._inputs if i._id == id]
            if match:
                match[0].setPose(data)
            return

        if not id in self._outputs:
            self.createOutput(id, data)
        
        if name == "preview":
            self._outputs[id].setPreview(data)
        elif name == "temporary":
            self._outputs[id].setTemporary(data)
        else:
            self._outputs[id].addArtifact(name, data)

    @pyqtSlot()
    def onFinished(self):
        if self._forever or self._manager.requests:
            self.generate(user=False)
        else:
            self._manager.count = 0

    @pyqtSlot(int, object)
    def handleResponse(self, id, response):
        if response["type"] == "hello":
            self._manager.monitoring = False
        if response["type"] == "owner":
            self._manager.monitoring = True
        if response["type"] == "ack":
            id = response["data"]["id"]
            queue = response["data"]["queue"]
            if id in self._manager.ids and queue > 0:
                self.gui.setWaiting()
        
    @pyqtSlot(int)
    def handleReset(self, id):
        self.clearUnfinished()

    def clearUnfinished(self):
        for out in list(self._outputs.keys()):
            if not self._outputs[out]._ready and not self._outputs[out]._fetching:
                if self._opened_index == out:
                    self.right()
                self.deleteOutput(out)

    @pyqtSlot()
    def cancel(self):
        if self._manager.cancelRequest():
            self.gui.setCancelling()
        self.updated.emit()

    @pyqtProperty(bool, notify=updated)
    def forever(self):
        return self._forever

    @forever.setter
    def forever(self, forever):
        self._forever = forever
        self.updated.emit()

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
        self._inputs += [BasicInput(self, QImage(), InputRole.IMAGE)]
        self.updated.emit()

    @pyqtSlot()
    def addMask(self):
        self._inputs += [BasicInput(self, QImage(), InputRole.MASK)]
        self.updated.emit()

    @pyqtSlot()
    def addSegment(self):
        self._inputs += [BasicInput(self, QImage(), InputRole.SEGMENTATION)]
        self.updated.emit()

    @pyqtSlot()
    def addSubprompt(self):
        self._inputs += [BasicInput(self, QImage(), InputRole.SUBPROMPT)]
        self.updated.emit()

    @pyqtSlot(str)
    def addControl(self, mode):
        i = BasicInput(self, QImage(), InputRole.CONTROL)
        i._control_settings.set("mode", mode)
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
            if i == 0 or curr._role in {InputRole.IMAGE, InputRole.SEGMENTATION}:
                curr.setLinked(None)
                continue
            prev = self._inputs[i-1]
            if prev._role == InputRole.IMAGE:
                curr.setLinked(prev)
                continue
            if prev._role == InputRole.CONTROL and curr._role == InputRole.CONTROL:
                curr.setLinked(prev)
                continue
            if prev._linked:
                linked = [p for p in self._inputs if p._linked == prev._linked and p != curr]
                if any([p.isTile for p in linked]):
                    continue
                linked_roles = set([p.effectiveRole() for p in linked])
                curr_role = curr.effectiveRole()
                if not curr_role in linked_roles or curr_role == InputRole.CONTROL:
                    curr.setLinked(prev._linked)
                    continue
            curr.setLinked(None)
        for i in range(len(self._inputs)):
            self._inputs[i].updateLinked()

    def hasMask(self, input):
        for i in range(len(self._inputs)):
            curr = self._inputs[i]
            if curr._linked == input and curr.isMask:
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
        self._inputs.append(BasicInput(self, source, InputRole.IMAGE))
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
                    path = url.toLocalFile()
                    if os.path.isdir(path):
                        input = BasicInput(self, QImage(), InputRole.IMAGE)
                        input.setFolder(url)
                        self._inputs.insert(index, input)
                    else:
                        self._inputs.insert(index, BasicInput(self, QImage(path), InputRole.IMAGE))
                    done = True
                elif url.scheme() == "http" or url.scheme() == "https":
                    if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                        self.download(url, index)
            
            source = mimeData.imageData()
            if not done and source and not source.isNull():
                self._inputs.insert(index, BasicInput(self, source, InputRole.IMAGE))
                
        self.updated.emit()

    @pyqtSlot(MimeData)
    def sizeDrop(self, mimeData):
        mimeData = mimeData.mimeData
        width,height = None,None
        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
            width, height = self._inputs[source].dropWidth, self._inputs[source].dropHeight
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
                params = parameters.getParameters(image)
                if params:
                    try:
                        seed = parameters.parseParameters(params)["seed"]
                        self._parameters._values.set("seed", int(seed))
                    except Exception:
                        pass
            
    @pyqtSlot(int)
    def deleteInput(self, index):
        self._inputs.pop(index)
        self.updated.emit()

        if self._opened_index == index and self._opened_area == "input":
            if index > len(self._inputs):
                index -= 1
            self.open(index, "input")

    @pyqtSlot(int)
    def deleteOutput(self, id):
        if not id in self._outputs:
            return
        self._outputs[id].deleteLater()
        del self._outputs[id]
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM outputs WHERE id = :id;")
        q.bindValue(":id", id)
        self.conn.doQuery(q)
   
    @pyqtSlot(int)
    def deleteOutputAfter(self, id):
        for i in list(self._outputs.keys()):
            if i < id:
                self._outputs[i].deleteLater()
                del self._outputs[i]
        q = QSqlQuery(self.conn.db)
        q.prepare("DELETE FROM outputs WHERE id < :idx;")
        q.bindValue(":idx", id)
        self.conn.doQuery(q)

    @pyqtProperty(int, notify=openedUpdated)
    def openedIndex(self):
        return self._opened_index

    @pyqtProperty(str, notify=openedUpdated)
    def openedArea(self):
        return self._opened_area
    
    @pyqtSlot(int, str)
    def open(self, index, area):
        change = False
        if area == "input" and index < len(self._inputs) and index >= 0:
            change = True
        if area == "output" and index in self._outputs:
            change = True
        if change:
            self._opened_index = index
            self._opened_area = area
            self.openedUpdated.emit()
    
    @pyqtSlot()
    def close(self):
        self._opened_index = -1
        self._opened_area = ""
        self.openedUpdated.emit()

    @pyqtSlot()
    def delete(self):
        if self._opened_index == -1:
            return
        
        if self._opened_area == "output":
            idx = self.outputIDToIndex(self._opened_index)
            self.deleteOutput(self._opened_index)
            if len(self._outputs) == 0:
                self.close()
                return
            id = self.outputIndexToID(idx-1)
            if id in self._outputs:
                self._opened_index = id
                self.openedUpdated.emit()
                return
            id = self.outputIndexToID(idx)
            if id in self._outputs:
                self._opened_index = id
                self.openedUpdated.emit()
                return

        
        if self._opened_area == "input":
            self.deleteInput(self._opened_index)
            if len(self._inputs) == 0:
                self.close()
                return
            idx = self._opened_index-1
            if idx >= 0:
                self._opened_index = idx
                self.openedUpdated.emit()
    @pyqtSlot()
    def right(self):
        if self._opened_index == -1:
            return
        
        if self._opened_area == "output":
            idx = self.outputIDToIndex(self._opened_index) + 1
            id = self.outputIndexToID(idx)
            if id in self._outputs:
                self._opened_index = id
                self.openedUpdated.emit()
        
        if self._opened_area == "input":
            idx = self._opened_index + 1
            if idx < len(self._inputs):
                self._opened_index = idx
                self.openedUpdated.emit()

    @pyqtSlot()
    def left(self):
        if self._opened_index == -1:
            return
        
        if self._opened_area == "output":
            idx = self.outputIDToIndex(self._opened_index) - 1
            id = self.outputIndexToID(idx)
            if id in self._outputs and self._outputs[id]._ready:
                self._opened_index = id
                self.openedUpdated.emit()
        
        if self._opened_area == "input":
            idx = self._opened_index - 1
            if idx >= 0:
                self._opened_index = idx
                self.openedUpdated.emit()

    @pyqtSlot()
    def stick(self, id=None):
        if self._opened_area == "output":
            if not id:
                id = self.outputIndexToID(0)
            if id in self._outputs:
                self._opened_index = id
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
        if self._opened_index == -1 or self._opened_area != "output":
            return False
        if not self._opened_index in self._outputs:
            return True
        idx = self.outputIDToIndex(self._opened_index)
        any_ready = False

        for i in range(idx-1, -1, -1):
            if self._outputs[self.outputIndexToID(i)].ready:
                any_ready = True

        if not any_ready:
            return True

        return False
        
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
                    break

        if image and not image.isNull():
            self.pastedImage.emit(image)
            params = parameters.getParameters(image)
            if params:
                self.pastedText.emit(params)
        

    def download(self, url, index):
        self._reply_index = index
        self._reply_id = self.gui.network.download(url.fileName(), url)

    @pyqtSlot(misc.DownloadInstance)
    def onNetworkReply(self, reply):
        if reply._id != self._reply_id or reply._error != "":
            return

        image = QImage()
        image.loadFromData(reply._reply.readAll())
        if not image.isNull():
            if self._reply_index == None:
                self.pastedImage.emit(image)
                params = parameters.getParameters(image)
                if params:
                    self.pastedText.emit(params)
            else:
                if self._reply_index == -1:
                    self._reply_index = len(self._inputs)
                if len(self._inputs) <= self._reply_index:
                    self._inputs.insert(self._reply_index, BasicInput(self, image, InputRole.IMAGE))
                else:
                    self._inputs[self._reply_index].setImageData(image)
        self.updated.emit()
        self._reply_index = None

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
            request["data"]["prompt"] = self._parameters.buildPrompts()

        self.gui.makeRequest(request)    

    @pyqtSlot(CanvasWrapper, BasicInput)
    def setupCanvas(self, wrapper, target):
        canvas = wrapper.canvas
        if target._role in {InputRole.IMAGE, InputRole.CONTROL}:
            if target._paint.isNull():
                canvas.setupPainting(target._original)
            else:
                canvas.setupPainting(target._base, target._paint)
            return
        if target._role == InputRole.MASK:
            canvas.setupMask(target.image, QSize(target.linkedWidth, target.linkedHeight))
            return
        if target._role == InputRole.SUBPROMPT:
            if target._linked and target._linked._role == InputRole.IMAGE:
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
        if target._role in {InputRole.IMAGE, InputRole.CONTROL}:
            image = canvas.getDisplay()
            base, paint = canvas.getImages()
            target.setPaintedData(image, base, paint)
            return
        if target._role == InputRole.MASK:
            target.setImageData(canvas.getImage())
            return
        if target._role == InputRole.SUBPROMPT:
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
        annotator = input._control_settings.get("preprocessor")
        args = input.getControlArgs()

        img = input.image
        if input.isPose:
            img = input.originalCrop

        request = self._parameters.buildAnnotateRequest(annotator, args, encodeImage(img))
        self._manager.makeAnnotationRequest(request, input._id)

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

    @pyqtProperty(misc.SuggestionManager, notify=managersUpdated)
    def suggestions(self):
        return self._suggestions
    
    @pyqtProperty(manager.DetailerManager, notify=managersUpdated)
    def detailers(self):
        return self._detailers

    @pyqtProperty(manager.RequestManager, notify=managersUpdated)
    def manager(self):
        return self._manager

    @pyqtProperty(misc.GridManager, notify=managersUpdated)
    def grid(self):
        return self._grid

    @pyqtSlot(result=str)
    def getRequestType(self):
        t = None
        for i in self._inputs:
            r = i.effectiveRole()
            if r == InputRole.IMAGE:
                t = "Img2Img"
            if r == InputRole.MASK and t == "Img2Img":
                t = "Inpainting"
            if r == InputRole.SEGMENTATION and t == None:
                t = "Segmenting"
        if not t:
            t = "Txt2Img"
        
        upsc = self._parameters._values.get("steps") == 0 or self._parameters._values.get("strength") == 0.0
        if t in ["Img2Img", "Inpainting"] and upsc:
            t = "Upscaling"

        hr = self._parameters._values.get("hr_factor") > 1.0

        is_txt2img = t == "Txt2Img"
        if is_txt2img and hr:
            t += " + HR"
        if is_txt2img and self._parameters._activeDetailers:
            t += " + Detail"

        return t

    @pyqtSlot()
    def onImageUpdated(self):
        self.typeUpdated.emit()

    @pyqtSlot()
    def applyDefaults(self):
        model = self._parameters._values.get("model")
        model_name = self.gui.modelName(model)

        defaults = self.gui.getDefaults(model_name)
        fallback = {
            "model_mode": "Standard",
            "prediction_type": "Default",
            "cfg_rescale": 0.0,
            "clip_skip": 1
        }
        for k, v in fallback.items():
            if not k in defaults:
                defaults[k] = v

        for k, v in defaults.items():
            kk = k + "s"
            if kk in self._parameters._values._map:
                if not v in self._parameters._values.get(kk):
                    continue
            self._parameters._values.set(k, v)

    @pyqtSlot()
    def saveDefaults(self):
        model = self._parameters._values.get("model")
        model_name = self.gui.modelName(model)
        defaults = {}
        for k in ["model_mode", "prediction_type", "cfg_rescale", "clip_skip"]:
            defaults[k] = self._parameters._values.get(k)
        self.gui.setDefaults(model_name, defaults)