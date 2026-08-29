---
title: 前后端分离重构 - FastAPI 后端开发
status: draft
created: 2026-08-16
updated: 2026-08-16
---

# 前后端分离重构规格文档

## 1. 项目概述

### 1.1 目标
将现有 Streamlit 单体应用重构为前后端分离架构：
- **前端**：Next.js 16 + React 19 + TypeScript（已完成静态页面）
- **后端**：FastAPI + SQLite → PostgreSQL（新建）
- **部署**：前后端独立部署，支持横向扩展

### 1.2 当前状态
- ✅ 前端静态页面已完成（`frontend/` 目录）
- ✅ 核心业务逻辑完整（70+ 核心模块）
- ✅ SQLite 数据库（profiles.db）
- ⏳ 需要创建 RESTful API 层
- ⏳ 需要数据库迁移方案
- ⏳ 需要前后端对接

### 1.3 技术栈对比

| 组件 | 当前 | 目标 |
|------|------|------|
| Web 框架 | Streamlit | FastAPI |
| 前端 | Streamlit UI | Next.js + React |
| 数据库 | SQLite | PostgreSQL (生产) / SQLite (开发) |
| 认证 | Session | JWT Token |
| API 风格 | - | RESTful + WebSocket (AI 问答流式) |
| 部署 | Docker 单容器 | Docker Compose (多容器) |

---

## 2. 功能需求（基于新版 UI 设计）

### 2.0 首页 UI 模块分析

根据新版 UI 设计，首页包含以下核心模块：

**左侧导航栏**：
- 首页
- AI 聊天
- 流月日历
- 命盘分析
- 记忆档案
- 知识库
- 设置/用户中心/反馈提交

**主内容区（从上到下，从左到右）**：

**第一行**：
1. **今日能量值** - 显示综合能量分数 82/100，包含事业、财富、情感、健康四个维度
2. **本月关键词** - 主动·合作·收获，显示月度关键特征
3. **运势运势** - 上升年，显示年度运势趋势百分比 75%
4. **用户信息卡片** - 显示用户头像、称呼、生日、会员身份

**第二行**：
5. **AI 命理小助手** - AI 对话界面，包含历史消息、快捷问题按钮、输入框
6. **12 个月流月总览** - 显示全年 12 个月的运势状态和表情图标
7. **7 月运势属性** - 显示该月的事业、财富、健康、机遇四个维度评分

**第三行**：
8. **我的本命盘** - 显示八字四柱（年柱、月柱、日柱、时柱）的天干地支
9. **2024 甲辰年运势总述** - 环形进度条显示年度评分，包含事业、财富、情感、健康四维评分
10. **7 月运势详情** - 大吉月，显示综合、事业、财富、情感、健康五项星级评分
11. **AI 建议卡片** - 显示多个 AI 建议卡片（事业建议、财运建议、感情建议、健康建议）

**第四行**：
12. **五行能量分布** - 饼图显示五行（木火土金水）分布百分比
13. **查看完整命盘解析** - 链接按钮
14. **查看完整详细解析** - 链接按钮
15. **查看完整运盘分析** - 链接按钮

**右侧快捷入口**：
- 我的管理账号 - 账号管理、资料管理、会员权益
- 帮助文档 - 使用指南、解释器操作、使用说明
- 收费师微信 - AI 老师微信对话查询
- 每月拱晨 - 查看你本使用情况详情
- 收据相册 - 资讯相册、查询当前相册

### 2.1 核心业务模块映射

根据新版 UI 设计和现有 core/ 模块，定义以下 API 需求：

#### 2.1.1 用户认证与档案管理
**前端需求**：用户登录、用户信息展示、会员管理
**UI 位置**：右上角用户头像卡片、右侧用户管理入口
**API 端点**：
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `POST /api/auth/refresh` - 刷新 Token
- `GET /api/user/profile` - 获取用户信息（包含会员状态）
- `PUT /api/user/profile` - 更新用户信息
- `GET /api/user/membership` - 获取会员信息

**对应模块**：
- 新建：`backend/api/auth.py`
- 新建：`backend/models/user.py`

