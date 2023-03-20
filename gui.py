import os
import glob
import importlib

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QImage, QColor
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtWidgets import QFileDialog
from enum import Enum

import sql
import filesystem
import thumbnails
import backend

class StatusMode(Enum):
    STARTING = 0
    IDLE = 1
    WORKING = 2
    ERRORED = 3

class GUI(QObject):
    statusUpdated = pyqtSignal()
    errorUpdated = pyqtSignal()
    optionsUpdated = pyqtSignal()
    result = pyqtSignal(int)
    aboutToQuit = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        self.backend = backend.Backend(self)
        self.db = sql.Database(self)
        self.watcher = filesystem.Watcher()
        self.thumbnails = thumbnails.ThumbnailStorage((256, 256), 75, self)
        self.tabs = []

        self._id = 0

        self._statusMode = StatusMode.STARTING
        self._statusText = "Disconnected"
        self._statusProgress = -1.0
        self._statusInfo = ""

        self._errorStatus = ""
        self._errorText = ""

        self._options = {}

        parent.aboutToQuit.connect(self.stop)

        self.backend.response.connect(self.onResponse)

    @pyqtSlot()
    def stop(self):
        self.aboutToQuit.emit()
        self.backend.wait()
        self.watcher.wait()
    
    def registerTabs(self, tabs):
        self.tabs = tabs

    @pyqtProperty(list, constant=True)
    def tabSources(self):
        return [tab.source for tab in self.tabs]

    @pyqtProperty(list, constant=True)
    def tabNames(self): 
        return [tab.name for tab in self.tabs]

    @pyqtProperty('QString', constant=True)
    def title(self):
        return "qDiffusion"

    @pyqtSlot(str, result=bool)
    def isCached(self, file):
        return self.thumbnails.has(file)
    
    @pyqtProperty('QString', notify=statusUpdated)
    def statusText(self):
        return self._statusText
    
    @pyqtProperty(int, notify=statusUpdated)
    def statusMode(self):
        return self._statusMode.value
    
    @pyqtProperty('QString', notify=statusUpdated)
    def statusInfo(self):
        return self._statusInfo
    
    @pyqtProperty(float, notify=statusUpdated)
    def statusProgress(self):
        return self._statusProgress
    
    @pyqtProperty('QString', notify=errorUpdated)
    def errorText(self):
        return self._errorText
    
    @pyqtProperty('QString', notify=statusUpdated)
    def errorStatus(self):
        return self._errorStatus
    
    def makeRequest(self, request):
        self._id += 1024
        self.backend.makeRequest(self._id, request)
        return self._id
    
    @pyqtSlot(int, object)
    def onResponse(self, id, response):
        if response["type"] == "result":
            print({"type": "result", "data": {"metadata": response["data"]["metadata"]}})
        else:
            print(response)
        
        if response["type"] == "status":
            self._statusText = response["data"]["message"]
            if self._statusText == "Initializing":
                self._statusMode = StatusMode.STARTING
            elif self._statusText == "Ready":
                self._statusMode = StatusMode.IDLE
            else:
                self._statusMode = StatusMode.WORKING
            self.statusUpdated.emit()
        
        if response["type"] == "options":
            self._options = response["data"]
            self.optionsUpdated.emit()
            if self._statusText == "Initializing":
                self._statusMode = StatusMode.IDLE
                self._statusText = "Ready"
                self._statusProgress = -1.0
                self.statusUpdated.emit()

        if response["type"] == "error":
            self._errorStatus = self._statusText
            self._errorText = response["data"]["message"]
            self._statusText = "Errored"
            self._statusMode = StatusMode.ERRORED
            self.statusUpdated.emit()
            self.errorUpdated.emit()

        if response["type"] == "progress":
            self._statusProgress = response["data"]["current"]/response["data"]["total"]
            self._statusInfo = ""
            if response['data']['rate']:
                self._statusInfo = f"{response['data']['rate']:.2f}it/s"
            self.statusUpdated.emit()

        if response["type"] == "result":
            self._results = []
            for bytes in response["data"]["images"]:
                img = QImage()
                img.loadFromData(bytes, "png")
                self._results += [img]
            self.result.emit(id)

            self._statusMode = StatusMode.IDLE
            self._statusText = "Ready"
            self._statusInfo = ""
            self._statusProgress = -1.0
            self.statusUpdated.emit()

    @pyqtSlot()
    def clearError(self):
        self._statusMode = StatusMode.IDLE
        self._statusText = "Ready"
        self._statusProgress = -1.0
        self.statusUpdated.emit()

