# 命数研究室 — 项目档案

> 生成日期：2026-06-27
> 当前版本：v1.2-F-Fix
> 服务地址：http://127.0.0.1:8501
> 代码总量：118 个文件（34 core + 22 rules + 23 tests + 19 ui + 13 report + 7 utils）
> 测试总数：145 个测试函数

---

## 一、项目概述

命数研究室是一个本机离线运行的八字 + 紫微斗数命理分析工具，基于 Python + Streamlit + SQLite + JSON 规则库 + lunar_python。不上传数据，不需要账号。

**核心理念：**
- 所有判断必须基于真实命盘数据，不使用通用模板
- 禁用绝对化断言（禁止词：必定、绝对、注定、一定发财、一定离婚、必有灾等）
- 不伪造未实现算法
- 报告为趋势参考，不是绝对预测

---

## 二、版本历史

| 版本 | 里程碑 |
|------|--------|
| v0.1 | 基础 Streamlit 应用、八字排盘、本地保存 |
| v0.2 | 日主强弱、喜忌初判、基础报告增强 |
| v0.3 | 大运流年、Markdown/TXT 导出、命盘档案增强 |
| v0.4 | 年度运程、12 个月流月、PDF 友好导出 |
| v0.4.2 | 报告有效性检查、年度深度化、流月事件化 |
| v1.0 | 专项报告、规则库系统化、紫微基础盘、备份、设置、日志 |
| v1.1-A | 八字典籍依据化，source_registry，所有规则加 source_ids/basis/school/confidence |
| v1.1-A2 | 命盘总体结论引擎（财富/桃花/健康/事业四维评分），命盘总览页面 |
| v1.2-A | 紫微参考源（5本典籍）注册，6个紫微规则文件，紫微命盘名片引擎 |
| v1.2-B | 紫微差异化修复（fingerprint），十四主星落宫算法，三方四正基础 |
| v1.2-C | 生年四化引擎，三方四正深化 |
| v1.2-D | 辅星/煞星数据结构（24颗星），紫微页面 6 Tab 重构 |
| v1.2-D-Polish | 紫微 CSS + 卡片化 UI，修复 styles.py CSS 裸露 Bug |
| v1.2-E | 辅星落宫算法（文昌/文曲/左辅/右弼），煞星落宫算法（擎羊/陀罗/火星/铃星/地空/地劫），大限基础结构引擎 |
| v1.2-F | 紫微综合报告增强 + 流月大概率事件推断引擎 + 五行结构深度报告 |
| v1.2-F-Fix | 统一 8501 端口、流月事件差异化修复、UI 格式化展示修复 |

---

## 三、页面导航（15 页）

| 序号 | 页面 | 文件 | 功能 |
|------|------|------|------|
| 1 | 首页 | `ui/home.py` | 欢迎页、快捷导航 |
| 2 | 新建命盘 | `ui/profile_form.py` | 输入姓名/性别/出生日期时间地点 |
| 3 | 八字排盘 | `ui/bazi_page.py` | 四柱、五行统计、日主强弱、十神分析 |
| 4 | 命盘总览 | `ui/life_overview_page.py` | 财富/桃花/健康/事业四维评分 |
| 5 | 综合问盘 | `ui/inquiry_page.py` | 五行能量轮盘、综合问答 |
| 6 | 五行喜忌 | `ui/five_element_page.py` | 五行结构深度报告、各五行详情卡片 |
| 7 | 大运流年 | `ui/luck_page.py` | 大运阶段详情 |
| 8 | 年度运程 | `ui/yearly_page.py` | 年度概要、12 个月流月分析、大概率事件 |
| 9 | 专项报告 | `ui/special_reports_page.py` | 事业/财运/婚恋专项报告 |
| 10 | 紫微斗数 | `ui/ziwei_page.py` | 6 Tab：命盘名片/十二宫盘/主星速查/重点宫位/三方四正/参考依据 |
| 11 | 报告导出 | `ui/report_page.py` | 综合报告 Markdown/TXT/PDF 导出 |
| 12 | 命盘档案 | `ui/archive_page.py` | 命盘保存、搜索、编辑、删除 |
| 13 | 合婚匹配 | `ui/compatibility_page.py` | 双人八字合婚 |
| 14 | 数据备份 | `ui/backup_page.py` | JSON 导出/导入、SQLite 备份 |
| 15 | 设置 | `ui/settings_page.py` | 错误日志、报告质量检查 |

---

