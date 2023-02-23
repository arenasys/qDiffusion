from PyQt5.QtCore import pyqtProperty, pyqtSlot, pyqtSignal, QObject, Qt, QByteArray
from PyQt5.QtQml import qmlRegisterSingletonType, qmlRegisterType
from PyQt5.QtGui import QImage
class img2img(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 1
        self.name = "Img2Img"
        qmlRegisterSingletonType(img2img, "gui", 1, 0, "IMG2IMG", lambda qml, js: self)