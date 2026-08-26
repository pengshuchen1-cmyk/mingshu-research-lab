# 明枢后端 API 文档（v1）

本文档对应当前 FastAPI 后端实现，适合前端联调、ApiPost 测试和人工查阅。

后端同时提供以下三种接口文档：

- 本文档：`API.md`，包含业务说明、参数规则和完整示例。
- Swagger UI：`GET /docs`，本地默认地址为 <http://127.0.0.1:8000/docs>。
- OpenAPI JSON：`GET /openapi.json`，可导入 ApiPost 等接口工具。

## 1. 基本约定

### 1.1 地址

本机开发地址：

```text
http://127.0.0.1:8000
```

业务接口统一前缀为 `/api/v1`。运维探针 `/healthz` 和 `/readyz` 不使用该前缀。

### 1.2 数据格式

- 请求和响应使用 JSON，请求头使用 `Content-Type: application/json`。
- 时间使用 ISO 8601 格式，例如 `2026-08-17T12:30:00Z`。
- 金额单位统一为“分”，例如 `990` 表示人民币 `9.90` 元。
- 点数为整数，ID 当前使用长度为 36 的 UUID 字符串。
- 中国大陆手机号可以提交 `13800138000` 或 `+8613800138000`，服务端会转换为 E.164 格式。

### 1.3 认证

标记为“用户”或“管理员”的接口必须携带访问令牌：

```http
Authorization: Bearer <access_token>
```

注意 `Bearer` 和令牌之间有一个空格。`refresh_token` 不能作为 Bearer 令牌调用业务接口。

### 1.4 通用错误

普通业务错误：

```json
{
  "detail": "错误原因"
}
```

业务错误的内部编码、HTTP 状态码和提示信息统一定义在
`app/errors.py` 的 `Errors` 中，路由、认证依赖和服务代码不再自行维护错误文案。
当前响应格式保持兼容，仍返回字符串形式的 `detail`；`ErrorDefinition.code` 是供后端
定位和后续扩展使用的稳定内部编码，暂不作为接口字段返回。

参数校验错误通常返回 `422`，格式类似：

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

| 状态码 | 含义 |
|---|---|
| `200` | 请求成功 |
| `401` | 未登录、令牌错误、令牌过期、密码错误或用户已停用 |
| `403` | 当前用户不是管理员 |
| `404` | 用户、套餐、功能规则、命理档案、命盘或支付渠道不存在 |
| `409` | 新旧密码相同、点数不足、幂等键冲突，或保存时的命盘与预览结果不一致 |
| `422` | 请求体、路径参数或查询参数不合法 |
| `429` | 验证码受限、密码连续输错后暂时锁定，或命理档案尚未到允许修改的日期 |
| `501` | 预留接口尚未接入真实适配器 |
| `503` | 短信服务未配置，或 MySQL/Redis 尚未就绪 |

## 2. 快速完成一次注册登录

注册没有单独接口。手机号第一次验证码登录成功时会自动注册，并赠送配置的注册点数。

1. 调用 `POST /api/v1/auth/otp/login/code` 获取登录验证码。
2. 开发环境从 `development_code` 取得验证码。
3. 调用 `POST /api/v1/auth/otp/login` 完成注册或登录。
4. 保存返回的 `access_token` 和 `refresh_token`。
5. 携带 access token 调用 `GET /api/v1/me` 验证登录状态。
6. 如需以后使用密码登录，携带 access token 调用 `PUT /api/v1/auth/password` 设置首个密码。

生产环境不会在响应中返回验证码；当前尚未注册真实短信适配器，因此生产环境请求验证码会返回 `503`。

## 3. 认证接口

### 3.1 获取短信验证码

```http
POST /api/v1/auth/otp/login/code
```

权限：公开。

| 字段 | 位置 | 类型 | 必填 | 规则 |
|---|---|---:|:---:|---|
| `phone` | JSON Body | string | 是 | 有效手机号；中国号码支持国内格式或 `+86` 格式 |

请求示例：

```json
{
  "phone": "13800138000"
}
```

开发环境成功响应：

```json
{
  "message": "OTP sent",
  "development_code": "123456"
}
```

规则：验证码为 6 位数字，默认有效期 5 分钟，60 秒内不能重复发送，每个手机号每天最多请求 10 次。生产环境不返回真实验证码。

可能错误：`401` 用户已停用；`422` 手机号无效；`429` 请求过于频繁或达到每日上限；`503` 生产短信适配器未配置。

### 3.2 验证验证码并注册/登录

```http
POST /api/v1/auth/otp/login
```

权限：公开。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `phone` | string | 是 | 与获取验证码时使用的手机号一致 |
| `code` | string | 是 | 正好 6 位数字 |

请求示例：

```json
{
  "phone": "13800138000",
  "code": "123456"
}
```

成功响应：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "new_user": true
}
```

| 字段 | 类型 | 说明 |
|---|---:|---|
| `access_token` | string | 调用受保护接口的短期 JWT |
| `refresh_token` | string | 用于换取新 access token 的长期 JWT |
| `token_type` | string | 固定为 `bearer` |
| `new_user` | boolean | `true` 表示本次自动注册；`false` 表示已有用户登录 |

验证码错误会累加失败次数，默认达到 5 次后锁定本次验证码；验证码成功使用后不能再次使用。

可能错误：`400` 验证码错误、过期或已使用；`401` 用户已停用；`422` 手机号或验证码格式不正确；`429` 错误次数达到上限。

### 3.3 设置或修改密码

```http
PUT /api/v1/auth/password
```

权限：用户。需要 Bearer access token。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `current_password` | string | 修改已有密码时是 | 8～128 个字符；首次设置密码时省略 |
| `new_password` | string | 是 | 8～128 个字符 |

首次设置密码：

```json
{
  "new_password": "My-Secure-Passphrase-2026"
}
```

修改已有密码：

```json
{
  "current_password": "My-Secure-Passphrase-2026",
  "new_password": "My-New-Passphrase-2027"
}
```

成功响应会返回一组新的令牌：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "new_user": false
}
```

密码设置或修改成功后，之前签发的所有 access token 和 refresh token 都会失效，客户端必须立即保存本次返回的新令牌。

可能错误：`400` 已有密码但未提交当前密码；`401` 当前密码错误或登录令牌无效；`409` 新密码与当前密码相同；`422` 密码长度或请求格式不正确。

### 3.4 手机号密码登录

```http
POST /api/v1/auth/password/login
```

权限：公开。用户必须已经通过短信登录并设置过密码。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `phone` | string | 是 | 注册时使用的有效手机号 |
| `password` | string | 是 | 8～128 个字符 |

请求示例：

```json
{
  "phone": "13800138000",
  "password": "My-Secure-Passphrase-2026"
}
```

成功响应与短信登录相同，其中 `new_user` 固定为 `false`。

可能错误：`401` 手机号不存在、尚未设置密码、密码错误或用户已停用；`429` 连续输错达到上限，密码登录被暂时锁定；`422` 手机号或密码格式不正确。为避免泄露帐号是否存在，前三类失败使用相同的错误信息。

### 3.5 获取密码重置验证码

```http
POST /api/v1/auth/password/reset/otp
```

权限：公开。请求体与 `POST /api/v1/auth/otp/login/code` 相同：

```json
{
  "phone": "13800138000"
}
```

该验证码只允许用于密码重置，不能用于注册登录；普通登录验证码也不能用于重置密码。发送频率、每日上限和开发环境响应格式与登录验证码相同。用户已停用时返回 `401`，不会发送重置验证码。

### 3.6 使用短信验证码重置密码

```http
POST /api/v1/auth/password/reset
```

权限：公开。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `phone` | string | 是 | 获取重置验证码时使用的手机号 |
| `code` | string | 是 | 正好 6 位数字 |
| `new_password` | string | 是 | 8～128 个字符 |

请求示例：

```json
{
  "phone": "13800138000",
  "code": "123456",
  "new_password": "My-New-Passphrase-2027"
}
```

成功响应是一组新的 access token 和 refresh token。重置成功后会解除密码登录锁定，并使此前所有令牌失效。

可能错误：`400` 验证码错误、过期或已使用；`401` 帐号不可用；`422` 字段格式不正确；`429` 验证码错误次数达到上限。

### 3.7 刷新访问令牌

```http
POST /api/v1/auth/refresh
```

权限：公开，但必须提供有效 refresh token。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `refresh_token` | string | 是 | 登录接口返回的刷新令牌 |

请求示例：

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

成功响应：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

可能错误：`401` 令牌无效、令牌类型不是 refresh、令牌已过期或用户已停用。

当前尚未实现 refresh token 的逐次轮换、单设备撤销和退出登录会话管理。修改或重置密码时可以通过帐号认证版本统一撤销该用户此前签发的令牌。

### 3.8 微信扫码登录预留接口

```http
GET /api/v1/auth/wechat/qr
```

权限：公开。当前不可用于真实登录，未配置微信 App ID 时返回 `501`：

```json
{
  "detail": "WeChat QR login is not configured"
}
```

## 4. 当前用户与点数接口

### 4.1 查询当前用户

```http
GET /api/v1/me
```

权限：用户。需要 Bearer access token。无请求参数。

