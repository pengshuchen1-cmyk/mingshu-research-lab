# 数理后端 FastAPI 抽离计划（Phase 1 细化）

> 版本 v1.0 · 2026-08-16
> 前置文档：`docs/FRONTEND_REFACTOR_PLAN.md`
> 前端现状：`github-demo`（Vite + React 19 静态原型，PrototypePages 已覆盖首页/命盘/问答/我的等页面）

## 1. 总体思路

- **不重写域逻辑**：`core/`（排盘引擎）、`services/`（AI provider）、`rules/`（规则数据）、`report/`（报告生成）原样复用，FastAPI 只做薄封装层。
- **Streamlit 与 API 双轨共存**：新增 `backend/` 目录承载 FastAPI 应用，`app.py` 不动，迁移期共享 `core/` 但不共享 session。
- **所有不变量保留**（见 AGENTS.md）：本地引擎是唯一命理权威；public 模式不碰 SQLite/备份/持久日志；AI 走 FactPacket → AnalysisPlan → 单次 provider 调用；chart 输入流 form → preview → fingerprint → confirm。

## 2. 目标目录结构

```
backend/
├── main.py                 # FastAPI 实例、CORS、runtime-mode 中间件
├── deps.py                 # 依赖注入：runtime mode、session、限流
├── api/v1/
│   ├── chart.py            # 排盘 preview/confirm/get
│   ├── luck.py             # 今日/流月/流年
│   ├── inquiry.py          # AI 问答（SSE 流式）
│   ├── report.py           # 报告生成与导出
│   ├── profile.py          # 档案 CRUD（仅 local 模式）
│   ├── ziwei.py            # 紫微排盘
│   └── compatibility.py    # 合婚
├── schemas/                # Pydantic 模型（extra="forbid"，从 core/chart_facts 映射）
├── session/                # 服务端会话（内存 TTL，对齐 utils/session_privacy）
└── tests/                  # API 层测试（fake provider，不走网络）
```

## 3. API 契约（v1）

| Endpoint | 方法 | 对应现有模块 | 说明 |
|---|---|---|---|
| `/api/v1/chart/preview` | POST | `core/birth_input_preview.py` + `four_pillars_engine` | 出生输入校验 + 四柱预览，返回未确认的 ChartFacts 预览 |
| `/api/v1/chart/confirm` | POST | `core/chart_fingerprint.py` | fingerprint 校验 → 确认盘，返回 chart_id + 完整 ChartFacts |
| `/api/v1/chart/{chart_id}` | GET | `core/chart_facts.py` | 会话内取已确认命盘（不落盘，public 模式仅内存） |
| `/api/v1/ziwei/chart` | POST | `core/ziwei_*` 系列 | 紫微排盘（P2，可延后） |
| `/api/v1/luck/daily` `monthly` `yearly` | GET | `core/luck_engine` `monthly_engine` `yearly_engine` | 需 chart_id |
| `/api/v1/inquiry/stream` | POST(SSE) | `core/ai_orchestrator` + `services/` | 先本地安全答案，再单次 provider；SSE 分段推送 |
| `/api/v1/report/generate` | POST | `report/` | Markdown/文本；PDF 仅 local |
| `/api/v1/profile/*` | CRUD | `utils/database.py` | **仅 local 模式注册路由**，public 模式 404 |
| `/healthz` | GET | — | 部署健康检查 |

横切能力：runtime-mode 中间件（public/local）、进程内限流复用 `core/ai_request_control.py`、CORS 白名单、错误码统一、OpenAPI schema 供前端 `openapi-typescript` 生成类型。

## 4. 会话与隐私设计

- 会话标识用 HttpOnly Cookie（签名 session id），服务端内存存储已确认 ChartFacts，TTL 与 chart 切换清理逻辑对齐 `utils/session_privacy.py`。
- Public 模式：不注册 profile 路由、不初始化 SQLite、日志仅 allowlist 元数据；请求体/响应不落日志。
- Local 模式：SQLite 仅 backend 进程访问，schema 迁移走现有 `utils/database.py` 路径。
- 明确局限：内存会话与限流是单实例的，部署文档需注明不支持多副本（除非引入 Redis，本期不做）。

