@echo off
IF NOT EXIST "python" (
    echo DOWNLOADING PYTHON...
    bitsadmin.exe /transfer "DOWNLOADING PYTHON..." "https://github.com/indygreg/python-build-standalone/releases/download/20230507/cpython-3.10.11+20230507-x86_64-pc-windows-msvc-shared-install_only.tar.gz" "%CD%/python-3.10.11.tar.gz"
    echo EXTRACTING PYTHON...
    tar -xf "python-3.10.11.tar.gz"
    del /Q "python-3.10.11.tar.gz"
)
start .\python\python.exe source\launch.py
exit