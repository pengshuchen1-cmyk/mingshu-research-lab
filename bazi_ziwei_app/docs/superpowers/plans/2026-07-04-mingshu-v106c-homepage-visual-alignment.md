# v1.0.6-C 首页视觉对齐实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将「命数研究室」首页从 Streamlit 工具页质感，调整为接近参考图的黑金 AI 东方玄学产品首页。

**Architecture:** 保持 Python + Streamlit 结构不变，不迁移到 Vue/React。以 `ui/homepage_styles.py` 和 `ui/homepage_components.py` 为首页视觉主入口，减少 Streamlit 原生视觉干扰，建立更接近参考图的宽屏 Landing Page。全局样式只做必要收束，避免影响算法、报告、档案等功能页面。

**Tech Stack:** Python、Streamlit、HTML/CSS、Altair、现有 `shadcn` 设计原则、浏览器截图验收。

## Global Constraints

- 主程序只使用 `http://127.0.0.1:8501`。
- 不重构整个项目。
- 不改命理算法。
- 不新增账号、云端、小程序、会员系统。
- 用户可见文案必须中文为主。
- 禁止绝对化命理表达。
- 首页可以使用演示数据，但必须标注为展示数据，不代表预测准确率承诺。
- 参考图风格：黑金、深蓝黑、东方玄学、AI 科技感、五行轮盘、数据面板、产品官网首页。

---

## 当前差距摘要

1. Streamlit 左侧导航和顶部开发提示仍然暴露，削弱官网质感。
2. 首页存在“左侧原生导航 + 自定义顶部导航 + 金色按钮导航”重复。
3. Hero 首屏没有稳定形成参考图的横向大布局。
4. 五行轮盘细节不足，科技 HUD、星轨、八卦、罗盘层次不够。
5. 金色按钮面积偏大、亮度偏高，色彩统一性不足。
6. 功能卡片图标和边框较简单，不够精致。
7. 数据展示区更像普通卡片，不够像参考图里的产品 Dashboard。
8. 底部 CTA 缺少山水、门洞、星空、远景层次。
9. 部分旧页面内联浅色样式仍需要逐步收束，但本阶段优先首页。

## 所需 Skill 状态

- `shadcn`：已安装，用于设计 token、卡片、按钮、导航、布局规范参考。
- `browser:control-in-app-browser`：已可用，用于 8501 页面截图与视觉验收。
- `test-driven-development`：已可用，用于先写视觉结构测试。
- `verification-before-completion`：已可用，用于完成前跑测试与截图确认。
- `writing-plans`：已使用，用于本计划。
- 不安装 `Chanzhaoyu/chatgpt-web` 为 Codex skill：该仓库是 Vue 项目，不是 skill。若后续需要，可作为交互排版参考，但不直接引入项目依赖。

---

## Task 1: 首页独立展示模式与 Streamlit 干扰收束

**Files:**
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_styles.py`
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/home.py`
- Test: `/Users/uni/Desktop/workspace/bazi_ziwei_app/tests/test_homepage_v106c_visual_alignment.py`

**Interfaces:**
- Consumes: `render_home()` 当前首页入口。
- Produces: 首页专用 CSS 类 `.v106c-homepage-app`, `.v106c-hide-streamlit-chrome`。

- [ ] **Step 1: 写失败测试**

```python
def test_homepage_has_v106c_visual_contract():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    home = (root / "ui" / "home.py").read_text(encoding="utf-8")
    css = (root / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
    assert "v1.0.6-C" in home
    assert ".v106c-homepage-app" in css
    assert "section[data-testid=\"stSidebar\"]" in css
    assert "header[data-testid=\"stHeader\"]" in css
```

- [ ] **Step 2: 运行测试确认失败**

Run:

```bash
cd "/Users/uni/Desktop/workspace/bazi_ziwei_app"
PYTHONPYCACHEPREFIX=/private/tmp/mingshu_pycache .venv/bin/python -m unittest tests.test_homepage_v106c_visual_alignment -v
```

Expected: FAIL，提示缺少 `v1.0.6-C` 或 `.v106c-homepage-app`。

- [ ] **Step 3: 增加首页专用收束样式**

在 `homepage_styles.py` 中新增首页模式样式：

```css
.v106c-homepage-app {
    max-width: 1440px;
    margin: 0 auto;
    color: var(--home-text);
}

body:has(.v106c-homepage-app) section[data-testid="stSidebar"] {
    width: 0 !important;
    min-width: 0 !important;
    transform: translateX(-100%) !important;
    opacity: 0 !important;
    pointer-events: none !important;
}

body:has(.v106c-homepage-app) header[data-testid="stHeader"],
body:has(.v106c-homepage-app) div[data-testid="stToolbar"] {
    display: none !important;
}
```

