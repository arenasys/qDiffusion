@echo off

for /f "tokens=4-7 delims=[.] " %%i in ('ver') do (if %%i==Version (set v=%%j.%%k) else (set v=%%i.%%j))
echo "%v"
IF "%v%" == "6.1" (
    set python_version = "20230726/cpython-3.8.16+20230726-x86_64-pc-windows-msvc-shared-install_only.tar.gz"
) ELSE (
    set python_version = "20230726/cpython-3.10.12+20230726-x86_64-pc-windows-msvc-shared-install_only.tar.gz"
)

IF NOT EXIST "python" (
    echo DOWNLOADING PYTHON...
    bitsadmin.exe /transfer "DOWNLOADING PYTHON..." "https://github.com/indygreg/python-build-standalone/releases/download/%python_version%" "%CD%/python.tar.gz"
    echo EXTRACTING PYTHON...
    tar -xf "python.tar.gz"
    del /Q "python.tar.gz"
)
start .\python\python.exe source\launch.py
exit