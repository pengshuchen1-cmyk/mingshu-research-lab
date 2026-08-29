# 首页功能团队分工计划

## 团队成员
- **老板**（产品 + 项目管理）
- **前端工程师** × 1
- **后端工程师** × 1

---

## 一、老板职责

### 1.1 产品设计与需求定义
- ✅ **已完成**：UI 设计稿（首页）
- [ ] 审核 API 接口设计是否符合产品需求
- [ ] 定义各功能模块的优先级
- [ ] 制定验收标准

### 1.2 项目管理
- [ ] 制定项目时间表（建议 2-3 周完成首页）
- [ ] 协调前后端开发进度
- [ ] 组织每日站会（15 分钟）
- [ ] 跟踪任务完成情况
- [ ] 解决开发过程中的阻塞问题

### 1.3 质量把控
- [ ] 每日验收已完成的功能模块
- [ ] UI/UX 细节审查
- [ ] 用户体验测试
- [ ] Bug 优先级判定

### 1.4 业务逻辑确认
- [ ] 确认"能量值"的计算规则
- [ ] 确认"月度关键词"的生成逻辑
- [ ] 确认 AI 建议的内容策略
- [ ] 确认会员权益展示方式

### 1.5 数据准备（可选）
- [ ] 准备测试用户数据
- [ ] 准备示例命盘数据
- [ ] 提供 AI 建议的文案模板

---

## 二、后端工程师职责

### 2.1 基础架构搭建（Day 1-2）

**任务**：
- [ ] 初始化 FastAPI 项目
- [ ] 配置数据库连接（SQLite → PostgreSQL）
- [ ] 配置 Redis 缓存
- [ ] 实现健康检查接口 `/api/health`
- [ ] 配置 CORS、日志、环境变量
- [ ] 编写 `README.md` 和部署文档

**交付物**：
```
backend/
├── main.py                  # FastAPI 入口
├── config.py                # 配置管理
├── database.py              # 数据库连接
├── requirements-backend.txt # 依赖清单
└── README.md               # 项目文档
```

**验收标准**：
- FastAPI 服务启动成功（`http://localhost:8000`）
- 健康检查接口返回正常
- 数据库连接测试通过
- Swagger 文档可访问（`http://localhost:8000/docs`）

---

### 2.2 用户认证模块（Day 3）

**任务**：
- [ ] 创建 User 数据模型（SQLAlchemy）
- [ ] 实现用户注册接口 `POST /api/auth/register`
- [ ] 实现用户登录接口 `POST /api/auth/login`（JWT）
- [ ] 实现 Token 刷新接口 `POST /api/auth/refresh`
- [ ] 实现 JWT 中间件
- [ ] 配置密码加密（bcrypt）
- [ ] 编写单元测试

**交付物**：
```python
# API 端点
POST /api/auth/register
POST /api/auth/login
POST /api/auth/refresh
GET /api/user/profile
```

**验收标准**：
- 用户可以注册、登录
- JWT Token 正确签发和验证
- 密码加密存储
- Postman 测试通过

---

### 2.3 首页数据 API（Day 4-7）

#### 2.3.1 今日能量值 API（Day 4 上午）

**任务**：
- [ ] 封装 `core/life_assessment.py` 为 Service 层
- [ ] 实现 `GET /api/dashboard/daily-energy` 接口
- [ ] 计算综合能量分数（82/100）
- [ ] 计算四维评分（事业、财富、情感、健康）
- [ ] 实现 Redis 缓存（1 小时）

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "energy_score": 82,
    "max_score": 100,
    "dimensions": [
      { "name": "事业", "score": 80, "icon": "💼" },
      { "name": "财富", "score": 70, "icon": "💰" },
      { "name": "情感", "score": 85, "icon": "💕" },
      { "name": "健康", "score": 78, "icon": "🌿" }
    ]
  }
}
```

**验收标准**：
- 能量分数计算正确
- 响应时间 < 200ms
- 缓存命中率 > 80%

---

#### 2.3.2 本月关键词 API（Day 4 下午）

**任务**：
- [ ] 封装 `core/monthly_engine.py`
- [ ] 实现 `GET /api/dashboard/monthly-keywords` 接口
- [ ] 生成月度关键词（3 个）
- [ ] 生成关键词描述

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "keywords": ["主动", "合作", "收获"],
    "descriptions": [
      "把握时机，精确行动",
      "贵人运旺，共赢可期",
      "成果可见，机会把握"
    ]
  }
}
```

