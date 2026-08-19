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
| `401` | 未登录、令牌错误、令牌过期或用户已停用 |
| `403` | 当前用户不是管理员 |
| `404` | 用户、套餐、功能规则或支付渠道不存在 |
| `409` | 点数不足，或幂等键被用于不同操作 |
| `422` | 请求体、路径参数或查询参数不合法 |
| `429` | 验证码发送过于频繁、达到每日上限或错误次数达到上限 |
| `501` | 预留接口尚未接入真实适配器 |
| `503` | 短信服务未配置，或 MySQL/Redis 尚未就绪 |

## 2. 快速完成一次注册登录

注册没有单独接口。手机号第一次验证码登录成功时会自动注册，并赠送配置的注册点数。

1. 调用 `POST /api/v1/auth/otp` 获取验证码。
2. 开发环境从 `development_code` 取得验证码。
3. 调用 `POST /api/v1/auth/verify` 完成注册或登录。
4. 保存返回的 `access_token` 和 `refresh_token`。
5. 携带 access token 调用 `GET /api/v1/me` 验证登录状态。

生产环境不会在响应中返回验证码；当前尚未注册真实短信适配器，因此生产环境请求验证码会返回 `503`。

## 3. 认证接口

### 3.1 获取短信验证码

```http
POST /api/v1/auth/otp
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

可能错误：`422` 手机号无效；`429` 请求过于频繁或达到每日上限；`503` 生产短信适配器未配置。

### 3.2 验证验证码并注册/登录

```http
POST /api/v1/auth/verify
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

可能错误：`400` 验证码错误、过期或已使用；`422` 手机号或验证码格式不正确；`429` 错误次数达到上限。

### 3.3 刷新访问令牌

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

当前尚未实现 refresh token 轮换、撤销和退出登录会话管理，正式上线前需要补充。

### 3.4 微信扫码登录预留接口

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
  "points": 20
}
```

| 字段 | 类型 | 说明 |
|---|---:|---|
| `id` | string | 用户 ID |
| `phone` | string/null | E.164 格式手机号 |
| `role` | string | `user` 或 `admin` |
| `points` | integer | 当前可用点数 |

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

停用后，目标用户不能刷新令牌或调用需要登录的接口。可能错误：`404` 用户不存在。

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

## 7. 运维接口

### 7.1 存活检查

```http
GET /healthz
```

权限：公开。只表示 FastAPI 进程可以响应，不检查 MySQL 和 Redis。

```json
{
  "status": "ok"
}
```

### 7.2 就绪检查

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

## 8. 当前能力边界

以下功能已有接口或模型骨架，但尚未完成真实第三方接入：

- 生产短信发送适配器。
- 微信公众号扫码登录场景码、回调和签名校验。
- 微信与支付宝预支付参数生成。
- 微信与支付宝支付回调验签和到账处理。
- 月度套餐续费、取消、到期和周期权益结算。
- refresh token 轮换、撤销、退出登录和多设备会话管理。
- 点数流水分页和用户列表总数。

不要将占位接口返回值视为第三方平台已接入。

## 9. 点数与支付安全约定

- `PointLedger` 是不可变审计记录。
- `PointBalance` 是同一事务内更新并加行锁保护的余额投影。
- 点数消费使用用户范围内的幂等键，避免重试造成重复扣点。
- 前端不能自行上报“支付成功”，支付到账必须以服务端验证通过的平台回调为准。
- 生产运营应定期核对账本 `SUM(delta)` 与余额投影，发现偏差时以账本重建投影。
- 数据库、Redis、短信和支付密钥不得写入前端、接口响应、日志或本文档。
