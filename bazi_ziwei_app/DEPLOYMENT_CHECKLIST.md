# 部署检查清单

## 🚀 部署前检查（必须）

### 1. 代码清理

```bash
# 检查是否有敏感文件
python3 << 'EOF'
from pathlib import Path
from utils.release_privacy import find_private_release_artifacts

artifacts = find_private_release_artifacts(Path.cwd())
if artifacts:
    print("❌ 发现以下敏感文件，请清理：")
    for p in artifacts:
        print(f"   {p}")
    exit(1)
else:
    print("✅ 安全检查通过")
EOF
```

**手动清理：**
```bash
# 删除本地数据库
rm -f data/*.db data/*backup*

# 删除日志
rm -rf logs/*.log

# 删除密钥文件
rm -f .streamlit/secrets.toml

# 清空临时文件
find . -type f -name "*.pyc" -delete
find . -type d -name "__pycache__" -delete
```

### 2. 环境变量配置

**公网模式（推荐）：**
```bash
export MINGSHU_RUNTIME_MODE=public
export MOONSHOT_API_KEY=sk-xxx  # 可选
```

**本地模式（私有部署）：**
```bash
export MINGSHU_RUNTIME_MODE=local
export MOONSHOT_API_KEY=sk-xxx  # 可选
```

### 3. .gitignore 检查

确保以下内容在 `.gitignore` 中：
```
data/*.db
data/*backup*
logs/
.streamlit/secrets.toml
.env
*.log
__pycache__/
.venv/
```

---

## 📦 选择部署方案

### 方案 A：Streamlit Cloud（最简单）

**适用场景：** 个人项目、演示、免费托管

**步骤：**
1. ✅ 代码推送到 GitHub（公开仓库）
2. ✅ 访问 https://share.streamlit.io
3. ✅ 连接 GitHub 账号
4. ✅ 选择仓库和主文件：`bazi_ziwei_app/app.py`
5. ✅ 配置环境变量（Secrets）
6. ✅ 点击 Deploy

**优点：** 零成本、零运维、自动 HTTPS  
**缺点：** 资源限制、必须公开仓库

---

### 方案 B：Docker 部署（推荐）

**适用场景：** 生产环境、独立服务器

**步骤：**
```bash
# 1. 构建镜像
docker build -t mingshu-app .

# 2. 运行容器（公网模式）
docker run -d \
  --name mingshu \
  -p 8501:8501 \
  -e MINGSHU_RUNTIME_MODE=public \
  -e MOONSHOT_API_KEY=$MOONSHOT_API_KEY \
  --restart unless-stopped \
  mingshu-app

# 或使用 docker-compose
docker-compose up -d

# 3. 查看日志
docker logs -f mingshu

# 4. 健康检查
curl http://localhost:8501/_stcore/health
```

**优点：** 环境隔离、易迁移、支持本地模式  
**缺点：** 需要 Docker 知识

---

### 方案 C：VPS 传统部署

**适用场景：** 阿里云、腾讯云等云服务器

**快速部署：**
```bash
# 下载并运行部署脚本
curl -o deploy.sh https://你的仓库/deploy.sh
bash deploy.sh
```

**手动部署：**
```bash
# 1. 安装依赖
sudo apt-get update
sudo apt-get install -y python3.11 python3-venv git nginx

# 2. 克隆代码
cd /opt
git clone https://你的仓库.git
cd mingshu-research-lab/bazi_ziwei_app

# 3. 创建虚拟环境
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 4. 配置 systemd
sudo cp mingshu.service /etc/systemd/system/
sudo systemctl enable mingshu
sudo systemctl start mingshu

# 5. 配置 Nginx
sudo cp nginx.conf /etc/nginx/sites-available/mingshu
sudo ln -s /etc/nginx/sites-available/mingshu /etc/nginx/sites-enabled/
sudo systemctl restart nginx
```

---

## 🔒 安全配置

### 1. 防火墙设置

```bash
# Ubuntu/Debian (UFW)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# CentOS/RHEL (Firewalld)
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

### 2. Nginx 安全加固

```nginx
# 限流配置
limit_req_zone $binary_remote_addr zone=mingshu:10m rate=10r/s;

