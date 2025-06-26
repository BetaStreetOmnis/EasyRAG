# EasyRAG 部署指南

EasyRAG知识库系统提供多种部署方式，请根据您的环境和需求选择合适的部署方案。

## 🚀 部署方式概览

| 部署方式 | 适用场景 | 优点 | 缺点 |
|---------|----------|------|------|
| **Docker部署** | 生产环境、跨平台 | 环境隔离、一键部署、易维护 | 需要Docker环境 |
| **Python 3.9原生部署** | 开发环境、最佳兼容性 | 性能最佳、调试方便 | 环境配置复杂 |
| **Python 3.13兼容部署** | 已有Python 3.13环境 | 使用现有环境 | 可能有兼容性问题 |

## 📦 Docker部署（推荐）

### 系统要求
- Docker Engine 20.10+
- Docker Compose 2.0+
- 系统内存: 4GB+ (推荐8GB+)
- 磁盘空间: 10GB+

### 快速开始

#### Windows用户
```batch
# 一键部署（自动检测GPU）
docker-deploy.bat

# 指定版本部署
docker-deploy.bat --cpu    # CPU版本
docker-deploy.bat --gpu    # GPU版本

# 服务管理
docker-deploy.bat --stop     # 停止服务
docker-deploy.bat --restart  # 重启服务
docker-deploy.bat --logs     # 查看日志
```

#### Linux用户
```bash
# 给脚本添加执行权限
chmod +x docker-deploy.sh

# 一键部署（自动检测GPU）
./docker-deploy.sh

# 指定版本部署
./docker-deploy.sh --cpu    # CPU版本
./docker-deploy.sh --gpu    # GPU版本

# 服务管理
./docker-deploy.sh --stop     # 停止服务
./docker-deploy.sh --restart  # 重启服务
./docker-deploy.sh --logs     # 查看日志
```

#### 手动Docker部署
```bash
# CPU版本
docker-compose up -d

# GPU版本
docker-compose -f docker-compose.gpu.yml up -d
```

### 访问服务
- **Web界面**: http://localhost:7861
- **API服务**: http://localhost:8028

### 详细文档
请参考 [README_DOCKER.md](README_DOCKER.md) 获取完整的Docker部署指南。

## 🐍 Python原生部署

### Python 3.9部署（推荐）

#### Windows用户
```batch
# 自动安装Python 3.9并部署
deploy.bat

# 如果自动安装失败，手动安装Python 3.9
install_python39_manual.bat
# 然后重新运行
deploy.bat
```

#### Linux用户
```bash
# Ubuntu/Debian系统
./deploy_ubuntu.sh
```

### Python 3.13兼容部署

如果您已经安装了Python 3.13，可以使用兼容版本：

```batch
# Windows用户
deploy_python313.bat
```

### 访问服务
- **Web界面**: http://localhost:7861
- **API服务**: http://localhost:8028

## ⚙️ 配置说明

### 环境变量配置
创建 `.env` 文件或修改现有配置：

```bash
# API服务器配置
API_HOST=0.0.0.0
API_PORT=8028

# 前端API基础URL配置
API_BASE_URL=http://localhost:8028

# GPU支持（仅Docker部署需要）
USE_GPU=false
```

### 端口配置
- `8028`: API服务端口
- `7861`: Web界面端口

如需修改端口，请编辑相应的配置文件。

## 🔧 故障排除

### 常见问题

#### 1. 端口被占用
```bash
# 检查端口占用
netstat -tulpn | grep 8028
netstat -tulpn | grep 7861

# Windows用户
netstat -ano | findstr :8028
netstat -ano | findstr :7861
```

#### 2. Python环境问题
- 确保Python版本正确（推荐3.9）
- 检查虚拟环境是否正确激活
- 重新安装依赖包

#### 3. Docker问题
- 确保Docker服务正在运行
- 检查Docker Compose版本
- 清理Docker缓存：`docker system prune -f`

#### 4. GPU支持问题
- 确保NVIDIA驱动已安装
- 检查CUDA版本兼容性
- 验证nvidia-smi命令可用

### 获取帮助

如果遇到问题：

1. 查看相应的详细部署文档
2. 检查系统日志和错误信息
3. 确认系统要求已满足
4. 在GitHub Issues中搜索类似问题
5. 提交新的Issue并包含详细信息

## 📊 性能优化建议

### 硬件配置
- **CPU**: 4核心以上推荐
- **内存**: 8GB以上推荐
- **存储**: SSD推荐
- **GPU**: NVIDIA GPU（可选，用于加速）

### 软件优化
- 使用SSD存储数据库和模型文件
- 适当调整向量数据库参数
- 根据硬件配置调整并发数
- 定期清理临时文件和日志

## 📋 部署检查清单

### 部署前检查
- [ ] 系统要求已满足
- [ ] 必要的软件已安装
- [ ] 端口未被占用
- [ ] 磁盘空间充足

### 部署后验证
- [ ] 服务正常启动
- [ ] Web界面可访问
- [ ] API服务响应正常
- [ ] 知识库功能正常
- [ ] 文件上传功能正常

## 🔄 更新升级

### Docker部署更新
```bash
# 拉取最新代码
git pull

# 重新构建和部署
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Python原生部署更新
```bash
# 拉取最新代码
git pull

# 激活虚拟环境
source py_env/bin/activate  # Linux
# 或
py_env\Scripts\activate.bat  # Windows

# 更新依赖
pip install -r requirements_cpu.txt --upgrade

# 重启服务
```

## 📄 许可证

本项目遵循 [LICENSE](LICENSE) 文件中的许可证条款。 