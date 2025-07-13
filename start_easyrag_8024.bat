@echo off
chcp 65001 > nul

echo ===================================================
echo        EasyRAG 知识库系统启动脚本 (8024端口)
echo ===================================================
echo.

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python 未安装，请先安装 Python
    pause
    exit /b 1
)

:: 检查虚拟环境
if not exist "py_env\Scripts\activate.bat" (
    echo ❌ 虚拟环境不存在，请先运行 deploy.bat 进行部署
    pause
    exit /b 1
)

:: 检查app.py是否存在
if not exist "app.py" (
    echo ❌ app.py 文件不存在，请确保在正确的目录中
    pause
    exit /b 1
)

:: 激活虚拟环境
echo 🔌 激活虚拟环境...
call py_env\Scripts\activate.bat

:: 创建必要的目录
echo 📁 创建必要的目录...
if not exist "db" mkdir db
if not exist "logs" mkdir logs
if not exist "models_file" mkdir models_file
if not exist "files" mkdir files
if not exist "temp_files" mkdir temp_files

:: 检查端口8024是否被占用
netstat -an | findstr ":8024" >nul 2>&1
if %errorlevel% equ 0 (
    echo ⚠️  端口8024已被占用，正在尝试停止现有服务...
    taskkill /f /im python.exe >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: 启动服务
echo 🚀 启动 EasyRAG 服务...
echo.
echo 🌐 访问地址: http://localhost:8024
echo 📖 API文档: http://localhost:8024/docs
echo 📋 知识库列表: http://localhost:8024/kb/list
echo.
echo ⚠️  按 Ctrl+C 停止服务
echo.

:: 启动应用，指定端口为8024
python app.py --port 8024

pause 