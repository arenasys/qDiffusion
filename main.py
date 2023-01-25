import sys
import signal
import traceback
import datetime
import subprocess
import os

from PyQt5.QtCore import QUrl, QCoreApplication, Qt
from PyQt5.QtQml import QQmlApplicationEngine, qmlRegisterSingletonType
from PyQt5.QtWidgets import QApplication

import gui

class Application(QApplication):
        def event(self, e):
            return QApplication.event(self, e)

def compile():
    qml_py = os.path.join("qml", "qml_rc.py")
    qml_rc = os.path.join("qml", "qml.qrc")
    
    if os.path.exists(qml_py):
        os.remove(qml_py)
    status = subprocess.run(["pyrcc5", "-o", qml_py, qml_rc], capture_output=True)
    if status.returncode != 0:
        raise Exception(status.stderr.decode("utf-8"))

def start():
    import qml.qml_rc

    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = Application(sys.argv)
    signal.signal(signal.SIGINT, lambda sig, frame: app.quit())
    app.startTimer(100)

    engine = QQmlApplicationEngine()
    engine.quit.connect(app.quit)

    qmlRegisterSingletonType(QUrl("qrc:/Common.qml"), "gui", 1, 0, "COMMON")
    qmlRegisterSingletonType(gui.GUI, "gui", 1, 0, "GUI", lambda qml, js: gui.GUI(parent=app))

    engine.load(QUrl('qrc:/Main.qml'))
    
    sys.exit(app.exec())

def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a") as f:
        f.write(f"{datetime.datetime.now()}\n{tb}\n")
    print(tb)
    print("TRACEBACK SAVED: crash.log")
    QApplication.quit()

if __name__ == "__main__":
    sys.excepthook = excepthook
    compile()
    start()
