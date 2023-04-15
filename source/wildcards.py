from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread, Qt
import os, re, glob, time

import filesystem

class Wildcards(QObject):
    updated = pyqtSignal()
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self._wildcards = {}
        self.reload()

    @pyqtSlot()
    def reload(self):
        self._wildcards = {}
        for file in glob.glob(os.path.join(self.gui.modelDirectory(), "WILDCARD", "*.txt")):
            self.loadFile(file)
    
    def loadFile(self, file):
        with open(file, 'r') as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
            if lines:
                name = file.rsplit(os.path.sep,1)[-1].rsplit('.',1)[0]
                self._wildcards[name] = lines
        self.updated.emit()