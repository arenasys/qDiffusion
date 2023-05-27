from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtQml import qmlRegisterSingletonType

import parameters

class Editor(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 4
        self.hidden = True
        self.name = "Editor"