#### 2.1.2 今日能量值与四维评分
**前端需求**：显示今日综合能量分数及事业、财富、情感、健康四维评分
**UI 位置**：首页左上角第一个卡片
**API 端点**：
- `GET /api/dashboard/daily-energy` - 获取今日能量值（82/100）
- `GET /api/dashboard/daily-dimensions` - 获取四维评分（事业 80、财富 70、情感 85、健康 78）

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "energy_score": 82,
    "max_score": 100,
    "date": "2024-08-16",
    "dimensions": [
      { "name": "事业", "score": 80, "icon": "💼" },
      { "name": "财富", "score": 70, "icon": "💰" },
      { "name": "情感", "score": 85, "icon": "💕" },
      { "name": "健康", "score": 78, "icon": "🌿" }
    ],
    "description": "状态不错，特异事业会有好运"
  }
}
```

**对应模块**：
- 复用：`core/life_assessment.py`
- 复用：`core/life_overview_engine.py`
- 新建：`backend/services/daily_energy_service.py`

#### 2.1.3 本月关键词
**前端需求**：显示本月运势关键词和描述
**UI 位置**：首页第一行中间卡片
**API 端点**：
- `GET /api/dashboard/monthly-keywords` - 获取本月关键词

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "month": 8,
    "keywords": ["主动", "合作", "收获"],
    "descriptions": [
      "把握时机，精确行动",
      "贵人运旺，共赢可期",
      "成果可见，机会把握"
    ],
    "view_detail_text": "查看学习日程"
  }
}
```

**对应模块**：
- 复用：`core/monthly_engine.py`
- 复用：`core/enhanced_monthly_engine.py`

#### 2.1.4 运势趋势（上升年/下降年）
**前端需求**：显示年度运势趋势和百分比
**UI 位置**：首页第一行右侧卡片
**API 端点**：
- `GET /api/dashboard/annual-trend` - 获取年度运势趋势

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "trend_type": "上升年",
    "trend_percent": 75,
    "description": "运渐提升，持续提升"
  }
}
```

**对应模块**：
- 复用：`core/yearly_engine.py`
- 复用：`core/stage_engine.py`

#### 2.1.5 12 个月流月总览
**前端需求**：显示全年 12 个月的运势状态、表情图标
**UI 位置**：首页第二行中间大卡片
**API 端点**：
- `GET /api/dashboard/yearly-calendar` - 获取全年月度运势总览

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "months": [
      { "month": 1, "status": "平稳", "emoji": "😊", "score": 70 },
      { "month": 2, "status": "上升", "emoji": "😄", "score": 80 },
      { "month": 3, "status": "大吉", "emoji": "😍", "score": 95 },
      ...
    ]
  }
}
```

**对应模块**：
- 复用：`core/monthly_engine.py`
- 复用：`core/luck_engine.py`

#### 2.1.6 月度运势详情
**前端需求**：显示指定月份的五维星级评分（综合、事业、财富、情感、健康）
**UI 位置**：首页第三行右侧卡片
**API 端点**：
- `GET /api/dashboard/monthly-detail?year={year}&month={month}` - 获取月度详细评分

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "month": 7,
    "title": "大吉月",
    "emoji": "😍",
    "ratings": [
      { "dimension": "综合", "stars": 5 },
      { "dimension": "事业", "stars": 4 },
      { "dimension": "财富", "stars": 5 },
      { "dimension": "情感", "stars": 4 },
      { "dimension": "健康", "stars": 3 }
    ]
  }
}
```

**对应模块**：
- 复用：`core/monthly_engine.py`

#### 2.1.7 命盘档案 (Profile Management)
**前端需求**：创建、查询、更新、删除命盘档案
**UI 位置**：记忆档案导航项
**API 端点**：
- `POST /api/profiles` - 创建命盘档案
- `GET /api/profiles` - 获取命盘列表（支持搜索、分页）
- `GET /api/profiles/{profile_id}` - 获取单个命盘详情
- `PUT /api/profiles/{profile_id}` - 更新命盘基础信息
- `DELETE /api/profiles/{profile_id}` - 删除命盘
- `GET /api/profiles/search?keyword={keyword}&gender={gender}` - 搜索命盘

**对应模块**：
- 复用：`utils/database.py` → `backend/repositories/profile_repository.py`
- 新建：`backend/api/profiles.py`

#### 2.1.8 我的本命盘（八字四柱）
**前端需求**：显示八字四柱（年月日时柱）的天干地支和五行
**UI 位置**：首页第三行左下角卡片
**API 端点**：
- `GET /api/dashboard/bazi-pillars` - 获取八字四柱简要信息

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "pillars": {
      "year": { "gan": "甲", "zhi": "申", "element": "金" },
      "month": { "gan": "辛", "zhi": "卯", "element": "木" },
      "day": { "gan": "丙", "zhi": "丁", "element": "火" },
      "hour": { "gan": "丁", "zhi": "巳", "element": "火" }
    },
    "view_detail_link": "/bazi/detail"
  }
}
```

