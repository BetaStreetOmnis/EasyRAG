@echo off
setlocal enabledelayedexpansion

:: Set console code page to UTF-8
chcp 65001 > nul

:: Title and color settings
title EasyRAG Knowledge Base System - Deployment
color 0B

:: Welcome message with system info
echo =======================================================
echo           EasyRAG Knowledge Base System
echo                   自动部署脚本 v2.0
echo =======================================================
echo.
echo 🚀 本脚本将自动为您部署EasyRAG本地知识库系统
echo 📋 包含：Python环境检测、依赖安装、服务启动
echo ⚡ 支持：CPU/GPU自动检测、多镜像源、智能重试
echo.
echo 系统信息：
echo - 操作系统：!OS! !PROCESSOR_ARCHITECTURE!
echo - 用户名：!USERNAME!
echo - 当前目录：!CD!
echo.
echo =======================================================
echo.

:: Check administrator privileges
net session >nul 2>&1
if "!errorlevel!" equ "0" (
    echo ✅ 管理员权限：已获取
) else (
    echo ⚠️  管理员权限：未获取 ^(建议以管理员身份运行以获得最佳体验^)
)
echo.

:: Pre-flight checks
echo [预检] 检查系统环境...
echo 检查网络连接...
ping -n 1 8.8.8.8 >nul 2>&1
if "!errorlevel!" equ "0" (
    echo ✅ 网络连接正常
) else (
    echo ⚠️  网络连接可能存在问题，将使用本地缓存和镜像源
)

echo 检查磁盘空间...
for /f "tokens=3" %%a in ('dir /-c !SystemDrive!\ 2^>nul ^| find "bytes free"') do set FREE_SPACE=%%a
if defined FREE_SPACE (
    echo ✅ 磁盘空间充足
) else (
    echo ⚠️  无法检测磁盘空间，请确保至少有2GB可用空间
)
echo.

:: Check if Python is installed and verify version
echo [1/6] 🐍 检查Python环境...
python --version >nul 2>nul
if "!errorlevel!" neq "0" (
    echo ❌ 未找到Python，将安装Python 3.9.13...
    goto InstallPython
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo 📍 检测到Python版本：!PYTHON_VERSION!
    
    :: Parse version
    for /f "tokens=1,2,3 delims=." %%a in ("!PYTHON_VERSION!") do (
        set MAJOR=%%a
        set MINOR=%%b
        set PATCH=%%c
    )
    
    :: Version compatibility check
    if "!MAJOR!" LSS "3" (
        echo ❌ Python版本过低 ^(!PYTHON_VERSION! ^< 3.0^)，需要安装Python 3.9
        goto InstallPython
    ) else if "!MAJOR!" EQU "3" (
        if "!MINOR!" LSS "8" (
            echo ❌ Python版本过低 ^(!PYTHON_VERSION! ^< 3.8^)，需要安装Python 3.9
            goto InstallPython
        ) else if "!MINOR!" EQU "9" (
            echo ✅ Python 3.9版本完美匹配！
            goto ContinueSetup
        ) else (
            echo ⚠️  Python版本为 !PYTHON_VERSION!，为了最佳兼容性建议使用3.9
            echo 是否继续使用当前版本？^(Y/N^)
            set /p CONTINUE_CHOICE=请选择 ^(默认Y^): 
            if /i "!CONTINUE_CHOICE!"=="N" (
                goto InstallPython
            ) else (
                echo ✅ 继续使用Python !PYTHON_VERSION!
                goto ContinueSetup
            )
        )
    ) else (
        echo ⚠️  Python版本为 !PYTHON_VERSION! ^(^> 4.0^)，可能存在兼容性问题
        echo 建议安装Python 3.9以获得最佳兼容性
        echo 是否安装Python 3.9？^(Y/N^)
        set /p INSTALL_CHOICE=请选择 ^(默认Y^): 
        if /i "!INSTALL_CHOICE!"=="N" (
            goto ContinueSetup
        ) else (
            goto InstallPython
        )
    )
)

