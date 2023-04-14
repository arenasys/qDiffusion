import platform

from PyQt5.QtCore import pyqtProperty, pyqtSignal, QObject, pyqtSlot
from PyQt5.QtQml import qmlRegisterSingletonType

class Explorer(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 1
        self.name = "Models"
        self.gui = parent

        qmlRegisterSingletonType(Explorer, "gui", 1, 0, "EXPLORER", lambda qml, js: self)