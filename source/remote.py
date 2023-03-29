import queue
import multiprocessing
import websocket as ws_client
import bson

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

from parameters import save_image

import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

def get_scheme(password):
    password = password.encode("utf8")
    h = hashes.Hash(hashes.SHA256())
    h.update(password)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=h.finalize()[:16], #lol
        iterations=480000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password))
    return Fernet(key)

class RemoteInference(QThread):
    response = pyqtSignal(int, object)
    def __init__(self, endpoint, password=None):
        super().__init__()

        self.stopping = False
        self.requests = multiprocessing.Queue(16)
        self.responses = multiprocessing.Queue(16)
        self.endpoint = endpoint
        self.client = ws_client.WebSocket()

        self.scheme = None
        if password:
            self.scheme = get_scheme(password)

    def connect(self):
        if self.client.connected:
            return
        
        self.onResponse(-1, {"type": "status", "data": {"message": "Connecting"}})
        while not self.client.connected and not self.stopping:
            try:
                self.client.connect(self.endpoint)
            except Exception as e:
                for _ in range(100):
                    QApplication.processEvents()
                    QThread.msleep(10)
                pass
        self.onResponse(-1, {"type": "status", "data": {"message": "Connected"}})
        self.requests.put((-1, {"type":"options"}))

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
                    data = bson.dumps(request)
                    if self.scheme:
                        data = self.scheme.encrypt(data)
                    self.client.send_binary(data)
                else:
                    data = self.client.recv()
                    if self.scheme:
                        data = self.scheme.decrypt(data)
                    response = bson.loads(data)
                    self.onResponse(self.id, response)
                    if not response["type"] in {"progress", "status"}:
                        requesting = True
            except queue.Empty:
                pass
            except Exception as e:
                if str(e) in {"socket is already closed.", "[Errno 32] Broken pipe"}:
                    continue
                if type(e) == InvalidToken:
                    self.onResponse(-1, {"type": "error", "data": {"message": "Incorrect password"}})
                    requesting = True
                elif not self.client.connected:
                    self.onResponse(-1, {"type": "error", "data": {"message": str(e)}})
                    requesting = True
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