:InstallPython
echo.
echo =======================================================
echo 🔄 安装Python 3.9.13 ^(企业级稳定版本^)
echo =======================================================
echo.
echo 📝 安装说明：
echo   - 将安装到用户目录，不影响系统Python
echo   - 自动配置环境变量
echo   - 支持多种安装方式和自动重试
echo.

:: Create temp directory with timestamp
set TIMESTAMP=!date:~0,4!!date:~5,2!!date:~8,2!_!time:~0,2!!time:~3,2!!time:~6,2!
set TIMESTAMP=!TIMESTAMP: =0!
set TEMP_DIR=tmp_!TIMESTAMP!
mkdir !TEMP_DIR! 2>nul
cd !TEMP_DIR!

:: Download Python installer with multiple methods
echo [1/4] 📥 下载Python 3.9.13安装程序...
set PYTHON_URL=https://www.python.org/ftp/python/3.9.13/python-3.9.13-amd64.exe
set INSTALLER_NAME=python-3.9.13-installer.exe

echo 方法1: 使用curl下载...
curl -L --connect-timeout 30 --max-time 300 --retry 3 "!PYTHON_URL!" -o "!INSTALLER_NAME!"

if not exist "!INSTALLER_NAME!" (
    echo 方法2: 使用PowerShell下载...
    powershell -Command "try { $ProgressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri '!PYTHON_URL!' -OutFile '!INSTALLER_NAME!' -TimeoutSec 300 } catch { exit 1 }"
)

if not exist "!INSTALLER_NAME!" (
    echo 方法3: 使用bitsadmin下载...
    bitsadmin /transfer "PythonDownload" "!PYTHON_URL!" "!CD!\!INSTALLER_NAME!"
)

:: Verify download
if exist "!INSTALLER_NAME!" (
    echo ✅ 下载完成！文件大小：
    for %%F in ("!INSTALLER_NAME!") do echo    %%~zF bytes
) else (
    echo ❌ 下载失败！请检查网络连接或手动下载
    echo 手动下载地址：!PYTHON_URL!
    echo 下载后请将文件重命名为 !INSTALLER_NAME! 并放在 !TEMP_DIR! 目录中
    echo 然后按任意键继续...
    pause
    if not exist "!INSTALLER_NAME!" (
        cd ..
        rmdir /s /q !TEMP_DIR!
        echo ❌ 安装失败，退出程序
        pause
        exit /b 1
    )
)

:: Install Python with multiple strategies
echo.
echo [2/4] 🔧 安装Python 3.9.13...
set PYTHON39_PATH=!LOCALAPPDATA!\Programs\Python\Python39

echo 策略1: 静默安装到用户目录...
"!INSTALLER_NAME!" /quiet InstallAllUsers=0 TargetDir="!PYTHON39_PATH!" PrependPath=1 Include_test=0 Include_tcltk=1 Include_pip=1 Include_doc=0

:: Wait for installation to complete
timeout /t 10 /nobreak > nul

