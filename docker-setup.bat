@echo off
setlocal enabledelayedexpansion

:: 设置控制台编码为UTF-8
chcp 65001 > nul

echo ===================================================
echo        EasyRAG Docker 环境设置脚本
echo ===================================================
echo.

:: 创建数据目录
echo 📁 创建数据目录...
if not exist "D:\data\easyrag" (
    mkdir "D:\data\easyrag"
)
if not exist "D:\data\easyrag\db" (
    mkdir "D:\data\easyrag\db"
)
if not exist "D:\data\easyrag\logs" (
    mkdir "D:\data\easyrag\logs"
)
if not exist "D:\data\easyrag\models" (
    mkdir "D:\data\easyrag\models"
)
if not exist "D:\data\easyrag\files" (
    mkdir "D:\data\easyrag\files"
)
if not exist "D:\data\easyrag\temp" (
    mkdir "D:\data\easyrag\temp"
)

echo ✅ 数据目录创建完成:
echo    - 数据库目录: D:\data\easyrag\db
echo    - 日志目录: D:\data\easyrag\logs
echo    - 模型目录: D:\data\easyrag\models
echo    - 文件目录: D:\data\easyrag\files
echo    - 临时目录: D:\data\easyrag\temp
echo.

echo 🚀 现在可以运行以下命令启动服务:
echo    docker-compose up -d
echo.
echo 🌐 服务启动后访问: http://localhost:8028
echo ===================================================
pause 