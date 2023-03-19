from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QUrl, QMimeData, QByteArray, QBuffer, Qt, QRegExp, QIODevice
from PyQt5.QtQml import qmlRegisterSingletonType
from PyQt5.QtGui import QImage, QDrag, QPixmap, QSyntaxHighlighter, QTextCharFormat, QFont
from PyQt5.QtQuick import QQuickTextDocument
from enum import Enum

import parameters
import re
from gui import MimeData

MIME_BASIC_INPUT = "application/x-qd-basic-input"
MIME_BASIC_OUTPUT = "application/x-qd-basic-output"

class BasicInputRole(Enum):
    IMAGE = 1
    MASK = 2

class BasicInput(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, image=QImage(), role=BasicInputRole.IMAGE):
        super().__init__(parent)
        self._image = image
        self._role = role
        self._linked = None
        self._dragging = False
    
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

    @pyqtProperty(bool, notify=updated)
    def linked(self):
        return self._linked != None and not self._linked.empty

    @pyqtProperty(QImage, notify=updated)
    def linkedImage(self):
        if not self._linked:
            return QImage()
        return self._linked._image
    
    @pyqtProperty(int, notify=updated)
    def linkedWidth(self):
        if not self._linked:
            return 0
        return self._linked._image.width()
    
    @pyqtProperty(int, notify=updated)
    def linkedHeight(self):
        if not self._linked:
            return 0
        return self._linked._image.height()
        
    @pyqtProperty(str, notify=updated)
    def size(self):
        if self._image.isNull():
            return ""
        return f"{self._image.width()}x{self._image.height()}"

    @pyqtSlot(QUrl)
    def setImageFile(self, path):
        self._image = QImage(path.toLocalFile())
        self.updated.emit()
        self.parent().updated.emit()

    @pyqtSlot()
    def setImageCanvas(self):
        self._image = QImage(self._linked._image.size(), QImage.Format_ARGB32_Premultiplied)
        self._image.fill(0)
        self.updated.emit()
        self.parent().updated.emit()

    @pyqtSlot(MimeData, int)
    def setImageDrop(self, mimeData, index):
        mimeData = mimeData.mimeData
        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
            destination = index
            self.parent().swapItem(source, destination)
        elif MIME_BASIC_OUTPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_OUTPUT), 'utf-8'))
            self._image = QImage(self.parent()._outputs[source]._image)
        else:
            source = mimeData.imageData()
            if source and not source.isNull():
                self._image = source
            for url in mimeData.urls():
                if url.isLocalFile():
                     self._image = QImage(url.toLocalFile())
        self.updated.emit()
        self.parent().updated.emit()

    @pyqtSlot(QImage)
    def setImageData(self, data):
        self._image = data
        self.updated.emit()
        self.parent().updated.emit()

    @pyqtSlot()
    def clearImage(self):
        self._image = QImage()
        self.updated.emit()
        self.parent().updated.emit()

    @pyqtSlot(int, QImage)
    def drag(self, index, image):
        if self._dragging:
            return
        self._dragging = True
        drag = QDrag(self)
        drag.setPixmap(QPixmap.fromImage(image).scaledToWidth(50, Qt.SmoothTransformation))
        mimeData = QMimeData()
        mimeData.setData(MIME_BASIC_INPUT, QByteArray(f"{index}".encode()))

        drag.setMimeData(mimeData)
        drag.exec()
        self._dragging = False

class BasicOutput(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, image=QImage()):
        super().__init__(parent)
        self._image = image
        self._dragging = False

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

    @pyqtSlot(int, QImage)
    def drag(self, index, image):
        if self._dragging:
            return
        self._dragging = True
        drag = QDrag(self)
        drag.setPixmap(QPixmap.fromImage(image).scaledToWidth(50, Qt.SmoothTransformation))
        mimeData = QMimeData()
        mimeData.setData(MIME_BASIC_OUTPUT, QByteArray(f"{index}".encode()))
        drag.setMimeData(mimeData)
        drag.exec()
        self._dragging = False

