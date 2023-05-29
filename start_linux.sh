if [ ! -d "./python" ] 
then
    echo "DOWNLOADING PYTHON..."
    curl -L --progress-bar "https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64_v3-unknown-linux-gnu-install_only.tar.gz" -o "python-3.10.11.tar.gz"
    echo "EXTRACTING PYTHON..."
    tar -xf "python-3.10.11.tar.gz"
    rm "python-3.10.11.tar.gz"
fi
./python/bin/python3 source/launch.py