**对应模块**：
- 复用：`core/bazi_engine.py`
- 复用：`core/four_pillars_engine.py`

#### 2.1.9 八字排盘详细 (Bazi Chart Detail)
**前端需求**：完整八字命盘、四柱、五行、十神、大运流年
**UI 位置**：命盘分析导航项
**API 端点**：
- `POST /api/bazi/chart` - 生成八字命盘
- `GET /api/bazi/chart/{profile_id}` - 获取已保存的八字命盘
- `POST /api/bazi/preview` - 预览八字命盘（不保存）
- `GET /api/bazi/dayun/{profile_id}` - 获取大运流年数据
- `GET /api/bazi/yearly/{profile_id}?year={year}` - 获取年度运势

**对应模块**：
- 复用：`core/bazi_engine.py`
- 复用：`core/four_pillars_engine.py`
- 复用：`core/dayun_rule_engine.py`
- 复用：`core/yearly_engine.py`
- 复用：`core/five_elements.py`
- 复用：`core/ten_gods.py`
- 复用：`core/pattern_engine.py`
- 复用：`core/strength_engine.py`

#### 2.1.10 年度运势总述（环形图 + 四维评分）
**前端需求**：显示年度总评分（环形进度条）和事业、财富、情感、健康四维评分
**UI 位置**：首页第三行中间卡片
**API 端点**：
- `GET /api/dashboard/annual-summary?year={year}` - 获取年度运势总述

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "year_name": "甲辰年",
    "total_score": 75,
    "max_score": 100,
    "trend": "上升",
    "dimensions": [
      { "name": "事业", "score": 78 },
      { "name": "财富", "score": 72 },
      { "name": "情感", "score": 65 },
      { "name": "健康", "score": 80 }
    ],
    "summary": "今年走势平稳上升，事业和财运表现出色，值得重点把握机会。",
    "view_detail_link": "/annual/detail"
  }
}
```

**对应模块**：
- 复用：`core/yearly_engine.py`
- 复用：`core/life_assessment.py`

#### 2.1.11 五行能量分布
**前端需求**：显示五行（木火土金水）分布百分比和饼图
**UI 位置**：首页第四行左下角卡片
**API 端点**：
- `GET /api/dashboard/wuxing-distribution` - 获取五行分布

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "wuxing": [
      { "element": "木", "percent": 15, "color": "#22c55e" },
      { "element": "火", "percent": 35, "color": "#ef4444" },
      { "element": "土", "percent": 25, "color": "#eab308" },
      { "element": "金", "percent": 15, "color": "#94a3b8" },
      { "element": "水", "percent": 10, "color": "#3b82f6" }
    ],
    "favorable_elements": ["火", "土"],
    "unfavorable_elements": ["水"],
    "view_detail_link": "/wuxing/detail"
  }
}
```

**对应模块**：
- 复用：`core/five_elements.py`