成功响应：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "phone": "+8613800138000",
  "role": "user",
  "has_password": true,
  "points": 20,
  "created_at": "2026-08-26T03:20:15Z",
  "companion_days": 1
}
```

| 字段 | 类型 | 说明 |
|---|---:|---|
| `id` | string | 用户 ID |
| `phone` | string/null | E.164 格式手机号 |
| `role` | string | `user` 或 `admin` |
| `has_password` | boolean | 当前账号是否已经设置密码 |
| `points` | integer | 当前可用点数 |
| `created_at` | string(datetime) | 账号创建时间，使用 UTC ISO 8601 格式返回 |
| `companion_days` | integer | 陪伴天数；按照 `APP_TIMEZONE` 的自然日计算，注册当天为第 1 天 |

`companion_days` 是服务端根据 `created_at` 实时计算的派生值，不存入数据库。前端首页应直接展示该字段，不要根据客户端时间重复计算。默认业务时区为 `Asia/Shanghai`，可通过服务端环境变量 `APP_TIMEZONE` 修改。

可能错误：`401` access token 缺失、无效、过期或用户已停用。

### 4.2 查询点数流水

```http
GET /api/v1/points/ledger
```

权限：用户。需要 Bearer access token。当前版本不分页，按创建时间从新到旧返回当前用户全部流水。

成功响应示例：

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

`delta` 大于 0 表示增加点数，小于 0 表示扣减点数；`balance_after` 是该笔业务完成后的余额。

### 4.3 消耗点数

```http
POST /api/v1/points/consume
```

权限：用户。需要 Bearer access token。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `feature_code` | string | 是 | 管理员已启用的功能编码，例如 `ziwei_report` |
| `idempotency_key` | string | 是 | 长度 8～128；同一用户的一次业务操作必须固定且唯一 |

请求示例：

```json
{
  "feature_code": "ziwei_report",
  "idempotency_key": "report-550e8400-20260817-001"
}
```

成功响应：

```json
{
  "ledger_id": "24770e92-c67e-4140-a19f-7637e0a5567f",
  "balance": 17
}
```

同一用户使用相同幂等键重复提交同一操作，不会重复扣点；相同键用于不同操作时返回 `409`。

可能错误：`404` 功能规则不存在或未启用；`409` 点数不足或幂等键冲突；`422` 幂等键长度不合法。

## 5. 套餐与支付接口

### 5.1 查询可购买套餐

```http
GET /api/v1/payments/packages
```

权限：公开。无请求参数，只返回已启用套餐。

成功响应示例：

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

`kind` 允许 `one_time` 和 `monthly`，但 `monthly` 尚未实现自动续费、到期或周期权益结算。

### 5.2 创建支付订单

```http
POST /api/v1/payments/orders
```

权限：用户。需要 Bearer access token。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `package_id` | string | 是 | 已启用套餐的 UUID |
| `provider` | string | 是 | 只能是 `wechat` 或 `alipay` |

请求示例：

```json
{
  "package_id": "b1acb40e-8265-4b0d-9083-31e7803a8c65",
  "provider": "wechat"
}
```

当前成功响应：

```json
{
  "order_id": "41a957d9-12f9-4394-b13c-e6aed89d996d",
  "status": "pending",
  "provider": "wechat",
  "payment_payload": null
}
```

当前只创建 `pending` 订单。微信/支付宝预支付适配器尚未实现，因此 `payment_payload` 为 `null`，暂时不能完成真实付款。

可能错误：`401` 未登录；`404` 套餐不存在或未启用；`422` provider 不合法。

### 5.3 支付平台回调预留接口

```http
POST /api/v1/payments/webhooks/{provider}
```

权限：支付平台回调，不使用用户 Bearer token。

| 字段 | 位置 | 类型 | 必填 | 规则 |
|---|---|---:|:---:|---|
| `provider` | Path | string | 是 | `wechat` 或 `alipay` |
| `event_id` | JSON Body | string | 是 | 平台事件 ID |
| `order_id` | JSON Body | string | 是 | 本系统订单 ID |
| `provider_trade_no` | JSON Body | string | 是 | 平台交易号 |

当前占位请求示例：

```json
{
  "event_id": "platform-event-001",
  "order_id": "41a957d9-12f9-4394-b13c-e6aed89d996d",
  "provider_trade_no": "platform-trade-001"
}
```

当前固定安全返回 `501`：

```json
{
  "detail": "Payment provider signature verification is not configured"
}
```

当前不会根据回调修改订单或增加点数。真实接入时必须验证平台签名/证书、App ID、商户号、订单归属和金额。

## 6. 管理员接口

管理员接口必须使用 `role=admin` 用户的 access token。当前没有公开的“注册管理员”接口，管理员角色需要通过受控运维流程授予。

### 6.1 创建点数套餐

```http
POST /api/v1/admin/packages
```

权限：管理员。

| 字段 | 类型 | 必填 | 规则 |
|---|---:|:---:|---|
| `name` | string | 是 | 套餐名称；数据库要求唯一 |
| `kind` | string | 是 | `one_time` 或 `monthly` |
| `points` | integer | 是 | 大于 0 |
| `price_fen` | integer | 是 | 大于 0，单位为分 |
| `active` | boolean | 否 | 默认 `true` |

请求示例：

```json
{
  "name": "100点",
  "kind": "one_time",
  "points": 100,
  "price_fen": 990,
  "active": true
}
```

成功响应示例：

```json
{
  "id": "b1acb40e-8265-4b0d-9083-31e7803a8c65",
  "name": "100点",
  "kind": "one_time",
  "points": 100,
  "price_fen": 990,
  "active": true,
  "created_at": "2026-08-17T12:30:00"
}
```

套餐名称重复时返回 `409 Conflict`：

```json
{
  "detail": "Package name already exists"
}
```

### 6.2 查询全部套餐

```http
GET /api/v1/admin/packages
```

权限：管理员。无请求参数。与公开套餐接口不同，本接口包括未启用套餐。响应格式为套餐对象数组，字段与创建套餐响应一致。

### 6.3 新增或更新功能扣点规则

```http
PUT /api/v1/admin/feature-rules/{code}
```

权限：管理员。

| 字段 | 位置 | 类型 | 必填 | 规则 |
|---|---|---:|:---:|---|
| `code` | Path | string | 是 | 功能编码，例如 `ziwei_report`；数据库最长 64 字符 |
| `points_cost` | JSON Body | integer | 是 | 大于或等于 0 |
| `active` | JSON Body | boolean | 否 | 默认 `true` |

请求示例：

```json
{
  "points_cost": 3,
  "active": true
}
```

成功响应示例：

```json
{
  "feature_code": "ziwei_report",
  "points_cost": 3,
  "active": true,
  "updated_at": "2026-08-17T12:30:00"
}
```

### 6.4 查询用户列表

```http
GET /api/v1/admin/users
```

权限：管理员。

| 字段 | 类型 | 必填 | 默认值 | 规则 |
|---|---:|:---:|---:|---|
| `phone` | string | 否 | 无 | 按手机号片段模糊查询 |
| `offset` | integer | 否 | `0` | 大于或等于 0 |
| `limit` | integer | 否 | `20` | 1～100 |

请求示例：

```http
GET /api/v1/admin/users?phone=138&offset=0&limit=20
```

成功响应示例：

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "phone": "+8613800138000",
    "role": "user",
    "is_active": true,
    "created_at": "2026-08-17T12:30:00"
  }
]
```

当前响应不包含总记录数，前端通过返回条数和下一页请求判断是否继续加载。

### 6.5 启用或停用用户

```http
PATCH /api/v1/admin/users/{user_id}/active
```

权限：管理员。

| 字段 | 位置 | 类型 | 必填 | 说明 |
|---|---|---:|:---:|---|
| `user_id` | Path | string | 是 | 目标用户 UUID |
| `is_active` | JSON Body | boolean | 是 | `true` 启用，`false` 停用 |

请求示例：

```json
{
  "is_active": false
}
```

