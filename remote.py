import os
import shutil
import sys
import subprocess
import traceback
import io
import queue
import threading
import multiprocessing
import websocket as ws_client
import bson

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

from parameters import save_image

class RemoteInference(QThread):
    response = pyqtSignal(int, object)
    def __init__(self, endpoint):
        super().__init__()

        self.stopping = False
        self.requests = multiprocessing.Queue(16)
        self.responses = multiprocessing.Queue(16)
        self.endpoint = endpoint
        self.client = ws_client.WebSocket()

    def connect(self):
        if self.client.connected:
            return
        
        self.onResponse(-1, {"type": "status", "data": {"message": "Connecting"}})
        while not self.client.connected and not self.stopping:
            try:
                self.client.connect(self.endpoint)
            except Exception as e:
                QApplication.processEvents()
                QThread.msleep(10)
                pass
        self.onResponse(-1, {"type": "status", "data": {"message": "Connected"}})

    def run(self):
        self.id = -1
        requesting = True
        
        while not self.stopping:
            self.connect()
            try:
                QApplication.processEvents()
                QThread.msleep(10)

                if requesting:
                    self.id, request = self.requests.get(False)
                    requesting = False
                    self.client.send_binary(bson.dumps(request))
                else:
                    response = self.client.recv()
                    response = bson.loads(response)
                    self.onResponse(self.id, response)
                    if not response["type"] in {"progress", "status"}:
                        requesting = True
            except queue.Empty:
                pass
            except Exception as e:
                if str(e) in {"socket is already closed.", "[Errno 32] Broken pipe"}:
                    continue

                if not self.client.connected:
                    requesting = True
                    self.onResponse(-1, {"type": "error", "data": {"message": str(e)}})
                else:
                    raise e
            
    @pyqtSlot()
    def stop(self):
        self.requests.put((-1, {"type": "stop", "data":{}}))
        self.stopping = True
        if self.client.connected:
            self.client.close()

    @pyqtSlot(int, object)
    def onRequest(self, id, request):
        self.requests.put((id, request))

    @pyqtSlot(int)
    def onCancel(self, id):
        if self.client.connected:
            self.client.send_binary(bson.dumps({"type": "cancel", "data":{}}))

    def onResponse(self, id, response):
        if response["type"] == "result":
            self.saveResults(response["data"]["images"], response["data"]["metadata"])

        self.response.emit(id, response)

    def saveResults(self, images, metadata):
        for i in range(len(images)):
            save_image(images[i], metadata[i])