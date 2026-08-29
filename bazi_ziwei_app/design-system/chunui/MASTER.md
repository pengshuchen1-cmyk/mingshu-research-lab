# 命数研究室 ChunUI Web SSOT

本文件是本项目 ChunUI 视觉实现的唯一规范。它依据 ChunUI 生产组件与 `ProfileView`、`MainTabbar` 的真实结构翻译为 Streamlit/Web；任何自动生成的 dark/cinematic、持续动画或多彩建议均不得覆盖本文件。

## 视觉原则

- Monochrome 承载层级。低饱和浅绿只用于 primary CTA、中央问 AI 和少量明确操作；普通 active、输入、选择器、卡片边线与标题装饰保持中性灰。成功与错误色只用于明确反馈。
- 内容背景 `#f2f4f3`，卡片 `#fff`，前景 `#111`，次级文字 `#71717a`，发丝边 `rgba(0,0,0,.08)`。页面标题区使用低饱和浅绿承托，与浅灰内容区形成稳定分区。
- 全产品只有 13 / 17 / 24px 三个文本梯度；同一梯度可用 400/600/700 字重。页面 H1 不超过 24px。
- 页面单列移动优先，桌面内容最大宽度 920px；组卡连续圆角 30px，设置行最小高度 54px，分隔线从正文起点缩进。
- Apple Card 使用白底、发丝边和两级软阴影，不用彩色渐变、厚描边或浮夸 glow。
- Neo 按钮高度 large 58 / medium 48 / small 38，胶囊轮廓，轻内高光与软影；active 只做 `scale(.97)`，不改变布局尺寸。
- 顶部 chrome 是无阴影、无模糊的浅绿静态渐变承托；底部 tabbar 是浮动白色胶囊岛。五项尺寸稳定，AI 项用浅绿强调。
- sheet 桌面居中，移动贴底并带静态遮罩；必须保留安全区和 44px 触控目标。
- 只允许 150–250ms hover/press/focus 过渡。禁止循环动画、Canvas、重 GPU blur；`prefers-reduced-motion` 下禁用过渡。

## Web tokens

```css
--cc-primary: #dcede5;
--cc-primary-foreground: #174e3c;
--cc-background: #f5f5f7;
--cc-content-background: #f2f4f3;
--cc-header-green: #e2f1e9;
--cc-header-green-soft: #f0f7f3;
--cc-card: #fff;
--cc-foreground: #111;
--cc-muted-foreground: #71717a;
--cc-border: rgba(0,0,0,.08);
--cc-radius-card: 30px;
--cc-font-sm: 13px;
--cc-font-base: 17px;
--cc-font-lg: 24px;
```

## 组件映射

- `page_header` / 今日 `ms2-page-hero` → floating page header：24px 标题、13px 副标题、低饱和浅绿多层静态渐变；标题区不使用阴影与 GPU blur，下方内容回到浅灰背景。
- `st.container(border=True)` / report panels → `CCAppleCard`：30px 圆角、发丝边、软阴影；统一空状态例外，使用无框内容块。
- `st.button` → `CCNeoButton`：默认 48px；主 CTA 58px；紧凑 chip 38px。
- setting/profile facts → `ccGroupCard + CCSettingRow`：每行 ≥54px，末端值或箭头，hairline 分隔。
- `st.tabs` / horizontal radio → 中性浅灰 chip group；radio/checkbox 选中 indicator 也保持中性。
- 文本、长文本和选择器只有一个真实外壳：中性发丝边；内部 input/textarea/combobox 无 border、outline 或 shadow。focus-within 使用单一中性可访问环，option hover/selected 使用浅灰。
- `st.expander` → group card row，不另造深色块。
- Streamlit toast/status → 语义反馈胶囊；成功/错误色不得扩散到普通卡片。
- 出生选择器 → native sheet 映射：真实取消/完成、移动贴底、桌面居中、五列联动。

## 页面组成

- 今日：浮动页头 → 公共指导 Apple Cards → 克制的 88 自评起点 → 行动/反思组卡。分数不超过 24px。
- 命盘：统一空态或个人身份卡 → 规则摘要 → 柱/元素组卡 → 下一步胶囊 CTA。
- 问 AI：24px 页头 → 建议 chips → 白色消息卡 → 位于底栏上方的输入 dock。
- 报告：统一空态或摘要 Apple Card → 设置行式导出操作。
- 我的：ProfileView 节奏，但不提供头像上传或头像占位模块；资料与隐私为设置组卡，编辑/新建/清除使用真实操作。

## 响应式与安全

- 375px、横屏与桌面均不得水平滚动；主内容为 `min(100%, 920px)`。
- 内容底部预留 tabbar + safe-area；AI 输入 dock 位于 tabbar 上方。
- 底栏始终五列等宽且高度稳定，active 状态不得造成跳动。
- 所有动态 HTML 先 `html.escape`；视觉重构不得改变 public/local 隔离、canonical preview → fingerprint → confirm 或 AI 安全边界。