#### 2.1.12 AI 建议卡片
**前端需求**：显示多个维度的 AI 建议（事业、财运、感情、健康）
**UI 位置**：首页第三行右下角卡片
**API 端点**：
- `GET /api/dashboard/ai-advice` - 获取今日 AI 建议

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "date": "2024-08-16",
    "advices": [
      {
        "category": "事业建议",
        "icon": "💼",
        "title": "草稿建议",
        "summary": "了深度连锁处理持续，今作业是最后冲刺",
        "status": "查看详情"
      },
      {
        "category": "财运建议",
        "icon": "💰",
        "title": "财运建议",
        "summary": "财运可见，成点合作自我保障",
        "status": "查看详情"
      },
      {
        "category": "感情建议",
        "icon": "💕",
        "title": "感情建议",
        "summary": "可予视频意向，工作流程简易",
        "status": "查看详情"
      },
      {
        "category": "健康建议",
        "icon": "🌿",
        "title": "健康建议",
        "summary": "注重调节状态脑健康，需为合适",
        "status": "查看详情"
      }
    ]
  }
}
```

**对应模块**：
- 复用：`core/popular_advice_engine.py`
- 复用：`core/ai_orchestrator.py`（可选，用于生成更智能的建议）

#### 2.1.13 紫微斗数 (Ziwei Chart)
**前端需求**：紫微斗数命盘、宫位、星曜
**API 端点**：
- `POST /api/ziwei/chart` - 生成紫微斗数命盘
- `GET /api/ziwei/chart/{profile_id}` - 获取已保存的紫微命盘
- `POST /api/ziwei/preview` - 预览紫微命盘（不保存）

**对应模块**：
- 复用：`core/ziwei_engine.py`
- 复用：`core/ziwei_star_engine.py`
- 复用：`core/ziwei_minor_star_engine.py`
- 复用：`core/ziwei_fierce_star_engine.py`
- 复用：`core/ziwei_daxian_engine.py`

#### 2.1.14 AI 命理小助手（对话界面）
**前端需求**：AI 对话、历史消息展示、快捷问题、流式输出
**UI 位置**：首页第二行左侧大卡片、AI 聊天导航项
**API 端点**：
- `POST /api/ai/chat` - AI 问答（支持 WebSocket 流式）
- `GET /api/ai/chat/history/{session_id}` - 获取对话历史
- `POST /api/ai/chat/session` - 创建新会话
- `DELETE /api/ai/chat/session/{session_id}` - 删除会话
- `GET /api/ai/quick-questions` - 获取快捷问题列表

**WebSocket 端点**：
- `WS /ws/ai/chat` - AI 流式问答

**快捷问题响应格式**：
```json
{
  "code": 0,
  "data": {
    "questions": [
      "事业运连接器",
      "感情运势",
      "财运分析树",
      "如何提升赛程"
    ]
  }
}
```

**对应模块**：
- 复用：`core/ai_orchestrator.py`
- 复用：`core/ai_question_resolver.py`
- 复用：`core/ai_context.py`
- 复用：`core/ai_models.py`
- 复用：`services/ai_client_factory.py`
- 复用：`services/kimi_bazi_client.py`

#### 2.1.15 首页数据聚合接口（推荐）
**前端需求**：一次性获取首页所有数据，减少请求次数
**UI 位置**：整个首页
**API 端点**：
- `GET /api/dashboard/home` - 获取首页所有数据（聚合接口）

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "user": { ... },
    "daily_energy": { ... },
    "monthly_keywords": { ... },
    "annual_trend": { ... },
    "yearly_calendar": { ... },
    "monthly_detail": { ... },
    "bazi_pillars": { ... },
    "annual_summary": { ... },
    "wuxing_distribution": { ... },
    "ai_advice": { ... },
    "ai_recent_messages": [ ... ]
  }
}
```

**优点**：
- 减少前端请求次数（从 10+ 个减少到 1 个）
- 降低网络延迟
- 提高首屏加载速度
- 后端可以并行计算多个数据

**对应模块**：
- 新建：`backend/services/dashboard_service.py`（聚合服务）
- 复用：所有上述核心模块

#### 2.1.16 报告导出
**前端需求**：导出完整报告（PDF/Markdown/TXT）
**UI 位置**：右侧快捷入口
**API 端点**：
- `GET /api/reports/{profile_id}/export?format={pdf|markdown|txt}` - 导出报告

**对应模块**：
- 复用：`report/` 目录下的报告生成模块

#### 2.1.7 其他功能
**API 端点**：
- `GET /api/compatibility` - 合婚匹配分析
- `GET /api/health` - 健康检查
- `GET /api/version` - 版本信息

**对应模块**：
- 复用：`core/compatibility.py`

---

## 3. 非功能需求

### 3.1 性能要求
- **响应时间**：
  - 简单查询：< 100ms
  - 八字/紫微排盘：< 500ms
  - AI 问答首字：< 2s
  - 报告导出：< 3s
- **并发**：支持 100+ 并发请求
- **缓存策略**：
  - 命盘数据：Redis 缓存 1 小时
  - AI 问答：无缓存（实时计算）

### 3.2 安全要求
- JWT Token 认证，有效期 24 小时
- HTTPS 加密传输
- SQL 注入防护（ORM 层）
- XSS 防护（输入验证）
- CORS 配置（仅允许前端域名）
- 敏感数据脱敏（日志）

### 3.3 可用性要求
- 服务可用性：99.5%+
- 错误日志记录
- 健康检查端点
- Graceful Shutdown

### 3.4 可维护性要求
- API 文档自动生成（Swagger/OpenAPI）
- 代码覆盖率：> 80%
- 单元测试 + 集成测试
- 统一错误码体系

