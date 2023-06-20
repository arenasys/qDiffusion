from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, QSize, QUrl, QMimeData, QByteArray, Qt, QRect
from PyQt5.QtGui import QImage, QDrag
from PyQt5.QtWidgets import QApplication
from enum import Enum

import parameters
from misc import MimeData, sortFiles, cropImage
from canvas.shared import QImagetoPIL
import math
import os
import glob

MIME_BASIC_INPUT = "application/x-qd-basic-input"

class BasicInputRole(Enum):
    IMAGE = 1
    MASK = 2
    SUBPROMPT = 3
    CONTROL = 4

INPUT_ID = 1

class BasicInput(QObject):
    updated = pyqtSignal()
    linkedUpdated = pyqtSignal()
    extentUpdated = pyqtSignal()
    folderUpdated = pyqtSignal()
    def __init__(self, basic, image=QImage(), role=BasicInputRole.IMAGE):
        global INPUT_ID
        super().__init__(basic)
        self.basic = basic
        self._originalCrop = None
        self._original = image.copy()
        self._image = image
        self._role = role
        self._linked = None
        self._dragging = False
        self._offset = 0.5

        self._display = None
        self._artifacts = {}
        self._artifactNames = []

        self._id = INPUT_ID
        INPUT_ID += 1

        # Masks
        self._extent = QRect()
        self._extentWarning = False
        
        # ControlNet
        self._mode = ""
        self._settings = parameters.VariantMap(self, {
            "mode": "", "CN_strength":1.0, "CN_preprocessors": [], "CN_preprocessor": "", "CN_bools": ["False", "True"],
            "CN_bool": "False", "CN_bool_label": "", "CN_slider_a": 0.0, "CN_slider_a_label": "", "CN_slider_b": 0.0, "CN_slider_b_label": ""
            })
        self._settings.updated.connect(self.onSettingsUpdated)

        # Subprompts
        self._areas = []

        # Bulk inputs
        self._folder = ""
        self._files = []
        self._currentFile = ""
        self._originalFile = QImage()
        self._file = QImage()

        basic.parameters._values.updated.connect(self.updateImage)

    def updateImage(self):
        if self._image and not self._image.isNull():
            if self._linked and self._linked.image and not self._linked.image.isNull():
                bg = self._linked.image
                self.resizeImage(bg.size())
            else:
                if self._role == BasicInputRole.IMAGE and self.basic.hasMask(self):
                    self._image = self._original
                    self._originalCrop = None
                else:
                    w,h = self.basic.parameters.values.get("width"),  self.basic.parameters.values.get("height")
                    self.resizeImage(QSize(int(w),int(h)))
        
        if self._currentFile:
            self.getFile()

        self.updateExtent()
        self.updated.emit()

    def resizeImage(self, out_z):
        self._originalCrop = cropImage(self._original, out_z, self._offset)
        self._image = self._originalCrop.scaled(out_z, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

    @pyqtSlot(QUrl)
    def saveImage(self, file):
        file = file.toLocalFile()
        if not "." in file.rsplit(os.path.sep,1)[-1]:
            file = file + ".png"
        try:
            self.display.save(file)
        except Exception:
            pass

    def setLinked(self, linked):
        prevLinked = self._linked
        self._linked = linked
        if prevLinked:
            prevLinked.updated.disconnect(self.updateImage)
            prevLinked.updateLinked()
        if self._linked:
            self._linked.updated.connect(self.updateImage)
            self._linked.updateLinked()
        self.updateLinked()

    @pyqtSlot()
    def updateLinked(self):
        self.updateImage()
        self.linkedUpdated.emit()
    
    @pyqtProperty(int, notify=updated)
    def role(self):
        return self._role.value

    @role.setter
    def role(self, role):
        self._role = BasicInputRole(role)
        if self._role != BasicInputRole.CONTROL:
            self._settings.set("mode", "")
        self.updated.emit()
        self.parent().updated.emit()

    @pyqtProperty(QImage, notify=updated)
    def image(self):
        return self._image
    
    @pyqtProperty(int, notify=updated)
    def width(self):
        if not self._file.isNull():
            return self._file.width()
        return self._image.width()
    
    @pyqtProperty(int, notify=updated)
    def height(self):
        if not self._file.isNull():
            return self._file.height()
        return self._image.height()
    
    @pyqtProperty(int, notify=updated)
    def dropWidth(self):
        if not self._originalFile.isNull():
            return self._originalFile.width()
        if not self._original.isNull():
            return self._original.width()
        return self._image.width()
    
    @pyqtProperty(int, notify=updated)
    def dropHeight(self):
        if not self._originalFile.isNull():
            return self._originalFile.height()
        if not self._original.isNull():
            return self._original.width()
        return self._image.height()
    
    @pyqtProperty(float, notify=updated)
    def offset(self):
        return self._offset
    
    @offset.setter
    def offset(self, offset):
        self._offset = max(0.0, min(1.0, offset))
        self.updateImage()

    @pyqtProperty(bool, notify=updated)
    def offsetDirection(self):
        rw = self._image.width() / self._original.width()
        rh = self._image.height() / self._original.height()
        return rw > rh
    
    @pyqtProperty(int, notify=updated)
    def originalWidth(self):
        return self._original.width()
    
    @pyqtProperty(int, notify=updated)
    def originalHeight(self):
        return self._original.height()

    @pyqtProperty(bool, notify=updated)
    def empty(self):
        return self._image.isNull()
    
    @pyqtProperty(bool, notify=updated)
    def hasSource(self):
        return (not self._image.isNull()) or (self._folder != "")

    @pyqtProperty(bool, notify=linkedUpdated)
    def linked(self):
        return self._linked != None
    
    @pyqtProperty(bool, notify=linkedUpdated)
    def linkedTo(self):
        i = self.basic._inputs.index(self) + 1
        if i >= len(self.basic._inputs):
            return False
        return self.basic._inputs[i]._linked != None

    @pyqtProperty(QImage, notify=linkedUpdated)
    def linkedImage(self):
        if not self._linked:
            return QImage()
        return self._linked._image
    
    @pyqtProperty(int, notify=linkedUpdated)
    def linkedWidth(self):
        if not self._linked or not self._linked._image.width():
            return int(self.basic.parameters.values.get("width"))
        return self._linked._image.width()
    
    @pyqtProperty(int, notify=linkedUpdated)
    def linkedHeight(self):
        if not self._linked or not self._linked._image.height():
            return int(self.basic.parameters.values.get("height"))
        return self._linked._image.height()
        
    @pyqtProperty(str, notify=updated)
    def size(self):
        if self._image.isNull():
            return ""
        o = self._originalCrop or self._original
        return f"{o.width()}x{o.height()}"
    
    @pyqtProperty(QRect, notify=extentUpdated)
    def extent(self):
        return self._extent
    
    @pyqtProperty(bool, notify=extentUpdated)
    def extentWarning(self):
        return self._extentWarning
    
    @pyqtProperty(parameters.VariantMap, notify=updated)
    def settings(self):
        return self._settings
    
    @pyqtSlot(str)
    def onSettingsUpdated(self, key):
        if key == "mode":
            value = self._settings.get("mode")
            self._mode = value

            self._settings.set("CN_preprocessors", self.basic._parameters._values.get("CN_preprocessors"))
            self._settings.set("CN_preprocessor", value)

            self.setArtifacts({})
            
            self.updated.emit()
            self.parent().updated.emit()
        if key == "CN_preprocessor":
            self.setArtifacts({})

            value = self._settings.get("CN_preprocessor")
            settings = {
                "CN_bool_label": "", "CN_slider_a_label": "", "CN_slider_b_label": ""
            }
            if value == "Canny":
                settings = {
                    "CN_bool_label": "",
                    "CN_slider_a": 0.4, "CN_slider_a_label": "Lower threshold",
                    "CN_slider_b": 0.8, "CN_slider_b_label": "Upper threshold"
                }
            if value == "Mlsd":
                settings = {
                    "CN_bool_label": "",
                    "CN_slider_a": 0.1, "CN_slider_a_label": "Score threshold",
                    "CN_slider_b": 0.1, "CN_slider_b_label": "Distance threshold"
                }
            if value == "Pose":
                settings = {
                    "CN_bool": "False", "CN_bool_label": "Hands and Face",
                    "CN_slider_a_label": "", "CN_slider_b_label": ""
                }
            for k,v in settings.items():
                self._settings.set(k,v)

    @pyqtProperty(str, notify=updated)
    def mode(self):
        return self._mode

    @pyqtSlot()
    def annotate(self):
        self.basic.annotate(self)

    def getCNArgs(self):
        args = []
        if self._settings.get("CN_slider_a_label"):
            args += [self._settings.get("CN_slider_a")]
        if self._settings.get("CN_slider_b_label"):
            args += [self._settings.get("CN_slider_b")]
        if self._settings.get("CN_bool_label"):
            args += [self._settings.get("CN_bool") == "True"]
        return args
    
    def setArtifacts(self, artifacts):
        self._artifacts = artifacts
        self._artifactNames = list(self._artifacts.keys())
        if self._artifactNames:
            self._display = self._artifactNames[-1]
        else:
            self._display = None
        self.updated.emit()
    
    @pyqtProperty(QImage, notify=updated)
    def display(self):
        if not self._display:
            return self._image
        return self._artifacts[self._display]
    
    @pyqtProperty(str, notify=updated)
    def displayName(self):
        return ["", "Image", "Mask", "Subprompts", "Control"][self._role.value]
    
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
        if not self._file.isNull():
            return self._file
        return self.display

    @pyqtSlot()
    def nextDisplay(self):
        if self._currentFile:
            i = self._files.index(self._currentFile) + 1
            if i < len(self._files):
                self.setFile(self._files[i])
            self.updated.emit()
            return
        
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
        if self._currentFile:
            i = self._files.index(self._currentFile) - 1
            if i >= 0:
                self.setFile(self._files[i])
            self.updated.emit()
            return

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

    @pyqtSlot()
    def resetDisplay(self):
        self._display = None
        self.updated.emit()

    def resetAnnotation(self):
        self.setArtifacts({})

    def getAreas(self):
        out = []
        for a in self._areas:
            size = self._image.size()
            a = a.scaled(size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            dx = int((a.width()-size.width())*self._offset)
            dy = int((a.height()-size.height())*self._offset)
            a = a.copy(dx, dy, size.width(), size.height())
            out += [a]
        return out

    @pyqtSlot(QUrl)
    def setImageFile(self, path):
        self._image = QImage(path.toLocalFile())
        self._original = self._image.copy()
        self.updateImage()
        self.resetAnnotation()

    @pyqtSlot()
    def setImageCanvas(self):
        w,h = 0,0
        if self._linked:
            w,h = self._linked._image.size().width(),  self._linked._image.size().height()
        if not w or not w:
            w,h = self.basic.parameters.values.get("width"),  self.basic.parameters.values.get("height")
        self._image = QImage(QSize(int(w),int(h)), QImage.Format_ARGB32_Premultiplied)
        self._image.fill(0)
        self._original = self._image.copy()
        self.updateImage()
        self.resetAnnotation()

    @pyqtSlot(MimeData, int)
    def setImageDrop(self, mimeData, index):
        mimeData = mimeData.mimeData
        found = False
        if MIME_BASIC_INPUT in mimeData.formats():
            source = int(str(mimeData.data(MIME_BASIC_INPUT), 'utf-8'))
            if source != index:
                source = self.basic._inputs[source]
                if not source._display:
                    self._image = source._original
                    self._offset = source._offset
                else:
                    self._image = source.display
                found = True
        else:
            source = mimeData.imageData()
            if source and not source.isNull():
                self._image = source
                found = True
            else:
                for url in mimeData.urls():
                    if url.isLocalFile():
                        self._image = QImage(url.toLocalFile())
                        found = True
                        break
                    elif url.scheme() == "http" or url.scheme() == "https":
                        if url.fileName().rsplit(".")[-1] in {"png", "jpg", "jpeg", "webp", "gif"}:
                            self.basic.download(url, index)
                            break

        if found:
            self._original = self._image.copy()
            self.updateImage()
            self.resetAnnotation()

    @pyqtSlot(QImage)
    def setImageData(self, data):
        self._image = data

        self._original = self._image.copy()
        self.updateImage()
        self.resetAnnotation()

    def updateExtent(self):
        if self._role != BasicInputRole.MASK or not self._image or self._image.isNull():
            self._extent = QRect()
            self.updated.emit()
            return
                
        img = QImagetoPIL(self._image)
        bound = img.getbbox()
        if bound == None:
            self._extent = QRect()
            self.extentUpdated.emit()
            return

        source = (self._image.width(), self._image.height())
        padding = self.parent()._parameters._values.get("padding")
        working = (self.parent()._parameters._values.get("width"), self.parent()._parameters._values.get("height"))
        
        x1,y1,x2,y2 = parameters.getExtent(bound, padding, source, working)
        self._extent = QRect(x1,y1,x2-x1,y2-y1)
        self._extentWarning = (x2-x1) > working[0] or (y2-y1) > working[1]
        self.extentUpdated.emit()

    @pyqtSlot()
    def clearImage(self):
        self._image = QImage()
        self.updateImage()

    def getMimeData(self, index):
        mimeData = QMimeData()
        mimeData.setData(MIME_BASIC_INPUT, QByteArray(f"{index}".encode()))
        mimeData.setImageData(self._image)
        return mimeData

    @pyqtSlot(int)
    def drag(self, index):
        if self._dragging:
            return
        self._dragging = True
        drag = QDrag(self)
        drag.setMimeData(self.getMimeData(index))
        drag.exec()
        self._dragging = False

    @pyqtSlot(int)
    def copy(self, index):
        QApplication.clipboard().setMimeData(self.getMimeData(index))

    @pyqtProperty(str, notify=folderUpdated)
    def folder(self):
        return self._folder
    
    @pyqtProperty(list, notify=folderUpdated)
    def files(self):
        return self._files
    
    @pyqtProperty(str, notify=folderUpdated)
    def currentFile(self):
        return self._currentFile
    
    @pyqtSlot(str)
    def setFolder(self, folder):
        folder = QUrl(folder).toLocalFile()
        files = glob.glob(os.path.join(folder, "*.png")) + glob.glob(os.path.join(folder, "*.jpg"))
        files = sortFiles([f.rsplit(os.path.sep)[-1] for f in files])

        if files:
            self._folder = folder
            self._files = files
            self.updated.emit()
            self.folderUpdated.emit()

    def getFile(self):
        filePath = os.path.join(self._folder, self._currentFile)
        self._originalFile = QImage(filePath)

        w,h = self.basic.parameters.values.get("width"),  self.basic.parameters.values.get("height")
        size = QSize(int(w),int(h))

        self._file = cropImage(self._originalFile, size)
    
    def getFilePath(self, file):
        return os.path.join(self._folder, file)

    @pyqtSlot(str)
    def setFile(self, file):
        filePath = os.path.join(self._folder, file)
        if os.path.exists(filePath):
            self._currentFile = file
            self.getFile()
            self.folderUpdated.emit()
            self.updated.emit()
