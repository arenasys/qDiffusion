import random
import queue
import json
import bson
import datetime
import copy
import os

from PyQt5.QtCore import pyqtSlot, pyqtProperty, pyqtSignal, QObject, QThread, Qt
from PyQt5.QtWidgets import QApplication

import local
import remote
import host

HAVE_TORCH = False
try:
    import torch
    HAVE_TORCH = True
except ImportError as e:
    pass

def hideBytes(d):
    if type(d) == dict:
        for k,v in d.items():
            if type(v) in {bytes, bytearray}:
                d[k] = "..."
            if type(v) in {dict, list}:
                hideBytes(d[k])
    elif type(d) == list:
        for i in range(len(d)):
            if type(d[i]) in {bytes, bytearray}:
                d[i] = "..."
            if type(d[i]) in {dict, list}:
                hideBytes(d[i])

SEP = os.path.sep
INV_SEP = {"\\": '/', '/':'\\'}[os.path.sep]
NO_CONV = {"prompt", "negative_prompt", "url", "trace", "message", "endpoint", "password", "metadata"}

def convert_path(p):
    return p.replace(INV_SEP, SEP)

def convert_all_paths(j):
    if type(j) == list:
        for i in range(len(j)):
            v = j[i]
            if type(v) == str and INV_SEP in v:
                j[i] = convert_path(v)
            if type(v) == list or type(v) == dict:
                convert_all_paths(j[i])
    elif type(j) == dict: 
        for k, v in j.items():
            if k in NO_CONV: continue
            if type(v) == str and INV_SEP in v:
                j[k] = convert_path(v)
            if type(v) == list or type(v) == dict:
                convert_all_paths(j[k])

class Backend(QObject):
    updated = pyqtSignal()
    request = pyqtSignal(object)
    response = pyqtSignal(object)
    stopping = pyqtSignal()

    def __init__(self, gui):
        super().__init__(gui)
        self.gui = gui
        self.responses = queue.Queue()
        self.inference = None
        gui.aboutToQuit.connect(self.stop)

    def setEndpoint(self, endpoint, password):
        self.debugLogging("NEW SESSION", {"endpoint": endpoint})
        self.inference = None
        if endpoint == "":
            if HAVE_TORCH and self.gui.config.get("mode") != "remote":
                if self.gui.config.get("host_enabled"):
                    ip = self.gui.config.get("host_address")
                    port = int(self.gui.config.get("host_port"))
                    tunnel = self.gui.config.get("host_tunnel")
                    read_only = self.gui.config.get("host_read_only")
                    monitor = self.gui.config.get("host_monitor")
                    password = self.gui._hostSetPassword
                    self.inference = host.HostInference(self.gui, ip, port, password, tunnel, read_only, monitor)
                else:
                    self.inference = local.LocalInference(self.gui)
            else:
                self.onResponse({"type": "remote_only"})
        else:
            self.inference = remote.RemoteInference(self.gui, endpoint, password)
        self.updated.emit()

        if not self.inference:
            return

        self.request.connect(self.inference.onRequest, type=Qt.QueuedConnection)
        self.inference.response.connect(self.onResponse)
        self.stopping.connect(self.inference.stop)
        self.inference.start()

    @pyqtSlot()
    def stop(self):
        self.stopping.emit()

    def wait(self):
        if self.inference:
            if not self.inference.wait(100):
                self.inference.terminate()
    
    def debugLogging(self, type, data):
        if self.gui._debugJSONLogging:
            if "type" in data and data["type"] == "remote_latency":
                return

            try:
                j = copy.deepcopy(data)
            except Exception as e:
                with open("debug.log", "a", encoding='utf-8') as f:
                    f.write(f"NOT NICE {str(e)}\n")
                    f.write(f"{type} {datetime.datetime.now()}\n{str(data)}\n")
                    return
                
            hideBytes(j)
            j = json.dumps(j)
            with open("debug.log", "a", encoding='utf-8') as f:
                f.write(f"{type} {datetime.datetime.now()}\n{j}\n")

    @pyqtSlot(object)
    def makeRequest(self, request):
        self.debugLogging("REQUEST", request)
        self.request.emit(request)

    @pyqtSlot(object)
    def onResponse(self, response):
        convert_all_paths(response)
        self.debugLogging("RESPONSE", response)
        self.response.emit(response)

    @pyqtProperty(str, notify=updated)
    def mode(self):
        if self.inference and type(self.inference) == remote.RemoteInference:
            return "Remote"
        elif self.inference and type(self.inference) == host.HostInference:
            return "Host"
        else:
            return "Local"