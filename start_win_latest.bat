@echo off

if not exist .\venv\ (
	echo INITIALIZING...
	mkdir venv
	python -m venv .\venv\
	call .\venv\Scripts\activate.bat
	start /wait /b pip install wheel
	start /wait /b pip install torch==2.0.0+cu118 torchvision==0.15.0+cu118 --extra-index-url https://download.pytorch.org/whl/cu118
	start /wait /b pip install -r source\requirements_gui.txt
	start /wait /b pip install -r source\requirements_inference.txt
	start /wait /b pip install -I -U --no-deps https://github.com/DDStorage/LoRA_Easy_Training_Scripts/releases/download/torch2.0.0/xformers-0.0.17+b3d75b3.d20230320-cp310-cp310-win_amd64.whl
	start /wait /b pip install -I -U --no-deps https://github.com/derrian-distro/LoRA_Easy_Training_Scripts/blob/main/installables/triton-2.0.0-cp310-cp310-win_amd64.whl?raw=true
	start /wait /b pip install basicsr
	start /wait /b pip uninstall --yes opencv-python
	start /wait /b pip install opencv-python-headless
) else (
	call .\venv\Scripts\activate.bat
)

start python source\main.py
exit