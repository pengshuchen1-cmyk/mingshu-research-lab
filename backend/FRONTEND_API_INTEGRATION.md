# Mingshu 后端本次改动前端联调文档

> 2026-08-28 AI 会话式问答的最新破坏性变更，请优先查看 [前端接口变更与联调说明（2026-08-28）](FRONTEND_API_CHANGES_2026-08-28.md)。本文其余内容主要记录 2026-08-25 的命盘分析、报告、合婚、紫微等历史联调合同。

> 文档日期：2026-08-25
>
> API 基础路径：`/api/v1`
>
> 本地联调地址：`http://127.0.0.1:8000`
> 在线接口定义：`http://127.0.0.1:8000/docs`、`http://127.0.0.1:8000/openapi.json`

本文只描述本次合并新增或行为发生变化的接口。原有用户、点数、支付、命理档案、今日指引和年度运势接口继续保持原合同，完整接口可参考 [API.md](API.md)。

## 1. 本次接口改动概览

### 1.1 新增接口

| 功能 | 方法 | 路径 | 登录 |
|---|---|---|:---:|
| 命盘综合分析 | `GET` | `/api/v1/chart-profiles/{profile_id}/analysis` | 是 |
| 完整大运与未来十年 | `GET` | `/api/v1/chart-profiles/{profile_id}/luck-cycles` | 是 |
| 六十甲子知识查询 | `GET` | `/api/v1/knowledge/sixty-jiazi` | 否 |
| 命盘四柱甲子卡片 | `GET` | `/api/v1/chart-profiles/{profile_id}/sixty-jiazi` | 是 |
| 结构化专项报告 | `GET` | `/api/v1/chart-profiles/{profile_id}/reports/{report_type}` | 是 |
| 命盘报告下载 | `GET` | `/api/v1/chart-profiles/{profile_id}/reports/{report_type}/export` | 是 |
| 合婚分析 | `POST` | `/api/v1/compatibility/analyze` | 是 |
| 合婚报告下载 | `POST` | `/api/v1/compatibility/export` | 是 |
| 紫微命盘与解读 | `GET` | `/api/v1/chart-profiles/{profile_id}/ziwei` | 是 |
| 紫微报告下载 | `GET` | `/api/v1/chart-profiles/{profile_id}/ziwei/export` | 是 |
| AI 命理问答 | `POST` | `/api/v1/chart-profiles/{profile_id}/questions` | 是 |

### 1.2 行为变化接口

| 方法 | 路径 | 变化 |
|---|---|---|
| `POST` | `/api/v1/auth/otp/login/code` | 停用用户不能再获取登录验证码，返回 `401`。 |
| `POST` | `/api/v1/auth/otp/login` | 用户在验证码签发后被停用时也不能登录，返回 `401`。 |
| `POST` | `/api/v1/auth/password/reset/otp` | 停用用户不能获取密码重置验证码，返回 `401`。 |
| `POST` | `/api/v1/auth/password/reset` | 用户在验证码签发后被停用时不能重置密码，返回 `401`。 |
| `PATCH` | `/api/v1/admin/users/{user_id}/active` | 每次真实启用/停用都会撤销该用户此前签发的全部 access token 和 refresh token。重新启用后必须重新登录。 |

以下原有行为继续保留：

- `POST /api/v1/auth/password/register` 仍支持不经过短信验证码的手机号密码直接注册。
- 停用用户不能使用密码登录、刷新 token 或访问受保护接口。
- 密码设置、修改或重置成功后，旧 token 全部失效。

## 2. 通用联调约定

### 2.1 鉴权

除六十甲子知识查询外，本次新增接口都需要 access token：

```http
Authorization: Bearer <access_token>
```

前端建议统一处理：

1. `401`：尝试使用 refresh token 调用 `POST /api/v1/auth/refresh`。
2. refresh 仍返回 `401`：清空本地 access/refresh token，跳转登录页。
3. 用户经历停用再启用后，旧 refresh token 也不能继续使用，必须重新登录。

### 2.2 前置数据

大多数新接口接收 `profile_id`，该 ID 必须满足：

- 来自当前登录用户自己的命理档案；
- 档案已经经过预览和确认；
- 档案已有成功生成并保存的八字命盘快照。

