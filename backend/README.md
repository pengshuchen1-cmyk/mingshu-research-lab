# Mingshu 独立后端

基于 FastAPI、SQLAlchemy 2 异步 ORM、MySQL 8.4、Alembic、Redis 和 JWT。应用使用 `asyncmy`，数据库迁移使用同步 `PyMySQL`。SQLite 只用于隔离测试，正常运行必须配置 MySQL 和 Redis。

## Docker 一键启动（推荐）

`.env.example` 只包含可公开的、一次性本地开发值。复制后即可启动 API、MySQL、Redis 和数据库迁移；不要将这些示例密码用于生产环境。

Windows PowerShell：

```powershell
cd backend
Copy-Item .env.example .env
docker compose up -d --build
docker compose ps
```

Linux/macOS：

```bash
cd backend
cp .env.example .env
docker compose up -d --build
docker compose ps
```

首次启动会自动执行 `alembic upgrade head`，无需另外运行迁移。验证服务：

```text
Swagger       http://127.0.0.1:8000/docs
健康检查      http://127.0.0.1:8000/healthz
数据库/Redis  http://127.0.0.1:8000/readyz
OpenAPI       http://127.0.0.1:8000/openapi.json
```

查看日志和停止（默认保留数据库卷）：

```bash
docker compose logs -f --tail=200 api
docker compose down
```

开发时启用代码热更新：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## 原生 Python 开发

原生 Python 仍需要另行提供可用的 MySQL 和 Redis，并把 `.env` 中的地址配置成宿主机可访问的地址。不要同时启动上面的完整栈 API（会占用同一个 `8000` 端口），也不能让原生 Python 使用仅在 Docker 网络内可解析的 `mysql`、`redis` 主机名。推荐使用运维文档中的通用 SSH 隧道方案连接开发依赖。Python 3.11+：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Linux/macOS 激活环境使用 `source .venv/bin/activate`，其余命令相同。

## 配置与文档

- `.env.example`：完整本地 Docker 栈，可直接复制。
- `.env.production.example`：生产配置占位模板，所有密钥必须替换。
- `.env.remote.example`：本机原生 Python 通过 SSH 隧道连接远程依赖。
- `.env.remote-docker.example`：本机 API 容器通过 SSH 隧道连接远程依赖。
- [API.md](API.md)：接口、参数和示例。
- [运维与Docker运行指南.md](运维与Docker运行指南.md)：生产部署、SSH 隧道和备份。

真实 `.env`、`.env.*`、导出的 `openapi.json`、本地数据库和虚拟环境均被 Git 忽略；`*.example` 配置模板会被保留。提交前建议执行 `git status --ignored -- backend` 再次确认。

## 上线前限制

生产环境必须使用至少 32 字符的随机 JWT 密钥并设置精确的 `CORS_ORIGINS`。真实短信、微信扫码、微信/支付宝支付和月度订阅适配器尚未实现；生产环境未注册短信适配器时会返回 `503`，不会把验证码返回给客户端。首个管理员帐号也需要通过受控运维流程授予 `admin` 角色。
