from PyQt5.QtCore import pyqtProperty, QObject

class txt2img(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 0
        self.name = "Txt2Img"
        self.qml = f"qrc:/tabs/txt2img/txt2img.qml"