# 使用官方 Python 3.10 基础镜像
FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    libopencv-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# 创建数据目录并设置权限
RUN mkdir -p /data/milvus/etcd \
    && mkdir -p /data/milvus/minio \
    && mkdir -p /data/milvus/milvus \
    && mkdir -p /app/db \
    && mkdir -p /app/logs \
    && mkdir -p /app/models_file \
    && mkdir -p /app/files \
    && mkdir -p /app/temp_files \
    && chmod -R 755 /data \
    && chmod -R 755 /app

# 复制依赖文件
COPY requirements_cpu.txt /app/

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements_cpu.txt

# 复制项目文件
COPY . /app/

# 创建环境配置文件
RUN if [ ! -f /app/.env ]; then \
    cp /app/.env.example /app/.env; \
    fi

# 设置权限
RUN chmod +x /app/start.sh || true
RUN chmod +x /app/app.py

# 暴露端口
EXPOSE 8028

# 设置挂载点
VOLUME ["/data", "/app/db", "/app/logs", "/app/models_file", "/app/files"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8028/kb/list || exit 1

# 启动命令
CMD ["python", "app.py"] 