---

#### 2.3.3 年度趋势 API（Day 5 上午）

**任务**：
- [ ] 封装 `core/yearly_engine.py`
- [ ] 实现 `GET /api/dashboard/annual-trend` 接口
- [ ] 计算年度趋势（上升/下降）
- [ ] 计算趋势百分比

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "trend_type": "上升年",
    "trend_percent": 75,
    "description": "运势提升，持续上升"
  }
}
```

---

#### 2.3.4 12 个月流月总览 API（Day 5 下午）

**任务**：
- [ ] 封装 `core/monthly_engine.py` + `core/luck_engine.py`
- [ ] 实现 `GET /api/dashboard/yearly-calendar` 接口
- [ ] 生成全年 12 个月运势数据
- [ ] 分配运势等级和表情图标

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "months": [
      { "month": 1, "status": "平稳", "emoji": "😊", "score": 70 },
      { "month": 2, "status": "上升", "emoji": "😄", "score": 80 },
      ...
    ]
  }
}
```

---

#### 2.3.5 月度运势详情 API（Day 6 上午）

**任务**：
- [ ] 实现 `GET /api/dashboard/monthly-detail` 接口
- [ ] 计算五维星级评分（综合、事业、财富、情感、健康）
- [ ] 生成月度标题和图标

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "month": 7,
    "title": "大吉月",
    "emoji": "😍",
    "ratings": [
      { "dimension": "综合", "stars": 5 },
      { "dimension": "事业", "stars": 4 }
    ]
  }
}
```

---

#### 2.3.6 八字四柱 API（Day 6 下午）

**任务**：
- [ ] 封装 `core/bazi_engine.py`
- [ ] 实现 `GET /api/dashboard/bazi-pillars` 接口
- [ ] 提取四柱简要信息（天干地支 + 五行）

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "pillars": {
      "year": { "gan": "甲", "zhi": "申", "element": "金" },
      "month": { "gan": "辛", "zhi": "卯", "element": "木" }
    }
  }
}
```

---

#### 2.3.7 年度运势总述 API（Day 7 上午）

**任务**：
- [ ] 实现 `GET /api/dashboard/annual-summary` 接口
- [ ] 计算年度总评分
- [ ] 计算四维评分（事业、财富、情感、健康）

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "year": 2024,
    "total_score": 75,
    "dimensions": [
      { "name": "事业", "score": 78 },
      { "name": "财富", "score": 72 }
    ]
  }
}
```

---

#### 2.3.8 五行分布 API（Day 7 下午）

**任务**：
- [ ] 封装 `core/five_elements.py`
- [ ] 实现 `GET /api/dashboard/wuxing-distribution` 接口
- [ ] 计算五行百分比

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "wuxing": [
      { "element": "木", "percent": 15, "color": "#22c55e" },
      { "element": "火", "percent": 35, "color": "#ef4444" }
    ]
  }
}
```

---

#### 2.3.9 AI 建议卡片 API（Day 8 上午）

**任务**：
- [ ] 封装 `core/popular_advice_engine.py`
- [ ] 实现 `GET /api/dashboard/ai-advice` 接口
- [ ] 生成四个维度的建议（事业、财运、感情、健康）

**响应格式**：
```json
{
  "code": 0,
  "data": {
    "advices": [
      {
        "category": "事业建议",
        "icon": "💼",
        "summary": "把握下午黄金时段"
      }
    ]
  }
}
```

---

### 2.4 首页聚合 API（Day 8 下午）⭐️ **重点**

