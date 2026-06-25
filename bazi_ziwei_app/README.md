# 命数研究室

命数研究室是一个本机离线运行的八字 + 紫微斗数命理分析工具，技术路线为 Python、Streamlit、SQLite、JSON 规则库和 lunar_python。程序不需要账号，不上传数据，适合个人兴趣、传统文化研究和自我规划参考。

## 功能列表

- 八字排盘、五行统计、十神分析
- 日主强弱、喜忌五行、喜用五行细化解释
- 大运阶段、未来十年流年、年度运程、12 个月流月事件倾向
- 事业、财运、婚恋专项报告
- 紫微斗数基础宫位盘和基础报告
- Markdown、TXT、PDF 导出，PDF 优先嵌入本机中文字体，不可用时友好降级
- 命盘保存、搜索、编辑、重新排盘、删除
- 数据备份、JSON 导出、JSON 导入、SQLite 数据库备份
- 设置页面、错误日志、报告质量检查
- 禁用绝对化判断，报告使用“大概率、倾向、容易、适合、建议”等表达

## 安装步骤

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python check_env.py
```

如果提示依赖缺失，请先运行：

```bash
python -m pip install -r requirements.txt
```

## 启动方式

首选启动命令：

```bash
python -m streamlit run app.py
```

macOS 也可以使用一键启动脚本：

```bash
bash run_mac.sh
```

打开浏览器访问：

[http://127.0.0.1:8501](http://127.0.0.1:8501)

## 常见问题

- 如果页面打不开，先确认终端里程序仍在运行。
- 如果提示缺少 Streamlit、pandas 或 lunar_python，请运行 `python -m pip install -r requirements.txt`。
- 如果 PDF 导出失败，可以先使用 Markdown 或 TXT；PDF 会优先使用 macOS 本机中文字体，失败时不会让程序崩溃。
- 如果数据库读取异常，可先用“数据备份”页面导出的 JSON 或 SQLite 备份恢复。

## 数据存储位置

- 命盘数据库：`data/profiles.db`
- 错误日志：`logs/app.log`
- 规则库：`rules/*.json`

## 如何备份

进入“数据备份”页面：

- 点击“导出所有命盘 JSON”保存可迁移备份。
- 点击“备份 SQLite 数据库”保存本机数据库副本。
- 导入 JSON 前请确认文件来源可靠，导入会新增命盘记录。

## 如何导出报告

- “报告导出”页面支持综合报告 Markdown、TXT、PDF。
- “专项报告”页面支持事业、财运、婚恋专项报告 Markdown、TXT、PDF。
- PDF 会优先嵌入可渲染中文字体；如遇字体或依赖问题，会返回中文提示，建议改用 Markdown/TXT。

## 版本路线

- v0.1：基础 Streamlit 应用、八字排盘、本地保存。
- v0.2：日主强弱、喜忌初判、基础报告增强。
- v0.3：大运流年、Markdown/TXT 导出、命盘档案增强。
- v0.4：年度运程、12 个月流月、PDF 友好导出。
- v0.4.2：报告有效性检查、年度深度化、流月事件化。
- v1.0：专项报告、规则库系统化、紫微基础盘、备份、设置、日志和完整本机版整理。

## 紫微斗数说明

当前紫微斗数为基础宫位分析版，支持命宫、身宫、十二宫表格和基础宫位报告。十四主星、四化、大限流年属于后续增强方向；当前版本不会伪造没有把握的主星落宫。

## 免责声明

本报告基于传统命理模型生成，仅供个人兴趣、文化研究和自我规划参考，不应作为医疗、法律、投资、婚姻等重大决策的唯一依据。