成功响应：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "is_active": false
}
```

停用后，目标用户不能获取或验证登录验证码、使用密码登录、获取密码重置验证码、刷新令牌或调用需要登录的接口。启用、停用状态每次真正发生变化时都会撤销此前签发的 access token 和 refresh token，因此重新启用后用户必须重新登录。可能错误：`404` 用户不存在。

### 6.6 查询充值统计

```http
GET /api/v1/admin/recharge-statistics
```

权限：管理员。

| 字段 | 类型 | 必填 | 示例 | 说明 |
|---|---:|:---:|---|---|
| `provider` | string | 否 | `wechat` | 支付渠道，预期为 `wechat` 或 `alipay` |
| `package_id` | string | 否 | UUID | 套餐 ID |
| `start_at` | datetime | 否 | `2026-08-01T00:00:00Z` | 支付时间起点，包含边界 |
| `end_at` | datetime | 否 | `2026-08-31T23:59:59Z` | 支付时间终点，包含边界 |

请求示例：

```http
GET /api/v1/admin/recharge-statistics?provider=wechat&start_at=2026-08-01T00%3A00%3A00Z&end_at=2026-08-31T23%3A59%3A59Z
```

成功响应示例：

```json
[
  {
    "provider": "wechat",
    "orders": 12,
    "amount_fen": 11880
  }
]
```

只统计状态为 `paid` 的订单，并按支付渠道分组。`amount_fen` 单位为分。`start_at` 晚于 `end_at` 时返回 `422`。

## 7. 命理档案与命盘接口

本组接口均要求用户登录。一个用户可以保存多个命理档案，每个档案保存一份由确定性
排盘引擎生成的最新命盘快照。创建和修改必须遵循“预览 → 用户确认 → 保存”的顺序，
不能直接用未经确认的输入创建命盘。

存储采用“档案为事实来源 + 命盘为版本化快照”的混合方案：个人信息只以命理档案为准，
命盘 JSON 不重复保存姓名和出生地点；登录和普通查询直接读取快照，不重复计算；个人
信息修改或排盘规则升级时再重新生成。快照同时记录输入指纹、命盘指纹和引擎版本。

接口之间的数据传递关系如下：

| 数据 | 从哪里取得 | 传到哪里 |
|---|---|---|
| 个人信息字段 | 用户在前端或 ApiPost 中填写 | 先传给预览接口；确认未修改后，再原样传给创建或修改接口 |
| `expected_input_fingerprint` | 本次预览响应的 `input_fingerprint` | 创建或修改请求体 |
| `expected_chart_fingerprint` | 本次预览响应的 `chart_fingerprint` | 创建或修改请求体 |
| `profile_id` | 创建接口响应的 `profile.id`，或档案列表每一项的 `id` | 查询、修改、读取命盘和重新生成接口的 URL 路径 |
| access token | 短信登录或密码登录响应的 `access_token` | 本组所有接口的 `Authorization: Bearer <access_token>` 请求头 |

两个指纹不是客户端自行计算的，也不能从旧档案或另一次预览中复制。它们只用于证明：
用户最终确认的个人信息与服务端保存前重新生成的命盘完全一致。

### 7.1 个人信息字段

预览、创建和修改共用以下个人信息：

| 字段 | 类型 | 必填 | 示例 | 规则 |
|---|---:|:---:|---|---|
| `name` | string | 是 | `张三` | 1～100 字符 |
| `gender` | string | 是 | `男` | 只能是 `男` 或 `女` |
| `calendar_type` | string | 是 | `solar` | `solar` 公历，`lunar` 农历 |
| `birth_date` | string | 是 | `1996-09-04` | `YYYY-MM-DD`；表示原始历法下的年月日，年份从 1900 至今年 |
| `birth_hour` | integer/null | 否 | `10` | 0～23；未知时与 `birth_minute` 同时传 `null` |
| `birth_minute` | integer/null | 否 | `30` | 0～59；未知时与 `birth_hour` 同时传 `null` |
| `birth_place` | string | 否 | `广东广州` | 最多 200 字符；当前不参与真太阳时换算 |
| `is_leap_month` | boolean | 否 | `false` | 仅农历输入可以为 `true` |
| `time_label` | string | 否 | `精确时间` | 用于记录用户选择的时间精度或传统时辰标签 |

当前排盘沿用原项目的中国标准时间策略，不支持真太阳时。`solar_birth_date` 是服务端换算
并保存的公历日期，客户端不能直接指定。

### 7.2 校验并预览命盘

```http
POST /api/v1/chart-profiles/preview
```

权限：用户。请求示例：

请求体来源：用户当前填写的个人信息。预览请求不要提交 `profile_id`，也不要提交
`expected_input_fingerprint` 或 `expected_chart_fingerprint`。

```json
{
  "name": "张三",
  "gender": "男",
  "calendar_type": "solar",
  "birth_date": "1996-09-04",
  "birth_hour": 10,
  "birth_minute": 30,
  "birth_place": "广东广州",
  "is_leap_month": false,
  "time_label": "精确时间"
}
```

成功响应示例：

```json
{
  "input_fingerprint": "64位十六进制输入指纹",
  "chart_fingerprint": "64位十六进制命盘指纹",
  "engine_version": "2.0.0",
  "input_text": "公历1996年9月4日，男，精确时间",
  "solar_datetime": "1996-09-04 10:30",
  "pillars": ["丙子", "丙申", "甲辰", "己巳"],
  "calculation_basis": "排盘采用中国标准时间……"
}
```

成功响应字段：

| 字段 | 类型 | 来源与用途 |
|---|---:|---|
| `input_fingerprint` | string | 服务端根据本次全部个人信息生成的 64 位指纹；下一步原样复制到 `expected_input_fingerprint` |
| `chart_fingerprint` | string | 服务端根据本次排盘结果生成的 64 位指纹；下一步原样复制到 `expected_chart_fingerprint` |
| `engine_version` | string | 本次使用的排盘引擎/规则版本，用于判断快照是否需要重新生成 |
| `input_text` | string | 服务端整理的出生信息说明，供用户确认输入是否正确 |
| `solar_datetime` | string | 农历换算或公历校验后的实际排盘时间 |
| `pillars` | array[string] | 按年、月、日、时顺序返回的四柱 |
| `calculation_basis` | string | 时间标准、换算方式等排盘依据说明 |

前端应把两个指纹连同原个人信息暂存，并让用户检查输入文本、换算日期和四柱。用户修改
任何输入后必须重新预览。即使只修改姓名、出生地点或时间标签，旧输入指纹也不能继续
使用。此接口只计算并返回预览，不写数据库，也不会产生 `profile_id`。

### 7.3 确认并新建命理档案

```http
POST /api/v1/chart-profiles
```

权限：用户。请求体由两部分组成：

1. 与刚才预览请求完全相同的个人信息。
2. 从该次预览响应中原样复制并改名的两个指纹。

```json
{
  "name": "张三",
  "gender": "男",
  "calendar_type": "solar",
  "birth_date": "1996-09-04",
  "birth_hour": 10,
  "birth_minute": 30,
  "birth_place": "广东广州",
  "is_leap_month": false,
  "time_label": "精确时间",
  "expected_input_fingerprint": "预览返回的64位输入指纹",
  "expected_chart_fingerprint": "预览返回的64位命盘指纹"
}
```

字段对应关系必须是：

```text
预览响应 input_fingerprint  → 创建请求 expected_input_fingerprint
预览响应 chart_fingerprint  → 创建请求 expected_chart_fingerprint
```

服务端会再次排盘并核对两个指纹，完全一致后才在同一数据库事务中保存档案和命盘。
成功返回 `201`，响应结构为：

```json
{
  "profile": {
    "id": "档案UUID",
    "name": "张三",
    "gender": "男",
    "calendar_type": "solar",
    "birth_date": "1996-09-04",
    "solar_birth_date": "1996-09-04",
    "birth_hour": 10,
    "birth_minute": 30,
    "birth_place": "广东广州",
    "is_leap_month": false,
    "time_label": "精确时间",
    "last_edited_at": null,
    "next_edit_at": null,
    "can_edit": true,
    "created_at": "2026-08-19T12:00:00Z",
    "updated_at": "2026-08-19T12:00:00Z"
  },
  "chart": {
    "id": "命盘UUID",
    "profile_id": "档案UUID",
    "input_fingerprint": "64位输入指纹",
    "chart_fingerprint": "64位命盘指纹",
    "engine_version": "2.0.0",
    "chart": {"profile": {}, "pillars": {}, "chart_facts": {}},
    "generated_at": "2026-08-19T12:00:00Z"
  }
}
```

响应由两部分组成：

| 字段 | 来源与用途 |
|---|---|
| `profile` | 已保存的命理档案和当前修改状态 |
| `profile.id` | 数据库生成的档案 ID；后续作为 URL 中的 `{profile_id}` |
| `profile.solar_birth_date` | 服务端根据输入历法换算得到的公历日期，不由客户端提交 |
| `profile.last_edited_at` | 最近一次真正修改个人信息的时间；刚创建时为 `null` |
| `profile.next_edit_at` | 下次允许修改的时间；没有冷却限制时为 `null` |
| `profile.can_edit` | 服务端根据修改次数、最近修改时间和冷却配置实时计算 |
| `profile.created_at` / `updated_at` | 数据库记录的创建时间和最近更新时间 |
| `chart` | 与该档案一同保存的最新命盘快照 |
| `chart.id` | 命盘快照自身 ID，不能代替 `profile.id` 放入档案接口 URL |
| `chart.profile_id` | 该命盘所属档案的 ID，与 `profile.id` 相同 |
| `chart.input_fingerprint` | 服务端保存前重新计算并确认通过的输入指纹 |
| `chart.chart_fingerprint` | 服务端保存前重新计算并确认通过的命盘指纹 |
| `chart.engine_version` | 生成这份命盘快照时使用的规则版本 |
| `chart.chart` | 完整命盘数据，供后续命盘展示和分析使用 |
| `chart.generated_at` | 当前命盘快照的生成时间 |

`chart` 字段是完整排盘 JSON，上例只展示结构。新建档案后允许立即进行第一次修改；
第一次修改成功后才开始计算冷却时间。后续接口 URL 需要使用的 `profile_id`，就是本次
响应中的 `profile.id`，不是 `chart.id`。指纹不一致返回 `409` 且不保存任何数据。

### 7.4 查询我的命理档案列表

```http
GET /api/v1/chart-profiles?offset=0&limit=20
```

权限：用户。`offset` 最小为 0，`limit` 为 1～100。返回当前用户的档案数组，不包含
完整命盘；每项中的 `can_edit` 和 `next_edit_at` 可直接用于前端按钮状态和提示。

响应示例：

```json
[
  {
    "id": "b3bcb9f0-f9e1-4cab-bd69-cf1b0599533a",
    "name": "张三",
    "gender": "男",
    "calendar_type": "solar",
    "birth_date": "1996-09-04",
    "solar_birth_date": "1996-09-04",
    "birth_hour": 10,
    "birth_minute": 30,
    "birth_place": "广东广州",
    "is_leap_month": false,
    "time_label": "精确时间",
    "last_edited_at": null,
    "next_edit_at": null,
    "can_edit": true,
    "created_at": "2026-08-19T12:00:00Z",
    "updated_at": "2026-08-19T12:00:00Z"
  }
]
```

例如要修改上面这条档案，URL 中的 `{profile_id}` 应替换为数组元素的 `id`：

```http
PUT /api/v1/chart-profiles/b3bcb9f0-f9e1-4cab-bd69-cf1b0599533a
```

### 7.5 查询档案和命盘

```http
GET /api/v1/chart-profiles/{profile_id}
```

权限：用户。返回结构与创建成功响应相同。只能读取自己的档案；档案不存在或属于其他
用户时统一返回 `404`，避免泄露其他用户的数据。这里的 `{profile_id}` 来自创建响应的
`profile.id` 或 7.4 列表元素的 `id`。

### 7.6 修改个人信息并重新排盘

```http
PUT /api/v1/chart-profiles/{profile_id}
```

权限：用户。请求体与 7.3 完全相同，因此修改前也必须先用 7.2 对新信息进行预览。
第一次修改可以立即进行。修改成功后会在同一事务中更新个人信息和命盘快照，并开始或
重新开始冷却周期。

ApiPost 测试修改接口时，按以下顺序操作：

1. 从创建响应或档案列表取得要修改档案的 `profile.id`。
2. 将修改后的个人信息发送给 `POST /api/v1/chart-profiles/preview`。
3. 检查预览响应，然后复制本次响应的两个指纹。
4. 向 `PUT /api/v1/chart-profiles/{profile_id}` 提交与第 2 步完全相同的个人信息，并加入两个指纹。

例如预览响应为：

```json
{
  "input_fingerprint": "6273d8365ab0009cfbc6af26948f1a6a30d473cf5600240b262fd3c14ef06d6d",
  "chart_fingerprint": "f100098b5c36936e1a44d78f6f5e558a2beda54bd21cd1f418a70b9248ff75be",
  "engine_version": "2.0.0",
  "input_text": "……",
  "solar_datetime": "2000-09-04 10:30",
  "pillars": ["……", "……", "……", "……"],
  "calculation_basis": "……"
}
```

修改请求中必须对应填写：

```json
{
  "name": "张三丰",
  "gender": "男",
  "calendar_type": "solar",
  "birth_date": "2000-09-04",
  "birth_hour": 10,
  "birth_minute": 30,
  "birth_place": "广东汕头",
  "is_leap_month": false,
  "time_label": "精确时间",
  "expected_input_fingerprint": "6273d8365ab0009cfbc6af26948f1a6a30d473cf5600240b262fd3c14ef06d6d",
  "expected_chart_fingerprint": "f100098b5c36936e1a44d78f6f5e558a2beda54bd21cd1f418a70b9248ff75be"
}
```

以上指纹仅用于说明字段对应关系；实际测试必须使用你当前运行的后端在第 2 步实时返回
的值。如果预览后修改了任何个人信息、使用了上一次预览的指纹，或者不同后端实例使用
了不同排盘规则，都会返回 `409 Chart result changed`。修改成功响应与 7.3 的创建响应
结构相同，包含更新后的 `profile` 和最新 `chart`。

冷却天数由环境变量 `PROFILE_EDIT_COOLDOWN_DAYS` 控制，默认 `30`；设为 `0` 可关闭
限制。尚未到期时返回 `429`。服务端在事务中锁定档案行，因此同时提交多个修改请求也
不能绕过限制。

### 7.7 只读取已保存命盘

```http
GET /api/v1/chart-profiles/{profile_id}/chart
```

权限：用户。直接返回已保存的 `BaziChartOut`，不会在每次请求或登录时重新计算。
返回值就是 7.3 成功响应中的 `chart` 对象，不包含外层的 `profile`，其中
`chart` 字段保存完整命盘 JSON。

### 7.8 使用现有个人信息重新生成命盘

```http
POST /api/v1/chart-profiles/{profile_id}/regenerate
```

权限：用户。用于排盘规则升级后重建快照，不修改个人信息，也不影响个人信息的修改冷却
时间。成功返回新的 `BaziChartOut`，结构与 7.7 相同；`generated_at`、引擎版本、命盘
内容及相关指纹会更新，`profile.id` 和个人信息不会改变。

## 8. 今日指引接口

该接口迁移自旧应用的“今日”页面公共内容。它不读取用户帐号、命理档案或命盘，未登录
用户也可以调用；同一日期和年份的结果对所有用户相同。

```http
GET /api/v1/guidance/today
```

权限：公开。没有请求体。

| 查询参数 | 类型 | 必填 | 来源与规则 |
|---|---:|:---:|---|
| `target_date` | date | 否 | 客户端日期选择器，格式为 `YYYY-MM-DD`，范围 `1900-01-01`～`2100-12-31`；省略时使用 `Asia/Shanghai` 的当天 |
| `target_year` | integer | 否 | 客户端年度选择器，范围 1900～2100；省略时使用 `target_date` 所在年份 |

查看当天内容：

```http
GET /api/v1/guidance/today
```

查看指定日期并同时查看指定年度内容：

```http
GET /api/v1/guidance/today?target_date=2026-07-11&target_year=2026
```

成功响应示例：

```json
{
  "timezone": "Asia/Shanghai",
  "daily_guidance": {
    "kind": "daily_guidance",
    "is_personal": false,
    "date": "2026-07-11",
    "day_pillar": "丙戌",
    "title": "今日建议｜丙戌日",
    "element_theme": "火",
    "wearing_colors": ["红色", "暖橙", "米黄"],
    "wearing_advice": "可用一点红色、橙色或暖色配饰提气，但不必过度张扬。",
    "cautions": ["急躁争辩", "过度透支", "拖延堆积"],
    "primary_action": "表达展示",
    "theme": "火",
    "focus": "表达展示",
    "action": "可用一点红色、橙色或暖色配饰提气，但不必过度张扬。",
    "reminder": "急躁争辩",
    "details": {
      "colors": ["红色", "暖橙", "米黄"],
      "relaxation": "适合收纳、慢走、规律饮食，用秩序感安顿压力。",
      "actions": ["表达展示", "推进事项", "整理目标", "整理财务"]
    },
    "basis": "依据今日干支丙戌的天干五行火、地支主气土生成大众节律提醒；不替代个人命盘分析。",
    "boundary_note": "本内容未读取姓名、性别或出生资料，是同一天所有用户共用的传统历法生活参考，属于非个人命盘分析。不作为医疗、投资、法律、婚姻等重大决定依据。"
  },
  "yearly_guidance": {
    "kind": "yearly_guidance",
    "is_personal": false,
    "year": 2026,
    "title": "今年建议｜2026年 丙午",
    "theme": "丙午年可从重视表达、行动、曝光、热度管理和节奏控制。同时留意重视表达、行动、曝光、热度管理和节奏控制。",
    "focus": "表达",
    "actions": ["表达展示", "推进事项", "整理目标"],
    "basis": "依据2026年干支丙午、天干五行火、地支主气火生成大众化年度提醒；个人运势仍需结合完整命盘。",
    "boundary_note": "八字年柱通常以立春为换年点，不是简单按公历1月1日切换；如果生日在2月3日至2月5日前后，需要结合当年立春时间复核。"
  }
}
```

响应字段来源和用途：

| 字段 | 来源与用途 |
|---|---|
| `timezone` | 服务端计算默认日期使用的固定时区，当前为 `Asia/Shanghai` |
| `daily_guidance` | 根据 `target_date` 的日柱及天干、地支五行生成的公共日建议 |
| `daily_guidance.day_pillar` | 后端权威历法适配器计算的当日干支，不由客户端提交 |
| `daily_guidance.wearing_colors` / `details` | 旧今日页面的颜色、穿搭、行动、注意和放松内容 |
| `daily_guidance.basis` | 本次公共建议使用的传统历法依据 |
| `daily_guidance.boundary_note` | 明确内容不是个人命盘预测，也不能替代重大现实决策 |
| `yearly_guidance` | 根据 `target_year` 年干支生成的同页公共年度节奏 |
| `is_personal` | 固定为 `false`，表示响应没有读取任何个人资料 |

如果日历适配器临时无法可靠计算日柱，接口仍返回 `200` 和可用的年度内容，此时
`daily_guidance` 为 `null`。日期或年份格式错误、超出支持范围时返回 `422`。

## 9. 个人运势接口

该接口等价迁移旧应用“个人年度分析”中的年度总览、事业/财务/关系/身心专项、机会月、
高关注月、12 个月流月、叙事结果和完整事件激活规则。它直接使用第 7 节已经保存的命盘
快照计算，不要求客户端再次发送姓名或出生资料。接口仅允许档案所有者访问；旧版分析
依据文本可能包含命盘中的出生日期或时辰摘要，因此客户端应按个人敏感数据保护整个响应。

```http
GET /api/v1/chart-profiles/{profile_id}/fortune?target_year=2026
```

权限：登录用户。只能查询当前用户自己的档案。请求没有 Body。

| 参数 | 位置 | 类型 | 必填 | 规则与来源 |
|---|---|---:|:---:|---|
| `profile_id` | Path | string | 是 | 新建档案响应中的 `profile.id`，或档案列表接口每一项的 `id`；不是 `chart.id` |
| `target_year` | Query | integer | 否 | 1900～2100；省略时使用服务端当前年份 |
| `Authorization` | Header | string | 是 | `Bearer <短信或密码登录返回的 access_token>` |

ApiPost 测试步骤：

1. 先完成短信或密码登录，复制响应中的 `access_token`。
2. 调用 `GET /api/v1/chart-profiles?offset=0&limit=20`，复制目标档案的 `id`。
3. 新建 GET 请求，将地址写成
   `http://127.0.0.1:8000/api/v1/chart-profiles/档案ID/fortune?target_year=2026`。
