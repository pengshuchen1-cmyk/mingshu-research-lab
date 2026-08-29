# API 功能测试文档

> 测试对象：仓库根目录 `backend/` 独立 FastAPI 后端。
>
> 基准日期：2026-08-21。
>
> 契约来源：实际路由、Pydantic schema、service、ORM、错误目录、运行时 OpenAPI 和 `docs/API_INTEGRATION.md`，不以旧 `bazi_ziwei_app/backend/` 为准。

## 1. 测试目标和范围

当前运行时共有 **30 个 HTTP API**：GET 12、POST 14、PUT 3、PATCH 1、DELETE 0。

本文共整理 **227 条可执行测试用例**，覆盖：

- 30 个接口的正常、异常、边界和权限行为。
- 手机号密码直接注册、密码登录、Token 生命周期。
- 可选 OTP 注册/登录和密码找回。
- 用户信息、点数余额、流水和幂等扣点。
- 套餐、待支付订单和支付占位边界。
- 管理员套餐、规则、用户启停和充值统计。
- 命理档案预览、确认、查询、修改、重建和跨用户隔离。
- CORS、敏感信息、并发、幂等和依赖故障。

以下尚未实现真实业务，只验证当前安全边界，不作为“功能可上线”验收：

- 微信扫码登录。
- 微信/支付宝真实预支付、验签、到账、退款和订单状态查询。
- SSE、WebSocket、文件上传、AI 问答和报告生成。

接口请求字段、响应字段和前端调用示例见配套文档 [`API_INTEGRATION.md`](API_INTEGRATION.md)。本文用于测试执行和验收，不重复把动态响应整包写死。

## 2. 测试环境

### 2.1 服务地址

```text
Base URL: http://127.0.0.1:8000
Swagger:  http://127.0.0.1:8000/docs
OpenAPI:  http://127.0.0.1:8000/openapi.json
```

启动并检查：

```bash
cd backend
docker compose up -d --build
docker compose ps -a
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

通过条件：

- `api`、`mysql`、`redis` 为 healthy。
- `migrate` 为 `Exited (0)`；它是一次性任务，不需要保持 Running。
- `/healthz` 返回 `{"status":"ok"}`。
- `/readyz` 返回 `{"status":"ready"}`。

### 2.2 默认测试配置

| 配置 | 默认值 | 影响 |
|---|---:|---|
| `ACCESS_TOKEN_MINUTES` | 30 | access token 有效期 |
| `REFRESH_TOKEN_DAYS` | 30 | refresh token 有效期 |
| `REGISTRATION_BONUS_POINTS` | 20 | 新用户赠送点数 |
| `OTP_TTL_SECONDS` | 300 | OTP 5 分钟有效 |
| `OTP_RESEND_SECONDS` | 60 | 同手机号重发间隔 |
| `OTP_DAILY_LIMIT` | 10 | 同手机号滚动 24 小时上限 |
| `OTP_MAX_ATTEMPTS` | 5 | OTP 最大错误次数 |
| `PASSWORD_MAX_ATTEMPTS` | 5 | 密码最大连续错误次数 |
| `PASSWORD_LOCK_MINUTES` | 15 | 密码登录锁定时间 |
| `PROFILE_EDIT_COOLDOWN_DAYS` | 30 | 档案第二次及后续修改冷却 |

若为缩短限流类用例而修改 `.env`，必须重建 API，并在报告中记录实际配置。不得在生产环境降低这些限制。

### 2.3 测试帐号和数据

建议至少准备：

| 代号 | 用途 |
|---|---|
| U1 | 密码注册、登录、命盘主流程 |
| U2 | 跨用户资源隔离、停用用户 |
| U3 | OTP 注册、首次设置密码、密码重置 |
| ADMIN | 管理员接口、套餐和规则造数 |

手机号必须能通过 `phonenumbers` 校验。同一个测试数据库没有删除用户接口，重复执行时应换一个有效测试手机号。

将已经注册的 ADMIN 提升为管理员，仅允许在专用测试数据库执行：

```bash
docker compose exec mysql sh -lc 'exec mysql -u"$MYSQL_USER" -p"$MYSQL_PASSWORD" "$MYSQL_DATABASE"'
```

进入 MySQL 后执行：

```sql
UPDATE users SET role = 'admin' WHERE phone = '+8613800138001';
```

退出后重新登录 ADMIN，再执行管理端用例。

如确实需要清空全部本地测试数据，`docker compose down -v` 会永久删除当前 Compose 的 MySQL/Redis 卷。只能在确认是一次性本地测试环境后使用，不得对共享或生产环境执行。

### 2.4 推荐工具

- 手工联调：Swagger、Apifox、Postman 或 curl。
- 自动化：pytest + httpx/TestClient。
- 浏览器 CORS：实际前端页面或浏览器开发者工具。
- 并发测试：k6、JMeter、pytest asyncio 或并行 curl。

## 3. 通用断言规范

### 3.1 请求格式

JSON 请求统一使用：

```http
Content-Type: application/json
Accept: application/json
```

受保护接口统一使用：

```http
Authorization: Bearer <access_token>
```

refresh token 只放 `/auth/refresh` 的 JSON Body，不能作为 Bearer 调业务接口。

### 3.2 错误结构

业务错误：

```json
{"detail":"Account already registered"}
```

参数校验错误：

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "input": "short"
    }
  ]
}
```

