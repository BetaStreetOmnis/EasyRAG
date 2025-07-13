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
echo -e "此脚本将帮助您部署EasyRAG本地知识库系统。"
echo -e "它将自动检查并安装所需组件。"
echo ""
echo -e "${GREEN}=======================================================${NC}"
echo ""

# [1/7] 检查Python安装
echo -e "${GREEN}[1/7] 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}未安装Python。请先安装Python 3.9。${NC}"
    echo "运行: sudo apt update && sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "检测到 ${GREEN}${PYTHON_VERSION}${NC}"
echo ""

# [2/7] 设置虚拟环境
echo -e "${GREEN}[2/7] 设置虚拟环境...${NC}"
if [ ! -d "py_env" ]; then
    echo "创建虚拟环境..."
    python3 -m venv py_env
else
    echo "发现已存在的虚拟环境。是否要重新创建？(y/n)"
    read -p "> " recreate
    if [ "$recreate" = "y" ] || [ "$recreate" = "Y" ]; then
        echo "删除现有虚拟环境..."
        rm -rf py_env
        echo "创建全新虚拟环境..."
        python3 -m venv py_env
    else
        echo "使用现有虚拟环境..."
    fi
fi

# 验证激活脚本是否存在
if [ ! -f "py_env/bin/activate" ]; then
    echo -e "${RED}未找到虚拟环境激活脚本。重新创建...${NC}"
    rm -rf py_env
    python3 -m venv py_env
    
    if [ ! -f "py_env/bin/activate" ]; then
        echo -e "${RED}创建虚拟环境失败。请检查您的Python安装。${NC}"
        exit 1
    fi
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source py_env/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}虚拟环境激活失败。请尝试手动激活。${NC}"
    exit 1
fi
echo -e "${GREEN}虚拟环境成功激活！${NC}"
echo ""

# [3/7] 安装依赖
echo -e "${GREEN}[3/7] 安装依赖...${NC}"
echo "创建并配置pip缓存目录..."
mkdir -p pip_cache
export PIP_CACHE_DIR="$(pwd)/pip_cache"

echo "首先安装基础依赖..."
python -m pip install --upgrade pip setuptools wheel --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
python -m pip install numpy==1.24.4 --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/

# 检查NVIDIA GPU
echo "检查NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null; then
    echo -e "${GREEN}检测到NVIDIA GPU，使用GPU版本...${NC}"
    
    # 添加PyTorch安装容错逻辑
    echo "安装PyTorch GPU版本..."
    echo "首先尝试特定版本..."
    python -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cu118 --no-cache-dir -U
    
    # 检查PyTorch是否安装成功
    if ! python -c "import torch; print(f'PyTorch {torch.__version__} 安装成功')" 2>/dev/null; then
        echo -e "${YELLOW}安装特定PyTorch版本失败，尝试最新稳定版本...${NC}"
        python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cu118 --no-cache-dir -U
        
        # 再次检查PyTorch是否安装成功
        if ! python -c "import torch; print(f'PyTorch {torch.__version__} 安装成功')" 2>/dev/null; then
            echo -e "${YELLOW}使用镜像源失败，尝试官方PyTorch源...${NC}"
            python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://download.pytorch.org/whl/cu118 --no-cache-dir -U
        fi
    fi
    
    # 安装其他依赖
    echo "安装剩余GPU依赖..."
    pip install -r requirements_gpu.txt --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir
    
    # [4/7] 安装FAISS GPU版本
    echo -e "${GREEN}[4/7] 安装FAISS GPU版本...${NC}"
    pip install faiss-gpu --no-cache-dir --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
else
    echo -e "${YELLOW}未检测到NVIDIA GPU或未安装NVIDIA驱动，使用CPU版本...${NC}"
    
    # 添加PyTorch安装容错逻辑
    echo "安装PyTorch CPU版本..."
    echo "首先尝试特定版本..."
    python -m pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2 --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cpu --no-cache-dir -U
    
    # 检查PyTorch是否安装成功
    if ! python -c "import torch; print(f'PyTorch {torch.__version__} 安装成功')" 2>/dev/null; then
        echo -e "${YELLOW}安装特定PyTorch版本失败，尝试最新稳定版本...${NC}"
        python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://mirrors.tuna.tsinghua.edu.cn/pytorch/whl/cpu --no-cache-dir -U
        
        # 再次检查PyTorch是否安装成功
        if ! python -c "import torch; print(f'PyTorch {torch.__version__} 安装成功')" 2>/dev/null; then
            echo -e "${YELLOW}使用镜像源失败，尝试官方PyTorch源...${NC}"
            python -m pip install torch torchvision torchaudio --cache-dir "$PIP_CACHE_DIR" --index-url https://download.pytorch.org/whl/cpu --no-cache-dir -U
        fi
    fi
    
    # 安装其他依赖
    echo "安装剩余CPU依赖..."
    pip install -r requirements_cpu.txt --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/ --no-cache-dir
    
    # [4/7] 安装FAISS CPU版本
    echo -e "${GREEN}[4/7] 安装FAISS CPU版本...${NC}"
    pip install faiss-cpu --no-cache-dir --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}依赖安装失败。请检查您的网络连接。${NC}"
    exit 1
fi
echo -e "${GREEN}依赖安装完成！${NC}"

# 验证FAISS安装
echo "验证FAISS安装..."
if ! python -c "import faiss; print(f'FAISS {faiss.__version__} 安装成功')" 2>/dev/null; then
    echo -e "${RED}无法验证FAISS安装。尝试替代方法...${NC}"
    if command -v nvidia-smi &> /dev/null; then
        pip install faiss-gpu --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/
    else
        pip install faiss-cpu --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/
    fi
    
    if python -c "import faiss; print(f'FAISS {faiss.__version__} 安装成功')" 2>/dev/null; then
        echo -e "${GREEN}使用替代方法成功安装FAISS！${NC}"
    else
        echo -e "${RED}FAISS安装失败。请在脚本完成后手动安装。${NC}"
        echo "CPU版本: pip install faiss-cpu"
        echo "GPU版本: pip install faiss-gpu"
    fi
fi

echo ""

# [5/7] 创建必要的目录
echo -e "${GREEN}[5/7] 创建必要目录...${NC}"
mkdir -p db
mkdir -p models_file
mkdir -p temp_files
echo -e "${GREEN}目录创建完成！${NC}"
echo ""

# [6/7] 下载所需模型
echo -e "${GREEN}[6/7] 下载并准备所需模型...${NC}"
echo "此过程将下载所有必需的模型到models_file目录。"
echo "总下载大小约为7GB，请确保有足够的磁盘空间和稳定的网络连接。"
echo ""

# [7/7] 启动服务
echo -e "${GREEN}[7/7] 启动服务...${NC}"
echo ""
echo -e "${GREEN}所有准备工作完成，启动服务！${NC}"
echo ""
echo -e "${YELLOW}注意：按Ctrl+C停止服务${NC}"
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
EOF

# 设置执行权限
chmod +x start_service.sh

# 启动服务
echo "启动服务..."
./start_service.sh