- [ ] **Step 4: 首页根容器使用新类名**

在 `home.py` 或 `homepage_components.py` 的首页最外层 HTML 增加：

```html
<div class="v106-homepage-shell v106c-homepage-app">
```

- [ ] **Step 5: 跑测试**

Expected: PASS。

## Task 2: 重做 Hero 宽屏结构

**Files:**
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_components.py`
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_styles.py`
- Test: `/Users/uni/Desktop/workspace/bazi_ziwei_app/tests/test_homepage_v106c_visual_alignment.py`

**Interfaces:**
- Consumes: `render_hero()`。
- Produces: `.v106c-hero-grid` 三栏结构：左文案、中轮盘、右数据卡。

- [ ] **Step 1: 写失败测试**

```python
def test_homepage_hero_matches_reference_structure():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    comp = (root / "ui" / "homepage_components.py").read_text(encoding="utf-8")
    css = (root / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
    assert "v106c-hero-grid" in comp
    assert "v106c-hero-copy" in comp
    assert "v106c-orbit-stage" in comp
    assert "v106c-side-panels" in comp
    assert "grid-template-columns: minmax(360px, 0.95fr) minmax(420px, 1.12fr) minmax(220px, 0.55fr)" in css
```

- [ ] **Step 2: 将 Hero 结构固定为三栏**

左侧：

```html
<div class="v106c-hero-copy">
  <div class="v106c-vertical-words">知命 · 趋势 · 行运</div>
  <div class="v106c-lab-label">AI ORIENTAL RESEARCH LAB</div>
  <h1 class="v106-hero-title v106c-title">AI命数研究室</h1>
  <div class="v106-hero-subtitle">古法智慧 × 现代算法 × 数据洞察</div>
  <p class="v106-hero-text">融合八字、紫微斗数与五行体系，结合结构化算法与现实事件库，为你提供可解释的命理趋势参考。</p>
</div>
```

中间：

```html
<div class="v106c-orbit-stage">
  <!-- 复用并增强五行轮盘 -->
</div>
```

右侧：

```html
<div class="v106c-side-panels">
  <!-- AI命理分析引擎 + 趋势概览 -->
</div>
```

- [ ] **Step 3: 桌面优先，移动端再堆叠**

CSS:

```css
.v106c-hero-grid {
    display: grid;
    grid-template-columns: minmax(360px, 0.95fr) minmax(420px, 1.12fr) minmax(220px, 0.55fr);
    gap: 28px;
    align-items: center;
}

@media (max-width: 1100px) {
    .v106c-hero-grid {
        grid-template-columns: 1fr;
    }
}
```

## Task 3: 精修五行轮盘与参考图层次

**Files:**
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_components.py`
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_styles.py`
- Test: `/Users/uni/Desktop/workspace/bazi_ziwei_app/tests/test_homepage_v106c_visual_alignment.py`

**Interfaces:**
- Produces: `.v106c-orbit-ring`, `.v106c-orbit-bagua`, `.v106c-orbit-lines`, `.v106c-star-map`。

- [ ] **Step 1: 写失败测试**

```python
def test_orbit_has_reference_visual_layers():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    comp = (root / "ui" / "homepage_components.py").read_text(encoding="utf-8")
    for cls in ["v106c-orbit-ring", "v106c-orbit-bagua", "v106c-orbit-lines", "v106c-star-map"]:
        assert cls in comp
```

- [ ] **Step 2: 增加轮盘层**

轮盘 HTML 中加入：

```html
<div class="v106c-star-map"></div>
<div class="v106c-orbit-ring ring-1"></div>
<div class="v106c-orbit-ring ring-2"></div>
<div class="v106c-orbit-ring ring-3"></div>
<div class="v106c-orbit-lines"></div>
<div class="v106c-orbit-bagua">☰ ☱ ☲ ☳ ☴ ☵ ☶ ☷</div>
```

- [ ] **Step 3: 降低五行发光饱和度**

不要使用大面积高饱和红绿蓝。五行节点只做边缘光和文字点缀。

## Task 4: 功能卡片区对齐参考图

**Files:**
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_components.py`
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_styles.py`
- Test: `/Users/uni/Desktop/workspace/bazi_ziwei_app/tests/test_homepage_v106c_visual_alignment.py`

**Interfaces:**
- Produces: 6 张 `.v106c-feature-card`，保持真实跳转按钮。

- [ ] **Step 1: 写失败测试**

