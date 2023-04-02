@echo off

if not exist .\venv\ (
	echo INITIALIZING...
	python -m venv venv
	call .\venv\Scripts\activate.bat
	start /wait /b pip install "PyQt5==5.15.7"
) else (
	call .\venv\Scripts\activate.bat
)

start python source\launch.py
exit