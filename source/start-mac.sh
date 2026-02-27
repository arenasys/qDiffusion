#!/bin/sh

if [ ! -d "./python" ]
then
    python_url="https://github.com/indygreg/python-build-standalone/releases/download/20260112/cpython-3.14.0+20260112-x86_64-apple-darwin-install_only.tar.gz"

    echo "DOWNLOADING PYTHON..."
    if ! curl -fL --progress-bar "$python_url" -o "python.tar.gz"; then
        echo "ERROR: Failed to download bundled Python 3.14 for macOS x86_64."
        echo "Tried URL: $python_url"
        exit 1
    fi

    echo "EXTRACTING PYTHON..."
    if ! tar -xf "python.tar.gz"; then
        echo "ERROR: Failed to extract bundled Python archive."
        rm -f "python.tar.gz"
        exit 1
    fi

    rm "python.tar.gz"
fi
./python/bin/python3 source/launch.py "$@"