## 四、核心架构（4 层）

### 4.1 引擎层 `core/`（34 文件）

**八字核心：**
- `bazi_engine.py` — 八字排盘入口
- `bazi_constants.py` — 天干地支五行藏干等常量
- `five_elements.py` — 五行权重统计
- `strength_engine.py` — 日主强弱判断（得令/得地/得势）
- `ten_gods.py` — 十神关系
- `branch_relations.py` — 地支六冲/三合/六合/刑/害/破
- `monthly_engine.py` — 12 个月流月分析
- `yearly_engine.py` — 年度运程
- `luck_engine.py` — 大运流年
- `enhanced_monthly_engine.py` — 增强版流月（方向/事件/建议）
- `calendar_engine.py` — 农历/节气转换
- `chart_fingerprint.py` — 命盘差异化特征
- `chart_type.py` — 命局类型判断
- `compatibility.py` — 合婚匹配

**命局总论：**
- `life_overview_engine.py` — 财富/桃花/健康/事业四维评分
- `life_assessment.py` — 命局总论
- `romance_star_engine.py` — 桃花星检测

**紫微斗数：**
- `ziwei_engine.py` — 紫微基础排盘 + 主星集成
- `ziwei_star_engine.py` — 十四主星落宫算法（五虎遁 + 纳音 + 紫微系 + 天府系）
- `ziwei_sihua_engine.py` — 生年四化引擎
- `ziwei_triangle_engine.py` — 三方四正
- `ziwei_fingerprint.py` — 紫微差异化特征
- `ziwei_life_card_engine.py` — 紫微命盘名片
- `ziwei_minor_star_engine.py` — 辅星落宫（文昌/文曲/左辅/右弼）
- `ziwei_fierce_star_engine.py` — 煞星落宫（擎羊/陀罗/火星/铃星/地空/地劫）
- `ziwei_daxian_engine.py` — 大限基础结构
- `ziwei_constants.py` — 星曜常量、24星含义

**事件推断：**
- `monthly_event_inference_engine.py` — 流月大概率事件推断（十神事件池 + 地支冲击 + 严格条件 + 后处理）

### 4.2 页面层 `ui/`（19 文件）

- 15 个页面文件（见"页面导航"表）
- `styles.py` — 全局 CSS（淡雅东方色调：墨色/米白/藤黄/朱砂/淡金）
- `charts.py` — 五行轮盘 SVG
- `ziwei_components.py` — 紫微组件库（主星/辅星/煞星标签、大限卡片、重点宫位卡片）

### 4.3 报告层 `report/`（13 文件）

- `bazi_report.py` — 八字报告
- `export_report.py` — 综合导出报告（Markdown/TXT/PDF）
- `five_element_deep_report.py` — 五行结构深度报告
- `life_overview_report.py` — 命盘总览报告
- `useful_god_report.py` — 喜用五行细化解释
- `ziwei_report.py` — 紫微综合报告
- `ziwei_life_card_report.py` — 紫微命盘名片报告
- `career_report.py` / `wealth_report.py` / `love_report.py` — 专项报告
- `narrative_engine.py` — 叙事引擎
- `special_report_common.py` — 专项报告公共模块

### 4.4 规则层 `rules/`（22 JSON 文件）

**八字规则（12 个）：**
- `source_registry.json` — 参考书注册表
- `ten_god_rules.json` / `five_element_rules.json` / `useful_god_rules.json`
- `yearly_rules.json` / `monthly_event_rules.json`
- `wealth_rules.json` / `career_rules.json` / `love_rules.json`
- `risk_rules.json` / `advice_rules.json`
- `wealth_overview_rules.json` / `romance_overview_rules.json` / `health_overview_rules.json` / `career_overview_rules.json`

**紫微规则（8 个）：**
- `ziwei_rules.json` / `ziwei_palace_rules.json` / `ziwei_star_rules.json`
- `ziwei_sihua_rules.json` / `ziwei_life_card_rules.json`
- `ziwei_risk_rules.json` / `ziwei_advice_rules.json`

---

## 五、测试体系（23 文件，145 个测试函数）

