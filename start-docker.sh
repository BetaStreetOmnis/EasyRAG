#!/bin/bash

# EasyRAG Docker 一键启动脚本

echo "==================================================="
echo "       EasyRAG Docker 一键启动脚本"
echo "==================================================="
echo

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查Docker Compose是否可用
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装"
    exit 1
fi

echo "✅ Docker 环境检查通过"

# 设置环境变量
export DATA_PATH="/data"
echo "🔧 设置数据路径: $DATA_PATH"

# 创建数据目录
echo "📁 检查并创建数据目录..."
if [ ! -d "$DATA_PATH/easyrag" ]; then
    sudo mkdir -p $DATA_PATH/easyrag/{db,logs,models,files,temp}
    sudo chown -R $USER:$USER $DATA_PATH/easyrag
    sudo chmod -R 755 $DATA_PATH/easyrag
    echo "✅ 数据目录创建完成"
else
    echo "✅ 数据目录已存在"
fi

# 检查是否已有运行的容器
echo "🔍 检查现有容器状态..."
if docker-compose ps | grep -q "easyrag_app"; then
    echo "⚠️  发现已运行的容器，正在重启..."
    docker-compose restart
else
    echo "🚀 启动 EasyRAG 服务..."
    docker-compose up -d
fi

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 15

# 检查服务状态
echo "📊 检查服务状态..."
docker-compose ps

echo
echo "==================================================="
echo "🎉 EasyRAG 服务启动完成！"
echo
echo "🌐 访问地址："
echo "   主页面：http://localhost:8028"
echo "   API文档：http://localhost:8028/docs"
echo
echo "📁 数据目录："
echo "   $DATA_PATH/easyrag/db       - 数据库文件"
echo "   $DATA_PATH/easyrag/logs     - 日志文件"
echo "   $DATA_PATH/easyrag/models   - 模型文件"
echo "   $DATA_PATH/easyrag/files    - 上传文件"
echo "   $DATA_PATH/easyrag/temp     - 临时文件"
echo
echo "🔧 管理命令："
echo "   查看日志：docker-compose logs -f easyrag"
echo "   停止服务：docker-compose down"
echo "   重启服务：docker-compose restart"
echo "==================================================="

# 询问是否打开浏览器
echo
read -p "是否打开浏览器访问服务？(Y/N，默认Y): " OPEN_BROWSER
if [[ ! "$OPEN_BROWSER" =~ ^[Nn]$ ]]; then
    echo "🌐 正在打开浏览器..."
    if command -v xdg-open &> /dev/null; then
        xdg-open http://localhost:8028
    elif command -v open &> /dev/null; then
        open http://localhost:8028
    else
        echo "无法自动打开浏览器，请手动访问 http://localhost:8028"
    fi
fi 