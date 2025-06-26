@echo off
echo 启动知识库管理系统...

REM 检查是否存在.env文件
if exist .env (
    echo 从.env文件加载环境变量...
    for /F "tokens=*" %%i in (.env) do (
        set %%i
    )
) else (
    echo .env文件不存在，使用默认配置...
)

REM 启动API服务器
python app.py

pause 