通用断言：

- 不能只判断 HTTP 200；必须同时检查状态码、响应结构和数据库副作用。
- 401 后前端最多刷新并重试一次，不能无限循环。
- 404 同时用于“资源不存在”和“不属于当前用户”，测试不能要求后端区分。
- 未捕获 500 可能是纯文本 `Internal Server Error`。
- 默认 422 可能回显输入值；测试报告必须删除真实密码、JWT、手机号和出生信息。

### 3.3 ID、时间和排序

- 当前输出 ID 是 36 字符 UUID 字符串，但部分输入只按普通 string 校验。
- 时间按 ISO 字符串断言，不要强制要求所有环境都有 `Z`。
- 只有代码明确指定排序的接口才断言顺序。
- 动态命盘内部 JSON 不做整包快照断言，优先断言稳定顶层字段和关键事实。

### 3.4 用例结果记录

每个失败用例至少记录：

```text
用例 ID：
环境/配置：
请求 Method + URL：
脱敏后的请求：
实际状态码：
脱敏后的实际响应：
预期：
是否可稳定复现：
相关日志时间：
```

## 4. 30 个接口覆盖矩阵

| Method | URL | 主要用例 | 等级 |
|---|---|---|---|
| GET | `/healthz` | OPS-001～003 | P0 |
| GET | `/readyz` | OPS-004～008 | P0 |
| POST | `/api/v1/auth/otp/login/code` | AUTH-OTP-001～008 | P1 |
| POST | `/api/v1/auth/otp/login` | AUTH-OTP-009～016 | P1 |
| POST | `/api/v1/auth/password/register` | AUTH-REG-001～014 | P0 |
| POST | `/api/v1/auth/password/login` | AUTH-LOGIN-001～010 | P0 |
| PUT | `/api/v1/auth/password` | AUTH-PWD-001～010 | P1 |
| POST | `/api/v1/auth/password/reset/otp` | AUTH-RESET-001～005 | P1 |
| POST | `/api/v1/auth/password/reset` | AUTH-RESET-006～013 | P1 |
| POST | `/api/v1/auth/refresh` | AUTH-TOKEN-001～009 | P0 |
| GET | `/api/v1/auth/wechat/qr` | BOUNDARY-001～002 | 边界 |
| GET | `/api/v1/me` | USER-001～007 | P0 |
| GET | `/api/v1/points/ledger` | POINT-001～005 | P1 |
| POST | `/api/v1/points/consume` | POINT-006～016 | P1 |
| GET | `/api/v1/payments/packages` | PAY-001～004 | P1 |
| POST | `/api/v1/payments/orders` | PAY-005～011 | 边界 |
| POST | `/api/v1/payments/webhooks/{provider}` | BOUNDARY-003～006 | 边界 |
| POST | `/api/v1/admin/packages` | ADMIN-PKG-001～007 | P2 |
| GET | `/api/v1/admin/packages` | ADMIN-PKG-008～010 | P2 |
| PUT | `/api/v1/admin/feature-rules/{code}` | ADMIN-RULE-001～008 | P2 |
| GET | `/api/v1/admin/users` | ADMIN-USER-001～009 | P2 |
| PATCH | `/api/v1/admin/users/{user_id}/active` | ADMIN-USER-010～017 | P2 |
| GET | `/api/v1/admin/recharge-statistics` | ADMIN-STAT-001～010 | P2 |
| POST | `/api/v1/chart-profiles/preview` | CHART-PREVIEW-001～017 | P0 |
| POST | `/api/v1/chart-profiles` | CHART-CREATE-001～010 | P0 |
| GET | `/api/v1/chart-profiles` | CHART-LIST-001～007 | P0 |
| GET | `/api/v1/chart-profiles/{profile_id}` | CHART-DETAIL-001～005 | P0 |
| PUT | `/api/v1/chart-profiles/{profile_id}` | CHART-UPDATE-001～012 | P1 |
| GET | `/api/v1/chart-profiles/{profile_id}/chart` | CHART-SNAPSHOT-001～004 | P1 |
| POST | `/api/v1/chart-profiles/{profile_id}/regenerate` | CHART-REGEN-001～007 | P1 |

## 5. 运维和基础设施测试

### 5.1 存活与就绪

| 用例 | 操作 | 预期 |
|---|---|---|
| OPS-001 | `GET /healthz` | 200，`{"status":"ok"}` |
| OPS-002 | 不带任何 Header 请求 healthz | 200，无鉴权要求 |
| OPS-003 | MySQL 或 Redis 不可用时请求 healthz | 仍为 200，只代表 API 进程存活 |
| OPS-004 | MySQL、Redis 正常时请求 readyz | 200，`{"status":"ready"}` |
| OPS-005 | 停止 Redis 后请求 readyz | 503，`redis is not ready` |
| OPS-006 | 恢复 Redis 后请求 readyz | 恢复为 200 |
| OPS-007 | 停止 MySQL 后请求 readyz | 503，`database is not ready` |
| OPS-008 | 恢复 MySQL 后请求 readyz | 恢复为 200 |