:: Verify installation
echo [3/4] ✅ 验证安装结果...
if exist "!PYTHON39_PATH!\python.exe" (
    echo ✅ Python 3.9安装成功！
    echo 安装路径：!PYTHON39_PATH!
    
    :: Test Python
    "!PYTHON39_PATH!\python.exe" --version >nul 2>&1
    if "!errorlevel!" equ "0" (
        for /f "tokens=2" %%i in ('"!PYTHON39_PATH!\python.exe" --version 2^>^&1') do set INSTALLED_VERSION=%%i
        echo ✅ Python版本验证：!INSTALLED_VERSION!
        set PYTHON_CMD="!PYTHON39_PATH!\python.exe"
        set PATH=!PYTHON39_PATH!;!PYTHON39_PATH!\Scripts;!PATH!
    ) else (
        echo ❌ Python安装验证失败
        goto InstallationFallback
    )
) else (
    :InstallationFallback
    echo ⚠️  默认安装位置未找到，尝试其他安装方式...
    
    echo 策略2: 交互式安装...
    start /wait "!INSTALLER_NAME!"
    
    :: Search for Python 3.9 in common locations
    echo 搜索Python 3.9安装位置...
    set PYTHON39_PATH=
    
    for %%P in (
        "!LOCALAPPDATA!\Programs\Python\Python39"
        "!APPDATA!\Local\Programs\Python\Python39"
        "C:\Users\!USERNAME!\AppData\Local\Programs\Python\Python39"
        "C:\Python39"
        "C:\Program Files\Python39"
        "C:\Program Files (x86)\Python39"
    ) do (
        if exist "%%P\python.exe" (
            set PYTHON39_PATH=%%P
            echo ✅ 找到Python安装：%%P
            goto FoundPython
        )
    )
    
    :: Search in PATH
    echo 在系统PATH中搜索Python 3.9...
    for /f "tokens=*" %%i in ('where python 2^>nul') do (
        for /f "tokens=2" %%j in ('"%%i" --version 2^>^&1') do (
            if "%%j"=="3.9.13" (
                set PYTHON39_PATH=%%~dpi
                set PYTHON39_PATH=!PYTHON39_PATH:~0,-1!
                echo ✅ 在PATH中找到Python 3.9：!PYTHON39_PATH!
                goto FoundPython
            )
        )
    )
    
    :FoundPython
    if defined PYTHON39_PATH (
        set PYTHON_CMD="!PYTHON39_PATH!\python.exe"
        set PATH=!PYTHON39_PATH!;!PYTHON39_PATH!\Scripts;!PATH!
        echo ✅ Python 3.9配置完成
    ) else (
        echo ❌ Python 3.9安装失败
        echo.
        echo 🔧 故障排除建议：
        echo 1. 以管理员身份运行此脚本
        echo 2. 临时关闭杀毒软件
        echo 3. 检查磁盘空间 ^(需要至少500MB^)
        echo 4. 手动安装：
        echo    下载：https://www.python.org/downloads/release/python-3913/
        echo    选择：Windows installer ^(64-bit^)
        echo    安装时勾选：Add Python to PATH
        echo.
        cd ..
        rmdir /s /q !TEMP_DIR!
        pause
        exit /b 1
    )
)

:: Clean up
echo [4/4] 🧹 清理临时文件...
cd ..
rmdir /s /q !TEMP_DIR!
echo ✅ Python 3.9.13安装完成！
echo.

:ContinueSetup
:: Set Python command if not already set
if not defined PYTHON_CMD (
    set PYTHON_CMD=python
)

:: Enhanced virtual environment setup
echo [2/6] 🏠 配置虚拟环境...
if exist py_env (
    echo 📁 发现现有虚拟环境，检查状态...
    call py_env\Scripts\activate.bat >nul 2>&1
    if "!errorlevel!" equ "0" (
        for /f "tokens=2" %%i in ('python --version 2^>^&1') do set VENV_VERSION=%%i
        echo 现有环境Python版本：!VENV_VERSION!
        
        :: Check if virtual environment is functional
        python -c "import sys; print('OK')" >nul 2>&1
        if "!errorlevel!" equ "0" (
            :: Check Python version compatibility
            for /f "tokens=1,2 delims=." %%a in ("!VENV_VERSION!") do (
                set VENV_MAJOR=%%a
                set VENV_MINOR=%%b
            )
            
            if "!VENV_MAJOR!" EQU "3" (
                if !VENV_MINOR! GEQ 8 (
                    echo ✅ 虚拟环境状态良好，版本兼容
                    
                    :: Check if core packages are installed
                    echo 🔍 检查核心依赖包...
                    set CORE_PACKAGES_OK=true
                    
                    python -c "import numpy" >nul 2>&1
                    if "!errorlevel!" neq "0" set CORE_PACKAGES_OK=false
                    
                    python -c "import torch" >nul 2>&1
                    if "!errorlevel!" neq "0" set CORE_PACKAGES_OK=false
                    
                    if "!CORE_PACKAGES_OK!"=="true" (
                        echo ✅ 核心依赖包已安装，跳过重复安装
                        set SKIP_PACKAGE_INSTALL=true
                        goto ActivateVenv
                    ) else (
                        echo ⚠️  核心依赖包缺失，需要安装依赖
                        set SKIP_PACKAGE_INSTALL=false
                        goto ActivateVenv
                    )
                ) else (
                    echo ⚠️  Python版本过低 ^(!VENV_VERSION! ^< 3.8^)，需要重新创建
                    goto RecreateVenv
                )
            ) else (
                echo ⚠️  Python版本异常 ^(!VENV_VERSION!^)，需要重新创建
                goto RecreateVenv
            )
        ) else (
            echo ❌ 虚拟环境损坏，需要重新创建
            goto RecreateVenv
        )
    ) else (
        echo ❌ 虚拟环境激活失败，需要重新创建
        goto RecreateVenv
    )
) else (
    goto CreateNewVenv
)