---

## 4. 数据模型

### 4.1 用户表 (users)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    avatar_url VARCHAR(255),
    membership_type VARCHAR(20) DEFAULT 'free', -- free, vip
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);
```

### 4.2 命盘档案表 (profiles)
```sql
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100),
    gender VARCHAR(10),
    calendar_type VARCHAR(10) NOT NULL DEFAULT 'solar', -- solar, lunar
    birth_date DATE NOT NULL,
    lunar_birth_date VARCHAR(20),
    birth_hour INTEGER,
    birth_minute INTEGER,
    birth_place VARCHAR(100),
    is_leap_month BOOLEAN DEFAULT FALSE,
    time_mode VARCHAR(20) DEFAULT 'china_standard',
    time_known BOOLEAN DEFAULT TRUE,
    use_solar_time BOOLEAN DEFAULT FALSE,
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_name ON profiles(name);
```

### 4.3 命盘数据表 (bazi_charts)
```sql
CREATE TABLE bazi_charts (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE CASCADE,
    chart_json JSONB NOT NULL,
    report_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_bazi_charts_profile_id ON bazi_charts(profile_id);
```

### 4.4 AI 对话会话表 (ai_sessions)
```sql
CREATE TABLE ai_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    profile_id INTEGER REFERENCES profiles(id) ON DELETE SET NULL,
    session_id VARCHAR(50) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 4.5 AI 对话消息表 (ai_messages)
```sql
CREATE TABLE ai_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(50) REFERENCES ai_sessions(session_id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL, -- user, assistant
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_ai_messages_session_id ON ai_messages(session_id);
```

---

## 5. API 设计规范

### 5.1 响应格式
```json
// 成功响应
{
  "code": 0,
  "message": "success",
  "data": { ... },
  "timestamp": "2026-08-16T10:00:00Z"
}

// 错误响应
{
  "code": 4001,
  "message": "Invalid input",
  "error": "birth_date is required",
  "timestamp": "2026-08-16T10:00:00Z"
}
```

### 5.2 错误码体系
| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 1000 | 未知错误 |
| 4000 | 请求参数错误 |
| 4001 | 参数验证失败 |
| 4010 | 未登录 |
| 4011 | Token 过期 |
| 4012 | Token 无效 |
| 4030 | 无权限 |
| 4040 | 资源不存在 |
| 4290 | 请求过于频繁 |
| 5000 | 服务器内部错误 |
| 5001 | 数据库错误 |
| 5002 | 外部服务错误（AI API） |

### 5.3 分页规范
```
GET /api/profiles?page=1&page_size=20

Response:
{
  "code": 0,
  "data": {
    "items": [ ... ],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  }
}
```

---

## 6. 开发计划（每日任务）

### Day 1: 项目初始化与基础框架
**目标**：搭建 FastAPI 项目结构，配置开发环境
- [ ] 创建 `backend/` 目录结构
- [ ] 初始化 FastAPI 项目
- [ ] 配置 Poetry/pip 依赖管理
- [ ] 创建 `requirements-backend.txt`
- [ ] 配置数据库连接（SQLAlchemy）
- [ ] 实现健康检查端点 `/api/health`
- [ ] 配置 CORS、日志、环境变量
- [ ] 编写项目 README

**验收标准**：
- FastAPI 服务启动成功
- 健康检查端点返回正常
- 数据库连接测试通过

### Day 2: 用户认证模块
**目标**：实现 JWT 认证体系
- [ ] 创建 User 数据模型（SQLAlchemy）
- [ ] 实现用户注册接口
- [ ] 实现用户登录接口（JWT）
- [ ] 实现 Token 刷新接口
- [ ] 实现 JWT 中间件
- [ ] 编写认证单元测试
- [ ] 配置密码加密（bcrypt）

**验收标准**：
- 用户可以注册、登录
- JWT Token 正确签发和验证
- 受保护端点需要 Token 访问

### Day 3: 命盘档案 API
**目标**：实现 Profile CRUD 接口
- [ ] 创建 Profile 数据模型
- [ ] 迁移 `utils/database.py` 逻辑到 Repository 层
- [ ] 实现 `POST /api/profiles` - 创建命盘
- [ ] 实现 `GET /api/profiles` - 列表查询（分页）
- [ ] 实现 `GET /api/profiles/{id}` - 详情查询
- [ ] 实现 `PUT /api/profiles/{id}` - 更新命盘
- [ ] 实现 `DELETE /api/profiles/{id}` - 删除命盘
- [ ] 实现搜索接口（关键词、性别）
- [ ] 编写单元测试

**验收标准**：
- CRUD 操作正常
- 分页、搜索功能正常
- 权限控制正常（只能操作自己的档案）

### Day 4: 八字排盘 API (1/2)
**目标**：实现八字命盘生成接口
- [ ] 封装 `core/bazi_engine.py` 为 Service 层
- [ ] 实现 `POST /api/bazi/chart` - 生成并保存命盘
- [ ] 实现 `POST /api/bazi/preview` - 预览命盘（不保存）
- [ ] 实现 `GET /api/bazi/chart/{profile_id}` - 获取命盘
- [ ] 处理农历/公历转换逻辑
- [ ] 处理真太阳时计算
- [ ] 编写单元测试

**验收标准**：
- 八字命盘生成正确
- 四柱、五行、十神数据完整
- 响应时间 < 500ms

### Day 5: 八字排盘 API (2/2) + 大运流年
**目标**：补充大运流年、年度运势接口
- [ ] 封装 `core/dayun_rule_engine.py`
- [ ] 封装 `core/yearly_engine.py`
- [ ] 实现 `GET /api/bazi/dayun/{profile_id}` - 大运流年
- [ ] 实现 `GET /api/bazi/yearly/{profile_id}` - 年度运势
- [ ] 实现缓存机制（Redis）
- [ ] 优化性能
- [ ] 编写单元测试

**验收标准**：
- 大运流年数据正确
- 年度运势分析正确
- 缓存命中率 > 80%

### Day 6: 紫微斗数 API
**目标**：实现紫微斗数命盘接口
- [ ] 封装 `core/ziwei_engine.py` 为 Service 层
- [ ] 封装星曜计算模块
- [ ] 实现 `POST /api/ziwei/chart` - 生成紫微命盘
- [ ] 实现 `POST /api/ziwei/preview` - 预览紫微命盘
- [ ] 实现 `GET /api/ziwei/chart/{profile_id}` - 获取紫微命盘
- [ ] 编写单元测试

**验收标准**：
- 紫微命盘生成正确
- 十四主星、辅星、煞星落宫准确
- 大限数据正确

### Day 7: AI 问答 API (1/2)
**目标**：实现 AI 问答基础接口
- [ ] 封装 `core/ai_orchestrator.py`
- [ ] 创建 AI Session 数据模型
- [ ] 实现 `POST /api/ai/chat/session` - 创建会话
- [ ] 实现 `POST /api/ai/chat` - 同步问答
- [ ] 实现 `GET /api/ai/chat/history/{session_id}` - 获取历史
- [ ] 集成 OpenAI/Kimi API
- [ ] 编写单元测试

**验收标准**：
- AI 问答功能正常
- 对话上下文保持
- 响应时间 < 5s

### Day 8: AI 问答 WebSocket 流式输出
**目标**：实现流式 AI 问答
- [ ] 实现 `WS /ws/ai/chat` - WebSocket 端点
- [ ] 实现流式输出（SSE 或 WebSocket）
- [ ] 实现前端 WebSocket 客户端对接
- [ ] 优化流式响应性能
- [ ] 编写集成测试

**验收标准**：
- WebSocket 连接稳定
- 流式输出流畅
- 首字延迟 < 2s

### Day 9: 综合分析 API
**目标**：实现能量分析、五行分析等接口
- [ ] 封装 `core/life_overview_engine.py`
- [ ] 封装 `core/monthly_engine.py`
- [ ] 实现 `GET /api/analysis/energy/{profile_id}` - 能量分数
- [ ] 实现 `GET /api/analysis/wuxing/{profile_id}` - 五行分析
- [ ] 实现 `GET /api/analysis/monthly/{profile_id}` - 月度分析
- [ ] 实现 `GET /api/analysis/daily/{profile_id}` - 日运势
- [ ] 编写单元测试

**验收标准**：
- 能量分数计算正确
- 五行分析数据完整
- 月度/日运势分析正确

### Day 10: 报告导出与其他功能
**目标**：实现报告导出、合婚匹配
- [ ] 封装 `core/compatibility.py`
- [ ] 实现 `GET /api/reports/{profile_id}/export` - 导出报告（PDF/Markdown/TXT）
- [ ] 实现 `POST /api/compatibility` - 合婚匹配
- [ ] 优化 PDF 生成性能
- [ ] 编写单元测试

**验收标准**：
- PDF/Markdown/TXT 导出正常
- 合婚匹配分析正确
- 导出时间 < 3s

### Day 11-12: 前后端对接
**目标**：前端集成 API，替换 mock 数据
- [ ] 前端配置 API 基础 URL
- [ ] 实现 API Client（axios）
- [ ] 实现 Token 管理（localStorage）
- [ ] 替换所有 mock 数据为真实 API 调用
- [ ] 实现错误处理
- [ ] 实现加载状态
- [ ] 测试完整用户流程

**验收标准**：
- 前端所有功能正常
- API 调用稳定
- 错误处理完善

### Day 13: 数据库迁移与优化
**目标**：从 SQLite 迁移到 PostgreSQL
- [ ] 编写数据迁移脚本
- [ ] 导出 SQLite 数据
- [ ] 导入 PostgreSQL
- [ ] 验证数据完整性
- [ ] 配置数据库连接池
- [ ] 优化索引

**验收标准**：
- 数据迁移无丢失
- PostgreSQL 查询性能 > SQLite
- 连接池配置合理

### Day 14: 测试与文档
**目标**：完善测试和文档
- [ ] 补充单元测试（覆盖率 > 80%）
- [ ] 编写集成测试
- [ ] 编写 API 文档（Swagger）
- [ ] 编写部署文档
- [ ] 编写前端对接文档
- [ ] 代码审查

**验收标准**：
- 测试覆盖率 > 80%
- API 文档完整
- 部署文档清晰

### Day 15: 部署上线
**目标**：生产环境部署
- [ ] 配置生产环境变量
- [ ] 配置 Nginx 反向代理
- [ ] 配置 HTTPS 证书
- [ ] 配置 Docker Compose
- [ ] 部署到生产服务器
- [ ] 压力测试
- [ ] 监控配置

**验收标准**：
- 生产环境稳定运行
- HTTPS 证书有效
- 监控告警正常

---

## 7. 技术选型细节

### 7.1 后端技术栈
- **Web 框架**：FastAPI 0.115+
- **ORM**：SQLAlchemy 2.0+
- **数据库**：PostgreSQL 15+ (生产) / SQLite 3.45+ (开发)
- **数据验证**：Pydantic 2.13+
- **认证**：python-jose (JWT)
- **密码加密**：passlib + bcrypt
- **缓存**：Redis 7+
- **任务队列**：Celery (可选，用于报告导出)
- **日志**：structlog
- **测试**：pytest + pytest-asyncio

### 7.2 部署架构
```
[用户浏览器]
    ↓
[Nginx (HTTPS, 反向代理)]
    ↓
    ├─→ [Next.js 前端容器] (端口 3000)
    └─→ [FastAPI 后端容器] (端口 8000)
         ↓
         ├─→ [PostgreSQL 容器] (端口 5432)
         ├─→ [Redis 容器] (端口 6379)
         └─→ [外部 AI API] (OpenAI/Kimi)
```

### 7.3 目录结构
```
backend/
├── api/                    # API 路由
│   ├── __init__.py
│   ├── auth.py            # 认证接口
│   ├── profiles.py        # 命盘档案接口
│   ├── bazi.py            # 八字接口
│   ├── ziwei.py           # 紫微接口
│   ├── ai.py              # AI 问答接口
│   ├── analysis.py        # 综合分析接口
│   └── reports.py         # 报告导出接口
├── core/                   # 业务逻辑（复用现有 core/）
├── models/                 # 数据模型（SQLAlchemy）
│   ├── user.py
│   ├── profile.py
│   ├── chart.py
│   └── ai_session.py
├── repositories/           # 数据访问层
│   ├── user_repository.py
│   ├── profile_repository.py
│   └── chart_repository.py
├── services/               # 业务服务层
│   ├── bazi_service.py
│   ├── ziwei_service.py
│   ├── ai_service.py
│   └── export_service.py
├── schemas/                # Pydantic 数据模型
│   ├── user.py
│   ├── profile.py
│   ├── chart.py
│   └── response.py
├── middleware/             # 中间件
│   ├── auth.py
│   └── error_handler.py
├── utils/                  # 工具函数
│   ├── jwt.py
│   ├── password.py
│   └── cache.py
├── config.py               # 配置管理
├── database.py             # 数据库连接
├── main.py                 # 应用入口
├── requirements-backend.txt
└── tests/                  # 测试
    ├── test_auth.py
    ├── test_profiles.py
    └── test_bazi.py
```

---

## 8. 风险与挑战

### 8.1 技术风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI API 稳定性 | 高 | 实现降级方案（本地规则引擎） |
| 数据库迁移丢失 | 高 | 备份 + 数据校验脚本 |
| 性能瓶颈 | 中 | Redis 缓存 + 数据库优化 |
| 前后端协议不匹配 | 中 | TypeScript 类型定义 + API 文档 |

### 8.2 进度风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| AI 问答流式输出复杂 | 中 | 预留 2 天缓冲时间 |
| 前端对接耗时 | 中 | 提前定义 API 契约 |
| 测试覆盖不足 | 低 | 每天完成当天模块测试 |

---

## 9. 验收标准

### 9.1 功能验收
- [ ] 用户可以注册、登录
- [ ] 用户可以创建、查询、更新、删除命盘档案
- [ ] 八字排盘功能正常，数据准确
- [ ] 紫微斗数排盘功能正常，数据准确
- [ ] AI 问答功能正常，支持流式输出
- [ ] 能量分析、五行分析功能正常
- [ ] 年度、月度、日运势分析正常
- [ ] 报告导出功能正常（PDF/Markdown/TXT）
- [ ] 合婚匹配功能正常

### 9.2 性能验收
- [ ] 简单查询响应时间 < 100ms
- [ ] 排盘响应时间 < 500ms
- [ ] AI 问答首字延迟 < 2s
- [ ] 报告导出时间 < 3s
- [ ] 支持 100+ 并发请求

### 9.3 安全验收
- [ ] JWT Token 认证正常
- [ ] HTTPS 加密传输
- [ ] SQL 注入防护
- [ ] XSS 防护
- [ ] CORS 配置正确

### 9.4 文档验收
- [ ] API 文档完整（Swagger）
- [ ] 部署文档清晰
- [ ] 代码注释充分
- [ ] 测试覆盖率 > 80%

---

## 10. 后续优化方向

### 10.1 短期优化（1 个月内）
- 实现用户反馈系统
- 优化 AI 问答准确度
- 增加更多分析维度（事业、财富、健康）
- 实现用户行为埋点

### 10.2 中期优化（3 个月内）
- 实现付费会员体系
- 集成微信/支付宝支付
- 实现社交分享功能
- 开发移动端 App

### 10.3 长期优化（6 个月+）
- 实现多语言支持
- 实现个性化推荐
- 实现命理知识库
- 实现命理师平台

---

## 附录 A：环境变量配置

```bash
# backend/.env.example

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/mingshu
DATABASE_URL_DEV=sqlite:///./data/mingshu.db

# Redis 配置
REDIS_URL=redis://localhost:6379/0

# JWT 配置
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# AI API 配置
OPENAI_API_KEY=sk-...
KIMI_API_KEY=...

# CORS 配置
ALLOWED_ORIGINS=https://mingshu.cloud,http://localhost:3000

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/backend.log

# 环境
ENVIRONMENT=production  # development / production
```

---

## 附录 B：API 请求示例

### B.1 用户登录
```bash
POST /api/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}

Response:
{
  "code": 0,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "expires_in": 86400
  }
}
```

### B.2 创建命盘
```bash
POST /api/profiles
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "name": "张三",
  "gender": "male",
  "calendar_type": "solar",
  "birth_date": "1990-05-15",
  "birth_hour": 14,
  "birth_minute": 30,
  "birth_place": "北京"
}

Response:
{
  "code": 0,
  "data": {
    "id": 123,
    "name": "张三",
    "gender": "male",
    ...
  }
}
```

### B.3 生成八字命盘
```bash
POST /api/bazi/chart
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "profile_id": 123
}

Response:
{
  "code": 0,
  "data": {
    "pillars": {
      "year": { "gan": "庚", "zhi": "午", ... },
      "month": { "gan": "辛", "zhi": "巳", ... },
      "day": { "gan": "丙", "zhi": "辰", ... },
      "hour": { "gan": "甲", "zhi": "午", ... }
    },
    "five_elements": { ... },
    "ten_gods": { ... },
    ...
  }
}
```

---

## 变更日志

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-08-16 | v1.0 | 初始版本，定义需求和开发计划 |

