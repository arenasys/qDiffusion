import os

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData, QUrl
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QImage, QColor, QDrag
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from enum import Enum

import sql
import filesystem
import thumbnails
import backend
import config
from parameters import VariantMap

class StatusMode(Enum):
    STARTING = 0
    IDLE = 1
    WORKING = 2
    ERRORED = 3

class RemoteStatusMode(Enum):
    INACTIVE = 0
    CONNECTING = 1
    CONNECTED = 2
    ERRORED = 3

class GUI(QObject):
    statusUpdated = pyqtSignal()
    errorUpdated = pyqtSignal()
    optionsUpdated = pyqtSignal()
    result = pyqtSignal(int)
    aboutToQuit = pyqtSignal()
    networkReply = pyqtSignal(QNetworkReply)
    remoteUpdated = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.db = sql.Database(self)
        self.watcher = filesystem.Watcher()
        self.thumbnails = thumbnails.ThumbnailStorage((256, 256), 75, self)
        self.network = QNetworkAccessManager(self)
        self.requestProgress = 0.0
        self.tabs = []

        self._id = 0

        self._statusMode = StatusMode.STARTING
        self._statusText = "Disconnected"
        self._statusProgress = -1.0
        self._statusInfo = ""

        self._errorStatus = ""
        self._errorText = ""

        self._config = config.Config(self, "config.json", {"endpoint": "", "password": ""})
        self._remoteStatus = RemoteStatusMode.INACTIVE

        self.backend = backend.Backend(self, self._config._values.get("endpoint"), self._config._values.get("password"))

        self._options = {}

        self._modelFolders = [os.path.join("models", f) for f in ["SD", "LoRA", "HN", "SR", "TI"]]
        for folder in self._modelFolders:
            self.watcher.watchFolder(folder)
        self._trashFolder = os.path.join("models", "TRASH")

        parent.aboutToQuit.connect(self.stop)

        self.backend.response.connect(self.onResponse)
        self.watcher.finished.connect(self.onFolderChanged)
        self.network.finished.connect(self.onNetworkReply)
    


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
        if self.requestProgress > 0:
            return "Downloading"
        return self._statusText
    
    @pyqtProperty(int, notify=statusUpdated)
    def statusMode(self):
        if self.requestProgress > 0:
            return StatusMode.WORKING.value
        return self._statusMode.value
    
    @pyqtProperty('QString', notify=statusUpdated)
    def statusInfo(self):
        return self._statusInfo
    
    @pyqtProperty(float, notify=statusUpdated)
    def statusProgress(self):
        if self.requestProgress > 0:
            return self.requestProgress
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

    def cancelRequest(self, id):
        self.backend.cancelRequest(id)

    def setReady(self):
        self._statusMode = StatusMode.IDLE
        self._statusInfo = ""
        self._statusText = "Ready"
        self._statusProgress = -1.0
        self.statusUpdated.emit()
    
    @pyqtSlot(int, object)
    def onResponse(self, id, response):       
        if response["type"] == "status":
            self._statusText = response["data"]["message"]
            if self._statusText == "Initializing" or self._statusText == "Connecting":
                self._remoteStatus = RemoteStatusMode.CONNECTING
                self._statusMode = StatusMode.STARTING
            elif self._statusText == "Ready" or self._statusText == "Connected":
                self._statusText = "Ready"
                self._remoteStatus = RemoteStatusMode.CONNECTED
                self._statusMode = StatusMode.IDLE
            else:
                self._statusProgress = -1.0
                self._statusMode = StatusMode.WORKING
            self.statusUpdated.emit()

        if response["type"] == "done":
            self.setReady()

        if response["type"] == "options":
            self._options = response["data"]
            self.optionsUpdated.emit()
            if self._statusText == "Initializing":
                self.setReady()

        if response["type"] == "error":
            self._errorStatus = self._statusText
            self._errorText = response["data"]["message"]
            self.statusUpdated.emit()
            self.errorUpdated.emit()

        if response["type"] == "aborted":
            self.setReady()

        if response["type"] == "progress":
            self._statusProgress = response["data"]["current"]/response["data"]["total"]
            self._statusInfo = ""
            if response['data']['rate']:
                self._statusInfo = f"{response['data']['rate']:.2f}it/s"
            self.statusUpdated.emit()

        if response["type"] == "result":
            self._results = []
            for i, bytes in enumerate(response["data"]["images"]):
                img = QImage()
                img.loadFromData(bytes, "png")
                self._results += [{"image": img, "metadata": response["data"]["metadata"][i]}]
            self.result.emit(id)
            self.setReady()
    
    @pyqtSlot(str, int)
    def onFolderChanged(self, folder, total):
        if folder in self._modelFolders:
            if folder == self._modelFolders[0]:
                self.backend.makeRequest(-1, {"type":"convert", "data":{"model_folder": self._modelFolders[0], "trash_folder":self._trashFolder}})
            self.backend.makeRequest(-1, {"type":"options"})
            return

    @pyqtSlot()
    def clearError(self):
        if self._statusMode != StatusMode.STARTING:
            self._statusText = "Ready"
            self._statusMode = StatusMode.IDLE
        self._statusProgress = -1.0
        self.statusUpdated.emit()

    @pyqtSlot(QNetworkRequest)
    def makeNetworkRequest(self, request):
        reply = self.network.get(request)
        reply.downloadProgress.connect(self.onNetworkProgress)
        self.requestProgress = 0.001
        self.statusUpdated.emit()

    @pyqtSlot(QNetworkReply)
    def onNetworkReply(self, reply):
        self.networkReply.emit(reply)
        self.requestProgress = 0.0
        self.statusUpdated.emit()

    @pyqtSlot('qint64', 'qint64')
    def onNetworkProgress(self, current, total):
        self.requestProgress = max(self.requestProgress, current/total)
        self.statusUpdated.emit()

    def getFilesMimeData(self, files):
        urls = [QUrl.fromLocalFile(os.path.abspath(file)) for file in files]
        mimedata = QMimeData()
        mimedata.setUrls(urls)

        gnome = "copy\n"+'\n'.join(["file://"+url.toLocalFile() for url in urls])
        mimedata.setData("x-special/gnome-copied-files", gnome.encode("utf-8"))
        return mimedata

    def copyFiles(self, files):
        QApplication.clipboard().setMimeData(self.getFilesMimeData(files))

    def dragFiles(self, files):
        drag = QDrag(self)
        drag.setMimeData(self.getFilesMimeData(files))
        drag.exec()
    
    @pyqtProperty(VariantMap, notify=remoteUpdated)
    def config(self):
        return self._config._values
    
    @pyqtProperty(str, notify=remoteUpdated)
    def remoteEndpoint(self):
        endpoint = self._config._values.get("endpoint")
        if not endpoint:
            return "Local"
        return endpoint
    
    @pyqtSlot()
    def restartBackend(self):
        endpoint = self._config._values.get("endpoint")
        password = self._config._values.get("password")
        self.remoteUpdated.emit()

        self._statusMode = StatusMode.STARTING
        self._statusProgress = -1
        self._statusText = "Restarting"
        self.backend.stop()
        self.backend.wait()
        self.backend.setEndpoint(endpoint, password)

class FocusReleaser(QQuickItem):
    releaseFocus = pyqtSignal()
    dropped = pyqtSignal()
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
        self._last = None
        self._image = image

        self.setImplicitHeight(image.height())
        self.setImplicitWidth(image.width())
        self.imageUpdated.emit()

        if self._image and not self._image.isNull():
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio)
            if self._trueWidth != img.width() or self._trueHeight != img.height():
                self._trueWidth = img.width()
                self._trueHeight = img.height()
                self.sizeUpdated.emit()
        else:
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

    @pyqtProperty(int, notify=imageUpdated)
    def sourceWidth(self):
        if self._image:
            return self._image.width()
        return 0
    
    @pyqtProperty(int, notify=imageUpdated)
    def sourceHeight(self):
        if self._image:
            return self._image.height()
        return 0

    def paint(self, painter):
        if self._image and not self._image.isNull():
            transform = Qt.SmoothTransformation
            if not self.smooth():
                transform = Qt.FastTransformation

            # FIX THIS CRAP
            img = self._image.scaled(int(self.width()), int(self.height()), Qt.KeepAspectRatio, transform)
            if self._trueWidth != img.width() or self._trueHeight != img.height():
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