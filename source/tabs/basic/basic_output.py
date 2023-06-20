from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QUrl
from PyQt5.QtGui import QImage

import parameters
import os

class BasicOutput(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None, image=QImage()):
        super().__init__(parent)
        self.basic = parent
        self._image = image
        self._metadata = None
        self._artifacts = {}
        self._artifactNames = []
        self._display = None
        self._file = ""
        self._parameters = ""
        self._dragging = False
        self._ready = False

    def setResult(self, image, metadata):
        self._image = image
        self._metadata = metadata
        self._file = metadata["file"]
        self._parameters = parameters.formatParameters(self._metadata)
        self._image.setText("parameters", self._parameters)
        self._ready = True
        self.updated.emit()

    def setPreview(self, image):
        self._image = image
        self.updated.emit()

    def setArtifacts(self, artifacts):
        self._artifacts = artifacts
        self._artifactNames = list(self._artifacts.keys())
        self._display = None
        self.updated.emit()

    @pyqtSlot(QUrl)
    def saveImage(self, file):
        file = file.toLocalFile()
        if not "." in file.rsplit(os.path.sep,1)[-1]:
            file = file + ".png"
        try:
            self.display.save(file)
        except Exception:
            pass

    @pyqtProperty(bool, notify=updated)
    def ready(self):
        return self._ready

    @pyqtProperty(QImage, notify=updated)
    def image(self):
        return self._image
    
    @pyqtProperty(QImage, notify=updated)
    def display(self):
        if not self._display:
            return self._image
        return self._artifacts[self._display]
    
    @pyqtProperty(str, notify=updated)
    def displayName(self):
        return self._display
    
    @pyqtProperty(str, notify=updated)
    def displayIndex(self):
        if not self._artifacts:
            return ""
        if not self._display:
            return f"1 of {len(self._artifactNames)+1}"
        else:
            idx = self._artifactNames.index(self._display)
            return f"{idx+2} of {len(self._artifactNames)+1}"
        
    @pyqtProperty(QImage, notify=updated)
    def displayFull(self):
        return self.display

    @pyqtSlot()
    def nextDisplay(self):
        if not self._display:
            if self._artifactNames:
                self._display = self._artifactNames[0]
        else:
            idx = self._artifactNames.index(self._display) + 1
            if idx < len(self._artifactNames):
                self._display = self._artifactNames[idx]
            else:
                self._display = None
        self.updated.emit()
    
    @pyqtSlot()
    def prevDisplay(self):
        if not self._display:
            if self._artifactNames:
                self._display = self._artifactNames[-1]
        else:
            idx = self._artifactNames.index(self._display) - 1
            if idx >= 0:
                self._display = self._artifactNames[idx]
            else:
                self._display = None
        self.updated.emit()

    @pyqtProperty(str, notify=updated)
    def file(self):
        return self._file
    
    @pyqtProperty(str, notify=updated)
    def mode(self):
        if not self._metadata:
            return ""
        return self._metadata["mode"]
    
    @pyqtProperty(int, notify=updated)
    def width(self):
        return self.display.width()
    
    @pyqtProperty(int, notify=updated)
    def height(self):
        return self.display.height()

    @pyqtProperty(bool, notify=updated)
    def empty(self):
        return self._image.isNull()
        
    @pyqtProperty(str, notify=updated)
    def size(self):
        if self._image.isNull():
            return ""
        return f"{self._image.width()}x{self._image.height()}"

    @pyqtProperty(str, notify=updated)
    def parameters(self):
        return self._parameters

    @pyqtSlot()
    def drag(self):
        if not self._display:
            self.basic.gui.dragFiles([self._file])
        else:
            self.basic.gui.dragImage(self.display)

    @pyqtSlot()
    def copy(self):
        if not self._display:
            self.basic.gui.copyFiles([self._file])
        else:
            self.basic.gui.copyImage(self.display)

    @pyqtProperty(list, notify=updated)
    def artifacts(self):
        return list(self._artifacts.keys())

    @pyqtSlot(str, result=QImage)
    def artifact(self, name):
        return self._artifacts[name]