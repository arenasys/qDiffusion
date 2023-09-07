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

from translation import Translator

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
        raise Exception(status.stderr)

    shutil.rmtree(os.path.join(qml_path, "tabs"))
    os.remove(qml_rc)

def loadTabs(app, backend):
    tabs = []
    for tab in glob.glob(os.path.join("source", "tabs", "*")):
        tab_name = tab.split(os.path.sep)[-1]
        if tab_name == "editor":
            continue
        tab_name_c = tab_name.capitalize()
        try:
            tab_module = importlib.import_module(f"tabs.{tab_name}.{tab_name}")
            tab_class = getattr(tab_module, tab_name_c)
            tab_instance = tab_class(parent=app)
            tab_instance.source = f"qrc:/tabs/{tab_name}/{tab_name_c}.qml"
            tabs += [tab_instance]
        except Exception as e:
            raise e
            #continue
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

def check(dependancies, enforce_version=True):
    importlib.reload(pkg_resources)
    needed = []
    for d in dependancies:
        try:
            pkg_resources.require(d)
        except pkg_resources.DistributionNotFound:
            needed += [d]
        except pkg_resources.VersionConflict as e:
            if enforce_version:
                #print("CONFLICT", d, e)
                needed += [d]
        except Exception:
            pass
    return needed

class Installer(QThread):
    output = pyqtSignal(str)
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
            pkg = p.split("=",1)[0]
            if pkg in {"torch", "torchvision"}:
                args = ["pip", "install", "-U", pkg, "--index-url", "https://download.pytorch.org/whl/" + p.rsplit("+",1)[-1]]
            args = ["python", "-m"] + args
            #print("INSTALL", " ".join(args))
            self.proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=IS_WIN)

            output = ""
            while self.proc.poll() == None:
                while line := self.proc.stdout.readline():
                    if line:
                        line = line.strip()
                        output += line + "\n"
                        self.output.emit(line)
                    if self.stopping:
                        return
            if self.stopping:
                return
            if self.proc.returncode:
                raise RuntimeError("Failed to install: ", p, "\n", output)
            
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

    output = pyqtSignal(str)

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

        self._modes = ["nvidia", "amd", "remote"]

        self._mode = 0
        self.in_venv = "VIRTUAL_ENV" in os.environ
        self.override = False

        self.enforce = True

        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if "show_installer" in cfg:
                    self.override = cfg["show_installer"]
                if "enforce_versions" in cfg:
                    self.enforce = cfg["enforce_versions"]
                mode = self._modes.index(cfg["mode"].lower())
                self._mode = mode
        except Exception:
            pass

        with open(os.path.join("source", "requirements_gui.txt")) as file:
            self.required = [line.rstrip() for line in file]

        with open(os.path.join("source", "requirements_inference.txt")) as file:
            self.optional = [line.rstrip() for line in file]

        self.find_needed()

        qmlRegisterSingletonType(Coordinator, "gui", 1, 0, "COORDINATOR", lambda qml, js: self)

    def find_needed(self):
        self.torch_version = ""
        self.torchvision_version = ""
        self.directml_version = ""

        try:
            self.torch_version = str(pkg_resources.get_distribution("torch")).split()[-1]
        except:
            pass

        try:
            self.torchvision_version = str(pkg_resources.get_distribution("torchvision")).split()[-1]
        except:
            pass

        try:
            self.directml_version = str(pkg_resources.get_distribution("torch-directml")).split()[-1]
        except:
            pass

        self.nvidia_torch_version = "2.0.1+cu118"
        self.nvidia_torchvision_version = "0.15.2+cu118"

        self.amd_torch_version = "2.0.1+rocm5.4.2"
        self.amd_torchvision_version = "0.15.2+rocm5.4.2"
        self.amd_torch_directml_version = "0.2.0.dev230426"
        
        self.required_need = check(self.required, self.enforce)
        self.optional_need = check(self.optional, self.enforce)
    
    @pyqtProperty(list, constant=True)
    def modes(self):
        return ["Nvidia", "AMD", "Remote"]

    @pyqtProperty(int, notify=updated)
    def mode(self):
        return self._mode
    
    @mode.setter
    def mode(self, mode):
        self._mode = mode
        self.updated.emit()

    @pyqtProperty(bool, notify=updated)
    def enforceVersions(self):
        return self.enforce
    
    @enforceVersions.setter
    def enforceVersions(self, enforce):
        self.enforce = enforce
        self.find_needed()
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
        mode = self._modes[self._mode]
        needed = []
        if mode == "nvidia":
            if not "+cu" in self.torch_version or (self.enforce and self.torch_version != self.nvidia_torch_version):
                needed += ["torch=="+self.nvidia_torch_version]
            if not "+cu" in self.torchvision_version or (self.enforce and self.torchvision_version != self.nvidia_torchvision_version):
                needed += ["torchvision=="+self.nvidia_torchvision_version]
            needed += self.optional_need
        if mode == "amd":
            if IS_WIN:
                if not self.directml_version or (self.enforce and self.directml_version != self.amd_torch_directml_version):
                    needed += ["torch-directml==" + self.amd_torch_directml_version]
            else:
                if not "+rocm" in self.torch_version or (self.enforce and self.torch_version != self.amd_torch_version):
                    needed += ["torch=="+self.amd_torch_version]
                if not "+rocm" in self.torchvision_version or (self.enforce and self.torchvision_version != self.amd_torchvision_version):
                    needed += ["torchvision=="+self.amd_torchvision_version]
            needed += self.optional_need

        needed += self.required_need

        needed = [n for n in needed if n.startswith("wheel")] + [n for n in needed if not n.startswith("wheel")]
        needed = [n for n in needed if n.startswith("pip")] + [n for n in needed if not n.startswith("pip")]
        
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
        self.installer.output.connect(self.onOutput)
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
    
    @pyqtSlot(str)
    def onOutput(self, out):
        self.output.emit(out)
    
    @pyqtSlot()
    def doneInstalling(self):
        cfg = {}
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception as e:
            pass
        cfg['mode'] = self._modes[self._mode]
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f)

        self._installing = ""
        self.installer = None
        self.installedUpdated.emit()
        self.find_needed()
        if not self.packages:
            self.done()
            return
        self.installer = None
        self.installedUpdated.emit()
        if all([p in self._installed for p in self.packages]):
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
    
    QCoreApplication.setAttribute(Qt.AA_UseDesktopOpenGL, True)
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = Application([NAME])
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    app.startTimer(100)

    app.setOrganizationName("qDiffusion")
    app.setOrganizationDomain("qDiffusion")
    
    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)
    
    translator = Translator(app)
    coordinator = Coordinator(app, engine)

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

    engine.addImageProvider("sync", backend.thumbnails.sync_provider)
    engine.addImageProvider("async", backend.thumbnails.async_provider)
    engine.addImageProvider("big", backend.thumbnails.big_provider)

    qmlRegisterSingletonType(gui.GUI, "gui", 1, 0, "GUI", lambda qml, js: backend)
    
    loadTabs(backend, backend)

def exceptHook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a", encoding='utf-8') as f:
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
