@echo off
setlocal enabledelayedexpansion

rem Color settings
set "GREEN=[92m"
set "YELLOW=[93m"
set "RED=[91m"
set "NC=[0m"

rem Display title
echo %GREEN%=======================================================
echo            EasyRAG Knowledge Base System
echo =======================================================%NC%
echo.
echo This script will help you deploy the EasyRAG local knowledge base system.
echo It will check and install required components automatically.
echo.
echo %GREEN%=======================================================%NC%
echo.

rem [1/7] Check Python installation
echo %GREEN%[1/7] Checking Python environment...%NC%
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Python is not installed or not in PATH. Please install Python 3.9 first.%NC%
    echo Visit https://www.python.org/downloads/ to download Python.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Detected %GREEN%%PYTHON_VERSION%%NC%
echo.

rem [2/7] Setup virtual environment
echo %GREEN%[2/7] Setting up virtual environment...%NC%
if not exist py_env\ (
    echo Creating virtual environment...
    python -m venv py_env
) else (
    echo Existing virtual environment found. Do you want to recreate it? (y/n)
    set /p recreate="> "
    if /i "!recreate!"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q py_env
        echo Creating fresh virtual environment...
        python -m venv py_env
    ) else (
        echo Using existing virtual environment...
    )
)

rem Verify activation script exists
if not exist py_env\Scripts\activate.bat (
    echo %RED%Virtual environment activation script not found. Creating again...%NC%
    rmdir /s /q py_env
    python -m venv py_env
    
    if not exist py_env\Scripts\activate.bat (
        echo %RED%Failed to create virtual environment. Please check your Python installation.%NC%
        pause
        exit /b 1
    )
)

rem Activate virtual environment
echo Activating virtual environment...
call py_env\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Virtual environment activation failed. Please try manually.%NC%
    pause
    exit /b 1
)
echo %GREEN%Virtual environment activated successfully!%NC%
echo.

rem [3/7] Install dependencies
echo %GREEN%[3/7] Installing dependencies...%NC%
echo Creating and configuring pip cache directory...
if not exist pip_cache mkdir pip_cache
set PIP_CACHE_DIR=%cd%\pip_cache

echo Installing base dependencies first...
python -m pip install --upgrade pip setuptools wheel --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/
python -m pip install numpy==1.24.4 --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/

rem Check for NVIDIA GPU
echo Checking for NVIDIA GPU...
where nvidia-smi > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo %GREEN%NVIDIA GPU detected, installing GPU dependencies...%NC%
    python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir "%PIP_CACHE_DIR%" -i https://download.pytorch.org/whl/cu121
    
    rem Install dependencies from requirements
    if exist requirements_gpu.txt (
        pip install -r requirements_gpu.txt --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/
    ) else (
        echo %YELLOW%requirements_gpu.txt not found, installing common dependencies...%NC%
        pip install transformers==4.36.2 gradio==4.19.1 matplotlib pymupdf requests pandas --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/
    )
    
    rem [4/7] Install FAISS GPU version
    echo %GREEN%[4/7] Installing FAISS GPU version...%NC%
    pip install faiss-gpu --no-cache-dir --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/
) else (
    echo %YELLOW%No NVIDIA GPU detected or NVIDIA driver not installed, using CPU version...%NC%
    python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir "%PIP_CACHE_DIR%" -i https://download.pytorch.org/whl/cpu
    
    rem Install dependencies from requirements
    if exist requirements_cpu.txt (
        pip install -r requirements_cpu.txt --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/
    ) else (
        echo %YELLOW%requirements_cpu.txt not found, installing common dependencies...%NC%
        pip install transformers==4.36.2 gradio==4.19.1 matplotlib pymupdf requests pandas --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/
    )
    
    rem [4/7] Install FAISS CPU version
    echo %GREEN%[4/7] Installing FAISS CPU version...%NC%
    pip install faiss-cpu --no-cache-dir --cache-dir "%PIP_CACHE_DIR%" -i https://mirrors.aliyun.com/pypi/simple/
)

