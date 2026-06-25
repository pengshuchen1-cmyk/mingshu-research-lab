# 命数研究室 视觉改造 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为命数研究室 Streamlit 应用实施淡雅东方调视觉改造，覆盖全部页面

**Architecture:** 通过全局 CSS 模块 (ui/styles.py) 注入设计系统，逐页改造至卡片布局，保留核心逻辑

**Tech Stack:** Streamlit + Altair + Plotly + 自定义 CSS

## Global Constraints

- 所有 CSS 值使用设计文档定义的色值（基底 #F5F0EB，卡片 #FAF7F4，墨色 #3D2B1A，藤黄 #B8860B 等）
- 圆角统一 10px，卡片阴影 `0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)`
- 不修改 core/ 和 report/ 下的引擎/报告逻辑
- 不修改数据库结构
- 不引入新的第三方依赖

---

### Task 1: 创建全局 CSS 模块 ui/styles.py

**Files:**
- Create: `bazi_ziwei_app/ui/styles.py`

**Interfaces:**
- Produces: `get_global_css() -> str` — 返回完整全局 CSS
- Produces: `ELEMENT_COLORS` — 五行色值字典
- Produces: `card_style()` — 卡片 inline style
- Produces: `metric_card_html(title, value, desc)` — 指标卡 HTML
- Produces: `element_tag(element)` — 五行标签 style
- Produces: `info_row(label, value)` — 信息行 HTML

### Task 2: 更新 app.py — 注入 CSS + 合并导航

**Files:**
- Modify: `bazi_ziwei_app/app.py`

从导航中移除 render_useful_god_page，注入全局 CSS，自定义侧边栏标题。

### Task 3: 更新 .streamlit/config.toml

**Files:**
- Modify: `bazi_ziwei_app/.streamlit/config.toml`

添加 theme 配置匹配设计系统。

### Task 4: 首页改造

**Files:**
- Modify: `bazi_ziwei_app/ui/home.py`

用指标卡 + 信息卡替换纯文本功能列表。

### Task 5: 八字排盘页改造 + 数据补全

**Files:**
- Modify: `bazi_ziwei_app/ui/bazi_page.py`

四柱改为 4 列网格卡片，补全藏干/空亡/纳音，总览指标卡化。

### Task 6: 合并五行十神 + 日主喜忌

**Files:**
- Modify: `bazi_ziwei_app/ui/five_element_page.py`

在五行十神页面底部嵌入日主喜忌内容，导入 ELEMENT_COLORS 统一配色。

### Task 7: 综合问盘布局优化

**Files:**
- Modify: `bazi_ziwei_app/ui/inquiry_page.py`

信息分组卡片化。

### Task 8: 大运走势图 (Plotly)

**Files:**
- Create: `bazi_ziwei_app/ui/charts.py`
- Modify: `bazi_ziwei_app/ui/luck_page.py`

创建 charts.py 包含 render_dayun_chart 和 render_yearly_radar 函数，在 luck_page 中插入走势图。

### Task 9: 年度评分雷达图

**Files:**
- Modify: `bazi_ziwei_app/ui/yearly_page.py`

在年度运程页插入 Plotly 雷达图展示各维度评分。

### Task 10: 大运流年页卡片化

**Files:**
- Modify: `bazi_ziwei_app/ui/luck_page.py`

起运信息改为指标卡，阶段色值统一，走势图集成。

### Task 11: 年度运程页卡片化

**Files:**
- Modify: `bazi_ziwei_app/ui/yearly_page.py`

月份卡片化（每行 3-4 张），配色统一。

### Task 12: 紫微斗数页网格化

**Files:**
- Modify: `bazi_ziwei_app/ui/ziwei_page.py`

十二宫位改为 4x3 卡片网格，命宫/身宫高亮。

### Task 13: 其余页面统一风格

**Files:**
- Modify: `bazi_ziwei_app/ui/special_reports_page.py`
- Modify: `bazi_ziwei_app/ui/report_page.py`
- Modify: `bazi_ziwei_app/ui/archive_page.py`
- Modify: `bazi_ziwei_app/ui/settings_page.py`
- Modify: `bazi_ziwei_app/ui/backup_page.py`
- Modify: `bazi_ziwei_app/ui/profile_form.py`

逐页应用卡片布局，由全局 CSS 统一处理样式。

### Task 14: 最终调优

遍历所有页面，检查视觉一致性，确认无残留默认样式。
