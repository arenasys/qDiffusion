from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QUrl, QMimeData, QByteArray, QBuffer, Qt, QRegExp, QIODevice, QRect
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtGui import QImage, QDrag, QPixmap
from PyQt5.QtWidgets import QApplication
from PyQt5.QtSql import QSqlQuery
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply
from enum import Enum

import parameters
import re
from misc import MimeData, SyntaxHighlighter
from canvas.shared import PILtoQImage, QImagetoPIL
import sql
import time
import json

MIME_BASIC_INPUT = "application/x-qd-basic-input"

class BasicInputRole(Enum):
    IMAGE = 1
    MASK = 2

class BasicInput(QObject):
    updated = pyqtSignal()
    linkedUpdated = pyqtSignal()
    extentUpdated = pyqtSignal()
    def __init__(self, parent=None, image=QImage(), role=BasicInputRole.IMAGE):
        super().__init__(parent)
        self._image = image
        self._role = role
        self._linked = None
        self._dragging = False
        self._extent = QRect()
        self._extentWarning = False

        parent.parameters._values.updated.connect(self.updateExtent)

    def updateImage(self):
        if self._image and not self._image.isNull() and self._linked and self._linked.image and not self._linked.image.isNull():
            bg = self._linked.image
            image = self._image.scaled(bg.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            dx = int((image.width()-bg.width())//2)
            dy = int((image.height()-bg.height())//2)
            self._image = image.copy(dx, dy, bg.size().width(), bg.size().height())
        self.updateExtent()
        self.updated.emit()

    def setLinked(self, linked):
        if self._linked:
            self._linked.updated.disconnect(self.updateImage)
        
        self._linked = linked
        if self._linked:
            self._linked.updated.connect(self.updateImage)
        
        self.updateImage()
        self.linkedUpdated.emit()
    
    @pyqtProperty(int, notify=updated)
    def role(self):
        return self._role.value

    @role.setter
    def role(self, role):
        self._role = BasicInputRole(role)
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

    @pyqtProperty(bool, notify=updated)
    def empty(self):
        return self._image.isNull()

    @pyqtProperty(bool, notify=linkedUpdated)
    def linked(self):
        return self._linked != None and not self._linked.empty

    @pyqtProperty(QImage, notify=linkedUpdated)
    def linkedImage(self):
        if not self._linked:
            return QImage()
        return self._linked._image
    
    @pyqtProperty(int, notify=linkedUpdated)
    def linkedWidth(self):
        if not self._linked:
            return 0
        return self._linked._image.width()
    
    @pyqtProperty(int, notify=linkedUpdated)
    def linkedHeight(self):
        if not self._linked:
            return 0
        return self._linked._image.height()
        
    @pyqtProperty(str, notify=updated)
    def size(self):
        if self._image.isNull():
            return ""
        return f"{self._image.width()}x{self._image.height()}"
    
    @pyqtProperty(QRect, notify=extentUpdated)
    def extent(self):
        return self._extent
    
    @pyqtProperty(bool, notify=extentUpdated)
    def extentWarning(self):
        return self._extentWarning
    
    @pyqtSlot(QUrl)
    def setImageFile(self, path):
        self._image = QImage(path.toLocalFile())
        self.updateImage()

    @pyqtSlot()
    def setImageCanvas(self):
        self._image = QImage(self._linked._image.size(), QImage.Format_ARGB32_Premultiplied)
        self._image.fill(0)
        self.updateImage()

    @pyqtSlot(MimeData, int)
    def setImageDrop(self, mimeData, index):
        mimeData = mimeData.mimeData
        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
            destination = index
            self.parent().swapItem(source, destination)
        else:
            source = mimeData.imageData()
            if source and not source.isNull():
                self._image = source
            for url in mimeData.urls():
                if url.isLocalFile():
                     self._image = QImage(url.toLocalFile())
        self.updateImage()

    @pyqtSlot(QImage)
    def setImageData(self, data):
        self._image = data
        self.updateImage()

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

    @pyqtSlot(int, QImage)
    def drag(self, index, image):
        if self._dragging:
            return
        self._dragging = True
        drag = QDrag(self)
        drag.setPixmap(QPixmap.fromImage(image).scaledToWidth(50, Qt.SmoothTransformation))
        mimeData = QMimeData()
        mimeData.setData(MIME_BASIC_INPUT, QByteArray(f"{index}".encode()))
        mimeData.setImageData(self._image)

        drag.setMimeData(mimeData)
        drag.exec()
        self._dragging = False

class BasicOutput(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, image=QImage(), metadata={}):
        super().__init__(parent)
        self.basic = parent
        self._image = image
        self._metadata = metadata
        self._file = metadata["file"]
        self._parameters = parameters.format_parameters(self._metadata)
        self._dragging = False
        self._image.setText("parameters", self._parameters)

    @pyqtProperty(QImage, notify=updated)
    def image(self):
        return self._image
    
    @pyqtProperty(int, notify=updated)
    def width(self):
        return self._image.width()
    
    @pyqtProperty(int, notify=updated)
    def height(self):
        return self._image.height()

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

    @pyqtSlot(int, QImage)
    def drag(self, id, image):
        self.basic.gui.dragFiles([self._file])

class Basic(QObject):
    updated = pyqtSignal()
    results = pyqtSignal()
    pastedText = pyqtSignal(str)
    pastedImage = pyqtSignal(QImage)
    openedUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.priority = 0
        self.name = "Basic"
        self._parameters = parameters.Parameters(parent)
        self._inputs = []
        self._outputs = {}
        self._links = {}
        self._ids = []
        self._forever = False

        self._openedIndex = -1
        self._openedArea = ""

        self.updated.connect(self.link)
        self.gui.result.connect(self.result)
        self.gui.reset.connect(self.reset)
        self.gui.networkReply.connect(self.onNetworkReply)

        qmlRegisterSingletonType(Basic, "gui", 1, 0, "BASIC", lambda qml, js: self)

        self.conn = sql.Connection(self)
        self.conn.connect()
        self.conn.doQuery("CREATE TABLE outputs(id INTEGER);")
        self.conn.enableNotifications("outputs")

    def buildRequest(self):
        images = []
        masks = []
        if self._inputs:
            for i in self._inputs:
                img = i._image
                if img.isNull():
                    continue
                    
                ba = QByteArray()
                bf = QBuffer(ba)
                bf.open(QIODevice.WriteOnly)
                img.save(bf, "PNG")
                img_data = ba.data()

                if i._role == BasicInputRole.IMAGE:
                    images += [img_data]
                if i._role == BasicInputRole.MASK and i._linked:
                    masks += [img_data]

        request = self._parameters.buildRequest(images, masks)
        return request

    @pyqtSlot()
    def generate(self):
        if not self._ids:
            request = self.buildRequest()
            self._ids += [self.gui.makeRequest(request)]

    @pyqtSlot(int)
    def result(self, id):
        if not id in self._ids:
            return
        self._ids.remove(id)
        
        id = (time.time_ns() // 1000000) % (2**31 - 1)

        sticky = self.isSticky()
        for i in range(len(self.gui._results)-1, -1, -1):
            img = self.gui._results[i]["image"]
            metadata = self.gui._results[i]["metadata"]
            self._outputs[id] = BasicOutput(self, img, metadata)
            q = QSqlQuery(self.conn.db)
            q.prepare("INSERT INTO outputs(id) VALUES (:id);")
            q.bindValue(":id", id)
            self.conn.doQuery(q)
            id += 1
        if self._forever:
            self.generate()
        self.updated.emit()
        self.results.emit()
        if sticky:
            self.left()
        
    @pyqtSlot()
    def reset(self):
        self._ids = []

    @pyqtSlot()
    def cancel(self):
        if self._ids:
            self.gui.cancelRequest(self._ids.pop())

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
        self._inputs += [BasicInput(self, QImage(), BasicInputRole.IMAGE)]
        self.updated.emit()

    @pyqtSlot()
    def addMask(self):
        self._inputs += [BasicInput(self, QImage(), BasicInputRole.MASK)]
        self.updated.emit()

    @pyqtSlot()
    def link(self):
        for i in range(len(self._inputs)):
            if i != 0 and self._inputs[i]._role == BasicInputRole.MASK and self._inputs[i-1]._role == BasicInputRole.IMAGE:
                self._inputs[i].setLinked(self._inputs[i-1])
            else:
                self._inputs[i].setLinked(None)

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
            source = mimeData.imageData()
            if source and not source.isNull():
                self._inputs.insert(index, BasicInput(self, source, BasicInputRole.IMAGE))
            for url in mimeData.urls():
                if url.isLocalFile():
                    source = QImage(url.toLocalFile())
                    self._inputs.insert(index, BasicInput(self, source, BasicInputRole.IMAGE))
        self.updated.emit()

    @pyqtSlot(MimeData)
    def sizeDrop(self, mimeData):
        mimeData = mimeData.mimeData
        width,height = None,None
        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
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
        return self.outputIDToIndex(self._openedIndex) == 0 
        
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
        
        if mimedata.hasImage():
            image = mimedata.imageData()
            if image and not image.isNull():
                self.pastedImage.emit(image)
                params = image.text("parameters")
                if params:
                    self.pastedText.emit(params)

        for url in mimedata.urls():
            if url.isLocalFile():
                image = QImage(url.toLocalFile())
                self.pastedImage.emit(image)
                params = image.text("parameters")
                if params:
                    self.pastedText.emit(params)
            elif url.scheme() == "http" or url.scheme() == "https":
                if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                    self.gui.makeNetworkRequest(QNetworkRequest(url))

    @pyqtSlot(QNetworkReply)
    def onNetworkReply(self, reply):
        image = QImage()
        image.loadFromData(reply.readAll())
        if not image.isNull():
            self.pastedImage.emit(image)
            params = image.text("parameters")
            if params:
                self.pastedText.emit(params)
        self.updated.emit()

    @pyqtSlot(int, str)
    def copyItem(self, index, area):
        if area == "input":
            mimeData = QMimeData()
            mimeData.setImageData(self._inputs[index]._image)
            QApplication.clipboard().setMimeData(mimeData)
        else:
            mimeData = QMimeData()
            mimeData.setImageData(self._outputs[index]._image)
            QApplication.clipboard().setMimeData(mimeData)

    @pyqtSlot(int, str)
    def pasteItem(self, index, area):
        if area == "input":
            inputs = []
            if index == -1:
                index = len(self._inputs)

            mimedata = QApplication.clipboard().mimeData()
            if mimedata.hasImage():
                image = mimedata.imageData()
                if image and not image.isNull():
                    inputs += [BasicInput(self, image)]

            for url in mimedata.urls():
                if url.isLocalFile():
                    image = QImage(url.toLocalFile())
                    inputs += [BasicInput(self, image)]
                elif url.scheme() == "http" or url.scheme() == "https":
                    if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                        self.gui.makeNetworkRequest(QNetworkRequest(url))
                        self.replyInsert = index

            for i in inputs[::-1]:
                self._inputs.insert(index, i)
            self.updated.emit()

    @pyqtSlot(list)
    def importParameters(self, params):
        self._parameters.importParameters(params)