**任务**：
- [ ] 创建 `backend/services/dashboard_service.py`
- [ ] 实现 `GET /api/dashboard/home` 聚合接口
- [ ] 并行调用所有子接口
- [ ] 统一返回所有首页数据
- [ ] 优化性能（总响应时间 < 1s）

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
    "ai_advice": { ... }
  }
}
```

**验收标准**：
- 一次请求返回所有首页数据
- 响应时间 < 1s
- 数据完整性 100%

---

### 2.5 AI 对话 API（Day 9-10）

**任务**：
- [ ] 封装 `core/ai_orchestrator.py`
- [ ] 实现 `POST /api/ai/chat` 接口（同步）
- [ ] 实现 `WS /ws/ai/chat` 接口（WebSocket 流式）
- [ ] 实现 `GET /api/ai/chat/history` 接口
- [ ] 实现 `POST /api/ai/chat/session` 接口
- [ ] 实现 `GET /api/ai/quick-questions` 接口

**验收标准**：
- AI 对话功能正常
- 流式输出流畅
- 首字延迟 < 2s

---

### 2.6 文档与测试（Day 11-12）

**任务**：
- [ ] 完善 API 文档（Swagger）
- [ ] 编写单元测试（覆盖率 > 80%）
- [ ] 编写集成测试
- [ ] 性能测试（压测）
- [ ] 编写部署文档

---

## 三、前端工程师职责

### 3.1 组件开发（Day 1-7）

#### 3.1.1 基础组件（Day 1-2）

**任务**：
- [ ] 配置 API 基础 URL
- [ ] 封装 Axios 请求库
- [ ] 实现 Token 管理（localStorage）
- [ ] 实现统一错误处理
- [ ] 实现 Loading 状态组件
- [ ] 实现 Toast 提示组件

**交付物**：
```
frontend/src/
├── lib/
│   ├── api-client.ts      # Axios 封装
│   ├── auth.ts            # Token 管理
│   └── error-handler.ts   # 错误处理
└── components/
    ├── loading.tsx        # Loading 组件
    └── toast.tsx          # Toast 组件
