import sys
import signal
import traceback
import datetime
import subprocess
import os
import glob
import shutil
import importlib

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QUrl, QCoreApplication, Qt, QElapsedTimer, QThread
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType, qmlRegisterType
from PyQt5.QtWidgets import QApplication

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

    status = subprocess.run(["pyrcc5", "-o", qml_py, qml_rc], capture_output=True)
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


class Coordinator(QObject):
    ready = pyqtSignal()
    def __init__(self, app, engine):
        super().__init__(app)
        self.app = app
        self.engine = engine
        self.builder = Builder(app, engine)
        self.builder.finished.connect(self.done)

    @pyqtSlot()
    def load(self):
        self.builder.start()

    @pyqtSlot()
    def done(self):
        start(self.engine, self.app)
        self.ready.emit()
    
def launch():
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = Application(sys.argv)
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    app.startTimer(100)
    
    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)

    coordinator = Coordinator(app, engine)
    qmlRegisterSingletonType(Coordinator, "gui", 1, 0, "COORDINATOR", lambda qml, js: coordinator)

    engine.load(QUrl('file:source/qml/Launcher.qml'))

    os._exit(app.exec())

def start(engine, app):
    import qml.qml_rc
    import gui
    import sql
    import canvas
    import parameters

    sql.registerTypes()
    gui.registerTypes()
    canvas.registerTypes()
    canvas.registerMiscTypes()
    parameters.registerTypes()

    qmlRegisterSingletonType(QUrl("qrc:/Common.qml"), "gui", 1, 0, "COMMON")

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

if __name__ == "__main__":
    if not os.path.exists("source"):
        os.chdir('..')

    sys.excepthook = exceptHook
    launch()
