@echo off
setlocal enabledelayedexpansion

:: Set console code page to UTF-8
chcp 65001 > nul

echo =======================================================
echo           EasyRAG Knowledge Base System
echo                   快速启动脚本 v1.0
echo =======================================================
echo.
echo 🚀 启动知识库管理系统...

:: Check if virtual environment exists
if exist py_env (
    echo 🔌 激活虚拟环境...
    call py_env\Scripts\activate.bat
    if "!errorlevel!" neq "0" (
        echo ❌ 虚拟环境激活失败，请先运行 deploy.bat 部署系统
        pause
        exit /b 1
    )
    echo ✅ 虚拟环境已激活
) else (
    echo ⚠️  未找到虚拟环境，请先运行 deploy.bat 部署系统
    echo.
    echo 是否现在运行部署脚本？^(Y/N^)
    set /p RUN_DEPLOY=请选择 ^(默认Y^): 
    if /i not "!RUN_DEPLOY!"=="N" (
        echo 🔄 正在启动部署脚本...
        call deploy.bat
        exit /b 0
    ) else (
        echo ❌ 无法启动服务，需要先部署环境
        pause
        exit /b 1
    )
)

:: Check if main application file exists
if not exist app.py (
    echo ❌ 未找到 app.py 文件，请确保在正确的项目目录中运行
    pause
    exit /b 1
)

:: Load environment variables from .env file
echo 🔧 加载配置...
if exist .env (
    echo 📋 从.env文件加载环境变量...
    for /F "usebackq tokens=1,2 delims==" %%i in (.env) do (
        if not "%%i"=="" if not "%%j"=="" (
            set %%i=%%j
        )
    )
    echo ✅ 环境变量加载完成
) else (
    echo ⚠️  .env文件不存在，使用默认配置...
)

:: Start the application
echo.
echo 🚀 启动EasyRAG知识库系统...
echo 📍 服务将在 http://localhost:8028 启动
echo 💡 按 Ctrl+C 可以停止服务
echo.

:: Start the API server
python app.py

:: Handle exit
echo.
if "!errorlevel!" equ "0" (
    echo ✅ 服务正常退出
) else (
    echo ❌ 服务异常退出，错误代码：!errorlevel!
    echo.
    echo 🔧 故障排除建议：
    echo 1. 检查端口8028是否被占用
    echo 2. 确认所有依赖包已正确安装
    echo 3. 查看上方的错误信息
    echo 4. 如需重新部署，请运行 deploy.bat
)

echo.
echo 按任意键退出...
pause > nul 