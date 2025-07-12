@echo off
setlocal enabledelayedexpansion

:: 设置控制台编码为UTF-8
chcp 65001 > nul

echo ===================================================
echo        EasyRAG Docker 一键启动脚本
echo ===================================================
echo.

:: 检查Docker是否安装
docker --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Docker 未安装或未启动，请先安装 Docker Desktop
    pause
    exit /b 1
)

:: 检查Docker Compose是否可用
docker-compose --version >nul 2>&1
if !errorlevel! neq 0 (
    echo ❌ Docker Compose 未安装或未启动
    pause
    exit /b 1
)

echo ✅ Docker 环境检查通过

:: 设置环境变量
set DATA_PATH=D:/data
echo 🔧 设置数据路径: %DATA_PATH%

:: 创建数据目录
echo 📁 检查并创建数据目录...
if not exist "%DATA_PATH%\easyrag" (
    mkdir "%DATA_PATH%\easyrag"
    mkdir "%DATA_PATH%\easyrag\db"
    mkdir "%DATA_PATH%\easyrag\logs"
    mkdir "%DATA_PATH%\easyrag\models"
    mkdir "%DATA_PATH%\easyrag\files"
    mkdir "%DATA_PATH%\easyrag\temp"
    echo ✅ 数据目录创建完成
) else (
    echo ✅ 数据目录已存在
)

:: 检查是否已有运行的容器
echo 🔍 检查现有容器状态...
docker-compose ps | findstr "easyrag_app" >nul 2>&1
if !errorlevel! equ 0 (
    echo ⚠️  发现已运行的容器，正在重启...
    docker-compose restart
) else (
    echo 🚀 启动 EasyRAG 服务...
    docker-compose up -d
)

:: 等待服务启动
echo ⏳ 等待服务启动...
timeout /t 15 /nobreak >nul

:: 检查服务状态
echo 📊 检查服务状态...
docker-compose ps

echo.
echo ===================================================
echo 🎉 EasyRAG 服务启动完成！
echo.
echo 🌐 访问地址：
echo    主页面：http://localhost:8028
echo    API文档：http://localhost:8028/docs
echo.
echo 📁 数据目录：
echo    %DATA_PATH%\easyrag\db       - 数据库文件
echo    %DATA_PATH%\easyrag\logs     - 日志文件
echo    %DATA_PATH%\easyrag\models   - 模型文件
echo    %DATA_PATH%\easyrag\files    - 上传文件
echo    %DATA_PATH%\easyrag\temp     - 临时文件
echo.
echo 🔧 管理命令：
echo    查看日志：docker-compose logs -f easyrag
echo    停止服务：docker-compose down
echo    重启服务：docker-compose restart
echo ===================================================

:: 询问是否打开浏览器
echo.
set /p OPEN_BROWSER=是否打开浏览器访问服务？(Y/N，默认Y): 
if /i not "!OPEN_BROWSER!"=="N" (
    echo 🌐 正在打开浏览器...
    start http://localhost:8028
)

pause 