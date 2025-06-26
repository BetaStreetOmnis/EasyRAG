@echo off
setlocal enabledelayedexpansion

:: Set console code page to UTF-8
chcp 65001 > nul

:: Title and color settings
title EasyRAG Knowledge Base System
color 0A

:: Welcome message
echo =======================================================
echo           EasyRAG Knowledge Base System
echo =======================================================
echo.
echo This script will help you deploy the EasyRAG local knowledge base system.
echo It will check and install required components automatically.
echo.
echo =======================================================
echo.

:: Check if Python is installed and verify version
echo [1/6] Checking Python environment...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    goto InstallPython
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Detected Python version: !PYTHON_VERSION!
    
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    
    if !MAJOR! LSS 3 (
        echo Current Python version is too old.
        goto InstallPython
    ) else if !MAJOR! EQU 3 (
        if !MINOR! LSS 9 (
            echo Current Python version is too old.
            goto InstallPython
        ) else if !MINOR! GTR 9 (
            echo WARNING: Python version higher than 3.9 detected.
            echo The system is designed for Python 3.9.
            choice /C YN /M "Do you want to continue anyway"
            if !errorlevel! equ 2 goto InstallPython
        )
    )
)
goto ContinueSetup

:InstallPython
echo Python 3.9 not found, downloading and installing Python 3.9...
echo.

:: Create temp directory
mkdir tmp 2>nul
cd tmp

:: Download Python installer
echo Downloading Python 3.9.13...
curl -L "https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe" -o python-installer.exe

if exist python-installer.exe (
    echo Download complete, installing Python 3.9...
    :: Silent install with /quiet parameter, add to PATH
    start /wait python-installer.exe /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
    
    :: Check if installation was successful
    python --version >nul 2>nul
    if !errorlevel! neq 0 (
        echo Python installation failed. Please install Python 3.9 manually from:
        echo https://www.python.org/downloads/release/python-3913/
        cd ..
        pause
        exit /b 1
    ) else (
        echo Python 3.9 installed successfully!
    )
) else (
    echo Failed to download Python installer. Please check your network connection.
    echo You can manually download Python 3.9.13 from:
    echo https://www.python.org/downloads/release/python-3913/
    cd ..
    pause
    exit /b 1
)

cd ..
rmdir /s /q tmp

:ContinueSetup
echo.

:: Check and create virtual environment
echo [2/6] Setting up virtual environment...
if not exist py_env (
    echo Creating virtual environment...
    python -m venv py_env
) else (
    echo Virtual environment already exists...
)

:: Activate virtual environment
echo Activating virtual environment...
call py_env\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Virtual environment activation failed. Please try manually.
    pause
    exit /b 1
)
echo Virtual environment activated successfully!

echo.

:: Install dependencies
echo [3/6] Installing dependencies...
echo Creating and configuring pip cache directory...
mkdir pip_cache 2>nul
set PIP_CACHE_DIR=%CD%\pip_cache

:: Check for NVIDIA GPU
echo Checking for NVIDIA GPU...
where nvidia-smi >nul 2>nul
if %errorlevel% equ 0 (
    echo nvidia-smi command found, checking if driver is working properly...
    nvidia-smi >nul 2>nul
    if !errorlevel! equ 0 (
        echo NVIDIA GPU detected, installing GPU dependencies...
        echo Installing base dependencies first...
        python -m pip install --upgrade pip setuptools wheel --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
        python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
        python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir %PIP_CACHE_DIR% -i https://download.pytorch.org/whl/cu121
        echo Installing remaining dependencies...
        pip install -r requirements_gpu.txt --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
    ) else (
        echo NVIDIA driver not working properly. Error running nvidia-smi.
        echo Using CPU version instead...
        goto InstallCPUVersion
    )
) else (
    echo No NVIDIA GPU detected, using CPU version...
    goto InstallCPUVersion
)
goto EndGPUCheck

:InstallCPUVersion
echo Installing base dependencies first...
python -m pip install --upgrade pip setuptools wheel --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir %PIP_CACHE_DIR% -i https://download.pytorch.org/whl/cpu
echo Installing remaining dependencies...
pip install -r requirements_cpu.txt --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
goto EndGPUCheck

:EndGPUCheck

if %errorlevel% neq 0 (
    echo Dependency installation failed. Check your network connection.
    pause
    exit /b 1
)
echo Dependencies installed!

echo.
echo NOTE: faiss package was skipped during installation.
echo If you need vector similarity search functionality, please install it manually:
echo - For CPU: pip install faiss-cpu
echo - For GPU: pip install faiss-gpu
echo.

:: Create necessary directories
echo [4/6] Creating necessary directories...
mkdir db 2>nul
mkdir models_file 2>nul
mkdir temp_files 2>nul
echo Directories created!

echo.


echo.

:: Start services
echo [6/6] Starting services...
echo.
echo All preparations complete, starting services!
echo.
echo Note: Press Ctrl+C to stop the services
echo.

:: Start two command prompt windows, one for API server, one for Web UI
start cmd /k "call py_env\Scripts\activate.bat && python app.py"
timeout /t 5 > nul
start cmd /k "call py_env\Scripts\activate.bat && python ui.py"

echo.
echo EasyRAG knowledge base system started!
echo API server running at: http://localhost:8000
echo Web interface running at: http://localhost:7861
echo.
echo Please visit http://localhost:7861 in your browser to use the system
echo.

pause 