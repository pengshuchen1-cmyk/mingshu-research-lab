# 命数研究室 - 线上部署指南

## 一、部署准备清单

### 1.1 环境准备

#### Python 环境
- Python 3.10+ （推荐 3.11）
- 虚拟环境管理（venv 或 conda）

#### 系统依赖
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv

# CentOS/RHEL
sudo yum install -y python3 python3-pip python3-venv
```

### 1.2 部署模式选择

项目支持两种运行模式：

| 模式 | 环境变量 | 数据存储 | 适用场景 |
|------|---------|---------|---------|
| **公网模式** | `MINGSHU_RUNTIME_MODE=public` | 会话内存（30分钟失效） | 公开网站，无用户注册 |
| **本地模式** | `MINGSHU_RUNTIME_MODE=local` | SQLite 数据库持久化 | 内网/私有部署，需要保存命盘 |

**重要：**
- 公网模式会自动阻断数据库、日志文件的读写
- 公网模式用户数据在 30 分钟无操作后自动清除
- 公网模式不支持命盘档案功能

---

## 二、部署方案

### 方案 A：Streamlit Cloud（推荐入门）

**优点：** 免费、零运维、自动 HTTPS  
**缺点：** 资源限制、需要公开 GitHub 仓库

#### 步骤：

1. **准备 GitHub 仓库**
```bash
# 确保代码已推送到 GitHub
git init
git add .
git commit -m "Initial commit for deployment"
git branch -M main
git remote add origin https://github.com/你的用户名/mingshu-research-lab.git
git push -u origin main
```

2. **清理敏感文件**（公网模式必须）
```bash
# 删除本地数据库和日志
rm -rf data/*.db data/*backup* logs/*

# 确认 .gitignore 包含：
cat >> .gitignore << 'EOF'
data/*.db
data/*backup*
logs/
.streamlit/secrets.toml
EOF
```

3. **配置 Streamlit Cloud**
   - 访问 https://share.streamlit.io
   - 登录 GitHub 授权
   - 点击 "New app"
   - 选择仓库：`你的用户名/mingshu-research-lab`
   - 主文件路径：`bazi_ziwei_app/app.py`
   - 高级设置 → 环境变量：
     ```
     MINGSHU_RUNTIME_MODE=public
     MOONSHOT_API_KEY=你的Kimi密钥（可选）
     MINGSHU_AI_PROVIDER=kimi
     MINGSHU_AI_MODEL=kimi-k3
     ```
   - 点击 Deploy

4. **访问地址**  
   部署后会获得类似 `https://你的应用名.streamlit.app` 的地址

---

### 方案 B：Docker 容器化部署（推荐生产）

**优点：** 环境隔离、易于迁移、支持本地模式  
**缺点：** 需要服务器和 Docker 知识

#### 1. 创建 Dockerfile

```bash
cd /Users/hongzezhang/workspace/mingshu-research-lab/bazi_ziwei_app
```

创建 `Dockerfile`：

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（PDF 导出需要）
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建数据和日志目录
RUN mkdir -p data logs

# 暴露端口
EXPOSE 8501

# 健康检查
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 启动命令
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

#### 2. 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  mingshu-app:
    build: .
    container_name: mingshu-research-lab
    ports:
      - "8501:8501"
    environment:
      # 选择运行模式（public 或 local）
      - MINGSHU_RUNTIME_MODE=public
      
      # AI 配置（可选）
      - MINGSHU_AI_PROVIDER=kimi
      - MOONSHOT_API_KEY=${MOONSHOT_API_KEY}
      - MINGSHU_AI_MODEL=kimi-k3
      - MINGSHU_AI_BASE_URL=https://api.moonshot.cn/v1
      - MINGSHU_AI_REASONING=low
      - MINGSHU_AI_TIMEOUT_SECONDS=90
    
    volumes:
      # 本地模式：持久化数据库和日志
      - ./data:/app/data
      - ./logs:/app/logs
    
    restart: unless-stopped
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

#### 3. 部署命令

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 4. 访问地址
- 本地：http://localhost:8501
- 服务器：http://你的服务器IP:8501

---

### 方案 C：传统 VPS 部署

**适用：** 阿里云、腾讯云、AWS 等云服务器

#### 1. 服务器配置要求
- CPU: 2核+
- 内存: 4GB+
- 磁盘: 20GB+
- 系统: Ubuntu 20.04+ / CentOS 8+

#### 2. 部署脚本

```bash
#!/bin/bash
# deploy.sh - 自动部署脚本

set -e

echo "=== 命数研究室部署脚本 ==="

# 1. 安装系统依赖
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv python3-pip git nginx

# 2. 克隆项目
cd /opt
sudo git clone https://github.com/你的用户名/mingshu-research-lab.git
cd mingshu-research-lab/bazi_ziwei_app

# 3. 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate

# 4. 安装依赖
pip install --upgrade pip
pip install -r requirements.txt

# 5. 设置环境变量
cat > .env << 'EOF'
MINGSHU_RUNTIME_MODE=public
MOONSHOT_API_KEY=你的密钥
MINGSHU_AI_PROVIDER=kimi
MINGSHU_AI_MODEL=kimi-k3
EOF

# 6. 创建 systemd 服务
sudo tee /etc/systemd/system/mingshu.service > /dev/null << 'EOF'
[Unit]
Description=Mingshu Research Lab
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/mingshu-research-lab/bazi_ziwei_app
Environment="PATH=/opt/mingshu-research-lab/bazi_ziwei_app/.venv/bin"
EnvironmentFile=/opt/mingshu-research-lab/bazi_ziwei_app/.env
ExecStart=/opt/mingshu-research-lab/bazi_ziwei_app/.venv/bin/streamlit run app.py --server.port=8501 --server.address=127.0.0.1
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 7. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable mingshu
sudo systemctl start mingshu

echo "=== 部署完成 ==="
echo "检查服务状态: sudo systemctl status mingshu"
echo "查看日志: sudo journalctl -u mingshu -f"
```

#### 3. 配置 Nginx 反向代理（支持 HTTPS）

```bash
sudo tee /etc/nginx/sites-available/mingshu << 'EOF'
server {
    listen 80;
    server_name 你的域名.com;

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

# 启用站点
sudo ln -s /etc/nginx/sites-available/mingshu /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# 配置 SSL（Let's Encrypt）
sudo apt-get install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名.com
```

---

## 三、安全加固

### 3.1 公网模式必检项

```bash
# 运行安全检查脚本
python3 << 'EOF'
from pathlib import Path
from utils.release_privacy import find_private_release_artifacts

root = Path.cwd()
artifacts = find_private_release_artifacts(root)

if artifacts:
    print("❌ 发现隐私文件，禁止公网发布：")
    for path in artifacts:
        print(f"   - {path.relative_to(root)}")
    exit(1)
else:
    print("✅ 公网发布安全检查通过")
EOF
```

### 3.2 环境变量加密

不要在代码中硬编码密钥，使用环境变量：

```bash
# 生产环境：使用密钥管理服务
export MOONSHOT_API_KEY=$(aws secretsmanager get-secret-value --secret-id mingshu/kimi-key --query SecretString --output text)
```

### 3.3 访问限制

```nginx
# Nginx 限流配置
limit_req_zone $binary_remote_addr zone=mingshu_limit:10m rate=10r/s;

server {
    location / {
        limit_req zone=mingshu_limit burst=20 nodelay;
        # ... 其他配置
    }
}
```

---

## 四、监控与维护

### 4.1 日志监控

```bash
# Docker 环境
docker-compose logs -f --tail=100

# Systemd 环境
sudo journalctl -u mingshu -f -n 100
```

### 4.2 性能监控

```bash
# 安装监控工具
pip install streamlit-analytics

# 在 app.py 中添加：
# import streamlit_analytics
# with streamlit_analytics.track():
#     main()
```

### 4.3 备份策略（本地模式）

```bash
# 每日自动备份脚本
cat > /opt/backup_mingshu.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups/mingshu"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /opt/mingshu-research-lab/bazi_ziwei_app/data/profiles.db \
   $BACKUP_DIR/profiles_${DATE}.db

# 保留最近 30 天的备份
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
EOF

chmod +x /opt/backup_mingshu.sh

# 添加到 crontab（每天凌晨 3 点）
echo "0 3 * * * /opt/backup_mingshu.sh" | sudo crontab -
```

---

## 五、常见问题

### 5.1 部署后打不开页面

```bash
# 检查服务状态
sudo systemctl status mingshu

# 检查端口占用
sudo lsof -i :8501

# 查看详细日志
sudo journalctl -u mingshu -n 50 --no-pager
```

### 5.2 内存不足

```python
# 在 app.py 开头添加内存优化配置：
import streamlit as st

st.set_page_config(
    page_title="命数研究室",
    layout="wide",
    initial_sidebar_state="collapsed"  # 减少初始加载
)

# 限制缓存大小
@st.cache_data(ttl=3600, max_entries=50)
def cached_function():
    pass
```

### 5.3 PDF 导出失败

```bash
# Docker 环境需要中文字体
RUN apt-get install -y fonts-noto-cjk fonts-wqy-zenhei

# 系统环境
sudo apt-get install -y fonts-noto-cjk
```

---

## 六、成本估算

| 方案 | 月成本 | 适用场景 |
|------|--------|---------|
| Streamlit Cloud | ¥0 | 个人项目、演示 |
| 阿里云轻量服务器 2C4G | ¥60-100 | 小型站点 |
| 腾讯云标准服务器 4C8G | ¥200-400 | 中等流量 |
| Docker + CDN | ¥150-300 | 推荐方案 |

---

## 七、检查清单

部署前请确认：

- [ ] 选择了运行模式（public/local）
- [ ] 清理了 `.db` `.log` 等隐私文件（公网模式）
- [ ] 配置了环境变量（AI 密钥等）
- [ ] 更新了 `.gitignore` 文件
- [ ] 测试了健康检查接口 `/_stcore/health`
- [ ] 配置了 HTTPS（生产环境）
- [ ] 设置了访问限流
- [ ] 配置了自动备份（本地模式）
- [ ] 添加了监控告警

---

## 八、快速启动命令

```bash
# 开发环境
source .venv/bin/activate
streamlit run app.py

# 公网模式（Docker）
docker-compose -f docker-compose.public.yml up -d

# 本地模式（Docker）
docker-compose -f docker-compose.local.yml up -d

# 查看状态
curl http://localhost:8501/_stcore/health
```

---

## 九、技术支持

- 项目文档：`README.md`
- API 配置：`PRIVACY.md`
- 变更日志：`CHANGELOG.md`

---

**免责声明：**  
本系统涉及传统命理内容，仅供文化研究和个人参考，不应作为医疗、法律、投资等重大决策的依据。
