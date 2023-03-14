from PyQt5.QtCore import pyqtProperty, QObject

class basic(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 0
        self.name = "Basic"