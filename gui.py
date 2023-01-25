from PyQt5.QtCore import pyqtProperty, QObject

class GUI(QObject):
    @pyqtProperty('QString', constant=True)
    def title(self):
        return "SD Inference GUI"