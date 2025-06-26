@echo off
setlocal enabledelayedexpansion

:: Set console code page to UTF-8
chcp 65001 > nul

echo =======================================================
echo           NumPy 安装诊断工具
echo =======================================================
echo.

:: 检查Python环境
echo [1/5] 检查Python环境...
python --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Python未安装或不在PATH中
    echo 请先安装Python 3.9+
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo ✅ Python版本: !PYTHON_VERSION!
)

:: 检查pip
echo.
echo [2/5] 检查pip...
python -m pip --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ pip不可用
    pause
    exit /b 1
) else (
    for /f "tokens=2" %%i in ('python -m pip --version 2^>^&1') do set PIP_VERSION=%%i
    echo ✅ pip版本: !PIP_VERSION!
)

:: 检查虚拟环境
echo.
echo [3/5] 检查虚拟环境...
if exist py_env (
    echo ✅ 虚拟环境存在
    call py_env\Scripts\activate.bat
    if %errorlevel% neq 0 (
        echo ❌ 虚拟环境激活失败
        pause
        exit /b 1
    ) else (
        echo ✅ 虚拟环境激活成功
    )
) else (
    echo ⚠️  虚拟环境不存在，创建中...
    python -m venv py_env
    if %errorlevel% neq 0 (
        echo ❌ 虚拟环境创建失败
        pause
        exit /b 1
    )
    call py_env\Scripts\activate.bat
    echo ✅ 虚拟环境创建并激活成功
)

:: 检查网络连接
echo.
echo [4/5] 检查网络连接...
ping -n 1 mirrors.aliyun.com >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ 阿里云镜像源连接正常
    set MIRROR_ALIYUN=1
) else (
    echo ❌ 阿里云镜像源连接失败
    set MIRROR_ALIYUN=0
)

ping -n 1 pypi.tuna.tsinghua.edu.cn >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ 清华镜像源连接正常
    set MIRROR_TSINGHUA=1
) else (
    echo ❌ 清华镜像源连接失败
    set MIRROR_TSINGHUA=0
)

ping -n 1 pypi.org >nul 2>nul
if %errorlevel% equ 0 (
    echo ✅ 官方PyPI连接正常
    set MIRROR_OFFICIAL=1
) else (
    echo ❌ 官方PyPI连接失败
    set MIRROR_OFFICIAL=0
)

:: 尝试安装numpy
echo.
echo [5/5] 尝试安装NumPy...
mkdir pip_cache 2>nul
set PIP_CACHE_DIR=%CD%\pip_cache

echo 升级pip、setuptools、wheel...
python -m pip install --upgrade pip setuptools wheel --cache-dir %PIP_CACHE_DIR% --quiet

echo.
echo 开始NumPy安装测试...

if %MIRROR_ALIYUN% equ 1 (
    echo 尝试阿里云镜像源...
    python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR% -i https://mirrors.aliyun.com/pypi/simple/ --quiet
    if !errorlevel! equ 0 (
        echo ✅ 阿里云镜像源安装成功！
        goto VerifyInstall
    ) else (
        echo ❌ 阿里云镜像源安装失败
    )
)

if %MIRROR_TSINGHUA% equ 1 (
    echo 尝试清华镜像源...
    python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR% -i https://pypi.tuna.tsinghua.edu.cn/simple/ --quiet
    if !errorlevel! equ 0 (
        echo ✅ 清华镜像源安装成功！
        goto VerifyInstall
    ) else (
        echo ❌ 清华镜像源安装失败
    )
)

if %MIRROR_OFFICIAL% equ 1 (
    echo 尝试官方PyPI...
    python -m pip install numpy==1.24.4 --cache-dir %PIP_CACHE_DIR% --quiet
    if !errorlevel! equ 0 (
        echo ✅ 官方PyPI安装成功！
        goto VerifyInstall
    ) else (
        echo ❌ 官方PyPI安装失败
    )
)

echo 尝试安装最新版本...
python -m pip install numpy --cache-dir %PIP_CACHE_DIR% --quiet
if !errorlevel! equ 0 (
    echo ✅ 最新版本安装成功！
    goto VerifyInstall
) else (
    echo ❌ 所有安装方式都失败了
    goto InstallFailed
)

:VerifyInstall
echo.
echo 验证NumPy安装...
python -c "import numpy; print(f'NumPy {numpy.__version__} 安装成功！')"
if %errorlevel% equ 0 (
    echo.
    echo =======================================================
    echo ✅ NumPy安装验证成功！
    echo =======================================================
    echo 现在可以运行 deploy.bat 继续安装其他依赖
) else (
    echo ❌ NumPy导入失败
    goto InstallFailed
)
goto End

:InstallFailed
echo.
echo =======================================================
echo ❌ NumPy安装失败诊断
echo =======================================================
echo.
echo 可能的解决方案：
echo 1. 检查网络连接是否稳定
echo 2. 尝试使用管理员权限运行
echo 3. 检查是否有防火墙阻止pip下载
echo 4. 手动安装：pip install numpy
echo 5. 如果是Windows，可能需要安装Visual C++ Build Tools
echo.
echo 详细错误信息请查看上面的输出
echo.

:End
pause 