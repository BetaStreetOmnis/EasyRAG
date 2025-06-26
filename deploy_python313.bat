@echo off
setlocal enabledelayedexpansion

:: Set console code page to UTF-8
chcp 65001 > nul

:: Title and color settings
title EasyRAG Knowledge Base System (Python 3.13 Compatible)
color 0A

:: Welcome message
echo =======================================================
echo      EasyRAG Knowledge Base System (Python 3.13)
echo =======================================================
echo.
echo This script will deploy EasyRAG using your existing Python 3.13.
echo.
echo =======================================================
echo.

:: Check if Python is installed
echo [1/6] Checking Python environment...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo Python not found. Please install Python first.
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo Detected Python version: !PYTHON_VERSION!
    echo ✅ Using existing Python installation
)

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

:: Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/

:: Install numpy with fallback
echo Installing numpy...
python -m pip install numpy --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
if !errorlevel! neq 0 (
    echo Aliyun mirror failed, trying official PyPI...
    python -m pip install numpy --cache-dir %PIP_CACHE_DIR%
)

:: Check for NVIDIA GPU
echo Checking for NVIDIA GPU...
where nvidia-smi >nul 2>nul
if %errorlevel% equ 0 (
    echo NVIDIA GPU detected, installing GPU dependencies...
    python -m pip install torch torchvision torchaudio --cache-dir %PIP_CACHE_DIR% --index-url https://download.pytorch.org/whl/cu121
    pip install -r requirements_gpu.txt --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
) else (
    echo No NVIDIA GPU detected, using CPU version...
    python -m pip install torch torchvision torchaudio --cache-dir %PIP_CACHE_DIR% --index-url https://download.pytorch.org/whl/cpu
    pip install -r requirements_cpu.txt --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
)

echo Dependencies installed!

:: Create necessary directories
echo [4/6] Creating necessary directories...
mkdir db 2>nul
mkdir models_file 2>nul
mkdir temp_files 2>nul
echo Directories created!

:: Start services
echo [6/6] Starting services...
echo.
echo All preparations complete, starting services!
echo.

:: Prepare the activation command for the virtual environment
set VENV_ACTIVATE=%CD%\py_env\Scripts\activate.bat

:: Start two command prompt windows
echo Starting API server in new window...
start cmd /k "call %VENV_ACTIVATE% && python app.py"
timeout /t 5 > nul

echo Starting Web UI in new window...
start cmd /k "call %VENV_ACTIVATE% && python ui.py"

echo.
echo EasyRAG knowledge base system started!
echo API server running at: http://localhost:8028
echo Web interface running at: http://localhost:7861
echo.
echo Please visit http://localhost:7861 in your browser to use the system
echo.

pause 