#!/bin/bash

# Color settings
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Set UTF-8 locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Display title
echo -e "${GREEN}======================================================="
echo "           EasyRAG Knowledge Base System"
echo "=======================================================${NC}"
echo ""
echo "This script will help you deploy the EasyRAG local knowledge base system."
echo "It will check and install required components automatically."
echo ""
echo -e "${GREEN}=======================================================${NC}"
echo ""

# Check if Python is installed
echo -e "${GREEN}[1/6] Checking Python environment...${NC}"
if ! command -v python3.9 &> /dev/null; then
    echo -e "${YELLOW}Python 3.9 not found, trying to install...${NC}"
    
    # Install Python 3.9
    echo "Installing Python 3.9..."
    sudo apt update
    sudo apt install -y software-properties-common
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install -y python3.9 python3.9-venv python3.9-dev python3-pip
    
    # Verify Python installation
    if ! command -v python3.9 &> /dev/null; then
        echo -e "${RED}Python 3.9 installation failed. Please install Python 3.9 manually.${NC}"
        exit 1
    fi
    
    # Create symbolic link to ensure python3 points to python3.9
    sudo update-alternatives --install /usr/bin/python3 python3 $(which python3.9) 1
    PYTHON_CMD=python3.9
else
    PYTHON_CMD=python3.9
    PYTHON_VERSION=$(python3.9 --version)
    echo -e "Detected ${GREEN}$PYTHON_VERSION${NC}"
fi

echo ""