典型前端流程：

```text
登录/注册
  → POST /chart-profiles/preview
  → POST /chart-profiles 确认保存
  → 获得 profile.id
  → 调用本次新增的分析、报告、紫微或 AI 接口
```

若 `profile_id` 不属于当前用户，后端统一返回 `404`，不会向前端暴露该 ID 是否属于其他用户。

### 2.3 通用业务错误

业务错误保持 FastAPI 现有格式：

```json
{
  "detail": "Chart interpretation could not be generated"
}
```

常见状态码：

| 状态码 | 前端含义 | 建议处理 |
|---:|---|---|
| `400` | OTP 错误、过期或缺少当前密码 | 表单字段提示 |
| `401` | 未登录、token 失效、用户停用 | 刷新 token 或退出登录 |
| `403` | 非管理员调用管理接口 | 展示无权限页 |
| `404` | 档案、命盘或知识项不存在 | 返回列表页或提示重新选择 |
| `409` | 重复注册、业务状态冲突 | 保留用户输入并提示具体冲突 |
| `422` | 参数校验失败或分析/导出不可用 | 展示 `detail`，不要自动重试 |
| `429` | OTP、密码或 AI 请求频率受限 | 禁用提交按钮并提示稍后重试 |
| `503` | 短信、数据库或 Redis 未就绪 | 展示服务暂不可用 |

Pydantic 参数校验错误仍使用 FastAPI 的 `detail: array` 格式，因此前端错误解析应兼容 `detail` 为字符串或数组。

### 2.4 CORS

当前后端允许以下三个来源并允许 credentials：

- `https://mingshu.cloud`
- `https://www.mingshu.cloud`
- `http://localhost:5173`

本地前端应使用 `http://localhost:5173`。如果开发服务器运行在 `3000` 等其他端口，浏览器请求会被 CORS 拦截。

### 2.5 缓存和刷新建议

所有命盘相关响应均返回 `chart_fingerprint`。建议前端以：

```text
profile_id + chart_fingerprint + endpoint + endpoint parameters
```

作为查询缓存键。档案重新生成命盘后指纹会变化，旧分析结果应立即失效。

## 3. 命盘综合分析

### `GET /api/v1/chart-profiles/{profile_id}/analysis`

功能：一次返回八字类型、基础白话报告、人生总览、五行深度分析和喜用五行。适合命盘总览页首次加载。

#### 入参

| 位置 | 字段 | 类型 | 必填 | 说明 |
|---|---|---|:---:|---|
| Path | `profile_id` | `string` | 是 | 当前用户已确认并保存的档案 ID |
| Header | `Authorization` | `string` | 是 | `Bearer <access_token>` |

无 Query 和 Body 参数。

#### 出参 `200 application/json`

```ts
interface ChartInterpretationResponse {
  profile_id: string;
  chart_fingerprint: string;
  chart_type: {
    basic_pattern: string;
    element_pattern: string;
    ten_god_pattern: string;
    special_combinations: unknown[];
    summary: string;
    [key: string]: unknown;
  };
  basic_report: {
    life_overview: string;
    personality_text: string;
    career_text: string;
    wealth_text: string;
    love_text: string;
    risk_text: string;
    advice: string;
    [key: string]: unknown;
  };
  life_assessment: {
    opening: string;
    wealth: Record<string, unknown>;
    romance: Record<string, unknown>;
    health: Record<string, unknown>;
    [key: string]: unknown;
  };
  life_overview: {
    overall_pattern: string;
    overall_summary: string;
    life_keywords: string[];
    wealth_overview: Record<string, unknown>;
    romance_overview: Record<string, unknown>;
    health_overview: Record<string, unknown>;
    career_overview: Record<string, unknown>;
    scores: Record<string, number>;
    score_details: Record<string, unknown>;
    key_strengths: string[];
    key_risks: string[];
    long_term_advice: string[];
    evidence: string[];
    source_ids: string[];
    source_titles: string[];
    [key: string]: unknown;
  };
  five_elements: {
    element_overview: string;
    element_balance_summary: string;
    strong_elements: string[];
    weak_elements: string[];
    favorable_elements: string[];
    unfavorable_elements: string[];
    element_details: Record<string, unknown>;
    career_implications: string;
    wealth_implications: string;
    relationship_implications: string;
    health_implications: string;
    adjustment_advice: string[];
    evidence: string[];
    source_ids: string[];
    source_titles: string[];
    [key: string]: unknown;
  };
  useful_god: {
    favorable_elements: string[];
    summary: string;
    details: unknown[];
    [key: string]: unknown;
  };
}
```

