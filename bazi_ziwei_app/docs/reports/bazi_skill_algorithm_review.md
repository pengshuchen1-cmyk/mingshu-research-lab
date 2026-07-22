# bazi-skill 算法复核报告

本报告对照已安装的 bazi-skill，检查命数研究室当前八字算法边界。结论只用于工程复核，不作为绝对命理判断。

## 总结
- 当前项目已具备立春换年、节气定月、真太阳时、大运、纳音、旬空、十二长生等基础能力。
- 本轮新增早晚子时用户可见提示，以及调候解释层。
- 起运顺逆目前主要依赖 lunar_python，建议后续把顺逆依据显示到页面和报告中。

## 对照清单
### 立春换年
- 状态：已接入，仍建议持续用边界样例复核
- 依据：四柱来自 lunar_python 的 EightChar，测试中已有立春前后年柱断言。
- 涉及文件：core/calendar_engine.py；tests/test_bazi_algorithm_accuracy.py；tests/test_jieqi_boundary_month_pillar.py
- 风险/边界：依赖 lunar_python 版本行为，若库接口变化，需要重新跑边界测试。

### 节气定月
- 状态：已接入
- 依据：月柱由 lunar_python 按节气体系生成，项目已有节气边界 fixture。
- 涉及文件：core/calendar_engine.py；tests/fixtures/jieqi_boundary_cases.json
- 风险/边界：节气交界小时仍需要以已知万年历样例持续校验。

### 早晚子时
- 状态：已增加用户可见提示，不改变既有排盘
- 依据：23:00-00:59 出生会提示早晚子时和换日流派差异，建议作为复核点。
- 涉及文件：core/calendar_engine.py；core/bazi_engine.py；ui/profile_form.py
- 风险/边界：当前只提示，不自动生成两套子时盘，避免破坏已有排盘结果。

### 起运顺逆与起运年龄
- 状态：已由 lunar_python 处理，并有负数年龄保护
- 依据：大运通过 EightChar.getYun(gender_code) 获取，年龄区间经 _normalize_age_range 保护。
- 涉及文件：core/luck_engine.py；tests/test_algorithm_boundaries.py
- 风险/边界：顺逆规则由依赖库承担，后续建议增加阳男阴女顺、阴男阳女逆的显式说明。

### 真太阳时
- 状态：已接入，用户勾选后按经度校正
- 依据：使用东经 120 度为北京时间基准，每 1 度约 4 分钟校正。
- 涉及文件：core/calendar_engine.py；core/bazi_engine.py；ui/profile_form.py；tests/test_true_solar_time_integration.py
- 风险/边界：当前为经度时差校正，未加入均时差；页面已提示可能影响时柱。

### 调候解释
- 状态：已增加解释层，不改变强弱评分
- 依据：结合月令季节给出寒暖燥湿的白话解释，参考《穷通宝鉴》调候思路。
- 涉及文件：core/strength_engine.py
- 风险/边界：当前是解释层，不直接参与用神评分，后续可由真实反馈校准。

## 建议下一步
1. 增加页面上的起运顺逆解释：阳男阴女顺，阴男阳女逆。
2. 为 23:00-00:59 增加可选的双盘复核，但不要默认改变当前排盘。
3. 继续用陈芃澍、周惠敏这类真实样本校准流月事件排序。

