#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

# 使用已有的虚拟环境
if [ ! -d ".venv" ]; then
  echo "错误：未找到 .venv 虚拟环境。请先运行 run_mac.sh 创建环境。"
  exit 1
fi

echo "正在启动命数研究室..."
echo "  地址: http://127.0.0.1:8501"
.venv/bin/python -m streamlit run app.py --server.port 8501