前端展示建议：

- 首屏优先展示 `life_overview.overall_summary`、`life_keywords` 和 `scores`；
- 五行页使用 `five_elements`，不要在前端重新计算五行强弱；
- “分析依据”抽屉展示 `evidence` 和 `source_titles`；
- `scores` 是开放键值结构，前端应容忍后端增加新维度。

#### 错误

- `401`：未登录或 token 失效；
- `404`：档案不属于当前用户或命盘不存在；
- `422 {"detail":"Chart interpretation could not be generated"}`：当前命盘无法完成分析。

## 4. 完整大运与未来十年

### `GET /api/v1/chart-profiles/{profile_id}/luck-cycles`

功能：返回起运方向与依据、最多十步完整大运，以及从服务器当前年份开始的未来十年流年摘要。

#### 入参

只有 Path `profile_id` 和 Bearer token，无 Query、Body。

#### 出参 `200 application/json`

```ts
interface LuckCyclesResponse {
  profile_id: string;
  chart_fingerprint: string;
  available: true;
  direction: "forward" | "reverse" | null;
  direction_label: string | null;
  start_age: number | null;
  start_year: number | null;
  start_month: number | null;
  start_day: number | null;
  start_text: string;
  dayun_basis: {
    boundary_name?: string;
    boundary_datetime?: string;
    interval_seconds?: number;
    start_datetime?: string;
    time_is_estimated?: boolean;
    rule_ids?: string[];
    [key: string]: unknown;
  };
  dayun_list: Array<{
    index: number;
    pillar: string;
    gan: string;
    zhi: string;
    start_age: number;
    end_age: number;
    start_year: number;
    end_year: number;
    start_date: string;
    end_date: string;
    gan_element: string;
    zhi_element: string;
    ten_god: string;
    stage_score: number;
    stage_level: string;
    stage_text: string;
    stage_summary: string;
    career_focus: string;
    wealth_focus: string;
    relationship_focus: string;
    risk_focus: string;
    action_advice: string;
    [key: string]: unknown;
  }>;
  yearly_list: Array<{
    year: number;
    pillar: string;
    overall_text: string;
    advice_text: string;
    [key: string]: unknown;
  }>;
  data_warnings: string[];
}
```

前端展示建议：

- `dayun_list` 按 `index` 正序显示时间轴；
- 不要用年龄自行推导年份，直接使用后端 `start_year/end_year`；
- `time_is_estimated=true` 时应展示“时间为估算值”；
- `data_warnings` 非空时在结果页展示非阻断提示。

错误：`401`、`404`，或 `422 Luck cycles could not be generated from this profile`。

## 5. 六十甲子

### 5.1 `GET /api/v1/knowledge/sixty-jiazi`

功能：公共知识库查询。可以按公历年份换算、按干支查询，或分页获取完整六十甲子列表。

#### Query 入参

| 字段 | 类型 | 必填 | 默认 | 规则 |
|---|---|:---:|---:|---|
| `year` | `integer` | 否 | - | `1900`～`2100` |
| `pillar` | `string` | 否 | - | 正好两个字符，例如 `甲子` |
| `offset` | `integer` | 否 | `0` | `>= 0` |
| `limit` | `integer` | 否 | `60` | `1`～`60` |

`year` 和 `pillar` 不能同时传。都不传时返回分页列表。

#### 出参

```ts
interface SixtyJiaziListResponse {
  total: number;
  offset: number;
  limit: number;
  items: Array<{
    index: number;
    pillar: string;
    gan: string;
    zhi: string;
    gan_element: string;
    zhi_element: string;
    nayin: string;
    nayin_element?: string;
    sample_years?: number[];
    plain_explanation?: string;
    symbolic_keywords?: string[];
    reality_mapping?: string;
    user_advice?: string;
    lichun_boundary_note?: string;
    [key: string]: unknown;
  }>;
}
```

