import os
import glob
import importlib

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt
from PyQt5.QtSql import QSqlDriver

import sql
import filesystem
import thumbnails

class GUI(QObject):
    aboutToQuit = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.db = sql.Database(self)
        self.watcher = filesystem.Watcher()
        self.thumbnails = thumbnails.ThumbnailStorage((256, 256), 75)
        self.tabs = []

        parent.aboutToQuit.connect(self.stop)

    @pyqtSlot()
    def stop(self):
        self.watcher.stop()
        self.aboutToQuit.emit()
    
    def register_tabs(self, tabs):
        self.tabs = tabs

    @pyqtProperty(list, constant=True)
    def tab_sources(self):
        return [tab.source for tab in self.tabs]

    @pyqtProperty(list, constant=True)
    def tab_names(self): 
        return [tab.name for tab in self.tabs]

    @pyqtProperty('QString', constant=True)
    def title(self):
        return "SD Inference GUI"