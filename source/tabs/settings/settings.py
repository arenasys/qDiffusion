import math
import os
import subprocess
import platform
import datetime
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QThread
from PyQt5.QtQml import qmlRegisterSingletonType

from misc import MimeData

class Update(QThread):
    def run(self):
        subprocess.run(["git", "fetch"], capture_output=True, shell=IS_WIN)
        subprocess.run(["git", "reset", "--hard", "origin/master"], capture_output=True, shell=IS_WIN)
        inf = os.path.join("source", "sd-inference-server")
        if os.path.exists(inf):
            subprocess.run(["git", "fetch"], capture_output=True, shell=IS_WIN)
            subprocess.run(["git", "reset", "--hard", "origin/master"], capture_output=True, shell=IS_WIN)

class Settings(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = math.inf
        self.name = "Settings"
        self.gui = parent

        self._log = ""

        qmlRegisterSingletonType(Settings, "gui", 1, 0, "SETTINGS", lambda qml, js: self)

        self.gui.response.connect(self.onResponse)

        self._needRestart = False
        self._currentGitInfo = None
        self._triedGitInit = False
        self.getGitInfo()

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
        update = Update(self)
        update.finished.connect(self.getGitInfo)
        update.start()
    
    @pyqtSlot(str, str)
    def upload(self, type, file):
        file = QUrl.fromLocalFile(file)
        if not file.isLocalFile():
            return

        print("SETTINGS")
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
    
    @pyqtProperty(bool, notify=updated)
    def needRestart(self):
        return self._needRestart
    
    @pyqtSlot()
    def getGitInfo(self):
        self._gitInfo = "Unknown"
        r = subprocess.run(["git", "log", "-1", "--format=%B (%h) (%cr)"], capture_output=True, shell=IS_WIN)
        if r.returncode == 0:
            m = r.stdout.decode('utf-8').replace("\n","")
            cm = m.rsplit(") (", 1)[0]
            if self._currentGitInfo == None:
                self._currentGitInfo = cm
            self._gitInfo = "Last commit: " + m
            self._needRestart = self._currentGitInfo != cm
        else:
            m = r.stderr.decode('utf-8')
            if not self._triedGitInit and m.startswith("fatal: not a git repository"):
                self._triedGitInit = True
                r = subprocess.run(["git", "init"], capture_output=True, shell=IS_WIN)
                r = subprocess.run(["git", "remote", "add", "origin", "https://github.com/arenasys/qDiffusion.git"], capture_output=True, shell=IS_WIN)
                r = subprocess.run(["git", "fetch"], capture_output=True, shell=IS_WIN)
                r = subprocess.run(["git", "reset", "--hard", "origin/master"], capture_output=True, shell=IS_WIN)

        self.updated.emit()