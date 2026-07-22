# 命数研究室小程序内容契约

本契约只定义网页展示模型到小程序视图的映射。小程序不得自行推导干支、十神、喜忌、流年或流月事件，也不得复制算法；所有客户端只读取共享核心生成的服务端展示模型。

## Tab 结构

| Tab | 小程序页面 | 读取模型 | 主要动作 |
|---|---|---|---|
| 今日 | `/pages/today/index` | `daily_guidance`、`yearly_guidance` | 阅读公开建议，查看依据与边界 |
| 命盘 | `/pages/chart/index` | `chart_summary`、`profile_status` | 新建命盘或查看个人摘要 |
| 我的 | `/pages/me/index` | `profile_status` | 管理本地档案与隐私设置 |

年度详情 `/pages/yearly/index` 从“今日”或“命盘”进入；资料编辑 `/pages/profile/edit/index` 从命盘空态或个人状态进入，均不新增底部 Tab。

## 页面与组件映射

| 组件 | 小程序页面 | 模型与字段语义 | 动作 |
|---|---|---|---|
| `Hero` | `/pages/today/index`、`/pages/chart/index`、`/pages/yearly/index` | `title` 是页面标题，`kicker` 是短栏目名，`summary` 是结论先行的一句话；个人页读取脱敏的 `chart_summary.summary` | 进入页面即读，不承担计算；可滚动到下一内容区 |
| `DailyAdvice` | `/pages/today/index` | `daily_guidance.date/day_pillar/theme/focus/reminder/action/details/basis/boundary_note` 分别表示日期、公开日柱、主题、重点、提醒、行动、生活细节、依据与边界 | 展开或收起“依据与边界”；不得要求个人资料 |
| `AnnualOverview` | `/pages/yearly/index` | `year/pillar/ten_god/relation_to_favorable/overall_level/overall_text/annual_keywords` 表示年份、流年柱、十神、喜忌关系、年度倾向、白话结论和最多三个关键词 | 切换目标年份，查看年度专项与月份；不显示来源不透明的重复评分图 |
| `RiskAction` | `/pages/yearly/index` | `risk_text/advice_text/suitable_actions/actions_to_avoid` 分别表示主要风险、优先行动、适合做与暂缓做；文案均为趋势建议而非确定结果 | 阅读“结论—为什么—怎么做”，无需二次计算 |
| `MonthCard` | `/pages/yearly/index` | `month_name/pillar/status/direction/event_tags` 表示月份、月柱、文字状态、行动方向和最多三个事件标签 | 点击“查看重点事件”；当前月已展开时显示“收起重点事件” |
| `EventDisclosure` | `/pages/yearly/index` | `title/probability/summary/reality/triggers/basis/advice` 表示事件名、可能性等级、一句话、现实表现、触发因素、依据简写和行动建议 | 展开当前月事件；依据默认折叠，切换月份时替换当前展开项 |
| `PersonalIdentityCard` | `/pages/chart/index` | `day_master/day_element/strength/dominant_elements/pattern/summary/term_ids` 分别表示日主、所属五行、强弱结论、偏旺五行、格局主线、脱敏摘要与可解释术语编号；姓名不进入服务端公开展示模型，用户自定称呼只保存在本地资料层 | 先读日主核心，再读强弱、偏旺元素与格局；点击关联术语时只更新 `activeTermId`，不在客户端推导结论 |
| `TermChip` | `/pages/chart/index` | `term_id/label/group/accessibility_label` 分别表示稳定编号、可见名称、分组与读屏名称；选中态来自页面状态而非服务端模型 | 点击或键盘确认后展开对应 `TermDetail`；触控高度至少 44px、相邻目标间距至少 8px，并提供可见焦点与已展开文字状态 |
| `TermDetail` | `/pages/chart/index` | `term_id/label/definition/observation_scope/boundary/personalized` 表示术语编号、名称、大众定义、观察范围、现实边界与可选的个人化展示；无有效命盘时不返回 `personalized` | 作为统一详情卡或底部抽屉展示；一次只显示当前活动术语，可关闭且不得用颜色作为唯一状态提示 |
| `FourPillarsMatrix` | `/pages/chart/index` | 固定年、月、日、时顺序；每柱读取 `label/ten_god/stem/stem_element/branch/branch_element/hidden_stems`，辅助字段为 `na_yin/di_shi/xun_kong` | 手机端在矩阵容器内横向浏览四列；页面本身不得横向溢出 |
| `ElementDistribution` | `/pages/chart/index` | 固定木、火、土、金、水顺序；`value` 是非负原始值，`percentage` 是占比，`level` 是文字强弱等级 | 阅读水平条、原始值、百分比和等级文字；不只依赖颜色 |
| `FiveDimensionInsight` | `/pages/chart/index` | 固定财富、关系、健康、事业、整体平衡；`key/label/score/level/summary/detail_label/evidence/strengths/risks/advice` 表示稳定键、名称、0–100 值、文字等级、完整正文、详情栏目、依据、优势、隐患与建议 | 卡片直接显示完整正文且不得截断；点击“查看详情”阅读其余字段，详情保留分数、等级和文本替代 |
| `UnifiedProfileForm` | `/pages/profile/edit/index` | `name/gender/calendar_type/birth_date/birth_hour/birth_minute/birth_place/use_solar_time/birth_longitude` 是排盘输入；日期传 ISO 字符串，经度仅在真太阳时启用时传数字 | 本地校验后提交“生成命盘”；错误贴近字段显示，可返回继续编辑 |
| `ProfileStatus` | `/pages/chart/index`、`/pages/me/index` | 只读取安全字段：`profile_status.kind` 固定为模型类型，`profile_status.has_profile` 表示是否有资料，`profile_status.has_chart` 表示是否有可用命盘，`profile_status.next_action` 表示下一页面动作 | 无命盘时按 `next_action` 进入资料表单；已有命盘时进入个人命盘 |

