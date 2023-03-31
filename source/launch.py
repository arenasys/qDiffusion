import sys
import subprocess
import os
import platform
import time
IS_WIN = platform.system() == 'Windows'
QT_VER = "PyQt5==5.15.7"
VENV_DIR = os.path.join(os.getcwd(), "venv")

INSIDE_VENV = VENV_DIR in sys.executable
MISSING_VENV = not os.path.exists("venv")
MISSING_QT = False

try:
    from PyQt5.QtCore import Qt
except Exception:
    MISSING_QT = True

def get_env():
    env = os.environ.copy()
    env["VIRTUAL_ENV"] = VENV_DIR
    if IS_WIN:
        env["PATH"] = VENV_DIR+"\\Scripts;" + env["PATH"]
    else:
        env["PATH"] = VENV_DIR+"/bin:" + env["PATH"]
    return env

def restart():
    print("DONE. PLEASE RELAUNCH.")
    print("CLOSING...")
    time.sleep(3)
    exit()

def install_venv():
    print("CREATING VENV...")
    subprocess.run("python -m venv venv".split(' '))

def install_qt():
    print("INSTALLNG PyQt...")
    if IS_WIN:
        subprocess.run(("venv\\Scripts\\pip install "+QT_VER).split(' '), env=get_env())
    else:
        subprocess.run(("venv/bin/pip install "+QT_VER).split(' '), env=get_env())

if not INSIDE_VENV:
    if MISSING_VENV:
        install_venv()
        install_qt()
    restart()

if INSIDE_VENV and MISSING_QT:
    install_qt()

import main
main.main()