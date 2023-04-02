if [ ! -d "venv" ] 
then
	echo INITIALIZING...
	python -m venv venv
	source venv/bin/activate
	pip install PyQt5==5.15.7
else
    source venv/bin/activate
fi

python source/main.py