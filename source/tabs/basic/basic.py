from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QSize, QUrl, QMimeData, QByteArray, QThreadPool, Qt, QRect, QRunnable, QMutex
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtGui import QImage, QDrag, QColor
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
from tabs.basic.basic_input import BasicInput, BasicInputRole, MIME_BASIC_INPUT
from tabs.basic.basic_output import BasicOutput

import misc

import PIL.Image
import PIL.PngImagePlugin

MIME_BASIC_DIVIDER = "application/x-qd-basic-divider"

SUGGESTION_BLOCK_REGEX = lambda spaces: r'(?=\n|,|(?<!lora|rnet):|\||\[|\]|\(|\)'+ ('|\s)' if spaces else r')')

class BasicImageWriter(QRunnable):
    guard = QMutex()
    def __init__(self, img, metadata, outputs, subfolder, filename):
        super(BasicImageWriter, self).__init__()
        self.setAutoDelete(True)

        if not BasicImageWriter.guard.tryLock(5000):
            BasicImageWriter.guard.unlock()
            BasicImageWriter.guard.lock()

        m = PIL.PngImagePlugin.PngInfo()
        if metadata:
            m.add_text("parameters", parameters.formatParameters(metadata))

        folder = os.path.join(outputs, subfolder)
        os.makedirs(folder, exist_ok=True)

        if not filename:
            idx = parameters.getIndex(folder)
            filename = f"{idx:08d}-" + datetime.datetime.now().strftime("%m%d%H%M")

        self.img = img
        self.tmp = os.path.join(folder, f"{filename}.tmp")
        self.file = os.path.join(folder, f"{filename}.png")
        self.metadata = m

    @pyqtSlot()
    def run(self):
        if type(self.img) == QImage:
            self.img = encodeImage(self.img)

        if type(self.img) == bytes:
            self.img = PIL.Image.open(io.BytesIO(self.img))

        self.img.save(self.tmp, format="PNG", pnginfo=self.metadata)
        os.replace(self.tmp, self.file)

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
        self._subfolders = {}
        self._filenames = {}
        self._accept_all = False

        self._openedIndex = -1
        self._openedArea = ""

        self._collection = []
        self._collectionDetails = {}
        self._dictionary = {}
        self._dictionaryDetails = {}

        self._suggestions = []
        self._vocab = {}

        self._replyIndex = None
        self._replyId = None

        self.updated.connect(self.link)
        self.gui.response.connect(self.response)
        self.gui.result.connect(self.result)
        self.gui.reset.connect(self.reset)
        self.gui.network.finished.connect(self.onNetworkReply)
        self.gui.optionsUpdated.connect(self.optionsUpdated)

        qmlRegisterSingletonType(Basic, "gui", 1, 0, "BASIC", lambda qml, js: self)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE outputs(id INTEGER);")
        self.conn.enableNotifications("outputs")

    def buildRequest(self):
        if self._remaining != 0 and self._requests:
            return self._requests[self._remaining-1]

        inputs = {}
        links = {}
        controls = {}

        segmentation = []
        
        if self._inputs:
            for i in self._inputs:
                data = []
                if i._role == BasicInputRole.IMAGE:
                    if i._image and not i._image.isNull():
                        data += [encodeImage(i._originalCrop or i._original)]
                    if i._files:
                        for f in i._files[::-1]:
                            data += [i.getFilePath(f)]
                    if data:
                        inputs[i] = data
                if i._role == BasicInputRole.MASK or (i._role == BasicInputRole.CONTROL and i._control_mode == "Inpaint"):
                    if i._linked:
                        links[i] = i._linked
                        if i._image and not i._image.isNull():
                            data += [encodeImage(i._image)]
                        if i._files:
                            for f in i._files[::-1]:
                                data += [i.getFilePath(f)]
                        if data:
                            inputs[i] = data
                            data = []
                if i._role == BasicInputRole.SUBPROMPT:
                    if i._linked:
                        links[i] = i._linked
                    if i._image and not i._image.isNull():
                        data += [[encodeImage(a) for a in i.getAreas()]]
                    if data:
                        inputs[i] = data
                if i._role == BasicInputRole.CONTROL:
                    model = i._control_settings.get("mode")
                    opts = {
                        "scale": i._control_settings.get("strength"),
                        "annotator": i._control_settings.get("preprocessor"),
                        "args": i.getControlArgs()
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

        if segmentation:
            return self.buildSegmentationRequest(segmentation)

        images, masks, areas = [], [], []
        used = []
        for k in inputs:
            if k in used:
                continue
            linked = [k] + [i for i in links if links[i] == k]
            size = max([len(inputs[i]) for i in linked])
            for z in range(size):
                img, msk, are = None, None, []
                for j in linked:
                    data = inputs[j][z % len(inputs[j])]
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

        batch_size = int(self._parameters._values.get("batch_size"))
        batch_count = int(self._parameters._values.get("batch_count"))

        total = max([len(controls[k]) for k in controls]) if controls else 0
        total = max(len(images), len(segmentation), batch_count * batch_size, total)

        def get_portion(data, start, amount):
            if not data:
                return []
            out = []
            for i in range(amount):
                out += [data[(start+i)%len(data)]]
            return out

        self._requests = []
        i = 0
        ci = 0
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
            
            self._requests += [self._parameters.buildRequest(size, batch_images, batch_masks, batch_areas, batch_control)]
        
        self._remaining = len(self._requests)

        return self._requests[self._remaining-1]
    
    def buildSegmentationRequest(self, segmentation):
        requests = []
        for img, opts in segmentation:
            request = {
                "type": "segmentation",
                "data": {
                    "image": [img],
                    "seg_opts": [opts],
                    "device": self._parameters._values.get("device")
                }
            }
            requests += [request]
        
        self._requests = requests
        self._remaining = len(self._requests)
        return self._requests[self._remaining-1]
        
    def loadRequestImages(self, request):
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

    @pyqtSlot()
    def generate(self, user=True):
        if not self._ids:
            if user:
                self._remaining = 0
                self._requests = None
                self._subfolders = {}
                self._filenames = {}
            request = self.buildRequest()
            filename = self.loadRequestImages(request)
            subfolder = self._parameters._values.get("output_folder")
            id = self.gui.makeRequest(request)

            self._subfolders[id] = subfolder or request["type"]
            self._filenames[id] = filename if subfolder else ""
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

        ours = id in self._ids
        if not ours and not self._accept_all:
            return
        
        if not id in self._mapping:
            self._mapping[id] = (time.time_ns() // 1000000) % (2**31 - 1)

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
            
        if name == "preview":
            previews = self.gui._results[id]["preview"]
            out = self._mapping[id]
            for i in range(len(previews)-1, -1, -1):
                self._outputs[out].setPreview(previews[i])
                out += 1

        if name == "result":
            if ours:
                self._ids.remove(id)
            sticky = self.isSticky()
            results = self.gui._results[id]["result"]
            metadata = self.gui._results[id].get("metadata", None)
            artifacts = {k:v for k,v in self.gui._results[id].items() if not k in {"result", "metadata", "preview"}}
            out = self._mapping[id]
            for i in range(len(results)-1, -1, -1):
                if not self._outputs[out]._ready:
                    result = results[i]
                    meta = metadata[i] if metadata else None

                    subfolder = self._subfolders.get(id, "monitor")
                    filename = self._filenames.get(id, None)
                    writer = BasicImageWriter(result, meta, self.gui.outputDirectory(), subfolder, filename)
                    file = writer.file
                    QThreadPool.globalInstance().start(writer)

                    self._outputs[out].setResult(result, meta, file)
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

    @pyqtSlot(int, object)
    def response(self, id, response):
        if response["type"] == "hello":
            self._accept_all = False
        if response["type"] == "owner":
            self._accept_all = True
        if response["type"] == "ack":
            id = response["data"]["id"]
            queue = response["data"]["queue"]
            if id in self._ids and queue > 0:
                self.gui.setWaiting()
        
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
    def addSegment(self):
        self._inputs += [BasicInput(self, QImage(), BasicInputRole.SEGMENTATION)]
        self.updated.emit()

    @pyqtSlot()
    def addSubprompt(self):
        self._inputs += [BasicInput(self, QImage(), BasicInputRole.SUBPROMPT)]
        self.updated.emit()

    @pyqtSlot(str)
    def addControl(self, mode):
        i = BasicInput(self, QImage(), BasicInputRole.CONTROL)
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
            if i == 0 or curr._role in {BasicInputRole.IMAGE, BasicInputRole.SEGMENTATION}:
                curr.setLinked(None)
                continue
            prev = self._inputs[i-1]
            if prev._role == BasicInputRole.IMAGE:
                curr.setLinked(prev)
                continue
            if prev._linked:
                linked_roles = set([p.effectiveRole() for p in self._inputs if p._linked == prev._linked and p != curr])
                curr_role = curr.effectiveRole()
                if not curr_role in linked_roles or curr_role == BasicInputRole.CONTROL:
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
                    path = url.toLocalFile()
                    if os.path.isdir(path):
                        input = BasicInput(self, QImage(), BasicInputRole.IMAGE)
                        input.setFolder(url)
                        self._inputs.insert(index, input)
                    else:
                        self._inputs.insert(index, BasicInput(self, QImage(path), BasicInputRole.IMAGE))
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
            params = parameters.getParameters(image)
            if params:
                self.pastedText.emit(params)
        

    def download(self, url, index):
        self._replyIndex = index
        self._replyId = self.gui.network.download(url.fileName(), url)

    @pyqtSlot(misc.DownloadInstance)
    def onNetworkReply(self, reply):
        if reply._id != self._replyId or reply._error != "":
            return

        image = QImage()
        image.loadFromData(reply._reply.readAll())
        if not image.isNull():
            if self._replyIndex == None:
                self.pastedImage.emit(image)
                params = parameters.getParameters(image)
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
        if target._role in {BasicInputRole.IMAGE, BasicInputRole.CONTROL}:
            if target._paint.isNull():
                canvas.setupPainting(target._original)
            else:
                canvas.setupPainting(target._base, target._paint)
            return
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
        if target._role in {BasicInputRole.IMAGE, BasicInputRole.CONTROL}:
            image = canvas.getDisplay()
            base, paint = canvas.getImages()
            target.setPaintedData(image, base, paint)
            return
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
        annotator = input._control_settings.get("preprocessor")
        args = input.getControlArgs()

        request = self._parameters.buildAnnotateRequest(annotator, args, encodeImage(input._image))
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
        spaces = False

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
    
    def getSuggestions(self, text, onlyModels):
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
        
        if onlyModels:
            return staging
        
        for t in self._dictionary:
            tl = t.lower()

            if tl == text:
                continue

            i = -1
            try:
                i = tl.index(text)
            except:
                pass

            if i == 0:
                i = 1 - (len(text.split()[0])/len(tl.split()[0]))
            elif i > 0:
                i = 1 - (len(text)/len(tl))
            else:
                continue
            staging[t] = i

        return staging

    @pyqtSlot(str, int, bool)
    def updateSuggestions(self, text, pos, onlyModels):
        self._suggestions = []

        sensitivity = self.gui.config.get("autocomplete")
        self.vocabSync()

        before, _ = self.beforePos(text, pos)
        if before and sensitivity and len(before) >= sensitivity:
            staging = self.getSuggestions(before.lower(), onlyModels)
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
    
    @pyqtSlot(str, int, result=bool)
    def suggestionReplace(self, text, pos):
        text, _ = self.beforePos(text, pos)
        return len(text) > 1
    
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