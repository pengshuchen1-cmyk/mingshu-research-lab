#!/bin/bash
# Ubuntu 服务器部署脚本

set -e

echo "================================"
echo "  命数研究室 - Ubuntu 部署"
echo "================================"

# 更新系统
echo ">>> 1. 更新系统..."
sudo apt-get update

# 安装依赖
echo ">>> 2. 安装系统依赖..."
sudo apt-get install -y python3 python3-pip python3-venv git nginx

# 克隆代码（如果本地没有）
if [ ! -d "/opt/mingshu-research-lab" ]; then
    echo ">>> 3. 克隆代码..."
    sudo mkdir -p /opt
    cd /opt
    sudo git clone https://github.com/pengshuchen1-cmyk/mingshu-research-lab.git
    sudo chown -R $USER:$USER /opt/mingshu-research-lab
else
    echo ">>> 3. 更新代码..."
    cd /opt/mingshu-research-lab
    git pull
fi

cd /opt/mingshu-research-lab/bazi_ziwei_app

# 创建虚拟环境
echo ">>> 4. 创建虚拟环境..."
python3 -m venv .venv
source .venv/bin/activate

# 安装 Python 依赖
echo ">>> 5. 安装 Python 依赖..."
pip install --upgrade pip
pip install -r requirements.txt

# 配置环境变量
echo ">>> 6. 配置环境变量..."
cat > .env << 'EOF'
MINGSHU_RUNTIME_MODE=public
# 如果有 Kimi API Key，在下面添加：
# MOONSHOT_API_KEY=sk-你的密钥
# MINGSHU_AI_PROVIDER=kimi
# MINGSHU_AI_MODEL=kimi-k3
EOF

echo "请编辑 /opt/mingshu-research-lab/bazi_ziwei_app/.env 配置 API Key（如需要）"

# 创建 systemd 服务
echo ">>> 7. 创建系统服务..."
sudo tee /etc/systemd/system/mingshu.service > /dev/null << 'EOF'
[Unit]
Description=Mingshu Research Lab
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/mingshu-research-lab/bazi_ziwei_app
Environment="PATH=/opt/mingshu-research-lab/bazi_ziwei_app/.venv/bin"
EnvironmentFile=/opt/mingshu-research-lab/bazi_ziwei_app/.env
ExecStart=/opt/mingshu-research-lab/bazi_ziwei_app/.venv/bin/streamlit run app.py --server.port=8501 --server.address=127.0.0.1 --server.headless=true
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo sed -i "s/\$USER/$USER/g" /etc/systemd/system/mingshu.service

# 启动服务
echo ">>> 8. 启动服务..."
sudo systemctl daemon-reload
sudo systemctl enable mingshu
sudo systemctl start mingshu

# 配置 Nginx
echo ">>> 9. 配置 Nginx..."
sudo tee /etc/nginx/sites-available/mingshu > /dev/null << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/mingshu /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

echo ""
echo "================================"
echo "  部署完成！"
echo "================================"
echo ""
echo "服务状态: sudo systemctl status mingshu"
echo "查看日志: sudo journalctl -u mingshu -f"
echo "访问地址: http://你的服务器IP"
echo ""
echo "重要提示："
echo "1. 确保防火墙开放 80 端口"
echo "2. 如需配置 AI 功能，编辑 /opt/mingshu-research-lab/bazi_ziwei_app/.env"
echo "3. 如需 HTTPS，运行: sudo apt-get install certbot python3-certbot-nginx"
echo ""
