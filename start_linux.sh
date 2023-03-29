if [ ! -d "venv" ] 
then
	pip install --upgrade pip
	python -m venv venv
	source venv/bin/activate
	pip install torch torchvision
	pip install -r source/requirements.txt
	pip install basicsr
	pip uninstall --yes opencv-python
	pip install opencv-python-headless
	pip install xformers
else
    source venv/bin/activate
fi

python source/main.py