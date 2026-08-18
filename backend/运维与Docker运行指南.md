# 明枢后端：Docker、服务器部署与远程调试

本文不绑定任何个人服务器。命令中的 `<SERVER_HOST>`、`<SSH_USER>` 和 `<PROCESS_ID>` 都是占位符，执行前替换为自己的值。

## 1. 默认安全拓扑

- 完整栈包含 FastAPI、MySQL 8.4、Redis 7 和一次性 Alembic 迁移任务。
- API、MySQL、Redis 默认只发布到宿主机 `127.0.0.1`，不会直接暴露到公网。
- 容器内部通过 Docker 网络使用 `mysql:3306` 和 `redis:6379` 通信。
- 对外上线时，仅由 Nginx/Caddy 等反向代理访问 API；不要向公网开放 `3306` 或 `6379`。
- 远程开发通过 SSH 加密隧道连接依赖，不需要修改服务器防火墙开放数据库端口。

> 从 PostgreSQL 切换到 MySQL 时，旧数据必须另行迁移和校验，不能复用 PostgreSQL 数据卷。

## 2. 新开发者在本机快速启动

前置条件：Git、Docker Engine/Desktop 和 Docker Compose v2。

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

Compose 会自动读取与 `docker-compose.yml` 同目录的 `.env`，将其中的 `MYSQL_*`、`REDIS_*` 等值替换到 `${变量名}`，并通过 `env_file: .env` 把应用配置传入 API 和迁移容器。`.env.example` 的密码只适用于一次性本地开发。

启动顺序为 MySQL/Redis 健康检查、`alembic upgrade head`、API。验证：

```bash
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
```

- Swagger：<http://127.0.0.1:8000/docs>
- OpenAPI：<http://127.0.0.1:8000/openapi.json>

查看日志、再次迁移、停止：

```bash
docker compose logs -f --tail=200 api
docker compose run --rm migrate
docker compose down
```

`docker compose down` 会保留命名数据卷。不要随意执行 `docker compose down -v`，它会删除本机 MySQL 和 Redis 数据。

需要代码热更新时：

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## 3. 通用服务器 Docker 部署

以下示例使用 `/opt/mingshu-backend`，也可以选择其他目录并同步修改命令。SSH 用户必须有 Docker 权限。

在服务器准备目录：

```bash
sudo mkdir -p /opt/mingshu-backend
sudo chown -R "$(id -un):$(id -gn)" /opt/mingshu-backend
```

从项目根目录上传公开的后端文件（把占位符替换为自己的服务器信息）：

```bash
scp -r backend/app backend/alembic backend/scripts <SSH_USER>@<SERVER_HOST>:/opt/mingshu-backend/
scp backend/alembic.ini backend/Dockerfile backend/requirements-prod.txt backend/docker-compose.yml backend/.dockerignore backend/.env.production.example <SSH_USER>@<SERVER_HOST>:/opt/mingshu-backend/
```

服务器首次配置有两种方式，任选其一。

自动生成随机密钥（推荐）：

```bash
ssh <SSH_USER>@<SERVER_HOST>
cd /opt/mingshu-backend
python3 scripts/bootstrap_remote_env.py
```

脚本默认在当前目录创建权限为 `600` 的 `.env` 和 `.env.local-client`，不会打印密钥，也不会覆盖已有文件。从其他目录调用时可设置：

```bash
MINGSHU_DEPLOY_DIR=/opt/mingshu-backend python3 /path/to/bootstrap_remote_env.py
```

或手工创建：

```bash
cd /opt/mingshu-backend
cp .env.production.example .env
chmod 600 .env
editor .env
```

手工配置时，三个基础设施密码必须各不相同。可分别执行三次 `openssl rand -hex 32`，把 MySQL/Redis 密码同时更新到对应 URL。JWT 密钥另行生成；`CORS_ORIGINS` 只能填写可信前端域名。

启动和验证：

```bash
cd /opt/mingshu-backend
docker compose config --quiet
docker compose up -d --build
docker compose ps
docker compose logs --tail=100 migrate
curl -fsS http://127.0.0.1:8000/healthz
curl -fsS http://127.0.0.1:8000/readyz
```

默认 API 仅监听服务器 `127.0.0.1:8000`。公开服务需要域名、TLS 证书以及 Nginx/Caddy 对 `127.0.0.1:8000` 的反向代理；仓库暂未提供代理和证书配置。

## 4. 远程 MySQL/Redis 的 SSH 隧道（可选）

先确保远程完整栈正在运行。服务器的 MySQL/Redis 端口仍只绑定回环地址。

Windows PowerShell：

```powershell
ssh -N `
  -L 127.0.0.1:13306:127.0.0.1:3306 `
  -L 127.0.0.1:16379:127.0.0.1:6379 `
  -o ServerAliveInterval=30 `
  -o ExitOnForwardFailure=yes `
  <SSH_USER>@<SERVER_HOST>
