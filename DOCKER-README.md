# EasyRAG Docker 部署说明

## 📋 概述

本文档介绍如何使用 Docker 部署 EasyRAG 知识库系统，并将数据库和相关数据映射到宿主机上，确保数据持久化。

## 🗂️ 文件结构

```
EasyRAG/
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 编排文件
├── docker-setup.bat        # Windows 环境设置脚本
├── docker-setup.sh         # Linux 环境设置脚本
├── .dockerignore           # Docker 构建忽略文件
└── DOCKER-README.md        # 本文档
```

## 🛠️ 部署步骤

### 1. 准备环境

确保您的系统已安装：
- Docker Desktop (Windows/Mac) 或 Docker Engine (Linux)
- Docker Compose

### 2. 初始化数据目录

#### Windows 系统：
```bash
# 运行环境设置脚本
docker-setup.bat
```

#### Linux 系统：
```bash
# 设置脚本执行权限
chmod +x docker-setup.sh

# 运行环境设置脚本
./docker-setup.sh
```

### 3. 构建和启动服务

```bash
# 构建镜像并启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f easyrag
```

### 4. 访问服务

服务启动后，访问以下地址：
- 主页面：http://localhost:8028
- API 文档：http://localhost:8028/docs

## 📁 数据目录映射

### Windows 系统映射：
```
宿主机路径                    容器内路径
D:/data/easyrag/db         → /app/db
D:/data/easyrag/logs       → /app/logs
D:/data/easyrag/models     → /app/models_file
D:/data/easyrag/files      → /app/files
D:/data/easyrag/temp       → /app/temp_files
```

### Linux 系统映射：
```
宿主机路径                    容器内路径
/data/easyrag/db          → /app/db
/data/easyrag/logs        → /app/logs
/data/easyrag/models      → /app/models_file
/data/easyrag/files       → /app/files
/data/easyrag/temp        → /app/temp_files
```

## 🔧 常用命令

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
docker-compose logs -f easyrag
```

### 数据管理
```bash
# 进入容器
docker-compose exec easyrag bash

# 查看数据目录
docker-compose exec easyrag ls -la /app/db
```

## 📊 健康检查

系统内置健康检查机制：
- 检查间隔：30秒
- 超时时间：10秒
- 重试次数：3次
- 启动等待：60秒

检查命令：
```bash
# 手动健康检查
curl -f http://localhost:8028/kb/list
```

## 🔒 安全配置

### 端口配置
- 默认端口：8028
- 如需修改，请编辑 `docker-compose.yml` 中的端口映射

### 数据权限
- 数据目录权限：755
- 确保 Docker 有权限访问映射的目录

## 🐛 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 查看端口占用
   netstat -ano | findstr :8028  # Windows
   lsof -i :8028                 # Linux
   
   # 修改端口
   # 编辑 docker-compose.yml 中的端口映射
   ```

2. **数据目录权限问题**
   ```bash
   # Linux 系统
   sudo chown -R $USER:$USER /data/easyrag
   sudo chmod -R 755 /data/easyrag
   ```

3. **容器无法启动**
   ```bash
   # 查看详细日志
   docker-compose logs easyrag
   
   # 重新构建镜像
   docker-compose build --no-cache
   ```

### 日志查看
```bash
# 查看应用日志
docker-compose logs -f easyrag

# 查看系统日志（Windows）
type D:\data\easyrag\logs\*.log

# 查看系统日志（Linux）
tail -f /data/easyrag/logs/*.log
```

## 🔄 更新和维护

### 更新应用
```bash
# 停止服务
docker-compose down

# 拉取最新代码
git pull

# 重新构建并启动
docker-compose build --no-cache
docker-compose up -d
```

### 数据备份
```bash
# Windows 系统备份
xcopy D:\data\easyrag D:\backup\easyrag-%date% /E /I

# Linux 系统备份
cp -r /data/easyrag /backup/easyrag-$(date +%Y%m%d)
```

## 📈 性能优化

### 资源限制
可以在 `docker-compose.yml` 中添加资源限制：
```yaml
services:
  easyrag:
    # ... 其他配置
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
```

### 存储优化
- 使用 SSD 存储提升性能
- 定期清理临时文件和日志

## 🆘 支持

如遇到问题，请：
1. 查看日志文件
2. 检查网络连接
3. 确认端口是否被占用
4. 验证数据目录权限

---

**注意**：首次启动时，系统会自动下载所需的模型文件，这可能需要一些时间，请耐心等待。 