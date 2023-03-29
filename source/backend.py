import random
import queue

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication

import local
import remote

class Backend(QObject):
    request = pyqtSignal(int, object)
    response = pyqtSignal(int, object)
    cancel = pyqtSignal(int)
    stopping = pyqtSignal()

    def __init__(self, parent, endpoint="", password=""):
        super().__init__(parent)
        self.responses = queue.Queue()

        self.setEndpoint(endpoint, password)
        
        parent.aboutToQuit.connect(self.stop)

    def setEndpoint(self, endpoint, password):
        if endpoint == "":
            self.inference = local.LocalInference()
        else:
            self.inference = remote.RemoteInference(endpoint, password)

        self.inference.start()
        self.request.connect(self.inference.onRequest)
        self.cancel.connect(self.inference.onCancel)
        self.inference.response.connect(self.onResponse)
        self.stopping.connect(self.inference.stop)

    @pyqtSlot()
    def stop(self):
        self.stopping.emit()

    def wait(self):
        self.inference.wait()
    
    @pyqtSlot(int, object)
    def makeRequest(self, id, request):
        self.request.emit(id, request)
        return id

    @pyqtSlot(int)
    def cancelRequest(self, id):
        self.cancel.emit(id)

    @pyqtSlot(int, object)
    def onResponse(self, id, response):
        self.response.emit(id, response)
