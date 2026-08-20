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

可能错误：`422` 手机号无效；`429` 请求过于频繁或达到每日上限；`503` 生产短信适配器未配置。

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

可能错误：`400` 验证码错误、过期或已使用；`422` 手机号或验证码格式不正确；`429` 错误次数达到上限。

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

该验证码只允许用于密码重置，不能用于注册登录；普通登录验证码也不能用于重置密码。发送频率、每日上限和开发环境响应格式与登录验证码相同。

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

## 8. 运维接口

### 8.1 存活检查

```http
GET /healthz
```

权限：公开。只表示 FastAPI 进程可以响应，不检查 MySQL 和 Redis。

```json
{
  "status": "ok"
}
```

### 8.2 就绪检查

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

## 9. 当前能力边界

以下功能已有接口或模型骨架，但尚未完成真实第三方接入：

- 生产短信发送适配器。
- 微信公众号扫码登录场景码、回调和签名校验。
- 微信与支付宝预支付参数生成。
- 微信与支付宝支付回调验签和到账处理。
- 月度套餐续费、取消、到期和周期权益结算。
- refresh token 逐次轮换、单设备撤销、退出登录和多设备会话管理。
- 点数流水分页和用户列表总数。

不要将占位接口返回值视为第三方平台已接入。

## 10. 点数与支付安全约定

- `PointLedger` 是不可变审计记录。
- `PointBalance` 是同一事务内更新并加行锁保护的余额投影。
- 点数消费使用用户范围内的幂等键，避免重试造成重复扣点。
- 前端不能自行上报“支付成功”，支付到账必须以服务端验证通过的平台回调为准。
- 生产运营应定期核对账本 `SUM(delta)` 与余额投影，发现偏差时以账本重建投影。
- 数据库、Redis、短信和支付密钥不得写入前端、接口响应、日志或本文档。

## 11. 密码安全约定

- 数据库只保存带独立随机盐的 `scrypt` 密码摘要，不保存或记录明文密码。
- 密码长度为 8～128 个字符，服务端不会擅自裁剪首尾空格或改变字符内容。
- 默认连续输错 5 次后锁定密码登录 15 分钟，可通过 `PASSWORD_MAX_ATTEMPTS` 和 `PASSWORD_LOCK_MINUTES` 调整。
- 登录验证码与密码重置验证码用途隔离，验证码使用一次后即失效。
- 设置、修改或重置密码都会递增帐号认证版本，使旧 access token 和 refresh token 失效。
