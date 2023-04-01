import sys
import signal
import traceback
import datetime
import subprocess
import os
import glob
import shutil
import importlib
import pkg_resources
import json

import platform
IS_WIN = platform.system() == 'Windows'

from PyQt5.QtCore import pyqtSignal, pyqtSlot, pyqtProperty, QObject, QUrl, QCoreApplication, Qt, QElapsedTimer, QThread
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType, qmlRegisterType
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon

NAME = "qDiffusion"

import warnings
warnings.filterwarnings("ignore", category=UserWarning) 

class Application(QApplication):
    t = QElapsedTimer()

    def event(self, e):
        return QApplication.event(self, e)
        
def buildQMLRc():
    qml_path = os.path.join("source", "qml")
    qml_rc = os.path.join(qml_path, "qml.qrc")
    if os.path.exists(qml_rc):
        os.remove(qml_rc)

    items = []

    tabs = glob.glob(os.path.join("source", "tabs", "*"))
    for tab in tabs:
        for src in glob.glob(os.path.join(tab, "*.*")):
            if src.split(".")[-1] in {"qml","svg"}:
                dst = os.path.join(qml_path, os.path.relpath(src, "source"))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy(src, dst)
                items += [dst]

    items += glob.glob(os.path.join(qml_path, "*.qml"))
    items += glob.glob(os.path.join(qml_path, "components", "*.qml"))
    items += glob.glob(os.path.join(qml_path, "style", "*.qml"))
    items += glob.glob(os.path.join(qml_path, "fonts", "*.ttf"))
    items += glob.glob(os.path.join(qml_path, "icons", "*.svg"))

    items = ''.join([f"\t\t<file>{os.path.relpath(f, qml_path )}</file>\n" for f in items])

    contents = f"""<RCC>\n\t<qresource prefix="/">\n{items}\t</qresource>\n</RCC>"""

    with open(qml_rc, "w") as f:
        f.write(contents)

def buildQMLPy():
    qml_path = os.path.join("source", "qml")
    qml_py = os.path.join(qml_path, "qml_rc.py")
    qml_rc = os.path.join(qml_path, "qml.qrc")

    if os.path.exists(qml_py):
        os.remove(qml_py)

    status = subprocess.run(["pyrcc5", "-o", qml_py, qml_rc], capture_output=True, shell=IS_WIN)
    if status.returncode != 0:
        raise Exception(status.stderr.decode("utf-8"))

    shutil.rmtree(os.path.join(qml_path, "tabs"))
    os.remove(qml_rc)

def loadTabs(app, backend):
    tabs = []
    for tab in glob.glob(os.path.join("source", "tabs", "*")):
        tab_name = tab.split(os.path.sep)[-1]
        tab_name_c = tab_name.capitalize()
        tab_module = importlib.import_module(f"tabs.{tab_name}.{tab_name}")
        tab_class = getattr(tab_module, tab_name_c)
        tab_instance = tab_class(parent=app)
        tab_instance.source = f"qrc:/tabs/{tab_name}/{tab_name_c}.qml"
        tabs += [tab_instance]
    for tab in tabs:
        if not hasattr(tab, "priority"):
            tab.priority = len(tabs)
    
    tabs.sort(key=lambda tab: tab.priority)
    backend.registerTabs(tabs)

class Builder(QThread):
    def __init__(self, app, engine):
        super().__init__()
        self.app = app
        self.engine = engine
    
    def run(self):
        buildQMLRc()
        buildQMLPy()

def check(dependancies):
    needed = []
    for d in dependancies:
        try:
            pkg_resources.require(d)
        except Exception:
            needed += [d]
    return needed

class Installer(QThread):
    installing = pyqtSignal(str)
    installed = pyqtSignal(str)
    def __init__(self, parent, packages):
        super().__init__(parent)
        self.packages = packages
        self.proc = None
        self.stopping = False

    def run(self):
        for p in self.packages:
            self.installing.emit(p)
            args = ["pip", "install", "-U", p]
            if p[:5] == "torch":
                args += ["--index-url", "https://download.pytorch.org/whl/" + p.rsplit("+",1)[-1]]
            self.proc = subprocess.Popen(args, shell=IS_WIN)
            if self.proc.wait():
                if self.stopping:
                    return
                raise RuntimeError("Failed to install: ", p)
            self.installed.emit(p)
        self.proc = None

    @pyqtSlot()
    def stop(self):
        self.stopping = True
        if self.proc:
            self.proc.kill()

