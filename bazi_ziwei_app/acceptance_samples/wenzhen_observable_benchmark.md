# 问真可观察结果对照与算法修改闸门

日期：2026-07-15
内部测试数据版本：`tests/fixtures/bazi_reference_cases.json` / `v1.0.0-bazi-reference-cases`

## 边界声明

本基准只保存本项目已有固定命例的内部快照，以及未来可以由截图或公开界面逐项核验的问真观察位。当前没有问真专有算法、完整外部输出、截图证据或可确认版本，因此不声称复制问真专有算法，也不声称内部结果与问真一致。

所有问真字段当前均为 `pending / unverified`。不得把不同流派口径直接当成程序错误；没有可复现证据时，不允许据此修改 `core/`。当前闸门关闭；未来只有真实独立证据包才能打开。

## 对照顺序与差异分类

对照必须先核对输入设置，再依次比较四柱、十神、强弱、关系解释。差异只能归入以下一类：

1. `输入设置不同`：公历/农历、换日规则、真太阳时、地点或时刻等设置不一致。
2. `流派口径不同`：基础排盘一致，但藏干权重、旺衰或关系取象采用不同口径。
3. `当前算法疑似错误`：输入设置一致、外部观察可复现且有证据，并能写出失败测试复现差异。
4. `无法核验`：版本、设置、输出或证据不足。当前六例均属此类。

## 固定内部快照索引

| 案例 | 输入口径 | 四柱 | 日主强弱 | 问真状态 | 当前差异分类 | 允许改算法 |
| --- | --- | --- | --- | --- | --- | --- |
| 唐瑞 | 公历，北京时间 1997-07-17 09:20，昆明 | 丁丑／丁未／庚申／辛巳 | 身强 | pending / unverified | 无法核验 | false |
| 谢昕 | 农历 2000-07-11（公历 2000-08-10）16:20，地点未提供 | 庚辰／甲申／庚子／甲申 | 身强 | pending / unverified | 无法核验 | false |
| 王伟蘅 | 公历 1996-08-28 申时，暂按 16:00，地点未提供 | 丙子／丙申／丁酉／戊申 | 身弱 | pending / unverified | 无法核验 | false |
| 张齐正 | 公历 2003-11-26 15:40，地点未提供 | 癸未／癸亥／癸卯／庚申 | 身强 | pending / unverified | 无法核验 | false |
| 张旭森 | 农历 2000-12-28（公历 2001-01-22）07:30，性别和地点待确认 | 庚辰／己丑／乙酉／庚辰 | 身弱 | pending / unverified | 无法核验 | false |
| 刘曼 | 农历 1994-11-28（公历 1994-12-30）21:45，地点未提供 | 甲戌／丙子／庚寅／丁亥 | 从弱 | pending / unverified | 无法核验 | false |

十神计数、藏干、五行权重和关系签名均保存在下方机器可读快照中。内部快照不代表外部问真输出。字段来源如下：

- `input`：原始输入逐字段来自 `tests/fixtures/bazi_reference_cases.json` 的 `profile`；`engine_profile` 明确记录当前引擎复算时的规范化结果（农历案例使用案例库已换算的公历生日、缺失分钟按案例既定中段值、未提供地点规范化为空字符串、真太阳时关闭）。
- `pillars`、`ten_god_counts`、`five_elements`、`day_master_strength`：同时与案例库 `standard_time_chart` 和当前 `build_bazi_chart` 输出比对。
- `hidden_stems`：来自当前引擎 `core.bazi_constants.BRANCH_HIDDEN_STEMS` 标准映射，并与 `build_bazi_chart` 输出比对；不声称原案例库自带此字段。
- `relationship_signature`：来自当前 `analyze_life_overview(chart)["romance_overview"]["relationship_signature"]`，不是把案例叙述手工改写成结构化签名。

## 算法修改闸门

`algorithm_change_allowed=true` 必须同时满足：

