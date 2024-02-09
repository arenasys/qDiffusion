import math
import os
import platform
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QThread
from PyQt5.QtQml import qmlRegisterSingletonType

from misc import MimeData
import git

class Update(QThread):
    def run(self):
        git.git_reset(".", git.QDIFF_URL)
        inf = os.path.join("source", "sd-inference-server")
        if os.path.exists(inf):
            git.git_reset(inf, git.INFER_URL)

class Settings(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = math.inf
        self.name = "Settings"
        self.gui = parent
        self._currentTab = "Remote"
        self._currentUpload = ""
        self._currentUploadMode = 0

        qmlRegisterSingletonType(Settings, "gui", 1, 0, "SETTINGS", lambda qml, js: self)

        self._needRestart = False
        self._currentGitInfo = None
        self._currentGitServerInfo = None
        self._triedGitInit = False
        self._updating = False
        self.getGitInfo()

    @pyqtProperty(str, notify=updated)
    def currentTab(self): 
        return self._currentTab
    
    @currentTab.setter
    def currentTab(self, tab):
        self._currentTab = tab
        self.updated.emit()

    @pyqtProperty(str, notify=updated)
    def currentUpload(self): 
        return self._currentUpload

    @pyqtProperty(int, notify=updated)
    def currentUploadMode(self): 
        return self._currentUploadMode

    @pyqtSlot(str, int)
    def setUpload(self, file, mode):
        if file.startswith("file:"):
            file = QUrl(file).toLocalFile()
        self._currentUpload = file
        self._currentUploadMode = mode
        self.updated.emit()

    @pyqtSlot()
    def restart(self):
        self.updated.emit()
        self.gui.restartBackend()

    @pyqtSlot(str, str)
    def download(self, type, url):
        if not url:# or self.gui.remoteInfoStatus != "Connected":
            return
        request = {"type": type, "url":url}
        
        for t in ["hf_token", "civitai_token"]:
            token = self.gui.config.get(t, "")
            if token:
                request[t] = token
        
        id = self.gui.makeRequest({"type":"download", "data":request})
        self.gui.network.create(url, id, True)

    @pyqtSlot()
    def refresh(self):
        self.gui.makeRequest({"type":"options"})

    @pyqtSlot()
    def update(self):
        self._updating = True
        update = Update(self)
        update.finished.connect(self.getGitInfo)
        update.finished.connect(self.updateDone)
        update.start()
        self.updated.emit()

    @pyqtSlot()
    def updateDone(self):
        self._updating = False
        self.updated.emit()
    
    @pyqtSlot(str, str)
    def upload(self, type, file):
        file = QUrl.fromLocalFile(file)
        if not file.isLocalFile() or self.gui.remoteInfoStatus != "Connected":
            return
        file = file.toLocalFile().replace('/', os.path.sep)
        id = self.gui.makeRequest({"type":"upload", "data":{"type": type, "file": file}})
        self.gui.network.create(file.split(os.path.sep)[-1], id, False)

    @pyqtSlot(QUrl, result=str)
    def toLocal(self, url):
        return url.toLocalFile()
    
    @pyqtSlot(MimeData, result=str)
    def pathDrop(self, mimeData):
        mimeData = mimeData.mimeData
        for url in mimeData.urls():
            if url.isLocalFile():
                return url.toLocalFile() 

    @pyqtProperty(str, notify=updated)
    def gitInfo(self):
        return self._gitInfo
    
    @pyqtProperty(str, notify=updated)
    def gitServerInfo(self):
        return self._gitServerInfo
    
    @pyqtProperty(bool, notify=updated)
    def needRestart(self):
        return self._needRestart
    
    @pyqtProperty(bool, notify=updated)
    def updating(self):
        return self._updating
    
    @pyqtSlot()
    def getGitInfo(self):
        self._gitInfo = "Unknown"
        self._gitServerInfo = ""

        commit, label = git.git_last(".")

        if commit:
            if self._currentGitInfo == None:
                self._currentGitInfo = commit
            self._gitInfo = label
            self._needRestart = self._currentGitInfo != commit
        elif not self._triedGitInit:
            self._triedGitInit = True
            git.git_init(".", git.QDIFF_URL)

        server_dir = os.path.join("source","sd-inference-server")
        if os.path.exists(server_dir):
            commit, label = git.git_last(server_dir)
            if commit:
                if self._currentGitServerInfo == None:
                    self._currentGitServerInfo = commit
                self._gitServerInfo = label
                self._needRestart = self._needRestart or (self._currentGitServerInfo != commit)

        self.updated.emit()