import sys
import os
import queue
import subprocess
import shutil
import time

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread
from PyQt5.QtWidgets import QApplication

class LocalInference(QThread):
    response = pyqtSignal(int, object)
    def __init__(self):
        super().__init__()

        if not os.path.exists("sd-inference-server"):
            subprocess.run(["git", "clone", "https://github.com/arenatemp/sd-inference-server/"])

        if not os.path.exists("models"):
            shutil.copytree(os.path.join("sd-inference-server", "models"), os.path.join(os.getcwd(), "models"))

        sys.path.insert(0, "sd-inference-server")

        import torch
        import attention, storage, wrapper

        attention.use_split_attention()

        model_storage = storage.ModelStorage("./models", torch.float16, torch.float32)
        self.wrapper = wrapper.GenerationParameters(model_storage, torch.device("cuda"))
        self.wrapper.callback = self.onResponse

        self.stopping = False

        self.requests = queue.Queue()
        self.current = None
        self.cancelled = set()
    
    def run(self):
        while not self.stopping:
            try:
                QThread.msleep(10)
                QApplication.processEvents()
                self.current, request = self.requests.get(False)
                if request["type"] == "txt2img":
                    self.wrapper.set(**request["data"])
                    self.wrapper.txt2img()
                elif request["type"] == "img2img":
                    self.wrapper.set(**request["data"])
                    self.wrapper.img2img()
                self.requests.task_done()
            except queue.Empty:
                pass
            except RuntimeError:
                pass
            except Exception as e:
                self.response.emit(self.current, {"type":"error", "data":{"message":str(e)}})

    @pyqtSlot()
    def stop(self):
        self.stopping = True

    @pyqtSlot(int, object)
    def onRequest(self, id, request):
        self.requests.put((id, request))

    @pyqtSlot(int)
    def onCancel(self, id):
        self.cancelled.add(id)

    def onResponse(self, response):
        self.response.emit(self.current, response)
        return not self.current in self.cancelled