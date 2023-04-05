import queue
import multiprocessing
import websockets.sync.client
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
FRAGMENT_SIZE = 1048576

def log_traceback(label):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a") as f:
        f.write(f"{label} {datetime.datetime.now()}\n{tb}\n")
    print(label, tb)

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
                chunk = f.read(1000000)
                if not chunk:
                    break
                request = {"type":"chunk", "data": {"type":self.type, "name": self.name, "chunk":chunk, "index":i}}

                while not self.queue.empty():
                    QThread.msleep(10)
                self.queue.put(request)
                i += 1

        self.queue.put({"type":"chunk", "data": {"type":self.type, "name": self.name}})
        self.done.emit()

class RemoteInference(QThread):
    response = pyqtSignal(object)
    def __init__(self, gui, endpoint, password=None):
        super().__init__(gui)
        self.gui = gui

        self.stopping = False
        self.requests = multiprocessing.Queue(16)
        self.responses = multiprocessing.Queue(16)
        self.endpoint = endpoint
        self.client = None

        self.scheme = None
        if not password:
            password = DEFAULT_PASSWORD
        self.scheme = get_scheme(password)
        self.id = None

    def connect(self):
        if self.client:
            return
        self.onResponse({"type": "status", "data": {"message": "Connecting"}})
        while not self.client and not self.stopping:
            try:
                self.client = websockets.sync.client.connect(self.endpoint, open_timeout=2, max_size=None)
            except TimeoutError:
                pass
            except Exception as e:
                self.onResponse({"type": "remote_error", "data": {"message": str(e)}})
                return
        if self.stopping:
            return
        if self.client:
            self.onResponse({"type": "status", "data": {"message": "Connected"}})
            self.requests.put({"type":"options"})

    def run(self):
        while not self.stopping:
            self.connect()
            if not self.client:
                return
            try:
                QApplication.processEvents()

                if not self.requests.empty():
                    request = self.requests.get()

                    if request["type"] == "upload":
                        thread = RemoteInferenceUpload(self.requests, request["data"]["type"], request["data"]["file"])
                        thread.start()
                        continue

                    data = encrypt(self.scheme, request)
                    data = [data[i:min(i+FRAGMENT_SIZE,len(data))] for i in range(0, len(data), FRAGMENT_SIZE)]

                    self.client.send(data)
                else:
                    try:
                        data = self.client.recv(0)
                    except TimeoutError:
                        QThread.msleep(10)
                        continue
                    if data:
                        response = decrypt(self.scheme, data)
                        self.onResponse(response)
            except queue.Empty:
                pass
            except Exception as e:
                if type(e) == InvalidToken or type(e) == IndexError:
                    self.onResponse({"type": "remote_error", "data": {"message": "Incorrect password"}})
                else:
                    self.onResponse({"type": "remote_error", "data": {"message": str(e)}})
                    log_traceback("REMOTE")
                return
            
    @pyqtSlot()
    def stop(self):
        self.stopping = True
        if self.client:
            self.client.close()
            self.client = None

    @pyqtSlot(object)
    def onRequest(self, request):
        self.requests.put(request)

    def onResponse(self, response):
        if response["type"] == "result":
            self.saveResults(response["data"]["images"], response["data"]["metadata"])
        self.response.emit(response)

    def saveResults(self, images, metadata):
        for i in range(len(images)):
            save_image(images[i], metadata[i], self.gui._output_directory)