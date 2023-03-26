@echo off

if not exist .\venv\ (
	mkdir venv
	python -m venv .\venv\
	start /wait /b "" .\venv\Scripts\pip3.exe install torch torchvision --index-url https://download.pytorch.org/whl/cu117
	start /wait /b "" .\venv\Scripts\pip3.exe install -r .\requirements.txt
	start /wait /b "" .\venv\Scripts\pip3.exe install basicsr
	start /wait /b "" .\venv\Scripts\pip3.exe uninstall --yes opencv-python
	start /wait /b "" .\venv\Scripts\pip3.exe install opencv-python-headless
	start /wait /b "" .\venv\Scripts\pip3.exe install xformers
)

.\venv\Scripts\python.exe .\main.py
exit