- 状态为 `observed` 且核验状态为 `verified`；
- 有非空、可定位并通过 SHA-256 校验的截图或公开观察存档；
- 设置完整，至少包含 app 版本、历法、真太阳时开关、时区、地点和换日规则，且不得是 `unknown/null`；
- 外部输出通过字段语义深度校验：四柱四键和干支值合法，十神计数是非负整数且至少一项为正，藏干四键每柱至少有一个与该地支对应的合法天干（不允许空数组），五行五键是有限非负数且总和大于零，强弱为规范值，关系签名使用精确子结构且无非法嵌套值；
- 差异已明确分类为 `当前算法疑似错误`；
- RED 证据是与外部截图分离的严格 JSON 产物，并单独登记 SHA-256；产物必须绑定 `case_id`、外部证据哈希、显式白名单中的具体算法 pytest 节点、非零退出码、精确 RED 命令、失败输出、`expected/actual` 和带时区采集时间。闸门自身测试和无关测试不能作为算法失败证据。

下方 truth table 只记录关闭态政策，不构造任何可放行的合成问真案例。当前所有实际案例和策略行均为 `false`，所以本任务不修改任何 `core/` 文件。

## 机器可读基准

```json benchmark-data
{
  "schema_version": "1.0",
  "snapshot_source": "tests/fixtures/bazi_reference_cases.json#v1.0.0-bazi-reference-cases",
  "field_sources": {
    "input": "tests/fixtures/bazi_reference_cases.json profile + explicit engine_profile normalization",
    "pillars": "standard_time_chart.pillars cross-checked with build_bazi_chart",
    "ten_god_counts": "standard_time_chart.ten_god_counts cross-checked with build_bazi_chart",
    "hidden_stems": "core.bazi_constants.BRANCH_HIDDEN_STEMS cross-checked with build_bazi_chart; not supplied by reference cases",
    "five_elements": "standard_time_chart.five_elements cross-checked with build_bazi_chart",
    "day_master_strength": "standard_time_chart.day_master_strength cross-checked with build_bazi_chart day_master_strength.strength",
    "relationship_signature": "analyze_life_overview(chart).romance_overview.relationship_signature"
  },
  "algorithm_change_gate": {
    "required_conditions": [
      "status_observed",
      "verification_verified",
      "traceable_evidence_reference",
      "complete_reproducible_settings",
      "nonempty_external_output",
      "difference_classified_as_current_algorithm_suspected_error",
      "independent_hashed_red_evidence_package"
    ],
    "truth_table": [
      {
        "status_observed": false,
        "verification_verified": true,
        "traceable_evidence_reference": true,
        "complete_reproducible_settings": true,
        "nonempty_external_output": true,
        "difference_classification": "当前算法疑似错误",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      },
      {
        "status_observed": true,
        "verification_verified": false,
        "traceable_evidence_reference": true,
        "complete_reproducible_settings": true,
        "nonempty_external_output": true,
        "difference_classification": "当前算法疑似错误",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      },
      {
        "status_observed": true,
        "verification_verified": true,
        "traceable_evidence_reference": false,
        "complete_reproducible_settings": true,
        "nonempty_external_output": true,
        "difference_classification": "当前算法疑似错误",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      },
      {
        "status_observed": true,
        "verification_verified": true,
        "traceable_evidence_reference": true,
        "complete_reproducible_settings": false,
        "nonempty_external_output": true,
        "difference_classification": "当前算法疑似错误",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      },
      {
        "status_observed": true,
        "verification_verified": true,
        "traceable_evidence_reference": true,
        "complete_reproducible_settings": true,
        "nonempty_external_output": false,
        "difference_classification": "当前算法疑似错误",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      },
      {
        "status_observed": true,
        "verification_verified": true,
        "traceable_evidence_reference": true,
        "complete_reproducible_settings": true,
        "nonempty_external_output": true,
        "difference_classification": "流派口径不同",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      },
      {
        "status_observed": true,
        "verification_verified": true,
        "traceable_evidence_reference": true,
        "complete_reproducible_settings": true,
        "nonempty_external_output": true,
        "difference_classification": "当前算法疑似错误",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      },
      {
        "status_observed": true,
        "verification_verified": true,
        "traceable_evidence_reference": true,
        "complete_reproducible_settings": true,
        "nonempty_external_output": true,
        "difference_classification": "当前算法疑似错误",
        "independent_hashed_red_evidence_package": false,
        "algorithm_change_allowed": false
      }
    ]
  },
  "cases": [
    {
      "benchmark_id": "wenzhen_pending_tang_rui_1997",
      "source_case_id": "bazi_ref_tang_rui_1997_2026",
      "internal_snapshot": {
        "input": {
          "source_profile": {"name": "唐瑞", "gender": "女", "birth_date": "1997-07-17", "birth_hour": 9, "birth_minute": 20, "birth_place": "云南省昆明市五华区", "calendar_type": "solar", "timezone": "Asia/Shanghai"},
          "engine_profile": {"name": "唐瑞", "gender": "女", "birth_date": "1997-07-17", "birth_hour": 9, "birth_minute": 20, "birth_place": "云南省昆明市五华区", "use_solar_time": false},
          "name": "唐瑞",
          "gender": "女",
          "calendar_type": "solar",
          "solar_birth_date": "1997-07-17",
          "lunar_birth_date": null,
          "birth_time": "09:20",
          "birth_place": "云南省昆明市五华区",
          "timezone": "Asia/Shanghai",
          "true_solar_time": false,
          "input_note": "主盘按北京时间；现有案例另存真太阳时参考盘，本快照不使用该参考盘。"
        },
        "pillars": {"year": "丁丑", "month": "丁未", "day": "庚申", "hour": "辛巳"},
        "ten_god_counts": {"比肩": 3, "劫财": 2, "食神": 1, "伤官": 1, "正财": 1, "七杀": 1, "正官": 3, "偏印": 2, "正印": 2},
        "hidden_stems": {"year": ["己", "癸", "辛"], "month": ["己", "丁", "乙"], "day": ["庚", "壬", "戊"], "hour": ["丙", "戊", "庚"]},
        "five_elements": {"木": 0.3, "火": 3.5, "土": 4.8, "金": 3.6, "水": 1.0},
        "day_master_strength": "身强",
        "relationship_signature": {"spouse_palace": {"branch": "申", "element": "金", "role": "忌神"}, "spouse_relations": {"clashes": [], "combinations": ["时支巳申合"]}, "spouse_star": {"basis": "官杀", "total": 4, "proper": 3, "indirect": 1}, "ten_god_support": {"output": 2, "peer": 5, "resource": 4}, "peach_blossom": {"count": 0, "positions": []}, "strength_preference": {"strength": "身强"}}
      },
      "comparison": {
        "comparison_order": ["四柱", "十神", "强弱", "关系解释"],
        "external_observation": {
          "provider": "问真",
          "status": "pending",
          "verification": "unverified",
          "version": "unknown",
          "settings": {"app_version": "unknown", "calendar_type": "unknown", "use_solar_time": "unknown", "timezone": "unknown", "birth_place": "unknown", "day_boundary_rule": "unknown"},
          "external_output": {"pillars": null, "ten_god_counts": null, "hidden_stems": null, "five_elements": null, "day_master_strength": null, "relationship_signature": null},
          "evidence_reference": null
        },
        "difference_classification": "无法核验",
        "difference_note": "无问真截图、版本和输入设置，不能比较。",
        "red_evidence_package": null,
        "algorithm_change_allowed": false
      }
    },
    {
      "benchmark_id": "wenzhen_pending_xie_xin_2000",
      "source_case_id": "bazi_ref_xie_xin_2000_2026",
      "internal_snapshot": {
        "input": {
          "source_profile": {"name": "谢昕", "gender": "女", "calendar_type": "lunar", "lunar_birth_date": "2000-07-11", "birth_date": "2000-08-10", "birth_hour": 16, "birth_minute": 20, "birth_place": "未提供", "timezone": "Asia/Shanghai"},
          "engine_profile": {"name": "谢昕", "gender": "女", "birth_date": "2000-08-10", "birth_hour": 16, "birth_minute": 20, "birth_place": "", "use_solar_time": false},
          "name": "谢昕",
          "gender": "女",
          "calendar_type": "lunar",
          "solar_birth_date": "2000-08-10",
          "lunar_birth_date": "2000-07-11",
          "birth_time": "16:20",
          "birth_place": "未提供",
          "timezone": "Asia/Shanghai",
          "true_solar_time": false,
          "input_note": "按北京时间标准盘；出生地未知，无法校正真太阳时。"
        },
        "pillars": {"year": "庚辰", "month": "甲申", "day": "庚子", "hour": "甲申"},
        "ten_god_counts": {"比肩": 4, "食神": 2, "伤官": 2, "偏财": 2, "正财": 1, "偏印": 3},
        "hidden_stems": {"year": ["戊", "乙", "癸"], "month": ["庚", "壬", "戊"], "day": ["癸"], "hour": ["庚", "壬", "戊"]},
        "five_elements": {"木": 2.5, "火": 0.0, "土": 1.6, "金": 6.0, "水": 2.3},
        "day_master_strength": "身强",
        "relationship_signature": {"spouse_palace": {"branch": "子", "element": "水", "role": "喜用"}, "spouse_relations": {"clashes": [], "combinations": []}, "spouse_star": {"basis": "官杀", "total": 0, "proper": 0, "indirect": 0}, "ten_god_support": {"output": 4, "peer": 4, "resource": 3}, "peach_blossom": {"count": 0, "positions": []}, "strength_preference": {"strength": "身强"}}
      },
      "comparison": {
        "comparison_order": ["四柱", "十神", "强弱", "关系解释"],
        "external_observation": {
          "provider": "问真",
          "status": "pending",
          "verification": "unverified",
          "version": "unknown",
          "settings": {"app_version": "unknown", "calendar_type": "unknown", "use_solar_time": "unknown", "timezone": "unknown", "birth_place": "unknown", "day_boundary_rule": "unknown"},
          "external_output": {"pillars": null, "ten_god_counts": null, "hidden_stems": null, "five_elements": null, "day_master_strength": null, "relationship_signature": null},
          "evidence_reference": null
        },
        "difference_classification": "无法核验",
        "difference_note": "出生地与问真设置均未知，无外部结果可核验。",
        "red_evidence_package": null,
        "algorithm_change_allowed": false
      }
    },
    {
      "benchmark_id": "wenzhen_pending_wang_weiheng_1996",
      "source_case_id": "bazi_ref_wang_weiheng_1996_2026",
      "internal_snapshot": {
        "input": {
          "source_profile": {"name": "王伟蘅", "gender": "男", "calendar_type": "solar", "birth_date": "1996-08-28", "birth_hour": 16, "birth_minute": null, "birth_time_label": "申时", "birth_place": "未提供", "timezone": "Asia/Shanghai"},
          "engine_profile": {"name": "王伟蘅", "gender": "男", "birth_date": "1996-08-28", "birth_hour": 16, "birth_minute": 0, "birth_place": "", "use_solar_time": false},
          "name": "王伟蘅",
          "gender": "男",
          "calendar_type": "solar",
          "solar_birth_date": "1996-08-28",
          "lunar_birth_date": null,
          "birth_time": "16:00 (申时中段暂定)",
          "birth_place": "未提供",
          "timezone": "Asia/Shanghai",
          "true_solar_time": false,
          "input_note": "原始信息只有申时，具体分钟与出生地未提供。"
        },
        "pillars": {"year": "丙子", "month": "丙申", "day": "丁酉", "hour": "戊申"},
        "ten_god_counts": {"比肩": 1, "劫财": 2, "伤官": 3, "偏财": 1, "正财": 2, "七杀": 1, "正官": 2},
        "hidden_stems": {"year": ["癸"], "month": ["庚", "壬", "戊"], "day": ["辛"], "hour": ["庚", "壬", "戊"]},
        "five_elements": {"木": 0.0, "火": 3.0, "土": 1.6, "金": 5.0, "水": 2.0},
        "day_master_strength": "身弱",
        "relationship_signature": {"spouse_palace": {"branch": "酉", "element": "金", "role": "忌神"}, "spouse_relations": {"clashes": [], "combinations": []}, "spouse_star": {"basis": "财星", "total": 3, "proper": 2, "indirect": 1}, "ten_god_support": {"output": 3, "peer": 3, "resource": 0}, "peach_blossom": {"count": 0, "positions": []}, "strength_preference": {"strength": "身弱"}}
      },
      "comparison": {
        "comparison_order": ["四柱", "十神", "强弱", "关系解释"],
        "external_observation": {
          "provider": "问真",
          "status": "pending",
          "verification": "unverified",
          "version": "unknown",
          "settings": {"app_version": "unknown", "calendar_type": "unknown", "use_solar_time": "unknown", "timezone": "unknown", "birth_place": "unknown", "day_boundary_rule": "unknown"},
          "external_output": {"pillars": null, "ten_god_counts": null, "hidden_stems": null, "five_elements": null, "day_master_strength": null, "relationship_signature": null},
          "evidence_reference": null
        },
        "difference_classification": "无法核验",
        "difference_note": "具体分钟、地点和外部输出均缺失。",
        "red_evidence_package": null,
        "algorithm_change_allowed": false
      }
    },
    {
      "benchmark_id": "wenzhen_pending_zhang_qizheng_2003",
      "source_case_id": "bazi_ref_zhang_qizheng_2003_2026",
      "internal_snapshot": {
        "input": {
          "source_profile": {"name": "张齐正", "gender": "男", "calendar_type": "solar", "birth_date": "2003-11-26", "birth_hour": 15, "birth_minute": 40, "birth_time_label": "申时", "birth_place": "未提供", "timezone": "Asia/Shanghai"},
          "engine_profile": {"name": "张齐正", "gender": "男", "birth_date": "2003-11-26", "birth_hour": 15, "birth_minute": 40, "birth_place": "", "use_solar_time": false},
          "name": "张齐正",
          "gender": "男",
          "calendar_type": "solar",
          "solar_birth_date": "2003-11-26",
          "lunar_birth_date": null,
          "birth_time": "15:40",
          "birth_place": "未提供",
          "timezone": "Asia/Shanghai",
          "true_solar_time": false,
          "input_note": "按北京时间标准盘；出生地未知。"
        },
        "pillars": {"year": "癸未", "month": "癸亥", "day": "癸卯", "hour": "庚申"},
        "ten_god_counts": {"比肩": 3, "劫财": 2, "食神": 2, "伤官": 1, "偏财": 1, "七杀": 1, "正官": 1, "正印": 2},
        "hidden_stems": {"year": ["己", "丁", "乙"], "month": ["壬", "甲"], "day": ["乙"], "hour": ["庚", "壬", "戊"]},
        "five_elements": {"木": 1.8, "火": 0.5, "土": 1.3, "金": 2.0, "水": 6.5},
        "day_master_strength": "身强",
        "relationship_signature": {"spouse_palace": {"branch": "卯", "element": "木", "role": "喜用"}, "spouse_relations": {"clashes": [], "combinations": []}, "spouse_star": {"basis": "财星", "total": 1, "proper": 0, "indirect": 1}, "ten_god_support": {"output": 3, "peer": 5, "resource": 2}, "peach_blossom": {"count": 0, "positions": []}, "strength_preference": {"strength": "身强"}}
      },
      "comparison": {
        "comparison_order": ["四柱", "十神", "强弱", "关系解释"],
        "external_observation": {
          "provider": "问真",
          "status": "pending",
          "verification": "unverified",
          "version": "unknown",
          "settings": {"app_version": "unknown", "calendar_type": "unknown", "use_solar_time": "unknown", "timezone": "unknown", "birth_place": "unknown", "day_boundary_rule": "unknown"},
          "external_output": {"pillars": null, "ten_god_counts": null, "hidden_stems": null, "five_elements": null, "day_master_strength": null, "relationship_signature": null},
          "evidence_reference": null
        },
        "difference_classification": "无法核验",
        "difference_note": "问真版本、地点设置与观察结果均缺失。",
        "red_evidence_package": null,
        "algorithm_change_allowed": false
      }
    },
    {
      "benchmark_id": "wenzhen_pending_zhang_xusen_2001",
      "source_case_id": "bazi_ref_zhang_xusen_2001_2026",
      "internal_snapshot": {
        "input": {
          "source_profile": {"name": "张旭森", "gender": "男（暂按，待确认）", "calendar_type": "lunar", "lunar_birth_date": "2000-12-28", "birth_date": "2001-01-22", "birth_hour": 7, "birth_minute": 30, "birth_time_label": "辰时", "birth_place": "未提供", "timezone": "Asia/Shanghai", "assumption_note": "用户提供农历2000年12月28日早上七点多，暂按07:30辰时、男命、未校正真太阳时记录；性别和出生地待后续校准。"},
          "engine_profile": {"name": "张旭森", "gender": "男", "birth_date": "2001-01-22", "birth_hour": 7, "birth_minute": 30, "birth_place": "", "use_solar_time": false},
          "name": "张旭森",
          "gender": "男（暂按，待确认）",
          "calendar_type": "lunar",
          "solar_birth_date": "2001-01-22",
          "lunar_birth_date": "2000-12-28",
          "birth_time": "07:30 (早上七点多暂定)",
          "birth_place": "未提供",
          "timezone": "Asia/Shanghai",
          "true_solar_time": false,
          "input_note": "性别、出生地和真太阳时均待确认；接近卯辰边界时需复核时柱。"
        },
        "pillars": {"year": "庚辰", "month": "己丑", "day": "乙酉", "hour": "庚辰"},
        "ten_god_counts": {"比肩": 3, "偏财": 2, "正财": 2, "七杀": 2, "正官": 2, "偏印": 3},
        "hidden_stems": {"year": ["戊", "乙", "癸"], "month": ["己", "癸", "辛"], "day": ["辛"], "hour": ["戊", "乙", "癸"]},
        "five_elements": {"木": 2.0, "火": 0.0, "土": 6.0, "金": 3.3, "水": 1.1},
        "day_master_strength": "身弱",
        "relationship_signature": {"spouse_palace": {"branch": "酉", "element": "金", "role": "忌神"}, "spouse_relations": {"clashes": [], "combinations": ["年支辰酉合", "时支辰酉合"]}, "spouse_star": {"basis": "财星", "total": 4, "proper": 2, "indirect": 2}, "ten_god_support": {"output": 0, "peer": 3, "resource": 3}, "peach_blossom": {"count": 0, "positions": []}, "strength_preference": {"strength": "身弱"}}
      },
      "comparison": {
        "comparison_order": ["四柱", "十神", "强弱", "关系解释"],
        "external_observation": {
          "provider": "问真",
          "status": "pending",
          "verification": "unverified",
          "version": "unknown",
          "settings": {"app_version": "unknown", "calendar_type": "unknown", "use_solar_time": "unknown", "timezone": "unknown", "birth_place": "unknown", "day_boundary_rule": "unknown"},
          "external_output": {"pillars": null, "ten_god_counts": null, "hidden_stems": null, "five_elements": null, "day_master_strength": null, "relationship_signature": null},
          "evidence_reference": null
        },
        "difference_classification": "无法核验",
        "difference_note": "内部输入本身含待确认项，且无外部结果，不可进入算法差异判断。",
        "red_evidence_package": null,
        "algorithm_change_allowed": false
      }
    },
    {
      "benchmark_id": "wenzhen_pending_liu_man_1994",
      "source_case_id": "bazi_ref_liu_man_1994_2026",
      "internal_snapshot": {
        "input": {
          "source_profile": {"name": "刘曼", "gender": "女", "calendar_type": "lunar", "lunar_birth_date": "1994-11-28", "birth_date": "1994-12-30", "birth_hour": 21, "birth_minute": 45, "birth_time_label": "亥时", "birth_place": "未提供", "timezone": "Asia/Shanghai", "assumption_note": "用户提供农历1994年11月28日晚上9点45分，换算为公历1994年12月30日21:45；出生地未提供，暂按北京时间标准盘，不做真太阳时校正。"},
          "engine_profile": {"name": "刘曼", "gender": "女", "birth_date": "1994-12-30", "birth_hour": 21, "birth_minute": 45, "birth_place": "", "use_solar_time": false},
          "name": "刘曼",
          "gender": "女",
          "calendar_type": "lunar",
          "solar_birth_date": "1994-12-30",
          "lunar_birth_date": "1994-11-28",
          "birth_time": "21:45",
          "birth_place": "未提供",
          "timezone": "Asia/Shanghai",
          "true_solar_time": false,
          "input_note": "按北京时间标准盘；出生地未知，不做真太阳时校正。"
        },
        "pillars": {"year": "甲戌", "month": "丙子", "day": "庚寅", "hour": "丁亥"},
        "ten_god_counts": {"比肩": 1, "劫财": 1, "食神": 1, "伤官": 1, "偏财": 3, "七杀": 2, "正官": 2, "偏印": 2},
        "hidden_stems": {"year": ["戊", "辛", "丁"], "month": ["癸"], "day": ["甲", "丙", "戊"], "hour": ["壬", "甲"]},
        "five_elements": {"木": 2.5, "火": 2.8, "土": 1.3, "金": 1.5, "水": 4.0},
        "day_master_strength": "身弱",
        "relationship_signature": {"spouse_palace": {"branch": "寅", "element": "木", "role": "忌神"}, "spouse_relations": {"clashes": [], "combinations": ["时支寅亥合"]}, "spouse_star": {"basis": "官杀", "total": 4, "proper": 2, "indirect": 2}, "ten_god_support": {"output": 2, "peer": 2, "resource": 2}, "peach_blossom": {"count": 0, "positions": []}, "strength_preference": {"strength": "身弱"}}
      },
      "comparison": {
        "comparison_order": ["四柱", "十神", "强弱", "关系解释"],
        "external_observation": {
          "provider": "问真",
          "status": "pending",
          "verification": "unverified",
          "version": "unknown",
          "settings": {"app_version": "unknown", "calendar_type": "unknown", "use_solar_time": "unknown", "timezone": "unknown", "birth_place": "unknown", "day_boundary_rule": "unknown"},
          "external_output": {"pillars": null, "ten_god_counts": null, "hidden_stems": null, "five_elements": null, "day_master_strength": null, "relationship_signature": null},
          "evidence_reference": null
        },
        "difference_classification": "无法核验",
        "difference_note": "没有可公开观察或截图证据，强弱与关系口径均不能比较。",
        "red_evidence_package": null,
        "algorithm_change_allowed": false
      }
    }
  ]
}
```

## 后续录入规则

只有拿到用户截图或可公开复现的界面观察后，才把对应案例的 `status` 改为 `observed`。录入者必须同时补全版本、历法、真太阳时、地点、换日规则、证据引用和逐项输出；不能确认的字段继续保留 `unknown`，并将差异归为 `无法核验`。若基础四柱因设置不同，先归为 `输入设置不同`；只有基础输入完全对齐后，才继续比较十神、强弱和关系解释。
