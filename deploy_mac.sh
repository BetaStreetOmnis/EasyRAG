#!/bin/bash

# Color settings
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

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

# Check if Homebrew is installed
echo -e "${GREEN}[1/7] Checking Homebrew...${NC}"
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}Homebrew not found, installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH
    if [[ $(uname -m) == "arm64" ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    
    if ! command -v brew &> /dev/null; then
        echo -e "${RED}Homebrew installation failed. Please install Homebrew manually.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}Homebrew is installed.${NC}"

echo ""

# Check if Python is installed
echo -e "${GREEN}[2/7] Checking Python environment...${NC}"
if ! command -v python3.9 &> /dev/null; then
    echo -e "${YELLOW}Python 3.9 not found, installing...${NC}"
    brew install python@3.9
    
    # Create symlink for python3.9 (may be needed on some systems)
    brew link python@3.9
    
    # Verify Python installation
    if ! command -v python3.9 &> /dev/null; then
        echo -e "${RED}Python 3.9 installation failed. Please install Python 3.9 manually.${NC}"
        exit 1
    fi
    PYTHON_CMD=python3.9
else
    PYTHON_CMD=python3.9
    PYTHON_VERSION=$(python3.9 --version)
    echo -e "Detected ${GREEN}$PYTHON_VERSION${NC}"
fi

echo ""

# Check and create virtual environment
echo -e "${GREEN}[3/7] Setting up virtual environment...${NC}"
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
echo -e "${GREEN}[4/7] Installing dependencies...${NC}"
echo "Creating and configuring pip cache directory..."
mkdir -p pip_cache
export PIP_CACHE_DIR="$(pwd)/pip_cache"

# Check for Apple Silicon (M1/M2) or Intel
echo "Checking Mac hardware architecture..."
if [[ $(uname -m) == "arm64" ]]; then
    echo -e "${YELLOW}Apple Silicon (M1/M2) detected${NC}"
    ARCH="arm64"
else
    echo -e "${YELLOW}Intel Mac detected${NC}"
    ARCH="x86_64"
fi

# Install dependencies based on architecture
echo "Installing base dependencies first..."
python -m pip install --upgrade pip setuptools wheel --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/
python -m pip install numpy==1.24.4 --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/

# Install PyTorch (architecture specific)
if [[ "$ARCH" == "arm64" ]]; then
    # For Apple Silicon (MPS acceleration)
    python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir "$PIP_CACHE_DIR"
else
    # For Intel Mac
    python -m pip install torch==2.4.1 torchvision==0.19.1 torchaudio==2.4.1 --cache-dir "$PIP_CACHE_DIR" -i https://download.pytorch.org/whl/cpu
fi

echo "Skipping faiss installation temporarily..."
echo "Installing remaining dependencies..."
pip install -r requirements_cpu.txt --cache-dir "$PIP_CACHE_DIR" -i https://mirrors.aliyun.com/pypi/simple/

if [ $? -ne 0 ]; then
    echo -e "${RED}Dependency installation failed. Check your network connection.${NC}"
    exit 1
fi
echo -e "${GREEN}Dependencies installed!${NC}"

echo ""
echo -e "${YELLOW}NOTE: faiss package was skipped during installation.${NC}"
echo "If you need vector similarity search functionality, please install it manually:"
echo "- For CPU: pip install faiss-cpu"
echo "For Apple Silicon Macs, you may need to build faiss from source, see: https://github.com/facebookresearch/faiss/wiki/Getting-started"
echo ""

# Create necessary directories
echo -e "${GREEN}[5/7] Creating necessary directories...${NC}"
mkdir -p db
mkdir -p models_file
mkdir -p temp_files
echo -e "${GREEN}Directories created!${NC}"

echo ""

# Download and prepare DeepSeek model
echo -e "${GREEN}[6/7] Preparing DeepSeek model...${NC}"
echo "The system will automatically download DeepSeek 1.5B model from ModelScope"
echo "Model size is approximately 3GB, please ensure sufficient disk space"

echo ""

# Start services
echo -e "${GREEN}[7/7] Starting services...${NC}"
echo ""
echo -e "${GREEN}All preparations complete, starting services!${NC}"
echo ""
echo -e "${YELLOW}Note: Press Ctrl+C to stop the services${NC}"
echo ""

# Create startup script
cat > start_service.sh << 'EOL'
#!/bin/bash

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

# Use terminal-notifier for notifications if available
if command -v terminal-notifier &> /dev/null; then
    terminal-notifier -title "EasyRAG" -message "Services are starting up" -sound default
fi

# Use tmux if available or run directly
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