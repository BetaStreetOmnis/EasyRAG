# EasyRAG Docker 部署指南

本指南提供了使用Docker部署EasyRAG知识库系统的完整说明。

## 📋 系统要求

### 基本要求
- Docker Engine 20.10+
- Docker Compose 2.0+
- 系统内存: 4GB+ (推荐8GB+)
- 磁盘空间: 10GB+ (用于模型和数据存储)

### GPU版本额外要求
- NVIDIA GPU (支持CUDA 11.8+)
- NVIDIA Docker Runtime
- NVIDIA Container Toolkit

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone <repository-url>
cd EasyRAG
```

### 2. 一键部署
```bash
# 自动检测GPU并部署
chmod +x docker-deploy.sh
./docker-deploy.sh

# 或者手动指定版本
./docker-deploy.sh --cpu   # CPU版本
./docker-deploy.sh --gpu   # GPU版本
```

### 3. 访问服务
- **Web界面**: http://localhost:7861
- **API服务**: http://localhost:8028

## 📖 详细部署说明

### CPU版本部署
```bash
# 使用默认配置
docker-compose up -d

# 或者使用CPU专用配置
docker-compose -f docker-compose.yml up -d
```

### GPU版本部署
```bash
# 确保已安装NVIDIA Docker支持
docker-compose -f docker-compose.gpu.yml up -d
```

### 自定义配置部署
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
nano .env

# 启动服务
docker-compose up -d
```

## ⚙️ 配置说明

### 环境变量配置 (.env)
```bash
# API服务器配置
API_HOST=0.0.0.0          # API服务监听地址
API_PORT=8028             # API服务端口

# 前端配置
API_BASE_URL=http://localhost:8028  # API基础URL

# GPU支持
USE_GPU=false             # 是否使用GPU (true/false)

# CUDA设置 (仅GPU版本)
CUDA_VISIBLE_DEVICES=0    # 指定使用的GPU设备
```

### 端口配置
- `8028`: API服务端口
- `7861`: Web界面端口

如需修改端口，请编辑 `docker-compose.yml` 文件。

### 数据持久化
以下目录会被持久化存储：
- `./db`: 数据库文件
- `./models_file`: 模型文件
- `./temp_files`: 临时文件
- `./files`: 上传的文件

## 🛠️ 常用命令

### 服务管理
```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f easyrag-api
docker-compose logs -f easyrag-web
```

### 镜像管理
```bash
# 重新构建镜像
docker-compose build --no-cache

# 删除镜像
docker-compose down --rmi all

# 清理未使用的镜像
docker image prune -f
```

### 数据管理
```bash
# 备份数据
tar -czf easyrag-backup-$(date +%Y%m%d).tar.gz db/ models_file/

# 恢复数据
tar -xzf easyrag-backup-YYYYMMDD.tar.gz
```

## 🔧 故障排除

### 常见问题

#### 1. 服务无法启动
```bash
# 检查日志
docker-compose logs

# 检查端口占用
netstat -tulpn | grep 8028
netstat -tulpn | grep 7861

# 清理并重新启动
docker-compose down
docker-compose up -d
```

#### 2. GPU不可用
```bash
# 检查NVIDIA Docker支持
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# 检查Docker Compose GPU配置
docker-compose -f docker-compose.gpu.yml config
```

#### 3. 内存不足
```bash
# 检查系统资源
docker stats

# 限制容器内存使用
# 在docker-compose.yml中添加:
# deploy:
#   resources:
#     limits:
#       memory: 4G
```

#### 4. 网络连接问题
```bash
# 检查容器网络
docker network ls
docker network inspect easyrag_easyrag-network

# 重新创建网络
docker-compose down
docker network prune
docker-compose up -d
```

### 性能优化

#### CPU版本优化
- 增加容器内存限制
- 使用SSD存储
- 优化模型参数

#### GPU版本优化
- 确保GPU驱动最新
- 调整CUDA_VISIBLE_DEVICES
- 监控GPU内存使用

## 📊 监控和维护

### 健康检查
系统内置健康检查，可通过以下方式查看：
```bash
# 查看容器健康状态
docker-compose ps

# 手动健康检查
curl -f http://localhost:8028/health
```

### 日志管理
```bash
# 查看实时日志
docker-compose logs -f --tail=100

# 日志轮转配置
# 在docker-compose.yml中添加:
# logging:
#   driver: "json-file"
#   options:
#     max-size: "10m"
#     max-file: "3"
```

### 自动备份脚本
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/easyrag"
mkdir -p $BACKUP_DIR

# 备份数据
tar -czf $BACKUP_DIR/easyrag_$DATE.tar.gz db/ models_file/

# 清理旧备份（保留7天）
find $BACKUP_DIR -name "easyrag_*.tar.gz" -mtime +7 -delete

echo "Backup completed: easyrag_$DATE.tar.gz"
```

## 🔄 更新升级

### 更新应用
```bash
# 拉取最新代码
git pull

# 重新构建和部署
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### 更新依赖
```bash
# 更新requirements文件后
docker-compose build --no-cache
docker-compose up -d
```

## 📝 开发环境

### 开发模式部署
```bash
# 创建开发配置
cp docker-compose.yml docker-compose.dev.yml

# 编辑开发配置，添加卷挂载
# volumes:
#   - .:/app
#   - /app/py_env

# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d
```

### 调试模式
```bash
# 进入容器调试
docker-compose exec easyrag-api bash
docker-compose exec easyrag-web bash

# 查看容器内部状态
docker-compose exec easyrag-api ps aux
docker-compose exec easyrag-api df -h
```

## 🆘 获取帮助

如果遇到问题：

1. 查看本文档的故障排除部分
2. 检查项目的 GitHub Issues
3. 查看 Docker 和 Docker Compose 官方文档
4. 提交新的 Issue 并包含详细的错误信息和系统环境

## 📄 许可证

本项目遵循 [LICENSE](LICENSE) 文件中的许可证条款。 