import math
import os
import subprocess

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot, QUrl, QThread
from PyQt5.QtQml import qmlRegisterSingletonType

from misc import MimeData

class Update(QThread):
    def run(self):
        subprocess.run(["git", "pull", "origin", "master"])
        inf = os.path.join("source", "sd-inference-server")
        if os.path.exists(inf):
            subprocess.run(["git", "pull", "origin", "master"], cwd=inf)

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
        self.gui.backend.makeRequest(-1, {"type":"options"})

    @pyqtSlot()
    def update(self):
        update = Update(self)
        update.finished.connect(self.gui.getGitDate)
        update.start()
    
    @pyqtSlot(str, str)
    def upload(self, type, file):
        file = QUrl.fromLocalFile(file)
        if not file.isLocalFile():
            return

        self.gui.remoteUpload(type, file.toLocalFile())
    
    @pyqtSlot(QUrl, result=str)
    def toLocal(self, url):
        return url.toLocalFile()
    
    @pyqtSlot(MimeData, result=str)
    def uploadDrop(self, mimeData):
        mimeData = mimeData.mimeData
        for url in mimeData.urls():
            if url.isLocalFile():
                return url.toLocalFile()
            
    @pyqtSlot(int, object)
    def onResponse(self, id, response):
        if id != -1 or response["type"] != "downloaded":
            return
        self._log += response["data"]["message"] + "\n"
        self.updated.emit()   
        self.gui.backend.makeRequest(-1, {"type":"options"})
