#!/bin/bash
# 命数研究室快速启动脚本

set -e

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 命数研究室启动脚本 ===${NC}\n"

# 1. 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}创建虚拟环境...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ 虚拟环境创建完成${NC}\n"
fi

# 2. 激活虚拟环境
echo -e "${YELLOW}激活虚拟环境...${NC}"
source .venv/bin/activate

# 3. 检查并安装依赖
echo -e "${YELLOW}检查依赖...${NC}"
if ! python -c "import streamlit" 2>/dev/null; then
    echo -e "${YELLOW}安装依赖包（首次运行需要 1-2 分钟）...${NC}"
    pip install --upgrade pip -q
    pip install -r requirements.txt -q
    echo -e "${GREEN}✓ 依赖安装完成${NC}\n"
else
    echo -e "${GREEN}✓ 依赖已安装${NC}\n"
fi

# 4. 设置环境变量（本地开发模式）
export MINGSHU_RUNTIME_MODE=local

# 5. 检查端口
if lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠️  端口 8501 已被占用${NC}"
    echo "是否要杀死占用进程并重新启动? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        lsof -ti:8501 | xargs kill -9
        echo -e "${GREEN}✓ 已释放端口 8501${NC}\n"
    else
        echo "请手动释放端口后再启动"
        exit 1
    fi
fi

# 6. 启动 Streamlit
echo -e "${GREEN}正在启动命数研究室...${NC}"
echo -e "${YELLOW}访问地址: http://127.0.0.1:8501${NC}\n"
echo "按 Ctrl+C 停止服务"
echo ""

streamlit run app.py --server.port 8501
