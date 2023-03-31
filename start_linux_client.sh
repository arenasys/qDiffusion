if [ ! -d "venv" ] 
then
	pip install --upgrade pip
	python -m venv venv
	source venv/bin/activate
	pip install wheel
	pip install -r source/requirements_gui.txt
else
    source venv/bin/activate
fi

python source/main.py