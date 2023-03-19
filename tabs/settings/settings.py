import math

from PyQt5.QtCore import pyqtProperty, QObject

class Settings(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = math.inf
        self.name = "Settings"