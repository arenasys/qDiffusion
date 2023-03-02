from PyQt5.QtCore import pyqtSlot, pyqtProperty, QPointF, QObject, QMimeData, QBuffer, QIODevice
from PyQt5.QtGui import QImage
from enum import Enum
import io
import numpy as np

import PIL.Image

class CanvasTool(Enum):
    BRUSH = 1
    ERASE = 2
    RECTANGLE_SELECT = 3
    ELLIPSE_SELECT = 4
    PATH_SELECT = 5
    FUZZY_SELECT = 6
    MOVE = 7

class CanvasSelectionMode(Enum):
    NORMAL = 1
    ADD = 2
    SUBTRACT = 3

class CanvasOperation(Enum):
    UPDATE_STROKE = 1
    STROKE = 2
    UNDO = 3
    SET_SELECTION = 4
    MOVE = 5
    SET_MOVE = 6
    UPDATE_MOVE = 7
    ANCHOR = 8
    PASTE = 9
    COPY = 10
    CUT = 11
    LOAD = 12
    DELETE = 13
    FUZZY = 14
    DESELECT = 15

class CanvasChanges():
    def __init__(self):
        self.reset = False
        self.layer = 1
        self.tool = CanvasTool.ERASE
        self.brush = None
        self.select = None
        self.strokes = []

        self.move = QPointF()
        self.position = QPointF()
        self.selection = []

        self.paste = None

        self.operations = set()

def alignQPointF(point):
    return QPointF(point.toPoint())

def PILtoQImage(pil):
    data = pil.convert("RGBA").tobytes("raw", "RGBA")
    img = QImage(data, pil.size[0], pil.size[1], QImage.Format_RGBA8888)
    img.convertTo(QImage.Format_ARGB32_Premultiplied)
    return img

def QImagetoPIL(img):
    img = img.convertToFormat(QImage.Format_RGBA8888)
    size = (img.size().width(), img.size().height())
    total = size[0]*size[1]*4
    return PIL.Image.frombytes("RGBA", size, img.bits().asarray(total), "raw", "RGBA")

def QImagetoCV2(img):
    img = img.convertToFormat(QImage.Format_RGBA8888)
    size = (img.size().width(), img.size().height())
    total = size[0]*size[1]*4
    arr = np.array(img.bits().asarray(total)).reshape(size[1], size[0], 4)
    return arr

def CV2toQImage(mat):
    width, height, _ = mat.shape
    data = mat.tobytes()
    img = QImage(data, width, height, QImage.Format_RGBA8888)
    img.convertTo(QImage.Format_ARGB32_Premultiplied)
    return img

class MimeData(QObject):
    def __init__(self, mimeData, parent=None):
        super().__init__(parent)
        self._mimeData = mimeData

    @pyqtProperty(QMimeData)
    def mimeData(self):
        return self._mimeData