import random
import queue

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication

import local

class Backend(QObject):
    request = pyqtSignal(int, object)
    response = pyqtSignal(int, object)
    cancel = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.inference = local.LocalInference()
        self.responses = queue.Queue()

        self.inferenceThread = QThread()
        self.inferenceThread.started.connect(self.inference.start)
        self.inference.moveToThread(self.inferenceThread)
        self.inferenceThread.start()

        self.request.connect(self.inference.onRequest)
        self.cancel.connect(self.inference.onCancel)
        self.inference.response.connect(self.onResponse)

    def stop(self):
        self.inference.stopping = True
        self.inferenceThread.join()
    
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
