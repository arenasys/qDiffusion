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
import time
import threading

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QImage

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

class RemoteHeartbeat(QThread):
    latency = pyqtSignal(float)
    def __init__(self, client):
        super().__init__()
        self.client = client
        self.last = time.time()
        self.latencies = []
        self.ping_interval = 1
        self.wait_interval = 10
    
    def run(self):
        try:
            while True:
                start = time.time()
                pong = self.client.ping()
                result = pong.wait(self.wait_interval)
                duration = time.time()-start

                if result:
                    self.last = time.time()
                    self.latencies += [duration]
                    if len(self.latencies) > 10:
                        self.latencies.pop(0)
                    latency = sum(self.latencies)/len(self.latencies)
                    self.latency.emit(latency)
                else:
                    timeout = time.time()-self.last
                    self.latency.emit(timeout)
                
                if duration < self.ping_interval:
                    time.sleep(self.ping_interval - duration)
                
        except Exception as e:
            print("HEART", e)
        
        self.latency.emit(0)

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

        self.heartbeat = RemoteHeartbeat(self.client)
        self.heartbeat.latency.connect(self.onLatency)
        self.heartbeat.start()

    def reconnect(self):
        start = time.time()
        timeout = 60
        self.client = None
        while not self.client and not self.stopping:
            try:
                self.client = websockets.sync.client.connect(self.endpoint, open_timeout=2, max_size=None)
            except Exception:
                if time.time() - start > timeout:
                    return
        if self.stopping:
            return
        if self.client:
            self.onResponse({"type": "status", "data": {"message": "Reconnected"}})

    def terminateConnection(self, errored=True):
        self.client.protocol.send_frame = lambda x: None
        self.client.socket.close()
        self.client = None
        if errored:
            raise websockets.exceptions.ConnectionClosedError(None, None)
    
    def run(self):
        self.scheme = get_scheme(self.password)
        self.connect()
        client_id = None

        while self.client and not self.stopping:
            try:
                while True:
                    try:
                        data = self.client.recv(0)
                        response = decrypt(self.scheme, data)
                        if response["type"] == "hello":
                            if not client_id:
                                client_id = response["data"]["id"]
                            else:
                                self.requests.put({"type": "reconnect", "data": {"id": client_id}})
                        if response["type"] == "temporary":
                            self.fetch(response["data"]["id"], response["id"])

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
            except websockets.exceptions.ConnectionClosedError as e:
                if not e.rcvd and not e.sent:
                    self.onResponse({"type": "status", "data": {"message": "Reconnecting"}})
                    self.reconnect()
                    if self.client:
                        continue
                    else:
                        self.onResponse({"type": "remote_error", "data": {"message": "Connection lost"}})
                else:
                    self.onResponse({"type": "remote_error", "data": {"message": "Connection aborted"}})
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
            self.terminateConnection(errored=False)

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

    @pyqtSlot(float)
    def onLatency(self, seconds):
        self.onResponse({"type": "remote_latency", "data": {"seconds": seconds}})

    def fetch(self, result_id, request_id):
        def do_fetch(endpoint, password, result_id, request_id, callback):
            scheme = get_scheme(password)
            client = None
            while True:
                try:
                    client = websockets.sync.client.connect(endpoint, open_timeout=2, max_size=None, close_timeout=0)
                    break
                except Exception:
                    continue
                
            request = {"type": "fetch", "data": {"id": result_id}}
            data = encrypt(scheme, request)
            try:
                client.send(data)
            except Exception as e:
                print(e)
                pass

            while True:
                try:
                    data = client.recv()
                except Exception as e:
                    print(e)
                    pass
                    
                response = decrypt(scheme, data)
                if response["type"] == "result":
                    response["id"] = request_id
                    images = []

                    typ = {"PNG": "png", "JPEG": "jpg"}[response["data"]["type"]]
                    for data in response["data"]["images"]:
                        image = QImage()
                        image.loadFromData(data, typ)
                        images += [image]
                    response["data"]["images"] = images

                    callback(response)
                    break
            
            client.close()
            client.close_socket()

        thread = threading.Thread(target=do_fetch, args=([self.endpoint, self.password, result_id, request_id, self.onResponse]), daemon=True)
        thread.start()