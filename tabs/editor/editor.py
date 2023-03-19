from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject
from PyQt5.QtQml import qmlRegisterSingletonType

import parameters

class Editor(QObject):
    updated = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 1
        self.name = "Editor"
        self._parameters = parameters.Parameters(parent)
        qmlRegisterSingletonType(Editor, "gui", 1, 0, "EDITOR", lambda qml, js: self)

    @pyqtProperty(parameters.Parameters, notify=updated)
    def parameters(self):
        return self._parameters