# Check and create virtual environment
echo -e "${GREEN}[2/6] Setting up virtual environment...${NC}"
if [ ! -d "py_env" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv py_env
else
    echo "Virtual environment already exists..."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source py_env/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Virtual environment activation failed. Please try manually.${NC}"
    exit 1
fi
echo -e "${GREEN}Virtual environment activated successfully!${NC}"

echo ""

# Install dependencies
echo -e "${GREEN}[3/6] Installing dependencies...${NC}"
echo "Creating and configuring pip cache directory..."
mkdir -p pip_cache
export PIP_CACHE_DIR="$(pwd)/pip_cache"

# Check for NVIDIA GPU
echo "Checking for NVIDIA GPU..."
if command -v nvidia-smi &> /dev/null && nvidia-smi &> /dev/null; then
    echo -e "${GREEN}NVIDIA GPU detected, installing GPU dependencies...${NC}"
    echo "Installing base dependencies first..."
    python -m pip install --upgrade pip setuptools wheel --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
    python -m pip install numpy==1.24.4 --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
    python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir "$PIP_CACHE_DIR" -i https://download.pytorch.org/whl/cu121
    echo "Skipping faiss-gpu installation temporarily..."
    echo "Installing remaining dependencies..."
    pip install -r requirements_gpu.txt --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
else
    echo -e "${YELLOW}No NVIDIA GPU detected or NVIDIA driver not installed, using CPU version...${NC}"
    echo "Installing base dependencies first..."
    python -m pip install --upgrade pip setuptools wheel --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
    python -m pip install numpy==1.24.4 --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
    python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir "$PIP_CACHE_DIR" -i https://download.pytorch.org/whl/cpu
    echo "Skipping faiss-cpu installation temporarily..."
    echo "Installing remaining dependencies..."
    pip install -r requirements_cpu.txt --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
fi

if [ $? -ne 0 ]; then
    echo -e "${RED}Dependency installation failed. Check your network connection.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies installed!${NC}"

echo ""
echo -e "${YELLOW}NOTE: faiss package was skipped during installation.${NC}"
echo "If you need vector similarity search functionality, please install it manually:"
echo "- For CPU: pip install faiss-cpu"
echo "- For GPU: pip install faiss-gpu"
echo ""

# Create necessary directories
echo -e "${GREEN}[4/6] Creating necessary directories...${NC}"
mkdir -p db
mkdir -p models_file
mkdir -p temp_files
echo -e "${GREEN}Directories created!${NC}"

echo ""

# Download and prepare all required models
echo -e "${GREEN}[5/6] Downloading and preparing all required models...${NC}"
echo "This process will download all required models to the models_file directory."
echo "Total download size is approximately 7GB, please ensure sufficient disk space and stable network connection."
echo ""

# Configure modelscope cache
echo "Configuring modelscope cache directory..."
export MODELSCOPE_CACHE=$(pwd)/models_file

# Ensure virtual environment is active
source py_env/bin/activate

# Download the DeepSeek LLM model
echo -e "${YELLOW}[Model 1/4] Downloading DeepSeek 1.5B model...${NC}"
python -c "
from modelscope import snapshot_download
import os
import shutil
import traceback
try:
    # 下载DeepSeek模型
    print('Downloading DeepSeek model...')
    model_id = 'deepseek-ai/deepseek-chat-1.5b-base'
    model_dir = snapshot_download(model_id, cache_dir='$(pwd)/models_file')
    print(f'DeepSeek model downloaded to {model_dir}')
except Exception as e:
    print(f'Error downloading DeepSeek model: {str(e)}')
    traceback.print_exc()
"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to download DeepSeek model. The system will attempt to download it at runtime.${NC}"
else
    echo -e "${GREEN}DeepSeek model downloaded successfully!${NC}"
fi

# Download the Embedding model
echo -e "${YELLOW}[Model 2/4] Downloading Embedding model...${NC}"
python -c "
from modelscope import snapshot_download
import os
import traceback
try:
    # 下载Embedding模型
    print('Downloading Embedding model...')
    model_id = 'iic/nlp_gte_sentence-embedding_chinese-base'
    model_dir = snapshot_download(model_id, cache_dir='$(pwd)/models_file')
    print(f'Embedding model downloaded to {model_dir}')
except Exception as e:
    print(f'Error downloading Embedding model: {str(e)}')
    traceback.print_exc()
"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to download Embedding model. The system will attempt to download it at runtime.${NC}"
else
    echo -e "${GREEN}Embedding model downloaded successfully!${NC}"
fi

# Download the Rerank model
echo -e "${YELLOW}[Model 3/4] Downloading Rerank model...${NC}"
python -c "
from modelscope import snapshot_download
import os
import traceback
try:
    # 下载Rerank模型
    print('Downloading Rerank model...')
    model_id = 'iic/gte_passage-ranking_multilingual-base'
    model_dir = snapshot_download(model_id, cache_dir='$(pwd)/models_file')
    print(f'Rerank model downloaded to {model_dir}')
except Exception as e:
    print(f'Error downloading Rerank model: {str(e)}')
    traceback.print_exc()
"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to download Rerank model. The system will attempt to download it at runtime.${NC}"
else
    echo -e "${GREEN}Rerank model downloaded successfully!${NC}"
fi

# Download the OCR models
echo -e "${YELLOW}[Model 4/4] Downloading OCR model...${NC}"
python -c "
from modelscope import snapshot_download
import os
import sys
import traceback

try:
    # 配置EasyOCR模型目录
    ocr_model_dir = os.path.join('$(pwd)/models_file', 'easyocr')
    os.makedirs(ocr_model_dir, exist_ok=True)
    print(f'OCR model directory: {ocr_model_dir}')
    
    # 下载OCR模型
    print('Downloading OCR model...')
    model_id = 'Ceceliachenen/easyocr'
    model_dir = snapshot_download(model_id, cache_dir=ocr_model_dir)
    print(f'OCR model downloaded to {model_dir}')
    
    # 安装easyocr（如果尚未安装）
    try:
        import easyocr
        print('EasyOCR already installed')
    except ImportError:
        print('Installing EasyOCR...')
        import pip
        pip.main(['install', 'easyocr'])
        print('EasyOCR installed')
    
    # 初始化EasyOCR以下载必要的模型文件
    print('Initializing EasyOCR to download language models...')
    sys.path.append('$(pwd)')
    os.environ['MODELSCOPE_CACHE'] = '$(pwd)/models_file'
    import easyocr
    reader = easyocr.Reader(['ch_sim', 'en'], model_storage_directory=ocr_model_dir, download_enabled=True)
    print('OCR language models downloaded and initialized')
    
except Exception as e:
    print(f'Error downloading or initializing OCR model: {str(e)}')
    traceback.print_exc()
"
if [ $? -ne 0 ]; then
    echo -e "${RED}Failed to download OCR model. The system will attempt to download it at runtime.${NC}"
else
    echo -e "${GREEN}OCR model downloaded successfully!${NC}"
fi

echo -e "${GREEN}All models download process completed. Some models may be downloaded at runtime if failed.${NC}"
echo ""

# Start services
echo -e "${GREEN}[6/6] Starting services...${NC}"
echo ""
echo -e "${GREEN}All preparations complete, starting services!${NC}"
echo ""
echo -e "${YELLOW}Note: Press Ctrl+C to stop the services${NC}"
echo ""

# Create startup script
cat > start_service.sh << 'EOL'
#!/bin/bash
# Set UTF-8 locale
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8

# Activate virtual environment
source py_env/bin/activate

# Start API server
python api_server.py &
API_PID=$!
echo "API server started, PID: $API_PID"

# Wait 5 seconds to let API server fully start
sleep 5

# Start Web UI
python ui_new.py &
UI_PID=$!
echo "Web UI started, PID: $UI_PID"

echo ""
echo "EasyRAG knowledge base system started!"
echo "API server running at: http://localhost:8000"
echo "Web interface running at: http://localhost:7861"
echo ""
echo "Please visit http://localhost:7861 in your browser to use the system"
echo ""
echo "Press Ctrl+C to stop all services"

# Capture Ctrl+C signal
trap 'echo "Stopping services..."; kill $API_PID $UI_PID; echo "Services stopped"; exit 0' INT

# Keep script running
wait
EOL

# Set startup script executable
chmod +x start_service.sh

# Use tmux or run directly
if command -v tmux &> /dev/null; then
    echo "Using tmux to start services..."
    tmux new-session -d -s easyrag './start_service.sh'
    echo -e "${GREEN}Services started in tmux session, use 'tmux attach -t easyrag' to view service status${NC}"
else
    echo "Starting services directly..."
    ./start_service.sh
fi

echo -e "${GREEN}EasyRAG knowledge base system started!${NC}"
echo "API server running at: http://localhost:8000"
echo "Web interface running at: http://localhost:7861"
echo ""
echo "Please visit http://localhost:7861 in your browser to use the system"
echo "" 