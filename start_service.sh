#!/bin/bash

# 颜色设置
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 激活虚拟环境
source py_env/bin/activate

# 启动API服务器
echo "Starting API server..."
python3 api_server.py > api_server.log 2>&1 &
API_PID=$!
echo "API server started with PID: $API_PID"

# 等待API服务器启动
echo "Waiting for API server to initialize..."
sleep 5

# 启动Web UI
echo "Starting Web UI..."
python3 ui.py > ui.log 2>&1 &
UI_PID=$!
echo "Web UI started with PID: $UI_PID"

echo -e "${GREEN}EasyRAG knowledge base system started!${NC}"
echo "API server running at: http://localhost:8023"
echo "Web interface running at: http://localhost:7860"
echo ""
echo "Please visit http://localhost:7860 in your browser to use the system"
echo ""
echo "Press Ctrl+C to stop all services and exit..."

# 保存进程ID到文件
echo "$API_PID $UI_PID" > .service_pids

# 监听CTRL+C以进行清理
trap 'echo "Stopping services..."; kill $API_PID $UI_PID 2>/dev/null; rm .service_pids; echo "Services stopped"; exit 0' INT
echo "Monitoring services... (press Ctrl+C to stop)"

# 保持脚本运行
while true; do
    sleep 1
done
