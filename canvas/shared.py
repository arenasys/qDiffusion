from PyQt5.QtCore import QPointF
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
    STROKE = 1
    SAVE_STATE = 2
    RESTORE_STATE = 3
    UPDATE_SELECTION = 4
    START_MOVE = 5
    UPDATE_MOVE = 6
    END_MOVE = 7

class CanvasChanges():
    def __init__(self):
        self.reset = False
        self.layer = 1
        self.tool = CanvasTool.ERASE
        self.brush = None
        self.strokes = []

        self.move = QPointF()
        self.selection = []

        self.operations = set()