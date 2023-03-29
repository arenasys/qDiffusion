@echo off

if not exist .\venv\ (
	echo "INITIALIZING..."
	mkdir venv
	python -m venv .\venv\
	call .\venv\Scripts\activate.bat
	start /wait /b pip3 install --upgrade pip
	start /wait /b pip3 install wheel
	start /wait /b pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu117
	start /wait /b pip3 install -r .\requirements.txt
	start /wait /b pip3 install xformers
	start /wait /b pip3 install basicsr
	start /wait /b pip3 uninstall --yes opencv-python
	start /wait /b pip3 install opencv-python-headless
) else (
	call .\venv\Scripts\activate.bat
)

start pythonw .\main.py
exit