## 5. 三周排期（按工作日）

### Week 1 — 骨架与排盘主链路

| 天 | 内容 | 验收 |
|---|---|---|
| D1 | `backend/` 脚手架：FastAPI 实例、runtime-mode 中间件、CORS、`/healthz`、pytest 基建（public/local 两套 fixture） | `pytest backend/tests` 绿；两种模式 healthz 行为正确 |
| D2 | schemas：`BirthInput`（china_standard only）、`ChartPreview`、`ChartFacts` 的 Pydantic 映射（`extra="forbid"`）；`POST /chart/preview` 接 `birth_input_preview` + 四柱引擎 | preview 接口对边界用例（23:00、闰月、未知时辰、立春）返回与 Streamlit 路径一致的结果 |
| D3 | `POST /chart/confirm`（fingerprint 校验）+ 会话存储（内存 TTL）+ `GET /chart/{id}` | 确认流测试：未确认取盘被拒、TTL 过期清理、chart 切换失效 |
| D4 | 回归对齐：用现有 `tests/test_bazi_calendar_adapter.py` 等的输入集做 API vs Streamlit 双跑对比测试（golden 数据） | 关键边界 golden 全部一致 |
| D5 | 运势三接口：daily/monthly/yearly 接 `luck_engine`/`monthly_engine`/`yearly_engine`；跑 `tools/validate_event_chain_quality.py` | 运势接口测试绿；事件链校验通过 |

### Week 2 — AI 问答与报告

| 天 | 内容 | 验收 |
|---|---|---|
| D6 | inquiry 请求模型（scope/question only）+ scope gate + 意图解析接 `ai_intent`/`ai_question_resolver`；本地安全答案先行（`local_bazi_answer`） | 无 provider 时返回本地答案；越界 scope 被拒 |
| D7 | FactPacket/AnalysisPlan 组装 + provider 调用（复用 orchestrator 单次调用约束、Kimi 固定模型、OpenAI store=False）；fake provider 测试 | 单次调用、注入拒绝、PII 脱敏有测试 |
| D8 | SSE 流式：`/inquiry/stream` 分段推送（segment guard、冲突替换、全不安全 fallback）；输出结构与 Streamlit 一致 | fake provider 下的流式分段测试 |
| D9 | 报告：`/report/generate`（Markdown/文本），public 导出无 PII 文件名、不写服务器文件；PDF 仅 local | public/local 双模式报告测试 |
| D10 | profile CRUD（仅 local 注册）+ SQLite 访问隔离测试；public 模式确认 404 且无 DB 初始化 | 隐私隔离测试：public 模式无 data/ 触碰 |

### Week 3 — 联调、部署与收尾

| 天 | 内容 | 验收 |
|---|---|---|
| D11 | OpenAPI 导出 + 前端 `api-client.ts` 类型生成（openapi-typescript）；`github-demo` 首页/命盘页从 mock 切到真实 API | 前端排盘页真数据可跑 |
| D12 | 问答页接 SSE（含 loading/降级本地答案）；我的页按模式显示/隐藏档案入口 | 浏览器手工验证流式渲染 |
| D13 | 部署：Dockerfile（backend 非 root）+ docker-compose 扩展 `backend` 服务 + Caddy 路由；`docker compose config --quiet` | `tests/test_deployment_assets.py` 相关项通过（注意既有 3 项基线失败） |
| D14 | 全量回归：本仓库 pytest 全套 + `check_env.py` + `pip check` + compileall + backend 套件；性能抽测（排盘接口 <300ms 量级） | 全绿（除已知基线失败），基线如实上报 |
| D15 | 缓冲日：修联调问题、补文档（API 使用说明、部署说明、会话/限流单实例局限）、评审与验收 | 文档合入 |

## 6. 团队分工（1 前端 + 1 后端 + 1 老板）

### 角色职责

**后端开发** — 唯一代码所有者：`backend/`、`backend/tests/`、部署配置（Dockerfile/compose/Caddy 的 backend 部分）
- FastAPI 脚手架、runtime-mode 中间件、会话与隐私隔离
- 排盘/运势/问答/报告/档案全部 endpoint 的实现与测试
- AI 边界完整性（scope gate、单次调用、脱敏、fallback）
- golden 双跑对比（API vs Streamlit）、日历边界回归
- D3 结束前冻结 OpenAPI 契约发给前端；D11 导出 schema

**前端开发** — 唯一代码所有者：`github-demo`（后续 `frontend/`）
- 静态原型继续推进为真实页面（P0：命盘、问答；P1：今日/年度、报告、我的；P2：紫微/合婚/专项）
- `api-client.ts`、openapi-typescript 类型接入、Zustand + TanStack Query 状态层
- SSE 流式渲染、public 模式不做 PII 本地缓存
- 前端不做任何命理计算，全部以 API 的 ChartFacts 为准

**老板** — 产品与验收，不写代码
- 里程碑验收：D5（排盘+运势真数据演示）、D10（问答+报告演示）、D15（整体验收）
- 决策项：P0/P1/P2 优先级调整、public/local 模式产品范围、Streamlit 下线时机、部署托管与域名/API key 等资源、隐私合规签字
- 每日 15 分钟站会同步阻塞；风险拍板（如是否带已知基线失败上线）

### 按天分工表

| 天 | 后端 | 前端 | 老板 |
|---|---|---|---|
| D1 | FastAPI 骨架+中间件+healthz | 命盘页静态原型（对齐设计稿） | 确认 P0 页面清单 |
| D2 | preview 接口+schemas | 问答页静态原型 | — |
| D3 | confirm+会话存储；**冻结 API 契约** | 我的页/年度页原型 | 验收静态原型方向 |
| D4 | golden 双跑对比 | 按契约写 mock，搭 api-client 骨架 | — |
| D5 | 运势三接口 | TanStack Query 接入 mock 数据 | **里程碑：原型+契约评审** |
| D6 | scope gate+本地安全答案 | 命盘页表单（RHF+Zod） | — |
| D7 | provider 调用链+fake 测试 | 命盘页渲染逻辑（等真数据） | — |
| D8 | SSE 流式接口 | 问答页流式 UI 骨架（用假流） | — |
| D9 | 报告导出接口 | 报告页+导出交互 | — |
| D10 | profile CRUD+隐私隔离测试 | 我的页按模式显隐档案入口 | **里程碑：功能演示** |
| D11 | OpenAPI 导出+联调支持 | **首页/命盘页切真数据** | — |
| D12 | 联调修 bug | **问答页接真 SSE+我的页** | — |
| D13 | Docker/Compose/Caddy | 构建产物+部署配置（前端侧） | 托管/域名决策落地 |
| D14 | 全量回归+性能抽测 | 全页面走查+bug 修复 | — |
| D15 | 修问题+API 文档 | 修问题+走查 | **整体验收+下一步拍板** |

### 协作规则

1. **契约是唯一接口**：D3 冻结后，改字段必须后端发起、前端确认，避免口头同步。
2. **代码所有权**：互不提交对方目录；`core/` 等域逻辑只允许后端改。
3. **阻塞升级**：联调期（D11-D12）问题当天不过夜，老板裁优先级。

## 7. 风险与守则


1. 前端绝不并行计算命理结论，一切以 API 返回的 ChartFacts 为准。
2. calendar 边界（立春/节气/23点/闰月/未知时辰/起运）每个接口都要有 golden 测试。
3. AI 边界全部在 backend 实施，前端只传 scope/question。
4. public 模式的任何新增代码路径都要有"未触碰 SQLite/备份/持久日志"的测试。
5. Streamlit 保持可运行，直到前端功能对齐后再评估下线，不在本期范围。