依赖故障测试必须串行执行，完成后立即恢复：

```bash
docker compose stop redis
docker compose start redis
docker compose stop mysql
docker compose start mysql
```

不要在其他测试人员正在共享环境执行用例时停止依赖。

## 6. 认证功能测试

### 6.1 手机号密码直接注册

接口：`POST /api/v1/auth/password/register`。

基准请求：

```json
{
  "phone": "13800138000",
  "password": "TestPassword123"
}
```

| 用例 | 操作 | 预期 |
|---|---|---|
| AUTH-REG-001 | 新手机号、合法密码注册 | 201；返回 access/refresh；`token_type=bearer`；`new_user=true` |
| AUTH-REG-002 | 注册时不提交 `code` | 201；接口不依赖 OTP |
| AUTH-REG-003 | 注册成功后请求 `/me` | 200；`has_password=true`；`points=20` |
| AUTH-REG-004 | 注册成功后查询流水 | 只有一次注册赠送流水；`delta=20`、`balance_after=20` |
| AUTH-REG-005 | 同一手机号重复注册 | 409 `Account already registered` |
| AUTH-REG-006 | 国内号码注册后用相同号码 `+86` 格式注册 | 409，证明规范化后唯一 |
| AUTH-REG-007 | 无效手机号 | 422 `Invalid phone number` |
| AUTH-REG-008 | 缺少 phone | 422 |
| AUTH-REG-009 | 缺少 password | 422 |
| AUTH-REG-010 | 密码 7 字符 | 422 |
| AUTH-REG-011 | 密码 8 字符 | 201 |
| AUTH-REG-012 | 密码 128 字符 | 201 |
| AUTH-REG-013 | 密码 129 字符 | 422 |
| AUTH-REG-014 | 两个请求并发注册同一规范化手机号 | 只能一个 201，另一个 409，只创建一个用户/钱包/赠送流水 |

当前代码不裁剪密码，也没有复杂度规则。8 个空格按现有 schema 可能通过长度校验，应作为安全改进项记录，而不能误报成“未符合现有接口契约”。

当前接口只校验手机号格式，不验证手机号归属。测试页面不能显示“手机号已验证”。

### 6.2 OTP 发送与注册/登录（可选功能）

接口：

```text
POST /api/v1/auth/otp/login/code
POST /api/v1/auth/otp/login
```

| 用例 | 操作 | 预期 |
|---|---|---|
| AUTH-OTP-001 | 开发环境对有效手机号请求 OTP | 200；`message=OTP sent`；返回6位 `development_code` |
| AUTH-OTP-002 | 无效手机号请求 OTP | 422 |
| AUTH-OTP-003 | 60秒内重复请求 | 429 `Please wait before requesting another OTP` |
| AUTH-OTP-004 | 滚动24小时达到10次 | 429 `Daily OTP limit reached` |
| AUTH-OTP-005 | 生产环境未配置短信 provider | 503 `SMS provider is not configured` |
| AUTH-OTP-006 | OTP 长度不是6位 | login 请求422 |
| AUTH-OTP-007 | OTP 包含非数字 | 422 |
| AUTH-OTP-008 | OTP 超过5分钟 | 登录400 |
| AUTH-OTP-009 | 新手机号提交正确 OTP | 200；自动注册；`new_user=true`；赠送点数 |
| AUTH-OTP-010 | 已有用户提交正确 OTP | 200；`new_user=false` |
| AUTH-OTP-011 | 错误 OTP | 400，失败次数增加 |
| AUTH-OTP-012 | 第5次错误 OTP | 400并消费挑战；后续请求达到限制 |
| AUTH-OTP-013 | 错误次数达到上限后继续提交 | 429 `OTP attempt limit reached` |
| AUTH-OTP-014 | 正确 OTP 使用两次 | 第一次成功，第二次400 |
| AUTH-OTP-015 | login-purpose OTP 用于密码重置 | 400 |
| AUTH-OTP-016 | 已停用用户使用正确 login OTP | 当前会返回 Token，但其受保护请求返回401；记录为已知缺陷 |

登录 OTP 和密码重置 OTP 的验证用途隔离，但发送频率和每日次数按手机号共享，不要同时快速请求两类 OTP 后期待都成功。

### 6.3 手机号密码登录

接口：`POST /api/v1/auth/password/login`。

| 用例 | 操作 | 预期 |
|---|---|---|
| AUTH-LOGIN-001 | 正确手机号和密码 | 200；TokenPair；`new_user=false` |
| AUTH-LOGIN-002 | 国内格式注册，使用 `+86` 登录 | 200 |
| AUTH-LOGIN-003 | 错误密码 | 401 `Invalid phone number or password` |
| AUTH-LOGIN-004 | 不存在手机号 | 同样401，不泄露帐号存在性 |
| AUTH-LOGIN-005 | OTP 注册但尚未设置密码 | 同样401 |
| AUTH-LOGIN-006 | 停用用户 | 同样401 |
| AUTH-LOGIN-007 | 前4次错误密码 | 每次401，失败计数累加 |
| AUTH-LOGIN-008 | 第5次错误密码 | 429并锁定 |
| AUTH-LOGIN-009 | 锁定期使用正确密码 | 429 |
| AUTH-LOGIN-010 | 锁定期结束后正确登录 | 200，失败计数清零 |

