# API 联调文档

> 审计基准：根目录独立后端 `backend/`，不是旧的 `bazi_ziwei_app/backend/`。
>
> 审计日期：2026-08-21
>
> 证据来源：实际 FastAPI 注册链、Pydantic schema、依赖注入、service、ORM model、异常目录、运行时 OpenAPI、测试客户端实测和 `backend/tests/`。`backend/API.md` 只用于交叉核对。

> 配套测试执行文档：[`API_FUNCTION_TEST.md`](API_FUNCTION_TEST.md)，覆盖全部 30 个 HTTP API，共 227 条功能、异常、权限、边界和并发用例。

## 联调结论摘要

1. 运行时共注册 **30 个 HTTP API**：28 个 `/api/v1` 业务接口，加 `/healthz`、`/readyz` 两个运维接口。
2. Method 数量：**GET 12、POST 14、PUT 3、PATCH 1、DELETE 0**。
3. 普通用户前端的最小 P0 主流程需要接 **8 个接口**：密码注册、密码登录、Token 刷新、当前用户、命盘预览、创建档案、档案列表、档案详情。
4. **没有 SSE、WebSocket、StreamingResponse、轮询任务或文件上传接口**。
5. 鉴权使用 **JWT Bearer Token**，不是 Cookie Session；access token 默认 30 分钟，refresh token 默认 30 天。
6. 最需要注意的 3 个联调问题：
   - 密码注册按当前产品要求不验证手机号归属；OTP 登录/重置仍依赖尚未接入的生产短信服务。
   - 14 个接口没有 `response_model`，Swagger/OpenAPI 的成功响应 schema 是 `{}`；本文按实际返回展开，但后端契约仍需补强。
   - 普通业务错误仅返回 `{"detail":"..."}`，内部错误码不下发；默认 422 还会在 `detail[].input` 回显提交值，包括非法密码值。

验证结果：运行时 OpenAPI 30 个操作；后端测试结果见附录 B；`docker compose --env-file .env.example config --quiet` 通过。

---

## 1. 后端整体 API 架构

### 1.1 实际应用入口和 prefix

入口：`backend/app/main.py`。

```text
app.main:app
├── include_router(app.api.v1.router)
│   └── prefix=/api/v1
│       ├── /auth                 → auth.py
│       ├── /me, /points/*        → users.py
│       ├── /admin/*              → admin.py
│       ├── /payments/*           → payments.py
│       └── /chart-profiles/*     → chart_profiles.py
├── GET /healthz
└── GET /readyz
```

完整注册链：

```text
backend/app/main.py
→ app.include_router(api_v1_router)
→ backend/app/api/v1/router.py (prefix="/api/v1")
→ include_router(auth/users/admin/payments/chart_profiles)
→ 各模块自身 prefix + 路由 path
```

本文所有 URL 已计算完嵌套 prefix，可以直接作为前端请求路径。

### 1.2 本地地址和启动边界

默认本地地址：

```text
http://127.0.0.1:8000
```

推荐按 `backend/README.md` 启动完整 Docker 栈：

```bash
cd backend
cp .env.example .env
docker compose up -d --build
```

代码中的 API Base URL 没有固定公网域名。前端应使用环境变量，例如：

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
```

### 1.3 技术组件

| 组件 | 实际用途 |
|---|---|
| FastAPI | 路由、依赖注入、OpenAPI |
| Pydantic v2 | request/部分 response 校验 |
| SQLAlchemy async | MySQL 异步 ORM；测试使用 SQLite |
| Alembic | 数据库迁移，当前 4 个 migration |
| Redis | 当前主要用于 `/readyz` 就绪检查；验证码限流实际落在数据库，不在 Redis |
| PyJWT HS256 | access/refresh token |
| phonenumbers | 手机号解析并转换为 E.164 |
| 后端内置 `app/bazi` | 确定性八字排盘，不依赖旧 Streamlit 应用 |

### 1.4 CORS

代码位置：`backend/app/main.py:17-23`。

- `allow_origins=settings.cors_origins`，由 `CORS_ORIGINS` 环境变量配置。
- `allow_methods=["*"]`、`allow_headers=["*"]`。
- `allow_credentials=False`。
- 本项目使用 Authorization Header，不依赖跨域 Cookie，因此 fetch 不需要 `credentials: "include"`。
- 前端 Origin 仍必须加入 `CORS_ORIGINS`，否则浏览器会在 CORS 层拦截响应。

### 1.5 自动文档端点

以下由 FastAPI 自动注册，不计入 30 个业务/运维操作：

| Method | URL | 用途 |
|---|---|---|
| GET/HEAD | `/docs` | Swagger UI |
| GET/HEAD | `/docs/oauth2-redirect` | Swagger OAuth 跳转辅助页 |
| GET/HEAD | `/openapi.json` | OpenAPI JSON |
| GET/HEAD | `/redoc` | ReDoc（FastAPI 默认保留） |

---

## 2. API 接口总表

| 模块 | Method | URL | 接口用途 | 鉴权 | 前端是否调用 | 当前状态 |
|---|---|---|---|---|---|---|
| 运维 | GET | `/healthz` | 进程存活检查 | 否 | 可选 | ✅ 可用 |
| 运维 | GET | `/readyz` | MySQL + Redis 就绪检查 | 否 | 通常不调用 | ✅ 可用 |
| 认证 | POST | `/api/v1/auth/otp/login/code` | 获取登录验证码 | 否 | P1/可选 | ⚠️ 仅开发短信适配器可用 |
| 认证 | POST | `/api/v1/auth/otp/login` | 验证码注册/登录 | 否 | P1/可选 | ✅ 开发环境可用 |
| 认证 | POST | `/api/v1/auth/password/register` | 手机号密码直接注册 | 否 | P0 | ✅ 可用；无需验证码，成功 201 |
| 认证 | POST | `/api/v1/auth/password/login` | 手机号密码登录 | 否 | P0 | ✅ 可用 |
| 认证 | PUT | `/api/v1/auth/password` | 首次设置或修改密码 | 用户 | P1 | ✅ 可用 |
| 认证 | POST | `/api/v1/auth/password/reset/otp` | 获取密码重置验证码 | 否 | P1 | ⚠️ 仅开发短信适配器可用 |
| 认证 | POST | `/api/v1/auth/password/reset` | 验证码重置密码 | 否 | P1 | ✅ 可用 |
| 认证 | POST | `/api/v1/auth/refresh` | refresh token 换 access token | 否；body 中提供 refresh token | P0 | ✅ 可用 |
| 认证 | GET | `/api/v1/auth/wechat/qr` | 微信扫码登录入口 | 否 | 暂不接 | ⛔ 占位，默认 501 |
| 用户 | GET | `/api/v1/me` | 当前用户、角色、密码状态、点数 | 用户 | P0 | ✅ 可用；无 response_model |
| 点数 | GET | `/api/v1/points/ledger` | 当前用户点数流水 | 用户 | P1 | ✅ 可用；无分页/无 response_model |
| 点数 | POST | `/api/v1/points/consume` | 按功能规则幂等扣点 | 用户 | 按付费功能需要 | ✅ 可用；无 response_model |
| 支付 | GET | `/api/v1/payments/packages` | 查询启用套餐 | 否 | P1 | ✅ 查询可用；无 response_model |
| 支付 | POST | `/api/v1/payments/orders` | 创建待支付订单 | 用户 | 暂不做真实支付 | ⚠️ 仅建 pending，不能付款 |
| 支付 | POST | `/api/v1/payments/webhooks/{provider}` | 支付平台回调 | 平台回调 | 前端绝不调用 | ⛔ 固定 501，不入账 |
| 管理员 | POST | `/api/v1/admin/packages` | 创建套餐 | 管理员 | 管理后台 | ✅ 可用；无 response_model |
| 管理员 | GET | `/api/v1/admin/packages` | 查询全部套餐 | 管理员 | 管理后台 | ✅ 可用；无 response_model |
| 管理员 | PUT | `/api/v1/admin/feature-rules/{code}` | 新增/更新扣点规则 | 管理员 | 管理后台 | ✅ 可用；无 response_model |
| 管理员 | GET | `/api/v1/admin/users` | 分页查询用户 | 管理员 | 管理后台 | ✅ 可用 |
| 管理员 | PATCH | `/api/v1/admin/users/{user_id}/active` | 启停用户 | 管理员 | 管理后台 | ✅ 可用；无 response_model |
| 管理员 | GET | `/api/v1/admin/recharge-statistics` | 已支付订单统计 | 管理员 | 管理后台 | ⚠️ 查询逻辑可用，但目前没有真实入账数据 |
| 命盘 | POST | `/api/v1/chart-profiles/preview` | 校验个人信息并预览命盘 | 用户 | P0 | ✅ 可用 |
| 命盘 | POST | `/api/v1/chart-profiles` | 确认并保存档案和命盘 | 用户 | P0 | ✅ 可用，成功 201 |
| 命盘 | GET | `/api/v1/chart-profiles` | 查询我的档案列表 | 用户 | P0 | ✅ 可用 |
| 命盘 | GET | `/api/v1/chart-profiles/{profile_id}` | 查询档案和命盘 | 用户 | P0 | ✅ 可用 |
| 命盘 | PUT | `/api/v1/chart-profiles/{profile_id}` | 修改档案并重新排盘 | 用户 | P1 | ✅ 可用，有冷却期 |
| 命盘 | GET | `/api/v1/chart-profiles/{profile_id}/chart` | 只读命盘快照 | 用户 | P1 | ✅ 可用 |
| 命盘 | POST | `/api/v1/chart-profiles/{profile_id}/regenerate` | 用现有档案重建命盘 | 用户 | P1/后台功能 | ✅ 可用 |

---

## 3. 接口详细说明

### 3.0 通用调用代码与数据契约

#### 3.0.1 推荐 fetch 封装

```ts
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type ApiBusinessError = { detail: string };
type ApiValidationError = {
  detail: Array<{
    type: string;
    loc: Array<string | number>;
    msg: string;
    input?: unknown;
    ctx?: Record<string, unknown>;
  }>;
};