## 服务端公开展示投影

公开命盘响应统一由 `core.presentation_models.build_chart_public_view` 生成，并组合以下真实 DTO 构建函数：

- `build_personal_identity_card_view`：返回不含姓名的 `PersonalIdentityCard`；网页内部身份卡仍可保留姓名，但不得复用为公开响应。
- `build_term_chip_view`：返回含稳定 `group` 与 `accessibility_label` 的 `TermChip`。
- `build_term_detail_view`：只投影通用定义和允许的 `personalized` 展示事实。
- `build_five_dimension_insight_view`：要求财富、关系、健康、事业、整体平衡使用稳定 `key`，并保留完整正文与详情列表。

投影入口先逐组件使用字段白名单，再递归移除 `source_titles`、`source_ids`、`relationship_signature` 及其 camelCase 形式；这些审计字段只按键删除，不把“火、财星、身强”等普通命理值当作隐私词全局替换。姓名、出生日期、出生时辰、地点、经度、用户标识及其常见字段别名另行作为 PII 处理，只清理自由文案中的原始值和常见日期分隔格式，同时保护日主、五行、强弱、格局、术语名称等安全结构字段。`personalized` 只允许契约声明的浅层字符串、字符串数组、有限数字与五行分布，不能透传任意深层对象。内部核心结果不被投影函数修改，典籍来源与关系签名继续留在服务端审查层。

`build_chart_public_view` 会把网页身份卡中的 `day-element-*`、`element-*`、`strength` 等别名规范为当前响应 `TermChip` 已实际提供的正式 `term_id`；`PersonalIdentityCard.term_ids` 中的每一项必须能在同一响应的 `term_chips[].term_id` 找到，不允许出现悬空入口。

术语交互使用 `build_term_disclosure_semantics` 生成稳定按钮编号、详情编号、展开状态与读屏名称；`transition_term_disclosure` 保证单活跃术语，并在关闭后给出应恢复焦点的原触发按钮。网页适配层将这些语义同步为 `aria-expanded`、`aria-controls` 和焦点恢复动作，小程序按同一状态模型映射原生无障碍属性。

## 单活跃月交互

小程序页面只维护一个视图状态 `activeMonthIndex: number | null`，默认值为 `null`，即十二个月全部收起。点击收起月份时把索引写入 `activeMonthIndex`；点击另一月直接替换旧索引，保证一次只展开一个月；再次点击当前月时恢复 `null`。该值仅属于页面临时状态，不写入展示模型、档案或埋点。

## 单活跃术语交互

命盘页只维护一个视图状态 `activeTermId: string | null`，默认值为 `null`。点击或键盘确认一个 `TermChip` 时写入其 `term_id`，一次只展开一个术语；选择另一术语时直接替换旧值，再次点击当前术语时恢复 `null`。关闭详情卡或底部抽屉也恢复 `null`，并将焦点送回触发它的 `TermChip`。`activeTermId` 只属于当前页面，不写入服务端展示模型、档案、缓存或分析埋点。