### 6.4 设置和修改密码

接口：`PUT /api/v1/auth/password`，需要 access token。

| 用例 | 操作 | 预期 |
|---|---|---|
| AUTH-PWD-001 | OTP 用户首次设置密码，仅传 new_password | 200；返回新 TokenPair |
| AUTH-PWD-002 | 密码注册用户修改密码但不传 current_password | 400 `Current password is required` |
| AUTH-PWD-003 | current_password 错误 | 401，失败次数增加 |
| AUTH-PWD-004 | current_password 连续错误到上限 | 429 |
| AUTH-PWD-005 | 新旧密码相同 | 409 `New password must be different...` |
| AUTH-PWD-006 | 正确修改密码 | 200，返回新 access/refresh |
| AUTH-PWD-007 | 修改成功后使用旧 access | 401 |
| AUTH-PWD-008 | 修改成功后使用旧 refresh | 401 |
| AUTH-PWD-009 | 新密码登录 | 200 |
| AUTH-PWD-010 | new_password 低于8或高于128字符 | 422 |

### 6.5 密码重置

接口：

```text
POST /api/v1/auth/password/reset/otp
POST /api/v1/auth/password/reset
```

| 用例 | 操作 | 预期 |
|---|---|---|
| AUTH-RESET-001 | 开发环境请求 reset OTP | 200，返回 development_code |
| AUTH-RESET-002 | 立即请求另一类 OTP | 可能429；两类发送共享手机号限流 |
| AUTH-RESET-003 | 无效手机号格式 | 422 |
| AUTH-RESET-004 | 生产短信 provider 未配置 | 503 |
| AUTH-RESET-005 | reset OTP 格式不是6位数字 | reset 请求422 |
| AUTH-RESET-006 | 正确 reset OTP + 新密码 | 200，新 TokenPair |
| AUTH-RESET-007 | 使用 login OTP 重置 | 400 |
| AUTH-RESET-008 | OTP 错误/过期/已使用 | 400 |
| AUTH-RESET-009 | OTP 错误达到上限 | 429 |
| AUTH-RESET-010 | 手机号没有用户但 OTP 有效 | 401 `User unavailable` |
| AUTH-RESET-011 | 重置成功后旧 Token | 401 |
| AUTH-RESET-012 | 使用重置后的密码登录 | 200 |
| AUTH-RESET-013 | 停用用户重置 | 当前可能返回 Token，但业务请求401；记录为已知缺陷 |

### 6.6 Refresh Token

接口：`POST /api/v1/auth/refresh`。

| 用例 | 操作 | 预期 |
|---|---|---|
| AUTH-TOKEN-001 | 有效 refresh token | 200；只返回 access_token 和 bearer |
| AUTH-TOKEN-002 | 不传 refresh_token | 422 |
| AUTH-TOKEN-003 | 空字符串/伪造 JWT | 401 `Invalid refresh token` |
| AUTH-TOKEN-004 | 把 access token 放入 refresh body | 401 `Refresh token required` |
| AUTH-TOKEN-005 | 把 refresh token作为 Bearer调 `/me` | 401 `Access token required` |
| AUTH-TOKEN-006 | refresh token 过期 | 401 |
| AUTH-TOKEN-007 | issuer 不匹配或签名被修改 | 401 |
| AUTH-TOKEN-008 | 用户停用后 refresh | 401 `User unavailable` |
| AUTH-TOKEN-009 | 密码改变导致 auth_version 增加后刷新旧 token | 401 |

不要强制断言新 access token 字符串一定与旧 token 不同；同一秒签发且 claims 相同时可能相同，应断言其有效性和 claims。

## 7. 当前用户和点数测试

### 7.1 当前用户

接口：`GET /api/v1/me`。

| 用例 | 操作 | 预期 |
|---|---|---|
| USER-001 | 密码注册后查询 | id、E.164 phone、role=user、has_password=true、points=20 |
| USER-002 | OTP 注册未设置密码 | has_password=false |
| USER-003 | 管理员查询 | role=admin |
| USER-004 | 不带 Token | 401 `Not authenticated` |
| USER-005 | 无效/过期 Token | 401 |
| USER-006 | 用户被停用后查询 | 401 `User unavailable` |
| USER-007 | 响应检查 | 不得出现 password_hash、auth_version、锁定计数 |

### 7.2 点数流水

接口：`GET /api/v1/points/ledger`。

| 用例 | 操作 | 预期 |
|---|---|---|
| POINT-001 | 新用户查询 | 包含注册赠送流水 |
| POINT-002 | 扣点后查询 | 新扣点流水排在前面，delta为负数 |
| POINT-003 | 无流水的历史/造数用户 | `[]` |
| POINT-004 | 用户U1查询 | 不包含U2流水 |
| POINT-005 | 不带/无效 Token | 401 |