server {
    # 限制请求频率
    limit_req zone=mingshu burst=20 nodelay;
    
    # 隐藏版本信息
    server_tokens off;
    
    # 防止点击劫持
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # HTTPS 重定向
    if ($scheme != "https") {
        return 301 https://$host$request_uri;
    }
}
```

### 3. SSL 证书（Let's Encrypt）

```bash
# 安装 certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 自动配置 HTTPS
sudo certbot --nginx -d 你的域名.com

# 测试自动续期
sudo certbot renew --dry-run
```

---

## 📊 监控配置

### 1. 服务监控

```bash
# 查看服务状态
systemctl status mingshu

# 实时日志
journalctl -u mingshu -f

# 错误日志
journalctl -u mingshu -p err -n 50
```

### 2. 资源监控

```bash
# 安装 htop
sudo apt-get install htop

# 查看资源占用
htop

# Docker 资源监控
docker stats mingshu
```

### 3. 日志分析

```bash
# 统计请求量
journalctl -u mingshu --since today | grep -c "GET"

# 查找错误
journalctl -u mingshu --since today | grep "ERROR"
```

---

## 🔄 备份策略（本地模式）

### 1. 数据库自动备份

```bash
# 创建备份脚本
cat > /opt/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/opt/backups/mingshu
mkdir -p $BACKUP_DIR

# 备份数据库
cp /opt/mingshu-research-lab/bazi_ziwei_app/data/profiles.db \
   $BACKUP_DIR/profiles_${DATE}.db

# 压缩备份
gzip $BACKUP_DIR/profiles_${DATE}.db

# 保留最近 30 天
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "备份完成: profiles_${DATE}.db.gz"
EOF

chmod +x /opt/backup.sh
```

### 2. 添加定时任务

```bash
# 每天凌晨 3 点备份
(crontab -l 2>/dev/null; echo "0 3 * * * /opt/backup.sh >> /var/log/mingshu-backup.log 2>&1") | crontab -
```

### 3. 恢复数据

```bash
# 停止服务
sudo systemctl stop mingshu

# 恢复数据库
gunzip -c /opt/backups/mingshu/profiles_YYYYMMDD_HHMMSS.db.gz > \
  /opt/mingshu-research-lab/bazi_ziwei_app/data/profiles.db

# 启动服务
sudo systemctl start mingshu
```

---

## ✅ 部署验证

### 1. 功能测试

```bash
# 健康检查
curl http://localhost:8501/_stcore/health
# 预期输出: {"status": "ok"}

# 访问首页
curl -I http://localhost:8501
# 预期输出: HTTP/1.1 200 OK
```

### 2. 性能测试

```bash
# 安装 ab（Apache Bench）
sudo apt-get install apache2-utils

# 压力测试（100 并发，1000 请求）
ab -n 1000 -c 100 http://localhost:8501/
```

### 3. 错误检查

```bash
# 检查 Python 错误
journalctl -u mingshu --since today | grep -i "error\|exception"

# 检查内存泄漏
watch -n 5 'docker stats mingshu --no-stream'
```

---

## 🚨 常见问题

### 问题 1：端口被占用

```bash
# 查看占用进程
sudo lsof -i :8501

# 杀死进程
sudo kill -9 <PID>
```

### 问题 2：内存不足

```bash
# 查看内存使用
free -h

# 限制 Docker 内存
docker update --memory 2g mingshu
```

### 问题 3：PDF 导出失败

```bash
# 安装中文字体
sudo apt-get install fonts-noto-cjk fonts-wqy-zenhei

# 重启服务
sudo systemctl restart mingshu
```

### 问题 4：AI 问答不可用

```bash
# 检查环境变量
echo $MOONSHOT_API_KEY

# 测试 API 连接
curl -H "Authorization: Bearer $MOONSHOT_API_KEY" \
  https://api.moonshot.cn/v1/models
```

---

## 📝 部署完成后

- [ ] 服务正常运行
- [ ] 页面可以访问
- [ ] HTTPS 配置完成（生产环境）
- [ ] 防火墙规则设置
- [ ] 备份脚本测试
- [ ] 监控告警配置
- [ ] 域名解析完成
- [ ] 性能测试通过

---

## 📞 技术支持

- 查看日志：`sudo journalctl -u mingshu -f`
- 重启服务：`sudo systemctl restart mingshu`
- 查看状态：`sudo systemctl status mingshu`

---

**部署完成！🎉**