```

Linux/macOS：

```bash
ssh -N \
  -L 127.0.0.1:13306:127.0.0.1:3306 \
  -L 127.0.0.1:16379:127.0.0.1:6379 \
  -o ServerAliveInterval=30 \
  -o ExitOnForwardFailure=yes \
  <SSH_USER>@<SERVER_HOST>
```

命令保持运行且没有输出是正常现象，按 `Ctrl+C` 关闭。Windows 可检查：

```powershell
Test-NetConnection 127.0.0.1 -Port 13306
Test-NetConnection 127.0.0.1 -Port 16379
```

如需 Windows 后台隧道：

```powershell
$sshArgs = @(
  "-N",
  "-L", "127.0.0.1:13306:127.0.0.1:3306",
  "-L", "127.0.0.1:16379:127.0.0.1:6379",
  "-o", "BatchMode=yes",
  "-o", "ExitOnForwardFailure=yes",
  "-o", "ServerAliveInterval=30",
  "<SSH_USER>@<SERVER_HOST>"
)
$tunnel = Start-Process ssh.exe -ArgumentList $sshArgs -WindowStyle Hidden -PassThru
$tunnel.Id
```

使用 `Stop-Process -Id <PROCESS_ID>` 停止后台隧道。停止隧道不会停止服务器容器。

### 本机原生 Python 连接远程依赖

安全取得服务器 `.env` 中的应用数据库密码和 Redis 密码；不要复制或共享 root 密码。然后：

```powershell
cd backend
Copy-Item .env.remote.example .env
# 编辑 .env 中的占位密码
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

Linux/macOS 将复制命令换成 `cp .env.remote.example .env`，激活命令换成 `source .venv/bin/activate`。手工运行迁移会修改远程数据库，应由团队统一协调。

### 本机仅运行 API 容器（Docker Desktop）

此方案面向 Windows/macOS 的 Docker Desktop。`host.docker.internal` 在原生 Linux Docker Engine 中不保证能访问仅绑定宿主机回环地址的 SSH 隧道；Linux 推荐直接运行原生 Python，或由运维人员另行设计受限的 host-gateway 隧道。保持隧道运行，然后：

```bash
cp .env.remote-docker.example .env
# 编辑 .env 中的占位密码
docker compose -f docker-compose.remote-dev.yml up --build
```

Windows 使用 `Copy-Item .env.remote-docker.example .env`。停止：

```bash
docker compose -f docker-compose.remote-dev.yml down
```

此编排只启动迁移和 API，不会在本机创建 MySQL 或 Redis。

## 5. 服务器日常运维

重新构建、迁移并更新 API：

```bash
cd /opt/mingshu-backend
docker compose build
docker compose run --rm migrate
docker compose up -d --no-deps --force-recreate api
docker compose ps
```

日志、停止和再次启动：

```bash
docker compose logs -f --tail=200 api
docker compose logs --tail=200 mysql redis
docker compose down
docker compose up -d
```

## 6. MySQL 备份和恢复

备份文件可能包含敏感数据，不应提交到 Git：

```bash
cd /opt/mingshu-backend
docker compose exec -T mysql sh -c 'exec mysqldump -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" --single-transaction --routines --triggers "$MYSQL_DATABASE"' > mingshu-$(date +%F-%H%M%S).sql
```

恢复会写入目标数据库，执行前确认备份和目标环境：

```bash
docker compose exec -T mysql sh -c 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"' < mingshu-YYYY-MM-DD-HHMMSS.sql
```

Docker 数据卷不是备份。应将备份加密保存到另一台机器或对象存储，并定期做恢复演练。

## 7. 故障排查

```bash
cd /opt/mingshu-backend
docker compose ps
docker compose logs --tail=200 migrate api mysql redis
docker compose exec mysql sh -c 'mysqladmin ping -h 127.0.0.1 -u"$MYSQL_USER" -p"$MYSQL_PASSWORD"'
docker compose exec redis sh -c 'redis-cli -a "$REDIS_PASSWORD" --no-auth-warning ping'
```

- `Connection refused`：检查隧道和远程容器状态。
- `/readyz` 报数据库未就绪：检查 `DATABASE_URL`、密码和迁移日志。
- `/readyz` 报 Redis 未就绪：检查 `REDIS_URL` 与 `REDIS_PASSWORD` 是否一致。
- 修改 Compose 环境变量后 MySQL 密码未变化：初始化变量只在空数据卷首次启动时生效，应在 MySQL 内显式改密，不要通过删除生产数据卷改密码。

## 8. 提交前隐私检查

真实 `.env` 和 `.env.*` 已被 `.gitignore` 排除，只有 `*.example` 模板允许提交。提交前执行：

```bash
git status --short -- backend
git status --ignored --short -- backend
git diff --cached -- backend
```

确认没有服务器 IP、SSH 用户、私钥、密码、数据库导出、日志或本机绝对路径。不要使用 `git add -f` 强行添加被忽略的配置文件。
