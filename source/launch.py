import sys
import subprocess
import os
import platform
import time
IS_WIN = platform.system() == 'Windows'
QT_VER = "PyQt5==5.15.7"
VENV_DIR = os.path.join(os.getcwd(), "venv")

INSIDE_VENV = VENV_DIR in sys.executable and VENV_DIR in os.environ["PATH"]
MISSING_VENV = not os.path.exists("venv")
MISSING_QT = False

PYTHON_RUN = sys.executable

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
    if IS_WIN:
        subprocess.Popen(("venv\\Scripts\\pythonw source\\launch.py").split(' '), env=get_env(), creationflags=0x00000008|0x00000200)
    else:
        subprocess.Popen(("venv/bin/python source/launch.py").split(' '), env=get_env())
    exit()

def install_venv():
    print("CREATING VENV...")
    subprocess.run(f"{PYTHON_RUN} -m venv venv".split(' '))

def install_qt():
    print("INSTALLNG PyQt...")
    if IS_WIN:
        subprocess.run(("venv\\Scripts\\pip install "+QT_VER).split(' '), env=get_env())
    else:
        subprocess.run(("venv/bin/pip install "+QT_VER).split(' '), env=get_env())

if __name__ == "__main__":
    if sys.version_info[0] < 3 or sys.version_info[1] < 8:
        raise Exception(f"Python 3.8 or greater required. Have Python {sys.version_info[0]}.{sys.version_info[1]}.")

    if not INSIDE_VENV:
        if MISSING_VENV:
            install_venv()
            install_qt()
            print("DONE.")
        restart()
    elif INSIDE_VENV and MISSING_QT:
        install_qt()

    import main
    main.main()