示例：

```http
GET /api/v1/knowledge/sixty-jiazi?year=1984
GET /api/v1/knowledge/sixty-jiazi?pillar=甲子
GET /api/v1/knowledge/sixty-jiazi?offset=0&limit=20
```

错误：同时传 `year` 和 `pillar` 返回 `422`；干支不存在返回 `404 Sixty Jiazi entry not found`。

### 5.2 `GET /api/v1/chart-profiles/{profile_id}/sixty-jiazi`

功能：将当前命盘的年、月、日、时四柱转换为甲子知识卡片，并对照原局五行。

#### 入参

Path `profile_id`，需要 Bearer token。

#### 出参

```ts
interface ChartSixtyJiaziResponse {
  profile_id: string;
  chart_fingerprint: string;
  pillar_cards: Array<{
    position: "year" | "month" | "day" | "hour" | string;
    label: string;
    pillar: string;
    nayin: string;
    user_explanation: string;
    reality_hint: string;
    advice: string;
    keywords: string[];
    boundary_note: string;
    [key: string]: unknown;
  }>;
  nayin_comparison: {
    nayin_distribution: Record<string, number>;
    chart_distribution: Record<string, number>;
    dominant_nayin_elements: string[];
    dominant_chart_elements: string[];
    explanation: string;
    [key: string]: unknown;
  };
}
```

出生时辰未知时，不要假定 `pillar_cards` 一定有四项，应按实际数组渲染。

## 6. 专项报告与命盘报告下载

### 6.1 `GET /api/v1/chart-profiles/{profile_id}/reports/{report_type}`

功能：生成事业、财富或感情专项结构化报告，适合直接渲染为页面卡片。

#### Path 入参

| 字段 | 类型 | 允许值 |
|---|---|---|
| `profile_id` | `string` | 当前用户档案 ID |
| `report_type` | `string` | `career`、`wealth`、`love` |

#### 出参

```ts
interface SpecialReportResponse {
  profile_id: string;
  chart_fingerprint: string;
  report_type: "career" | "wealth" | "love";
  report: {
    title: string;
    evidence: string[];
    chart_signature: string;
    sections: Array<{ title: string; text: string; [key: string]: unknown }>;
    advice: string;
    disclaimer: string;
    [key: string]: unknown;
  };
}
```

不同报告的扩展字段：

| 类型 | 主要扩展字段 |
|---|---|
| `career` | `career_identity`、`career_portrait`、`suitable_work_modes`、`suitable_industries`、`career_risks`、`action_plan` |
| `wealth` | `wealth_identity`、`financial_structure`、`main_income_modes`、`secondary_income_modes`、`money_risks`、`cashflow_advice` |
| `love` | `relationship_pattern`、`relationship_structure`、`suitable_partner_type`、`relationship_strengths`、`relationship_risks`、`communication_advice` |

前端应优先以通用 `sections` 渲染正文，扩展字段用于专属卡片，不要硬编码报告只能包含当前字段。

### 6.2 `GET /api/v1/chart-profiles/{profile_id}/reports/{report_type}/export`

功能：下载综合命盘或专项报告。响应是文件流，不是 JSON。

#### 入参

| 位置 | 字段 | 类型 | 必填 | 允许值/默认值 |
|---|---|---|:---:|---|
| Path | `profile_id` | `string` | 是 | 当前用户档案 ID |
| Path | `report_type` | `string` | 是 | `comprehensive`、`career`、`wealth`、`love` |
| Query | `format` | `string` | 否 | `markdown`、`txt`、`pdf`；默认 `markdown` |

#### 出参

| format | Content-Type | 文件扩展名 |
|---|---|---|
| `markdown` | `text/markdown; charset=utf-8` | `.md` |
| `txt` | `text/plain; charset=utf-8` | `.txt` |
| `pdf` | `application/pdf` | `.pdf` |

浏览器下载示例：

```ts
const response = await fetch(url, {
  headers: { Authorization: `Bearer ${accessToken}` },
});
if (!response.ok) throw await response.json();
const blob = await response.blob();
const disposition = response.headers.get("Content-Disposition");
// 从 disposition 读取文件名，或使用前端自定义文件名。
```

