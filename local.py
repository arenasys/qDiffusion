import os
import shutil
import sys
import subprocess
import traceback
import io
import queue
import threading
import multiprocessing

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

from parameters import save_image

class InferenceProcessThread(threading.Thread):
    def __init__(self, requests, responses):
        super().__init__()

        self.stopping = False
        self.requests = requests
        self.responses = responses
        self.current = None
        self.cancelled = set()

        if not os.path.exists("sd-inference-server"):
            self.responses.put((-1, {"type":"status", "data":{"message":"Downloading"}}))
            ret = subprocess.run(["git", "clone", "https://github.com/arenatemp/sd-inference-server/"], capture_output=True)
            if ret.returncode:
                raise RuntimeError(ret.stderr.decode("utf-8").split("fatal: ", 1)[1])

        if not os.path.exists("models"):
            shutil.copytree(os.path.join("sd-inference-server", "models"), os.path.join(os.getcwd(), "models"))

        sys.path.insert(0, "sd-inference-server")

        self.responses.put((-1, {"type":"status", "data":{"message":"Initializing"}}))
        import torch
        import attention, storage, wrapper

        attention.use_split_attention()

        model_storage = storage.ModelStorage("./models", torch.float16, torch.float32)
        self.wrapper = wrapper.GenerationParameters(model_storage, torch.device("cuda"))
        self.wrapper.callback = self.onResponse
    
    def run(self):
        self.requests.put((-1, {"type":"options"}))
        while not self.stopping:
            try:
                self.current, request = self.requests.get(True, 0.01)
                self.wrapper.reset()
                if request["type"] == "txt2img":
                    self.wrapper.set(**request["data"])
                    self.wrapper.txt2img()
                elif request["type"] == "img2img":
                    self.wrapper.set(**request["data"])
                    self.wrapper.img2img()
                elif request["type"] == "options":
                    self.wrapper.options()
                elif request["type"] == "convert":
                    self.wrapper.set(**request["data"])
                    self.wrapper.convert()
                self.requests.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                if str(e) == "Aborted":
                    self.responses.put((self.current, {"type":"aborted", "data":{}}))
                    continue
                additional = ""
                try:
                    s = traceback.extract_tb(e.__traceback__).format()
                    s = [e for e in s if not "site-packages" in e][-1]
                    s = s.split(", ")
                    file = s[0].split(os.path.sep)[-1][:-1]
                    line = s[1].split(" ")[1]
                    additional = f" ({file}:{line})"
                except Exception:
                    pass

                self.responses.put((self.current, {"type":"error", "data":{"message":str(e) + additional}}))

    def onResponse(self, response):
        self.responses.put((self.current, response))
        return not self.current in self.cancelled
    
    def cancel(self, id):
        self.cancelled.add(id)

class InferenceProcess(multiprocessing.Process):
    def __init__(self, requests, responses):
        super().__init__()
        self.stopping = False
        self.requests = requests
        self.responses = responses

    def run(self):
        inference_requests = queue.Queue()

        try:
            self.inference = InferenceProcessThread(inference_requests, self.responses)
        except Exception as e:
            self.responses.put((-1, {"type":"error", "data":{"message":str(e)}}))
            return

        self.inference.start()

        while not self.stopping:
            try:
                id, request = self.requests.get()
                if request["type"] == "cancel":
                    self.inference.cancel(id)
                if request["type"] == "stop":
                    self.stop()
                else:
                    inference_requests.put((id, request))
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.stopping = True
        self.inference.stopping = True
        self.inference.cancel(self.inference.current)

class LocalInference(QThread):
    response = pyqtSignal(int, object)
    def __init__(self):
        super().__init__()

        self.stopping = False
        self.requests = multiprocessing.Queue(16)
        self.responses = multiprocessing.Queue(16)
        self.inference = InferenceProcess(self.requests, self.responses)

    def run(self):
        self.inference.start()
        
        while not self.stopping:
            try:
                QApplication.processEvents()
                QThread.msleep(10)
                id, response = self.responses.get(False)
                self.onResponse(id, response)
            except queue.Empty:
                pass
            
    @pyqtSlot()
    def stop(self):
        self.requests.put((-1, {"type": "stop", "data":{}}))
        self.stopping = True
        self.inference.join()
        print("STOPPED")

    @pyqtSlot(int, object)
    def onRequest(self, id, request):
        self.requests.put((id, request))

    @pyqtSlot(int)
    def onCancel(self, id):
        self.requests.put((id, {"type": "cancel", "data":{}}))

    def onResponse(self, id, response):
        if response["type"] == "result":
            self.saveResults(response["data"]["images"], response["data"]["metadata"])

        self.response.emit(id, response)

    def saveResults(self, images, metadata):
        for i in range(len(images)):
            save_image(images[i], metadata[i])