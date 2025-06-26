# 使用官方Python 3.9镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgcc-s1 \
    && rm -rf /var/lib/apt/lists/*

# 升级pip并安装基础包
RUN pip install --upgrade pip setuptools wheel

# 复制requirements文件
COPY requirements_cpu.txt requirements_gpu.txt ./

# 安装Python依赖 (默认使用CPU版本)
ARG USE_GPU=false
RUN if [ "$USE_GPU" = "true" ] ; then \
        pip install -r requirements_gpu.txt -i https://mirrors.aliyun.com/pypi/simple/ ; \
    else \
        pip install -r requirements_cpu.txt -i https://mirrors.aliyun.com/pypi/simple/ ; \
    fi

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p db models_file temp_files static/uploads

# 设置权限
RUN chmod +x start.sh

# 暴露端口
EXPOSE 8028 7861

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8028/health || exit 1

# 启动命令
CMD ["python", "app.py"] 