4. 在 Auth 中选择 Bearer Token，粘贴 `access_token`；Body 保持空白。
5. 发送请求。成功状态码为 `200`。

成功响应示例（数组内容做了缩短；真实响应固定返回 12 个月）：

```json
{
  "kind": "personal_fortune",
  "is_personal": true,
  "profile_id": "b3bcb9f0-f9e1-4cab-bd69-cf1b0599533a",
  "chart_fingerprint": "64位十六进制命盘指纹",
  "target_year": 2026,
  "fortune_engine_version": "personal-fortune-legacy-equivalent-v1",
  "generated_at": "2026-08-22T12:30:00Z",
  "luck_context": {
    "available": true,
    "direction": "forward",
    "direction_label": "顺排",
    "start_text": "顺排，取相应节气折算……",
    "current_period": {
      "index": 3,
      "pillar": "己亥",
      "gan": "己",
      "zhi": "亥",
      "start_age": 22,
      "end_age": 31,
      "start_year": 2018,
      "end_year": 2027,
      "start_date": "2018-10-01",
      "end_date": "2028-10-01"
    }
  },
  "yearly": {
    "year": 2026,
    "pillar": "丙午",
    "gan": "丙",
    "zhi": "午",
    "gan_element": "火",
    "zhi_element": "火",
    "ten_god": "食神",
    "branch_ten_god": "伤官",
    "branch_relations": [],
    "relation_to_favorable": "喜用相关",
    "overall_level": "助力较明显",
    "keywords": ["表达", "技能", "作品", "喜用相关"],
    "annual_keywords": ["表达", "技能", "作品", "喜用相关"],
    "overall_text": "2026年为丙午年……",
    "career_text": "事业上适合把年度主题拆成阶段目标……",
    "wealth_text": "财务上优先管理预算、现金流和合同……",
    "relationship_text": "关系上以真实沟通和长期相处为准……",
    "health_text": "身心内容只作生活节奏提醒……",
    "risk_text": "整体按既定计划推进……",
    "advice_text": "先处理可验证、可回退的事项……",
    "brief_text": "2026年年度摘要……",
    "suitable_actions": ["设定阶段目标", "复核合同与预算", "保持稳定作息"],
    "actions_to_avoid": ["冲动投资或借贷", "把命理提示当成确定事件", "忽略专业意见"],
    "high_attention_months": ["1月（己丑）"],
    "opportunity_months": ["2月（庚寅）"],
    "career_good_months": [],
    "career_bad_months": [],
    "wealth_good_months": ["2月"],
    "wealth_bad_months": [],
    "relationship_good_months": [],
    "relationship_bad_months": [],
    "peach_months": ["2月"],
    "health_concerns": []
  },
  "monthly": [
    {
      "month": 1,
      "month_name": "1月",
      "pillar": "己丑",
      "gan": "己",
      "zhi": "丑",
      "gan_element": "土",
      "zhi_element": "土",
      "ten_god": "伤官",
      "relation_to_favorable": "平稳观察",
      "branch_relations": [],
      "theme": "突破和表达意愿增强……",
      "event_tags": ["创意与突破", "表达摩擦"],
      "event_tendency": "本月现实事件倾向……",
      "likely_events": ["事件提示一", "事件提示二"],
      "career_text": "事业方面宜稳步观察……",
      "wealth_text": "财务上先核对现金流、成本与承诺……",
      "relationship_text": "关系上把期待和边界说清楚……",
      "health_text": "身心提示只用于作息管理……",
      "risk_text": "按计划推进，并根据现实反馈及时校准。",
      "advice_text": "创新方案同时准备规则与风险说明。",
      "suitable_actions": ["复核本月重点", "把计划拆成可验证步骤"],
      "actions_to_avoid": ["仅凭命理提示作重大决定", "忽略现实条件和专业意见"],
      "basis": "流月规则命中依据……",
      "source_ids": ["san_ming_tong_hui"],
      "source_titles": ["三命通会"],
      "top_events": [
        {
          "event_type": "contract_cooperation_cluster",
          "label": "合同与合作边界",
          "category": "事业规则",
          "probability_level": "中等",
          "score": 64.0,
          "trigger_count": 4,
           "evidence": [
             {
               "type": "ten_god",
               "value": ["正官"],
               "detail": "流月十神匹配"
             }
           ],
           "display_trigger_factors": ["流月十神主题被引动"],
           "one_line": "合同、审批或合作边界信号被引动。",
          "real_world_signals": ["合同复核", "流程确认", "职责边界"],
          "advice": "重要事项落到文字，并复核金额、期限和责任。",
          "source_ids": ["san_ming_tong_hui"],
          "source_titles": ["三命通会"]
        }
      ]
    }
  ],
  "boundary_note": "本结果基于传统命理模型，仅供个人兴趣与文化研究参考……"
}
```