PDF 环境不可用时返回 `422 {"detail":"Report could not be exported"}`，不会返回伪 PDF 文本。

## 7. 合婚匹配

### 7.1 `POST /api/v1/compatibility/analyze`

功能：比较当前用户自己的两个不同档案，返回总分、维度评分、互补点、冲突点和相处建议。

#### Body 入参

```ts
interface CompatibilityRequest {
  profile_id_1: string;
  profile_id_2: string;
}
```

```json
{
  "profile_id_1": "第一个档案 ID",
  "profile_id_2": "第二个档案 ID"
}
```

两个 ID 必须不同且都属于当前用户，否则返回 `422` 或 `404`。

#### 出参

```ts
interface CompatibilityResponse {
  profile_id_1: string;
  profile_id_2: string;
  chart_fingerprint_1: string;
  chart_fingerprint_2: string;
  result: {
    overall_score: number;
    level: string;
    summary: string;
    dimensions: Array<{
      label: string;
      score: number;
      max_score: number;
      text: string;
      detail: string;
      [key: string]: unknown;
    }>;
    key_cautions: string[];
    person_a: Record<string, unknown>;
    person_b: Record<string, unknown>;
    match_reasons: string[];
    conflict_reasons: string[];
    advice_list: string[];
    basis: string;
    source_titles: string[];
    [key: string]: unknown;
  };
}
```

错误：`401`、`404`、`422 Compatibility analysis could not be generated`。

### 7.2 `POST /api/v1/compatibility/export?format={format}`

功能：下载合婚报告。

- Body 与 `/compatibility/analyze` 完全相同；
- `format` 为 `markdown | txt | pdf`，默认 `markdown`；
- 响应为对应文件流；
- 文件名来自 `Content-Disposition: attachment; filename="mingshu-compatibility.<ext>"`。

## 8. 紫微斗数

### 8.1 `GET /api/v1/chart-profiles/{profile_id}/ziwei`

功能：根据已确认档案生成紫微十二宫、主星、辅星、煞星、四化、大限、命盘名片和白话综合报告。

#### 入参

Path `profile_id`，需要 Bearer token。

#### 出参

```ts
interface ZiweiResponse {
  profile_id: string;
  chart_fingerprint: string;
  chart: {
    available: true;
    lunar_month: number;
    lunar_day: number;
    hour_branch: string;
    year_gan: string;
    year_branch: string;
    life_palace: string;
    body_palace: string;
    palaces: Array<Record<string, unknown>>;
    main_stars_ready: boolean;
    main_stars_by_palace: Record<string, unknown>;
    minor_stars_ready: boolean;
    minor_stars_by_palace: Record<string, unknown>;
    fierce_stars_ready: boolean;
    fierce_stars_by_palace: Record<string, unknown>;
    daxian: Record<string, unknown>;
    [key: string]: unknown;
  };
  life_card: {
    title: string;
    ziwei_profile_type: string;
    profile_keywords: string[];
    ming_gong_summary: string;
    shen_gong_summary: string;
    key_palace_summaries: Record<string, unknown>;
    personalized_evidence: string[];
    source_titles: string[];
    [key: string]: unknown;
  };
  report: {
    title: string;
    sections: Array<Record<string, unknown>>;
    advice: string;
    disclaimer: string;
    main_stars_ready: boolean;
    minor_stars_ready: boolean;
    fierce_stars_ready: boolean;
    daxian_ready: boolean;
    [key: string]: unknown;
  };
}
```

前端注意：

- 正常情况下 `palaces` 为十二宫，但应按数组实际长度渲染；
- 根据各类 `*_ready` 控制模块可见性，不要把算法尚未完成误显示为“无星”；
- 算法失败返回 `422 Ziwei analysis could not be generated from this profile`。

### 8.2 `GET /api/v1/chart-profiles/{profile_id}/ziwei/export`

Query `format=markdown|txt|pdf`，默认 `markdown`。响应为文件流，处理方式与命盘报告下载相同。

## 9. AI 命理问答

### `POST /api/v1/chart-profiles/{profile_id}/questions`

功能：基于已保存命盘回答四柱命理范围内的问题。默认使用本地规则；配置云模型时，后端只发送去标识化命盘事实，并对云回答进行事实和安全校验。

#### 入参

