import random
import queue

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication

import local
import remote

HAVE_TORCH = False
try:
    import torch
    HAVE_TORCH = True
except ImportError as e:
    pass

class Backend(QObject):
    request = pyqtSignal(object)
    response = pyqtSignal(object)
    stopping = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.responses = queue.Queue()
        self.inference = None
        parent.aboutToQuit.connect(self.stop)

    def setEndpoint(self, endpoint, password):
        self.inference = None
        if endpoint == "":
            if HAVE_TORCH:
                self.inference = local.LocalInference()
            else:
                self.response.emit(-1, {"type": "remote_only"})
                return
        else:
            self.inference = remote.RemoteInference(endpoint, password)

        self.inference.start()
        self.request.connect(self.inference.onRequest)
        self.inference.response.connect(self.onResponse)
        self.stopping.connect(self.inference.stop)

    @pyqtSlot()
    def stop(self):
        self.stopping.emit()

    def wait(self):
        if self.inference:
            self.inference.wait()
    
    @pyqtSlot(object)
    def makeRequest(self, request):
        self.request.emit(request)

    @pyqtSlot(object)
    def onResponse(self, response):
        self.response.emit(response)