```

**验收标准**：
- API 请求正常
- Token 自动刷新
- 错误提示友好

---

#### 3.1.2 今日能量值卡片（Day 3 上午）

**任务**：
- [ ] 调用 `GET /api/dashboard/daily-energy` API
- [ ] 渲染能量分数（82/100）
- [ ] 渲染四维评分（事业、财富、情感、健康）
- [ ] 实现动画效果（数字滚动、进度条）
- [ ] 实现响应式布局

**组件路径**：
```
frontend/src/components/dashboard/energy-score-card.tsx
```

**验收标准**：
- 数据展示正确
- 动画流畅
- 移动端适配

---

#### 3.1.3 本月关键词卡片（Day 3 下午）

**任务**：
- [ ] 调用 `GET /api/dashboard/monthly-keywords` API
- [ ] 渲染关键词（主动·合作·收获）
- [ ] 渲染描述文字
- [ ] 实现卡片悬停效果

**组件路径**：
```
frontend/src/components/dashboard/monthly-keywords-card.tsx
```

---

#### 3.1.4 运势趋势卡片（Day 4 上午）

**任务**：
- [ ] 调用 `GET /api/dashboard/annual-trend` API
- [ ] 渲染趋势类型（上升年/下降年）
- [ ] 渲染百分比（75%）
- [ ] 实现环形进度条

**组件路径**：
```
frontend/src/components/dashboard/annual-trend-card.tsx
```

---

#### 3.1.5 用户信息卡片（Day 4 下午）

**任务**：
- [ ] 调用 `GET /api/user/profile` API
- [ ] 渲染用户头像、昵称
- [ ] 渲染生日、会员身份
- [ ] 实现用户菜单（下拉）

**组件路径**：
```
frontend/src/components/dashboard/profile-card.tsx
```

---

#### 3.1.6 AI 对话卡片（Day 5）

**任务**：
- [ ] 调用 `WS /ws/ai/chat` WebSocket API
- [ ] 实现对话气泡组件
- [ ] 实现流式输出动画（打字机效果）
- [ ] 实现快捷问题按钮
- [ ] 实现输入框和发送按钮
- [ ] 实现语音输入（可选）

**组件路径**：
```
frontend/src/components/dashboard/ai-chat-card.tsx
```

**验收标准**：
- WebSocket 连接稳定
- 流式输出流畅
- 对话历史滚动正常

---

#### 3.1.7 12 个月流月总览卡片（Day 6）

**任务**：
- [ ] 调用 `GET /api/dashboard/yearly-calendar` API
- [ ] 渲染 12 个月网格
- [ ] 渲染每月表情图标
- [ ] 渲染每月运势状态
- [ ] 实现月份点击事件（跳转详情）

**组件路径**：
```
frontend/src/components/dashboard/month-overview-card.tsx
```

---

#### 3.1.8 月度运势详情卡片（Day 7 上午）

**任务**：
- [ ] 调用 `GET /api/dashboard/monthly-detail` API
- [ ] 渲染月份标题和图标
- [ ] 渲染五维星级评分
- [ ] 实现星级动画

**组件路径**：
```
frontend/src/components/dashboard/monthly-detail-card.tsx
```

---

#### 3.1.9 八字四柱卡片（Day 7 下午）

**任务**：
- [ ] 调用 `GET /api/dashboard/bazi-pillars` API
- [ ] 渲染四柱（年月日时）
- [ ] 渲染天干地支
- [ ] 实现点击跳转详情

**组件路径**：
```
frontend/src/components/dashboard/bazi-chart-card.tsx
```

---

#### 3.1.10 年度运势总述卡片（Day 8 上午）

**任务**：
- [ ] 调用 `GET /api/dashboard/annual-summary` API
- [ ] 渲染环形进度图（75/100）
- [ ] 渲染四维评分柱状图
- [ ] 实现图表动画（Recharts）

**组件路径**：
```
frontend/src/components/dashboard/yearly-overview-card.tsx
```

---

#### 3.1.11 五行分布卡片（Day 8 下午）

**任务**：
- [ ] 调用 `GET /api/dashboard/wuxing-distribution` API
- [ ] 渲染五行饼图
- [ ] 实现饼图动画
- [ ] 实现悬停提示

**组件路径**：
```
frontend/src/components/dashboard/wuxing-charts-card.tsx
```

---

#### 3.1.12 AI 建议卡片（Day 9）

**任务**：
- [ ] 调用 `GET /api/dashboard/ai-advice` API
- [ ] 渲染四个建议卡片（事业、财运、感情、健康）
- [ ] 实现卡片悬停效果
- [ ] 实现"查看详情"链接

**组件路径**：
```
frontend/src/components/dashboard/advice-cards.tsx
```

---

### 3.2 页面集成（Day 10）

**任务**：
- [ ] 调用 `GET /api/dashboard/home` 聚合 API
- [ ] 集成所有卡片组件到首页
- [ ] 实现响应式布局（移动端/桌面端）
- [ ] 实现骨架屏 Loading 效果
- [ ] 优化首屏加载速度

**页面路径**：
```
frontend/src/app/page.tsx
```

**验收标准**：
- 首屏加载时间 < 2s
- 所有卡片数据正常
- 移动端适配完美
- 无明显卡顿

---

### 3.3 交互优化（Day 11）

**任务**：
- [ ] 实现页面滚动动画
- [ ] 实现卡片进入动画
- [ ] 实现数据刷新动画
- [ ] 实现下拉刷新（移动端）
- [ ] 优化触摸体验（移动端）

---

### 3.4 测试与 Bug 修复（Day 12）

**任务**：
- [ ] 浏览器兼容性测试（Chrome、Safari、Firefox）
- [ ] 移动端测试（iOS、Android）
- [ ] 性能测试（Lighthouse）
- [ ] Bug 修复
- [ ] 代码优化

---

## 四、协作流程

### 4.1 每日站会（15 分钟）
**时间**：每天上午 10:00  
**参与人员**：老板 + 前端 + 后端  
**内容**：
1. 昨天完成了什么
2. 今天计划做什么
3. 遇到了什么阻塞

---

### 4.2 API 对接流程

**Step 1：后端先行**（Day 1-8）
- 后端完成 API 开发
- 后端使用 Postman 测试
- 后端更新 Swagger 文档

**Step 2：前端对接**（Day 3-10）
- 前端查看 Swagger 文档
- 前端调用 API
- 前端反馈 API 问题（如有）

**Step 3：联调**（Day 10-11）
- 前后端共同调试
- 修复对接问题
- 优化性能

---

### 4.3 代码审查

**后端代码审查**（老板负责）：
- 每天下班前审查当天代码
- 检查代码规范
- 检查性能优化

**前端代码审查**（老板负责）：
- 每天下班前审查当天代码
- 检查 UI 还原度
- 检查交互体验

---

### 4.4 版本管理

**分支策略**：
```
main          # 生产环境
├── develop   # 开发环境
    ├── feature/backend-dashboard   # 后端首页功能
    └── feature/frontend-homepage   # 前端首页
