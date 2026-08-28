# 前端接口变更与联调说明（2026-08-28）

> 对比范围：`3dfcbfc`（当前 `HEAD`）到当前合并工作区  
> API 前缀：`/api/v1`  
> 本地地址：`http://127.0.0.1:8000`  
> OpenAPI：`http://127.0.0.1:8000/openapi.json`  
> Swagger UI：`http://127.0.0.1:8000/docs`

## 1. 结论与影响范围

本次只有 **AI 命理问答**接口发生变化：删除 1 个旧接口，新增 7 个会话式接口。支付、认证、用户、点数、记忆档案、命盘、运势、报告、合婚和紫微接口均未改变。

这是一次破坏性变更。前端不能继续调用旧接口，必须切换到“创建/选择会话 → 拉取历史消息 → 发送问题”的流程。

### 1.1 删除的接口

| 方法 | 旧路径 | 当前行为 | 替代接口 |
|---|---|---|---|
| `POST` | `/api/v1/chart-profiles/{profile_id}/questions` | 已移除，返回 `404` | 先创建会话，再向会话发送消息 |

旧请求中的 `history` 字段同时废弃。前端不得再上传对话历史，历史由后端从数据库读取。

### 1.2 新增的接口

| 功能 | 方法 | 路径 | 成功状态码 |
|---|---|---|---:|
| 创建会话 | `POST` | `/api/v1/ai-conversations` | `201` |
| 查询会话列表 | `GET` | `/api/v1/ai-conversations` | `200` |
| 查询会话详情 | `GET` | `/api/v1/ai-conversations/{conversation_id}` | `200` |
| 修改标题/归档状态 | `PATCH` | `/api/v1/ai-conversations/{conversation_id}` | `200` |
| 删除会话 | `DELETE` | `/api/v1/ai-conversations/{conversation_id}` | `204` |
| 查询消息列表 | `GET` | `/api/v1/ai-conversations/{conversation_id}/messages` | `200` |
| 发送问题 | `POST` | `/api/v1/ai-conversations/{conversation_id}/messages` | `200` |

以上 7 个接口全部要求：

```http
Authorization: Bearer <access_token>
```

会话、消息和档案均按当前用户隔离。访问不存在、已删除或属于其他用户的会话统一返回 `404`。

## 2. 旧版到新版迁移对照

旧版：

```http
POST /api/v1/chart-profiles/{profile_id}/questions
```

```json
{
  "question": "未来三年的事业重点是什么？",
  "history": []
}
```

新版第一次提问需要两步：

```http
POST /api/v1/ai-conversations
```

```json
{
  "profile_id": "36 字符的命理档案 ID"
}
```

拿到响应中的 `id` 后：

```http
POST /api/v1/ai-conversations/{conversation_id}/messages
```

```json
{
  "question": "未来三年的事业重点是什么？",
  "idempotency_key": "chat-20260828-f47ac10b"
}
```

关键差异：

| 项目 | 旧版 | 新版 |
|---|---|---|
| 命盘档案 | 放在问答路径 `profile_id` | 创建会话时传 `profile_id`，会话永久绑定该档案 |
| 对话历史 | 前端传 `history` | 后端自动读取最近 6 条已完成消息 |
| 防重复提交 | 无 | 每个新问题必须传新的 `idempotency_key` |
| 会话历史 | 前端自行保存 | 后端持久化会话、问题和回答 |
| 会话管理 | 无 | 支持列表、详情、改名、归档、恢复和软删除 |
| 并发 | 未形成会话级约束 | 同一会话同一时间只能生成一个回答 |

## 3. 数据类型

前端可按以下 TypeScript 类型接入：

