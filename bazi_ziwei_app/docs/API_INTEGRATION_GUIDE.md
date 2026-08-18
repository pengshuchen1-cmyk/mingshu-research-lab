# 命数研究室 - 前端 API 联调文档

> API 版本: **1.0.0**  
> 基础 URL: `http://127.0.0.1:8000` (本地开发)  
> 协议: HTTP/1.1, JSON  
> 字符编码: UTF-8  
> 最后更新: 2026-08-18

---

## 目录

1. [概述](#1-概述)
2. [通用约定](#2-通用约定)
3. [会话机制](#3-会话机制)
4. [接口列表](#4-接口列表)
   - [4.1 健康检查 GET /healthz](#41-健康检查)
   - [4.2 命盘预览 POST /api/v1/chart/preview](#42-命盘预览)
   - [4.3 确认命盘 POST /api/v1/chart/confirm](#43-确认命盘)
   - [4.4 获取命盘 GET /api/v1/chart/{chart_id}](#44-获取命盘)
5. [完整调用流程](#5-完整调用流程)
6. [错误码参考](#6-错误码参考)
7. [CORS 配置](#7-cors-配置)
8. [数据模型速查](#8-数据模型速查)
9. [前端示例代码](#9-前端示例代码)
10. [连通性测试结果](#10-连通性测试结果)

---

## 1. 概述

命数研究室后端 API 基于 **FastAPI** 构建，提供八字命盘的生成、预览、确认和查询功能。API 采用 **Session-Cookie** 机制进行会话管理，所有敏感数据（姓名、出生地等）不会在 API 响应中直接暴露。

### 运行模式

| 模式 | 说明 | 隐私同意要求 |
|------|------|------------|
| `local` | 本地开发模式 | 不强制 |
| `public` | 公网部署模式 | 必须提供 `privacy_consent: true` |

### 启动后端服务

```bash
cd bazi_ziwei_app
MINGSHU_RUNTIME_MODE=local .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

---

## 2. 通用约定

### 请求头

| Header | 值 | 说明 |
|--------|-----|------|
| `Content-Type` | `application/json` | 所有 POST 请求必须 |
| `Cookie` | `mingshu_session=...` | 浏览器自动携带 |

### 响应头

| Header | 说明 |
|--------|------|
| `X-Request-ID` | 32 位十六进制请求 ID，用于追踪 |
| `Cache-Control` | `no-store, private` (API 接口) |
| `Set-Cookie` | 会话 Cookie，httponly + samesite=lax |

### 数据格式

- 所有请求/响应均为 JSON
- 字段严格校验，不允许额外字段（`additionalProperties: false`）
- 字符串最长 120 字符（`ShortText`）
- 指纹字段为 64 位十六进制

### 错误响应格式

所有错误响应使用统一结构:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "人类可读的错误描述",
    "fields": ["受影响的字段名"]
  },
  "request_id": "32位十六进制请求ID"
}
```

---

## 3. 会话机制

### Cookie

| 属性 | 值 |
|------|-----|
| 名称 | `mingshu_session` |
| 格式 | `{session_id}.{hmac_signature}` |
| HttpOnly | `true` |
| SameSite | `lax` |
| Secure | `true` (public 模式) / `false` (local 模式) |
| 有效期 | 默认 1800 秒 (30 分钟)，可配置 |

### 会话生命周期

```
首次请求 POST /preview (无 Cookie)
  → 服务端创建 Session，Set-Cookie 返回
  → 后续请求自动携带 Cookie
  → 每个请求刷新 TTL
  → 超时后 Session 过期，需重新开始
```

### 重要约束

- 每个 Session 同时只能持有 **一个** 已确认的命盘
- 确认新命盘会使旧命盘失效（状态码 410 `CHART_INVALIDATED`）
- 命盘只能被创建它的 Session 读取（跨 Session 返回 403）

---

## 4. 接口列表

### 4.1 健康检查

```
GET /healthz
```

**无需认证，无需 Cookie**

#### 响应示例

```json
{
  "status": "ok",
  "version": "1.0.0",
  "runtime_mode": "local"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `status` | `"ok"` | 固定值 |
| `version` | `string` | API 版本号 |
| `runtime_mode` | `"local"` \| `"public"` | 当前运行模式 |

---

### 4.2 命盘预览

```
POST /api/v1/chart/preview
```

**功能**: 提交出生信息，生成命盘预览。不会创建持久化的命盘记录，仅返回预览信息。

#### 请求体 (BirthInputRequest)

```json
{
  "name": "张三",
  "gender": "男",
  "calendar": "solar",
  "year": 1994,
  "month": 9,
  "day": 23,
  "hour": null,
  "minute": null,
  "is_leap_month": false,
  "birth_place": "北京",
  "time_label": "时辰不详",
  "privacy_consent": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | `string` | ✅ | 姓名，最长 120 字符 |
| `gender` | `"男"` \| `"女"` \| `"male"` \| `"female"` | ✅ | 性别 |
| `calendar` | `"solar"` \| `"lunar"` | ✅ | 历法：公历/农历 |
| `year` | `int` | ✅ | 出生年 (1900-2100) |
| `month` | `int` | ✅ | 出生月 (1-12) |
| `day` | `int` | ✅ | 出生日 (1-31) |
| `hour` | `int` \| `null` | 条件 | 出生时 (0-23)，与 minute 必须同时提供或同时为 null |
| `minute` | `int` \| `null` | 条件 | 出生分 (0-59)，与 hour 必须同时提供或同时为 null |
| `is_leap_month` | `bool` | ❌ | 是否闰月，仅农历有效，默认 `false` |
| `birth_place` | `string` | ❌ | 出生地，最长 120 字符，默认 `""` |
| `time_label` | `string` | ❌ | 时间标签，最长 120 字符，默认 `"精确时间"` |
| `privacy_consent` | `bool` | ❌ | 隐私同意，public 模式必填 `true`，默认 `false` |

**校验规则**:
- `hour` 和 `minute` 必须同时提供或同时为 null
- 公历 (`solar`) 模式下 `is_leap_month` 必须为 `false`
- 不允许请求体中出现额外字段

#### 成功响应 (200) - PreviewResponse

```json
{
  "preview_id": "pwPW17D_DHEA0WR4f86cX8o8TYDKD583",
  "input_text": "公历1994年9月23日 时辰不详",
  "solar_datetime": "1994-09-23 00:00:00",
  "pillars": ["甲戌", "癸酉", "壬子", "时柱不详"],
  "calculation_basis": "年柱以立春为界",
  "input_fingerprint": "bdfdd4b0a2cdb945...",
  "chart_fingerprint": "bf8733a1af02bd55..."
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| `preview_id` | `string` | 预览 ID，用于后续确认 |
| `input_text` | `string` | 格式化的出生信息文本 |
| `solar_datetime` | `string` | 转换后的公历日期时间 |
| `pillars` | `[string×4]` | 四柱（年柱、月柱、日柱、时柱） |
| `calculation_basis` | `string` | 计算依据说明 |
| `input_fingerprint` | `string` | **实际是确认用的 token**，64 位十六进制，需原样传给 confirm 接口 |
| `chart_fingerprint` | `string` | 命盘指纹，64 位十六进制，需原样传给 confirm 接口 |

> ⚠️ **重要**: `input_fingerprint` 字段在预览响应中实际上是确认用的安全 token（不是输入的哈希），必须在 confirm 接口中原样回传。

#### 错误响应

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 403 | `PRIVACY_CONSENT_REQUIRED` | public 模式未同意隐私处理 |
| 410 | `SESSION_EXPIRED` | 会话已过期 |
| 422 | `VALIDATION_ERROR` | 请求参数校验失败 |
| 422 | `INVALID_BIRTH_INPUT` | 出生信息无法生成命盘 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |
| 503 | `SESSION_CAPACITY` | 服务繁忙，会话容量已满 |

---

### 4.3 确认命盘

```
POST /api/v1/chart/confirm
```

**功能**: 基于预览信息确认生成命盘，返回完整的命盘事实数据。此操作会将命盘持久化到当前会话中。

#### 请求体 (ConfirmChartRequest)

继承 `BirthInputRequest` 的所有字段，额外增加:

```json
{
  "name": "张三",
  "gender": "男",
  "calendar": "solar",
  "year": 1994,
  "month": 9,
  "day": 23,
  "hour": null,
  "minute": null,
  "is_leap_month": false,
  "birth_place": "北京",
  "time_label": "时辰不详",
  "privacy_consent": true,
  "preview_id": "pwPW17D_DHEA0WR4f86cX8o8TYDKD583",
  "input_fingerprint": "bdfdd4b0a2cdb945...",
  "chart_fingerprint": "bf8733a1af02bd55..."
}
```

| 新增字段 | 类型 | 必填 | 说明 |
|----------|------|------|------|
| `preview_id` | `string` | ✅ | 来自预览响应的 preview_id，长度 16-80 |
| `input_fingerprint` | `string` | ✅ | 来自预览响应的 input_fingerprint (token)，64 位十六进制 |
| `chart_fingerprint` | `string` | ✅ | 来自预览响应的 chart_fingerprint，64 位十六进制 |

> ⚠️ 出生信息必须与预览时完全一致，否则会返回 409 `FINGERPRINT_MISMATCH`

#### 成功响应 (200) - ConfirmChartResponse

以下为真实调用返回的完整 JSON（输入: 1994年9月23日 男 时辰不详）:

```json
{
  "chart_id": "ywL6akW-QbmlRcmgNEGZ2X1EXYV-qu_9",
  "chart_fingerprint": "bf8733a1af02bd556d75b9a573a2671812f3b08d853786e91a3388c1d4b47bfb",
  "chart_facts": {
    "gender": "男",
    "pillars": ["甲戌", "癸酉", "壬子", "时柱不详"],
    "day_master": "壬",
    "hidden_stems": {
      "戌": ["戊", "辛", "丁"],
      "酉": ["辛"],
      "子": ["癸"]
    },
    "ten_gods": {
      "year": {
        "gan": "食神",
        "hidden_stems": [
          {"gan": "戊", "ten_god": "七杀"},
          {"gan": "辛", "ten_god": "正印"},
          {"gan": "丁", "ten_god": "正财"}
        ]
      },
      "month": {
        "gan": "劫财",
        "hidden_stems": [
          {"gan": "辛", "ten_god": "正印"}
        ]
      },
      "day": {
        "gan": "日主",
        "hidden_stems": [
          {"gan": "癸", "ten_god": "劫财"}
        ]
      }
    },
    "element_counts": {
      "土": 1.0,
      "木": 1.0,
      "水": 3.0,
      "火": 0.3,
      "金": 3.5
    },
    "time_mode": "中国标准时间（北京时间）",
    "pillar_basis": "以立春1994-02-04 09:30:56换年，采用1994年干支；最近已过的节为白露（1994-09-08 04:55:07），按五虎遁取月柱；未到23:00，按当日1994-09-23取日柱；时辰不详，不推定时柱",
    "dayun": {
      "direction": "顺排",
      "start": "时辰不详，暂按12:00估算；顺排，取寒露（1994-10-08 20:29:05）折算，约5年1个月12天起运（约1999-11-05）。"
    },
    "strength": {
      "classification": "身强",
      "evidence": [
        "月令主气生日主，日主得到季节层面的助力。",
        "地支中有部分根气，但力量不算特别稳定。藏干见日主0次，同气主气1处，生扶主气1处。",
        "命局中生扶日主的力量相对明显。生扶约4.5，克约1.0，泄约1.0，耗约0.3。",
        "当前强弱结论以月令、通根和透藏生克为主，合冲作为复核项。",
        "时辰不详，时柱可能改变部分通根、透干和生克证据。"
      ],
      "favorable_elements": ["木", "火", "土"],
      "unfavorable_elements": ["金", "水"]
    },
    "pattern": {
      "classification": "格局初判为正印格，来源是月令主气。它的白话意思是：重学习、资质、保护、系统和贵人支持，适合借助平台、专业和证照成长。当前更适合把它当成命盘主线之一，后面还要结合大运、流年和现实选择来验证。",
      "evidence": [
        "月令酉以辛为主气，对日主为正印。",
        "以月令主气正印定为正印格。",
        "有利配合：杀印相生、能和日主强弱一起观察，不是孤立断格",
        "需要经营：财印相碍，现实收益与学习资质需平衡"
      ]
    },
    "wealth": {
      "summary": "赚钱路径：财星显示对客户、资源、项目回报和现实收入的敏感度，但不等同现实资产数额。；食伤较清楚时，更适合把技能、产品、内容或服务输出转为收入。。留财条件：承接项目规模要与自身资源、团队、时间和现金流能力匹配。；比劫越集中，越需要提前写清合伙投入、分账、回款和退出条件。。风险提醒：抵押、借贷或扩大规模前，应以现实现金流和可承受损失为准。",
      "evidence": [
        "财星显示对客户、资源、项目回报和现实收入的敏感度，但不等同现实资产数额。",
        "食伤较清楚时，更适合把技能、产品、内容或服务输出转为收入。",
        "承接项目规模要与自身资源、团队、时间和现金流能力匹配。",
        "比劫越集中，越需要提前写清合伙投入、分账、回款和退出条件。",
        "命盘不能保证高杠杆项目结果；应先验证最坏情景、还款来源和退出机制。"
      ]
    },
    "relationship": {
      "summary": "吸引阶段：桃花只代表被注意和互动机会，不等同关系已经建立。关系建立：配偶星需要与夫妻宫及运年触发共同观察，不能只凭数量判断婚期。稳定阶段：有合重在边界与承诺落实，有冲重在变化和沟通管理；两者都不直接等于婚姻结果。建议结合现实互动和大运流年分阶段验证。",
      "evidence": [
        "桃花只代表被注意和互动机会，不等同关系已经建立。",
        "配偶星需要与夫妻宫及运年触发共同观察，不能只凭数量判断婚期。",
        "有合重在边界与承诺落实，有冲重在变化和沟通管理；两者都不直接等于婚姻结果。"
      ],
      "stability_signals": [
        {
          "polarity": "mixed",
          "fact": "日支子；合为无；冲为无",
          "explanation": "有合重在边界与承诺落实，有冲重在变化和沟通管理；两者都不直接等于婚姻结果。"
        }
      ]
    },
    "internal_rule_version": "2.0.0",
    "rule_ids": [
      "CAL-YEAR-LICHUN",
      "CAL-MONTH-JIE",
      "CAL-DAY-ZI23",
      "PILLAR-MONTH-FIVETIGER",
      "PILLAR-HOUR-FIVERAT"
    ],
    "current_context": {
      "day_pillar": "甲子",
      "month_pillar": "丙申",
      "year": 2026,
      "year_pillar": "丙午"
    }
  }
}
```

---

#### 顶层字段

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `chart_id` | `string` | **命盘唯一 ID**。确认后生成，用于后续 GET 接口查询。长度约 32 字符 | `"ywL6akW-QbmlRcmgNEGZ2X1EXYV-qu_9"` |
| `chart_fingerprint` | `string` | **命盘指纹**。64 位十六进制 SHA-256 哈希，对 `chart_facts`（不含 `current_context`）做摘要。当前端需要判断命盘数据是否变化时，可对比此值 | `"bf8733a1af02bd55..."` |
| `chart_facts` | `object` | **命盘事实数据**。核心业务数据，包含所有八字分析结果。详见下方逐字段说明 | 见下方 |

---

#### `chart_facts` 逐字段详解

##### 1. 基本信息

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `gender` | `string` | **性别**。标准化为 `"male"` 或 `"female"` | `"male"` |
| `pillars` | `[string×4]` | **四柱干支**。数组依次为 [年柱, 月柱, 日柱, 时柱]。每个元素是干支组合（如 "甲戌"），未知时柱为 `"时柱不详"` | `["甲戌", "癸酉", "壬子", "时柱不详"]` |
| `day_master` | `string` | **日主天干**。日柱的天干部分，代表命主自身，是八字分析的核心参照点 | `"壬"` |
| `hidden_stems` | `dict` | **地支藏干**。key 为地支名（来自四柱地支），value 为该地支中隐藏的天干数组。例如 "戌" 中藏有戊、辛、丁三个天干 | `{"戌": ["戊","辛","丁"], "酉": ["辛"], "子": ["癸"]}` |
| `time_mode` | `string` | **时间模式说明**。描述时区处理方式 | `"中国标准时间（北京时间）"` |
| `pillar_basis` | `string` | **排柱计算依据**。详细说明年柱、月柱、日柱、时柱的推算规则和依据（如节气分界、五虎遁等） | `"以立春1994-02-04 09:30:56换年..."` |

##### 2. `ten_gods` — 十神体系

| 字段 | 类型 | 含义 |
|------|------|------|
| `ten_gods` | `dict` | **十神分布**。key 为 `"year"` / `"month"` / `"day"` / `"hour"` 分别代表四柱。每个柱内包含: |

每个柱的结构:

| 子字段 | 类型 | 含义 | 示例值 |
|--------|------|------|--------|
| `gan` | `string` | 该柱天干对应的**十神名称**（相对于日主）。若为日柱则为 `"日主"`，若时柱未知则为 `null` | `"食神"` / `"正印"` / `"日主"` / `null` |
| `hidden_stems` | `array` | 该柱地支中藏干对应的十神列表。每个元素包含 `gan`（藏干天干名）和 `ten_god`（该藏干相对于日主的十神名） | `[{"gan":"戊","ten_god":"七杀"}, ...]` |

**十神名称速查表**（前端展示用）:

| 十神 | 含义 | 正面特质 | 负面特质 |
|------|------|----------|----------|
| 日主 | 命主自身 | — | — |
| 正印 | 学习、贵人、保护 | 聪明好学、有贵人助 | 依赖性强 |
| 偏印 | 偏门才能、孤独 | 特殊才能、悟性高 | 孤僻、不合群 |
| 食神 | 才华、表达、享受 | 温和有才、善表达 | 懒散、享乐 |
| 伤官 | 聪明、叛逆、创造 | 才华横溢、创新 | 傲气、叛逆 |
| 正财 | 稳定收入、妻子 | 勤俭、务实 | 保守、吝啬 |
| 偏财 | 意外之财、父亲 | 慷慨、人缘好 | 挥霍、不稳定 |
| 正官 | 事业、纪律、丈夫 | 正直、有责任感 | 刻板、压力大 |
| 七杀 | 竞争、挑战、权威 | 果断、有魄力 | 冲动、好斗 |
| 劫财 | 同辈、竞争 | 合作、社交 | 争夺、不专 |
| 比肩 | 自我、独立 | 独立、自主 | 固执、自我 |

##### 3. `element_counts` — 五行力量

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `element_counts` | `dict` | **五行力量分布**。key 为五行名（"金"/"木"/"水"/"火"/"土"），value 为 `float` 类型的加权计数值。数值越大表示该五行在命盘中越强。用于绘制五行雷达图或柱状图 | `{"土":1.0, "木":1.0, "水":3.0, "火":0.3, "金":3.5}` |

> 提示: 前端可用此数据绘制五行雷达图。value 为 `float`，可能包含小数（如 `0.3`）。

##### 4. `dayun` — 大运

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `dayun.direction` | `string` | **大运排盘方向**。`"顺排"` 或 `"逆排"`，由性别和年干阴阳决定 | `"顺排"` |
| `dayun.start` | `string` | **起运信息**。描述起运年龄、起运时间及计算依据 | `"顺排，取寒露...约5年1个月12天起运（约1999-11-05）"` |

##### 5. `strength` — 日主旺衰（身强/身弱）

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `strength.classification` | `string` | **旺衰结论**。`"身强"` 或 `"身弱"`，是八字分析的核心判断。身强喜克泄耗，身弱喜生扶 | `"身强"` |
| `strength.evidence` | `[string]` | **判断依据**。文字列表，逐条解释为什么得出此结论（月令、通根、生克力量对比等） | `["月令主气生日主...", "命局中生扶日主的力量相对明显..."]` |
| `strength.favorable_elements` | `[string]` | **喜用神（喜神）**。对命主有利的五行元素列表，如 `["木","火","土"]`。前端可用来做五行推荐 | `["木", "火", "土"]` |
| `strength.unfavorable_elements` | `[string]` | **忌神**。对命主不利的五行元素列表，如 `["金","水"]`。前端可用来做避免提示 | `["金", "水"]` |

##### 6. `pattern` — 格局

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `pattern.classification` | `string` | **格局名称及白话解释**。一段完整文本，包含格局名称、来源和白话说明。可直接展示给用户 | `"格局初判为正印格，来源是月令主气。它的白话意思是：重学习、资质..."` |
| `pattern.evidence` | `[string]` | **格局判断依据**。文字列表，逐条说明格局的推断逻辑 | `["月令酉以辛为主气，对日主为正印。", "以月令主气正印定为正印格。"]` |

##### 7. `wealth` — 财运分析

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `wealth.summary` | `string` | **财运总结**。一段完整文本，包含赚钱路径、留财条件和风险提醒。可直接展示给用户 | `"赚钱路径：财星显示对客户、资源...敏感度..."` |
| `wealth.evidence` | `[string]` | **财运分析依据**。文字列表，逐条说明财运判断的逻辑 | `["财星显示对客户...敏感度...", "食伤较清楚时，更适合..."]` |

##### 8. `relationship` — 感情/婚姻分析

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `relationship.summary` | `string` | **感情总结**。一段完整文本，分吸引/建立/稳定三个阶段描述。可直接展示给用户 | `"吸引阶段：桃花只代表被注意和互动机会..."` |
| `relationship.evidence` | `[string]` | **感情分析依据**。文字列表，逐条说明感情判断的逻辑 | `["桃花只代表被注意和互动机会...", "配偶星需要与夫妻宫..."]` |
| `relationship.stability_signals` | `array` | **婚姻稳定性信号**。数组，每个元素描述夫妻宫的一个关键信号 | 见下方 |

`stability_signals` 数组中每个元素:

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `polarity` | `string` | **信号极性**。`"positive"`（稳定有利）、`"negative"`（需注意）、`"mixed"`（中性） | `"mixed"` |
| `fact` | `string` | **事实描述**。具体的命盘事实，如日支是什么、有无合冲 | `"日支子；合为无；冲为无"` |
| `explanation` | `string` | **解释说明**。对此信号的解读 | `"有合重在边界与承诺落实，有冲重在变化和沟通管理..."` |

##### 9. 规则版本信息

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `internal_rule_version` | `string` | **内部规则引擎版本号**。用于追踪当前命盘使用了哪个版本的算法规则 | `"2.0.0"` |
| `rule_ids` | `[string]` | **应用的规则 ID 列表**。当前命盘计算过程中触发的规则标识，可用于调试或审计 | `["CAL-YEAR-LICHUN", "CAL-MONTH-JIE", "PILLAR-MONTH-FIVETIGER", ...]` |

##### 10. `current_context` — 当前上下文

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `current_context` | `dict` | **当前时空上下文**。包含当前年份的四柱信息，用于后续流年分析 | 见下方 |

`current_context` 子字段:

| 字段 | 类型 | 含义 | 示例值 |
|------|------|------|--------|
| `year` | `int` | 当前年份 | `2026` |
| `year_pillar` | `string` | 当前年柱干支 | `"丙午"` |
| `month_pillar` | `string` | 当前月柱干支 | `"丙申"` |
| `day_pillar` | `string` | 当前日柱干支 | `"甲子"` |

---

#### 错误响应

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 403 | `PRIVACY_CONSENT_REQUIRED` | public 模式未同意隐私处理 |
| 409 | `SESSION_REQUIRED` | 预览会话不存在或已过期 |
| 409 | `PREVIEW_CONFLICT` | 预览无效、已使用或不属于当前会话 |
| 409 | `FINGERPRINT_MISMATCH` | 输入信息或命盘已变化，需重新预览 |
| 410 | `SESSION_EXPIRED` | 会话已过期 |
| 422 | `VALIDATION_ERROR` | 请求参数校验失败 |
| 422 | `INVALID_BIRTH_INPUT` | 出生信息无法生成命盘 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |

---

### 4.4 获取命盘

```
GET /api/v1/chart/{chart_id}
```

**功能**: 根据 chart_id 获取已确认的命盘数据。chart_id 来自 confirm 接口的返回值。

#### 路径参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `chart_id` | `string` | 确认命盘时返回的 chart_id |

#### 成功响应 (200) - GetChartResponse

与 `ConfirmChartResponse` 结构相同:

```json
{
  "chart_id": "ywL6akW-QbmlRcmgNEGZ2X1EXYV-qu_9",
  "chart_facts": { ... },
  "chart_fingerprint": "bf8733a1af02bd55..."
}
```

#### 错误响应

| 状态码 | 错误码 | 说明 |
|--------|--------|------|
| 403 | `SESSION_REQUIRED` | 会话不存在或已过期 |
| 403 | `CHART_SESSION_MISMATCH` | 该命盘不属于当前会话 |
| 404 | `CHART_NOT_FOUND` | 命盘不存在 |
| 410 | `CHART_EXPIRED` | 命盘会话已过期 |
| 410 | `CHART_INVALIDATED` | 该命盘已被新确认的命盘替换 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 |

---

## 5. 完整调用流程

### 标准流程

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ 前端     │     │ 后端 API │     │ 说明     │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                 │               │
     │ POST /preview   │               │
     │ (出生信息)      │               │
     │────────────────>│               │
     │                 │               │
     │ 200 PreviewResponse             │
     │ (preview_id, fingerprints)      │
     │<────────────────│               │
     │                 │               │
     │ POST /confirm   │               │
     │ (出生信息 + preview 数据)        │
     │────────────────>│               │
     │                 │               │
     │ 200 ConfirmChartResponse        │
     │ (chart_id, chart_facts)         │
     │<────────────────│               │
     │                 │               │
     │ GET /chart/{id} │               │
     │────────────────>│               │
     │                 │               │
     │ 200 GetChartResponse            │
     │ (chart_facts)   │               │
     │<────────────────│               │
     │                 │               │
```

### 关键步骤说明

1. **Preview**: 前端提交出生信息，后端返回预览数据（包含四柱展示文本）和两个关键的指纹/token
2. **Confirm**: 前端将出生信息 + preview 返回的 `preview_id`、`input_fingerprint`、`chart_fingerprint` 原样回传，后端生成完整命盘数据
3. **Get Chart**: 用 `chart_id` 随时获取已确认的命盘数据

### 重试/错误处理

- **指纹不匹配 (409)**: 需要重新调用 preview 获取新的指纹
- **会话过期 (410)**: 需要重新从 preview 开始
- **命盘被替换 (410)**: 需要用新的 chart_id 查询

---

## 6. 错误码参考

| 状态码 | 错误码 | 说明 | 前端处理建议 |
|--------|--------|------|------------|
| 403 | `PRIVACY_CONSENT_REQUIRED` | 需同意隐私处理 | 弹窗要求用户同意隐私协议 |
| 403 | `SESSION_REQUIRED` | 会话不存在 | 重新从 preview 开始 |
| 403 | `CHART_SESSION_MISMATCH` | 命盘不属于当前会话 | 提示用户重新操作 |
| 404 | `CHART_NOT_FOUND` | 命盘不存在 | 提示用户命盘不存在 |
| 404 | `NOT_FOUND` | 路由不存在 | 检查请求 URL |
| 409 | `SESSION_REQUIRED` | 预览会话不存在 | 重新调用 preview |
| 409 | `PREVIEW_CONFLICT` | 预览冲突 | 重新调用 preview |
| 409 | `FINGERPRINT_MISMATCH` | 指纹不匹配 | 重新调用 preview |
| 410 | `SESSION_EXPIRED` | 会话过期 | 重新调用 preview |
| 410 | `CHART_EXPIRED` | 命盘过期 | 重新从 preview 开始 |
| 410 | `CHART_INVALIDATED` | 命盘已被替换 | 使用最新的 chart_id |
| 422 | `VALIDATION_ERROR` | 参数校验失败 | 检查 `fields` 数组，修正对应字段 |
| 422 | `INVALID_BIRTH_INPUT` | 出生信息无效 | 提示用户检查输入 |
| 500 | `INTERNAL_ERROR` | 服务器内部错误 | 提示用户稍后重试 |
| 503 | `SESSION_CAPACITY` | 服务繁忙 | 提示用户稍后重试 |

---

## 7. CORS 配置

### 允许的 Origin

默认允许以下 Origin:

```
http://localhost:3000
http://127.0.0.1:3000
http://localhost:5173
http://127.0.0.1:5173
```

可通过环境变量 `MINGSHU_CORS_ORIGINS` 配置（逗号分隔）。

### CORS 配置详情

| 配置项 | 值 |
|--------|-----|
| `Access-Control-Allow-Credentials` | `true` |
| `Access-Control-Allow-Methods` | `GET, POST, OPTIONS` |
| `Access-Control-Allow-Headers` | `Content-Type, X-Request-ID` |

### 前端请求注意事项

由于启用了 `credentials: true`，前端 fetch 请求需要设置:

```javascript
fetch(url, {
  method: 'POST',
  credentials: 'include',  // 关键：携带和接收 Cookie
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
})
```

---

## 8. 数据模型速查

### 请求模型

```
BirthInputRequest
├── name: string (max 120)
├── gender: "男" | "女" | "male" | "female"
├── calendar: "solar" | "lunar"
├── year: int (1900-2100)
├── month: int (1-12)
├── day: int (1-31)
├── hour: int | null (0-23)
├── minute: int | null (0-59)
├── is_leap_month: bool (default false)
├── birth_place: string (max 120)
├── time_label: string (max 120)
└── privacy_consent: bool (default false)

ConfirmChartRequest extends BirthInputRequest
├── preview_id: string (16-80)
├── input_fingerprint: string (64 hex)
└── chart_fingerprint: string (64 hex)
```

### 响应模型

```
PreviewResponse
├── preview_id: string
├── input_text: string
├── solar_datetime: string
├── pillars: [string, string, string, string]
├── calculation_basis: string
├── input_fingerprint: string (token)
└── chart_fingerprint: string

ConfirmChartResponse / GetChartResponse
├── chart_id: string
├── chart_fingerprint: string
└── chart_facts: CanonicalChartFacts
    ├── gender: string
    ├── pillars: [string, string, string, string]
    ├── day_master: string
    ├── hidden_stems: dict
    ├── ten_gods: dict
    ├── element_counts: dict
    ├── time_mode: string
    ├── pillar_basis: string
    ├── dayun: { direction: string, start: string }
    ├── strength: { classification, evidence[], favorable_elements[], unfavorable_elements[] }
    ├── pattern: { classification, evidence[] }
    ├── wealth: { summary, evidence[] }
    ├── relationship: { summary, evidence[], stability_signals[] }
    ├── internal_rule_version: string
    ├── rule_ids: string[]
    └── current_context: dict

ErrorResponse
├── error: { code: string, message: string, fields: string[] }
└── request_id: string
```

---

## 9. 前端示例代码

### JavaScript (fetch)

```javascript
const API_BASE = 'http://127.0.0.1:8000';

// 1. 检查服务健康
async function checkHealth() {
  const res = await fetch(`${API_BASE}/healthz`);
  return res.json();
  // => { status: "ok", version: "1.0.0", runtime_mode: "local" }
}

// 2. 预览命盘
async function previewChart(birthData) {
  const res = await fetch(`${API_BASE}/api/v1/chart/preview`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(birthData),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(`[${err.error.code}] ${err.error.message}`);
  }
  return res.json();
}

// 3. 确认命盘
async function confirmChart(birthData, previewData) {
  const res = await fetch(`${API_BASE}/api/v1/chart/confirm`, {
    method: 'POST',
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...birthData,
      preview_id: previewData.preview_id,
      input_fingerprint: previewData.input_fingerprint,
      chart_fingerprint: previewData.chart_fingerprint,
    }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(`[${err.error.code}] ${err.error.message}`);
  }
  return res.json();
}

// 4. 获取已确认的命盘
async function getChart(chartId) {
  const res = await fetch(`${API_BASE}/api/v1/chart/${chartId}`, {
    method: 'GET',
    credentials: 'include',
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(`[${err.error.code}] ${err.error.message}`);
  }
  return res.json();
}

// === 完整流程示例 ===
async function fullFlow() {
  const birthData = {
    name: '张三',
    gender: '男',
    calendar: 'solar',
    year: 1994,
    month: 9,
    day: 23,
    hour: null,
    minute: null,
    is_leap_month: false,
    birth_place: '北京',
    time_label: '时辰不详',
    privacy_consent: true,
  };

  // Step 1: Preview
  const preview = await previewChart(birthData);
  console.log('四柱:', preview.pillars);

  // Step 2: Confirm
  const confirmed = await confirmChart(birthData, preview);
  console.log('命盘 ID:', confirmed.chart_id);
  console.log('日主:', confirmed.chart_facts.day_master);
  console.log('旺衰:', confirmed.chart_facts.strength.classification);
  console.log('喜用神:', confirmed.chart_facts.strength.favorable_elements);

  // Step 3: 后续可通过 chart_id 获取
  const chart = await getChart(confirmed.chart_id);
  console.log('命盘数据:', chart.chart_facts);
}
```

### TypeScript 类型定义

```typescript
// 请求类型
interface BirthInputRequest {
  name: string;
  gender: '男' | '女' | 'male' | 'female';
  calendar: 'solar' | 'lunar';
  year: number;       // 1900-2100
  month: number;      // 1-12
  day: number;        // 1-31
  hour: number | null;    // 0-23
  minute: number | null;  // 0-59
  is_leap_month?: boolean;
  birth_place?: string;
  time_label?: string;
  privacy_consent?: boolean;
}

interface ConfirmChartRequest extends BirthInputRequest {
  preview_id: string;
  input_fingerprint: string;  // 64 hex
  chart_fingerprint: string;  // 64 hex
}

// 响应类型
interface HealthResponse {
  status: 'ok';
  version: string;
  runtime_mode: 'public' | 'local';
}

interface PreviewResponse {
  preview_id: string;
  input_text: string;
  solar_datetime: string;
  pillars: [string, string, string, string];
  calculation_basis: string;
  input_fingerprint: string;
  chart_fingerprint: string;
}

interface ChartResponse {
  chart_id: string;
  chart_fingerprint: string;
  chart_facts: CanonicalChartFacts;
}

interface CanonicalChartFacts {
  gender: string;
  pillars: string[];
  day_master: string;
  hidden_stems: Record<string, string[]>;
  ten_gods: Record<string, any>;
  element_counts: Record<string, number>;
  time_mode: string;
  pillar_basis: string;
  dayun: { direction: string; start: string };
  strength: { classification: string; evidence: string[]; favorable_elements: string[]; unfavorable_elements: string[] };
  pattern: { classification: string; evidence: string[] };
  wealth: { summary: string; evidence: string[] };
  relationship: { summary: string; evidence: string[]; stability_signals: StabilitySignal[] };
  internal_rule_version: string;
  rule_ids: string[];
  current_context: Record<string, any>;
}

interface StabilitySignal {
  polarity: string;
  fact: string;
  explanation: string;
}

interface ErrorResponse {
  error: { code: string; message: string; fields: string[] };
  request_id: string;
}
```

---

## 10. 连通性测试结果

> 测试日期: 2026-08-18  
> 测试环境: local 模式, Python 3.11, FastAPI TestClient

| 接口 | 方法 | 状态 | 结果 |
|------|------|------|------|
| `/healthz` | GET | ✅ 200 | 正常返回版本和运行模式 |
| `/openapi.json` | GET | ✅ 200 | OpenAPI schema 完整可用 |
| `/api/v1/chart/preview` | POST | ✅ 200 | 预览成功，返回四柱和指纹 |
| `/api/v1/chart/confirm` | POST | ✅ 200 | 确认成功，返回完整命盘事实 |
| `/api/v1/chart/{chart_id}` | GET | ✅ 200 | 查询成功，数据与确认时一致 |
| 参数校验 - 缺少必填字段 | POST | ✅ 422 | 正确返回 VALIDATION_ERROR |
| 参数校验 - 公历闰月 | POST | ✅ 422 | 正确拒绝 |
| 参数校验 - hour/min 不配对 | POST | ✅ 422 | 正确拒绝 |
| 参数校验 - 额外字段 | POST | ✅ 422 | 正确拒绝额外字段 |
| 安全 - 跨 Session 访问 | GET | ✅ 403 | 正确拒绝 CHART_SESSION_MISMATCH |
| 安全 - 无预览直接确认 | POST | ✅ 409 | 正确拒绝 SESSION_REQUIRED |
| 安全 - 指纹篡改 | POST | ✅ 409 | 正确拒绝 PREVIEW_CONFLICT |

**完整流程测试**: ✅ 通过  
`Preview → Confirm → Get Chart` 三步流程完整走通，数据一致性验证通过。

---

## 附录: 快速启动

### 后端

```bash
cd bazi_ziwei_app
MINGSHU_RUNTIME_MODE=local .venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 验证服务

```bash
curl http://127.0.0.1:8000/healthz
# => {"status":"ok","version":"1.0.0","runtime_mode":"local"}
```

### 运行自动化测试

```bash
cd bazi_ziwei_app
.venv/bin/python -m pytest tests/test_backend_api.py -v
```

### 查看 OpenAPI 文档

启动服务后访问:
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc