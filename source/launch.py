import sys
import subprocess
import os
import platform
import traceback
import datetime
import importlib.util

VENV_DIR = os.path.join(os.getcwd(), "venv")
IS_WIN = platform.system() == 'Windows'
PYTHON_RUN = sys.executable

QT_VER = "PyQt5==5.15.7"
MISSING_QT = False
try:
    from PyQt5.QtCore import Qt
except Exception:
    MISSING_QT = True

def get_env():
    env = {k:v for k,v in os.environ.items() if not k.startswith("QT")}
    env["VIRTUAL_ENV"] = VENV_DIR
    if IS_WIN:
        env["PATH"] = VENV_DIR+"\\Scripts;" + env["PATH"]
    else:
        env["PATH"] = VENV_DIR+"/bin:" + env["PATH"]
    
    if not IS_WIN and not "HSA_OVERRIDE_GFX_VERSION" in env:
        env["HSA_OVERRIDE_GFX_VERSION"] = "10.3.0"
    if not IS_WIN and not "MIOPEN_LOG_LEVEL" in env:
        env["MIOPEN_LOG_LEVEL"] = "4"
    return env

def restart():
    if IS_WIN:
        subprocess.Popen([VENV_DIR+"\\Scripts\\pythonw.exe", "source\\launch.py"], env=get_env(), creationflags=0x00000008|0x00000200)
    else:
        subprocess.Popen([VENV_DIR+"/bin/python", "source/launch.py"], env=get_env())
    exit()

def install_venv():
    print(f"CREATING VENV... ({VENV_DIR})")
    subprocess.run((f"{PYTHON_RUN} -m venv " + VENV_DIR).split(' '))

def install_qt():
    print("INSTALLNG PyQt...")
    if IS_WIN:
        subprocess.run([VENV_DIR+"\\Scripts\\python.exe", "-m", "pip", "install", QT_VER], env=get_env())
    else:
        subprocess.run([VENV_DIR+"/bin/python", "-m", "pip", "install", QT_VER], env=get_env())

def exceptHook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    with open("crash.log", "a", encoding='utf-8') as f:
        f.write(f"LAUNCH {datetime.datetime.now()}\n{tb}\n")
    print(tb)
    print("TRACEBACK SAVED: crash.log")

    if not "pythonw" in PYTHON_RUN:
        input("PRESS ENTER TO CLOSE")

if __name__ == "__main__":
    sys.excepthook = exceptHook

    if sys.version_info[0] < 3 or sys.version_info[1] < 8:
        print(f"Python 3.8 or greater is required. Have Python {sys.version_info[0]}.{sys.version_info[1]}.")
        input()
        exit()
    if not importlib.util.find_spec("pip"):
        print("PIP module is required.")
        input()
        exit()
    if not importlib.util.find_spec("venv"):
        print("VENV module is required.")
        input()
        exit()
    
    if len(sys.argv) > 1:
        VENV_DIR = sys.argv[1]
    VENV_DIR = os.path.abspath(VENV_DIR)

    invalid = ''.join([c for c in VENV_DIR if ord(c) > 127])
    if invalid:
        print(f"PATH INVALID ({VENV_DIR}) CONTAINS UNICODE ({invalid})")
        if IS_WIN:
            VENV_DIR = os.getcwd()[0]+":\\qDiffusion"
            print(f"USING {VENV_DIR} INSTEAD")
        else:
            print("FAILED")
            input()
            exit()

    inside_venv = VENV_DIR in sys.executable and VENV_DIR in os.environ["PATH"] and VENV_DIR == os.environ.get("VIRTUAL_ENV", "")
    missing_venv = not os.path.exists(VENV_DIR)

    if not inside_venv:
        if missing_venv:
            install_venv()
            install_qt()
            print("DONE.")
        restart()
    elif inside_venv and MISSING_QT:
        install_qt()

    import main
    main.main()