```ts
type ConversationStatus = "active" | "archived";
type MessageRole = "user" | "assistant";
type MessageStatus = "pending" | "completed" | "failed";

interface AIConversation {
  id: string;
  profile_id: string;
  title: string;
  status: ConversationStatus;
  message_count: number;
  last_message_at: string;
  created_at: string;
  updated_at: string;
}

interface AIMessage {
  id: string;
  conversation_id: string;
  sequence_no: number;
  role: MessageRole;
  content: string | null;
  status: MessageStatus;
  structured_content: Record<string, unknown> | null;
  created_at: string;
}

interface StructuredAnswer {
  source: "local_rules" | "cloud_validated" | "boundary" | "clarification";
  provider: string | null;
  sections: Record<string, unknown>;
  chart_evidence: string[];
  rule_evidence: string[];
  timing_conditions: string[];
  practical_advice: string[];
  uncertainty: string[];
  interpretation_receipt: string;
  retryable: boolean;
  violation_codes: string[];
}

interface SendMessageResult {
  conversation_id: string;
  user_message_id: string;
  assistant_message_id: string;
  profile_id: string;
  chart_fingerprint: string;
  mode: "local" | "cloud";
  answer: string;
  structured_answer: StructuredAnswer;
  degradation_reason: string | null;
  boundary_note: string;
  idempotent_replay: boolean;
}
```

所有时间字段均为 ISO 8601 字符串。前端展示时再转换为本地时区。

## 4. 接口明细

### 4.1 创建会话

```http
POST /api/v1/ai-conversations
Content-Type: application/json
Authorization: Bearer <access_token>
```

请求体：

```json
{
  "profile_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "title": "未来三年事业分析"
}
```

| 字段 | 必填 | 规则 |
|---|:---:|---|
| `profile_id` | 是 | 长度 36；必须属于当前用户且已有命盘 |
| `title` | 否 | 去除首尾空白后长度 `1`～`100` |

省略 `title` 时初始标题为“新会话”；第一次成功提交问题时，后端会自动使用压缩空白后的问题前 30 个字符作为标题。

响应 `201`：

```json
{
  "id": "会话 ID",
  "profile_id": "档案 ID",
  "title": "未来三年事业分析",
  "status": "active",
  "message_count": 0,
  "last_message_at": "2026-08-28T08:00:00Z",
  "created_at": "2026-08-28T08:00:00Z",
  "updated_at": "2026-08-28T08:00:00Z"
}
```

### 4.2 查询会话列表

```http
GET /api/v1/ai-conversations?profile_id={profile_id}&status=active&limit=20&cursor={cursor}
Authorization: Bearer <access_token>
```

| Query | 必填 | 规则 |
|---|:---:|---|
| `profile_id` | 否 | 只返回绑定该档案的会话 |
| `status` | 否 | `active` 或 `archived` |
| `limit` | 否 | `1`～`100`，默认 `20` |
| `cursor` | 否 | 上一页的 `next_cursor`，必须原样回传，不要解析或修改 |

会话按 `last_message_at` 从新到旧排序。

```json
{
  "items": [
    {
      "id": "会话 ID",
      "profile_id": "档案 ID",
      "title": "未来三年事业分析",
      "status": "active",
      "message_count": 4,
      "last_message_at": "2026-08-28T08:05:00Z",
      "created_at": "2026-08-28T08:00:00Z",
      "updated_at": "2026-08-28T08:05:00Z"
    }
  ],
  "next_cursor": null
}
```

`next_cursor` 非空时表示还有下一页。

### 4.3 查询会话详情

```http
GET /api/v1/ai-conversations/{conversation_id}
Authorization: Bearer <access_token>
```

响应结构与创建会话相同。

### 4.4 修改标题、归档或恢复会话

```http
PATCH /api/v1/ai-conversations/{conversation_id}
Content-Type: application/json
Authorization: Bearer <access_token>
```

请求体至少提供一个字段：

```json
{
  "title": "事业发展分析",
  "status": "archived"
}
```

| 字段 | 必填 | 规则 |
|---|:---:|---|
| `title` | 否 | 去除首尾空白后长度 `1`～`100` |
| `status` | 否 | `active` 或 `archived` |

归档后不能发送新问题；传 `{"status":"active"}` 可恢复。正在生成回答的会话不能归档。

### 4.5 删除会话

```http
DELETE /api/v1/ai-conversations/{conversation_id}
Authorization: Bearer <access_token>
```

成功返回 `204 No Content`，无 JSON 响应体。当前是软删除：删除后不再出现在列表，也不能继续查询详情或消息。正在生成回答的会话不能删除。

### 4.6 查询消息列表

第一次加载最新消息：

```http
GET /api/v1/ai-conversations/{conversation_id}/messages?limit=30
Authorization: Bearer <access_token>
```