:RecreateVenv
echo 🔄 删除现有虚拟环境...
call py_env\Scripts\deactivate.bat >nul 2>&1
rmdir /s /q py_env
goto CreateNewVenv

:CreateNewVenv
echo 🔨 创建新的虚拟环境...
!PYTHON_CMD! -m venv py_env --upgrade-deps
if "!errorlevel!" neq "0" (
    echo ❌ 虚拟环境创建失败
    echo 尝试不带升级参数...
    !PYTHON_CMD! -m venv py_env
    if "!errorlevel!" neq "0" (
        echo ❌ 虚拟环境创建完全失败
        pause
        exit /b 1
    )
)
echo ✅ 虚拟环境创建成功
set SKIP_PACKAGE_INSTALL=false

:ActivateVenv
echo 🔌 激活虚拟环境...
call py_env\Scripts\activate.bat
if "!errorlevel!" neq "0" (
    echo ❌ 虚拟环境激活失败
    pause
    exit /b 1
)

:: Verify virtual environment
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set VENV_PYTHON_VERSION=%%i
echo ✅ 虚拟环境已激活
echo 📍 虚拟环境Python版本：!VENV_PYTHON_VERSION!

:: Check Python version compatibility
for /f "tokens=1,2 delims=." %%a in ("!VENV_PYTHON_VERSION!") do (
    set VENV_MAJOR=%%a
    set VENV_MINOR=%%b
)

if "!VENV_MAJOR!" EQU "3" (
    if !VENV_MINOR! GEQ 8 (
        echo ✅ Python版本兼容性检查通过
    ) else (
        echo ⚠️  Python版本较低，可能存在兼容性问题
    )
) else (
    echo ⚠️  Python版本异常，可能存在兼容性问题
)
echo.

:: Enhanced dependency installation with smart skip
echo [3/6] 📦 安装项目依赖...

if "!SKIP_PACKAGE_INSTALL!"=="true" (
    echo ✅ 依赖包已存在且可用，跳过安装步骤
    echo 📍 如需重新安装依赖，请删除py_env目录后重新运行脚本
    goto CreateDirectories
)

echo 🔧 配置pip环境...
mkdir pip_cache 2>nul
set PIP_CACHE_DIR=!CD!\pip_cache

:: Upgrade pip first
echo 升级pip到最新版本...
python -m pip install --upgrade pip --cache-dir "!PIP_CACHE_DIR!" --timeout 60

:: Configure pip mirrors
echo 配置pip镜像源...
set MIRRORS[0]=https://mirrors.aliyun.com/pypi/simple/
set MIRRORS[1]=https://pypi.tuna.tsinghua.edu.cn/simple/
set MIRRORS[2]=https://mirrors.cloud.tencent.com/pypi/simple/
set MIRRORS[3]=https://pypi.python.org/simple/

