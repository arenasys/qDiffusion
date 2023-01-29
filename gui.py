import os
import glob
import importlib

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt
from PyQt5.QtSql import QSqlDriver

import sql
import filesystem
import thumbnails
import backend

class GUI(QObject):
    aboutToQuit = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)

        self.backend = backend.Backend(self)
        self.db = sql.Database(self)
        self.watcher = filesystem.Watcher()
        self.thumbnails = thumbnails.ThumbnailStorage((256, 256), 75, self)
        self.tabs = []

        parent.aboutToQuit.connect(self.stop)

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

    @pyqtProperty('QString', constant=True)
    def title(self):
        return "SD Inference GUI"

    @pyqtSlot(str, result=bool)
    def isCached(self, file):
        return self.thumbnails.has(file)