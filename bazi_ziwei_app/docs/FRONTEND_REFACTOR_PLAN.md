# 命数研究室 · 前后端分离重构方案

> 版本：v0.1 · 2026-08-15  
> 目标：将现有 Streamlit 单体应用拆分为 **Python API 后端** + **Next.js 前端**，实现设计稿中的 Bento Dashboard 体验。

---

## 1. 现状分析

| 维度 | 当前（Streamlit） | 目标（前后端分离） |
|------|-------------------|-------------------|
| 前端 | Streamlit + 自定义 CSS/HTML | Next.js 16 + Tailwind + shadcn/ui |
| 后端 | Python 内嵌于 `app.py` / `core/` | FastAPI REST + SSE 流式 |
| 状态 | `st.session_state` 会话 | JWT / 会话 Cookie + React Query |
| 部署 | 单容器 Streamlit | 前端 Vercel/CDN + 后端 Docker |
| 设计 | ChunUI Streamlit 映射 | ChunUI Web 原生组件 |

**核心不变量**（来自 AGENTS.md）：
- 本地规则引擎（`core/`）仍是四柱、格局、大运等结论的唯一权威
- Public 模式会话隔离，不读写 SQLite
- AI 请求经 FactPacket → AnalysisPlan → 单次 provider 调用
- 输入流：profile form → chart preview → fingerprint → confirmed chart

---

## 2. GitHub 开源参考项目

### 2.1 通用 Dashboard / Bento 布局（推荐参考 UI 结构）

