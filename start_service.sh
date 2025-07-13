#!/bin/bash

# 颜色设置
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================================="
echo -e "           启动 EasyRAG 知识库系统"
echo -e "=======================================================${NC}"
echo ""

# 检查虚拟环境是否存在
if [ ! -d "py_env" ]; then
    echo -e "${YELLOW}未找到虚拟环境，请先运行 deploy_ubuntu.sh 进行部署${NC}"
    exit 1
fi

# 检查app.py是否存在
if [ ! -f "app.py" ]; then
    echo -e "${YELLOW}未找到 app.py 文件，请确保在正确的目录中${NC}"
    exit 1
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source py_env/bin/activate

# 创建必要的目录
mkdir -p db logs models_file files temp_files

# 启动API服务器
echo "启动API服务器..."
python3 app.py --port 8028 > app.log 2>&1 &
API_PID=$! 
echo "API服务器已启动，PID: $API_PID"

# 等待API服务器启动
echo "等待API服务器初始化..."
sleep 5

echo -e "${GREEN}EasyRAG知识库系统已启动！${NC}"
echo "API服务器运行于: http://localhost:8028"
echo "API文档地址: http://localhost:8028/docs"
echo "知识库列表: http://localhost:8028/kb/list"
echo ""
echo "请在浏览器中访问 http://localhost:8028 使用系统"
echo ""
echo "按Ctrl+C停止服务并退出..."

# 保存进程ID到文件
echo "$API_PID" > .service_pids

# 监听CTRL+C以进行清理
trap 'echo "停止服务..."; kill $API_PID 2>/dev/null; rm -f .service_pids; echo "服务已停止"; exit 0' INT
echo "监控服务中... (按Ctrl+C停止)"

# 保持脚本运行
while true; do
    sleep 1
done 