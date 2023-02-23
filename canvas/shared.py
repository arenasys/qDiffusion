from PyQt5.QtCore import pyqtSlot, pyqtProperty
from PyQt5.QtCore import QPointF, QObject, QMimeData
from enum import Enum

class CanvasTool(Enum):
    BRUSH = 1
    ERASE = 2
    RECTANGLE_SELECT = 3
    ELLIPSE_SELECT = 4
    PATH_SELECT = 5
    MOVE = 6

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

class CanvasChanges():
    def __init__(self):
        self.reset = False
        self.layer = 1
        self.tool = CanvasTool.ERASE
        self.brush = None
        self.strokes = []

        self.move = QPointF()
        self.selection = []

        self.paste = None

        self.operations = set()

def alignQPointF(point):
    return QPointF(point.toPoint())

class MimeData(QObject):
    def __init__(self, mimeData, parent=None):
        super().__init__(parent)
        self._mimeData = mimeData

    @pyqtProperty(QMimeData)
    def mimeData(self):
        return self._mimeData