| 测试文件 | 测试数 | 测试内容 |
|----------|--------|----------|
| `test_algorithm_boundaries.py` | 9 | 特殊格局、年龄区间、真太阳时 |
| `test_core_behaviors.py` | 6 | 数据库、五行、大运、十神 |
| `test_cross_sample_diversity.py` | 2 | 命盘指纹、专项报告相似度 |
| `test_database.py` | 1 | 数据库 CRUD |
| `test_database_rebuild.py` | 1 | 数据库重建 |
| `test_environment_check.py` | 2 | 环境依赖检查 |
| `test_export_report.py` | 2 | 报告导出、PDF 字体 |
| `test_five_element_deep_report.py` | 13 | 五行深度报告完整性 |
| `test_life_overview.py` | 11 | 命盘总论差异化 |
| `test_monthly_specific_events.py` | 13 | 流月事件推断 + 差异化 |
| `test_narrative_quality.py` | 3 | 叙事质量 |
| `test_report_quality.py` | 5 | 报告质量 |
| `test_rule_engine.py` | 1 | 规则引擎 |
| `test_same_year_different_chart.py` | 1 | 同年不同命盘差异化 |
| `test_source_registry.py` | 13 | 参考源注册 |
| `test_streamlit_pages.py` | 1 | 页面导入 |
| `test_v1_local_features.py` | 6 | 本地功能 |
| `test_yearly_monthly.py` | 4 | 年月分析 |
| `test_ziwei_basic.py` | 1 | 紫微基础盘 |
| `test_ziwei_engines.py` | 16 | 辅星/煞星/大限引擎 |
| `test_ziwei_sources.py` | 21 | 紫微参考源 + 宫位 + 主星 + 四化 + 名片 |
| `test_ziwei_triangle.py` | 7 | 三方四正 + 四化引擎 |

---

## 六、参考书体系（7 + 5 本）

### 八字典籍

| 书名 | 主要用途 |
|------|---------|
| 《渊海子平》 | 十神基础、财官印食伤、六亲关系 |
| 《三命通会》 | 干支基础、五行生克、纳音 |
| 《子平真诠》 | 用神、格局、成败救应 |
| 《穷通宝鉴》 | 五行四时、寒暖燥湿、调候喜忌 |
| 《滴天髓阐微》 | 干支体用、旺衰、月令 |
| 《命理探源》 | 强弱判断、化合刑冲 |
| 《神峰通考》 | 命例式断法、格局取法 |

### 紫微典籍

| 书名 | 主要用途 |
|------|---------|
| 《紫微斗数全书》 | 十四主星、十二宫、安星法 |
| 《紫微斗数全集》 | 星曜组合、宫位分析、四化 |
| 《紫微斗数大全》 | 十二宫系统、命盘综合判断 |
| 传统十二宫体系 | 命宫/身宫/十二宫位解释 |
| 传统四化体系 | 化禄/化权/化科/化忌 |

---

## 七、技术栈

| 技术 | 用途 |
|------|------|
| Python 3.12 | 主语言 |
| Streamlit | Web UI 框架 |
| SQLite | 本地数据库 |
| lunar_python | 农历/节气转换 |
| pandas | 数据处理 |
| Altair | 图表渲染 |
| ReportLab | PDF 导出 |
| JSON | 规则文件 |

---

## 八、已实现的功能完整清单

### ✅ 八字排盘
- [x] 四柱推算（年/月/日/时）
- [x] 五行权重统计（天干+地支+藏干）
- [x] 日主强弱（得令/得地/得势）
- [x] 十神关系（正财/偏财/正官/七杀/正印/偏印/比肩/劫财/食神/伤官）
- [x] 地支六冲/三合/六合/刑/害/破

### ✅ 大运流年
- [x] 起运年龄计算
- [x] 大运阶段（10年一运）
- [x] 未来十年流年趋势
- [x] 年度运程分析
- [x] 12个月流月分析（含大概率事件 Top 3）

### ✅ 命盘总论
- [x] 财富潜力评估
- [x] 桃花/感情趋势
- [x] 健康稳定度
- [x] 事业发展方向
- [x] 四维评分系统

### ✅ 五行喜忌
- [x] 五行结构总览（强/弱/喜用/忌神）
- [x] 木火土金水逐一分析
- [x] 每个五行对事业/财运/感情/健康的影响
- [x] 过旺/过弱表现
- [x] 喜用发挥建议 / 忌神节制建议
- [x] 现实生活调整建议