### `monthly[]` 字段说明

`monthly` 固定包含 12 个对象，按 `month=1` 到 `month=12` 排列。流月干支使用目标年份
对应月份 15 日的节气定月和五虎遁规则计算；这里的月份序号是接口的公历月份索引，不是让
客户端提交的农历月份。

| 字段 | 类型 | 必有 | 说明与来源 |
|---|---|:---:|---|
| `month` | integer | 是 | 月份序号，固定为 1～12，也是数组的业务排序依据 |
| `month_name` | string | 是 | 用于展示的月份名称，例如 `1月`、`12月` |
| `pillar` | string | 是 | 该月月柱，例如 `己丑`；由后端日历与干支规则计算，不由客户端提交 |
| `gan` | string | 是 | `pillar` 中的月干，例如 `己` |
| `zhi` | string | 是 | `pillar` 中的月支，例如 `丑` |
| `gan_element` | string | 是 | 月干对应五行，取值为 `木`、`火`、`土`、`金`、`水`之一 |
| `zhi_element` | string | 是 | 月支主气对应五行，取值为 `木`、`火`、`土`、`金`、`水`之一 |
| `ten_god` | string | 是 | 月干相对命盘日主计算出的十神，例如 `正官`、`伤官`；这是个人化结果 |
| `relation_to_favorable` | string | 是 | 月干、月支五行与命盘喜用、忌神的关系，当前常见值为 `喜用相关`、`忌神相关`、`平稳观察` |
| `branch_relations` | array<object> | 是 | 流月地支与原局年、月、日、时支之间命中的六冲关系；没有命中时为空数组，子字段见下表 |
| `theme` | string | 是 | 综合十神、五行喜忌和规则叙事得到的本月主题摘要 |
| `event_tags` | array<string> | 是 | 用于列表、标签栏快速展示的本月关键词，已去重；它不是 `top_events` 的事件详情 |
| `event_tendency` | string | 是 | 本月整体事件倾向及本盘校准依据的说明文本 |
| `likely_events` | array<string> | 是 | 月度叙事层生成的概括性事件提示；与结构更完整的 `top_events` 用途不同 |
| `career_text` | string | 是 | 本月事业、工作与项目方向的文字分析 |
| `wealth_text` | string | 是 | 本月财务、预算、回款和支出方向的文字分析 |
| `relationship_text` | string | 是 | 本月感情、人际、家庭或合作关系方向的文字分析 |
| `health_text` | string | 是 | 本月作息和身心节奏提示，仅作生活管理参考，不是医疗结论 |
| `risk_text` | string | 是 | 本月需要注意的整体风险和现实约束 |
| `advice_text` | string | 是 | 针对本月整体趋势生成的行动建议 |
| `suitable_actions` | array<string> | 是 | 本月相对适合执行的行动建议列表 |
| `actions_to_avoid` | array<string> | 是 | 本月建议避免或谨慎处理的行动列表 |
| `basis` | string | 是 | 本月命中的规则依据摘要；没有明确规则文本时可能为空字符串 |
| `source_ids` | array<string> | 是 | 本月命中规则引用的内部来源编号；没有来源时为空数组 |
| `source_titles` | array<string> | 是 | `source_ids` 对应的可读资料名称；顺序不表示资料优先级 |
| `top_events` | array<object> | 是 | 证据激活链筛选的本月重点事件，当前最多 5 项；可能少于 5 项，字段见后文 |

