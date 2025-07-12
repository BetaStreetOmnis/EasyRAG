#!/bin/bash

# EasyRAG Docker 环境设置脚本
# 此脚本用于创建必要的数据目录并设置权限

echo "==================================================="
echo "       EasyRAG Docker 环境设置脚本"
echo "==================================================="

# 创建数据目录
echo "📁 创建数据目录..."
sudo mkdir -p /data/easyrag/db
sudo mkdir -p /data/easyrag/logs
sudo mkdir -p /data/easyrag/models
sudo mkdir -p /data/easyrag/files
sudo mkdir -p /data/easyrag/temp

# 设置目录权限
echo "🔧 设置目录权限..."
sudo chmod -R 755 /data/easyrag
sudo chown -R $USER:$USER /data/easyrag

echo "✅ 数据目录创建完成:"
echo "   - 数据库目录: /data/easyrag/db"
echo "   - 日志目录: /data/easyrag/logs"
echo "   - 模型目录: /data/easyrag/models"
echo "   - 文件目录: /data/easyrag/files"
echo "   - 临时目录: /data/easyrag/temp"

echo ""
echo "🚀 现在可以运行以下命令启动服务:"
echo "   docker-compose up -d"
echo ""
echo "🌐 服务启动后访问: http://localhost:8028"
echo "===================================================" 