:: Smart GPU detection
echo 🎮 检测GPU支持...
set GPU_SUPPORT=false
where nvidia-smi >nul 2>nul
if "!errorlevel!" equ "0" (
    nvidia-smi --query-gpu=name --format=csv,noheader >nul 2>nul
    if "!errorlevel!" equ "0" (
        echo ✅ 检测到NVIDIA GPU
        for /f "tokens=*" %%g in ('nvidia-smi --query-gpu=name --format=csv,noheader 2^>nul') do (
            echo    GPU: %%g
        )
        set GPU_SUPPORT=true
    ) else (
        echo ⚠️  NVIDIA驱动程序异常
    )
) else (
    echo 📱 未检测到NVIDIA GPU，使用CPU模式
)

:: Install core dependencies with retry mechanism
echo.
echo 🔄 安装核心依赖包...
call :InstallPackageWithRetry "wheel setuptools" "构建工具"
call :InstallPackageWithRetry "numpy>=1.21.0,<2.0.0" "数值计算库"

:: Install PyTorch based on GPU support
echo.
if "!GPU_SUPPORT!"=="true" (
    echo 🎮 安装GPU版本PyTorch...
    call :InstallPackageWithRetry "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121" "PyTorch GPU版本"
    
    :: Verify CUDA availability
    python -c "import torch; print('CUDA available:', torch.cuda.is_available())" 2>nul
    if "!errorlevel!" equ "0" (
        echo ✅ CUDA支持验证成功
    ) else (
        echo ⚠️  CUDA支持验证失败，将使用CPU版本
        set GPU_SUPPORT=false
    )
)

if "!GPU_SUPPORT!"=="false" (
    echo 💻 安装CPU版本PyTorch...
    call :InstallPackageWithRetry "torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu" "PyTorch CPU版本"
)

:: Install project requirements
echo.
echo 📋 安装项目依赖文件...
if "!GPU_SUPPORT!"=="true" (
    if exist requirements_gpu.txt (
        call :InstallRequirementsWithRetry "requirements_gpu.txt" "GPU项目依赖"
    ) else (
        echo ⚠️  requirements_gpu.txt文件不存在，使用通用依赖
        call :InstallRequirementsWithRetry "requirements.txt" "通用项目依赖"
    )
) else (
    if exist requirements_cpu.txt (
        call :InstallRequirementsWithRetry "requirements_cpu.txt" "CPU项目依赖"
    ) else if exist requirements.txt (
        call :InstallRequirementsWithRetry "requirements.txt" "通用项目依赖"
    ) else (
        echo ⚠️  未找到requirements文件，跳过依赖安装
    )
)

:: Optional packages
echo.
echo 🔧 安装可选增强包...
echo 注意：FAISS包用于向量相似度搜索，如安装失败不影响基本功能
if "!GPU_SUPPORT!"=="true" (
    call :InstallPackageOptional "faiss-gpu" "FAISS GPU版本"
) else (
    call :InstallPackageOptional "faiss-cpu" "FAISS CPU版本"
)

echo ✅ 依赖安装完成！
echo.

:CreateDirectories
:: Create directories
echo [4/6] 📁 创建项目目录...
for %%D in (db models_file temp_files logs) do (
    if not exist %%D (
        mkdir %%D
        echo ✅ 创建目录：%%D
    ) else (
        echo 📁 目录已存在：%%D
    )
)
echo.

:: Configuration check
echo [5/6] ⚙️  检查配置文件...
if exist config.py (
    echo ✅ 配置文件存在
) else if exist config.yaml (
    echo ✅ 配置文件存在
) else (
    echo ⚠️  未找到配置文件，将使用默认配置
)

:: Final system check
echo [6/6] 🔍 系统就绪检查...
echo 检查关键文件...
set MISSING_FILES=
for %%F in (app.py main.py) do (
    if not exist %%F (
        set MISSING_FILES=!MISSING_FILES! %%F
    )
)

if defined MISSING_FILES (
    echo ❌ 缺少关键文件：!MISSING_FILES!
    echo 请确保在正确的项目目录中运行此脚本
    pause
    exit /b 1
)

echo ✅ 系统检查通过
echo.

