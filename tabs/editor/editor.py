from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, Qt, QByteArray
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterType
from PyQt5.QtGui import QImage
class editor(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 1
        self.name = "Editor"
        qmlRegisterSingletonType(editor, "gui", 1, 0, "EDITOR", lambda qml, js: self)