import queue
import multiprocessing
import websocket as ws_client
import bson
import select
import os
import traceback
import datetime
import sys

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

from parameters import save_image

import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

DEFAULT_PASSWORD = "qDiffusion"

def log_traceback(label):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a") as f:
        f.write(f"{label} {datetime.datetime.now()}\n{tb}\n")
    print(tb)

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

def encrypt(scheme, obj):
    data = bson.dumps(obj)
    if scheme:
        data = base64.urlsafe_b64decode(scheme.encrypt(data))
    return data

def decrypt(scheme, data):
    if scheme:
        data = scheme.decrypt(base64.urlsafe_b64encode(data))
    obj = bson.loads(data)
    return obj

class RemoteInferenceUpload(QThread):
    done = pyqtSignal()
    def __init__(self, queue, type, file):
        super().__init__()
        self.queue = queue
        self.type = type
        self.file = file
        self.name = file.rsplit(os.path.sep, 1)[-1]

    def run(self):
        with open(self.file, 'rb') as f:
            i = 0
            while True:
                chunk = f.read(1024*1024)
                if not chunk:
                    break
                request = {"type":"chunk", "data": {"type":self.type, "name": self.name, "chunk":chunk, "index":i}}

                while not self.queue.empty():
                    QThread.msleep(10)
                self.queue.put((-1, request))
                i += 1

        self.queue.put((-1, {"type":"chunk", "data": {"type":self.type, "name": self.name}}))
        self.done.emit()

class RemoteInference(QThread):
    response = pyqtSignal(int, object)
    def __init__(self, endpoint, password=None):
        super().__init__()

        self.stopping = False
        self.requests = multiprocessing.Queue(16)
        self.responses = multiprocessing.Queue(16)
        self.endpoint = endpoint
        self.client = ws_client.WebSocket()
        self.client.settimeout(5)

        self.scheme = None
        if not password:
            password = DEFAULT_PASSWORD
        self.scheme = get_scheme(password)

    def connect(self, once=False):
        if self.client.connected:
            return
        
        self.onResponse(-1, {"type": "status", "data": {"message": "Connecting"}})
        while not self.client.connected and not self.stopping:
            try:
                self.client.connect(self.endpoint)
            except Exception as e:
                for _ in range(100):
                    if self.stopping:
                        return
                    QApplication.processEvents()
                    QThread.msleep(10)
                pass
            if once:
                break
        if self.stopping:
            return 
        if self.client.connected:
            self.onResponse(-1, {"type": "status", "data": {"message": "Connected"}})
            self.requests.put((-1, {"type":"options"}))

    def run(self):
        ctr = 0
        self.id = -1
        while not self.stopping:
            self.connect()
            
            try:
                QApplication.processEvents()

                if ctr == 200:
                    self.requests.put((-1, {"type":"ping"}))
                    ctr = 0
                ctr += 1

                if not self.requests.empty():
                    self.id, request = self.requests.get(False)
                    if request["type"] == "upload":
                        thread = RemoteInferenceUpload(self.requests, request["data"]["type"], request["data"]["file"])
                        thread.start()
                        continue
                    
                    data = encrypt(self.scheme, request)
                    self.client.send_binary(data)
                    ctr = 0
                else:
                    rd, _, _ = select.select([self.client], [], [], 0)
                    if not rd:
                        QThread.msleep(10)
                        continue
                    data = self.client.recv()
                    ctr = 0
                    if data:
                        response = decrypt(self.scheme, data)
                        self.onResponse(self.id, response)
            except queue.Empty:
                pass
            except Exception as e:
                if str(e) in {"socket is already closed.", "[Errno 32] Broken pipe"}:
                    continue
                if type(e) == InvalidToken or type(e) == IndexError:
                    self.onResponse(-1, {"type": "error", "data": {"message": "Incorrect password"}})
                    break
                else:
                    self.onResponse(-1, {"type": "error", "data": {"message": str(e)}})
                    log_traceback("REMOTE")
            
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
            data = encrypt(self.scheme, {"type": "cancel", "data":{}})
            self.client.send_binary(data)

    def onResponse(self, id, response):
        if response["type"] == "result":
            self.saveResults(response["data"]["images"], response["data"]["metadata"])

        self.response.emit(id, response)

    def saveResults(self, images, metadata):
        for i in range(len(images)):
            save_image(images[i], metadata[i])