加载更早消息：

```http
GET /api/v1/ai-conversations/{conversation_id}/messages?limit=30&before_sequence={next_before_sequence}
```

| Query | 必填 | 规则 |
|---|:---:|---|
| `limit` | 否 | `1`～`100`，默认 `30` |
| `before_sequence` | 否 | 大于等于 1；只查询序号小于该值的消息 |

接口每次返回最新一页或指定位置之前的一页，但 `items` 内始终按 `sequence_no` 从小到大排列，前端可直接按数组顺序渲染。

```json
{
  "items": [
    {
      "id": "用户消息 ID",
      "conversation_id": "会话 ID",
      "sequence_no": 1,
      "role": "user",
      "content": "未来三年的事业重点是什么？",
      "status": "completed",
      "structured_content": null,
      "created_at": "2026-08-28T08:01:00Z"
    },
    {
      "id": "助手消息 ID",
      "conversation_id": "会话 ID",
      "sequence_no": 2,
      "role": "assistant",
      "content": "回答正文",
      "status": "completed",
      "structured_content": {
        "source": "local_rules",
        "provider": null
      },
      "created_at": "2026-08-28T08:01:10Z"
    }
  ],
  "next_before_sequence": null
}
```

`next_before_sequence` 非空时表示还有更早的消息，应把它作为下一次请求的 `before_sequence`。

### 4.7 发送问题

```http
POST /api/v1/ai-conversations/{conversation_id}/messages
Content-Type: application/json
Authorization: Bearer <access_token>
```

```json
{
  "question": "未来三年的事业重点是什么？",
  "idempotency_key": "chat-20260828-f47ac10b"
}
```

| 字段 | 必填 | 规则 |
|---|:---:|---|
| `question` | 是 | 去除首尾空白后长度 `1`～`1000` |
| `idempotency_key` | 是 | 长度 `8`～`128`；只能包含字母、数字、`.`、`_`、`:`、`-` |

请求体禁止携带 `history` 或其他未声明字段，否则返回 `422`。

响应 `200`：

```json
{
  "conversation_id": "会话 ID",
  "user_message_id": "用户消息 ID",
  "assistant_message_id": "助手消息 ID",
  "profile_id": "档案 ID",
  "chart_fingerprint": "命盘指纹",
  "mode": "local",
  "answer": "回答正文",
  "structured_answer": {
    "source": "local_rules",
    "provider": null,
    "sections": {},
    "chart_evidence": ["命盘事实依据"],
    "rule_evidence": ["本地规则依据"],
    "timing_conditions": [],
    "practical_advice": ["现实建议"],
    "uncertainty": ["仅供传统文化参考"],
    "interpretation_receipt": "问题解释回执",
    "retryable": false,
    "violation_codes": []
  },
  "degradation_reason": "service_unavailable",
  "boundary_note": "命理分析仅供传统文化参考，不替代医疗、法律、投资或其他现实专业决策。",
  "idempotent_replay": false
}
```

`mode=local` 表示本地规则回答；`mode=cloud` 表示云模型结果已通过后端事实校验。`degradation_reason` 非空不等于请求失败，前端仍应正常展示 `answer`。

## 5. 幂等、并发与重试规则

前端发送每个新问题时应生成一个新幂等键，例如 UUID，去掉不符合规则的字符后加业务前缀：

```ts
const idempotencyKey = `chat-${crypto.randomUUID()}`;
```

处理规则：

| 场景 | 后端行为 | 前端处理 |
|---|---|---|
| 同一问题、同一幂等键重试 | 返回第一次的结果，`idempotent_replay=true` | 按成功结果展示，不要追加重复气泡 |
| 不同问题复用同一幂等键 | `409` | 这是前端键管理错误；为新问题生成新键 |
| 上一次同键请求已失败 | `409` | 使用新幂等键重试 |
| 同一会话已有问题生成中 | `409` | 禁用该会话发送按钮，等待当前请求结束 |
| 不同会话同时提问 | 允许，但仍受账号级限流和服务端并发限制 | 可分别展示 loading |

发送接口当前是同步响应，不是 SSE/WebSocket 流式接口。请求期间应展示 loading，并避免对同一会话并发提交；不要通过轮询伪造流式输出。

