@echo off
setlocal enabledelayedexpansion

:: 设置控制台代码页为UTF-8
chcp 65001 > nul

:: 标题和颜色设置
title EasyRAG Docker部署脚本
color 0A

:: 欢迎信息
echo =======================================================
echo           EasyRAG Docker部署脚本
echo =======================================================
echo.
echo 本脚本将帮助您使用Docker部署EasyRAG知识库系统
echo 支持CPU和GPU版本的自动部署
echo.
echo =======================================================
echo.

:: 检查Docker是否安装
echo [1/5] 检查Docker环境...
docker --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker未安装，请先安装Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('docker --version') do set DOCKER_VERSION=%%i
    echo ✅ Docker已安装: !DOCKER_VERSION!
)

:: 检查Docker Compose
docker-compose --version >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Docker Compose未安装，请先安装Docker Compose
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('docker-compose --version') do set COMPOSE_VERSION=%%i
    echo ✅ Docker Compose已安装: !COMPOSE_VERSION!
)

:: 检查GPU支持
echo [2/5] 检查GPU支持...
set USE_GPU=false
where nvidia-smi >nul 2>nul
if %errorlevel% equ 0 (
    nvidia-smi >nul 2>nul
    if !errorlevel! equ 0 (
        echo ✅ 检测到NVIDIA GPU，可以使用GPU版本
        set USE_GPU=true
    ) else (
        echo ⚠️  检测到nvidia-smi但GPU不可用，将使用CPU版本
    )
) else (
    echo ℹ️  未检测到NVIDIA GPU，将使用CPU版本
)

:: 处理命令行参数
if "%1"=="--gpu" (
    set USE_GPU=true
    echo 🔧 强制使用GPU版本
) else if "%1"=="--cpu" (
    set USE_GPU=false
    echo 🔧 强制使用CPU版本
) else if "%1"=="--stop" (
    echo 停止EasyRAG服务...
    docker-compose down
    echo ✅ 服务已停止
    pause
    exit /b 0
) else if "%1"=="--restart" (
    echo 重启EasyRAG服务...
    docker-compose restart
    echo ✅ 服务已重启
    pause
    exit /b 0
) else if "%1"=="--logs" (
    echo 查看服务日志...
    docker-compose logs -f
    exit /b 0
) else if "%1"=="--status" (
    echo 查看服务状态...
    docker-compose ps
    pause
    exit /b 0
) else if "%1"=="--help" (
    goto ShowHelp
)

:: 创建必要的目录
echo [3/5] 创建必要的目录...
mkdir db 2>nul
mkdir models_file 2>nul
mkdir temp_files 2>nul
mkdir files 2>nul
echo ✅ 目录创建完成

:: 设置环境配置
echo [4/5] 设置环境配置...
if not exist .env (
    if exist .env.example (
        echo 复制环境配置文件...
        copy .env.example .env >nul
        echo ✅ 环境配置文件已创建，请根据需要修改 .env 文件
    ) else (
        echo 创建默认环境配置文件...
        (
            echo # API服务器配置
            echo API_HOST=0.0.0.0
            echo API_PORT=8028
            echo.
            echo # 前端API基础URL配置
            echo API_BASE_URL=http://localhost:8028
            echo.
            echo # GPU支持（true/false）
            echo USE_GPU=false
        ) > .env
        echo ✅ 默认环境配置文件已创建
    )
) else (
    echo ℹ️  环境配置文件已存在
)

:: 部署服务
echo [5/5] 部署EasyRAG服务...
echo.
if "%USE_GPU%"=="true" (
    echo 🚀 使用GPU版本部署...
    set COMPOSE_FILE=docker-compose.gpu.yml
) else (
    echo 🚀 使用CPU版本部署...
    set COMPOSE_FILE=docker-compose.yml
)

:: 设置环境变量
set USE_GPU=%USE_GPU%

:: 构建和启动服务
echo 构建Docker镜像...
docker-compose -f %COMPOSE_FILE% build --no-cache
if %errorlevel% neq 0 (
    echo ❌ Docker镜像构建失败
    pause
    exit /b 1
)

echo 启动服务...
docker-compose -f %COMPOSE_FILE% up -d
if %errorlevel% neq 0 (
    echo ❌ 服务启动失败
    pause
    exit /b 1
)

:: 等待服务启动
echo 等待服务启动...
timeout /t 10 /nobreak > nul

:: 检查服务状态
docker-compose -f %COMPOSE_FILE% ps | findstr "Up" >nul
if %errorlevel% equ 0 (
    echo.
    echo ✅ EasyRAG服务部署成功！
    echo.
    echo 服务访问地址：
    echo   📱 Web界面: http://localhost:7861
    echo   🔗 API服务: http://localhost:8028
    echo.
    echo 常用命令：
    echo   查看服务状态: docker-compose ps
    echo   查看日志: docker-compose logs -f
    echo   停止服务: docker-compose down
    echo   重启服务: docker-compose restart
    echo.
    echo 请在浏览器中访问 http://localhost:7861 使用系统
) else (
    echo ❌ 服务启动失败，请检查日志
    docker-compose -f %COMPOSE_FILE% logs
    pause
    exit /b 1
)

pause
exit /b 0

:ShowHelp
echo EasyRAG Docker部署脚本
echo.
echo 用法: %0 [选项]
echo.
echo 选项:
echo   --help     显示帮助信息
echo   --gpu      使用GPU版本部署
echo   --cpu      使用CPU版本部署
echo   --stop     停止服务
echo   --restart  重启服务
echo   --logs     查看日志
echo   --status   查看服务状态
echo.
echo 示例:
echo   %0              # 自动检测GPU并部署
echo   %0 --gpu        # 强制使用GPU版本
echo   %0 --cpu        # 强制使用CPU版本
echo   %0 --stop       # 停止服务
echo.
pause
exit /b 0 