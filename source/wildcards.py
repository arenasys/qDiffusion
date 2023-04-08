from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread, Qt
import os, re, glob, time

import filesystem

class Wildcards(QObject):
    updated = pyqtSignal()
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self._folders = []
        self._wildcards = {}
        self.watcher = filesystem.Watcher.instance
        self.watcher.folder_changed.connect(self.onFolderChanged)
        self.reload()

    @pyqtSlot()
    def reload(self):
        self._wildcards = {}
        root = self.gui.config.get("model_directory")
        if os.path.exists(root):
            folders = [os.path.join(root,f) for f in os.listdir(root) if os.path.isdir(os.path.join(root,f))]
        else:
            folders = [f for f in os.listdir(".") if os.path.isdir(f)]
        self._folders = [f for f in folders if re.search('wildcard(s)?', f, re.IGNORECASE)]    
        for folder in self._folders:
            self.watcher.watchFolder(folder)
    
    def loadFile(self, file):
        with open(file, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            if lines:
                name = file.rsplit(os.path.sep,1)[-1].rsplit('.',1)[0]
                self._wildcards[name] = lines
        self.updated.emit()

    @pyqtSlot(str, str, int)
    def onFolderChanged(self, folder, file, idx):
        if folder in self._folders and file.endswith(".txt"):
            self.loadFile(file)