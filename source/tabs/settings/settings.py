import math
import os
import subprocess
import platform
import time
import pygit2
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QThread
from PyQt5.QtQml import qmlRegisterSingletonType

from misc import MimeData

QDIFF_URL = "https://github.com/arenasys/qDiffusion"
INFER_URL = "https://github.com/arenasys/sd-inference-server"

def git_reset(path, origin):
    repo = pygit2.Repository(os.path.abspath(path))
    repo.remotes.set_url("origin", origin)
    repo.remotes[0].fetch()
    head = repo.lookup_reference("refs/remotes/origin/master").raw_target
    print(head)
    repo.reset(head, pygit2.GIT_RESET_HARD)

def git_last(path):
    try:
        repo = pygit2.Repository(os.path.abspath(path))
        commit = repo[repo.head.target]
        message = commit.raw_message.decode('utf-8').strip()
        delta = time.time() - commit.commit_time
    except:
        return None, None
    
    spans = [
        ('year', 60*60*24*365),
        ('month', 60*60*24*30),
        ('day', 60*60*24),
        ('hour', 60*60),
        ('minute', 60),
        ('second', 1)
    ]
    when = "?"
    for label, span in spans:
        if delta >= span:
            count = int(delta//span)
            suffix = "" if count == 1 else "s"
            when = f"{count} {label}{suffix} ago"
            break

    return commit, f"{message} ({commit.short_id}) ({when})"

def git_init(path, origin):
    repo = pygit2.init_repository(os.path.abspath(path), False)
    if not "origin" in repo.remotes:
        repo.create_remote("origin", origin)
    git_reset(path, origin)

class Update(QThread):
    def run(self):
        git_reset(".", QDIFF_URL)
        inf = os.path.join("source", "sd-inference-server")
        if os.path.exists(inf):
            git_reset(inf, INFER_URL)

class Settings(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = math.inf
        self.name = "Settings"
        self.gui = parent
        self._currentTab = "Remote"

        self._log = ""

        qmlRegisterSingletonType(Settings, "gui", 1, 0, "SETTINGS", lambda qml, js: self)

        self.gui.response.connect(self.onResponse)

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
    def log(self):
        return self._log

    @pyqtSlot()
    def restart(self):
        self._log = ""
        self.updated.emit()
        self.gui.restartBackend()

    @pyqtSlot(str, str)
    def download(self, type, url):
        if not url:
            return
        self.gui.remoteDownload(type, url)

    @pyqtSlot()
    def refresh(self):
        self.gui.backend.makeRequest({"type":"options"})

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
        if not file.isLocalFile():
            return
        self.gui.remoteUpload(type, file.toLocalFile().replace('/', os.path.sep))
    
    @pyqtSlot(QUrl, result=str)
    def toLocal(self, url):
        return url.toLocalFile()
    
    @pyqtSlot(MimeData, result=str)
    def pathDrop(self, mimeData):
        mimeData = mimeData.mimeData
        for url in mimeData.urls():
            if url.isLocalFile():
                return url.toLocalFile() 
    
    @pyqtSlot(int, object)
    def onResponse(self, id, response):
        if response["type"] != "downloaded":
            return
        self._log += response["data"]["message"] + "\n"
        self.updated.emit()   
        self.gui.backend.makeRequest({"type":"options"})

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

        commit, label = git_last(".")

        if commit:
            if self._currentGitInfo == None:
                self._currentGitInfo = commit
            self._gitInfo = "GUI commit: " + label
            self._needRestart = self._currentGitInfo != commit
        elif not self._triedGitInit:
            self._triedGitInit = True
            git_init(".", QDIFF_URL)

        server_dir = os.path.join("source","sd-inference-server")
        if os.path.exists(server_dir):
            commit, label = git_last(server_dir)
            if self._currentGitServerInfo == None:
                self._currentGitServerInfo = commit
            self._gitServerInfo = "Inference commit: " + label
            self._needRestart = self._needRestart or (self._currentGitServerInfo != commit)

        self.updated.emit()