### ✅ 紫微斗数
- [x] 命宫/身宫定位
- [x] 十四主星落宫（紫微系 + 天府系）
- [x] 五行局推算
- [x] 生年四化（化禄/化权/化科/化忌）
- [x] 三方四正基础结构（三合宫 + 对宫 + 主星 + 四化）
- [x] 辅星落宫（文昌/文曲/左辅/右弼）
- [x] 煞星落宫（擎羊/陀罗/火星/铃星/地空/地劫）
- [x] 大限基础结构（10年一运，顺逆规则）
- [x] 紫微命盘名片
- [x] 紫微综合报告（八宫综合 + 四化摘要 + 大限提示）
- [x] 紫微 6 Tab 页面（命盘名片/十二宫盘/主星速查/重点宫位/三方四正/参考依据）

### ✅ 报告导出
- [x] Markdown 综合报告
- [x] TXT 纯文本报告
- [x] PDF 报告（优先本机中文字体）
- [x] 专项报告（事业/财运/婚恋）

### ✅ 用户系统
- [x] 命盘保存/搜索/编辑/删除
- [x] 数据备份（JSON/SQLite）
- [x] 合婚匹配
- [x] 设置/错误日志
- [x] 报告质量检查

---

## 九、当前边界与未实现

| 区域 | 状态 | 说明 |
|------|------|------|
| 紫微飞化 | ❌ 未实现 | 四化飞星体系 |
| 紫微流年流月 | ❌ 未实现 | 大限之后的流年流月推算 |
| 辅星四化 | ❌ 未实现 | 文昌*、文曲*等辅星四化 |
| 紫微大限断事 | ⚠️ 基础结构 | 仅基础结构，未加入复杂飞化断事 |
| 火星铃星查表 | ⚠️ 已完成 | 12年支×12时支共144组合（《紫微斗数全书》起法） |
| 地空地劫 | ⚠️ 已完成 | 年起法（亥宫逆排 / 巳宫顺排） |
| 真太阳时校正 | ❌ 未接入 | 算法已测试，未接入排盘流程 |
| 农历闰月 | ❌ 未处理 | lunar_python 边缘情况 |
| 不确定时辰对比 | ❌ 未实现 | 跨时辰对比功能 |

---

## 十、设计原则

1. **真实数据驱动**：所有判断基于 chart_fingerprint、十神、五行、喜忌、大小运等真实数据。
2. **无绝对化断言**：禁用"必定、绝对、注定、一定发财、一定离婚、必有灾"等。
3. **不伪造未实现算法**：紫微的辅星/煞星/飞化/大限流年标记为未完成时，不输出入宫断语。
4. **来源可追溯**：每条规则记录 source_ids / basis / school / confidence。
5. **两个 Python 版本兼容**：主开发 Python 3.12，同步兼容 Python 3.9（注意 `dict | None` 等语法）。
6. **8501 单一端口**：所有开发、测试、验收统一使用 http://127.0.0.1:8501。

---

## 十一、关键文件索引

```
bazi_ziwei_app/
├── app.py                      # Streamlit 主入口
├── run_mac.sh                  # macOS 一键启动
├── check_env.py                # 环境检查
├── requirements.txt            # 依赖清单
├── ARCHIVE.md                  # 本文件（项目档案）
├── README.md                   # 用户说明
├── CHANGELOG.md                # 更新日志
├── core/                       # 引擎层（34个文件）
│   ├── bazi_engine.py          # 八字排盘
│   ├── monthly_engine.py       # 流月分析
│   ├── monthly_event_inference_engine.py  # 流月事件推断
│   ├── yearly_engine.py        # 年度运程
│   ├── life_overview_engine.py # 命盘总论
│   ├── five_elements.py        # 五行统计
│   ├── strength_engine.py      # 日主强弱
│   └── ziwei_*.py              # 紫微引擎（10个文件）
├── ui/                         # 页面层（19个文件）
│   ├── yearly_page.py          # 年度运程
│   ├── five_element_page.py    # 五行喜忌
│   ├── ziwei_page.py           # 紫微斗数
│   └── ziwei_components.py     # 紫微组件库
├── report/                     # 报告层（13个文件）
│   ├── export_report.py        # 综合导出
│   ├── five_element_deep_report.py  # 五行深度报告
│   └── ziwei_report.py         # 紫微综合报告
├── rules/                      # 规则层（22个JSON文件）
├── tests/                      # 测试层（23个文件）
├── utils/                      # 工具层（7个文件）
└── data/                       # 运行时数据目录
    └── profiles.db             # SQLite 命盘数据库
```

---

## 十二、启动方式

```bash
cd /Users/uni/Documents/命数研究室/bazi_ziwei_app
python -m streamlit run app.py --server.port 8501
```

