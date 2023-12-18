#!/bin/bash

if [ ! -d "./source" ] 
then
    cd ..
fi

if [ ! -d "./python" ] 
then
    echo "DOWNLOADING PYTHON..."
    curl -L --progress-bar "https://github.com/indygreg/python-build-standalone/releases/download/20230726/cpython-3.10.12+20230726-x86_64_v3-unknown-linux-gnu-install_only.tar.gz" -o "python.tar.gz"
    
    echo "EXTRACTING PYTHON..."
    tar -xf "python.tar.gz"
    rm "python.tar.gz"
fi
./python/bin/python3 source/launch.py