`branch_relations[]` 子字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | string | 关系类型，当前为 `六冲` |
| `label` | string | 可读标签，例如 `冲日支` |
| `target` | string | 被影响的原局位置，例如 `年支`、`月支`、`日支`、`时支` |
| `native_zhi` | string | 对应位置的原局地支 |
| `year_zhi` | string | 当前参与比较的流月地支；字段名为兼容原引擎沿用 `year_zhi` |
| `text` | string | 该位置关系对应的现实领域提示 |

### `monthly[].top_events[]` 字段说明

以下是所有事件都应具备、并由接口响应模型约束的核心字段：

| 字段 | 类型 | 必有 | 说明与来源 |
|---|---|:---:|---|
| `event_type` | string | 是 | 稳定的事件类型机器标识，例如 `contract_cooperation_cluster`；前端判断类型时使用它，不要使用中文 `label` |
| `label` | string | 是 | 面向用户的事件名称，例如“合同与合作边界” |
| `category` | string | 是 | 事件所属领域，例如事业规则、财务支出、关系家庭或健康状态 |
| `score` | number | 是 | 规则命中后用于本月事件内部排序的 0～100 分；不是统计概率，也不能解释为事件有百分之多少会发生 |
| `probability_level` | string/null | 是 | 根据规则分数转换的定性可能性等级；没有可靠等级时为 `null`，它不等同于 `score` 的百分比 |
| `trigger_count` | integer/null | 是 | 事件命中的触发证据数量；聚合事件可能合并多条证据，因此不要假定它永远等于 `evidence` 数组长度 |
| `evidence` | array | 是 | 引擎原始触发证据。桥接事件通常是对象数组，兼容事件也可能是字符串数组；用于追溯，不建议直接展示 |
| `display_trigger_factors` | array<string> | 是 | 将 `evidence` 按旧页面规则翻译、去重后的用户可读“触发因素”，最多 3 项；前端应优先展示这个字段 |
| `reason` | string/null | 是 | 兼容基础事件的命中原因说明；桥接事件通常为 `null`，可使用 `one_line` 和 `user_visible_basis` 展示 |
| `advice` | string | 是 | 针对该重点事件的行动建议 |

`evidence[]` 为对象时，常见子字段如下：

| 字段 | 类型 | 说明 |
|---|---|---|
| `type` | string | 内部证据类型，例如 `ten_god`、`element`、`group_count_at_least`；用于翻译触发因素 |
| `value` | array | 实际命中的规则值；内容由证据类型决定，可能为空数组 |
| `detail` | string | 供规则追溯的内部说明，不建议原样展示给普通用户 |
| `source_ids` | array<string> | 支持该条证据的来源编号 |
| `source_relevance` | number | 该来源与本条规则的内部相关度，不是事件发生概率 |

下列是事件激活链返回的扩展字段。它们会随事件类型、规则版本和是否发生事件聚合而变化；
前端读取时应提供默认值，不应把它们都视为必有字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `one_line` | string | 该事件的一句话用户摘要，适合作为事件卡片简介 |
| `real_world_signals` | array<string> | 建议用户在现实中观察的具体信号 |
| `possible_manifestations` | array<string> | 事件可能出现的现实表现，聚合事件可能使用专门的表现列表 |
| `risk_points` | array<string> | 该事件需要留意的风险点 |
| `basis` | string | 事件类型本身的规则依据摘要 |
| `user_visible_basis` | string | 已整理成用户可读形式的命中依据，前端需要展示依据时优先使用 |
| `source_ids` | array<string> | 支持该事件结论的来源编号 |
| `source_titles` | array<string> | 来源编号对应的可读资料名称 |
| `confidence_level` | string | 综合证据数量、证据维度、反向条件和来源质量得到的置信等级，常见为 `high`、`medium`、`low` |
| `confidence_dimensions` | array<string> | 本事件覆盖的证据维度，例如十神、五行喜忌、宫位或地支 |
| `confidence_reasons` | array<string> | 形成当前置信等级的说明 |
| `downgrade_reasons` | array<string> | 导致置信等级被下调的原因；没有时为空数组 |
| `source_confidence_score` | number | 来源支撑质量的内部评分，不是事件发生概率 |
| `source_has_specific_support` | boolean | 是否存在针对该事件的具体来源支撑 |
| `source_has_category_match` | boolean | 来源领域是否与事件类别匹配 |
| `traditional_basis` | object | 规则资源中保存的传统依据结构，主要用于追溯和研究 |
| `structure_basis` | object | 原局结构相关的规则依据 |
| `palace_basis` | object | 宫位或地支落点相关的规则依据 |
| `modern_mapping` | object | 传统规则到现代现实场景的映射 |
| `confidence_basis` | object | 该事件类型的置信判断配置 |
| `anti_triggers` | array | 可能削弱或反转事件判断的条件 |
| `required_evidence_count` | integer | 该事件规则建议达到的最低证据数量 |
| `subtype_rules` | object | 事件子类型识别规则 |
| `subtype_candidates` | array<string> | 本次命中的事件子类型候选 |
| `subtype_label` | string | 最优先的事件子类型标签；没有时为空字符串 |
| `from_bridge` | boolean | 是否来自完整事件激活桥接链；当前主要重点事件通常为 `true` |
| `merged_from` | array<string> | 聚合事件由哪些原始 `event_type` 合并而来；未发生聚合时通常不存在 |
| `possible_sources` | array<string> | 聚合事件对应的原始事件名称；未发生聚合时通常不存在 |
| `trigger_factors` | array<string> | 兼容基础事件可能携带的原始触发文本；前端展示仍应使用稳定的 `display_trigger_factors` |

主要返回值来源：

| 字段 | 说明 |
|---|---|
| `chart_fingerprint` | 本次计算实际使用的已保存命盘版本；档案重排后会变化 |
| `luck_context` | 根据档案出生信息和后端大运规则计算的目标年份大运背景；计算失败时 `available=false`，但流年、流月仍可返回 |
| `yearly` | 目标年份干支与命盘的十神、喜忌、地支关系及年度专项结论 |
| `monthly` | 固定 12 项，按公历 1～12 月排列；每项含当月干支、十神、喜忌和事件提示 |
| `branch_relations` | 流年或流月地支与原局年、月、日、时支之间的六冲关系；没有时为空数组 |
| `top_events` | 旧版完整事件激活链输出的最多 5 项趋势提示，包含触发证据、现实表现、置信依据、降级原因和规则来源；`score` 只用于本次结果内部排序，不是事件发生概率 |
| `top_events[].evidence` | 引擎返回的原始结构化触发证据，供追溯规则依据，不建议直接作为前端文案展示 |
| `top_events[].display_trigger_factors` | 后端按照旧页面 `_EVIDENCE_TYPE_COPY` 规则将证据翻译并去重后的用户可读“触发因素”，固定为字符串数组，最多 3 项；前端应优先展示该字段 |
| `monthly[].basis/source_ids/source_titles` | 流月规则依据及参考来源；来源顺序不表达优先级 |
| `generated_at` | 本次接口生成响应的时间；相同命盘与年份的业务字段保持稳定，但该时间每次调用会更新 |

年度、流月、叙事和事件引擎以及所需 JSON 规则资源均位于后端 `app/fortune`，运行时不读取
`bazi_ziwei_app`。存储策略仍是数据库只保存个人档案和命盘快照，个人运势按请求实时生成。
这样规则升级后无需批量改写历史结果。后续需要提速时，应以
`chart_fingerprint + target_year + fortune_engine_version` 作为缓存键，而不是新增一份个人资料。

可能错误：`401` 未登录、token 无效或已过期；`404` 档案不属于当前用户、档案不存在或尚无
命盘；`422` 年份超出范围，或保存的命盘无法用于个人运势计算。

## 10. 命盘综合分析接口

### 10.1 获取八字详情、命盘总览和五行喜忌

```http
GET /api/v1/chart-profiles/{profile_id}/analysis
Authorization: Bearer <access_token>
```

权限：用户。`profile_id` 必须属于当前登录用户。接口读取已经确认并保存的命盘快照，
不会重新接收或覆盖出生信息。

路径参数：

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `profile_id` | string | 是 | 命理档案 ID，来自档案创建、列表或详情接口 |

成功返回：