`TermChip` 的视觉选中态、`aria-expanded`/无障碍展开状态与 `activeTermId` 保持一致；不能同时维护第二个布尔数组，否则容易出现多个术语同时展开。大众定义与个人化展示都由服务端返回，客户端不得计算十神、强弱、喜忌或 `relationship_signature`。

## JSON 可序列化边界

所有展示模型必须可直接 JSON 序列化，只允许对象、数组、字符串、有限数字、布尔值和 `null`。日期与时间使用 ISO 字符串；缺失值用 `null`、空数组或下述空态文案，不传 Python `date`、集合、元组、自定义对象、NaN 或 Infinity。字段名称和枚举值由共享契约固定，客户端只做布局和交互映射。

## 隐私与脱敏

`daily_guidance` 与 `yearly_guidance` 的公共部分不读取姓名、性别、出生日期、出生时辰、出生地点或完整命盘。`UnifiedProfileForm` 的原始出生资料只用于用户主动发起的排盘，不得写入 URL、公开分享内容、分析埋点或错误日志。

`profile_status` 不携带姓名、出生日期、出生时辰、出生地点、经度或其他原始出生资料。`chart_summary.summary` 只可基于已生成的日主与喜用元素输出一句脱敏摘要，不包含完整出生时间、地点、经度、原始样本编号或内部规则标识；客户端同时读取 `chart_summary.ready` 判断该摘要是否可用。

公开展示响应采用字段白名单：只返回本契约逐项列出的展示字段，不得返回 `source_titles`、`source_ids`、内部规则编号、`relationship_signature` 或原始命盘对象。典籍来源与关系签名可继续存在于服务端审查层，但不得进入小程序页面数据、分享内容或可下载报告。

内部展示 API 响应、错误日志和分析埋点不得包含姓名、出生日期、出生时辰、出生地点、经度、完整四柱输入或可反查用户的样本编号。原始资料仅存在于用户主动提交的排盘请求，并只在生成命盘所需的处理周期内使用；请求完成后不得写入日志或缓存键。排盘失败时记录错误类型、接口版本与匿名请求标识，不记录请求正文。

资料编辑页是唯一允许接收原始出生输入的入口；该请求必须与公开展示响应、分析埋点和错误日志分离。姓名不参与命理计算，可由客户端本地保存为用户自定称呼；生日与地点只传给受控排盘入口，不复制到展示 API。

## 空态与错误态

- `profile_status.has_chart=false` 或 `chart_summary.ready=false`：显示“尚未建立个人命盘”，主动作读取 `profile_status.next_action`（当前为“新建命盘”），不得生成或推测个人分析。
- 年度或月度列表为空：显示“暂无足够信息，请稍后重试”，不得保留空白图框或伪造默认事件。
- `event_tags=[]`：`MonthCard` 显示“暂无明确事件标签”；`EventDisclosure` 使用“需观察”的文本空态。
- 五行总值为 0：五项 `value` 与 `percentage` 均为 0，并保留可读的等级文字。
- 请求失败：保留当前可用内容，显示原因和重试动作；不得用公共内容冒充个人结果。

## 单位、等级与文本替代

- `ElementDistribution.percentage` 的单位为百分比，范围 `0–100`，界面显示 `%`；`value` 为同一命盘内的相对原始值，不声明物理单位。
- 五行 `level` 使用共享引擎返回的文字等级，例如“偏旺”“中等”“偏弱”，客户端不得重新划分阈值。
- 五维 `score` 为 `0–100` 的整数，必须同时展示名称、值、等级、解释和文本替代；等级包括“偏强”“中上”“中等”“需经营”“波动较大”。
- 事件 `probability` 是定性等级，例如“较高”“中等”“需观察”，不是统计概率，不得擅自添加 `%`。
- 状态、强弱和风险均必须有文字，不以颜色、条长或图形作为唯一表达。

## 算法归属

小程序不复制算法：干支与大众建议继续由 `popular_advice_engine` 生成，命盘、五行、流年和流月事件继续由现有共享核心生成。术语大众定义与 `personalized`、身份卡强弱与偏旺元素、五维洞察和关系结论均由服务端展示模型提供。

客户端不得计算十神、强弱、喜忌、格局、事件分数或 `relationship_signature`，也不得根据展示字段反推这些结果；客户端只负责读取已版本化的展示模型、呈现空态、维护 `activeMonthIndex`/`activeTermId` 等临时交互状态并发送用户动作。