if %ERRORLEVEL% NEQ 0 (
    echo %RED%Dependency installation failed. Check your network connection.%NC%
    pause
    exit /b 1
)
echo %GREEN%Dependencies installed!%NC%

rem Verify FAISS installation
echo Verifying FAISS installation...
python -c "import faiss; print(f'FAISS {faiss.__version__} installed successfully')" 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo %RED%FAISS installation could not be verified. Trying alternative method...%NC%
    where nvidia-smi > nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        pip install faiss-gpu --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/
    ) else (
        pip install faiss-cpu --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/
    )
    
    python -c "import faiss; print(f'FAISS {faiss.__version__} installed successfully')" 2>nul
    if %ERRORLEVEL% EQU 0 (
        echo %GREEN%FAISS installation succeeded with alternative method!%NC%
    ) else (
        echo %RED%FAISS installation failed. Please install it manually after the script completes.%NC%
        echo For CPU: pip install faiss-cpu
        echo For GPU: pip install faiss-gpu
    )
)

echo.

rem [5/7] Create necessary directories
echo %GREEN%[5/7] Creating necessary directories...%NC%
if not exist db mkdir db
if not exist models_file mkdir models_file
if not exist temp_files mkdir temp_files
echo %GREEN%Directories created!%NC%
echo.

rem [6/7] Download required models
echo %GREEN%[6/7] Downloading and preparing required models...%NC%
echo This process will download all required models to the models_file directory.
echo Total download size is approximately 7GB, please ensure sufficient disk space and stable network connection.
echo.

rem Configure modelscope cache
echo Configuring modelscope cache directory...
set MODELSCOPE_CACHE=%cd%\models_file

rem Download the DeepSeek LLM model
echo %YELLOW%[Model 1/4] Downloading DeepSeek 1.5B model...%NC%
python -c "from modelscope import snapshot_download; import os, traceback; try: print('Downloading DeepSeek model...'); model_id = 'deepseek-ai/deepseek-chat-1.5b-base'; model_dir = snapshot_download(model_id, cache_dir='%cd%/models_file'); print(f'DeepSeek model downloaded to {model_dir}'); except Exception as e: print(f'Error downloading DeepSeek model: {str(e)}'); traceback.print_exc();"
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Failed to download DeepSeek model. The system will attempt to download it at runtime.%NC%
) else (
    echo %GREEN%DeepSeek model downloaded successfully!%NC%
)

rem Download the Embedding model
echo %YELLOW%[Model 2/4] Downloading Embedding model...%NC%
python -c "from modelscope import snapshot_download; import os, traceback; try: print('Downloading Embedding model...'); model_id = 'iic/nlp_gte_sentence-embedding_chinese-base'; model_dir = snapshot_download(model_id, cache_dir='%cd%/models_file'); print(f'Embedding model downloaded to {model_dir}'); except Exception as e: print(f'Error downloading Embedding model: {str(e)}'); traceback.print_exc();"
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Failed to download Embedding model. The system will attempt to download it at runtime.%NC%
) else (
    echo %GREEN%Embedding model downloaded successfully!%NC%
)

rem Download the Rerank model
echo %YELLOW%[Model 3/4] Downloading Rerank model...%NC%
python -c "from modelscope import snapshot_download; import os, traceback; try: print('Downloading Rerank model...'); model_id = 'iic/gte_passage-ranking_multilingual-base'; model_dir = snapshot_download(model_id, cache_dir='%cd%/models_file'); print(f'Rerank model downloaded to {model_dir}'); except Exception as e: print(f'Error downloading Rerank model: {str(e)}'); traceback.print_exc();"
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Failed to download Rerank model. The system will attempt to download it at runtime.%NC%
) else (
    echo %GREEN%Rerank model downloaded successfully!%NC%
)