class SyntaxHighlighter(QSyntaxHighlighter):
    def highlightBlock(self, text):
        brackets = QTextCharFormat()
        brackets.setForeground(Qt.red)
        brackets.setFontWeight(65)

        occ = {'(': [], '{': [], '<': [], '[': []}
        rev = {')': '(', '}': '{', '>': '<', ']': '['}

        for i, c in enumerate(text):
            if c in "({<[":
                occ[c] += [i]
            if c in rev:
                if occ[rev[c]]:
                    occ[rev[c]].pop()
                else:
                    self.setFormat(i, 1, brackets)
            
        for b in occ:
            for i in occ[b]:
                self.setFormat(i, 1, brackets)

class Basic(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.gui = parent
        self.priority = 0
        self.name = "Basic"
        self._parameters = parameters.Parameters(parent)
        self._inputs = []
        self._outputs = []
        self._links = {}
        self._id = -1

        self.updated.connect(self.link)
        self.gui.result.connect(self.result)

        qmlRegisterSingletonType(Basic, "gui", 1, 0, "BASIC", lambda qml, js: self)

    @pyqtSlot(str, str)
    def generate(self, positive, negative):
        request = {"data": {}}

        if self._inputs:
            request["type"] = "img2img"
            request["data"]["image"] = []
            request["data"]["mask"] = []
            for i in self._inputs:
                img = i._image
                if img.isNull():
                    continue

                if i._role == BasicInputRole.MASK:
                    img.save("BASIC.png")
                    
                ba = QByteArray()
                bf = QBuffer(ba)
                bf.open(QIODevice.WriteOnly)
                img.save(bf, "PNG")
                data = ba.data()

                if i._role == BasicInputRole.IMAGE:
                    request["data"]["image"] += [data]
                if i._role == BasicInputRole.MASK and i._linked:
                    request["data"]["mask"] += [data]
                
        else:
            request["type"] = "txt2img"

        for k, v in self._parameters._values._map.items():
            if not k in ["models", "samplers"]:
                request["data"][k] = v
        request["data"]["prompt"] = positive
        request["data"]["negative_prompt"] = negative
        request["data"]["seed"] = 102

        self._id = self.gui.makeRequest(request)

    @pyqtSlot(int)
    def result(self, id):
        if self._id != id:
            return
        for r in self.gui._results:
            self._outputs = [BasicOutput(self, r)] + self._outputs
        self.updated.emit()

    @pyqtProperty(parameters.Parameters, notify=updated)
    def parameters(self):
        return self._parameters

    @pyqtProperty(list, notify=updated)
    def inputs(self):
        return self._inputs

    @pyqtProperty(list, notify=updated)
    def outputs(self):
        return self._outputs

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
                self._inputs[i]._linked = self._inputs[i-1]
            else:
                self._inputs[i]._linked = None
            self._inputs[i].updated.emit()

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
        elif MIME_BASIC_OUTPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_OUTPUT), 'utf-8'))
            self._inputs.insert(index, BasicInput(self, QImage(self._outputs[source]._image), BasicInputRole.IMAGE))
        else:
            source = mimeData.imageData()
            if source and not source.isNull():
                self._inputs.insert(index, BasicInput(self, source, BasicInputRole.IMAGE))

            for url in mimeData.urls():
                if url.isLocalFile():
                    source = QImage(url.toLocalFile())
                    self._inputs.insert(index, BasicInput(self, source, BasicInputRole.IMAGE))
        self.updated.emit()

    @pyqtSlot(int)
    def deleteInput(self, index):
        self._inputs.pop(index)
        self.updated.emit()

    @pyqtSlot(int)
    def deleteOutput(self, index):
        self._outputs.pop(index)
        self.updated.emit()

    @pyqtSlot(QQuickTextDocument)
    def setHighlighting(self, doc):
        highlighter = SyntaxHighlighter(self)
        highlighter.setDocument(doc.textDocument())
