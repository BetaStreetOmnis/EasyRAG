#!/bin/bash

echo "启动知识库管理系统..."

# 检查是否存在.env文件
if [ -f .env ]; then
    echo "从.env文件加载环境变量..."
    export $(grep -v '^#' .env | xargs)
else
    echo ".env文件不存在，使用默认配置..."
fi

# 启动API服务器
python api_server.py 