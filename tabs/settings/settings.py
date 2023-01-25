import math

from PyQt5.QtCore import pyqtProperty, QObject

class settings(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = math.inf
        self.name = "Settings"
        self.qml = f"qrc:/tabs/settings/settings.qml"