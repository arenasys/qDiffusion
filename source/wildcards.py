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
        folder = os.path.join(self.gui.modelDirectory(), "WILDCARD")
        for ext in ["*.txt", "*.csv"]:
            for file in glob.glob(os.path.join(folder, os.path.join("**", ext)), recursive=True):
                with open(file, 'r', encoding='utf-8') as f:
                    lines = []
                    for l in [l.strip() for l in f.readlines() if l.strip()]:
                        if l[0] == '#':
                            continue
                        if ',' in l:
                            a, b = l.rsplit(',',1)
                            try:
                                b = int(b)
                                l = a
                            except:
                                pass
                        lines += [l]

                    if not lines:
                        continue
                    path = os.path.relpath(file, folder)
                    name = path.rsplit('.',1)[0].replace(os.path.sep, "/")
                    sources[name] = path
                    wildcards[name] = lines
        self._wildcards = wildcards
        self._sources = sources
        self.updated.emit()