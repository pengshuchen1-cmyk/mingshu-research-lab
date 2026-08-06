#!/bin/bash
# 命数研究室自动部署脚本
# 用于 VPS/云服务器快速部署

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 命数研究室部署脚本 ===${NC}"

# 检查是否为 root 用户
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}请不要使用 root 用户运行此脚本${NC}"
    exit 1
fi

# 1. 检查系统
echo -e "${YELLOW}[1/8] 检查系统环境...${NC}"
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo "操作系统: $NAME $VERSION"
else
    echo -e "${RED}无法识别的操作系统${NC}"
    exit 1
fi

# 2. 安装系统依赖
echo -e "${YELLOW}[2/8] 安装系统依赖...${NC}"
if [ -x "$(command -v apt-get)" ]; then
    sudo apt-get update
    sudo apt-get install -y python3.11 python3.11-venv python3-pip git nginx
elif [ -x "$(command -v yum)" ]; then
    sudo yum install -y python311 python3-pip git nginx
else
    echo -e "${RED}不支持的包管理器${NC}"
    exit 1
fi

# 3. 创建项目目录
echo -e "${YELLOW}[3/8] 创建项目目录...${NC}"
PROJECT_DIR="/opt/mingshu-research-lab"
if [ -d "$PROJECT_DIR" ]; then
    echo "项目目录已存在，是否覆盖? (y/n)"
    read -r answer
    if [ "$answer" != "y" ]; then
        echo "取消部署"
        exit 0
    fi
    sudo rm -rf "$PROJECT_DIR"
fi

sudo mkdir -p "$PROJECT_DIR"
sudo chown $USER:$USER "$PROJECT_DIR"

# 4. 克隆代码（或复制本地代码）
echo -e "${YELLOW}[4/8] 获取项目代码...${NC}"
if [ -d ".git" ]; then
    echo "从本地复制代码..."
    cp -r . "$PROJECT_DIR/"
else
    echo "请输入 GitHub 仓库地址（留空跳过）："
    read -r REPO_URL
    if [ -n "$REPO_URL" ]; then
        git clone "$REPO_URL" "$PROJECT_DIR"
    else
        echo -e "${RED}请手动复制代码到 $PROJECT_DIR${NC}"
        exit 1
    fi
fi

cd "$PROJECT_DIR/bazi_ziwei_app"

# 5. 创建虚拟环境
echo -e "${YELLOW}[5/8] 创建 Python 虚拟环境...${NC}"
python3.11 -m venv .venv
source .venv/bin/activate

# 6. 安装依赖
echo -e "${YELLOW}[6/8] 安装 Python 依赖...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# 7. 配置环境变量
echo -e "${YELLOW}[7/8] 配置环境变量...${NC}"
echo "请选择运行模式："
echo "1) public - 公网模式（不保存数据）"
echo "2) local  - 本地模式（持久化数据库）"
read -r MODE_CHOICE

if [ "$MODE_CHOICE" == "2" ]; then
    RUNTIME_MODE="local"
else
    RUNTIME_MODE="public"
fi

echo "是否配置 AI 问答功能? (y/n)"
read -r AI_ANSWER
if [ "$AI_ANSWER" == "y" ]; then
    echo "请输入 Kimi API Key:"
    read -r -s API_KEY
    cat > .env << EOF
MINGSHU_RUNTIME_MODE=$RUNTIME_MODE
MOONSHOT_API_KEY=$API_KEY
MINGSHU_AI_PROVIDER=kimi
MINGSHU_AI_MODEL=kimi-k3
MINGSHU_AI_BASE_URL=https://api.moonshot.cn/v1
MINGSHU_AI_REASONING=low
MINGSHU_AI_TIMEOUT_SECONDS=90
EOF
else
    cat > .env << EOF
MINGSHU_RUNTIME_MODE=$RUNTIME_MODE
EOF
fi

echo -e "${GREEN}环境变量已配置${NC}"

# 8. 创建 systemd 服务
echo -e "${YELLOW}[8/8] 创建系统服务...${NC}"
sudo tee /etc/systemd/system/mingshu.service > /dev/null << EOF
[Unit]
Description=Mingshu Research Lab - 命数研究室
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR/bazi_ziwei_app
Environment="PATH=$PROJECT_DIR/bazi_ziwei_app/.venv/bin"
EnvironmentFile=$PROJECT_DIR/bazi_ziwei_app/.env
ExecStart=$PROJECT_DIR/bazi_ziwei_app/.venv/bin/streamlit run app.py --server.port=8501 --server.address=127.0.0.1 --server.headless=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable mingshu
sudo systemctl start mingshu

# 9. 配置 Nginx（可选）
echo -e "${YELLOW}是否配置 Nginx 反向代理? (y/n)${NC}"
read -r NGINX_ANSWER
if [ "$NGINX_ANSWER" == "y" ]; then
    echo "请输入域名（留空使用服务器 IP）:"
    read -r DOMAIN
    
    if [ -z "$DOMAIN" ]; then
        DOMAIN="_"
    fi
    
    sudo tee /etc/nginx/sites-available/mingshu > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;

    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
        proxy_buffering off;
    }
}
EOF
    
    # 启用站点
    sudo ln -sf /etc/nginx/sites-available/mingshu /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl restart nginx
    
    echo -e "${GREEN}Nginx 配置完成${NC}"
    
    # 询问是否配置 SSL
    if [ "$DOMAIN" != "_" ]; then
        echo -e "${YELLOW}是否配置 HTTPS (Let's Encrypt)? (y/n)${NC}"
        read -r SSL_ANSWER
        if [ "$SSL_ANSWER" == "y" ]; then
            sudo apt-get install -y certbot python3-certbot-nginx
            sudo certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --redirect
            echo -e "${GREEN}HTTPS 配置完成${NC}"
        fi
    fi
fi

# 完成
echo -e "${GREEN}"
echo "================================"
echo "      部署完成！"
echo "================================"
echo -e "${NC}"
echo "服务状态: sudo systemctl status mingshu"
echo "查看日志: sudo journalctl -u mingshu -f"
echo "重启服务: sudo systemctl restart mingshu"
echo ""
if [ "$DOMAIN" != "_" ]; then
    echo "访问地址: http://$DOMAIN"
else
    IP=$(hostname -I | awk '{print $1}')
    echo "访问地址: http://$IP"
fi
echo ""
echo -e "${YELLOW}注意：如果使用云服务器，请在安全组开放 80 和 443 端口${NC}"
