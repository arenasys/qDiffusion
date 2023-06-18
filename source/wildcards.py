from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread, Qt
import os, re, glob, time

import filesystem

class Wildcards(QObject):
    updated = pyqtSignal()
    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self._wildcards = {}
        self._sources = {}
        self._counter = {}
        self.reload()

    @pyqtSlot()
    def reload(self):
        wildcards = {}
        sources = {}
        for ext in ["*.txt", "*.csv"]:
            for file in glob.glob(os.path.join(self.gui.modelDirectory(), "WILDCARD", ext)):
                with open(file, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f.readlines() if l.strip()]
                    if not lines:
                        continue
                    name = file.rsplit(os.path.sep,1)[-1].rsplit('.',1)[0]
                    sources[name] = file.rsplit(os.path.sep,1)[-1]
                    wildcards[name] = lines
        self._wildcards = wildcards
        self._sources = sources
        self.updated.emit()