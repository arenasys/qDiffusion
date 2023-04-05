import random
import queue
import json
import bson
import datetime
import copy

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

def hideBytes(d):
    if type(d) == dict:
        for k,v in d.items():
            if type(v) in {bytes, bytearray}:
                d[k] = "..."
            if type(v) in {dict, list}:
                hideBytes(d[k])
    elif type(d) == list:
        for i in range(len(d)):
            if type(d[i]) in {bytes, bytearray}:
                d[i] = "..."
            if type(d[i]) in {dict, list}:
                hideBytes(d[i])

class Backend(QObject):
    request = pyqtSignal(object)
    response = pyqtSignal(object)
    stopping = pyqtSignal()

    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.responses = queue.Queue()
        self.inference = None
        gui.aboutToQuit.connect(self.stop)

    def setEndpoint(self, endpoint, password):
        self.debugLogging("NEW SESSION", {"endpoint": endpoint})
        self.inference = None
        if endpoint == "":
            if HAVE_TORCH:
                
                self.inference = local.LocalInference(self.gui)
            else:
                self.onResponse({"type": "remote_only"})
                return
        else:
            self.inference = remote.RemoteInference(self.gui, endpoint, password)

        self.inference.start()
        self.request.connect(self.inference.onRequest)
        self.inference.response.connect(self.onResponse)
        self.stopping.connect(self.inference.stop)

    @pyqtSlot()
    def stop(self):
        self.stopping.emit()

    @pyqtSlot()
    def started(self):
        if self.inference and type(self.inference) == local.LocalInference:
            print("WATCH")
            self.gui.watchModelDirectory()

    def wait(self):
        if self.inference:
            self.inference.wait()
    
    def debugLogging(self, type, data):
        if self.gui._debugJSONLogging:
            j = copy.deepcopy(data)
            hideBytes(j)
            j = json.dumps(j)
            with open("debug.log", "a") as f:
                f.write(f"{type} {datetime.datetime.now()}\n{j}\n")

    @pyqtSlot(object)
    def makeRequest(self, request):
        self.debugLogging("REQUEST", request)
        self.request.emit(request)

    @pyqtSlot(object)
    def onResponse(self, response):
        self.debugLogging("RESPONSE", response)
        self.response.emit(response)
