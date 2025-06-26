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
    echo Python not found, will install Python 3.9...
    goto InstallPython
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Detected Python version: !PYTHON_VERSION!
    
    for /f "tokens=1,2 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
    )
    
    if !MAJOR! LSS 3 (
        echo Current Python version is too old. Installing Python 3.9...
        goto InstallPython
    ) else if !MAJOR! EQU 3 (
        if !MINOR! NEQ 9 (
            echo Python 3.9 is required for optimal compatibility.
            echo Current version: !PYTHON_VERSION!
            echo Installing Python 3.9...
            goto InstallPython
        )
    ) else (
        echo Python version is newer than 3.9. Installing Python 3.9 for compatibility...
        goto InstallPython
    )
)
goto ContinueSetup

:InstallPython
echo.
echo =======================================================
echo Installing Python 3.9.13 for optimal compatibility
echo =======================================================
echo.
echo Note: This will install Python 3.9.13 alongside your existing Python installation.
echo The script will use Python 3.9 for this project while keeping your current Python intact.
echo.

:: Create temp directory
mkdir tmp 2>nul
cd tmp

:: Download Python installer
echo [Step 1/3] Downloading Python 3.9.13 installer...
echo This may take a few minutes depending on your internet connection...
curl -L "https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe" -o python-installer.exe

if exist python-installer.exe (
    echo [Step 2/3] Download complete! Installing Python 3.9.13...
    echo Installing to: %LOCALAPPDATA%\Programs\Python\Python39
    :: Install to a specific directory to avoid conflicts
    start /wait python-installer.exe /quiet InstallAllUsers=0 TargetDir="%LOCALAPPDATA%\Programs\Python\Python39" PrependPath=0 Include_test=0
    
    :: Set Python path for this session
    set PYTHON39_PATH=%LOCALAPPDATA%\Programs\Python\Python39
    set PATH=%PYTHON39_PATH%;%PYTHON39_PATH%\Scripts;%PATH%
    
    :: Check if installation was successful
    echo [Step 3/3] Verifying Python 3.9 installation...
    "%PYTHON39_PATH%\python.exe" --version >nul 2>nul
    if !errorlevel! neq 0 (
        echo Python 3.9 installation failed. Please try the following:
        echo 1. Run this script as Administrator
        echo 2. Check your internet connection
        echo 3. Manually install Python 3.9.13 from: https://www.python.org/downloads/release/python-3913/
        cd ..
        pause
        exit /b 1
    ) else (
        for /f "tokens=2" %%i in ('"%PYTHON39_PATH%\python.exe" --version 2^>^&1') do set INSTALLED_VERSION=%%i
        echo ✅ Python !INSTALLED_VERSION! installed successfully!
        echo Using Python 3.9 for this project: %PYTHON39_PATH%\python.exe
        
        :: Use the newly installed Python 3.9 for the rest of the script
        set PYTHON_CMD="%PYTHON39_PATH%\python.exe"
    )
) else (
    echo Failed to download Python installer. Please check:
    echo 1. Your internet connection
    echo 2. Firewall settings (curl may be blocked)
    echo 3. Try running as Administrator
    echo.
    echo You can manually download Python 3.9.13 from:
    echo https://www.python.org/downloads/release/python-3913/
    cd ..
    pause
    exit /b 1
)

cd ..
rmdir /s /q tmp
goto ContinueSetup

:ContinueSetup
echo.

:: Set Python command if not already set (for existing Python installations)
if not defined PYTHON_CMD (
    set PYTHON_CMD=python
)

:: Check and create virtual environment
echo [2/6] Setting up virtual environment...
if not exist py_env (
    echo Creating virtual environment with Python 3.9...
    %PYTHON_CMD% -m venv py_env
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