本接口没有分页，数据较多时也会返回全部流水；性能测试应记录响应大小和耗时。

### 7.3 幂等扣点

接口：`POST /api/v1/points/consume`。

前置：管理员创建启用规则，例如 `report`，`points_cost=3`。

| 用例 | 操作 | 预期 |
|---|---|---|
| POINT-006 | 正常扣3点 | 200；balance从20变17；返回 ledger_id |
| POINT-007 | 相同用户、相同 key、相同 feature重试 | 200；同 ledger_id、同余额，不重复扣点 |
| POINT-008 | 相同用户和key，改用另一个 feature | 409幂等冲突 |
| POINT-009 | 两用户使用相同 key | 各自成功；key按用户隔离 |
| POINT-010 | key少于8字符 | 422 |
| POINT-011 | key多于128字符 | 422 |
| POINT-012 | feature不存在 | 404 `Feature rule not found` |
| POINT-013 | feature被停用 | 404 |
| POINT-014 | 余额不足 | 409 `Insufficient points`，余额和流水不变化 |
| POINT-015 | cost=0的启用规则 | 200；生成delta=0流水，余额不变 |
| POINT-016 | 多请求并发使用同一个幂等 key | 只扣一次，其他请求复用同一流水或得到可解释冲突，不得重复扣费 |

如果管理员在第一次扣点后修改了同一 feature 的 cost，再用原 key 重试，delta 不同会返回409，这是当前设计。

## 8. 套餐和支付测试

### 8.1 公开套餐

接口：`GET /api/v1/payments/packages`。

| 用例 | 操作 | 预期 |
|---|---|---|
| PAY-001 | 无套餐 | 200，`[]` |
| PAY-002 | 同时存在 active/inactive 套餐 | 只返回 active |
| PAY-003 | 不带 Token | 200，公开接口 |
| PAY-004 | monthly 套餐 | 可以返回，但当前没有续费/到期逻辑 |

### 8.2 创建待支付订单

接口：`POST /api/v1/payments/orders`。

| 用例 | 操作 | 预期 |
|---|---|---|
| PAY-005 | 登录用户+active套餐+wechat | 200，status=pending，payment_payload=null |
| PAY-006 | 登录用户+active套餐+alipay | 同上，provider=alipay |
| PAY-007 | 不带 Token | 401 |
| PAY-008 | 套餐不存在 | 404 `Package unavailable` |
| PAY-009 | 套餐 inactive | 404 |
| PAY-010 | provider不是wechat/alipay | 422 |
| PAY-011 | 建单后查询用户点数 | 点数不增加，订单不会自动变paid |

该接口当前只能验证“生成 pending 订单记录”，不能按真实支付功能验收。

## 9. 管理员功能测试

所有 `/admin/*` 用例先验证三组权限：无 Token=401、普通用户=403、管理员进入业务逻辑。

### 9.1 套餐管理

| 用例 | 操作 | 预期 |
|---|---|---|
| ADMIN-PKG-001 | 管理员创建 one_time 套餐 | 200，返回完整套餐 |
| ADMIN-PKG-002 | 创建 monthly 套餐 | 200 |
| ADMIN-PKG-003 | active省略 | 默认true |
| ADMIN-PKG-004 | points或price_fen为0/负数 | 422 |
| ADMIN-PKG-005 | kind非法 | 422 |
| ADMIN-PKG-006 | 套餐名重复 | 409 `Package name already exists` |
| ADMIN-PKG-007 | 普通用户创建 | 403 |
| ADMIN-PKG-008 | 查询全部套餐 | 200，包含active和inactive |
| ADMIN-PKG-009 | 无套餐 | `[]` |
| ADMIN-PKG-010 | 列表顺序 | 不做固定顺序断言，代码未指定排序 |

套餐 name 的 Pydantic schema 当前没有长度和空白校验。空字符串或超长字符串属于探索性测试；若数据库抛500，应登记为已知输入校验缺口，不应视为正确行为。

### 9.2 FeatureRule 管理

| 用例 | 操作 | 预期 |
|---|---|---|
| ADMIN-RULE-001 | 新 code + 正成本 | 200，创建规则 |
| ADMIN-RULE-002 | 同 code 再 PUT | 200，更新原规则，不新增第二条 |
| ADMIN-RULE-003 | points_cost=0 | 200 |
| ADMIN-RULE-004 | points_cost负数 | 422 |
| ADMIN-RULE-005 | active省略 | 默认true |
| ADMIN-RULE-006 | active=false | 200，用户 consume 随后404 |
| ADMIN-RULE-007 | 普通用户 | 403 |
| ADMIN-RULE-008 | code超过数据库64字符 | 当前可能数据库错误；登记输入校验缺口 |

### 9.3 用户列表和启停