| 项目 | Stars | 技术栈 | 参考价值 |
|------|-------|--------|----------|
| [Kiranism/next-shadcn-dashboard-starter](https://github.com/Kiranism/next-shadcn-dashboard-starter) | ~6.7k | Next.js 16, shadcn/ui, Tailwind v4 | **首选脚手架**：Sidebar、DataTable、主题切换、生产级布局 |
| [arhamkhnz/next-shadcn-admin-dashboard](https://github.com/arhamkhnz/next-shadcn-admin-dashboard) | ~2.8k | Next.js 16, 8 种 Dashboard 变体 | 多主题 preset、可折叠侧栏 |
| [satnaing/shadcn-admin](https://github.com/satnaing/shadcn-admin) | ~13.6k | Vite + shadcn/ui | Command Palette (⌘K)、Sidebar 组件设计 |
| [SeifeddineJamei/OpenBento](https://github.com/SeifeddineJamei/OpenBento) | ~29 | Vite, 7 种 Bento Dashboard | **Bento Grid 卡片组合**、Framer Motion 动画 |
| [Kritoooo/Zenith](https://github.com/Kritoooo/Zenith) | ~3 | Next.js, Glassmorphism Bento | 工具注册表模式、⌘K 搜索 |
| [hari7261/bento-style](https://github.com/hari7261/bento-style) | 新 | React + Tailwind Bento 组件库 | 6 种 preset Bento 布局 |
| [shadcn/ui dashboard-01](https://ui.shadcn.com/blocks) | 官方 | shadcn blocks | 官方 Dashboard block，可直接 `npx shadcn add` |

### 2.2 命理 / 八字垂直领域（推荐参考业务组件）

| 项目 | 技术栈 | 参考价值 |
|------|--------|----------|
| [tianma-if/zhaoming](https://github.com/tianma-if/zhaoming) | Next.js 16, shadcn, lunar-typescript, iztro | **最接近**：八字排盘卡片、五行雷达图、紫微 4×4 宫格、AI 流式判词 |
| [gaaiyun/FOR-BAZI](https://github.com/gaaiyun/FOR-BAZI) | FastAPI + React + shadcn + ECharts | **前后端分离架构参考**：14 个 API endpoint、ReAct Agent、RAG |
| [ruijayfeng/ziwei](https://github.com/ruijayfeng/ziwei) | React + iztro + ECharts | 紫微命盘、人生 K 线、年度运势可视化 |
| [WuXieXie/AiTaoist](https://github.com/WuXieXie/AiTaoist) | React + Express | AI 流式推演、Express 代理层设计 |
| [patdelphi/suanming](https://github.com/patdelphi/suanming) | React + Tailwind 中国风 | 八字/紫微/易经三合一 UI 风格 |

### 2.3 推荐组合策略

```
UI 脚手架:  next-shadcn-dashboard-starter  (布局/导航/主题)
     +
Bento 布局: OpenBento / bento-style          (卡片网格)
     +
业务组件:   zhaoming / FOR-BAZI              (八字卡片/五行图/AI 流)
     +
设计规范:   本项目 design-system/chunui/MASTER.md
```

---

## 3. 目标架构

```
┌─────────────────────────────────────────────────────────┐
│  frontend/ (Next.js 16)                                 │
│  ├── App Router pages                                   │
│  ├── components/ (ChunUI Bento widgets)                 │
│  ├── lib/api-client.ts (typed fetch + SSE)              │
│  └── stores/ (Zustand: session, chart, profile)         │
└──────────────────────┬──────────────────────────────────┘
                       │ REST / SSE
┌──────────────────────▼──────────────────────────────────┐
│  backend/ (FastAPI)                                     │
│  ├── api/v1/                                            │
│  │   ├── chart.py        → core/bazi_engine             │
│  │   ├── profile.py      → utils/database (local only)  │
│  │   ├── inquiry.py      → core/ai_orchestrator (SSE)   │
│  │   ├── report.py       → report/                      │
│  │   └── session.py      → utils/session_privacy        │
│  ├── middleware/ (runtime mode, CORS, rate limit)       │
│  └── schemas/ (Pydantic, extra=forbid)                  │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│  core/ + rules/ + services/  (现有 Python 域逻辑，复用)  │
└─────────────────────────────────────────────────────────┘
```

---

## 4. 分阶段实施计划

### Phase 0 — Demo 验证 ✅（当前）

- [x] 创建 `frontend/` Next.js 项目
- [x] 实现首页 Bento Dashboard Demo（mock 数据）
- [x] 对齐 ChunUI design tokens
- [ ] 团队评审设计稿还原度

### Phase 1 — 后端 API 层（2-3 周）

1. 新建 `backend/` FastAPI 应用，挂载现有 `core/` 模块
2. 核心 endpoint：
   - `POST /api/v1/chart/preview` — 输入校验 + 四柱预览
   - `POST /api/v1/chart/confirm` — fingerprint 确认
   - `GET  /api/v1/chart/{id}` — 获取 ChartFacts JSON
   - `POST /api/v1/inquiry/stream` — AI 问答 SSE
   - `GET  /api/v1/luck/daily|monthly|yearly` — 运势数据
3. Public/Local 模式 middleware（复用 `utils/runtime_mode.py`）
4. OpenAPI schema 自动生成 → 前端 type codegen

**参考**：FOR-BAZI 的 `/api/v1/chart` + `/api/v1/chat/stream` 设计

### Phase 2 — 前端核心页面（3-4 周）

| 页面 | 对应现有 Streamlit | 优先级 |
|------|-------------------|--------|
| 首页 Dashboard | `ui/home.py` + 设计稿 | P0 ✅ Demo |
| 命盘 | `ui/bazi_page.py` | P0 |
| AI 问答 | `ui/inquiry_page.py` | P0 |
| 今日/年度 | `ui/yearly_page.py` | P1 |
| 报告 | `ui/report_page.py` | P1 |
| 我的/设置 | `ui/my_page.py` | P1 |
| 紫微/合婚/专项 | 其余 pages | P2 |

### Phase 3 — 状态管理与联调（1-2 周）

- React Query 缓存 chart/luck 数据
- 会话 TTL 对齐 `utils/session_privacy.py`
- Profile 确认流：form → preview → fingerprint → confirm
- AI SSE 流式渲染（参考 AiTaoist / zhaoming）

### Phase 4 — 部署与迁移（1 周）

- Docker Compose：`frontend` + `backend` + `caddy`
- Public 模式：前端 CDN + 后端无状态
- Local 模式：SQLite 仅 backend 访问
- Streamlit 保留为 fallback，逐步下线

---

## 5. 技术选型确认

| 层 | 选型 | 理由 |
|----|------|------|
| 框架 | **Next.js 16 App Router** | SSR/SSG、API Routes 代理、Vercel 部署 |
| UI | **shadcn/ui + Tailwind v4** | 与 ChunUI 低饱和风格契合，组件可复制定制 |
| 图表 | **Recharts**（轻量）/ ECharts（复杂命盘） | Demo 已用 Recharts；紫微宫格可能需要 ECharts |
| 状态 | **Zustand + TanStack Query** | 轻量本地状态 + 服务端缓存 |
| 表单 | **React Hook Form + Zod** | 出生信息表单校验 |
| 后端 | **FastAPI** | 与现有 Python 生态无缝、SSE 原生支持 |
| 类型 | **openapi-typescript** | 前后端 schema 同步 |

---

## 6. 设计规范映射

ChunUI MASTER.md → Web CSS Variables（已在 `frontend/src/app/globals.css` 实现）：

| ChunUI Token | CSS Variable | 用途 |
|-------------|-------------|------|
| `#dcede5` | `--cc-primary` | 浅绿强调 |
| `#174e3c` | `--cc-primary-foreground` | 主色文字/按钮 |
| `#f2f4f3` | `--cc-content-background` | 页面背景 |
| `#fff` | `--cc-card` | 卡片背景 |
| `30px` → `24px` | `--cc-radius-card` | Web 略小圆角 |
| 13/17/24px | font sizes | 三级文本梯度 |

---

## 7. 风险与注意事项

1. **日历边界回归**：前后端分离后，四柱/qiyun 计算必须仍走 `core/` 单一路径，前端不做平行计算
2. **Public 隐私**：前端不得缓存 PII 到 localStorage；会话数据仅内存 + HttpOnly Cookie
3. **AI 安全边界**：前端只提交 scope/question，不组装 prompt；provider 调用仍在 backend
4. **Streamlit 共存期**：迁移期间双轨运行，共享 `core/` 但不共享 session
5. **中文字体**：Web 端需加载 Noto Sans SC 或系统 fallback

---

## 8. 下一步行动

1. **Review Demo**：运行 `cd frontend && npm run dev`，对比设计稿
2. **确定 Phase 1 优先级**：建议先做 `POST /api/v1/chart/preview` + 命盘页
3. **引入 shadcn/ui CLI**：`npx shadcn@latest init` 替换手写基础组件
4. **CI 扩展**：frontend `npm run build` + backend pytest 并行

---

*本方案基于 GitHub 开源社区调研与项目 AGENTS.md 约束编写。Demo 代码位于 `frontend/` 目录。*
