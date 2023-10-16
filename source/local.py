import os
import shutil
import sys
import subprocess
import traceback
import io
import queue
import threading
import multiprocessing
import traceback
import datetime

import platform
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

import git

def log_traceback(label):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a", encoding='utf-8') as f:
        f.write(f"{label} {datetime.datetime.now()}\n{tb}\n")
    print(label, tb)
    return tb

class InferenceProcessThread(threading.Thread):
    def __init__(self, requests, responses, model_directory):
        super().__init__()

        self.stopping = False
        self.requests = requests
        self.responses = responses
        self.current = None
        self.cancelled = set()

        sd_path = os.path.join("source", "sd-inference-server")

        if not os.path.exists(sd_path):
            self.responses.put({"type":"status", "data":{"message":"Downloading"}})
            git.git_clone(sd_path, git.INFER_URL)

        if not os.path.exists(model_directory):
            shutil.copytree(os.path.join(sd_path, "models"), model_directory)

        sys.path.insert(0, sd_path)

        self.responses.put({"type":"status", "data":{"message":"Initializing"}})

        if sys.stdout == None:
            sys.stdout = open(os.devnull, 'w')
            sys.__stdout__ = sys.stdout
        if sys.stderr == None:
            sys.stderr = open(os.devnull, 'w')
            sys.__stderr__ = sys.stderr

        import torch
        import attention, storage, wrapper, server

        model_storage = storage.ModelStorage(model_directory, torch.float16, torch.float32)
        self.wrapper = wrapper.GenerationParameters(model_storage, torch.device("cuda"))
        self.wrapper.callback = self.onResponse
        self.do_download = server.do_download
    
    def run(self):
        self.requests.put({"type":"options"})
        while not self.stopping:
            try:
                request = self.requests.get(True, 0.01)
                self.current = None
                if "id" in request:
                    self.current = request["id"]
                self.wrapper.reset()
                if request["type"] == "txt2img":
                    self.wrapper.set(**request["data"])
                    self.wrapper.txt2img()
                elif request["type"] == "img2img":
                    self.wrapper.set(**request["data"])
                    self.wrapper.img2img()
                elif request["type"] == "options":
                    self.wrapper.options()
                elif request["type"] == "upscale":
                    self.wrapper.set(**request["data"])
                    self.wrapper.upscale()
                elif request["type"] == "manage":
                    self.wrapper.set(**request["data"])
                    self.wrapper.manage()
                elif request["type"] == "annotate":
                    self.wrapper.set(**request["data"])
                    self.wrapper.annotate()
                elif request["type"] == "segmentation":
                    self.wrapper.set(**request["data"])
                    self.wrapper.segmentation()
                elif request["type"] == "train_lora":
                    self.wrapper.set(**request["data"])
                    self.wrapper.train_lora()
                elif request["type"] == "download":
                    self.do_download(request["data"], self.wrapper.storage.path, self.current, self.onResponse)
                self.requests.task_done()
            except queue.Empty:
                pass
            except Exception as e:
                if str(e) == "Aborted":
                    self.responses.put({"type":"aborted", "id": self.current, "data":{}})
                    continue
                additional = ""
                trace = ""
                try:
                    trace = log_traceback("LOCAL THREAD")

                    frames = traceback.extract_tb(e.__traceback__).format()
                    frame = [e for e in frames if not "site-packages" in e][-1]
                    frame = frame.split(", ")
                    file = frame[0].split(os.path.sep)[-1][:-1]
                    line = frame[1].split(" ")[1]
                    additional = f" ({file}:{line})"
                except Exception:
                    pass

                self.responses.put({"type":"error", "id": self.current,  "data":{"message":str(e) + additional, "trace": trace}})

    def onResponse(self, response, id=None):
        if not id:
            id = self.current
        if id:
            response["id"] = id
        self.responses.put(response)
        return not self.current in self.cancelled
    
    def cancel(self, id):
        self.cancelled.add(id)

class InferenceProcess(multiprocessing.Process):
    def __init__(self, requests, responses, model_directory):
        super().__init__()
        self.stopping = False
        self.requests = requests
        self.responses = responses
        self.model_directory = model_directory

    def run(self):
        inference_requests = queue.Queue()

        try:
            self.inference = InferenceProcessThread(inference_requests, self.responses, self.model_directory)
        except Exception as e:
            trace = log_traceback("LOCAL PROCESS")
            self.responses.put({"type":"error", "data":{"message":str(e), "trace":trace}})
            return
    
        self.inference.start()

        while not self.stopping:
            parent = multiprocessing.parent_process()
            if not parent or not parent.is_alive():
                self.stop()
                return
            
            try:
                request = self.requests.get(True, 1)
                if request["type"] == "cancel":
                    self.inference.cancel(request["data"]["id"])
                if request["type"] == "stop":
                    self.stop()
                else:
                    inference_requests.put(request)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        self.stopping = True
        self.inference.stopping = True
        self.inference.cancel(self.inference.current)

class LocalInference(QThread):
    response = pyqtSignal(object)
    def __init__(self, gui):
        super().__init__()
        self.gui = gui

        self.stopping = False
        self.requests = multiprocessing.Queue(16)
        self.responses = multiprocessing.Queue(16)
        self.inference = InferenceProcess(self.requests, self.responses, self.gui.modelDirectory())

    def run(self):
        self.inference.start()
        while not self.stopping:
            try:
                QApplication.processEvents()
                QThread.msleep(10)
                response = self.responses.get(False)
                self.onResponse(response)
            except queue.Empty:
                pass
            
    @pyqtSlot()
    def stop(self):
        self.requests.put({"type": "stop", "data":{}})
        self.stopping = True
        self.inference.join(0.1)
        if self.inference.is_alive():
            print("TERMINATED")
            self.inference.terminate()
        print("STOPPED")

    @pyqtSlot(object)
    def onRequest(self, request):
        self.requests.put(request)

    def onResponse(self, response):
        self.response.emit(response)