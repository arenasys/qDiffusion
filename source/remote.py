import queue
import multiprocessing
import websockets.sync.client
import websockets.exceptions
import bson
import os
import traceback
import datetime
import sys
import math

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

DEFAULT_PASSWORD = "qDiffusion"
FRAGMENT_SIZE = 524288

def log_traceback(label):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a", encoding='utf-8') as f:
        f.write(f"{label} {datetime.datetime.now()}\n{tb}\n")
    print(label, tb)
    return tb

def get_scheme(password):
    password = password.encode("utf8")
    h = hashes.Hash(hashes.SHA256())
    h.update(password)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=h.finalize()[:16],
        iterations=480000,
    )
    return AESGCM(kdf.derive(password))

def encrypt(scheme, obj):
    data = bson.dumps(obj)
    if scheme:
        nonce = secrets.token_bytes(16)
        data = nonce + scheme.encrypt(nonce, data, b"")
    return data

def decrypt(scheme, data):
    if scheme:
        data = scheme.decrypt(data[:16], data[16:], b"")
    obj = bson.loads(data)
    return obj

class RemoteInferenceUpload(QThread):
    done = pyqtSignal(str)
    def __init__(self, queue, type, id, file):
        super().__init__()
        self.queue = queue
        self.type = type
        self.file = file
        self.id = id
        self.name = file.rsplit(os.path.sep, 1)[-1]
        self.stopping = False

    def run(self):
        try:
            with open(self.file, 'rb') as f:
                f.seek(0, os.SEEK_END)
                z = f.tell()
                f.seek(0)
                i = 0
                total = math.ceil(z/FRAGMENT_SIZE)
                while not self.stopping:
                    QApplication.processEvents()
                    chunk = f.read(FRAGMENT_SIZE)
                    if not chunk:
                        break
                    request = {"type":"chunk", "data": {"type":self.type, "name": self.name, "chunk":chunk, "index":i, "total": total}, "id":self.id}
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
        self.password = password
        self.id = None
        self.uploads = {}

    def connect(self):
        if self.client:
            return
        self.onResponse({"type": "status", "data": {"message": "Connecting"}})
        while not self.client and not self.stopping:
            try:
                self.client = websockets.sync.client.connect(self.endpoint, open_timeout=2, max_size=None)
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
        self.scheme = get_scheme(self.password)
        self.connect()
        while self.client and not self.stopping:
            try:
                while True:
                    try:
                        data = self.client.recv(0)
                        response = decrypt(self.scheme, data)
                        self.onResponse(response)
                        QApplication.processEvents()
                    except TimeoutError:
                        break
                
                try:
                    request = self.requests.get(False)

                    if request["type"] == "upload":
                        file = request["data"]["file"]
                        if not file in self.uploads:
                            self.uploads[file] = RemoteInferenceUpload(self.requests, request["data"]["type"], request["id"], file)
                            self.uploads[file].done.connect(self.onUploadDone)
                            self.kill.connect(self.uploads[file].stop)
                            self.uploads[file].start()
                            
                        continue

                    data = encrypt(self.scheme, request)
                    data = [data[i:min(i+FRAGMENT_SIZE,len(data))] for i in range(0, len(data), FRAGMENT_SIZE)]

                    self.client.send(data)
                    QApplication.processEvents()
                except queue.Empty:
                    QThread.msleep(5)

            except websockets.exceptions.ConnectionClosedOK:
                self.onResponse({"type": "remote_error", "data": {"message": "Connection closed"}})
                break
            except Exception as e:
                if type(e) == InvalidTag or type(e) == IndexError:
                    self.onResponse({"type": "remote_error", "data": {"message": "Incorrect password"}})
                else:
                    self.onResponse({"type": "remote_error", "data": {"message": str(e)}})
                    log_traceback("REMOTE")
                break

        if self.client:
            self.client.close()
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
        if not self.stopping:
            self.response.emit(response)

    @pyqtSlot(str)
    def onUploadDone(self, file):
        if file in self.uploads:
            del self.uploads[file]