```json
{
  "profile_id": "b3bcb9f0-f9e1-4cab-bd69-cf1b0599533a",
  "chart_fingerprint": "9e69e15bb2f7f5522d8f5a4423889ab621a24c1dde199e5081cfeafd8ded608a",
  "chart_type": {
    "basic_pattern": "常规格局",
    "element_pattern": "五行分布说明",
    "ten_god_pattern": "十神结构说明",
    "special_combinations": [],
    "summary": "命局类型摘要"
  },
  "basic_report": {
    "life_overview": "命局总论",
    "personality_text": "性格与行为模式",
    "career_text": "事业基础解读",
    "wealth_text": "财富基础解读",
    "love_text": "关系基础解读",
    "risk_text": "风险提醒",
    "advice": "综合建议"
  },
  "life_assessment": {
    "opening": "总体开场",
    "wealth": {},
    "romance": {},
    "health": {}
  },
  "life_overview": {
    "overall_pattern": "总体类型",
    "overall_summary": "总体结论",
    "life_keywords": ["关键词一", "关键词二"],
    "wealth_overview": {},
    "romance_overview": {},
    "health_overview": {},
    "career_overview": {},
    "scores": {"wealth": 70, "romance": 65, "health": 72, "career": 75},
    "score_details": {},
    "key_strengths": ["优势说明"],
    "key_risks": ["风险说明"],
    "long_term_advice": ["长期建议"],
    "evidence": ["命盘依据"],
    "source_ids": ["source_id"],
    "source_titles": ["参考来源"]
  },
  "five_elements": {
    "element_overview": "五行总览",
    "element_balance_summary": "平衡情况",
    "strong_elements": ["木"],
    "weak_elements": ["金"],
    "favorable_elements": ["水", "木"],
    "unfavorable_elements": ["土"],
    "element_details": {},
    "career_implications": "事业影响",
    "wealth_implications": "财富影响",
    "relationship_implications": "关系影响",
    "health_implications": "健康生活方式提醒",
    "adjustment_advice": ["调整建议"],
    "evidence": [],
    "source_ids": [],
    "source_titles": []
  },
  "useful_god": {
    "favorable_elements": ["水", "木"],
    "summary": "喜用五行摘要",
    "details": []
  }
}
```

主要字段：

| 字段 | 说明 |
|---|---|
| `chart_type` | 命局基础类型、五行类型、十神类型和特殊组合 |
| `basic_report` | 旧八字页面的基础白话解读 |
| `life_assessment` | 财富、感情和生活状态的基础评估 |
| `life_overview` | 五维总览、分数构成、优势、风险和长期建议 |
| `five_elements` | 五行强弱、喜忌、现实领域影响和调整建议 |
| `useful_god` | 喜用五行的摘要和逐项说明 |
| `evidence/source_ids/source_titles` | 结论依据和规则来源，用于解释及追溯 |

可能错误：`401` 未登录；`404` 档案不属于当前用户或命盘不存在；`422` 保存的命盘无法完成分析。

## 11. 完整大运接口

### 11.1 查询起运、十步大运和未来十年流年

```http
GET /api/v1/chart-profiles/{profile_id}/luck-cycles
Authorization: Bearer <access_token>
```

权限：用户。没有请求体和查询参数。

```json
{
  "profile_id": "b3bcb9f0-f9e1-4cab-bd69-cf1b0599533a",
  "chart_fingerprint": "9e69e15bb2f7f5522d8f5a4423889ab621a24c1dde199e5081cfeafd8ded608a",
  "available": true,
  "direction": "forward",
  "direction_label": "顺排",
  "start_age": 7,
  "start_year": 2007,
  "start_month": 2,
  "start_day": 5,
  "start_text": "7岁2个月5天起运",
  "dayun_basis": {
    "boundary_name": "节气名称",
    "boundary_datetime": "2000-09-07 15:59:00",
    "interval_seconds": 123456,
    "start_datetime": "2007-11-09 00:00:00",
    "time_is_estimated": false,
    "rule_ids": ["dayun.rule.id"]
  },
  "dayun_list": [
    {
      "index": 1,
      "pillar": "甲子",
      "gan": "甲",
      "zhi": "子",
      "start_age": 7,
      "end_age": 16,
      "start_year": 2007,
      "end_year": 2016,
      "start_date": "2007-11-09",
      "end_date": "2017-11-08",
      "gan_element": "木",
      "zhi_element": "水",
      "ten_god": "正印",
      "stage_score": 72,
      "stage_level": "稳中有进",
      "stage_text": "阶段说明",
      "stage_summary": "阶段摘要",
      "career_focus": "事业重点",
      "wealth_focus": "财富重点",
      "relationship_focus": "关系重点",
      "risk_focus": "风险重点",
      "action_advice": "行动建议"
    }
  ],
  "yearly_list": [
    {
      "year": 2026,
      "pillar": "丙午",
      "overall_text": "年度趋势",
      "advice_text": "年度建议"
    }
  ],
  "data_warnings": []
}
```

`dayun_list` 固定最多十步，每一步包括起止年龄、起止日期、五行、十神和阶段分析；
`yearly_list` 从当前年份起返回十年。起运时间使用后端确定性节气规则计算。

## 12. 六十甲子接口

### 12.1 查询六十甲子知识

```http
GET /api/v1/knowledge/sixty-jiazi?year=1984
```

权限：公开，不需要登录。

| 查询参数 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `year` | integer | 否 | `1900`～`2100`，根据年份查询干支 |
| `pillar` | string | 否 | 两个汉字，例如 `甲子` |
| `offset` | integer | 否 | 默认 `0`，不能小于 `0` |
| `limit` | integer | 否 | 默认 `60`，范围 `1`～`60` |

`year` 和 `pillar` 不能同时提交。两者都不提交时返回完整知识列表并应用分页。

```json
{
  "total": 1,
  "offset": 0,
  "limit": 60,
  "items": [
    {
      "index": 1,
      "pillar": "甲子",
      "gan": "甲",
      "zhi": "子",
      "gan_element": "木",
      "zhi_element": "水",
      "nayin": "海中金",
      "nayin_element": "金",
      "sample_years": [1924, 1984],
      "plain_explanation": "白话解释",
      "symbolic_keywords": ["关键词"],
      "reality_mapping": "现实映射",
      "user_advice": "参考建议",
      "lichun_boundary_note": "立春换年边界说明"
    }
  ]
}
```

### 12.2 查询某个命盘的四柱甲子卡片

```http
GET /api/v1/chart-profiles/{profile_id}/sixty-jiazi
Authorization: Bearer <access_token>
```

```json
{
  "profile_id": "档案 ID",
  "chart_fingerprint": "命盘指纹",
  "pillar_cards": [
    {
      "position": "year",
      "label": "年柱",
      "pillar": "甲子",
      "nayin": "海中金",
      "user_explanation": "面向用户的白话解释",
      "reality_hint": "现实映射",
      "advice": "参考建议",
      "keywords": ["关键词"],
      "boundary_note": "使用边界"
    }
  ],
  "nayin_comparison": {
    "nayin_distribution": {"金": 2, "木": 1, "水": 1},
    "chart_distribution": {},
    "dominant_nayin_elements": ["金"],
    "dominant_chart_elements": ["水", "木"],
    "explanation": "四柱纳音与原局五行对照"
  }
}
```

`pillar_cards` 正常为年、月、日、时四项；出生时辰不详时，时柱内容以实际引擎结果为准。

## 13. 专项报告和导出接口

### 13.1 获取结构化专项报告

```http
GET /api/v1/chart-profiles/{profile_id}/reports/{report_type}
Authorization: Bearer <access_token>
```

`report_type` 只允许：

| 值 | 含义 |
|---|---|
| `career` | 事业专项报告 |
| `wealth` | 财富专项报告 |
| `love` | 感情关系专项报告 |

```json
{
  "profile_id": "档案 ID",
  "chart_fingerprint": "命盘指纹",
  "report_type": "career",
  "report": {
    "title": "事业专项报告",
    "evidence": ["命盘依据"],
    "chart_signature": "本盘差异化结构",
    "sections": [
      {"title": "事业核心定位", "text": "分析内容"},
      {"title": "适合工作模式", "text": "分析内容"}
    ],
    "advice": "行动建议",
    "disclaimer": "免责声明"
  }
}
```

不同报告还会返回其专有字段：

| 报告 | 主要专有字段 |
|---|---|
| `career` | `career_identity`、`career_portrait`、`suitable_work_modes`、`suitable_industries`、`career_risks`、`action_plan` |
| `wealth` | `wealth_identity`、`financial_structure`、`main_income_modes`、`secondary_income_modes`、`money_risks`、`cashflow_advice` |
| `love` | `relationship_pattern`、`relationship_structure`、`suitable_partner_type`、`relationship_strengths`、`relationship_risks`、`communication_advice` |

### 13.2 下载综合或专项报告

```http
GET /api/v1/chart-profiles/{profile_id}/reports/{report_type}/export?format=markdown
Authorization: Bearer <access_token>
```

| 参数 | 允许值 |
|---|---|
| `report_type` | `comprehensive`、`career`、`wealth`、`love` |
| `format` | `markdown`、`txt`、`pdf`，默认 `markdown` |

该接口返回文件内容，不返回 JSON：

| 格式 | `Content-Type` | 扩展名 |
|---|---|---|
| `markdown` | `text/markdown; charset=utf-8` | `.md` |
| `txt` | `text/plain; charset=utf-8` | `.txt` |
| `pdf` | `application/pdf` | `.pdf` |

PDF 生成需要 `reportlab` 和可嵌入中文字体。Docker 镜像已经安装 Noto CJK 字体；本机缺少依赖或字体时返回 `422`，不会把错误文本伪装成 PDF。

## 14. 合婚匹配接口

### 14.1 比较两个命理档案

```http
POST /api/v1/compatibility/analyze
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "profile_id_1": "第一个档案 ID",
  "profile_id_2": "第二个档案 ID"
}
```

两个 ID 必须不同，并且都必须属于当前登录用户。接口不会允许使用其他用户的档案。

