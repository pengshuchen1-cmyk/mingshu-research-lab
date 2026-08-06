FROM python:3.11-slim

LABEL maintainer="Mingshu Research Lab"
LABEL description="命数研究室 - 八字紫微斗数分析工具"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
# - fonts-noto-cjk: 中文字体支持（PDF导出需要）
# - curl: 健康检查需要
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p data logs rules

# 设置权限（如果需要非 root 用户运行）
RUN useradd -m -u 1000 mingshu && \
    chown -R mingshu:mingshu /app

USER mingshu

# 暴露 Streamlit 默认端口
EXPOSE 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.fileWatcherType=none", \
     "--browser.gatherUsageStats=false"]