```python
def test_feature_cards_use_reference_grid_and_click_targets():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    comp = (root / "ui" / "homepage_components.py").read_text(encoding="utf-8")
    css = (root / "ui" / "homepage_styles.py").read_text(encoding="utf-8")
    for name in ["八字排盘", "紫微斗数", "命盘总览", "年度运程", "流月断事", "命理报告导出"]:
        assert name in comp
    assert ".v106c-feature-grid" in css
    assert "grid-template-columns: repeat(6, minmax(0, 1fr))" in css
```

- [ ] **Step 2: 卡片统一尺寸**

```css
.v106c-feature-grid {
    display: grid;
    grid-template-columns: repeat(6, minmax(0, 1fr));
    gap: 14px;
}
.v106c-feature-card {
    min-height: 198px;
    border-radius: 14px;
    background: linear-gradient(180deg, rgba(13, 24, 29, .92), rgba(7, 13, 18, .96));
}
```

## Task 5: 数据 Dashboard 对齐参考图

**Files:**
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_components.py`
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_styles.py`
- Test: `/Users/uni/Desktop/workspace/bazi_ziwei_app/tests/test_homepage_v106c_visual_alignment.py`

**Interfaces:**
- Produces: `.v106c-dashboard`, `.v106c-energy-donut`, `.v106c-score-ring`, `.v106c-trend-chart`。

- [ ] **Step 1: 写失败测试**

```python
def test_dashboard_has_reference_widgets():
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    comp = (root / "ui" / "homepage_components.py").read_text(encoding="utf-8")
    for cls in ["v106c-energy-donut", "v106c-score-ring", "v106c-trend-chart", "v106c-luck-card", "v106c-pattern-card"]:
        assert cls in comp
```

- [ ] **Step 2: 数据区变成一个大面板内部网格**

让五行能量、评分、趋势、大运、格局都在同一个暗色大面板里，而不是散落卡片。

## Task 6: 底部 CTA 东方意境增强

**Files:**
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_components.py`
- Modify: `/Users/uni/Desktop/workspace/bazi_ziwei_app/ui/homepage_styles.py`

**Interfaces:**
- Produces: `.v106c-footer-gate`, `.v106c-mountain-layer`, `.v106c-bottom-cta`。

- [ ] **Step 1: 增加底部视觉层**

使用 CSS 渐变和伪元素模拟山水、门洞、星光，不引入重型图片依赖。

```css
.v106c-bottom-cta::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
      radial-gradient(circle at 18% 52%, rgba(216,185,106,.22), transparent 18%),
      linear-gradient(180deg, transparent 35%, rgba(3,8,12,.92) 100%);
}
```

## Task 7: 浏览器截图验收与回归测试

**Files:**
- Create: `/Users/uni/Desktop/workspace/bazi_ziwei_app/docs/reports/homepage_v106c_visual_check.md`
- Test: `/Users/uni/Desktop/workspace/bazi_ziwei_app/tests/test_homepage_v106c_visual_alignment.py`

- [ ] **Step 1: 跑单测**

```bash
cd "/Users/uni/Desktop/workspace/bazi_ziwei_app"
PYTHONPYCACHEPREFIX=/private/tmp/mingshu_pycache .venv/bin/python -m unittest tests.test_homepage_v106c_visual_alignment -v
```

- [ ] **Step 2: 跑相关视觉测试**

```bash
PYTHONPYCACHEPREFIX=/private/tmp/mingshu_pycache .venv/bin/python -m unittest tests.test_homepage_v106 tests.test_visual_home_and_report_cards tests.test_shadcn_visual_system_v106b tests.test_homepage_v106c_visual_alignment -v
```

- [ ] **Step 3: 跑编译**

```bash
PYTHONPYCACHEPREFIX=/private/tmp/mingshu_pycache .venv/bin/python -m compileall ui/home.py ui/homepage_components.py ui/homepage_styles.py tests/test_homepage_v106c_visual_alignment.py
```

- [ ] **Step 4: 浏览器截图验收**

打开：

```text
http://127.0.0.1:8501/?v=v106c-homepage
```

验收标准：

- 首页不出现 Streamlit 左侧导航。
- 首页不出现 `File change / Rerun / Always rerun`。
- 首屏形成左文案、中轮盘、右数据卡横向结构。
- 六大功能卡片一排展示。
- 数据 Dashboard 与参考图布局接近。
- 底部 CTA 有东方意境收束。

## 不做事项

- 不把项目改成 Vue/React。
- 不直接引入 `chatgpt-web` 项目代码。
- 不改八字、紫微、流月算法。
- 不删除现有功能页面。
- 不新增复杂图片依赖。

## 执行建议

建议按 Task 1 到 Task 7 顺序执行。每完成一个 Task 都截图一次，避免最后才发现整体方向偏了。

