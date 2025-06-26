#!/bin/bash

# 颜色设置
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 显示标题
echo -e "${GREEN}======================================================="
echo -e "           EasyRAG Knowledge Base System"
echo -e "=======================================================${NC}"
echo ""
echo "This script will help you deploy the EasyRAG local knowledge base system."
echo "It will check and install required components automatically."
echo ""
echo -e "${GREEN}=======================================================${NC}"
echo ""

# [1/7] 检查Python安装
echo -e "${GREEN}[1/7] Checking Python environment...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python is not installed. Please install Python 3.9 first.${NC}"
    echo "Run: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "Detected ${GREEN}${PYTHON_VERSION}${NC}"
echo ""

# [2/7] 设置虚拟环境
echo -e "${GREEN}[2/7] Setting up virtual environment...${NC}"
if [ ! -d "py_env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv py_env
else
    echo "Existing virtual environment found. Do you want to recreate it? (y/n)"
    read -p "> " recreate
    if [ "$recreate" = "y" ] || [ "$recreate" = "Y" ]; then
        echo "Removing existing virtual environment..."
        rm -rf py_env
        echo "Creating fresh virtual environment..."
        python3 -m venv py_env
    else
        echo "Using existing virtual environment..."
    fi
fi

# 验证激活脚本是否存在
if [ ! -f "py_env/bin/activate" ]; then
    echo -e "${RED}Virtual environment activation script not found. Creating again...${NC}"
    rm -rf py_env
    python3 -m venv py_env
    
    if [ ! -f "py_env/bin/activate" ]; then
        echo -e "${RED}Failed to create virtual environment. Please check your Python installation.${NC}"
        exit 1
    fi
fi

# 激活虚拟环境
echo "Activating virtual environment..."
source py_env/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Virtual environment activation failed. Please try manually.${NC}"
    exit 1
fi
echo -e "${GREEN}Virtual environment activated successfully!${NC}"
echo ""

# [3/7] 安装依赖
echo -e "${GREEN}[3/7] Installing dependencies...${NC}"
echo "Creating and configuring pip cache directory..."
mkdir -p pip_cache
export PIP_CACHE_DIR="$(pwd)/pip_cache"

echo "Installing base dependencies first..."
python -m pip install --upgrade pip setuptools wheel --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
python -m pip install numpy==1.24.4 --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/

# 检查NVIDIA GPU
echo "Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}NVIDIA GPU detected, using GPU version...${NC}"
    
    # 添加PyTorch安装容错逻辑
    echo "Installing PyTorch GPU version..."
    echo "Trying specific version first..."
    python -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cu118 --no-cache-dir -U
    
    # 检查PyTorch是否安装成功
    if ! python -c "import torch; print(f'PyTorch {torch.__version__} installed successfully')" 2>/dev/null; then
        echo -e "${YELLOW}Failed to install specific PyTorch version, trying latest stable version...${NC}"
        python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cu118 --no-cache-dir -U
        
        # 再次检查PyTorch是否安装成功
        if ! python -c "import torch; print(f'PyTorch {torch.__version__} installed successfully')" 2>/dev/null; then
            echo -e "${YELLOW}Failed with mirror source, trying official PyTorch source...${NC}"
            python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir -U
        fi
    fi
    
    # 安装其他依赖
    echo "Installing remaining GPU dependencies..."
    pip install -r requirements_gpu.txt --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir
    
    # [4/7] 安装FAISS GPU版本
    echo -e "${GREEN}[4/7] Installing FAISS GPU version...${NC}"
    pip install faiss-gpu --no-cache-dir --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
else
    echo -e "${YELLOW}No NVIDIA GPU detected or NVIDIA driver not installed, using CPU version...${NC}"
    
    # 添加PyTorch安装容错逻辑
    echo "Installing PyTorch CPU version..."
    echo "Trying specific version first..."
    python -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cpu --no-cache-dir -U
    
    # 检查PyTorch是否安装成功
    if ! python -c "import torch; print(f'PyTorch {torch.__version__} installed successfully')" 2>/dev/null; then
        echo -e "${YELLOW}Failed to install specific PyTorch version, trying latest stable version...${NC}"
        python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cpu --no-cache-dir -U
        
        # 再次检查PyTorch是否安装成功
        if ! python -c "import torch; print(f'PyTorch {torch.__version__} installed successfully')" 2>/dev/null; then
            echo -e "${YELLOW}Failed with mirror source, trying official PyTorch source...${NC}"
            python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://download.pytorch.org/whl/cpu --no-cache-dir -U
        fi
    fi
    
    # 安装其他依赖
    echo "Installing remaining CPU dependencies..."
    pip install -r requirements_cpu.txt --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir
    
    # [4/7] 安装FAISS CPU版本
    echo -e "${GREEN}[4/7] Installing FAISS CPU version...${NC}"
    pip install faiss-cpu --no-cache-dir --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}Dependency installation failed. Check your network connection.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies installed!${NC}"

# 验证FAISS安装
echo "Verifying FAISS installation..."
if ! python -c "import faiss; print(f'FAISS {faiss.__version__} installed successfully')" 2>/dev/null; then
    echo -e "${RED}FAISS installation could not be verified. Trying alternative method...${NC}"
    if command -v nvidia-smi &> /dev/null; then
        pip install faiss-gpu --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/
    else
        pip install faiss-cpu --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/
    fi
    
    if python -c "import faiss; print(f'FAISS {faiss.__version__} installed successfully')" 2>/dev/null; then
        echo -e "${GREEN}FAISS installation succeeded with alternative method!${NC}"
    else
        echo -e "${RED}FAISS installation failed. Please install it manually after the script completes.${NC}"
        echo "For CPU: pip install faiss-cpu"
        echo "For GPU: pip install faiss-gpu"
    fi
fi

echo ""

# [5/7] 创建必要的目录
echo -e "${GREEN}[5/7] Creating necessary directories...${NC}"
mkdir -p db
mkdir -p models_file
mkdir -p temp_files
echo -e "${GREEN}Directories created!${NC}"
echo ""

# [6/7] 下载所需模型
echo -e "${GREEN}[6/7] Downloading and preparing required models...${NC}"
echo "This process will download all required models to the models_file directory."
echo "Total download size is approximately 7GB, please ensure sufficient disk space and stable network connection."
echo ""

# [7/7] 启动服务
echo -e "${GREEN}[7/7] Starting services...${NC}"
echo ""
echo -e "${GREEN}All preparations complete, starting services!${NC}"
echo ""
echo -e "${YELLOW}Note: Press Ctrl+C to stop the services${NC}"
echo ""

# 创建启动脚本
cat > start_service.sh << 'EOF'
#!/bin/bash

# 颜色设置
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# 激活虚拟环境
source py_env/bin/activate

# 启动API服务器
echo "Starting API server..."
python3 app.py > app.log 2>&1 &
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
EOF

# 设置执行权限
chmod +x start_service.sh

# 启动服务
echo "Starting services..."
./start_service.sh