## 6. 错误处理

业务错误响应格式：

```json
{
  "detail": "AI conversation is not active"
}
```

参数校验错误的 `detail` 是 FastAPI 数组，前端错误解析需兼容字符串和数组两种形式。

| 状态码 | `detail`/场景 | 前端建议 |
|---:|---|---|
| `401` | token 缺失、过期或用户已停用 | 尝试刷新 token；失败后退出登录 |
| `404` | `AI conversation not found` | 从列表移除会话并返回会话列表 |
| `404` | 档案不存在、不属于当前用户或没有命盘 | 提示用户重新选择命理档案 |
| `409` | `AI conversation is not active` | 禁用输入框；允许用户恢复会话 |
| `409` | `Another question is already being processed for this conversation` | 保持当前 loading，暂不重复发送 |
| `409` | `Idempotency key was reused for a different question` | 为新问题生成新键；记录前端异常 |
| `409` | `The previous request with this idempotency key failed; retry with a new key` | 使用新键重新发送 |
| `422` | `Invalid AI conversation cursor` | 清空游标并从第一页重载 |
| `422` | `The question could not be analyzed safely` | 展示失败状态，允许使用新键重试 |
| `422` | 请求字段、长度或枚举不合法 | 显示表单提示，不自动重试 |

归档、删除和发送问题都可能遇到“会话正在处理”的 `409`。

## 7. 推荐前端调用流程

```text
进入 AI 问答页
  ├─ GET /ai-conversations?profile_id=...
  ├─ 有会话：选择最近一条
  └─ 无会话：POST /ai-conversations
          ↓
GET /ai-conversations/{id}/messages
          ↓
用户发送问题
  ├─ 生成并保存本次 idempotency_key
  ├─ POST /ai-conversations/{id}/messages
  ├─ 成功：按 message ID 去重后更新消息区
  └─ 网络失败：用相同 key、相同 question 重试
          ↓
向上滚动加载历史
  └─ 使用 next_before_sequence 请求更早消息
```

建议前端状态设计：

- 会话列表缓存键包含 `profile_id` 和 `status`；
- 消息以 `message.id` 去重，以 `sequence_no` 排序；
- 网络失败重试时保留原 `idempotency_key` 和原问题；
- 用户编辑问题后重新发送时必须生成新键；
- 删除成功按 `204` 处理，不要尝试解析 JSON；
- 归档会话禁用输入框，并提供“恢复会话”操作；
- `degradation_reason` 非空时仍展示回答，可按产品需要增加“本地模式”标识。

## 8. 联调验收清单

- [ ] 旧 `/chart-profiles/{profile_id}/questions` 已从前端移除；
- [ ] 新建会话能正确处理 `201`；
- [ ] 省略标题后，第一次提问会自动更新会话标题；
- [ ] 会话列表支持 `profile_id`、`status` 筛选和游标分页；
- [ ] 消息列表首次加载最新一页，向上滚动能加载更早消息；
- [ ] `items` 按 `sequence_no` 渲染，不按返回时间自行重新排序；
- [ ] 每个新问题生成唯一 `idempotency_key`；
- [ ] 网络重试复用同一键和同一问题，不产生重复气泡；
- [ ] 同一会话生成回答期间发送按钮不可重复点击；
- [ ] `idempotent_replay=true` 时按消息 ID 覆盖/去重；
- [ ] 归档后不能提问，恢复为 `active` 后可以继续；
- [ ] 删除接口正确处理空响应体 `204`；
- [ ] `detail` 同时兼容字符串和参数校验数组；
- [ ] `mode=local` 或 `degradation_reason` 非空时仍正常展示回答；
- [ ] 不再向后端发送 `history`、`role` 或前端拼接的助手消息。

## 9. 后端联调前置条件

后端部署本次版本前必须执行数据库迁移：

```bash
uv run alembic upgrade head
```

迁移会新增 `ai_conversations`、`ai_messages`、`ai_answer_runs` 三张表。未迁移数据库时，新接口会因数据表缺失而不可用。

完整后端 API 文档仍以 [API.md](API.md#16-ai-命理问答接口) 为准；本文仅覆盖本次合并的接口差异和前端迁移事项。
