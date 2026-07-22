#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

find_python() {
  for candidate in python3.12 python3.11 /Users/uni/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 python3; do
    if command -v "$candidate" >/dev/null 2>&1 || [ -x "$candidate" ]; then
      if "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1; then
        echo "$candidate"
        return 0
      fi
    fi
  done
  return 1
}

PYTHON_BIN="$(find_python || true)"

if [ -z "$PYTHON_BIN" ]; then
  echo "未找到 Python 3.11 或更高版本。请先安装 Python 3.11+，再重新运行。"
  exit 1
fi

if [ ! -d ".venv" ]; then
  echo "正在创建虚拟环境：.venv"
  "$PYTHON_BIN" -m venv .venv
fi

# 激活虚拟环境（重要！直接调用 .venv/bin/python3 会报模块找不到错误）
source .venv/bin/activate

# 检查依赖是否已安装，避免每次都重装
if ! .venv/bin/python -c "import streamlit" 2>/dev/null; then
  echo "正在安装依赖，请稍等..."
  .venv/bin/python -m pip install --upgrade pip -q
  .venv/bin/python -m pip install -r requirements.txt -q
fi

echo "正在启动命数研究室..."
echo "  地址: http://127.0.0.1:8501"
MINGSHU_RUNTIME_MODE=local .venv/bin/python -m streamlit run app.py --server.port 8501
