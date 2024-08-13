#!/bin/sh

if [ ! -d "./python" ] 
then
    echo "DOWNLOADING PYTHON..."
    curl -L --progress-bar "https://github.com/indygreg/python-build-standalone/releases/download/20240726/cpython-3.10.14+20240726-x86_64-apple-darwin-install_only.tar.gz" -o "python.tar.gz"
    echo "EXTRACTING PYTHON..."
    tar -xf "python.tar.gz"
    rm "python.tar.gz"
fi
./python/bin/python3 source/launch.py "$@"