Path `profile_id`，Bearer token，JSON Body：

```ts
interface AIQuestionRequest {
  question: string; // 1～1000 字符
  history?: Array<{
    role: "user" | "assistant";
    content: string; // 1～4000 字符
  }>; // 最多 10 条，默认 []
}
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

前端只应发送当前问题所需的短历史，不要放入姓名、联系方式、证件、地址、API Key 或系统提示词。

#### 出参

```ts
interface AIQuestionResponse {
  profile_id: string;
  chart_fingerprint: string;
  mode: "local" | "cloud";
  answer: string;
  structured_answer: {
    source: "local_rules" | "cloud_validated" | "boundary" | "clarification" | string;
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
  };
  degradation_reason: string | null;
  boundary_note: string;
}
```

关键语义：

- `200 + mode=local` 是正常成功或安全降级，不应显示成接口失败；
- `mode=cloud` 仅表示云输出已经通过本地校验；
- `source=boundary` 表示问题超出允许范围，应直接展示后端边界回答；
- `source=clarification` 表示需要用户补充问题；
- `degradation_reason` 非空时可显示“已切换至本地分析”，但不要暴露内部异常；
- `retryable=true` 时前端才适合提供“重试云分析”按钮；
- `boundary_note` 应固定展示在回答区域底部。

输入或安全分析完全失败时返回 `422 The question could not be analyzed safely`。请求频率限制触发时可能返回 `429`。

## 10. 认证和停用用户联调

### 10.1 密码直接注册（保留）

```http
POST /api/v1/auth/password/register
Content-Type: application/json
```

```ts
interface PasswordRegisterRequest {
  phone: string;
  password: string; // 8～128 字符
}

interface TokenPairResponse {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  new_user: boolean;
}
```

成功返回 `201`，`new_user=true`。手机号会规范化为 E.164。已有手机号返回 `409 Account already registered`。

该方式不验证手机号归属，前端不能显示“手机号已验证”。

### 10.2 停用和重新启用

管理员调用：

```http
PATCH /api/v1/admin/users/{user_id}/active
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{"is_active": false}
```

出参：

```json
{
  "id": "用户 ID",
  "is_active": false
}
```

状态变化后的前端处理：

1. 被停用用户的所有旧 access/refresh token 立即失效；
2. 登录、OTP 获取/验证、密码重置和受保护接口均返回 `401`；
3. 管理员重新启用用户后，旧 token 仍然无效；
4. 用户必须重新调用密码登录或 OTP 登录获得新 token；
5. 重复提交相同状态不会再次递增认证版本，但前端仍可按成功响应更新列表。

## 11. 推荐联调顺序

1. 使用 `POST /auth/password/register` 创建测试用户并保存 token；
2. 创建并确认两个测试档案，保存两个 `profile_id`；
3. 联调 `/analysis`、`/luck-cycles`、命盘 `/sixty-jiazi`；
4. 联调三种专项报告和三种导出格式；
5. 使用两个不同档案联调合婚分析和导出；
6. 联调紫微详情和导出；
7. 在默认 `AI_PROVIDER=local` 下联调 AI 问答及历史消息；
8. 最后由管理员停用/启用测试用户，验证前端清理旧 token 和重新登录流程。

## 12. 前端验收清单

- [ ] 所有受保护接口均发送 Bearer access token；
- [ ] `401` 时不会无限循环刷新 token；
- [ ] `detail` 同时兼容字符串和校验错误数组；
- [ ] 非本人档案的 `404` 不展示资源归属信息；
- [ ] 下载接口使用 Blob，不调用 `response.json()`；
- [ ] 根据 `Content-Type` 和 `Content-Disposition` 处理下载；
- [ ] 使用 `chart_fingerprint` 使旧命盘分析缓存失效；
- [ ] 开放结构字段新增时不会导致页面崩溃；
- [ ] 时辰未知时不假定四柱卡片固定四项；
- [ ] 紫微各模块根据 `*_ready` 状态显示；
- [ ] AI 的 `mode=local` 被视为成功响应；
- [ ] AI 边界说明固定展示；
- [ ] 用户重新启用后强制重新登录，不复用旧 token；
- [ ] 本地前端运行在允许的 `http://localhost:5173` 来源。
