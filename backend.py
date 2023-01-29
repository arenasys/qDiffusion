import random
import queue

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication

import local

class Backend(QObject):
    request = pyqtSignal(int, object)
    response = pyqtSignal(int, object)
    cancel = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.inference = local.LocalInference()
        self.responses = queue.Queue()

        self.inference.start()

        self.request.connect(self.inference.onRequest)
        self.cancel.connect(self.inference.onCancel)
        self.inference.response.connect(self.onResponse)
        
        parent.aboutToQuit.connect(self.inference.stop)

    def wait(self):
        self.inference.wait()
    
    @pyqtSlot(object, result=int)
    def makeRequest(self, request):
        id = random.randrange(4294967294)
        self.request.emit(id, request)
        return id

    @pyqtSlot(int)
    def cancelRequest(self, id):
        self.cancel.emit(id)

    @pyqtSlot(int, object)
    def onResponse(self, id, response):
        self.response.emit(id, response)