class FocusReleaser(QQuickItem):
    releaseFocus = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        self.setFlag(QQuickItem.ItemAcceptsInputMethod, True)
        self.setFiltersChildMouseEvents(True)
    
    def onPress(self, source):
        if not source.hasActiveFocus():
            self.releaseFocus.emit()

    def childMouseEventFilter(self, child, event):
        if event.type() == QEvent.MouseButtonPress:
            self.onPress(child)
        return False

    def mousePressEvent(self, event):
        self.onPress(self)
        event.setAccepted(False)

class ImageDisplay(QQuickPaintedItem):
    imageUpdated = pyqtSignal()
    sizeUpdated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image = None
        self._centered = False
        self._trueWidth = 0
        self._trueHeight = 0

    @pyqtProperty(QImage, notify=imageUpdated)
    def image(self):
        return self._image
    
    @image.setter
    def image(self, image):
        self._image = image

        self.setImplicitHeight(image.height())
        self.setImplicitWidth(image.width())
        self.imageUpdated.emit()

        self._trueWidth = 0
        self._trueHeight = 0
        self.sizeUpdated.emit()

        self.update()

    @pyqtProperty(bool, notify=imageUpdated)
    def centered(self):
        return self._centered
    
    @centered.setter
    def centered(self, centered):
        self._centered = centered
        self.imageUpdated.emit()
        self.update()

    @pyqtProperty(int, notify=sizeUpdated)
    def trueWidth(self):
        return self._trueWidth
    
    @pyqtProperty(int, notify=sizeUpdated)
    def trueHeight(self):
        return self._trueHeight

    def paint(self, painter):
        if self._image and not self._image.isNull():
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._trueWidth = img.width()
            self._trueHeight = img.height()
            self.sizeUpdated.emit()
            x, y = 0, 0
            if self.centered:
                x = int((self.width() - img.width())/2)
                y = int((self.height() - img.height())//2)
            painter.drawImage(x,y,img)

class MimeData(QObject):
    def __init__(self, mimeData, parent=None):
        super().__init__(parent)
        self._mimeData = mimeData

    @pyqtProperty(QMimeData)
    def mimeData(self):
        return self._mimeData

class DropArea(QQuickItem):
    dropped = pyqtSignal(MimeData, arguments=["mimeData"])
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFlag(QQuickItem.ItemAcceptsDrops, True)
        self._containsDrag = False
    
    @pyqtProperty(bool, notify=updated)
    def containsDrag(self):
        return self._containsDrag
    
    def dragEnterEvent(self, enter): 
        enter.accept()
        self._containsDrag = True
        self.updated.emit()

    def dragLeaveEvent(self, leave): 
        leave.accept()
        self._containsDrag = False
        self.updated.emit()

    def dragMoveEvent(self, move):
        move.accept()

    def dropEvent(self, drop):
        drop.accept()
        self._containsDrag = False
        self.updated.emit()
        self.dropped.emit(MimeData(drop.mimeData()))

def registerTypes():
    qmlRegisterType(ImageDisplay, "gui", 1, 0, "ImageDisplay")
    qmlRegisterType(FocusReleaser, "gui", 1, 0, "FocusReleaser")
    qmlRegisterType(DropArea, "gui", 1, 0, "AdvancedDropArea")
    qmlRegisterType(MimeData, "gui", 1, 0, "MimeData")