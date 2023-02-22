import os
import glob
import importlib

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, Qt, QEvent
from PyQt5.QtQuick import QQuickItem
from PyQt5.QtQml import qmlRegisterType

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
        return "qDiffusion"

    @pyqtSlot(str, result=bool)
    def isCached(self, file):
        return self.thumbnails.has(file)

    @pyqtSlot()
    def generate(self):
        request = {"type":"txt2img", "data": {
            "model":"Anything-V3", "sampler":"Euler a", "clip_skip":2,
            "prompt":"masterpiece, highly detailed, white hair, smug, 1girl, holding big cat",
            "negative_prompt":"bad", "width":384, "height":384, "seed":2769446625, "steps":20, "scale":7,
            "hr_factor":2.0, "hr_strength":0.7, "hr_steps":20
        }}
        self.backend.makeRequest(1, request)

class FocusReleaser(QQuickItem):
    releaseFocus = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptedMouseButtons(Qt.AllButtons)
        self.setFlag(QQuickItem.ItemAcceptsInputMethod, True)
        self.setFiltersChildMouseEvents(True)
    
    def onPress(self, source):
        if not source.hasActiveFocus():
            self.releaseFocus.emit()

    def childMouseEventFilter(self, child, event):
        if event.type() == QEvent.MouseButtonPress:
            self.onPress(child)
        return False

    def mousePressEvent(self, event):
        self.onPress(self)
        event.setAccepted(False)

def registerTypes():
    qmlRegisterType(FocusReleaser, "gui", 1, 0, "FocusReleaser")