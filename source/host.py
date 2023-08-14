import os
import sys
import traceback
import multiprocessing
import traceback
import datetime
import time
import random
import string

import platform
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtSlot, pyqtSignal, QThread
from PyQt5.QtWidgets import QApplication

import remote

def log_traceback(label):
    exc_type, exc_value, exc_tb = sys.exc_info()
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a", encoding='utf-8') as f:
        f.write(f"{label} {datetime.datetime.now()}\n{tb}\n")
    print(label, tb)
    return tb

class HostProcess(multiprocessing.Process):
    def __init__(self, ip, port, password, tunnel, read_only, monitor, model_directory, loaded, stop, response):
        super().__init__()
        self.stopping = False
        self.ip = ip
        self.port = port
        self.tunnel = tunnel
        self.read_only = read_only
        self.monitor = monitor
        self.password = password
        self.model_directory = model_directory

        self.loaded = loaded
        self.stop = stop
        self.response = response

    def run(self):
        print("START")
        sys.path.insert(0, os.path.join("source", "sd-inference-server"))
        print("PATH")
        import torch
        print("TORCH")
        import storage, wrapper, server
        print("AUX")

        try:
            model_storage = storage.ModelStorage(self.model_directory, torch.float16, torch.float32)
            print("STORAGE")
            self.wrapper = wrapper.GenerationParameters(model_storage, torch.device("cuda"))
            print("WRAPPER")
            self.server = server.Server(self.wrapper, self.ip, self.port, self.password, True, self.read_only, self.monitor)
            print("DEFINE")
            self.server.start()
            print("BIND")

            endpoint = f"ws://{self.ip}:{self.port}"
            if self.tunnel:
                from pycloudflared import try_cloudflare
                tunnel_url = try_cloudflare(port=self.port, verbose=False)
                endpoint = tunnel_url.tunnel.replace("https", "wss")

            self.response.put({"type": "host", "data": {"endpoint": endpoint, "password": self.password}})
            print("RESPOND")

            self.loaded.set()

            while True:
                if self.stop.is_set():
                    self.server.stop()
                    break
                if self.server.join(0.5):
                    break

            if self.tunnel:
                try_cloudflare.terminate(self.port)
        except Exception as e:
            log_traceback("LOCAL HOST")
            self.response.put({"type": "remote_error", "data": {"message": str(e)}})

class HostInference(remote.RemoteInference):
    response = pyqtSignal(object)
    def __init__(self, gui, ip, port, password, tunnel, read_only, monitor):
        endpoint = f"ws://{ip}:{port}"
        if not password:
            password = ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for _ in range(8))

        super().__init__(gui, endpoint, password)

        self.loaded_sig = multiprocessing.Event()
        self.stop_sig = multiprocessing.Event()

        self.host_response = multiprocessing.Queue(16)
        self.host = HostProcess(ip, port, password, tunnel, read_only, monitor, self.gui.modelDirectory(), self.loaded_sig, self.stop_sig, self.host_response)

    def run(self):
        self.onResponse({"type": "status", "data": {"message": "Initializing"}})
        self.host.start()

        for _ in range(10):
            self.loaded_sig.wait(1)
            if self.loaded_sig.is_set() or not self.host_response.empty():
                break

        if not self.loaded_sig.is_set():
            self.stop_sig.set()
            error = {"type": "remote_error", "data": {"message": "Timeout starting host"}}
            if not self.host_response.empty():
                error = self.host_response.get_nowait()
            self.onResponse(error)
            return
        
        while not self.host_response.empty():
            self.onResponse(self.host_response.get_nowait())

        time.sleep(0.5)

        super().run()

    @pyqtSlot()
    def stop(self):
        self.stop_sig.set()
        super().stop()