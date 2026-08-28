# Mingshu 独立后端

基于 FastAPI、SQLAlchemy 2 异步 ORM、MySQL 8.4、Alembic、Redis 和 JWT。认证同时支持短信验证码注册/登录和手机号密码登录，并提供设置密码、修改密码与短信找回密码接口。应用使用 `asyncmy`，数据库迁移使用同步 `PyMySQL`。SQLite 只用于隔离测试，正常运行必须配置 MySQL 和 Redis。命盘接口使用后端自有的 `app/bazi` 确定性排盘包，不依赖旧 Streamlit 应用。

版本化业务接口统一放在 `app/api/v1`：`auth.py` 负责认证，`users.py` 负责当前用户与点数，`admin.py` 负责管理端，`payments.py` 负责支付，`chart_profiles.py` 负责命理档案与命盘，`fortunes.py` 负责个人年度与流月运势，`guidance.py` 负责公共今日指引，`router.py` 统一聚合后交给 `app/main.py` 挂载。无版本号的 `/healthz`、`/readyz` 是基础设施探针，保留在应用入口。

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

Dockerfile 的构建上下文就是 `backend` 目录，命盘核心与规则已经包含在后端的 `app/bazi` 中。后端目录可以独立复制、构建和部署，不需要保留 `bazi_ziwei_app`。

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

## 命理档案与命盘

登录用户可以保存多个命理档案。调用顺序为 `POST /api/v1/chart-profiles/preview` 预览并取得双指纹，再调用 `POST /api/v1/chart-profiles` 确认保存。新建后允许立即进行第一次修改；之后个人信息默认每 30 天可修改一次，由 `PROFILE_EDIT_COOLDOWN_DAYS` 配置。修改成功时命盘快照会在同一事务中重建。完整字段和示例见 [API.md](API.md#7-命理档案与命盘接口)。

## 今日指引

`GET /api/v1/guidance/today` 返回旧应用“今日”页面的公共日建议和年度节奏，无需登录，也不会读取姓名、出生资料、档案或命盘。省略参数时按 `Asia/Shanghai` 的当天计算，也可使用 `target_date`、`target_year` 查询指定日期和年度。完整响应字段见 [API.md](API.md#8-今日指引接口)。

## 个人运势

登录用户可调用 `GET /api/v1/chart-profiles/{profile_id}/fortune?target_year=2026`，从自己已保存的命盘快照生成年度总览、专项分析、目标年份大运背景和 12 个月流月事件。旧版年度、流月、叙事和完整事件规则已迁入后端自有 `app/fortune`，并由多档案、多年份合同测试保护；运行时不依赖旧 `bazi_ziwei_app`。结果实时派生，不另建运势数据表。完整参数、响应字段和 ApiPost 测试步骤见 [API.md](API.md#9-个人运势接口)。

## 深度命理能力

后端还提供命盘总览与五行喜忌、完整大运、六十甲子、事业/财富/感情专项报告、Markdown/TXT/PDF 导出、合婚、紫微斗数和带本地安全兜底的 AI 问答。AI 问答通过 `/api/v1/ai-conversations` 创建持久化会话，问题、回答和调用元数据保存在 MySQL，后端从数据库读取可信历史。相关计算与规则均在 `app/analysis`、`app/reports`、`app/ziwei` 和 `app/ai` 内，运行时不读取旧 Streamlit 项目。全部路径、输入和输出示例见 [API.md](API.md#10-命盘综合分析接口)。

## 登录方式

短信验证码仍是注册入口：先调用 `POST /api/v1/auth/otp/login/code` 获取登录验证码，首次调用 `POST /api/v1/auth/otp/login` 会自动创建用户。登录后可调用 `PUT /api/v1/auth/password` 设置密码，之后可使用 `POST /api/v1/auth/password/login` 登录；忘记密码时通过密码重置专用短信验证码找回。密码变更后旧 JWT 会失效，客户端需要保存接口返回的新令牌。完整参数见 [API.md](API.md#3-认证接口)。

## 上线前限制

生产环境必须使用至少 32 字符的随机 JWT 密钥并设置精确的 `CORS_ORIGINS`。真实短信、微信扫码、微信/支付宝支付和月度订阅适配器尚未实现；生产环境未注册短信适配器时会返回 `503`，不会把验证码返回给客户端。首个管理员帐号也需要通过受控运维流程授予 `admin` 角色。
