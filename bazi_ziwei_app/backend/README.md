# FastAPI 后端（Phase 1）

该服务是现有 Streamlit 应用的薄 API 层。四柱、起运、强弱、格局等结论仍只由 `core/` 的确定性引擎产生；API 不实现第二套命理规则。

## 本地启动

先安装已固定的运行依赖：

```bash
.venv/bin/python -m pip install -r requirements.txt
```

可信本机开发可使用 local 模式：

```bash
MINGSHU_RUNTIME_MODE=local \
MINGSHU_SESSION_COOKIE_SECURE=false \
MINGSHU_CORS_ORIGINS=http://localhost:3000 \
.venv/bin/python -m uvicorn backend.main:app \
  --host 127.0.0.1 --port 8000 --reload --no-access-log
```

访问：

- 健康检查：`http://127.0.0.1:8000/healthz`
- Swagger UI：`http://127.0.0.1:8000/docs`
- OpenAPI：`http://127.0.0.1:8000/openapi.json`

公网运行必须使用 `MINGSHU_RUNTIME_MODE=public`、HTTPS 和单 worker。public 模式默认生成 `Secure` Cookie，不读取或初始化 SQLite。

## 当前接口

| 方法 | 路径 | 用途 |
|---|---|---|
| `GET` | `/healthz` | 服务、版本与 runtime mode 健康检查 |
| `POST` | `/api/v1/chart/preview` | 严格校验出生输入并生成四柱预览 |
| `POST` | `/api/v1/chart/confirm` | 重新计算并消费当前会话的一次性预览凭据 |
| `GET` | `/api/v1/chart/{chart_id}` | 读取当前会话已确认的 canonical `ChartFacts` |

确认流程必须按顺序执行：

1. 前端提交出生输入到 `preview`。
2. 前端仅在内存中保留返回的 `preview_id`、`input_fingerprint` 和 `chart_fingerprint`。
3. 用户确认后，前端重新提交同一出生输入和三个校验字段到 `confirm`。
4. 前端使用返回的 `chart_id` 读取命盘；确认新盘会立即使旧 `chart_id` 失效。

`input_fingerprint` 是会话与预览绑定的服务端 HMAC 不透明令牌，不是原始 PII 的稳定摘要。预览只能使用一次，不能跨会话确认或重放。

## 前端调用示例

所有请求都需要 `credentials: "include"`，否则浏览器不会保存 HttpOnly 会话 Cookie：

```ts
const apiBase = "http://127.0.0.1:8000";

const birth = {
  name: "访客",
  gender: "男",
  calendar: "solar",
  year: 1994,
  month: 9,
  day: 23,
  hour: null,
  minute: null,
  is_leap_month: false,
  birth_place: "",
  time_label: "时辰不详",
  privacy_consent: true,
};

const previewResponse = await fetch(`${apiBase}/api/v1/chart/preview`, {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(birth),
});
const preview = await previewResponse.json();

const confirmResponse = await fetch(`${apiBase}/api/v1/chart/confirm`, {
  method: "POST",
  credentials: "include",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    ...birth,
    preview_id: preview.preview_id,
    input_fingerprint: preview.input_fingerprint,
    chart_fingerprint: preview.chart_fingerprint,
  }),
});
const confirmed = await confirmResponse.json();

const chartResponse = await fetch(
  `${apiBase}/api/v1/chart/${confirmed.chart_id}`,
  { credentials: "include" },
);
const chart = await chartResponse.json();
```

不要把 `birth`、预览结果或命盘写入 `localStorage`、埋点或前端日志。错误响应统一为：

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求参数无效。",
    "fields": ["body"]
  },
  "request_id": "..."
}
```

## 配置

| 环境变量 | 默认值 | 说明 |
|---|---|---|
| `MINGSHU_RUNTIME_MODE` | `public` | 只有精确值 `local` 才启用可信本机模式 |
| `MINGSHU_CORS_ORIGINS` | localhost 3000/5173 | 逗号分隔的精确 Origin 白名单，不接受 `*` |
| `MINGSHU_SESSION_TTL_SECONDS` | `1800` | 会话和确认命盘的空闲 TTL |
| `MINGSHU_SESSION_CAPACITY` | `4096` | 单进程活动会话硬上限，满载时新预览返回 503 |
| `MINGSHU_SESSION_COOKIE_SECURE` | public 强制 `true` | 仅影响 local 模式的 Cookie 设置 |

`SameSite=Lax` 适合 localhost 不同端口或同一站点的子域部署。如果前端和 API 位于不同注册域名，推荐由 Next.js/反向代理提供同源 `/api`，不要弱化 Cookie 安全策略。

## 运行边界

- 会话、预览凭据和命盘只在进程内存中，重启即丢失。
- 当前不支持多 worker 或多副本；不同进程不共享 Cookie 密钥和会话。
- public API 不注册档案 CRUD，也不访问 SQLite、备份或持久日志。
- API 响应带 `Cache-Control: no-store, private`；前端仍需避免自行持久化出生资料。
- `chart_id` 位于查询 URL 中，Uvicorn 和反向代理必须关闭访问日志或对该路径做脱敏；推荐启动命令已关闭 Uvicorn access log。
- Phase 2 再接入运势接口、AI SSE、报告和 local-only 档案 CRUD。

## 验证

```bash
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest \
  tests/test_backend_api.py tests/test_backend_session_store.py -q

PYTHONPYCACHEPREFIX=/tmp/mingshu-pycache \
  .venv/bin/python -m compileall -q backend
```
