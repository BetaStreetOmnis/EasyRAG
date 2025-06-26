#!/bin/bash

# EasyRAG Docker部署脚本
# 支持CPU和GPU版本的一键部署

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker是否安装
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        echo "安装指南: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose未安装，请先安装Docker Compose"
        echo "安装指南: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    print_success "Docker环境检查通过"
}

# 检查GPU支持
check_gpu() {
    if command -v nvidia-smi &> /dev/null; then
        if nvidia-smi &> /dev/null; then
            print_info "检测到NVIDIA GPU，可以使用GPU版本"
            return 0
        else
            print_warning "检测到nvidia-smi但GPU不可用，将使用CPU版本"
            return 1
        fi
    else
        print_info "未检测到NVIDIA GPU，将使用CPU版本"
        return 1
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p db models_file temp_files files
    print_success "目录创建完成"
}

# 复制环境配置文件
setup_env() {
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            print_info "复制环境配置文件..."
            cp .env.example .env
            print_success "环境配置文件已创建，请根据需要修改 .env 文件"
        else
            print_info "创建默认环境配置文件..."
            cat > .env << EOF
# API服务器配置
API_HOST=0.0.0.0
API_PORT=8028

# 前端API基础URL配置
API_BASE_URL=http://localhost:8028

# GPU支持（true/false）
USE_GPU=false
EOF
            print_success "默认环境配置文件已创建"
        fi
    else
        print_info "环境配置文件已存在"
    fi
}

# 构建和启动服务
deploy() {
    local use_gpu=$1
    
    print_info "开始部署EasyRAG服务..."
    
    # 设置GPU环境变量
    if [ "$use_gpu" = "true" ]; then
        export USE_GPU=true
        print_info "使用GPU版本部署"
    else
        export USE_GPU=false
        print_info "使用CPU版本部署"
    fi
    
    # 构建镜像
    print_info "构建Docker镜像..."
    docker-compose build --no-cache
    
    # 启动服务
    print_info "启动服务..."
    docker-compose up -d
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    if docker-compose ps | grep -q "Up"; then
        print_success "EasyRAG服务部署成功！"
        echo ""
        echo "服务访问地址："
        echo "  - API服务: http://localhost:8028"
        echo "  - Web界面: http://localhost:7861"
        echo ""
        echo "查看服务状态: docker-compose ps"
        echo "查看日志: docker-compose logs -f"
        echo "停止服务: docker-compose down"
    else
        print_error "服务启动失败，请检查日志"
        docker-compose logs
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "EasyRAG Docker部署脚本"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  -g, --gpu      使用GPU版本部署"
    echo "  -c, --cpu      使用CPU版本部署"
    echo "  --stop         停止服务"
    echo "  --restart      重启服务"
    echo "  --logs         查看日志"
    echo "  --status       查看服务状态"
    echo ""
    echo "示例:"
    echo "  $0              # 自动检测GPU并部署"
    echo "  $0 --gpu        # 强制使用GPU版本"
    echo "  $0 --cpu        # 强制使用CPU版本"
    echo "  $0 --stop       # 停止服务"
}

# 停止服务
stop_services() {
    print_info "停止EasyRAG服务..."
    docker-compose down
    print_success "服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启EasyRAG服务..."
    docker-compose restart
    print_success "服务已重启"
}

# 查看日志
show_logs() {
    docker-compose logs -f
}

# 查看状态
show_status() {
    docker-compose ps
}

# 主函数
main() {
    echo "======================================================="
    echo "           EasyRAG Docker部署脚本"
    echo "======================================================="
    echo ""
    
    # 解析命令行参数
    case "${1:-}" in
        -h|--help)
            show_help
            exit 0
            ;;
        --stop)
            stop_services
            exit 0
            ;;
        --restart)
            restart_services
            exit 0
            ;;
        --logs)
            show_logs
            exit 0
            ;;
        --status)
            show_status
            exit 0
            ;;
        -g|--gpu)
            USE_GPU_FORCE=true
            ;;
        -c|--cpu)
            USE_GPU_FORCE=false
            ;;
        "")
            # 自动检测
            ;;
        *)
            print_error "未知选项: $1"
            show_help
            exit 1
            ;;
    esac
    
    # 检查Docker环境
    check_docker
    
    # 创建目录和配置
    create_directories
    setup_env
    
    # 确定使用GPU还是CPU
    if [ "${USE_GPU_FORCE:-}" = "true" ]; then
        use_gpu=true
    elif [ "${USE_GPU_FORCE:-}" = "false" ]; then
        use_gpu=false
    else
        # 自动检测
        if check_gpu; then
            use_gpu=true
        else
            use_gpu=false
        fi
    fi
    
    # 部署服务
    deploy $use_gpu
}

# 运行主函数
main "$@" 