| 用例 | 操作 | 预期 |
|---|---|---|
| ADMIN-USER-001 | 默认查询 | 200，created_at倒序，默认limit=20 |
| ADMIN-USER-002 | phone片段过滤 | 只返回号码包含该文本的用户 |
| ADMIN-USER-003 | offset=0、limit=1 | 返回最多1条 |
| ADMIN-USER-004 | offset负数 | 422 |
| ADMIN-USER-005 | limit=0 | 422 |
| ADMIN-USER-006 | limit=100 | 可接受 |
| ADMIN-USER-007 | limit=101 | 422 |
| ADMIN-USER-008 | 响应字段 | 含has_password，不含password_hash/auth_version/锁定计数 |
| ADMIN-USER-009 | 普通用户查询 | 403 |
| ADMIN-USER-010 | 停用存在用户 | 200，is_active=false |
| ADMIN-USER-011 | 停用后旧access调用业务 | 401 |
| ADMIN-USER-012 | 停用后refresh | 401 |
| ADMIN-USER-013 | 重新启用 | 200；原未过期且版本匹配的Token可能恢复可用 |
| ADMIN-USER-014 | 不存在user_id | 404 `User not found` |
| ADMIN-USER-015 | user_id格式不是UUID | 路由按普通string处理，最终404 |
| ADMIN-USER-016 | body缺少is_active或类型错误 | 422 |
| ADMIN-USER-017 | 管理员停用自己 | 当前允许；随后自身Token不可用，登记产品风险 |

### 9.4 充值统计

| 用例 | 操作 | 预期 |
|---|---|---|
| ADMIN-STAT-001 | 无paid订单 | 200，`[]` |
| ADMIN-STAT-002 | 测试库造1条wechat paid订单 | 返回wechat、orders=1、正确amount_fen |
| ADMIN-STAT-003 | 多条同provider paid订单 | 聚合订单数和金额 |
| ADMIN-STAT-004 | 同时存在pending订单 | pending不计入 |
| ADMIN-STAT-005 | provider过滤 | 只返回指定provider |
| ADMIN-STAT-006 | package_id过滤 | 只统计指定套餐 |
| ADMIN-STAT-007 | start_at/end_at边界 | paid_at等于边界时包含 |
| ADMIN-STAT-008 | start_at大于end_at | 422 `start_at must be before end_at` |
| ADMIN-STAT-009 | datetime无法解析 | 422 |
| ADMIN-STAT-010 | 普通用户 | 403 |

paid 数据只能在专用测试数据库造数；当前 API 支付回调不会自然生成 paid 订单。

## 10. 命理档案和命盘测试

### 10.1 基准输入

公历精确时间：

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

未知时辰：

```json
{
  "name": "测试用户",
  "gender": "女",
  "calendar_type": "solar",
  "birth_date": "1998-01-01",
  "birth_hour": null,
  "birth_minute": null,
  "birth_place": "",
  "is_leap_month": false,
  "time_label": "时辰不详"
}
```

测试日志和缺陷单应使用虚构数据，不得使用真实用户出生信息和完整命盘。

### 10.2 Preview

接口：`POST /api/v1/chart-profiles/preview`。

| 用例 | 操作 | 预期 |
|---|---|---|
| CHART-PREVIEW-001 | 基准公历输入 | 200；四柱4项；双指纹各64位小写hex |
| CHART-PREVIEW-002 | 完全相同输入重复调用 | 指纹和排盘事实一致 |
| CHART-PREVIEW-003 | 修改姓名 | input_fingerprint变化；chart_fingerprint可保持不变 |
| CHART-PREVIEW-004 | 修改出生事实 | 双指纹按实际事实变化 |
| CHART-PREVIEW-005 | name首尾空格 | 被裁剪后参与结果 |
| CHART-PREVIEW-006 | 未知时辰：hour/minute均null | 200 |
| CHART-PREVIEW-007 | 只传hour不传minute | 422 |
| CHART-PREVIEW-008 | hour=-1或24 | 422 |
| CHART-PREVIEW-009 | minute=-1或60 | 422 |
| CHART-PREVIEW-010 | gender不是男/女 | 422 |
| CHART-PREVIEW-011 | calendar_type非法 | 422 |
| CHART-PREVIEW-012 | 公历不存在日期 | 422 |
| CHART-PREVIEW-013 | 未来公历日期 | 422 |
| CHART-PREVIEW-014 | 年份小于1900或大于当前年 | 422 |
| CHART-PREVIEW-015 | solar输入is_leap_month=true | 422 |
| CHART-PREVIEW-016 | 农历月超1～12或日超1～30 | 422 |
| CHART-PREVIEW-017 | 不带/无效 Token | 401 |

### 10.3 创建档案

流程必须是 preview 后，把完全相同的9个输入字段加上返回的两个指纹提交创建。

| 用例 | 操作 | 预期 |
|---|---|---|
| CHART-CREATE-001 | 原输入+原双指纹 | 201，返回profile+chart |
| CHART-CREATE-002 | expected_input_fingerprint缺失 | 422 |
| CHART-CREATE-003 | expected_chart_fingerprint缺失 | 422 |
| CHART-CREATE-004 | 指纹不是64位小写hex | 422 |
| CHART-CREATE-005 | preview后改输入但沿用旧指纹 | 409，不创建档案 |
| CHART-CREATE-006 | 手工伪造合法格式指纹 | 409 |
| CHART-CREATE-007 | 创建成功后的profile | `can_edit=true`、last_edited_at/next_edit_at为null |
| CHART-CREATE-008 | chart.profile检查 | 不包含name和birth_place |
| CHART-CREATE-009 | 使用返回的profile.id查询 | 200 |
| CHART-CREATE-010 | 使用chart.id当profile_id查询 | 404 |

