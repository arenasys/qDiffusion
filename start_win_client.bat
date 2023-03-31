@echo off

if not exist .\venv\ (
	echo INITIALIZING...
	mkdir venv
	python -m venv .\venv\
	call .\venv\Scripts\activate.bat
	start /wait /b pip install wheel
	start /wait /b pip install -r source\requirements_gui.txt
) else (
	call .\venv\Scripts\activate.bat
)

start python source\main.py
exit