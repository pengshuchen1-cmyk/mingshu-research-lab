# 中国大陆单机部署指南

本指南面向已经完成 ICP 备案的中国大陆云服务器，使用 Docker Compose 运行 Streamlit，并由 Caddy 提供 HTTPS 和反向代理。

## 1. 上线前准备

- 中国大陆轻量应用服务器：建议 2 核 4 GB、40 GB SSD、5 Mbps，Ubuntu LTS。
- 已实名认证且与备案主体一致的域名。
- 已完成 ICP 备案；网站开通后按要求继续办理公安联网备案。
- 云服务器安全组只开放 `22`、`80`、`443`，不要开放 `8501`。
- 域名 A 记录已经指向服务器公网 IP。
- 已安装 Docker Engine 与 Docker Compose 插件。

备案通过前不要通过域名或公网 IP 对外开放网站。可以先在服务器内部完成容器健康检查。

## 2. 上传干净的代码

推荐从 Git 仓库拉取代码，不要把本机整个目录上传到服务器。尤其不要上传 `.venv`、`data/*.db`、`logs/`、`.env` 或 `.streamlit/secrets.toml`。

进入应用目录：

```bash
cd bazi_ziwei_app
```

## 3. 配置服务器密钥

```bash
cp .env.example .env
chmod 600 .env
```

编辑 `.env`，至少填写：

```dotenv
MINGSHU_DOMAIN=你的已备案域名
MOONSHOT_API_KEY=你的服务器端Kimi密钥
MINGSHU_ICP_NUMBER=你的ICP备案号
MINGSHU_PUBLIC_SECURITY_NUMBER=你的公安备案号
```

公安备案号尚未取得时可先留空，取得后再填写并重启容器。`MINGSHU_RUNTIME_MODE` 必须保持为 `public`。真实 `.env` 只保存在服务器，不得提交到 Git。

## 4. 构建并启动

先验证 Compose 配置：

```bash
docker compose config --quiet
```

构建并后台启动：

```bash
docker compose up -d --build
```

查看状态：

```bash
docker compose ps
docker compose logs --tail=100 app
docker compose logs --tail=100 caddy
```

在服务器内部检查 Streamlit：

```bash
docker compose exec -T app curl --fail http://127.0.0.1:8501/_stcore/health
```

预期输出为 `ok`。域名解析生效且 80/443 可访问后，Caddy 会自动申请 HTTPS 证书。

## 5. 验收清单

- `https://你的域名` 可以打开，HTTP 会自动跳转 HTTPS。
- 首页、新建命盘、报告、AI 问答均可正常使用。
- 服务器上没有创建 `data/profiles.db`，公网模式不保存命盘档案。
- PDF 导出可以正确显示中文。
- 刷新或清除会话后，其他用户看不到前一个用户的命盘。
- AI 密钥不出现在网页、Git、容器日志或浏览器请求中。
- 网站底部展示 ICP 备案号并链接工信部备案系统。
- 页面提供隐私说明、清除资料入口、AI 辅助生成标识和使用边界。

## 6. 更新与回滚

更新代码后重新构建：

```bash
docker compose up -d --build
docker image prune -f
```

查看实时日志：

```bash
docker compose logs -f --tail=200
```

停止服务：

```bash
docker compose down
```

不要执行 `docker compose down -v`，否则会删除 Caddy 保存的证书和配置卷。

## 7. 当前架构边界

- 公网版本只在 Streamlit 会话内保存出生资料，30 分钟无操作后清除；服务器重启也会丢失会话。
- AI 限流和预算控制是单进程内存状态，适合当前单机公测；多实例部署时应迁移到 Redis。
- 当前没有账号、订单、支付和永久命盘。增加付费功能前，需要完成相应的主体备案、支付商户、用户协议、隐私与税务准备。
