if not DEFINED IS_MINIMIZED set IS_MINIMIZED=1 && start "" /min "%~dpnx0" %* && exit
@echo off

if not exist .\venv\ (
	mkdir venv
	python -m venv .\venv\
	start /wait /b "" .\venv\Scripts\pip3.exe install -r .\requirements.txt
	start /wait /b "" .\venv\Scripts\pip3.exe install basicsr
	start /wait /b "" .\venv\Scripts\pip3.exe uninstall opencv-python
	start /wait /b "" .\venv\Scripts\pip3.exe uninstall opencv-python-headless
	start /wait /b "" .\venv\Scripts\pip3.exe install opencv-python-headless
	start /wait /b "" .\venv\Scripts\pip3.exe install xformers
)

.\venv\Scripts\python.exe .\main.py
exit