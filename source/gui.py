import os
import random
import datetime
import json
import bson
import platform
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData, QUrl, QSize, QThreadPool
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QImage, QColor, QDrag, QDesktopServices
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
import wildcards
import translation
import misc
import parameters

NAME = "qDiffusion"

MODEL_FOLDERS = {
    "checkpoint": ["SD", "Stable-diffusion"],
    "component": ["SD", "Stable-diffusion", "VAE"],
    "upscale": ["SR", "ESRGAN", "RealESRGAN"], 
    "embedding": ["TI", "embeddings", os.path.join("..", "embeddings")], 
    "lora": ["LoRA"], 
    "hypernet": ["HN", "hypernetworks"],
    "wildcard": ["WILDCARD"],
    "controlnet": ["CN"]
}

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
    tabUpdated = pyqtSignal()
    favUpdated = pyqtSignal()
    configUpdated = pyqtSignal()
    result = pyqtSignal(int, str)
    response = pyqtSignal(int, object)
    aboutToQuit = pyqtSignal()
    networkReply = pyqtSignal(QNetworkReply)
    reset = pyqtSignal(int)

    def __init__(self, parent):
        super().__init__(parent)
        self.db = sql.Database(self)
        self.watcher = filesystem.Watcher()
        self.thumbnails = thumbnails.ThumbnailStorage((256,256),(640, 640),75, self)
        self.network = QNetworkAccessManager(self)
        self.requestProgress = 0.0
        self.tabs = []
        
        self._currentTab = "Generate"
        self._workingTabs = []

        self._statusMode = StatusMode.STARTING
        self._statusText = "Inactive"
        self._statusProgress = -1.0
        self._statusInfo = ""

        self._errorStatus = ""
        self._errorText = ""
        self._errorTrace = ""

        self._hostEndpoint = ""
        self._hostPassword = ""
        self._hostSetPassword = ""

        self._config = config.Config(self, "config.json", {
            "endpoint": "", "password": "", "output_directory": "outputs", "model_directory": "models", "device": "",
            "swap": False, "advanced": False, "autocomplete": 1, "vocab": [], "enforce_versions": True,
            "host_enabled": False, "host_address": "127.0.0.1", "host_port": 28888, "host_tunnel": False,
            "host_read_only": True, "host_monitor": False, "tabs": []
        })
        self._config.updated.connect(self.onConfigUpdated)
        self._remoteStatus = RemoteStatusMode.INACTIVE

        self._modelFolders = []

        self._debugJSONLogging = self._config._values.get("debug") == True

        self.wildcards = wildcards.Wildcards(self)
        self.wildcards.updated.connect(self.wildcardsUpdated)
        self.wildcards.reload()

        self._favourites = None
        self.syncFavourites()

        self.backend = backend.Backend(self)
        self.backend.response.connect(self.onResponse)
        self.backend.updated.connect(self.backendUpdated)
        self.backend.setEndpoint(self._config._values.get("endpoint"), self._config._values.get("password"))

        self.watchModelDirectory()

        self._options = {}
        self._empty = {}
        self._results = {}

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
    
    @pyqtProperty(str, notify=tabUpdated)
    def currentTab(self): 
        return self._currentTab
    
    @currentTab.setter
    def currentTab(self, tab):
        self._currentTab = tab
        self.tabUpdated.emit()

    @pyqtProperty(list, notify=tabUpdated)
    def workingTabs(self):
        return self._workingTabs
    
    @pyqtSlot(str, bool)
    def setTabWorking(self, tab, working):
        if working and not tab in self._workingTabs:
            self._workingTabs += [tab]
            self.tabUpdated.emit()
        if not working and tab in self._workingTabs:
            self._workingTabs.remove(tab)
            self.tabUpdated.emit()

    @pyqtSlot(str, result=bool)
    def tabInitialStatus(self, tab):
        tabs = self._config._values.get("tabs")
        if tabs:
            if not self._currentTab in tabs:
                self._currentTab = [t.name for t in self.tabs if t.name in tabs][0]
                self.tabUpdated.emit()
            return tab in tabs
        
        status = True

        for t in self.tabs:
            tab_status = not getattr(t, "hidden", False)
            self.setTabInitialStatus(t.name, tab_status)
            if t.name == tab:
                status = tab_status
        
        return status
    
    @pyqtSlot(str, bool)
    def setTabInitialStatus(self, tab, status):
        tabs = list(self._config._values.get("tabs"))
        
        if not status and tab in tabs:
            tabs.remove(tab)
        elif status and not tab in tabs:
            tabs += [tab] 

        self._config._values.set("tabs", tuple(tabs))

    @pyqtProperty('QString', notify=statusUpdated)
    def title(self):
        if self._remoteStatus != RemoteStatusMode.INACTIVE:
            if self._hostEndpoint:
                return NAME + ": Hosting"
            else:
                return NAME + ": Remote"
        return NAME

    @pyqtSlot(str, result=bool)
    def isCached(self, file):
        return self.thumbnails.has(QUrl.fromLocalFile(file).toLocalFile(), (256,256))
    
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
    
    @pyqtProperty('QString', notify=errorUpdated)
    def errorTrace(self):
        return self._errorTrace
    
    @pyqtProperty('QString', notify=statusUpdated)
    def errorStatus(self):
        return self._errorStatus
    
    @pyqtProperty(int, notify=optionsUpdated)
    def modelCount(self):
        if not "UNET" in self._options:
            return 0
        return len(self._options["UNET"])
    
    def setOptions(self, options):
        if options:
            self._empty = {k:[] for k in options}
        self._options = options
        self.optionsUpdated.emit()

    def clearOptions(self):
        if self._empty:
            self._options = self._empty.copy()
        self.optionsUpdated.emit()
    
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

    def setWaiting(self):
        self._statusMode = StatusMode.WORKING
        self._statusInfo = ""
        self._statusText = "Waiting"
        self._statusProgress = -1.0
        self.statusUpdated.emit()
    
    @pyqtSlot(object)
    def onResponse(self, response):
        id = response.get("id", -1)
        monitor = response.get("monitor", False)
        type = response.get("type", "")
        data = response.get("data", {})

        if monitor and type in {"error"}:
            self.setReady()
            self.reset.emit(id)

        if monitor and not type in {"status", "progress", "aborted", "result", "artifact"}:
            return

        if type == "status":
            self._statusText = data["message"]
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

        if type == "remote_only":
            self._statusText = "Inactive"
            self._statusProgress = -1.0
            self._statusMode = StatusMode.INACTIVE
            self.statusUpdated.emit()

        if type == "done":
            self.setReady()
            self.refreshModels()

        if type == "options":
            self.setOptions(data)
            self.wildcards.reload()
            if self._statusText == "Initializing":
                self.setReady()

        if type == "error":
            self._errorStatus = self._statusText
            self._errorText = data["message"]
            self._errorTrace = ""
            if "trace" in data:
                self._errorTrace = data["trace"]
                with open("crash.log", "a", encoding='utf-8') as f:
                    f.write(f"INFERENCE {datetime.datetime.now()}\n{self._errorTrace}\n")
            self.statusUpdated.emit()
            self.errorUpdated.emit()
            self.reset.emit(id)
            
        if type == "remote_error":
            self._errorStatus = self._statusText
            self._errorText = data["message"]
            self._errorTrace = ""
            if "trace" in data:
                self._errorTrace = data["trace"]
                with open("crash.log", "a", encoding='utf-8') as f:
                    f.write(f"REMOTE {datetime.datetime.now()}\n{self._errorTrace}\n")
            self._remoteStatus = RemoteStatusMode.ERRORED
            self.statusUpdated.emit()
            self.errorUpdated.emit()
            self.reset.emit(id)
            self.backend.stop()
            self.backend.wait()
            
        if type == "aborted":
            self.reset.emit(id)
            self.setReady()

        if type == "progress":
            self._statusProgress = data["current"]/data["total"]
            self._statusInfo = ""
            if response['data']['rate']:
                self._statusInfo = f"{response['data']['rate']:.2f}{response['data']['unit']}"
            self.statusUpdated.emit()
            if "previews" in data:
                self.addResult(id, "preview", data["previews"])

        if type == "result":
            self.addResult(id, "metadata", data["metadata"])
            self.addResult(id, "result", data["images"])
            self.setReady()
            self._results = {}

        if type == "annotate":
            self.addResult(id, "result", data["images"])
            self.setReady()

        if type == "artifact":
            self.addResult(id, data["name"], data["images"])

        if type == "host":
            self._hostEndpoint = data["endpoint"]
            self._hostPassword = data["password"]
            self.statusUpdated.emit()

        if type == "segmentation":
            self.addResult(id, "result", data["images"])
            self.setReady()
        
        self.response.emit(id, response)

    def addResult(self, id, name, data):
        if not id in self._results:
            self._results[id] = {}
        self._results[id][name] = []
        for d in data:
            if type(d) == bytes or type(d) == bytearray:
                img = QImage()
                img.loadFromData(d, "png")
                self._results[id][name] += [img]
            else:
                self._results[id][name] += [d]
        self.result.emit(id, name)
    
    @pyqtSlot(str, int)
    def onFolderChanged(self, folder, total):
        if folder in self._modelFolders:
            if self._statusMode != StatusMode.STARTING:
                self.refreshModels()
            return

    @pyqtSlot()
    def refreshModels(self):
        self.wildcards.reload()
        self.backend.makeRequest({"type":"options"})

    @pyqtSlot()
    def clearError(self):
        if self._statusMode != StatusMode.STARTING:
            self._statusText = "Ready"
            self._statusMode = StatusMode.IDLE
        self._statusProgress = -1.0
        self.statusUpdated.emit()

    @pyqtSlot()
    def copyError(self):
        self.copyText(self._errorTrace)

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
        self.requestProgress = max(self.requestProgress, (current/total) if total else 0)
        self.statusUpdated.emit()

    def getFilesMimeData(self, files):
        urls = [QUrl.fromLocalFile(os.path.abspath(file)) for file in files]
        mimedata = QMimeData()
        mimedata.setUrls(urls)
        mimedata.setImageData(QImage(files[0]))

        gnome = "copy\n"+'\n'.join(["file://"+url.toLocalFile() for url in urls])
        mimedata.setData("x-special/gnome-copied-files", gnome.encode("utf-8"))
        return mimedata
    
    def getImageMimeData(self, img):
        mimedata = QMimeData()
        mimedata.setImageData(img)
        return mimedata

    def copyFiles(self, files):
        QApplication.clipboard().setMimeData(self.getFilesMimeData(files))
    
    def copyImage(self, img):
        QApplication.clipboard().setMimeData(self.getImageMimeData(img))

    def copyText(self, text):
        QApplication.clipboard().setText(text)

    def dragFiles(self, files):
        drag = QDrag(self)
        drag.setMimeData(self.getFilesMimeData(files))
        drag.exec()
    
    def dragImage(self, img):
        drag = QDrag(self)
        drag.setMimeData(self.getImageMimeData(img))
        drag.exec()
    
    @pyqtProperty(parameters.VariantMap, notify=configUpdated)
    def config(self):
        return self._config._values
    
    @pyqtSlot()
    def onConfigUpdated(self):
        self.configUpdated.emit()

    @pyqtProperty(str, notify=statusUpdated)
    def remoteEndpoint(self):
        endpoint = self._config._values.get("endpoint")
        if not endpoint:
            return ""
        return endpoint
    
    @pyqtProperty(int, notify=statusUpdated)
    def remoteStatus(self):
        return self._remoteStatus.value
    
    @pyqtProperty(bool, notify=statusUpdated)
    def isRemote(self):
        return self.backend.mode == "Remote"
    
    @pyqtProperty(str, notify=statusUpdated)
    def remoteInfoMode(self):
        return self.backend.mode
    
    @pyqtProperty(str, notify=statusUpdated)
    def remoteInfoStatus(self):
        status = ""
        if self._config._values.get("endpoint"):
            if self._remoteStatus == RemoteStatusMode.CONNECTING:
                status = "Connecting"
            elif self._remoteStatus == RemoteStatusMode.ERRORED:
                status = "Errored"
            else:
                status = "Connected"
        else:
            if self._statusMode == StatusMode.STARTING:
                status = "Initializing"
            elif self._statusMode == StatusMode.INACTIVE:
                status = "Inactive"
            else:
                status = "Ready"

        return status

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
        self._hostEndpoint = ""
        self._hostPassword = ""
        self.statusUpdated.emit()

        self.clearOptions()

        self.backend.stop()
        self.backend.wait()
        self.backend.setEndpoint(endpoint, password)
        self.reset.emit(-1)

    @pyqtSlot()
    def backendUpdated(self):
        self.statusUpdated.emit()

    @pyqtSlot()
    def quit(self):
        QApplication.quit()
        
    @pyqtSlot(QQuickTextDocument)
    def setHighlighting(self, doc):
        highlighter = misc.SyntaxHighlighter(self)
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

    def modelDirectory(self):
        return self._config._values.get("model_directory")
    
    def outputDirectory(self):
        return self._config._values.get("output_directory")
    
    @pyqtSlot()
    def watchModelDirectory(self):
        folders = ["SD", "LoRA", "HN", "SR", "TI", "Stable-diffusion", "ESRGAN", "RealESRGAN", "Lora", "hypernetworks", os.path.join("..", "embeddings"), "WILDCARD"]
        folders = [os.path.abspath(os.path.join(self.modelDirectory(), f)) for f in folders]
        folders = [f for f in folders if os.path.exists(f)]
        for folder in folders:
            if not folder in self._modelFolders and os.path.exists(folder):
                self.watcher.watchFolder(folder)
                self._modelFolders += [folder]
        self._trashFolder = os.path.join(self.modelDirectory(), "TRASH")

    @pyqtSlot(str, result=str)
    def modelName(self, name):
        return name.rsplit(".",1)[0].rsplit(os.path.sep,1)[-1]
    
    @pyqtSlot(str, result=str)
    def modelFileName(self, name):
        return name.rsplit(os.path.sep,1)[-1]
    
    @pyqtSlot(str, result=str)
    def netType(self, name):
        folder = name.rsplit(os.path.sep,1)[0].rsplit(os.path.sep,1)[0]
        if folder in {"LoRA"}:
            return "LoRA"
        elif folder in {"HN", "hypernetworks"}:
            return "HN"
        return None
    
    @pyqtSlot(str)
    def visitFolder(self, folder):
        QDesktopServices.openUrl(QUrl.fromLocalFile(folder))

    @pyqtSlot(str)
    def openFiles(self, files):
        for file in files:
            QDesktopServices.openUrl(QUrl.fromLocalFile(file))

    @pyqtSlot(list)
    def visitFiles(self, files):
        folder = os.path.dirname(files[0])
        if not IS_WIN:
            self.visitFolder(folder)
        else:
            misc.showFilesInExplorer(folder, files)

    @pyqtSlot(str)
    def openModelFolder(self, mode):
        dir = self.modelDirectory()
        found = None
        for f in MODEL_FOLDERS[mode]:
            path = os.path.join(dir, f)
            if os.path.exists(path):
                found = path
                break
        if not found:
            found = os.path.join(dir, MODEL_FOLDERS[mode][0])
            os.makedirs(found)
        try:
            found = os.path.abspath(found)
            self.visitFolder(found)
        except Exception:
            pass
    
    @pyqtSlot(str)
    def openLink(self, link):
        try:
            QDesktopServices.openUrl(QUrl.fromUserInput(link))
        except Exception:
            pass
    
    @pyqtProperty(list, notify=favUpdated)
    def favourites(self):
        return self._favourites

    @pyqtSlot(str)
    def toggleFavourite(self, value):
        if value in self._favourites:
            self._favourites.remove(value)
        else:
            self._favourites.append(value)
        self.favUpdated.emit()
        self.syncFavourites()

    @pyqtSlot(list, result=list)
    def filterFavourites(self, model):
        filtered = [m for m in model if m in self._favourites]
        if not filtered:
            return model
        return filtered

    @pyqtSlot()
    def syncFavourites(self):
        if self._favourites == None:
            data = []
            try:
                with open("fav.json", 'r', encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
            self._favourites = data
        else:
            if self._favourites == []:
                if os.path.exists("fav.json"):
                    os.remove("fav.json")
            else:
                data = list(self._favourites)
                try:
                    with open("fav.json", 'w', encoding="utf-8") as f:
                        json.dump(data, f)
                except Exception:
                    pass

    @pyqtSlot(str, str)
    def importModel(self, mode, file):
        old = QUrl(file).toLocalFile()

        base = self.modelDirectory()
        folder = None
        for f in MODEL_FOLDERS[mode]:
            tmp = os.path.join(base, f)
            if os.path.exists(tmp):
                folder = tmp

        if not folder:
            folder = os.path.join(base, MODEL_FOLDERS[mode][0])

        new = os.path.abspath(os.path.join(folder, old.rsplit(os.path.sep,1)[-1]))

        request = {"type":"manage", "data": {"operation": "rename", "old_file": old, "new_file": new}}
        self.makeRequest(request)

    @pyqtSlot()
    def wildcardsUpdated(self):
        self.optionsUpdated.emit()

    @pyqtProperty(str, notify=statusUpdated)
    def hostEndpoint(self):
        return self._hostEndpoint
    
    @pyqtProperty(str, notify=statusUpdated)
    def hostPassword(self):
        return self._hostPassword
    
    @hostPassword.setter
    def hostPassword(self, password):
        self._hostSetPassword = password