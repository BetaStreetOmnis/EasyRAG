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
    
    :: Try multiple installation strategies
    echo Attempting installation method 1: User-level installation...
    start /wait python-installer.exe /quiet InstallAllUsers=0 TargetDir="%LOCALAPPDATA%\Programs\Python\Python39" PrependPath=0 Include_test=0
    
    :: Set Python path for this session
    set PYTHON39_PATH=%LOCALAPPDATA%\Programs\Python\Python39
    set PATH=%PYTHON39_PATH%;%PYTHON39_PATH%\Scripts;%PATH%
    
    :: Check if installation was successful
    echo [Step 3/3] Verifying Python 3.9 installation...
    "%PYTHON39_PATH%\python.exe" --version >nul 2>nul
    if !errorlevel! neq 0 (
        echo First installation attempt failed, trying alternative method...
        
        :: Try simpler installation without target directory
        echo Attempting installation method 2: Default user installation...
        start /wait python-installer.exe /quiet InstallAllUsers=0 PrependPath=0 Include_test=0
        
        :: Try to find Python 3.9 in common locations
        set PYTHON39_PATH=
        if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" (
            set PYTHON39_PATH=%LOCALAPPDATA%\Programs\Python\Python39
        ) else if exist "%APPDATA%\Local\Programs\Python\Python39\python.exe" (
            set PYTHON39_PATH=%APPDATA%\Local\Programs\Python\Python39
        ) else if exist "C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39\python.exe" (
            set PYTHON39_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python39
        ) else (
            :: Try to find any Python 3.9 installation
            for /f "tokens=*" %%i in ('where python 2^>nul') do (
                for /f "tokens=2" %%j in ('"%%i" --version 2^>^&1') do (
                    echo Found Python: %%i with version %%j
                    if "%%j"=="3.9.13" (
                        set PYTHON39_PATH=%%~dpi
                        goto FoundPython39
                    )
                )
            )
        )
        
        :FoundPython39
        if defined PYTHON39_PATH (
            set PATH=%PYTHON39_PATH%;%PYTHON39_PATH%\Scripts;%PATH%
            "%PYTHON39_PATH%\python.exe" --version >nul 2>nul
            if !errorlevel! equ 0 (
                for /f "tokens=2" %%i in ('"%PYTHON39_PATH%\python.exe" --version 2^>^&1') do set INSTALLED_VERSION=%%i
                echo ✅ Python !INSTALLED_VERSION! found and verified!
                echo Using Python 3.9 for this project: %PYTHON39_PATH%\python.exe
                set PYTHON_CMD="%PYTHON39_PATH%\python.exe"
                goto PythonInstallSuccess
            )
        )
        
        :: If all methods failed, try interactive installation
        echo All automatic installation methods failed.
        echo Attempting interactive installation (you may see a window)...
        start /wait python-installer.exe
        
        :: Final check
        python --version >nul 2>nul
        if !errorlevel! equ 0 (
            for /f "tokens=2" %%i in ('python --version 2^>^&1') do set FINAL_VERSION=%%i
            echo ✅ Python !FINAL_VERSION! is now available!
            set PYTHON_CMD=python
            goto PythonInstallSuccess
        )
        
        :: Complete failure
        echo ❌ Python 3.9 installation failed completely.
        echo.
        echo Troubleshooting steps:
        echo 1. Run this script as Administrator (Right-click → Run as administrator)
        echo 2. Temporarily disable antivirus software
        echo 3. Check if you have sufficient disk space (at least 100MB)
        echo 4. Manual installation:
        echo    - Download from: https://www.python.org/downloads/release/python-3913/
        echo    - Choose "Windows installer (64-bit)" 
        echo    - Run the installer and check "Add Python to PATH"
        echo.
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
    
    :PythonInstallSuccess
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

:: Verify Python version in virtual environment
echo Verifying Python version in virtual environment...
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set VENV_PYTHON_VERSION=%%i
echo Virtual environment Python version: !VENV_PYTHON_VERSION!

:: Check if it's Python 3.9.x
for /f "tokens=1,2 delims=." %%a in ("!VENV_PYTHON_VERSION!") do (
    set VENV_MAJOR=%%a
    set VENV_MINOR=%%b
)

if !VENV_MAJOR! EQU 3 (
    if !VENV_MINOR! EQU 9 (
        echo ✅ Virtual environment is using Python 3.9 correctly!
    ) else (
        echo ⚠️  Warning: Virtual environment is using Python 3.!VENV_MINOR! instead of 3.9
        echo This may cause compatibility issues.
    )
) else (
    echo ⚠️  Warning: Virtual environment is using Python !VENV_MAJOR!.!VENV_MINOR! instead of 3.9
    echo This may cause compatibility issues.
)

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
        
        echo Installing numpy with multiple fallback strategies...
        python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/
        if !errorlevel! neq 0 (
            echo Aliyun mirror failed, trying Tsinghua mirror...
            python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR% -i https://pypi.tuna.tsinghua.edu.cn/simple/
            if !errorlevel! neq 0 (
                echo Tsinghua mirror failed, trying official PyPI...
                python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR%
                if !errorlevel! neq 0 (
                    echo Specific version failed, trying latest compatible version...
                    python -m pip install numpy --cache-dir %PIP_CACHE_DIR%
                    if !errorlevel! neq 0 (
                        echo NumPy installation failed completely. Please check your Python environment.
                        pause
                        exit /b 1
                    )
                )
            )
        )
        echo NumPy installed successfully!
        
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

:: Prepare the activation command for the virtual environment
set VENV_ACTIVATE=%CD%\py_env\Scripts\activate.bat

:: Start two command prompt windows, one for API server, one for Web UI
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
echo Two new command prompt windows have been opened:
echo - One for the API server (app.py)
echo - One for the Web UI (ui.py)
echo.
echo Both are using the Python 3.9 virtual environment created by this script.
echo.

pause 