class ApiError extends Error {
  constructor(
    public status: number,
    public body: ApiBusinessError | ApiValidationError | string,
  ) {
    super(typeof body === "string" ? body : JSON.stringify(body));
  }
}

async function apiFetch<T>(
  path: string,
  init: RequestInit = {},
  accessToken?: string,
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body) headers.set("Content-Type", "application/json");
  if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  const contentType = response.headers.get("content-type") ?? "";
  const body = contentType.includes("application/json")
    ? await response.json()
    : await response.text();
  if (!response.ok) throw new ApiError(response.status, body);
  return body as T;
}
```

没有 Cookie Session，不要设置 `credentials: "include"`，除非前端自身代理另有需要。

#### 3.0.2 通用错误结构

业务错误由 `APIError` 继承 FastAPI `HTTPException`：

```json
{
  "detail": "Invalid or expired token"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `detail` | string | 英文错误信息；当前没有对外返回 `error.code` |

Pydantic/FastAPI 参数校验错误：

```json
{
  "detail": [
    {
      "type": "string_pattern_mismatch",
      "loc": ["body", "code"],
      "msg": "String should match pattern '^\\d{6}$'",
      "input": "123"
    }
  ]
}
```

前端必须同时兼容 `detail: string` 和 `detail: array`。未捕获异常没有统一 JSON handler，500 可能是纯文本 `Internal Server Error`，因此上面的 fetch 封装不能无条件调用 `response.json()`。

常见状态：

| HTTP | 含义 |
|---:|---|
| 400 | OTP 无效、过期或已使用；缺少当前密码 |
| 401 | 未认证、Token 无效/过期/类型错误、用户不可用、密码错误 |
| 403 | 不是管理员 |
| 404 | 资源不存在/不属于当前用户、功能规则不存在、provider 未知 |
| 409 | 帐号已注册、指纹不一致、点数不足、幂等冲突、密码未改变、套餐重名 |
| 422 | Pydantic 参数错误、出生信息无法排盘、统计时间范围错误 |
| 429 | OTP/密码频率或次数限制、档案修改冷却 |
| 501 | 微信扫码或支付验签适配器未实现 |
| 503 | 短信、数据库或 Redis 未就绪 |

#### 3.0.3 公共 TypeScript 类型

```ts
type UUID = string;
type ISODateTime = string;

type OTPOut = {
  message: string;
  development_code: string | null;
};

type TokenPairOut = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  new_user: boolean;
};

type AccessTokenOut = {
  access_token: string;
  token_type: "bearer";
};

type MeOut = {
  id: UUID;
  phone: string | null;
  role: "user" | "admin" | string;
  has_password: boolean;
  points: number;
};

type PointLedgerOut = {
  id: UUID;
  user_id: UUID;
  delta: number;
  balance_after: number;
  event_type: string;
  reference_id: string | null;
  idempotency_key: string;
  metadata_: Record<string, unknown>;
  created_at: ISODateTime;
};

type PointPackageOut = {
  id: UUID;
  name: string;
  kind: "one_time" | "monthly" | string;
  points: number;
  price_fen: number;
  active: boolean;
  created_at: ISODateTime;
};

type UserOut = {
  id: UUID;
  phone: string | null;
  role: string;
  is_active: boolean;
  has_password: boolean;
  created_at: ISODateTime;
};

type BirthProfileInput = {
  name: string;
  gender: "男" | "女";
  calendar_type: "solar" | "lunar";
  birth_date: string;
  birth_hour?: number | null;
  birth_minute?: number | null;
  birth_place?: string;
  is_leap_month?: boolean;
  time_label?: string;
};

type ChartPreviewOut = {
  input_fingerprint: string;
  chart_fingerprint: string;
  engine_version: string;
  input_text: string;
  solar_datetime: string;
  pillars: string[];
  calculation_basis: string;
};

type BirthProfileOut = {
  id: UUID;
  name: string;
  gender: string;
  calendar_type: string;
  birth_date: string;
  solar_birth_date: string;
  birth_hour: number | null;
  birth_minute: number | null;
  birth_place: string;
  is_leap_month: boolean;
  time_label: string;
  last_edited_at: ISODateTime | null;
  next_edit_at: ISODateTime | null;
  can_edit: boolean;
  created_at: ISODateTime;
  updated_at: ISODateTime;
};

type BaziChartOut = {
  id: UUID;
  profile_id: UUID;
  input_fingerprint: string;
  chart_fingerprint: string;
  engine_version: string;
  chart: Record<string, unknown>;
  generated_at: ISODateTime;
};

type BirthProfileDetailOut = {
  profile: BirthProfileOut;
  chart: BaziChartOut;
};
```

`UUID` 只是前端别名。输出 ID 由 `uuid.uuid4()` 生成，当前是 36 字符；多数输入 schema/path 仍声明普通 string，没有后端 UUID 格式校验。

#### 3.0.4 命理档案公共请求字段

`BirthProfileIn` 定义于 `backend/app/schemas.py:99-130`。Pydantic 会对全部 string 执行首尾空白裁剪。

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则/说明 |
|---|---|---|---|---|---|
| `name` | Body | string | 是 | 无 | 裁剪后 1～100 字符 |
| `gender` | Body | literal | 是 | 无 | 只允许 `男`、`女` |
| `calendar_type` | Body | literal | 是 | 无 | `solar` 或 `lunar` |
| `birth_date` | Body | string | 是 | 无 | 正则 `YYYY-MM-DD`；年份 1900～当前年 |
| `birth_hour` | Body | integer/null | 否 | null | 0～23；必须与 minute 同时有值或同时 null |
| `birth_minute` | Body | integer/null | 否 | null | 0～59；必须与 hour 成对 |
| `birth_place` | Body | string | 否 | `""` | 最大 200；不参与真太阳时换算，但参与 input fingerprint |
| `is_leap_month` | Body | boolean | 否 | false | 仅 lunar 可为 true |
| `time_label` | Body | string | 否 | `"精确时间"` | 裁剪后 1～40；参与 input fingerprint |

公历日期必须真实存在且不能是未来日期。农历只在 schema 层检查月 1～12、日 1～30，随后由排盘引擎完成真实转换；转换失败返回业务 422。

### 3.1 运维接口

#### 3.1.1 存活检查 — `GET /healthz`

| 项目 | 内容 |
|---|---|
| 用途 | 只检查 FastAPI 进程能否响应，不访问外部依赖 |
| Content-Type | Request 无 body；Response `application/json` |
| 鉴权 | 无 |
| 后端代码 | `backend/app/main.py:51-54` |
| 函数 | `health` |
| response_model | 无；OpenAPI 成功 schema 为 `{}` |

Path、Query、Body、Form、Header、Cookie、File 参数均无。

```ts
const health = await apiFetch<{ status: "ok" }>("/healthz");
```

HTTP 200：

```json
{"status":"ok"}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `status` | string | 当前固定 `ok` |

代码没有主动业务错误；未捕获异常为 500。

#### 3.1.2 就绪检查 — `GET /readyz`

| 项目 | 内容 |
|---|---|
| 用途 | 实际执行 MySQL `SELECT 1` 和 Redis `PING` |
| Content-Type | Request 无 body；Response `application/json` |
| 鉴权 | 无 |
| 后端代码 | `backend/app/main.py:57-75` |
| 函数 | `readiness` |
| Depends | `DBSession`、`RedisClient` |
| response_model | 无；OpenAPI 成功 schema 为 `{}` |

无前端业务参数。

```ts
const ready = await apiFetch<{ status: "ready" }>("/readyz");
```

HTTP 200：

```json
{"status":"ready"}
```

| HTTP | detail | 触发条件 |
|---:|---|---|
| 503 | `database is not ready` | SQLAlchemy 查询失败或返回值不是 1 |
| 503 | `redis is not ready` | Redis 依赖为空、PING false 或抛出 RedisError |

错误响应均为上述 `{"detail":"..."}`；代码未定义其他主动业务错误，未捕获异常为 500。

### 3.2 认证接口

#### 3.2.1 获取登录验证码 — `POST /api/v1/auth/otp/login/code`

| 项目 | 内容 |
|---|---|
| 用途 | 校验并规范化手机号，生成一次性登录 OTP |
| Content-Type | Request/Response `application/json` |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/auth.py:55-60` |
| 函数 | `request_login_otp` |
| service | `normalize` → `issue_otp` → SMS provider → DB commit |
| response_model | `OTPOut` |

请求参数：

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `phone` | Body | string | 是 | 无 | Pydantic 无长度限制；service 用 `phonenumbers` 校验。中国号码可传 `13800138000` 或 `+8613800138000` |

Path、Query、Form、Cookie、File 参数无；无需 Authorization。

```ts
const otp = await apiFetch<OTPOut>("/api/v1/auth/otp/login/code", {
  method: "POST",
  body: JSON.stringify({ phone: "13800138000" }),
});
```

开发环境 HTTP 200：

```json
{"message":"OTP sent","development_code":"123456"}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `message` | string | 当前固定 `OTP sent` |
| `development_code` | string/null | 开发 adapter 返回 6 位验证码；生产不得依赖该字段 |

错误：422 `Invalid phone number` 或 body 校验失败；429 `Daily OTP limit reached` / `Please wait before requesting another OTP`；503 `SMS provider is not configured`。默认 TTL 300 秒、重发间隔 60 秒、每手机号滚动 24 小时最多 10 次。

#### 3.2.2 验证码注册/登录 — `POST /api/v1/auth/otp/login`

| 项目 | 内容 |
|---|---|
| 用途 | 验证 login-purpose OTP；手机号首次成功时自动注册并赠送点数 |
| Content-Type | Request/Response `application/json` |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/auth.py:63-73` |
| 函数 | `otp_login` |
| service | `normalize` → `verify_otp` → `_token_pair` |
| response_model | `TokenPairOut` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `phone` | Body | string | 是 | 无 | 必须对应验证码手机号；会规范化为 E.164 |
| `code` | Body | string | 是 | 无 | 正则 `^\d{6}$` |

```ts
const tokens = await apiFetch<TokenPairOut>("/api/v1/auth/otp/login", {
  method: "POST",
  body: JSON.stringify({ phone: "13800138000", code: otp.development_code }),
});
```

HTTP 200：

```json
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "bearer",
  "new_user": true
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `access_token` | string | 默认 30 分钟，用作 Bearer |
| `refresh_token` | string | 默认 30 天，只能提交到 refresh body |
| `token_type` | literal `bearer` | 固定值 |
| `new_user` | boolean | 本次是否自动创建用户 |

错误：400 `Invalid or expired OTP`；422 手机/验证码格式错误；429 `OTP attempt limit reached`。验证码最多默认失败 5 次，成功后一次性消费。

⚠️ 当前 `verify_otp` 对已有用户没有检查 `is_active`，停用用户仍可能从此接口拿到 Token；但使用该 Token 调受保护接口时会返回 401 `User unavailable`。

#### 3.2.3 手机号密码直接注册 — `POST /api/v1/auth/password/register`

| 项目 | 内容 |
|---|---|
| 用途 | 使用手机号和初始密码直接创建用户、钱包和注册赠送流水 |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/auth.py:89-98` |
| 函数 | `password_register` |
| service | `backend/app/services.py:200-230`；`normalize` → `register_password_user` → scrypt hash → 创建 User/PointBalance/PointLedger |
| Content-Type | Request/Response `application/json` |
| response_model | `TokenPairOut` |
| 成功状态 | **201 Created** |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `phone` | Body | string | 是 | 无 | service 校验有效手机号并规范化为 E.164；中国号码可传国内格式或 `+86` 格式 |
| `password` | Body | string | 是 | 无 | 8～128 字符，不裁剪空格；只保存 scrypt 摘要 |

无 Path、Query、Header、Cookie、Form 或 File 参数，也不需要先请求或提交短信验证码。

```ts
const tokens = await apiFetch<TokenPairOut>(
  "/api/v1/auth/password/register",
  {
    method: "POST",
    body: JSON.stringify({
      phone: "13800138000",
      password: "My-Secure-Passphrase-2026",
    }),
  },
);
```

HTTP 201：

```json
{
  "access_token": "<JWT>",
  "refresh_token": "<JWT>",
  "token_type": "bearer",
  "new_user": true
}
```

响应字段与 3.2.2 的 `TokenPairOut` 相同，`new_user` 固定 true。注册事务会创建用户、余额账户，并通过流水增加 `REGISTRATION_BONUS_POINTS`（默认 20）；成功后可立即携带 access token 调用 `/me`，或以后调用 `/password/login`。

错误：409 `Account already registered`（规范化后的手机号已经存在，绝不会覆盖原密码）；422 `Invalid phone number` 或 password/body 校验失败；未预期的密码散列或数据库异常为 500。并发重复注册由数据库手机号唯一约束兜底。

⚠️ 按当前产品要求，本接口只检查手机号格式，不验证手机号归属，也不会创建或消费 OTP。前端不能把注册成功解释为“手机号已验证”。

#### 3.2.4 手机号密码登录 — `POST /api/v1/auth/password/login`

| 项目 | 内容 |
|---|---|
| 用途 | 已设置密码的用户使用手机号和密码获取 TokenPair |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/auth.py:76-86` |
| 函数 | `password_login` |
| service | `normalize` → `authenticate_password` |
| Content-Type | Request/Response `application/json` |
| response_model | `TokenPairOut` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `phone` | Body | string | 是 | 无 | 有效手机号 |
| `password` | Body | string | 是 | 无 | 8～128 字符，不裁剪空格 |

```ts
const tokens = await apiFetch<TokenPairOut>("/api/v1/auth/password/login", {
  method: "POST",
  body: JSON.stringify({
    phone: "13800138000",
    password: "My-Secure-Passphrase-2026",
  }),
});
```

HTTP 200 与 3.2.2 的 `TokenPairOut` 相同，`new_user` 固定 false。

错误：401 `Invalid phone number or password`（用户不存在、停用、未设置密码、密码错误统一消息）；429 密码登录锁定；422 字段格式错误。默认连续失败 5 次锁定 15 分钟。

#### 3.2.5 设置或修改密码 — `PUT /api/v1/auth/password`

| 项目 | 内容 |
|---|---|
| 用途 | 首次设置密码，或验证旧密码后修改；成功后撤销旧 Token |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/auth.py:101-121` |
| 函数 | `set_or_change_password` |
| service | `CurrentUser` → `change_user_password` → auth_version + 1 |
| Content-Type | Request/Response `application/json` |
| response_model | `TokenPairOut` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `Authorization` | Header | string | 是 | 无 | `Bearer <access_token>` |
| `current_password` | Body | string/null | 有旧密码时必填 | null | 8～128 字符 |
| `new_password` | Body | string | 是 | 无 | 8～128 字符，不得与旧密码相同 |

首次设置：

```ts
const newTokens = await apiFetch<TokenPairOut>(
  "/api/v1/auth/password",
  { method: "PUT", body: JSON.stringify({ new_password: "My-Secure-Passphrase-2026" }) },
  accessToken,
);
```

修改：

```ts
const newTokens = await apiFetch<TokenPairOut>(
  "/api/v1/auth/password",
  {
    method: "PUT",
    body: JSON.stringify({
      current_password: "My-Secure-Passphrase-2026",
      new_password: "My-New-Passphrase-2027",
    }),
  },
  accessToken,
);
```

HTTP 200 返回新的 `TokenPairOut`。成功后旧 access/refresh token 因 `auth_version` 变化全部失效，前端必须原子替换本地两枚 Token。

错误：400 `Current password is required`；401 Token 或当前密码错误；409 `New password must be different...`；422 长度错误；429 账户暂时锁定。

#### 3.2.6 获取密码重置验证码 — `POST /api/v1/auth/password/reset/otp`

| 项目 | 内容 |
|---|---|
| 用途 | 签发 password_reset-purpose OTP，与登录 OTP 隔离 |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/auth.py:124-129` |
| 函数 | `request_password_reset_otp` |
| Content-Type | Request/Response `application/json` |
| response_model | `OTPOut` |

请求字段、响应和发送限制与 3.2.1 相同，只有 OTP purpose 不同。

```ts
const otp = await apiFetch<OTPOut>("/api/v1/auth/password/reset/otp", {
  method: "POST",
  body: JSON.stringify({ phone: "13800138000" }),
});
```

HTTP 200 与 3.2.1 相同：

```json
{"message":"OTP sent","development_code":"123456"}
```

错误：422 手机无效；429 日限额/重发过快；503 生产短信 adapter 未配置。

#### 3.2.7 使用验证码重置密码 — `POST /api/v1/auth/password/reset`

| 项目 | 内容 |
|---|---|
| 用途 | 校验 reset OTP，设置新密码、解除密码锁定并撤销旧 Token |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/auth.py:132-154` |
| 函数 | `reset_password` |
| Content-Type | Request/Response `application/json` |
| response_model | `TokenPairOut` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `phone` | Body | string | 是 | 无 | 获取 reset OTP 的手机号 |
| `code` | Body | string | 是 | 无 | 6 位数字，只接受 reset purpose |
| `new_password` | Body | string | 是 | 无 | 8～128 字符 |

```ts
const tokens = await apiFetch<TokenPairOut>("/api/v1/auth/password/reset", {
  method: "POST",
  body: JSON.stringify({
    phone: "13800138000",
    code: "123456",
    new_password: "My-New-Passphrase-2027",
  }),
});
```

HTTP 200 返回新的 `TokenPairOut`，旧 Token 失效。

错误：400 OTP 无效/过期/已用/用途错误；401 手机号没有对应用户；422 字段错误；429 OTP 尝试超限。

⚠️ 已存在但被停用的用户目前不会在此处被 `is_active` 拦截，仍可能重置密码并收到随后无法调用受保护接口的 Token。

#### 3.2.8 刷新访问令牌 — `POST /api/v1/auth/refresh`

| 项目 | 内容 |
|---|---|
| 用途 | 使用 refresh JWT 换一枚新 access JWT |
| 鉴权 | 不用 Authorization；refresh token 放 JSON Body |
| 后端代码 | `backend/app/api/v1/auth.py:157-177` |
| 函数 | `refresh` |
| Content-Type | Request/Response `application/json` |
| response_model | `AccessTokenOut` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|---|
| `refresh_token` | Body | string | 是 | 无 | 必须是 typ=refresh、签名/issuer/exp/auth_version 有效的 JWT |

```ts
const refreshed = await apiFetch<AccessTokenOut>("/api/v1/auth/refresh", {
  method: "POST",
  body: JSON.stringify({ refresh_token: refreshToken }),
});
```

HTTP 200：

```json
{"access_token":"<new JWT>","token_type":"bearer"}
```

本接口不轮换或返回新 refresh token。错误统一为 401，detail 可能是 `Invalid refresh token`、`Refresh token required` 或 `User unavailable`。

#### 3.2.9 微信扫码登录占位 — `GET /api/v1/auth/wechat/qr`

| 项目 | 内容 |
|---|---|
| 用途 | 预留微信公众号扫码登录入口 |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/auth.py:180-187` |
| 函数 | `wechat_qr` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | 无 |
| 当前可联调性 | 不可用于真实登录 |

无请求参数。

```ts
// 当前不应在生产前端调用
await apiFetch<{ message: string }>("/api/v1/auth/wechat/qr");
```

未配置 `WECHAT_APP_ID` 时固定 501：

```json
{"detail":"WeChat QR login is not configured"}
```

即使配置 App ID，当前也只返回一条实现提示 message，不会返回 QR URL、scene、过期时间或登录状态，不能进入真实扫码流程。

配置任意非空 `WECHAT_APP_ID` 时当前 HTTP 200 仅为：

```json
{"message":"Implement official-account QR scene creation and callback signature verification here"}
```

### 3.3 当前用户与点数接口

#### 3.3.1 查询当前用户 — `GET /api/v1/me`

| 项目 | 内容 |
|---|---|
| 用途 | 返回当前用户基本信息、角色、是否已设置密码和实时点数余额 |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/users.py:15-24` |
| 函数 | `profile` |
| Depends | `CurrentUser`、`DBSession` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | 无；以下结构来自实际 return 和测试客户端 |

除 `Authorization: Bearer <access_token>` 外无 Path、Query、Body、Form、Cookie、File 参数。

```ts
const me = await apiFetch<MeOut>("/api/v1/me", {}, accessToken);
```

HTTP 200：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "phone": "+8613800138000",
  "role": "user",
  "has_password": true,
  "points": 20
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 用户 UUID |
| `phone` | string/null | 规范化后的 E.164 手机号 |
| `role` | string | 当前代码使用 `user` / `admin`，数据库层未做 Enum 约束 |
| `has_password` | boolean | ORM property，是否存在密码摘要 |
| `points` | integer | `PointBalance.balance`；不存在钱包时返回 0 |

错误：401 缺少/无效/过期/错误类型 Token，或用户停用。实测缺少 Header 为 `{"detail":"Not authenticated"}`。

#### 3.3.2 查询点数流水 — `GET /api/v1/points/ledger`

| 项目 | 内容 |
|---|---|
| 用途 | 按 `created_at DESC` 返回当前用户全部流水 |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/users.py:27-40` |
| 函数 | `ledger` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | 无；直接序列化 `PointLedger` ORM 列表 |

没有 Path、Query 或 Body 参数，当前不分页。

```ts
const ledger = await apiFetch<PointLedgerOut[]>(
  "/api/v1/points/ledger",
  {},
  accessToken,
);
```

HTTP 200：

```json
[
  {
    "id": "82cb77e2-3ec4-42f7-9f52-56758a09fa00",
    "user_id": "550e8400-e29b-41d4-a716-446655440000",
    "delta": 20,
    "balance_after": 20,
    "event_type": "registration_bonus",
    "reference_id": null,
    "idempotency_key": "signup:550e8400-e29b-41d4-a716-446655440000",
    "metadata_": {},
    "created_at": "2026-08-17T12:30:00"
  }
]
```

`delta > 0` 是增加，`delta < 0` 是扣减；`balance_after` 是该流水完成后的余额。空流水返回 `[]`。错误主要是认证 401。

⚠️ 返回包含内部 `idempotency_key`、`user_id` 和 `metadata_`，且没有 response_model；前端可读取但不应把这些字段当作永不变化的严格契约。

#### 3.3.3 消耗点数 — `POST /api/v1/points/consume`

| 项目 | 内容 |
|---|---|
| 用途 | 按已启用 FeatureRule 扣点，并通过用户范围内幂等键防重复扣费 |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/users.py:43-48` |
| 函数 | `consume_points` |
| service | `consume` → `credit`，钱包行锁 + ledger 唯一约束 |
| Content-Type | Request/Response `application/json` |
| response_model | 无 |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `Authorization` | Header | string | 是 | 无 | Bearer access token |
| `feature_code` | Body | string | 是 | 无 | 必须存在且 active；schema 无长度/格式约束 |
| `idempotency_key` | Body | string | 是 | 无 | 8～128 字符；同一用户一次业务操作固定唯一 |

```ts
const consumed = await apiFetch<{ ledger_id: UUID; balance: number }>(
  "/api/v1/points/consume",
  {
    method: "POST",
    body: JSON.stringify({
      feature_code: "ziwei_report",
      idempotency_key: crypto.randomUUID(),
    }),
  },
  accessToken,
);
```

HTTP 200：

```json
{"ledger_id":"24770e92-c67e-4140-a19f-7637e0a5567f","balance":17}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `ledger_id` | string | 本次或幂等复用的 PointLedger ID |
| `balance` | integer | 扣点后的余额 |

同一用户、同一 key、同一 feature 重试返回原 ledger，不重复扣点；同 key 改做其他操作返回 409。

错误：401 认证失败；404 `Feature rule not found`（不存在或 inactive）；409 `Insufficient points` / `Idempotency key was reused...`；422 body 校验失败。

### 3.4 套餐与支付接口

#### 3.4.1 查询可购买套餐 — `GET /api/v1/payments/packages`

| 项目 | 内容 |
|---|---|
| 用途 | 查询 `active=true` 的套餐 |
| 鉴权 | 无 |
| 后端代码 | `backend/app/api/v1/payments.py:15-22` |
| 函数 | `public_packages` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | 无；直接序列化 ORM |

无请求参数。

```ts
const packages = await apiFetch<PointPackageOut[]>("/api/v1/payments/packages");
```

HTTP 200：

```json
[
  {
    "id": "b1acb40e-8265-4b0d-9083-31e7803a8c65",
    "name": "100点",
    "kind": "one_time",
    "points": 100,
    "price_fen": 990,
    "active": true,
    "created_at": "2026-08-17T12:30:00"
  }
]
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 套餐 UUID |
| `name` | string | 名称 |
| `kind` | string | schema 创建时允许 `one_time`、`monthly` |
| `points` | integer | 到账点数定义；当前支付尚不会到账 |
| `price_fen` | integer | 人民币分 |
| `active` | boolean | 本接口只返回 true |
| `created_at` | datetime string | 创建时间 |

空列表返回 `[]`。`monthly` 当前只是可存储类型，没有续费/到期/周期权益逻辑。

代码没有主动业务错误；数据库/序列化等未捕获异常为 500。

#### 3.4.2 创建支付订单 — `POST /api/v1/payments/orders`

| 项目 | 内容 |
|---|---|
| 用途 | 为当前用户和套餐创建 pending PaymentOrder |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/payments.py:25-46` |
| 函数 | `order` |
| Content-Type | Request/Response `application/json` |
| response_model | 无 |
| 当前可联调性 | 只能验证建单，不能拉起支付 |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `package_id` | Body | string | 是 | 无 | 必须对应 active 套餐；schema 不校验 UUID |
| `provider` | Body | string literal | 是 | 无 | `wechat` 或 `alipay` |

```ts
type PaymentOrderCreated = {
  order_id: UUID;
  status: string;
  provider: "wechat" | "alipay";
  payment_payload: null;
};

const order = await apiFetch<PaymentOrderCreated>(
  "/api/v1/payments/orders",
  {
    method: "POST",
    body: JSON.stringify({ package_id: selected.id, provider: "wechat" }),
  },
  accessToken,
);
```

当前 HTTP 200：

```json
{
  "order_id": "41a957d9-12f9-4394-b13c-e6aed89d996d",
  "status": "pending",
  "provider": "wechat",
  "payment_payload": null
}
```

`payment_payload` 当前固定 null，没有支付 URL、二维码、prepay_id 或支付宝 order string。错误：401 认证失败；404 `Package unavailable`；422 provider/body 错误。

#### 3.4.3 支付平台回调占位 — `POST /api/v1/payments/webhooks/{provider}`

| 项目 | 内容 |
|---|---|
| 用途 | 预留支付平台异步回调 |
| 鉴权 | 不用用户 Bearer；未来应由平台签名/证书鉴权 |
| 后端代码 | `backend/app/api/v1/payments.py:49-57` |
| 函数 | `webhook` |
| Content-Type | Request/Response `application/json` |
| response_model | 无 |
| 当前可联调性 | 前端绝不调用；后端固定拒绝 |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `provider` | Path | string | 是 | 无 | 仅 `wechat` / `alipay` 进入 501 分支 |
| `event_id` | Body | string | 是 | 无 | 当前无长度约束 |
| `order_id` | Body | string | 是 | 无 | 当前无 UUID 约束 |
| `provider_trade_no` | Body | string | 是 | 无 | 当前无长度约束 |

仅供平台接入测试的请求形式：

```ts
await apiFetch<never>("/api/v1/payments/webhooks/wechat", {
  method: "POST",
  body: JSON.stringify({
    event_id: "platform-event-001",
    order_id: "41a957d9-12f9-4394-b13c-e6aed89d996d",
    provider_trade_no: "platform-trade-001",
  }),
});
```

已知 provider 固定 501：

```json
{"detail":"Payment provider signature verification is not configured"}
```

当前实现没有任何 HTTP 2xx 成功响应；完成平台验签和入账实现前，应把 501 视为该路由的固定结果，而不是可重试错误。

未知 provider 返回 404 `Unknown payment provider`。请求 body 在路由函数前先由 Pydantic 校验，body 不合法可能先得到 422。当前不会写 WebhookEvent、更新订单或增加点数。

### 3.5 管理员接口

本组全部要求 `Authorization: Bearer <admin access_token>`。先由 `CurrentUser` 检查 Token、用户状态和 auth_version，再由 `AdminUser` 检查 `role == "admin"`。普通用户返回 403 `Administrator role required`；代码没有公开授予管理员角色的接口。

#### 3.5.1 创建点数套餐 — `POST /api/v1/admin/packages`

| 项目 | 内容 |
|---|---|
| 用途 | 创建套餐记录 |
| 鉴权 | 管理员 access token |
| 后端代码 | `backend/app/api/v1/admin.py:19-29` |
| 函数 | `create_package` |
| Content-Type | Request/Response `application/json` |
| response_model | 无；实际返回 ORM |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `name` | Body | string | 是 | 无 | 数据库唯一、列长 100；Pydantic 当前没有长度/空白校验 |
| `kind` | Body | string | 是 | 无 | 正则 `^(one_time|monthly)$` |
| `points` | Body | integer | 是 | 无 | > 0 |
| `price_fen` | Body | integer | 是 | 无 | > 0，单位分 |
| `active` | Body | boolean | 否 | true | 是否公开可购买 |

```ts
const created = await apiFetch<PointPackageOut>(
  "/api/v1/admin/packages",
  {
    method: "POST",
    body: JSON.stringify({
      name: "100点",
      kind: "one_time",
      points: 100,
      price_fen: 990,
      active: true,
    }),
  },
  adminAccessToken,
);
```

当前成功状态为 HTTP 200：

```json
{
  "id":"b1acb40e-8265-4b0d-9083-31e7803a8c65",
  "name":"100点",
  "kind":"one_time",
  "points":100,
  "price_fen":990,
  "active":true,
  "created_at":"2026-08-17T12:30:00"
}
```

响应字段与 `PointPackageOut` 相同。错误：401/403；409 `Package name already exists`；422 schema 错误；超长 name 在 MySQL 可能成为未统一处理的数据库错误。

#### 3.5.2 查询全部套餐 — `GET /api/v1/admin/packages`

| 项目 | 内容 |
|---|---|
| 用途 | 查询全部套餐，包括 inactive |
| 鉴权 | 管理员 access token |
| 后端代码 | `backend/app/api/v1/admin.py:32-35` |
| 函数 | `packages` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | 无；ORM 数组 |

无业务参数。

```ts
const packages = await apiFetch<PointPackageOut[]>(
  "/api/v1/admin/packages",
  {},
  adminAccessToken,
);
```

HTTP 200 返回 `PointPackageOut[]`，字段与 3.4.1 相同；空数据为 `[]`。代码未指定排序。错误主要是 401/403。

#### 3.5.3 新增或更新扣点规则 — `PUT /api/v1/admin/feature-rules/{code}`

| 项目 | 内容 |
|---|---|
| 用途 | 以 feature code 为主键做 upsert |
| 鉴权 | 管理员 access token |
| 后端代码 | `backend/app/api/v1/admin.py:38-49` |
| 函数 | `set_rule` |
| Content-Type | Request/Response `application/json` |
| response_model | 无；返回 `FeatureRule` ORM |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `code` | Path | string | 是 | 无 | 数据库列长 64；路由当前无长度/格式校验 |
| `points_cost` | Body | integer | 是 | 无 | >= 0 |
| `active` | Body | boolean | 否 | true | inactive 后用户 consume 会得到 404 |

```ts
type FeatureRuleOut = {
  feature_code: string;
  points_cost: number;
  active: boolean;
  updated_at: ISODateTime;
};

const rule = await apiFetch<FeatureRuleOut>(
  `/api/v1/admin/feature-rules/${encodeURIComponent("ziwei_report")}`,
  { method: "PUT", body: JSON.stringify({ points_cost: 3, active: true }) },
  adminAccessToken,
);
```

HTTP 200：

```json
{
  "feature_code":"ziwei_report",
  "points_cost":3,
  "active":true,
  "updated_at":"2026-08-17T12:30:00"
}
```

错误：401/403、422 body 错误；过长 code 可能由数据库拒绝而不是标准 422。

#### 3.5.4 查询用户列表 — `GET /api/v1/admin/users`

| 项目 | 内容 |
|---|---|
| 用途 | 按创建时间倒序分页查询用户，可按手机号片段过滤 |
| 鉴权 | 管理员 access token |
| 后端代码 | `backend/app/api/v1/admin.py:52-67` |
| 函数 | `users` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | `list[UserOut]` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `phone` | Query | string/null | 否 | null | SQL contains 模糊匹配，没有额外规范化 |
| `offset` | Query | integer | 否 | 0 | >= 0 |
| `limit` | Query | integer | 否 | 20 | 1～100 |

```ts
const params = new URLSearchParams({ phone: "138", offset: "0", limit: "20" });
const users = await apiFetch<UserOut[]>(
  `/api/v1/admin/users?${params}`,
  {},
  adminAccessToken,
);
```

HTTP 200：

```json
[
  {
    "id":"550e8400-e29b-41d4-a716-446655440000",
    "phone":"+8613800138000",
    "role":"user",
    "is_active":true,
    "has_password":true,
    "created_at":"2026-08-17T12:30:00"
  }
]
```

响应没有 `total`、`next_cursor` 或 has_more；前端只能根据返回条数是否等于 limit 决定是否尝试下一页。错误：401/403；422 offset/limit 类型或范围错误。

#### 3.5.5 启用或停用用户 — `PATCH /api/v1/admin/users/{user_id}/active`

| 项目 | 内容 |
|---|---|
| 用途 | 修改目标用户 `is_active` |
| 鉴权 | 管理员 access token |
| 后端代码 | `backend/app/api/v1/admin.py:70-80` |
| 函数 | `set_user_active` |
| Content-Type | Request/Response `application/json` |
| response_model | 无 |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `user_id` | Path | string | 是 | 无 | 目标用户 ID；无 UUID schema 校验 |
| `is_active` | Body | boolean | 是 | 无 | true 启用、false 停用 |

```ts
const result = await apiFetch<{ id: UUID; is_active: boolean }>(
  `/api/v1/admin/users/${encodeURIComponent(userId)}/active`,
  { method: "PATCH", body: JSON.stringify({ is_active: false }) },
  adminAccessToken,
);
```

HTTP 200：

```json
{"id":"550e8400-e29b-41d4-a716-446655440000","is_active":false}
```

错误：401/403；404 `User not found`；422 body 错误。代码未禁止管理员停用自己。停用用户后其 access/refresh token 在依赖层被拒绝，但见 3.2.2/3.2.7 的 OTP 状态检查缺口。

#### 3.5.6 查询充值统计 — `GET /api/v1/admin/recharge-statistics`

| 项目 | 内容 |
|---|---|
| 用途 | 对 status=paid 的订单按 provider 分组，统计订单数和金额 |
| 鉴权 | 管理员 access token |
| 后端代码 | `backend/app/api/v1/admin.py:83-115` |
| 函数 | `stats` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | 无 |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `provider` | Query | string/null | 否 | null | 当前未限定 wechat/alipay；任意字符串会作为过滤值 |
| `package_id` | Query | string/null | 否 | null | 当前无 UUID/存在性校验 |
| `start_at` | Query | ISO datetime/null | 否 | null | 过滤 `paid_at >= start_at` |
| `end_at` | Query | ISO datetime/null | 否 | null | 过滤 `paid_at <= end_at` |

```ts
type RechargeStatistic = { provider: string; orders: number; amount_fen: number };

const params = new URLSearchParams({
  provider: "wechat",
  start_at: "2026-08-01T00:00:00Z",
  end_at: "2026-08-31T23:59:59Z",
});
const stats = await apiFetch<RechargeStatistic[]>(
  `/api/v1/admin/recharge-statistics?${params}`,
  {},
  adminAccessToken,
);
```

HTTP 200：

```json
[{"provider":"wechat","orders":12,"amount_fen":11880}]
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `provider` | string | 分组渠道 |
| `orders` | integer | paid 订单数 |
| `amount_fen` | integer | paid 订单金额合计，单位分 |

无匹配数据返回 `[]`。`start_at > end_at` 返回 422 `start_at must be before end_at`；datetime 解析错误也是 422；另有 401/403。

⚠️ 当前支付回调不会将任何订单改为 paid，因此正常 API 流程下此接口通常只能得到空数组；示例非当前支付闭环可自然产生的数据。

### 3.6 命理档案与命盘接口

本组全部需要用户 access token。权限查询始终同时限制 `profile_id` 和 `user_id`，不存在和不属于当前用户统一返回 404，避免泄露其他用户档案。

#### 3.6.0 预览、确认和命盘结构约定

实际生成链：

```text
BirthProfileIn
→ chart_profiles._generate (run_in_threadpool)
→ chart_engine.generate_chart
→ app.bazi.birth_input_preview.build_birth_preview
→ app.bazi.bazi_engine.build_bazi_chart
→ GeneratedChart
```

创建/修改没有服务端 preview session 或 preview_id。`input_fingerprint` 与 `chart_fingerprint` 是确定性 64 位小写十六进制摘要，不是一次性 Token，也没有单独 TTL。保存时服务端会重新排盘并与请求中的 `expected_*` 比较；规则或输入改变则 409。

`BaziChartOut.chart` 在 Pydantic 中只约束为 `dict`。当前引擎实际顶层键包括：

```text
profile, pillars, pillar_evidence, calendar_evidence, facts,
public_summary, day_master, hidden_stems, ten_gods, five_elements,
day_master_strength, pattern_analysis, wealth_analysis,
relationship_analysis, dayun_basis, current_context, rule_version,
chart_fingerprint_v2, seasonal_adjustment, time_mode, time_mode_label,
timezone_offset, solar, lunar_text, original_birth_datetime,
adjusted_birth_datetime, true_solar_time_applied,
true_solar_time_warning, use_true_solar_time, birth_longitude,
zi_time_boundary_note, ten_god_counts, ming_gong, shen_gong,
tai_yuan, tai_xi
```

`chart.profile` 会移除 `name` 和 `birth_place`，但仍包含出生日期、性别、时间和历法等排盘事实。`chart.facts` 当前包含：

```text
gender, pillars, day_master, hidden_stems, ten_gods, element_counts,
time_mode, pillar_basis, dayun, strength, pattern, wealth,
relationship, internal_rule_version, rule_ids, current_context
```

⚠️ 这些内部键来自当前 service，未被 `BaziChartOut` 的 response model 逐层锁定。前端优先依赖 `profile`、BaziChartOut 顶层字段以及经过确认的 `chart.facts`；若要生成严格类型，应先让后端细化 `chart` schema。

#### 3.6.1 校验并预览命盘 — `POST /api/v1/chart-profiles/preview`

| 项目 | 内容 |
|---|---|
| 用途 | 校验出生输入、同步排盘并返回双指纹和可确认预览 |
| 后端代码 | `backend/app/api/v1/chart_profiles.py:129-141` |
| 函数 | `preview_birth_profile` |
| 鉴权 | 用户 access token |
| Content-Type | Request/Response `application/json` |
| response_model | `ChartPreviewOut` |
| 数据写入 | 无；只计算 |

Request Body 是 3.0.4 展开的 9 个 `BirthProfileInput` 字段；不要传 profile_id 或 expected fingerprint。

```ts
const birth: BirthProfileInput = {
  name: "张三",
  gender: "男",
  calendar_type: "solar",
  birth_date: "1996-09-04",
  birth_hour: 10,
  birth_minute: 30,
  birth_place: "广东广州",
  is_leap_month: false,
  time_label: "精确时间",
};

const preview = await apiFetch<ChartPreviewOut>(
  "/api/v1/chart-profiles/preview",
  { method: "POST", body: JSON.stringify(birth) },
  accessToken,
);
```

HTTP 200 实测当前输入可得到：

```json
{
  "input_fingerprint":"d33dc64425c51e84e723b65ffbd8af423533b14bbfcea7cbac281c72f6ebabce",
  "chart_fingerprint":"9e69e15bb2f7f5522d8f5a4423889ab621a24c1dde199e5081cfeafd8ded608a",
  "engine_version":"2.0.0",
  "input_text":"公历1996年9月4日，男，精确时间",
  "solar_datetime":"1996-09-04 10:30",
  "pillars":["丙子","丙申","甲辰","己巳"],
  "calculation_basis":"以立春1996-02-04 21:07:54换年，采用1996年干支；最近已过的节为立秋（1996-08-07 13:48:49），按五虎遁取月柱；未到23:00，按当日1996-09-04取日柱；按五鼠遁，以甲日和10:30确定己巳"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| `input_fingerprint` | string | 根据规范化完整输入生成，下一步映射到 expected_input_fingerprint |
| `chart_fingerprint` | string | canonical facts 指纹，下一步映射到 expected_chart_fingerprint |
| `engine_version` | string | 当前规则版本，实测为 2.0.0；不要硬编码 |
| `input_text` | string | 用户确认用文本 |
| `solar_datetime` | string | 换算后的公历日期时间或时辰不详 |
| `pillars` | string[] | 实际固定年/月/日/时 4 项；response schema 只声明 list |
| `calculation_basis` | string | 立春、节气、23 点换日和时柱依据 |

错误：401 认证失败；422 默认 schema 错误，或 `Birth information could not be converted into a chart`。引擎异常不会把内部异常文本返回前端。

#### 3.6.2 确认并创建档案 — `POST /api/v1/chart-profiles`

| 项目 | 内容 |
|---|---|
| 用途 | 重新排盘核对双指纹，在一个事务中保存 BirthProfile 和 BaziChart |
| 后端代码 | `backend/app/api/v1/chart_profiles.py:144-174` |
| 函数 | `create_birth_profile` |
| 鉴权 | 用户 access token |
| Content-Type | Request/Response `application/json` |
| response_model | `BirthProfileDetailOut` |
| 成功状态 | **201 Created** |

Request Body 包含 3.0.4 的全部出生字段，再增加：

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `expected_input_fingerprint` | Body | string | 是 | 无 | `^[0-9a-f]{64}$`；来自本次 preview.input_fingerprint |
| `expected_chart_fingerprint` | Body | string | 是 | 无 | `^[0-9a-f]{64}$`；来自本次 preview.chart_fingerprint |

```ts
const detail = await apiFetch<BirthProfileDetailOut>(
  "/api/v1/chart-profiles",
  {
    method: "POST",
    body: JSON.stringify({
      ...birth,
      expected_input_fingerprint: preview.input_fingerprint,
      expected_chart_fingerprint: preview.chart_fingerprint,
    }),
  },
  accessToken,
);
```

HTTP 201：

```json
{
  "profile": {
    "id":"<profile UUID>",
    "name":"张三",
    "gender":"男",
    "calendar_type":"solar",
    "birth_date":"1996-09-04",
    "solar_birth_date":"1996-09-04",
    "birth_hour":10,
    "birth_minute":30,
    "birth_place":"广东广州",
    "is_leap_month":false,
    "time_label":"精确时间",
    "last_edited_at":null,
    "next_edit_at":null,
    "can_edit":true,
    "created_at":"2026-08-19T12:00:00",
    "updated_at":"2026-08-19T12:00:00"
  },
  "chart": {
    "id":"<chart UUID>",
    "profile_id":"<profile UUID>",
    "input_fingerprint":"<64 hex>",
    "chart_fingerprint":"<64 hex>",
    "engine_version":"2.0.0",
    "chart": {"profile":{},"pillars":{},"facts":{}},
    "generated_at":"2026-08-19T12:00:00"
  }
}
```

上例把动态完整命盘压缩展示；顶层及内部已在 3.6.0 列出。`profile.id` 才是后续 `{profile_id}`，不要使用 `chart.id`。

`BirthProfileOut` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 档案 UUID |
| `name/gender/calendar_type/birth_date` | string | 保存的规范化源输入 |
| `solar_birth_date` | date string | 服务端转换结果，客户端不可指定 |
| `birth_hour/birth_minute` | integer/null | 时间对 |
| `birth_place/time_label` | string | 保存的展示输入 |
| `is_leap_month` | boolean | 农历闰月标志 |
| `last_edited_at` | datetime/null | 最近一次真正修改时间，新建为 null |
| `next_edit_at` | datetime/null | 下次允许修改时间 |
| `can_edit` | boolean | 服务端实时计算的编辑权限 |
| `created_at/updated_at` | datetime string | 数据库时间 |

`BaziChartOut` 字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | string | 命盘快照 UUID |
| `profile_id` | string | 所属档案 ID |
| `input_fingerprint/chart_fingerprint` | string | 保存前重新计算的双指纹 |
| `engine_version` | string | 生成时规则版本 |
| `chart` | object | 完整动态命盘 JSON |
| `generated_at` | datetime string | 该快照生成时间 |

错误：401；409 `Chart result changed; preview and confirm...`；422 schema/排盘失败；数据库未预期错误为 500。指纹不一致时不会写档案或命盘。

#### 3.6.3 查询我的档案列表 — `GET /api/v1/chart-profiles`

| 项目 | 内容 |
|---|---|
| 用途 | 只返回当前用户档案，按 created_at DESC 分页，不含命盘 JSON |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/chart_profiles.py:177-198` |
| 函数 | `list_birth_profiles` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | `list[BirthProfileOut]` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `offset` | Query | integer | 否 | 0 | >= 0 |
| `limit` | Query | integer | 否 | 20 | 1～100 |

```ts
const profiles = await apiFetch<BirthProfileOut[]>(
  "/api/v1/chart-profiles?offset=0&limit=20",
  {},
  accessToken,
);
```

HTTP 200 返回 `BirthProfileOut[]`，字段见 3.6.2；无数据为 `[]`。没有 total/has_more。错误：401；422 Query 校验。

#### 3.6.4 查询档案和命盘 — `GET /api/v1/chart-profiles/{profile_id}`

| 项目 | 内容 |
|---|---|
| 用途 | 返回当前用户拥有的一条档案和对应最新命盘快照 |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/chart_profiles.py:201-206` |
| 函数 | `get_birth_profile` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | `BirthProfileDetailOut` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `profile_id` | Path | string | 是 | 无 | 来自 profile.id；路由不做 UUID 格式校验 |

```ts
const detail = await apiFetch<BirthProfileDetailOut>(
  `/api/v1/chart-profiles/${encodeURIComponent(profileId)}`,
  {},
  accessToken,
);
```

HTTP 200 结构与 3.6.2 完全相同。错误：401；404 `Birth profile not found`（不存在或属于其他用户）或 `Chart has not been generated`（档案存在但快照缺失）。

#### 3.6.5 修改档案并重新排盘 — `PUT /api/v1/chart-profiles/{profile_id}`

| 项目 | 内容 |
|---|---|
| 用途 | 预览确认后修改个人信息，并原子更新/创建对应命盘快照 |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/chart_profiles.py:209-246` |
| 函数 | `update_birth_profile` |
| Content-Type | Request/Response `application/json` |
| response_model | `BirthProfileDetailOut` |
| 并发 | 对档案和命盘使用 `SELECT ... FOR UPDATE` |

Path：`profile_id: string`，必填。Body 与 3.6.2 完全相同：9 个出生字段 + 两个 64 hex expected fingerprint。

```ts
const nextBirth: BirthProfileInput = { ...birth, birth_place: "广东汕头" };
const nextPreview = await apiFetch<ChartPreviewOut>(
  "/api/v1/chart-profiles/preview",
  { method: "POST", body: JSON.stringify(nextBirth) },
  accessToken,
);

const updated = await apiFetch<BirthProfileDetailOut>(
  `/api/v1/chart-profiles/${encodeURIComponent(profileId)}`,
  {
    method: "PUT",
    body: JSON.stringify({
      ...nextBirth,
      expected_input_fingerprint: nextPreview.input_fingerprint,
      expected_chart_fingerprint: nextPreview.chart_fingerprint,
    }),
  },
  accessToken,
);
```

HTTP 200 返回与创建相同的 `BirthProfileDetailOut`。第一次真实修改立即允许；成功后 `edit_count += 1`、写 `last_edited_at`，默认 30 天内 `can_edit=false`。`PROFILE_EDIT_COOLDOWN_DAYS=0` 可关闭。

错误：401；404 档案不属于当前用户/不存在；409 指纹不匹配；422 schema/排盘失败；429 `Birth profile cannot be edited again...`。

⚠️ 当前代码在查询所有权和检查冷却期之前先完成一次排盘及 fingerprint 校验；因此被冷却/不存在的档案请求也会先消耗排盘 CPU，并可能先返回 409/422。前端应按 preview → update 正常流程调用，不要对 429 自动重试。

#### 3.6.6 只读取已保存命盘 — `GET /api/v1/chart-profiles/{profile_id}/chart`

| 项目 | 内容 |
|---|---|
| 用途 | 只返回最新 BaziChart 快照，不返回外层 profile，也不重新计算 |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/chart_profiles.py:249-253` |
| 函数 | `get_birth_chart` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | `BaziChartOut` |

| 参数 | 位置 | 类型 | 必填 | 默认值 | 规则 |
|---|---|---|---|---|---|
| `profile_id` | Path | string | 是 | 无 | 当前用户的 profile.id |

```ts
const chart = await apiFetch<BaziChartOut>(
  `/api/v1/chart-profiles/${encodeURIComponent(profileId)}/chart`,
  {},
  accessToken,
);
```

HTTP 200 返回 3.6.2 中 `chart` 对象的完整结构。错误：401；404 档案不存在/不属于用户，或命盘快照缺失。

#### 3.6.7 使用现有档案重新生成命盘 — `POST /api/v1/chart-profiles/{profile_id}/regenerate`

| 项目 | 内容 |
|---|---|
| 用途 | 规则升级后用数据库内现有个人信息重建快照，不修改个人信息 |
| 鉴权 | 用户 access token |
| 后端代码 | `backend/app/api/v1/chart_profiles.py:256-294` |
| 函数 | `regenerate_birth_chart` |
| Content-Type | Request 无 body；Response `application/json` |
| response_model | `BaziChartOut` |
| 并发 | 锁定 profile 和 chart，避免与编辑并发覆盖 |

只有 Path `profile_id: string`，无 Request Body。

```ts
const regenerated = await apiFetch<BaziChartOut>(
  `/api/v1/chart-profiles/${encodeURIComponent(profileId)}/regenerate`,
  { method: "POST" },
  accessToken,
);
```

HTTP 200 返回新的 `BaziChartOut`：chart ID/profile ID 保持原关联，fingerprint、engine_version、chart 内容和 generated_at 可能更新。不会改变 `edit_count`、last_edited_at 或修改冷却。

错误：401；404 档案不存在/不属于当前用户或命盘快照缺失；422 现有档案已无法被当前引擎转换；未预期数据库/引擎异常为 500。

---

## 4. 鉴权机制

### 4.1 机制结论

| 机制 | 是否存在 | 实际行为 |
|---|---|---|
| JWT | 是 | HS256，issuer 默认 `mingshu-api` |
| Bearer Token | 是 | 受保护接口使用 access token |
| Refresh Token | 是 | JSON body 刷新，不做轮换 |
| Cookie Session | 否 | 后端不 Set-Cookie |
| API Key | 否 | 普通前端接口没有 API Key |
| 用户 ID Header/Query | 否 | 用户身份只取 JWT `sub`，不信任客户端另传 user_id |
| 手机号注册/登录 | 是 | 手机号+密码可直接注册和登录；OTP 注册/登录作为可选路径 |
| 管理员鉴权 | 是 | 数据库用户 `role == "admin"` |

### 4.2 Token 从哪里取得

- `POST /api/v1/auth/password/register`：直接注册并返回 access + refresh。
- `POST /api/v1/auth/otp/login`：返回 access + refresh。
- `POST /api/v1/auth/password/login`：返回 access + refresh。
- `PUT /api/v1/auth/password`：返回新 access + refresh，并使旧 Token 失效。
- `POST /api/v1/auth/password/reset`：返回新 access + refresh，并使旧 Token 失效。
- `POST /api/v1/auth/refresh`：只返回新 access，不返回新 refresh。

### 4.3 Token Claims 和有效期

`backend/app/security.py:18-31` 实际生成：

```json
{
  "sub": "<user UUID>",
  "role": "user",
  "ver": 0,
  "typ": "access",
  "iss": "mingshu-api",
  "exp": 1787283713
}
```

| Claim | 说明 |
|---|---|
| `sub` | 用户 ID |
| `role` | 签发时角色；授权时管理员依赖实际数据库 User 对象，不单独信任 claim role |
| `ver` | 帐号认证版本；密码变化后数据库版本增加，旧 Token 失效 |
| `typ` | `access` 或 `refresh` |
| `iss` | 必须匹配 `JWT_ISSUER` |
| `exp` | 过期时间 |

默认配置：access 30 分钟，refresh 30 天。

### 4.4 请求格式

```http
Authorization: Bearer <access_token>
```

不要把 refresh token 放在 Authorization Header。`CurrentUser` 会逐请求：

1. 验 JWT 签名、issuer、exp。
2. 要求 `typ=access`。
3. 用 `sub` 查询数据库用户。
4. 检查 `is_active`。
5. 检查 token `ver == user.auth_version`。

### 4.5 前端存储

代码没有规定客户端存储位置，也没有 HttpOnly Cookie 登录模式。前端必须自行持有 Token：

- access token 优先只放内存状态。
- 页面刷新恢复若必须持久化 refresh token，需要由前端安全方案决定；直接放 localStorage 会扩大 XSS 风险。
- 当前后端没有 Cookie refresh、logout、单设备撤销或 token blacklist 接口。
- 密码修改/重置后立即用响应的新 Token 原子替换旧 Token。
- 收到 401 时可尝试一次 refresh；refresh 也 401 时清空认证状态并回登录页，避免无限重试。

### 4.6 受保护接口清单

- 用户：`PUT /auth/password`、`/me`、`/points/*`、全部 `/chart-profiles*`、`POST /payments/orders`。
- 管理员：全部 `/admin/*`。
- 公开：密码注册/登录、OTP、密码重置、refresh、微信占位、公开套餐、支付 webhook、两个探针。

支付 webhook 虽公开，但当前固定 501；未来必须由支付平台签名鉴权，不能改成用户 Bearer。

---

## 5. SSE / WebSocket / 流式及文件接口

### 5.1 扫描结论

在根目录 `backend/app` 中未发现：

- `StreamingResponse` / `text/event-stream` / `EventSourceResponse`
- `WebSocket` / `@router.websocket`
- `UploadFile` / `File(...)`
- `Form(...)`
- 后台 task、task_id 或任务状态查询路由

因此当前没有：

- SSE event 格式、`[DONE]` 标志或 EventSource/fetch stream 选择。
- WebSocket URL、客户端消息协议或重连机制。
- multipart/form-data、文件字段、多文件或大小限制。
- 轮询任务链。

前端所有现有接口都使用普通 JSON 请求/响应。排盘 preview、create、update、regenerate 在单个 HTTP 请求中同步等待计算完成。

### 5.2 与旧后端的区别

旧 `bazi_ziwei_app/backend/main.py` 的匿名 Cookie `/api/v1/chart/*` 接口不属于本文件的目标后端。当前独立后端使用 JWT 和 `/api/v1/chart-profiles/*`，前端不要混用：

```text
错误：POST /api/v1/chart/preview + credentials: include
正确：POST /api/v1/chart-profiles/preview + Authorization: Bearer <access>
```

---

## 6. 完整业务调用流程

### 6.1 新用户注册并进入应用

```text
用户输入手机号和密码
  ↓
POST /api/v1/auth/password/register
  ↓
201 access_token + refresh_token + new_user=true
  ↓
GET /api/v1/me (Bearer access)
  ↓
用户信息 + 注册赠送后的 points
```

密码注册不需要短信验证码。数据库事务创建 User、PointBalance，并通过 ledger 增加 `REGISTRATION_BONUS_POINTS`（默认 20）；已注册手机号返回 409，不覆盖原密码。

可选的 OTP 注册/登录流程仍为 `/otp/login/code` → `/otp/login`，但生产短信 adapter 未接入时不可用。

### 6.2 Token 生命周期

```text
业务请求使用 access token
  ↓ 401（可能过期）
POST /api/v1/auth/refresh { refresh_token }
  ├── 200 → 替换 access token，原业务请求最多重试一次
  └── 401 → 清空 access/refresh，回登录页
```

refresh 不轮换。密码设置、修改或重置会让旧 access/refresh 同时失效，并直接返回新 TokenPair。

### 6.3 密码登录和密码管理

```text
密码注册成功
  ↓
以后使用 POST /api/v1/auth/password/login

若用户通过 OTP 注册且 GET /me 返回 has_password=false
  ↓
PUT /api/v1/auth/password { new_password }
  ↓ 保存新 TokenPair
```

已有密码时 PUT 必须提交 current_password。忘记密码流程为 reset/otp → reset，不可使用 login-purpose OTP。

### 6.4 创建命理档案和命盘

```text
用户填写 BirthProfileInput
  ↓
POST /api/v1/chart-profiles/preview (Bearer)
  ↓ 同步排盘，无数据库写入
input_fingerprint + chart_fingerprint + 展示预览
  ↓ 用户检查并确认；输入一旦修改必须重新 preview
POST /api/v1/chart-profiles
  body = 完全相同的出生字段
       + expected_input_fingerprint
       + expected_chart_fingerprint
  ↓ 服务端重新排盘并比较双指纹
201 profile + chart snapshot
  ↓
使用 response.profile.id 进入档案详情页
```

这里没有 preview_id、一次性服务器状态或轮询。指纹不一致为 409，不保存任何数据。

### 6.5 档案列表、详情和编辑

```text
GET /api/v1/chart-profiles?offset=0&limit=20
  ↓ 选择 profile.id
GET /api/v1/chart-profiles/{profile_id}
  ↓ 展示 profile + chart

用户修改个人信息
  ↓ 先 POST /chart-profiles/preview 获取新双指纹
PUT /chart-profiles/{profile_id}
  ├── 200 → 原子更新 profile + chart
  ├── 409 → 输入/规则变化，重新 preview
  └── 429 → 冷却未结束，读取 next_edit_at 展示
```

新建后第一次编辑可立即进行；第一次编辑成功后默认开始 30 天冷却。

### 6.6 点数消费

```text
管理员先配置 active FeatureRule
  ↓
前端为一次业务操作生成固定 idempotency_key
  ↓
POST /api/v1/points/consume
  ├── 200 → 得到 ledger_id 和 balance
  ├── 相同 key 重试 → 返回同一 ledger，不重复扣点
  ├── 404 → 功能规则不存在/未启用
  └── 409 → 点数不足或 key 被挪作其他操作
```

⚠️ 当前没有“扣点 + 生成报告”合并事务接口。若前端先扣点、随后调用另一个尚未存在/失败的功能接口，后端没有自动退款编排。具体付费业务接入前需确认扣点边界。

### 6.7 支付流程（当前不完整）

```text
GET /api/v1/payments/packages
  ↓
POST /api/v1/payments/orders
  ↓
pending + payment_payload=null
  ✕ 无法拉起真实支付
  ✕ webhook 固定 501
  ✕ 不会变 paid
  ✕ 不会增加点数
  ✕ 没有订单状态查询接口
```

前端当前最多展示套餐数据；不要上线购买按钮或伪造支付成功状态。

### 6.8 当前不存在的前端业务

- AI 问答/SSE
- 日、月、年运势 API
- 报告生成/下载 API
- 历史对话 API
- 真实微信扫码登录
- 真实支付、订单查询、退款、订阅续费
- logout/设备会话管理
- 档案删除接口

---

## 7. 前端联调优先级

### P0：最小可运行主流程（8 个）

1. `POST /api/v1/auth/password/register` — 注册页直接创建帐号并保存 TokenPair。
2. `POST /api/v1/auth/password/login` — 登录页手机号密码登录。
3. `POST /api/v1/auth/refresh` — API 客户端统一 401 刷新逻辑。
4. `GET /api/v1/me` — 应用启动恢复用户、密码状态和点数。
5. `POST /api/v1/chart-profiles/preview` — 出生信息确认页。
6. `POST /api/v1/chart-profiles` — 创建档案并进入命盘结果页。
7. `GET /api/v1/chart-profiles` — 我的档案列表。
8. `GET /api/v1/chart-profiles/{profile_id}` — 档案/命盘详情页。

### P1：完整用户功能

- `POST /auth/otp/login/code`、`POST /auth/otp/login` — 可选的验证码注册/登录。
- `PUT /auth/password` — 设置/修改密码。
- `POST /auth/password/reset/otp`、`POST /auth/password/reset` — 忘记密码。
- `GET /points/ledger` — 点数明细。
- `POST /points/consume` — 仅在明确具体付费功能和失败补偿后接入。
- `PUT /chart-profiles/{profile_id}` — 编辑档案。
- `GET /chart-profiles/{profile_id}/chart` — 只需要命盘时调用。
- `POST /chart-profiles/{profile_id}/regenerate` — 规则升级后的重建入口。
- `GET /payments/packages` — 套餐展示可以联调，但购买按钮暂不上线。

### P2：管理后台

- 套餐创建/列表。
- 功能扣点规则 upsert。
- 用户列表和启停。
- 充值统计；当前不会有自然产生的 paid 数据。

### 暂不接入

- `GET /auth/wechat/qr`
- `POST /payments/orders` 的真实支付 UI
- `POST /payments/webhooks/{provider}`（永远不是浏览器接口）

### 7.1 前端联调验收清单

- [ ] Base URL 指向根目录独立后端 8000，不是 Streamlit 8501 或旧 chart API。
- [ ] 浏览器 Origin 已加入 `CORS_ORIGINS`。
- [ ] 密码注册只提交 phone/password，不请求或提交 OTP，也不展示“手机号已验证”。
- [ ] 受保护请求统一携带 `Authorization: Bearer <access_token>`。
- [ ] 不把 refresh token 当 Bearer 使用。
- [ ] API 错误兼容 `detail: string`、`detail: array` 和非 JSON 500。
- [ ] 401 refresh 最多重试一次，避免循环。
- [ ] 密码变化后替换 access/refresh 两枚 Token。
- [ ] profile 创建/修改使用本次 preview 的双指纹和完全相同输入。
- [ ] URL 使用 `profile.id`，不使用 `chart.id`。
- [ ] 429 编辑冷却直接展示 `profile.next_edit_at`，不轮询重试。
- [ ] 列表当前无 total/has_more，按 limit 判断是否继续加载。
- [ ] 不依赖动态 chart 文案、内部键或 engine_version 固定值。
- [ ] 不上线微信扫码和支付按钮。
- [ ] 不把密码、Token、出生信息或完整命盘写入日志/埋点。

---

## 8. 待确认问题

### ⚠️ 待确认 1：密码注册不验证手机号归属，生产短信仍未接入

`POST /auth/password/register` 按当前产品要求无需验证码，只校验手机号格式，因此无法证明注册者拥有该号码，可能产生手机号抢注风险。生产环境 `sms_provider=None`，OTP 登录和密码重置验证码请求仍会返回 503，但不影响密码直接注册。若未来需要验证手机号，应重新确认注册流程，并实现 `SMSProvider.send` 后在启动阶段调用 `register_sms_provider`。

### ⚠️ 待确认 2：微信和支付都是占位

微信 QR 没有 scene/二维码/回调；支付没有 prepay adapter、验签、订单 paid 更新、点数到账、订单查询、退款或订阅逻辑。前端暂不接入。

### ⚠️ 待确认 3：14 个接口缺少 response_model

运行时 OpenAPI 的成功响应 schema 为 `{}`：

```text
GET  /auth/wechat/qr
GET  /me
GET  /points/ledger
POST /points/consume
GET/POST /admin/packages
PUT  /admin/feature-rules/{code}
PATCH /admin/users/{user_id}/active
GET  /admin/recharge-statistics
GET  /payments/packages
POST /payments/orders
POST /payments/webhooks/{provider}
GET  /healthz
GET  /readyz
```

前端可以暂按本文实测结构定义类型，但 OpenAPI codegen 不完整，ORM 直接序列化还可能随模型字段增长意外扩大响应。建议为这些接口补严格 response model。

### ⚠️ 待确认 4：错误没有对外稳定 code

`ErrorDefinition.code` 只留在服务端，响应仍是英文 `detail`。同一个 HTTP status 对应多种原因，前端若按英文文本分支会非常脆弱。建议改为兼容结构，例如：

```json
{"code":"POINTS_INSUFFICIENT","message":"Insufficient points"}
```

### ⚠️ 待确认 5：422 会回显敏感 input

FastAPI 默认验证错误包含 `detail[].input`。实测短密码会原样出现在响应：

```json
{"detail":[{"loc":["body","password"],"input":"secret"}]}
```

需要统一 `RequestValidationError` handler，对 password/current_password/new_password、Token 和未来密钥字段做脱敏。

### ⚠️ 待确认 6：停用用户仍可走部分 OTP 流程

`verify_otp` 没有检查已有 User 的 `is_active`：

- 停用用户可能 OTP 登录成功并收到随后不能使用的 Token。
- 停用用户可能通过 reset OTP 修改密码并收到不能使用的 Token。

应确认产品预期并在 service 层统一阻止或明确返回 401。

### ⚠️ 待确认 7：命盘 JSON 仍是动态 dict

`BaziChartOut.chart: dict` 没有嵌套 schema，前端无法从 OpenAPI 获得完整命盘类型。本文列出了当前实际键，但它们不是被 response model 锁定的契约。

### ⚠️ 待确认 8：档案更新先计算、后鉴权资源和冷却

update 路由先 `_generate` / `_confirm`，再查询并锁定 profile、检查冷却。这会让无权、资源不存在或冷却中的请求先消耗排盘 CPU，且可能先返回 409/422 而不是 404/429。建议后端调整执行顺序。

### ⚠️ 待确认 9：部分数据库长度没有 Pydantic 前置校验

例如套餐 name 数据库长 100、feature code 长 64，但对应 request/path 没有 max_length。超长输入在 MySQL 可能变成数据库异常，而不是可预期的 422。

### ⚠️ 待确认 10：时间字符串时区表现

ORM 时间列声明 `DateTime(timezone=True)`，但 SQLite 实测 JSON 如 `2026-08-21T03:11:53` 不带 `Z`/offset。前端应先按 ISO 字符串处理，不要假设所有环境都有 `Z`；后端应决定统一 UTC 序列化契约。

### ⚠️ 待确认 11：缺少订单查询和扣点业务编排

没有获取支付订单状态的接口；点数扣减也没有与报告/分析生成放在同一事务或补偿流程。具体付费功能上线前必须补齐状态机和失败补偿。

### ⚠️ 待确认 12：HTTP 行为测试覆盖不完整

35 个测试全部通过；密码直接注册已有成功、重复手机号、字段错误、密码登录、赠送点数、密码摘要和零 OTP 记录的 HTTP 回归测试。但公开套餐、支付建单、点数流水、管理员查询套餐、用户启停、充值统计、有效 refresh 成功等路由仍缺少各自明确的 HTTP 成功/错误测试。本文对这些接口额外做了测试客户端实测，但建议沉淀成回归用例。

### ⚠️ 待确认 13：依赖版本未锁定

`pyproject.toml`/`requirements-prod.txt` 多数使用范围版本，没有 lockfile。FastAPI/Starlette 行为可能随部署时间变化；本次测试已出现 TestClient deprecation warning，`@app.on_event` 也被 FastAPI 标记废弃。建议建立可重复的生产锁定策略。

---

## 附录 A：实际代码证据索引

| 内容 | 文件 |
|---|---|
| FastAPI、CORS、探针、总 router 挂载 | `backend/app/main.py` |
| `/api/v1` 聚合 | `backend/app/api/v1/router.py` |
| OTP、密码、JWT 刷新、微信占位 | `backend/app/api/v1/auth.py` |
| 当前用户、流水、扣点 | `backend/app/api/v1/users.py` |
| 管理员接口 | `backend/app/api/v1/admin.py` |
| 套餐查询、订单、webhook 占位 | `backend/app/api/v1/payments.py` |
| 命理档案 7 个路由 | `backend/app/api/v1/chart_profiles.py` |
| 全部 request/已声明 response schema | `backend/app/schemas.py` |
| JWT 生成和 CurrentUser/AdminUser | `backend/app/security.py` |
| OTP、密码、点数 service | `backend/app/services.py` |
| 业务错误目录 | `backend/app/errors.py` |
| ORM models | `backend/app/models.py` |
| 排盘适配和 PII 去重 | `backend/app/chart_engine.py` |
| 配置项 | `backend/app/config.py` |
| 数据库/Redis Depends | `backend/app/database.py`、`backend/app/cache.py` |
| API 测试 | `backend/tests/` |

## 附录 B：当前验证记录

```text
运行时 OpenAPI operations: 30
GET 12 / POST 14 / PUT 3 / PATCH 1 / DELETE 0
pytest: 35 passed, 3 warnings
docker compose --env-file .env.example config --quiet: passed
ruff: 4 errors，均为 tests/test_services.py 导入排序/未使用导入
```

本次已新增无需验证码的密码注册接口、回归测试和 Docker 模块路径修复，并同步本文档；没有触碰工作区原有的其他修改。
