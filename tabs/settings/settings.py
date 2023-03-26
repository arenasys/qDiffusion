import math

from PyQt5.QtCore import pyqtProperty, QObject, pyqtSlot
from PyQt5.QtQml import qmlRegisterSingletonType

class Settings(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = math.inf
        self.name = "Settings"
        self.gui = parent

        qmlRegisterSingletonType(Settings, "gui", 1, 0, "SETTINGS", lambda qml, js: self)

    @pyqtSlot()
    def restart(self):
        self.gui.restartBackend()