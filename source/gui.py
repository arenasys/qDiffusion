import os
import random
import datetime
import json
import bson
import difflib
import time
import platform
import urllib.parse
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent, QMimeData, QUrl, QSize, QThreadPool
from PyQt5.QtQuick import QQuickItem, QQuickPaintedItem
from PyQt5.QtGui import QImage, QColor, QDrag, QDesktopServices
from PyQt5.QtQml import qmlRegisterType
from PyQt5.QtWidgets import QApplication

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
    "upscaler": ["SR", "ESRGAN", "RealESRGAN"], 
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
    ABORTING = 5

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
    downloadsUpdated = pyqtSignal()
    windowUpdated = pyqtSignal()
    result = pyqtSignal(int, str)
    response = pyqtSignal(int, object)
    aboutToQuit = pyqtSignal()
    reset = pyqtSignal(int)
    raiseToTop = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.db = sql.Database(self)
        self.watcher = filesystem.Watcher()
        self.thumbnails = thumbnails.ThumbnailStorage((256,256),(640, 640),75, self)

        self._window_active = True
        
        self.tabs = []
        
        self._currentTab = "Generate"
        self._workingTabs = []
        self._visibleTabs = []

        self._statusMode = StatusMode.STARTING
        self._statusText = "Inactive"
        self._statusProgress = -1.0
        self._statusInfo = ""

        self._cancelled = False

        self._errorStatus = ""
        self._errorText = ""
        self._errorTrace = ""

        self._hostEndpoint = ""
        self._hostPassword = ""
        self._hostSetPassword = ""

        self._network = misc.DownloadManager(self)
        self._networkMapping = {}

        self._config = config.Config(self, "config.json", {
            "endpoint": "", "password": "", "output_directory": "outputs", "model_directory": "models", "device": "",
            "swap": False, "advanced": False, "autocomplete": 1, "vocab": [], "enforce_versions": True,
            "host_enabled": False, "host_address": "127.0.0.1", "host_port": 28888, "host_tunnel": False,
            "host_read_only": True, "host_monitor": False, "tabs": [], "grid_save_all": False,
            "scaling": False
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

        self._defaults = None
        self.syncDefaults()

        self.backend = backend.Backend(self)
        self.backend.response.connect(self.onResponse)
        self.backend.updated.connect(self.backendUpdated)
        if not parent.endpoint:
            self.backend.setEndpoint(self._config._values.get("endpoint"), self._config._values.get("password"))

        self.watchModelDirectory()

        self.signaller = misc.Signaller()
        parent.aboutToQuit.connect(self.signaller.stop)
        self.signaller.signal.connect(self.onSignal)
        self.signaller.start()

        self._options = {}
        self._empty = {}
        self._results = {}
        self._delayed = set()

        parent.aboutToQuit.connect(self.stop)

        self.watcher.finished.connect(self.onFolderChanged)

        if parent.endpoint:
            self.parseEndpoint(parent.endpoint)

    @pyqtSlot()
    def stop(self):
        self.aboutToQuit.emit()
        self.backend.wait()
        self.watcher.wait()
        self.signaller.wait()
    
    def registerTabs(self, tabs):
        self.tabs = tabs

        shown = self._config._values.get("tabs")
        if not shown:
            for t in self.tabs:
                if not getattr(t, "hidden", False):
                    shown += [t.name]
        
        shown = [t.name for t in self.tabs if t.name in shown and t.name != "Settings"]
        self._config._values.set("tabs", shown)
        
        self._visibleTabs = shown
        self.tabUpdated.emit()

    @pyqtProperty(list, constant=True)
    def tabSources(self):
        return [tab.source for tab in self.tabs]

    @pyqtProperty(list, constant=True)
    def tabNames(self): 
        return [tab.name for tab in self.tabs]
    
    @pyqtProperty(list, notify=tabUpdated)
    def visibleTabs(self):
        return self._visibleTabs
    
    @pyqtSlot(str, bool)
    def setTabVisible(self, tab, visible):
        shown = self._visibleTabs.copy()

        if tab in shown and visible:
            return
        if not tab in shown and not visible:
            return
        
        if not visible and tab in shown:
            shown.remove(tab)
        if visible and not tab in shown:
            shown += [tab]
        
        shown = [t.name for t in self.tabs if t.name in shown and t.name != "Settings"]
        self._config._values.set("tabs", shown)

        self._visibleTabs = shown
        self.tabUpdated.emit()
    
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

    @pyqtProperty('QString', notify=statusUpdated)
    def title(self):
        name = NAME

        if self.debugMode() != 0:
            name += " [DEBUG]"

        if self._remoteStatus != RemoteStatusMode.INACTIVE:
            if self._hostEndpoint:
                name += ": Hosting"
            else:
                name += ": Remote"
        
        return name

    @pyqtSlot(str, result=bool)
    def isCached(self, file):
        return self.thumbnails.has(QUrl.fromLocalFile(file).toLocalFile(), (256,256))
    
    @pyqtProperty('QString', notify=statusUpdated)
    def statusText(self):
        if self._remoteStatus == RemoteStatusMode.ERRORED:
            return "Errored"
        return self._statusText
    
    @pyqtProperty(int, notify=statusUpdated)
    def statusMode(self):
        if self._remoteStatus == RemoteStatusMode.ERRORED:
            return StatusMode.ERRORED.value
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
    
    def setError(self, status, text, trace):
        self._errorStatus = status
        self._errorText = text
        self._errorTrace = trace
        self.statusUpdated.emit()
        self.errorUpdated.emit()

    def setSending(self):
        self._statusMode = StatusMode.WORKING
        self._statusInfo = "Sending..."
        self._statusText = "Sending"
        self._statusProgress = -1.0
        self.statusUpdated.emit()

    def setCancelling(self):
        self._statusMode = StatusMode.ABORTING
        self._statusInfo = "Aborting..."
        self._statusText = "Aborting"
        self._cancelled = True
        self.statusUpdated.emit()

    def isCancelled(self):
        return self._cancelled
    
    def clearCancelled(self):
        self._cancelled = False

    @pyqtSlot(object)
    def onResponse(self, response):
        id = response.get("id", -1)
        monitor = response.get("monitor", False)
        type = response.get("type", "")
        data = response.get("data", {})

        if monitor and type in {"error"}:
            self.setReady()
            self.reset.emit(id)

        if monitor and not type in {"result", "artifact"}:
            return

        if type == "status" and self._statusMode != StatusMode.ABORTING:
            self._statusText = data["message"]
            self._statusInfo = ""
            if self._statusText in {"Initializing", "Connecting", "Reconnecting"}:
                if self._statusText in {"Connecting", "Reconnecting"}:
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
            trace = ""
            if "trace" in data:
                trace = data["trace"]
                with open("crash.log", "a", encoding='utf-8') as f:
                    f.write(f"INFERENCE {datetime.datetime.now()}\n{self._errorTrace}\n")
            self.setError(self._statusText, data["message"], trace)
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

        if type == "progress" and self._statusMode != StatusMode.ABORTING:
            self._statusProgress = data["current"]/data["total"]
            self._statusInfo = ""
            if response['data']['rate']:
                self._statusInfo = f"{response['data']['rate']:.2f}{response['data']['unit']}"
            self.statusUpdated.emit()
            if "previews" in data:
                self.addResult(id, "preview", data["previews"], "JPEG")
        
        if type == "temporary":
            self.addResult(id, "temporary", data["images"], data["type"])
            self._delayed.add(id)
            self.setReady()

        if type == "result":
            self.addResult(id, "metadata", data["metadata"])
            self.addResult(id, "result", data["images"], data["type"])

            if not id in self._delayed:
                self.setReady()
            else:
                self._delayed.remove(id)
            
            if id in self._results:
                del self._results[id]
                
        if type == "annotate":
            if "pose" in data:
                self.addResult(id, "pose", data["pose"])
            self.addResult(id, "result", data["images"], data["type"])
            self.setReady()

        if type == "artifact":
            self.addResult(id, data["name"], data["images"], data["type"])

        if type == "host":
            self._hostEndpoint = data["endpoint"]
            self._hostPassword = data["password"]
            self.statusUpdated.emit()

        if type == "segmentation":
            self.addResult(id, "result", data["images"], data["type"])
            self.setReady()
        
        self.response.emit(id, response)

    def addResult(self, id, name, data, typ=None):
        if not id in self._results:
            self._results[id] = {}
        self._results[id][name] = []
        if typ:
            typ = {"PNG": "png", "JPEG": "jpg"}[typ]
        for d in data:
            if type(d) == bytes or type(d) == bytearray:
                img = QImage()
                img.loadFromData(d, typ)
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
        return self.backend.mode == "Remote" or self.config.get("mode") == "remote"
    
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

    @pyqtSlot(str)
    def onSignal(self, message):
        self.parseEndpoint(message)
    
    def parseEndpoint(self, endpoint):
        try:
            parsed = urllib.parse.urlparse(endpoint)
            query = urllib.parse.parse_qs(parsed.query)
            endpoint, password = query["endpoint"][0], query["password"][0]
        except:
            return
        
        self.raiseToTop.emit()

        self._config._values.set("endpoint", endpoint)
        self._config._values.set("password", password)

        self.restartBackend()

    @pyqtSlot()
    def backendUpdated(self):
        self.statusUpdated.emit()

    @pyqtSlot()
    def quit(self):
        QApplication.quit()
        
    @pyqtSlot(QQuickTextDocument, result=misc.SyntaxManager)
    def setHighlighting(self, doc):
        manager = misc.SyntaxManager(self)
        manager.highlighter.setDocument(doc.textDocument())
        return manager

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
    
    def closestModel(self, name, models):
        if not models:
            return ''
        
        name = name.lower()
        best = models[0]
        score = 0

        for m in models:
            m_name = self.modelName(m).lower()
            m_score = difflib.SequenceMatcher(a=m_name, b=name).ratio()
            if m_score > score:
                best = m
                score = m_score
        
        return best
    
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
        if IS_WIN:
            try:
                misc.showFilesInExplorer(folder, files)
            except:
                self.setError("Visiting", f"Failed to visit: {folder}, {files}", "")
        else:
            self.visitFolder(folder)    

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
                        json.dump(data, f, indent=4)
                except Exception:
                    pass

    def getDefaults(self, model):
        return self._defaults.get(model, {})

    def setDefaults(self, model, params):
        self._defaults[model] = params
        self.syncDefaults() 

    def syncDefaults(self):
        if self._defaults == None:
            data = {}
            try:
                with open("defaults.json", 'r', encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass
            self._defaults = data
        else:
            if self._defaults == {}:
                if os.path.exists("defaults.json"):
                    os.remove("defaults.json")
            else:
                data = dict(self._defaults)
                try:
                    with open("defaults.json", 'w', encoding="utf-8") as f:
                        json.dump(data, f, indent=4)
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

    @pyqtProperty(str, notify=statusUpdated)
    def hostWeb(self):
        url = self._hostEndpoint
        password = self._hostPassword
        if url.startswith("wss") or "127.0.0.1" in url:
            return "https://arenasys.github.io/?" + urllib.parse.urlencode({'endpoint': url, "password": password})
        else:
            return ""

    @pyqtSlot(str, float, int, int, result='QVariant')
    def weightText(self, text, inc, start, end):
        return misc.weightText(text, inc, start, end)
    
    @pyqtProperty(misc.DownloadManager, notify=downloadsUpdated)
    def network(self):
        return self._network
    
    @pyqtProperty(bool, notify=windowUpdated)
    def windowActive(self):
        return self._window_active
    
    @windowActive.setter
    def windowActive(self, value):
        if value != self._window_active:
            self._window_active = value
            self.parent().setCursorFlashTime(1000 if self._window_active else 0)
            self.windowUpdated.emit()

    def debugMode(self):
        return self._config._values.get("debug_mode", 0)
    
    @pyqtSlot(int)
    def setDebugMode(self, mode):
        self._config._values.set("debug_mode", mode)
        self.statusUpdated.emit()