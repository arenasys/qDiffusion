import sys
import subprocess
import os
import platform
IS_WIN = platform.system() == 'Windows'
QT_VER = "PyQt5==5.15.7"
VENV_DIR = os.path.join(os.getcwd(), "venv")

INSIDE_VENV = sys.prefix == VENV_DIR
MISSING_VENV = not os.path.exists("venv")
MISSING_QT = False

try:
    from PyQt5.QtCore import Qt
except Exception:
    MISSING_QT = True

def restart():
    if IS_WIN:
        env = os.environ.copy()
        env["PATH"] = os.getcwd()+"\\venv\\Scripts:" + env["PATH"]
        subprocess.run(("venv\\Scripts\\pythonw source\\launch.py").split(' '), env=env)
    else:
        env = os.environ.copy()
        env["PATH"] = os.getcwd()+"/venv/bin:" + env["PATH"]
        subprocess.Popen(("venv/bin/python source/launch.py").split(' '), env=env)
    exit()

def install_venv():
    subprocess.run("python -m venv venv".split(' '))

def install_qt():
    if IS_WIN:
        subprocess.run(("venv\\Scripts\\pip install "+QT_VER).split(' '))
    else:
        subprocess.run(("venv/bin/pip install "+QT_VER).split(' '))

if not INSIDE_VENV:
    if MISSING_VENV:
        install_venv()
        if MISSING_QT:
            install_qt()
    restart()

if INSIDE_VENV and MISSING_QT:
    install_qt()

import main
main.main()