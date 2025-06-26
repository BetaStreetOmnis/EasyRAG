#!/bin/bash

# Set colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo "======================================================="
echo "          EasyRAG Knowledge Base System"
echo "                  快速启动脚本 v1.0"
echo "======================================================="
echo ""
echo "🚀 启动知识库管理系统..."

# Check if virtual environment exists
if [ -d "py_env" ]; then
    echo "🔌 激活虚拟环境..."
    source py_env/bin/activate
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 虚拟环境激活失败，请先运行 deploy.sh 部署系统${NC}"
        read -p "按任意键退出..."
        exit 1
    fi
    echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
else
    echo -e "${YELLOW}⚠️  未找到虚拟环境，请先运行 deploy.sh 部署系统${NC}"
    echo ""
    read -p "是否现在运行部署脚本？(Y/N) [默认Y]: " RUN_DEPLOY
    RUN_DEPLOY=${RUN_DEPLOY:-Y}
    if [[ ! "$RUN_DEPLOY" =~ ^[Nn]$ ]]; then
        echo "🔄 正在启动部署脚本..."
        if [ -f "deploy.sh" ]; then
            bash deploy.sh
        else
            echo -e "${RED}❌ 未找到 deploy.sh 文件${NC}"
            read -p "按任意键退出..."
            exit 1
        fi
        exit 0
    else
        echo -e "${RED}❌ 无法启动服务，需要先部署环境${NC}"
        read -p "按任意键退出..."
        exit 1
    fi
fi

# Check if main application file exists
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ 未找到 app.py 文件，请确保在正确的项目目录中运行${NC}"
    read -p "按任意键退出..."
    exit 1
fi

# Load environment variables from .env file
echo "🔧 加载配置..."
if [ -f .env ]; then
    echo "📋 从.env文件加载环境变量..."
    # Load .env file with proper parsing
    while IFS='=' read -r key value; do
        # Skip empty lines and comments
        if [[ -n "$key" && ! "$key" =~ ^[[:space:]]*# ]]; then
            # Remove quotes if present
            value=$(echo "$value" | sed 's/^"\(.*\)"$/\1/' | sed "s/^'\(.*\)'$/\1/")
            export "$key=$value"
        fi
    done < .env
    echo -e "${GREEN}✅ 环境变量加载完成${NC}"
else
    echo -e "${YELLOW}⚠️  .env文件不存在，使用默认配置...${NC}"
fi

# Start the application
echo ""
echo "🚀 启动EasyRAG知识库系统..."
echo "📍 服务将在 http://localhost:8028 启动"
echo "💡 按 Ctrl+C 可以停止服务"
echo ""

# Start the API server
python app.py

# Handle exit
EXIT_CODE=$?
echo ""
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ 服务正常退出${NC}"
else
    echo -e "${RED}❌ 服务异常退出，错误代码：$EXIT_CODE${NC}"
    echo ""
    echo "🔧 故障排除建议："
    echo "1. 检查端口8028是否被占用"
    echo "2. 确认所有依赖包已正确安装"
    echo "3. 查看上方的错误信息"
    echo "4. 如需重新部署，请运行 deploy.sh"
fi

echo ""
echo "按任意键退出..."
read -n 1 -s 