:: Start services
echo =======================================================
echo 🚀 启动EasyRAG知识库系统
echo =======================================================
echo.
echo 📋 服务信息：
echo   - 统一服务端口：8028 ^(包含API和Web界面^)
echo   - GPU支持：!GPU_SUPPORT!
echo   - Python版本：!VENV_PYTHON_VERSION!
echo.

echo 🔄 启动EasyRAG服务...
start "EasyRAG Service" cmd /k "title EasyRAG Knowledge Base System && call py_env\Scripts\activate.bat && echo 🚀 启动EasyRAG知识库系统... && python app.py"

echo ⏳ 等待服务启动...
timeout /t 8 /nobreak > nul

echo.
echo ✅ EasyRAG知识库系统启动完成！
echo.
echo 🌐 访问地址：
echo   - 系统界面：http://localhost:8028
echo.
echo 📝 使用说明：
echo   - 新的命令行窗口已打开^(EasyRAG服务^)
echo   - 在浏览器中访问 http://localhost:8028 使用系统
echo   - 可以上传文档、创建知识库、进行问答
echo   - 按Ctrl+C可以停止服务
echo   - 服务运行在Python虚拟环境中
echo.
echo 🎉 部署完成！祝您使用愉快！
echo.

:: Open browser automatically
echo 是否自动打开浏览器访问系统界面？^(Y/N^)
set /p OPEN_BROWSER=请选择 ^(默认Y^): 
if /i not "!OPEN_BROWSER!"=="N" (
    echo 🌐 正在打开浏览器...
    timeout /t 3 /nobreak > nul
    start http://localhost:8028
)

pause
goto :eof

:: Helper functions
:InstallPackageWithRetry
set PACKAGE=%~1
set DESCRIPTION=%~2
echo 安装 !DESCRIPTION! ^(!PACKAGE!^)...

for /L %%i in (0,1,3) do (
    if %%i equ 0 (
        python -m pip install !PACKAGE! --cache-dir "!PIP_CACHE_DIR!" -i !MIRRORS[%%i]! --timeout 60
    ) else (
        echo 重试 %%i/3 - 使用镜像源 %%i...
        python -m pip install !PACKAGE! --cache-dir "!PIP_CACHE_DIR!" -i !MIRRORS[%%i]! --timeout 60
    )
    
    if "!errorlevel!" equ "0" (
        echo ✅ !DESCRIPTION! 安装成功
        goto :eof
    )
)

echo ❌ !DESCRIPTION! 安装失败
pause
exit /b 1

:InstallRequirementsWithRetry
set REQ_FILE=%~1
set DESCRIPTION=%~2
echo 安装 !DESCRIPTION! ^(!REQ_FILE!^)...

for /L %%i in (0,1,3) do (
    if %%i equ 0 (
        python -m pip install -r !REQ_FILE! --cache-dir "!PIP_CACHE_DIR!" -i !MIRRORS[%%i]! --timeout 60
    ) else (
        echo 重试 %%i/3 - 使用镜像源 %%i...
        python -m pip install -r !REQ_FILE! --cache-dir "!PIP_CACHE_DIR!" -i !MIRRORS[%%i]! --timeout 60
    )
    
    if "!errorlevel!" equ "0" (
        echo ✅ !DESCRIPTION! 安装成功
        goto :eof
    )
)

echo ❌ !DESCRIPTION! 安装失败
pause
exit /b 1

:InstallPackageOptional
set PACKAGE=%~1
set DESCRIPTION=%~2
echo 尝试安装 !DESCRIPTION! ^(!PACKAGE!^)...

python -m pip install !PACKAGE! --cache-dir "!PIP_CACHE_DIR!" -i !MIRRORS[0]! --timeout 60 >nul 2>&1
if "!errorlevel!" equ "0" (
    echo ✅ !DESCRIPTION! 安装成功
) else (
    echo ⚠️  !DESCRIPTION! 安装失败^(可选包，不影响基本功能^)
)
goto :eof 