```

**提交规范**：
```
feat: 实现今日能量值 API
fix: 修复月度关键词计算错误
style: 优化 AI 对话卡片样式
docs: 更新 API 文档
```

---

## 五、时间表（12 天完成首页）

| 天数 | 后端任务 | 前端任务 | 老板任务 |
|------|---------|---------|---------|
| **Day 1** | 搭建 FastAPI 项目 | 配置 API 请求库 | 审核 API 设计 |
| **Day 2** | 完成基础架构 | 开发基础组件 | 制定时间表 |
| **Day 3** | 实现用户认证 API | 开发能量值卡片 + 关键词卡片 | 每日验收 |
| **Day 4** | 实现能量值 + 关键词 API | 开发趋势卡片 + 用户卡片 | 每日验收 |
| **Day 5** | 实现年度趋势 + 流月总览 API | 开发 AI 对话卡片 | 每日验收 |
| **Day 6** | 实现月度详情 + 八字四柱 API | 开发流月总览卡片 | 每日验收 |
| **Day 7** | 实现年度总述 + 五行分布 API | 开发月度详情 + 八字卡片 | 每日验收 |
| **Day 8** | 实现 AI 建议 + 聚合 API | 开发年度总述 + 五行卡片 | 每日验收 |
| **Day 9** | 实现 AI 对话 API（同步） | 开发 AI 建议卡片 | 每日验收 |
| **Day 10** | 实现 AI 对话 API（流式） | 页面集成 | 全面测试 |
| **Day 11** | Bug 修复 + 性能优化 | 交互优化 | Bug 优先级排序 |
| **Day 12** | 文档完善 + 部署准备 | 测试 + Bug 修复 | 最终验收 |

---

## 六、交付物清单

### 6.1 后端交付物
- [ ] FastAPI 项目（完整代码）
- [ ] API 文档（Swagger）
- [ ] 数据库迁移脚本
- [ ] 单元测试（覆盖率 > 80%）
- [ ] 部署文档
- [ ] Postman Collection

### 6.2 前端交付物
- [ ] Next.js 项目（完整代码）
- [ ] 所有 UI 组件
- [ ] 首页集成
- [ ] 移动端适配
- [ ] 性能优化报告（Lighthouse）

### 6.3 老板交付物
- [ ] 产品验收报告
- [ ] Bug 列表及优先级
- [ ] 下一阶段计划

---

## 七、风险管理

### 7.1 技术风险

| 风险 | 影响 | 负责人 | 缓解措施 |
|------|------|--------|----------|
| AI API 不稳定 | 高 | 后端 | 实现本地降级方案 |
| WebSocket 连接问题 | 中 | 后端 + 前端 | 实现自动重连 |
| 首屏加载慢 | 中 | 前端 + 后端 | 实现聚合 API + 缓存 |
| 数据计算耗时 | 中 | 后端 | Redis 缓存 + 异步计算 |

### 7.2 进度风险

| 风险 | 影响 | 负责人 | 缓解措施 |
|------|------|--------|----------|
| 后端进度延迟 | 高 | 老板 | 前端使用 Mock 数据先行开发 |
| 前端进度延迟 | 中 | 老板 | 后端协助前端调试 |
| API 对接问题 | 中 | 老板 | 每天联调 1 小时 |

---

## 八、沟通工具

**推荐工具栈**：
- **项目管理**：Notion / Trello / 飞书文档
- **即时通讯**：微信群 / 钉钉群 / Slack
- **代码管理**：GitHub / GitLab
- **API 测试**：Postman
- **设计稿**：Figma / Sketch
- **Bug 追踪**：GitHub Issues / 飞书任务

---

## 九、验收标准

### 9.1 功能验收
- [ ] 所有 11 个功能卡片正常展示
- [ ] 数据准确性 100%
- [ ] AI 对话功能正常
- [ ] 响应式布局完美
- [ ] 无严重 Bug

### 9.2 性能验收
- [ ] 首屏加载时间 < 2s
- [ ] API 响应时间 < 1s
- [ ] Lighthouse 性能分数 > 90
- [ ] 移动端流畅度 > 60 FPS

### 9.3 体验验收
- [ ] UI 还原度 > 95%
- [ ] 动画流畅
- [ ] 交互友好
- [ ] 错误提示清晰

---

## 十、下一阶段计划

首页完成后，按优先级开发：
1. **AI 聊天页面**（独立页面）
2. **流月日历页面**（详细视图）
3. **命盘分析页面**（八字详情 + 紫微详情）
4. **人生趋势页面**（大运流年）
5. **记忆档案页面**（命盘管理）
6. **命数工具页面**（工具集）
7. **知识库页面**（命理知识）
8. **设置页面**（用户设置 + 反馈）

---

**制定人**：Kiro  
**制定日期**：2026-08-16  
**版本**：v1.0
