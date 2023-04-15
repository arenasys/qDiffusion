import queue
import multiprocessing
import websockets.sync.client
import websockets.exceptions
import bson
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
    done = pyqtSignal(str)
    def __init__(self, queue, type, file):
        super().__init__()
        self.queue = queue
        self.type = type
        self.file = file
        self.name = file.rsplit(os.path.sep, 1)[-1]
        self.stopping = False

    def run(self):
        try:
            with open(self.file, 'rb') as f:
                i = 0
                while not self.stopping:
                    QApplication.processEvents()
                    chunk = f.read(FRAGMENT_SIZE-1024)
                    if not chunk:
                        break
                    request = {"type":"chunk", "data": {"type":self.type, "name": self.name, "chunk":chunk, "index":i}}

                    while not self.queue.empty():
                        QThread.msleep(10)
                        QApplication.processEvents()
                        if self.stopping:
                            break
                    if self.stopping:
                        break
                    self.queue.put(request)
                    i += 1
        except Exception:
            self.done.emit(self.file)
            return
            
        if self.stopping:
            self.queue.put({"type":"chunk", "data": {"type":self.type, "name": self.name, "index":-1}})
        else:
            self.queue.put({"type":"chunk", "data": {"type":self.type, "name": self.name}})
        self.done.emit(self.file)

    @pyqtSlot()
    def stop(self):
        self.stopping = True

class RemoteInference(QThread):
    kill = pyqtSignal()
    response = pyqtSignal(object)
    def __init__(self, gui, endpoint, password=None):
        super().__init__()
        self.gui = gui

        self.stopping = False
        self.requests = queue.Queue()
        self.responses = queue.Queue()
        self.endpoint = endpoint
        self.client = None

        self.scheme = None
        if not password:
            password = DEFAULT_PASSWORD
        self.scheme = get_scheme(password)
        self.id = None
        self.uploads = {}

    def connect(self):
        if self.client:
            return
        self.onResponse({"type": "status", "data": {"message": "Connecting"}})
        while not self.client and not self.stopping:
            try:
                self.client = websockets.sync.client.connect(self.endpoint, open_timeout=2, close_timeout=0.1, max_size=None)
            except TimeoutError:
                pass
            except ConnectionRefusedError:
                self.onResponse({"type": "remote_error", "data": {"message": "Connection refused"}})
                return
            except Exception as e:
                self.onResponse({"type": "remote_error", "data": {"message": str(e)}})
                return
        if self.stopping:
            return
        if self.client:
            self.onResponse({"type": "status", "data": {"message": "Connected"}})
            self.requests.put({"type":"options"})

    def run(self):
        self.connect()
        while self.client and not self.stopping:
            try:
                QApplication.processEvents()

                try:
                    request = self.requests.get(False)

                    if request["type"] == "upload":
                        file = request["data"]["file"]
                        if not file in self.uploads:
                            self.uploads[file] = RemoteInferenceUpload(self.requests, request["data"]["type"], file)
                            self.uploads[file].done.connect(self.onUploadDone)
                            self.kill.connect(self.uploads[file].stop)
                            self.uploads[file].start()
                            
                        continue

                    data = encrypt(self.scheme, request)
                    data = [data[i:min(i+FRAGMENT_SIZE,len(data))] for i in range(0, len(data), FRAGMENT_SIZE)]

                    self.client.send(data)
                except queue.Empty:
                    try:
                        data = self.client.recv(5/1000)
                    except TimeoutError:
                        QThread.msleep(5)
                        continue
                    response = decrypt(self.scheme, data)
                    self.onResponse(response)
            except websockets.exceptions.ConnectionClosedOK:
                self.onResponse({"type": "remote_error", "data": {"message": "Connection closed"}})
            except Exception as e:
                if type(e) == InvalidToken or type(e) == IndexError:
                    self.onResponse({"type": "remote_error", "data": {"message": "Incorrect password"}})
                else:
                    self.onResponse({"type": "remote_error", "data": {"message": str(e)}})
                    log_traceback("REMOTE")
                return

        if self.client:
            self.client.recv_messages.close()
            self.client.close()
            self.client.socket.close()
            self.client = None

    @pyqtSlot()
    def stop(self):
        for file in self.uploads:
            self.uploads[file].stopping = True
        self.stopping = True

    @pyqtSlot(object)
    def onRequest(self, request):
        self.requests.put(request)

    def onResponse(self, response):
        if response["type"] == "result":
            self.saveResults(response["data"]["images"], response["data"]["metadata"])
        self.response.emit(response)

    def saveResults(self, images, metadata):
        for i in range(len(images)):
            save_image(images[i], metadata[i], self.gui.outputDirectory())

    @pyqtSlot(str)
    def onUploadDone(self, file):
        if file in self.uploads:
            del self.uploads[file]