### 10.4 列表与详情

| 用例 | 操作 | 预期 |
|---|---|---|
| CHART-LIST-001 | 当前用户无档案 | `[]` |
| CHART-LIST-002 | 创建多条后默认查询 | created_at倒序，默认最多20条 |
| CHART-LIST-003 | offset=0、limit=1 | 最多1条 |
| CHART-LIST-004 | offset负数 | 422 |
| CHART-LIST-005 | limit=0或101 | 422 |
| CHART-LIST-006 | U1和U2各有档案 | 各自列表只包含自己的数据 |
| CHART-LIST-007 | 列表响应 | 不包含完整chart JSON，没有total/has_more |
| CHART-DETAIL-001 | 所有者查询profile.id | 200，profile+chart |
| CHART-DETAIL-002 | 不存在profile_id | 404 |
| CHART-DETAIL-003 | U2查询U1 profile_id | 404 |
| CHART-DETAIL-004 | 非UUID字符串 | 404，不是422 |
| CHART-DETAIL-005 | 不带Token | 401 |

### 10.5 修改档案

修改前必须对新输入重新 preview。

| 用例 | 操作 | 预期 |
|---|---|---|
| CHART-UPDATE-001 | 新建档案第一次修改 | 200，允许立即修改 |
| CHART-UPDATE-002 | 修改成功后 | edit状态反映`can_edit=false`，返回next_edit_at |
| CHART-UPDATE-003 | 冷却期内第二次修改 | 429 |
| CHART-UPDATE-004 | `PROFILE_EDIT_COOLDOWN_DAYS=0`环境连续修改 | 均可成功 |
| CHART-UPDATE-005 | 使用旧preview指纹 | 409 |
| CHART-UPDATE-006 | U2修改U1档案且body/指纹有效 | 404 |
| CHART-UPDATE-007 | 不存在ID且body/指纹有效 | 404 |
| CHART-UPDATE-008 | 非法body访问不存在ID | 当前可能先422，因为代码先排盘；按现状记录 |
| CHART-UPDATE-009 | 错误指纹访问不存在ID | 当前可能先409；登记执行顺序风险 |
| CHART-UPDATE-010 | 更新成功后查询详情 | profile和chart同步为新输入 |
| CHART-UPDATE-011 | 两个请求并发修改同一档案 | 行锁避免静默覆盖；最多按冷却规则成功一次 |
| CHART-UPDATE-012 | 修改失败 | 原profile和chart不得部分更新 |

### 10.6 命盘快照和重建

| 用例 | 操作 | 预期 |
|---|---|---|
| CHART-SNAPSHOT-001 | 所有者读取 `/chart` | 200，只返回BaziChartOut |
| CHART-SNAPSHOT-002 | U2读取U1快照 | 404 |
| CHART-SNAPSHOT-003 | profile不存在 | 404 |
| CHART-SNAPSHOT-004 | 不带Token | 401 |
| CHART-REGEN-001 | 所有者重建 | 200，profile_id/chart关联保持 |
| CHART-REGEN-002 | 重建后generated_at | 更新或不早于旧值 |
| CHART-REGEN-003 | 重建后profile字段 | 不变化，edit_count/冷却不变化 |
| CHART-REGEN-004 | 冷却期内重建 | 仍可执行，重建不属于档案编辑 |
| CHART-REGEN-005 | U2重建U1档案 | 404 |
| CHART-REGEN-006 | 不存在profile | 404 |
| CHART-REGEN-007 | 并发重建和编辑 | 行锁后最终chart必须与最终profile一致，不得旧数据覆盖新数据 |

命盘 `chart` 当前在 response model 中只是动态 dict。测试应重点检查：

- 顶层 id、profile_id、input_fingerprint、chart_fingerprint、engine_version、generated_at。
- `chart.profile`、`chart.pillars`、`chart.facts` 存在且结构为对象。
- 不要把所有内部文案或 engine_version 写死成永不变化的快照。

## 11. 能力边界测试

| 用例 | 操作 | 当前正确结果 |
|---|---|---|
| BOUNDARY-001 | 未配置WECHAT_APP_ID请求 `/auth/wechat/qr` | 501 `WeChat QR login is not configured` |
| BOUNDARY-002 | 配置任意WECHAT_APP_ID后请求 | 200但只有实现提示，不应出现可用二维码流程 |
| BOUNDARY-003 | webhook provider=wechat，body合法 | 501支付验签未配置 |
| BOUNDARY-004 | webhook provider=alipay，body合法 | 501 |
| BOUNDARY-005 | webhook provider未知 | 404 `Unknown payment provider` |
| BOUNDARY-006 | webhook body缺字段 | 在路由业务前返回422 |

