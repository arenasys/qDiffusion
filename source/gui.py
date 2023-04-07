import os
import random
import subprocess
import datetime
import json
import bson
import platform
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData, QUrl
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QImage, QColor, QDrag
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtWidgets import QApplication
from PyQt5.QtNetwork import QNetworkRequest, QNetworkReply, QNetworkAccessManager
from PyQt5.QtQuick import QQuickTextDocument
from enum import Enum

import sql
import filesystem
import thumbnails
import backend
import config
from misc import SyntaxHighlighter
from parameters import VariantMap

NAME = "qDiffusion"

class StatusMode(Enum):
    STARTING = 0
    IDLE = 1
    WORKING = 2
    ERRORED = 3
    INACTIVE = 4

class RemoteStatusMode(Enum):
    INACTIVE = 0
    CONNECTING = 1
    CONNECTED = 2
    ERRORED = 3

def get_id():
    return random.SystemRandom().randint(1, 2**31 - 1)

class GUI(QObject):
    statusUpdated = pyqtSignal()
    errorUpdated = pyqtSignal()
    optionsUpdated = pyqtSignal()
    result = pyqtSignal(int)
    response = pyqtSignal(int, object)
    aboutToQuit = pyqtSignal()
    networkReply = pyqtSignal(QNetworkReply)
    reset = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.db = sql.Database(self)
        self.watcher = filesystem.Watcher()
        self.thumbnails = thumbnails.ThumbnailStorage((256, 256), 75, self)
        self.network = QNetworkAccessManager(self)
        self.requestProgress = 0.0
        self.tabs = []

        self._statusMode = StatusMode.STARTING
        self._statusText = "Inactive"
        self._statusProgress = -1.0
        self._statusInfo = ""

        self._errorStatus = ""
        self._errorText = ""

        self._config = config.Config(self, "config.json", {"endpoint": "", "password": "", "output_directory":"outputs", "model_directory":"models"})
        self._remoteStatus = RemoteStatusMode.INACTIVE

        self._output_directory = self._config._values.get("output_directory")
        self._model_directory = self._config._values.get("model_directory")

        self._modelFolders = []

        self._debugJSONLogging = self._config._values.get("debug") == True

        self.backend = backend.Backend(self)
        self.backend.response.connect(self.onResponse)
        self.backend.setEndpoint(self._config._values.get("endpoint"), self._config._values.get("password"))

        self.watchModelDirectory()

        self._options = {}

        parent.aboutToQuit.connect(self.stop)

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

    @pyqtProperty('QString', notify=statusUpdated)
    def title(self):
        if self._remoteStatus != RemoteStatusMode.INACTIVE:
            return NAME + ": Remote"
        return NAME

    @pyqtSlot(str, result=bool)
    def isCached(self, file):
        return self.thumbnails.has(file)
    
    @pyqtProperty('QString', notify=statusUpdated)
    def statusText(self):
        if self.requestProgress > 0:
            return "Downloading"
        if self._remoteStatus == RemoteStatusMode.ERRORED:
            return "Errored"
        return self._statusText
    
    @pyqtProperty(int, notify=statusUpdated)
    def statusMode(self):
        if self.requestProgress > 0:
            return StatusMode.WORKING.value
        if self._remoteStatus == RemoteStatusMode.ERRORED:
            return StatusMode.ERRORED.value
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
        id = get_id()
        request["id"] = id
        self.backend.makeRequest(request)
        return id

    def cancelRequest(self, id):
        if id:
            self.backend.makeRequest({"type":"cancel", "data":{"id": id}})

    def setReady(self):
        self._statusMode = StatusMode.IDLE
        self._statusInfo = ""
        self._statusText = "Ready"
        self._statusProgress = -1.0
        self.statusUpdated.emit()
    
    @pyqtSlot(object)
    def onResponse(self, response):
        id = -1
        if "id" in response:
            id = response["id"]

        if response["type"] == "status":
            self._statusText = response["data"]["message"]
            self._statusInfo = ""
            if self._statusText == "Initializing" or self._statusText == "Connecting":
                if self._statusText == "Connecting":
                    self._remoteStatus = RemoteStatusMode.CONNECTING
                self._statusMode = StatusMode.STARTING
                self.watchModelDirectory()
            elif self._statusText == "Ready" or self._statusText == "Connected":
                if self._statusText == "Connected":
                    self._remoteStatus = RemoteStatusMode.CONNECTED
                self._statusText = "Ready"
                self._statusMode = StatusMode.IDLE
            else:
                self._statusProgress = -1.0
                self._statusMode = StatusMode.WORKING
            self.statusUpdated.emit()

        if response["type"] == "remote_only":
            self._statusText = "Inactive"
            self._statusProgress = -1.0
            self._statusMode = StatusMode.INACTIVE
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
            if "traceback" in response["data"]:
                with open("crash.log", "a") as f:
                    f.write(f"INFERENCE {datetime.datetime.now()}\n{response['data']['traceback']}\n")

        if response["type"] == "remote_error":
            self._errorStatus = self._statusText
            self._errorText = response["data"]["message"]
            self._remoteStatus = RemoteStatusMode.ERRORED
            self.backend.stop()
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

        self.response.emit(id, response)
    
    @pyqtSlot(str, int)
    def onFolderChanged(self, folder, total):
        if folder in self._modelFolders:
            self.refreshModels()
            return

    @pyqtSlot()
    def refreshModels(self):
        self.backend.makeRequest({"type":"options"})

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

    def copyText(self, text):
        QApplication.clipboard().setText(text)

    def dragFiles(self, files):
        drag = QDrag(self)
        drag.setMimeData(self.getFilesMimeData(files))
        drag.exec()
    
    @pyqtProperty(VariantMap, constant=True)
    def config(self):
        return self._config._values
    
    @pyqtProperty(str, notify=statusUpdated)
    def remoteEndpoint(self):
        endpoint = self._config._values.get("endpoint")
        if not endpoint:
            return "Local"
        return endpoint
    
    @pyqtProperty(int, notify=statusUpdated)
    def remoteStatus(self):
        return self._remoteStatus.value
    
    @pyqtProperty(str, notify=statusUpdated)
    def remoteInfo(self):
        endpoint = self._config._values.get("endpoint")
        
        mode = ""
        status = ""
        if endpoint:
            mode = "Remote"
            if self._remoteStatus == RemoteStatusMode.CONNECTING:
                status = "Connecting"
            elif self._remoteStatus == RemoteStatusMode.ERRORED:
                status = "Errored"
            else:
                status = "Connected"
        else:
            mode = "Local"
            if self._statusMode == StatusMode.STARTING:
                status = "Initializing"
            elif self._statusMode == StatusMode.INACTIVE:
                status = "Inactive"
            else:
                status = "Ready"

        return mode + ", " + status

    @pyqtSlot()
    def restartBackend(self):
        endpoint = self._config._values.get("endpoint")
        password = self._config._values.get("password")

        if endpoint:
            self._remoteStatus = RemoteStatusMode.CONNECTING
        else:
            self._remoteStatus = RemoteStatusMode.INACTIVE

        self._statusMode = StatusMode.STARTING
        self._statusProgress = -1
        self._statusText = "Restarting"
        self.statusUpdated.emit()
        self.backend.stop()
        self.backend.wait()
        self.backend.setEndpoint(endpoint, password)
        self.reset.emit()

    @pyqtSlot(str, str)
    def remoteDownload(self, type, url):
        if self._remoteStatus != RemoteStatusMode.CONNECTED:
            return
        
        self.backend.makeRequest({"type":"download", "data":{"type": type, "url":url}})

    @pyqtSlot(str, str)
    def remoteUpload(self, type, file):
        if self._remoteStatus != RemoteStatusMode.CONNECTED:
            return
        
        self.backend.makeRequest({"type":"upload", "data":{"type": type, "file":file}})

    @pyqtSlot(QQuickTextDocument)
    def setHighlighting(self, doc):
        highlighter = SyntaxHighlighter(self)
        highlighter.setDocument(doc.textDocument())

    @pyqtSlot(str, bool)
    def debugLogging(self, mode, enabled):
        if mode == "json":
            self._debugJSONLogging = enabled
        if mode == "bin":
            self._debugBINLogging = enabled

    @pyqtSlot()
    def debugRequest(self):
        try:
            mimedata = QApplication.clipboard().mimeData()
            if mimedata.hasText():
                text = mimedata.text()
                request = json.loads(text)
                self.makeRequest(request)
            elif mimedata.hasUrls():
                for url in mimedata.urls():
                    if url.isLocalFile() and url.endswith(".bin"):
                        with open(url.toLocalFile(), mode="rb") as f:
                            data = f.read()
                            request = bson.loads(data)
                            self.makeRequest(request)
                            break
        except Exception as e:
                self._errorStatus = "DEBUG"
                self._errorText = str(e)
                self.errorUpdated.emit()
    
    @pyqtSlot()
    def watchModelDirectory(self):
        modelFolders = [os.path.join(self._model_directory, f) for f in ["SD", "LoRA", "HN", "SR", "TI"]]
        for folder in modelFolders:
            if not folder in self._modelFolders and os.path.exists(folder):
                self.watcher.watchFolder(folder)
                self._modelFolders += [folder]
        self._trashFolder = os.path.join(self._model_directory, "TRASH")