class Coordinator(QObject):
    ready = pyqtSignal()
    show = pyqtSignal()
    proceed = pyqtSignal()
    cancel = pyqtSignal()

    updated = pyqtSignal()
    installedUpdated = pyqtSignal()
    def __init__(self, app, engine):
        super().__init__(app)
        self.app = app
        self.engine = engine
        self.builder = Builder(app, engine)
        self.builder.finished.connect(self.loaded)
        self.installer = None

        self._needRestart = False
        self._installed = []
        self._installing = ""

        self.modes = ["nvidia", "amd", "remote"]
        self._mode = 0
        self.in_venv = "VIRTUAL_ENV" in os.environ and os.path.join(os.getcwd(), "venv") == os.environ["VIRTUAL_ENV"]
        self.override = False

        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
                self.override = 'show' in cfg
                mode = self.modes.index(cfg['mode'].lower())
                self._mode = mode
        except Exception:
            pass

        with open(os.path.join("source", "requirements_gui.txt")) as file:
            self.required = [line.rstrip() for line in file]

        with open(os.path.join("source", "requirements_inference.txt")) as file:
            self.optional = [line.rstrip() for line in file]

        self.find_needed()

    def find_needed(self):
        self.torch_version = ""
        self.torchvision_version = ""

        try:
            self.torch_version = str(pkg_resources.get_distribution("torch"))
        except:
            pass

        try:
            self.torchvision_version = str(pkg_resources.get_distribution("torchvision"))
        except:
            pass

        self.nvidia_torch_version = "2.0.0+cu117"
        self.nvidia_torchvision_version = "0.15.1+cu117"

        self.amd_torch_version = "2.0.0+rocm5.4.2"
        self.amd_torchvision_version = "0.15.1+rocm5.4.2"
        
        self.required_need = check(self.required)
        self.optional_need = check(self.optional)
    
    @pyqtProperty(int, notify=updated)
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, mode):
        self._mode = mode
        self.updated.emit()

    @pyqtProperty(list, notify=updated)
    def packages(self):
        return self.get_needed()
    
    @pyqtProperty(list, notify=installedUpdated)
    def installed(self):
        return self._installed
    
    @pyqtProperty(str, notify=installedUpdated)
    def installing(self):
        return self._installing
    
    @pyqtProperty(bool, notify=installedUpdated)
    def disable(self):
        return self.installer != None
    
    @pyqtProperty(bool, notify=updated)
    def needRestart(self):
        return self._needRestart

    def get_needed(self):
        needed = []
        if self._mode == 0:
            if not "+cu" in self.torch_version:
                needed += ["torch=="+self.nvidia_torch_version]
            if not "+cu" in self.torchvision_version:
                needed += ["torchvision=="+self.nvidia_torchvision_version]
            needed += self.optional_need
        if self._mode == 1:
            if not "+rocm" in self.torch_version:
                needed += ["torch=="+self.amd_torch_version]
            if not "+rocm" in self.torchvision_version:
                needed += ["torchvision=="+self.amd_torchvision_version]
            needed += self.optional_need

        needed += self.required_need

        needed = [n for n in needed if n[:5] == "wheel"] + [n for n in needed if n[:5] != "wheel"]
        
        return needed

    @pyqtSlot()
    def load(self):
        self.app.setWindowIcon(QIcon("source/qml/icons/placeholder.svg"))
        self.builder.start()

    @pyqtSlot()
    def loaded(self):
        ready()
        self.ready.emit()
        
        if self.override or (self.in_venv and self.packages):
            self.show.emit()
        else:
            self.done()
        
    @pyqtSlot()
    def done(self):
        start(self.engine, self.app)
        self.proceed.emit()

    @pyqtSlot()
    def install(self):
        if self.installer:
            self.cancel.emit()
            return
        packages = self.packages
        if not packages:
            self.done()
            return
        self.installer = Installer(self, packages)
        self.installer.installed.connect(self.onInstalled)
        self.installer.installing.connect(self.onInstalling)
        self.installer.finished.connect(self.doneInstalling)
        self.app.aboutToQuit.connect(self.installer.stop)
        self.cancel.connect(self.installer.stop)
        self.installer.start()
        self.installedUpdated.emit()

    @pyqtSlot(str)
    def onInstalled(self, package):
        self._installed += [package]
        self.installedUpdated.emit()
    
    @pyqtSlot(str)
    def onInstalling(self, package):
        self._installing = package
        self.installedUpdated.emit()
    
    @pyqtSlot()
    def doneInstalling(self):
        cfg = {}
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            pass
        cfg['mode'] = self.modes[self._mode]
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f)

        self.installer = None
        self._installing = ""
        self.installedUpdated.emit()
        self.find_needed()
        self.updated.emit()
        if not self.packages:
            self.done()
        else:
            self._needRestart = True
            self.updated.emit()
    
def launch():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(NAME)
        import setproctitle
        setproctitle.setproctitle(NAME)
    except:
        pass

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = Application([NAME])
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    app.startTimer(100)
    
    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)

    coordinator = Coordinator(app, engine)
    qmlRegisterSingletonType(Coordinator, "gui", 1, 0, "COORDINATOR", lambda qml, js: coordinator)

    engine.load(QUrl('file:source/qml/Splash.qml'))

    os._exit(app.exec())

def ready():
    import qml.qml_rc
    import misc
    qmlRegisterSingletonType(QUrl("qrc:/Common.qml"), "gui", 1, 0, "COMMON")
    misc.registerTypes()

def start(engine, app):
    import gui
    import sql
    import canvas
    import parameters

    sql.registerTypes()
    canvas.registerTypes()
    canvas.registerMiscTypes()
    parameters.registerTypes()

    backend = gui.GUI(parent=app)

    os.makedirs("outputs/txt2img", exist_ok=True)
    os.makedirs("outputs/img2img", exist_ok=True)
    os.makedirs("outputs/favourites", exist_ok=True)

    engine.addImageProvider("sync", backend.thumbnails.sync_provider)
    engine.addImageProvider("async", backend.thumbnails.async_provider)

    qmlRegisterSingletonType(gui.GUI, "gui", 1, 0, "GUI", lambda qml, js: backend)
    
    loadTabs(backend, backend)

def exceptHook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a") as f:
        f.write(f"GUI {datetime.datetime.now()}\n{tb}\n")
    print(tb)
    print("TRACEBACK SAVED: crash.log")
    QApplication.quit()

def main():
    if not os.path.exists("source"):
        os.chdir('..')

    sys.excepthook = exceptHook
    launch()

if __name__ == "__main__":
    main()