rem Download the OCR model
echo %YELLOW%[Model 4/4] Downloading OCR model...%NC%
python -c "from modelscope import snapshot_download; import os, sys, traceback; try: ocr_model_dir = os.path.join('%cd%/models_file', 'easyocr'); os.makedirs(ocr_model_dir, exist_ok=True); print(f'OCR model directory: {ocr_model_dir}'); print('Downloading OCR model...'); model_id = 'Ceceliachenen/easyocr'; model_dir = snapshot_download(model_id, cache_dir=ocr_model_dir); print(f'OCR model downloaded to {model_dir}'); try: import easyocr; print('EasyOCR already installed'); except ImportError: print('Installing EasyOCR...'); import pip; pip.main(['install', 'easyocr']); print('EasyOCR installed'); print('Initializing EasyOCR to download language models...'); sys.path.append('%cd%'); os.environ['MODELSCOPE_CACHE'] = '%cd%/models_file'; import easyocr; reader = easyocr.Reader(['ch_sim', 'en'], model_storage_directory=ocr_model_dir, download_enabled=True); print('OCR language models downloaded and initialized'); except Exception as e: print(f'Error downloading or initializing OCR model: {str(e)}'); traceback.print_exc();"
if %ERRORLEVEL% NEQ 0 (
    echo %RED%Failed to download OCR model. The system will attempt to download it at runtime.%NC%
) else (
    echo %GREEN%OCR model downloaded successfully!%NC%
)

echo %GREEN%All models download process completed. Some models may be downloaded at runtime if failed.%NC%
echo.

rem [7/7] Start services
echo %GREEN%[7/7] Starting services...%NC%
echo.
echo %GREEN%All preparations complete, starting services!%NC%
echo.
echo %YELLOW%Note: Press Ctrl+C to stop the services%NC%
echo.

rem Create startup script
echo @echo off > start_service.bat
echo setlocal >> start_service.bat
echo. >> start_service.bat
echo rem Activate virtual environment >> start_service.bat
echo call py_env\Scripts\activate.bat >> start_service.bat
echo. >> start_service.bat
echo rem Start API server >> start_service.bat
echo start "EasyRAG API Server" /min cmd /c "python api_server.py" >> start_service.bat
echo echo API server started >> start_service.bat
echo. >> start_service.bat
echo rem Wait for API server to start >> start_service.bat
echo timeout /t 5 /nobreak >> start_service.bat
echo. >> start_service.bat
echo rem Start Web UI >> start_service.bat
echo start "EasyRAG Web UI" /min cmd /c "python ui_new.py" >> start_service.bat
echo echo Web UI started >> start_service.bat
echo. >> start_service.bat
echo echo EasyRAG knowledge base system started! >> start_service.bat
echo echo API server running at: http://localhost:8000 >> start_service.bat
echo echo Web interface running at: http://localhost:7861 >> start_service.bat
echo echo. >> start_service.bat
echo echo Please visit http://localhost:7861 in your browser to use the system >> start_service.bat
echo echo. >> start_service.bat
echo echo Press any key to stop all services and exit... >> start_service.bat
echo pause >> start_service.bat
echo. >> start_service.bat
echo echo Stopping services... >> start_service.bat
echo taskkill /f /fi "WINDOWTITLE eq EasyRAG API Server*" ^>nul 2^>^&1 >> start_service.bat
echo taskkill /f /fi "WINDOWTITLE eq EasyRAG Web UI*" ^>nul 2^>^&1 >> start_service.bat
echo echo Services stopped >> start_service.bat
echo exit /b 0 >> start_service.bat

rem Start services
echo Starting services...
call start_service.bat

echo %GREEN%EasyRAG knowledge base system started!%NC%
echo API server running at: http://localhost:8000
echo Web interface running at: http://localhost:7861
echo.
echo Please visit http://localhost:7861 in your browser to use the system
echo.

endlocal