```json
{
  "profile_id_1": "第一个档案 ID",
  "profile_id_2": "第二个档案 ID",
  "chart_fingerprint_1": "第一个命盘指纹",
  "chart_fingerprint_2": "第二个命盘指纹",
  "result": {
    "overall_score": 78,
    "level": "较匹配",
    "summary": "总体结论",
    "dimensions": [
      {
        "label": "日主关系",
        "score": 18,
        "max_score": 20,
        "text": "维度说明",
        "detail": "具体依据"
      }
    ],
    "key_cautions": ["重点提醒"],
    "person_a": {},
    "person_b": {},
    "match_reasons": ["互补原因"],
    "conflict_reasons": ["可能冲突"],
    "advice_list": ["相处建议"],
    "basis": "命理依据",
    "source_titles": ["参考来源"]
  }
}
```

### 14.2 下载合婚报告

```http
POST /api/v1/compatibility/export?format=txt
Authorization: Bearer <access_token>
Content-Type: application/json
```

请求体与分析接口相同，`format` 支持 `markdown`、`txt`、`pdf`，响应为下载文件。

## 15. 紫微斗数接口

### 15.1 获取紫微命盘和综合解读

```http
GET /api/v1/chart-profiles/{profile_id}/ziwei
Authorization: Bearer <access_token>
```

```json
{
  "profile_id": "档案 ID",
  "chart_fingerprint": "对应八字命盘指纹",
  "chart": {
    "available": true,
    "lunar_month": 8,
    "lunar_day": 7,
    "hour_branch": "巳",
    "year_gan": "庚",
    "year_branch": "午",
    "life_palace": "辰",
    "body_palace": "申",
    "palaces": [],
    "main_stars_ready": true,
    "main_stars_by_palace": {},
    "minor_stars_ready": true,
    "minor_stars_by_palace": {},
    "fierce_stars_ready": true,
    "fierce_stars_by_palace": {},
    "daxian": {}
  },
  "life_card": {
    "title": "紫微命盘名片",
    "ziwei_profile_type": "命宫与身宫类型",
    "profile_keywords": [],
    "ming_gong_summary": "命宫说明",
    "shen_gong_summary": "身宫说明",
    "key_palace_summaries": {},
    "personalized_evidence": [],
    "source_titles": []
  },
  "report": {
    "title": "紫微人生说明书",
    "sections": [],
    "advice": "综合建议",
    "disclaimer": "免责声明",
    "main_stars_ready": true,
    "minor_stars_ready": true,
    "fierce_stars_ready": true,
    "daxian_ready": true
  }
}
```

`palaces` 正常为十二项，包含宫名、地支、主星、辅星、煞星和宫位说明；`report.sections`
包含人生说明书、重点宫位、三方四正、四化和算法完成度说明。

### 15.2 下载紫微报告

```http
GET /api/v1/chart-profiles/{profile_id}/ziwei/export?format=markdown
Authorization: Bearer <access_token>
```

`format` 支持 `markdown`、`txt`、`pdf`，响应为下载文件。

## 16. AI 命理问答接口

### 16.1 对已保存命盘提问

```http
POST /api/v1/chart-profiles/{profile_id}/questions
Authorization: Bearer <access_token>
Content-Type: application/json
```

```json
{
  "question": "未来三年的事业重点是什么？",
  "history": [
    {"role": "user", "content": "我想了解事业方向"},
    {"role": "assistant", "content": "可以具体到年份或工作类型"}
  ]
}
```

输入规则：

| 字段 | 类型 | 必填 | 规则 |
|---|---|---|---|
| `question` | string | 是 | `1`～`1000` 字符，只支持四柱命理范围内的问题 |
| `history` | array | 否 | 默认空数组，最多 10 条 |
| `history[].role` | string | 是 | `user` 或 `assistant` |
| `history[].content` | string | 是 | `1`～`4000` 字符 |

成功或安全降级均返回 `200`：

```json
{
  "profile_id": "档案 ID",
  "chart_fingerprint": "命盘指纹",
  "mode": "local",
  "answer": "本地规则生成并经过安全边界处理的回答",
  "structured_answer": {
    "source": "local_rules",
    "provider": null,
    "sections": {},
    "chart_evidence": ["命盘事实依据"],
    "rule_evidence": ["规则依据"],
    "timing_conditions": ["时间条件"],
    "practical_advice": ["现实建议"],
    "uncertainty": ["不确定性和边界"],
    "interpretation_receipt": "问题解释回执",
    "retryable": false,
    "violation_codes": []
  },
  "degradation_reason": "service_unavailable",
  "boundary_note": "命理分析仅供传统文化参考，不替代医疗、法律、投资或其他现实专业决策。"
}
```

字段解释：

| 字段 | 说明 |
|---|---|
| `mode` | `local` 表示本地规则回答，`cloud` 表示云模型结果通过本地事实校验 |
| `structured_answer.source` | `local_rules`、`cloud_validated`、`boundary` 或 `clarification` |
| `degradation_reason` | 云模型未使用或不可用的原因；正常云回答时为 `null` |
| `violation_codes` | 云输出被修复或拒绝时的安全校验编码 |
| `retryable` | 本次降级是否适合稍后重试 |

常见的 `degradation_reason` 包括：`missing_api_key`（缺少密钥）、
`model_unavailable`（模型名称不存在或当前账号无权使用）、`invalid_credentials`（密钥无效）、
`insufficient_quota`（额度不足）、`rate_limited`（触发限流）、`timeout`（调用超时）、
`network_error`（网络异常）和 `local_validation_failed`（云回答未通过本地事实校验）。

默认配置 `AI_PROVIDER=local`，完全不调用外部模型。启用云增强时在服务器 `.env` 配置：

```dotenv
AI_PROVIDER=kimi
AI_API_KEY=仅保存在服务器的密钥
AI_MODEL=kimi-k2.6
AI_BASE_URL=https://api.moonshot.cn/v1
AI_KIMI_THINKING=false
AI_TIMEOUT_SECONDS=90
```

`AI_KIMI_THINKING=false` 表示关闭 Kimi 深度推理。命盘事实与允许输出的结论已经由本地规则生成，
云模型只负责组织表达，因此默认关闭可以显著降低响应时间和 token 消耗；需要额外推理时可显式改为 `true`。

也可以将 `AI_PROVIDER` 设置为 `openai` 并指定对应模型。后端只把去标识化后的命盘事实、
本地规则和问题语义发送给模型，不发送姓名、地点、档案 ID、完整出生资料或内部密钥；云回答还会经过
事实矛盾、越界结论、提示词注入和输出结构检查。速率、每日请求和并发限制由
`AI_PER_USER_PER_MINUTE`、`AI_PER_USER_DAILY_REQUESTS`、`AI_DAILY_TOKEN_BUDGET` 和
`AI_MAX_CONCURRENT_REQUESTS` 配置。当前限制为单进程限制，多实例部署时应升级为 Redis 分布式限流。

## 17. 运维接口

### 17.1 存活检查

```http
GET /healthz
```

权限：公开。只表示 FastAPI 进程可以响应，不检查 MySQL 和 Redis。

```json
{
  "status": "ok"
}
```

### 17.2 就绪检查

```http
GET /readyz
```

权限：公开。实际执行 MySQL `SELECT 1` 和 Redis `PING`，两者均成功才返回：

```json
{
  "status": "ready"
}
```

数据库不可用时返回 `503`：

```json
{
  "detail": "database is not ready"
}
```

Redis 不可用时返回 `503`：

```json
{
  "detail": "redis is not ready"
}
```

响应不会泄露连接字符串或底层异常。

## 18. 当前能力边界

以下功能已有接口或模型骨架，但尚未完成真实第三方接入：

- 生产短信发送适配器。
- 微信公众号扫码登录场景码、回调和签名校验。
- 微信与支付宝预支付参数生成。
- 微信与支付宝支付回调验签和到账处理。
- 月度套餐续费、取消、到期和周期权益结算。
- refresh token 逐次轮换、单设备撤销、退出登录和多设备会话管理。
- 点数流水分页和用户列表总数。

不要将占位接口返回值视为第三方平台已接入。

## 19. 点数与支付安全约定

- `PointLedger` 是不可变审计记录。
- `PointBalance` 是同一事务内更新并加行锁保护的余额投影。
- 点数消费使用用户范围内的幂等键，避免重试造成重复扣点。
- 前端不能自行上报“支付成功”，支付到账必须以服务端验证通过的平台回调为准。
- 生产运营应定期核对账本 `SUM(delta)` 与余额投影，发现偏差时以账本重建投影。
- 数据库、Redis、短信和支付密钥不得写入前端、接口响应、日志或本文档。

## 20. 密码安全约定

- 数据库只保存带独立随机盐的 `scrypt` 密码摘要，不保存或记录明文密码。
- 密码长度为 8～128 个字符，服务端不会擅自裁剪首尾空格或改变字符内容。
- 默认连续输错 5 次后锁定密码登录 15 分钟，可通过 `PASSWORD_MAX_ATTEMPTS` 和 `PASSWORD_LOCK_MINUTES` 调整。
- 登录验证码与密码重置验证码用途隔离，验证码使用一次后即失效。
- 设置、修改或重置密码都会递增帐号认证版本，使旧 access token 和 refresh token 失效。