这些用例通过只代表“占位接口安全失败”，不代表微信或支付功能完成。

扫描边界：当前没有 SSE、WebSocket、StreamingResponse、UploadFile、Form 或任务轮询接口。前端和测试不得构造不存在的流式/上传测试流程。

## 12. 横向安全、并发和兼容性测试

### 12.1 权限矩阵

对每个受保护接口至少重复以下组合：

| Token | 用户接口 | 管理员接口 |
|---|---|---|
| 无 Token | 401 | 401 |
| 伪造/过期 access | 401 | 401 |
| refresh 作为 Bearer | 401 | 401 |
| 正常普通用户 access | 进入业务 | 403 |
| 正常管理员 access | 进入业务 | 进入业务 |
| 停用用户 access | 401 | 401 |

### 12.2 CORS

本地 `.env.example` 默认允许 `http://localhost:3000`。

| 用例 | 预期 |
|---|---|
| 允许 Origin 的预检请求 | 返回对应 `Access-Control-Allow-Origin` |
| 未配置 Origin | 浏览器侧被CORS阻止，不返回允许Origin Header |
| Authorization Header预检 | 被允许 |
| Cookie credentials | 后端没有Cookie Session，`allow_credentials=false` |

### 12.3 敏感字段

检查所有响应和日志：

- 不得返回 password_hash。
- 不得在业务响应返回数据库密码、Redis密码或 JWT secret。
- `/admin/users` 不得返回 auth_version、密码失败次数或锁定时间。
- `chart.profile` 不得包含姓名和出生地点。
- 422 当前会回显非法 password/token 输入，必须记录为已知安全问题，测试材料需要人工脱敏。

### 12.4 并发和原子性

最低并发场景：

1. 相同手机号同时注册：一个成功、一个冲突，只赠送一次点数。
2. 相同用户和幂等 key 同时扣点：只扣一次。
3. 相同档案同时更新：不得部分覆盖或产生 profile/chart 不一致。
4. 重建和更新同时发生：最终命盘必须对应最终档案。
5. 余额不足的并发扣点：余额不得小于0。

### 12.5 OpenAPI 和文档一致性

检查：

- OpenAPI 操作总数为30。
- Method 统计为 GET 12、POST 14、PUT 3、PATCH 1、DELETE 0。
- `/auth/password/register` request schema 只要求 phone、password。
- 注册成功状态为201。
- 所有文档 URL 都包含完整 `/api/v1` prefix。

14个接口目前没有严格 response_model，OpenAPI 成功 schema 可能显示 `{}`。这些接口需要按实际响应断言，并把后端补 response model 作为契约改进任务。

## 13. 执行顺序

### P0：每次联调和发布前必须通过

1. OPS-001、OPS-004。
2. AUTH-REG 全部。
3. AUTH-LOGIN 全部。
4. AUTH-TOKEN 全部。
5. USER-001、USER-004、USER-007。
6. CHART-PREVIEW、CHART-CREATE、CHART-LIST、CHART-DETAIL。
7. 跨用户档案隔离。

### P1：用户完整功能

1. OTP 可选登录和密码重置。
2. 密码设置/修改和旧 Token 撤销。
3. 点数流水、扣点、余额不足和幂等。
4. 档案修改、冷却、命盘快照和重建。
5. 公开套餐查询。

### P2：管理和运营

1. 管理员权限矩阵。
2. 套餐、FeatureRule。
3. 用户列表和启停。
4. 充值统计造数测试。
5. 支付/微信占位边界。

## 14. 发布阻断标准

出现以下任一情况应阻断发布或前端联调：

- 密码注册仍要求验证码，或 request schema 出现必填 code。
- 重复注册覆盖原密码或重复发放注册奖励。
- 密码明文进入数据库、响应或日志。
- 密码登录、Token refresh 或密码变更撤销失效。
- 普通用户能够调用管理员接口。
- 用户能够读取或修改其他用户的档案。
- 点数并发后余额小于0，或同一幂等 key 重复扣费。
- preview/create 指纹不一致仍能保存。
- profile 更新成功但 chart 未同步，或反之。
- `/readyz` 在 MySQL/Redis 正常时不是200。
- 运行时 Method、URL、状态码或关键字段与接口文档不一致。

以下是已知能力限制，不单独作为本阶段阻断项，但必须在测试报告中列出：

- 密码注册不验证手机号归属。
- OTP 生产短信未接入。
- 微信和支付为占位。
- 14个接口缺少 response_model。
- 422可能回显敏感输入。
- 停用用户的部分 OTP 流程状态检查不完整。
- 动态命盘 JSON 没有完整嵌套 schema。

## 15. 当前自动化基线

```text
pytest: 35 passed, 3 warnings
运行时 OpenAPI: 30 operations
GET 12 / POST 14 / PUT 3 / PATCH 1 / DELETE 0
Docker: API/MySQL/Redis healthy，migrate Exited (0)
```

现有自动化已经覆盖密码直接注册的成功、重复手机号、字段错误、密码登录、注册赠送、密码摘要和不产生 OTP 记录。本文中的其余手工用例应逐步沉淀为 HTTP 回归和并发测试。