或使用一键脚本：

```bash
bash run_mac.sh
```

打开浏览器访问 http://127.0.0.1:8501


---

## 十三、用户创建的 Codex Skills

项目目录下的 `skills/` 中包含 2 个 Codex 技能文件，用于指导 AI 助手进行针对性的算法审查和修复。

### 技能 1：bazi-algorithm-review

**文件：** `skills/bazi-algorithm-review/SKILL.md`（135 行）

**目的：** 审查八字排盘核心算法正确性，定位入口函数调用链，按风险等级（HIGH/MEDIUM/LOW）排序并给出修改建议。

**调用链（审查入口）：**
```
app.py → render_bazi_page() → ui/bazi_page.py
  └─ core/bazi_engine.build_bazi_chart(profile)
       ├─ core/calendar_engine.get_lunar_eight_char()  ← 节气/干支/时辰
       ├─ core/five_elements.calculate_five_elements()
       ├─ core/ten_gods.count_ten_gods()
       └─ core/strength_engine.analyze_day_master_strength()
            ├─ 得令 _score_month_command()
            ├─ 得地 _score_branch_roots()
            └─ 得势 _score_influence()

app.py → render_luck_page() → ui/luck_page.py
  └─ core/luck_engine.get_luck_cycles(profile, chart)
       ├─ core/stage_engine.analyze_luck_stage()    ← 大运阶段
       └─ core/yearly_engine.analyze_yearly_fortune() ← 单年流年
            └─ core/monthly_engine.analyze_monthly_fortune() ← 流月
```

**风险等级：**
| 等级 | 含义 |
|------|------|
| HIGH | 影响排盘正确性（节气边界、真太阳时、起运倒挂等） |
| MEDIUM | 影响分析质量（大运匹配、特殊格局、流月喜忌等） |
| LOW | 信息展示问题（文案模糊、布局混乱等） |

**审查步骤：** 定位风险 → 读调用链代码 → 每轮最多 5 个文件 → 检查节气/干支/时辰/起运/大运/流年 → 每轮最多提 3 个继续查看的文件 → 给出风险排序后再修改。

### 技能 2：bazi-algorithm-fix

**文件：** `skills/bazi-algorithm-fix/SKILL.md`（107 行）

**目的：** 按最小改动原则修复八字排盘核心算法问题，包含修复流程和回归验证。

**修复原则：**
1. **最小改动**：只改目标问题对应的代码行，不改格式、命名、注释风格
2. **计划优先**：改前列出待改文件、改动点、风险等级
3. **分片阅读**：每轮最多读 5 个文件
4. **不改无关**：拒绝任何"顺便重构"
5. **改后说明**：列出改了哪些文件的行号，以及如何验证

**修复流程：**
1. 从审查风险列表中选取目标问题
2. 按风险排序列修复计划
3. 分片读取相关文件（最多 5 个）
4. 执行最小改动修复
5. 回归验证（`python -m compileall .` + `python -m unittest discover -s tests -v`）

**示例标签：**
```
标签：八字排盘修复，算法修复，最小改动，回归验证
难度：初级可执行，每轮修复焦点问题上限为 1
```

---

## 十四、附录

### 文件统计汇总

| 目录 | 文件数（.py + .json） | 用途 |
|------|----------------------|------|
| `core/` | 34 | 引擎层：八字、紫微、流月、五行、强弱等 |
| `ui/` | 19 | 页面层：15 个页面 + 样式 + 组件 |
| `report/` | 13 | 报告层：导出 + 专项 + 五行 + 紫微报告 |
| `rules/` | 22 | 规则层：八字 + 紫微 JSON 规则文件 |
| `tests/` | 23 | 测试层：145 个测试函数 |
| `utils/` | 7 | 工具层：数据库、备份、日志、质量检查 |
| `skills/` | 2 | Codex Skills：算法审查 + 算法修复 |
| **总计** | **120** | |

### 关键引用

- 八字参考：7 本典籍（《渊海子平》《三命通会》《子平真诠》《穷通宝鉴》《滴天髓阐微》《命理探源》《神峰通考》）
- 紫微参考：5 个体系（《紫微斗数全书》《紫微斗数全集》《紫微斗数大全》、传统十二宫体系、传统四化体系）
- 星曜总数：24 颗（14 主星 + 4 辅星 + 6 煞星）
- 测试函数：145 个
- 规则文件：22 个
- 页面总数：15 页
- 端口：8501（统一）
