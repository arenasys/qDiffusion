from PyQt5.QtCore import pyqtProperty, QObject

class img2img(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.priority = 1
        self.name = "Img2Img"
        self.qml = f"qrc:/tabs/img2img/img2img.qml"