# 命数研究室

<div align="center">

🔮 **专业的八字与紫微斗数分析工具**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](你的应用地址)

[English](./README_EN.md) | 简体中文

</div>

## 📖 项目简介

命数研究室是一个基于传统命理学的分析工具，提供：

- 🎯 **八字排盘** - 精确的四柱八字计算
- ⭐ **紫微斗数** - 完整的紫微命盘排布
- 🤖 **AI 问答** - 智能命理解析（支持 Kimi AI）
- 📊 **详细报告** - 多维度命理分析
- 💾 **数据管理** - 本地/云端两种模式

## 🚀 快速开始

### 在线体验

访问我们的在线应用：[Streamlit Cloud 部署地址](你的应用地址)

### 本地运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/mingshu-research-lab.git
cd mingshu-research-lab/bazi_ziwei_app

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或 .venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run app.py
```

访问 http://localhost:8501

## ✨ 主要功能

### 八字分析
- 精确的四柱排盘（支持公历/农历）
- 五行强弱分析
- 十神系统解析
- 大运流年推算
- 格局判定
- 喜忌五行

### 紫微斗数
- 十二宫位排布
- 十四主星落宫
- 四化分析
- 大限推算
- 辅星/煞星

### AI 智能问答
- 支持 Kimi K3 模型
- 基于本地规则校验
- 无密钥时自动降级到本地回答

### 报告导出
- Markdown 格式
- TXT 纯文本
- PDF 文档（含中文字体）

## 🔧 技术栈

- **前端框架**: Streamlit
- **数据存储**: SQLite（本地模式）
- **历法计算**: lunar_python
- **AI 服务**: Kimi API（可选）
- **PDF 生成**: ReportLab

## 📊 部署

### Streamlit Cloud（推荐）

1. Fork 本仓库
2. 访问 [Streamlit Cloud](https://share.streamlit.io)
3. 连接你的 GitHub 账号
4. 选择仓库和主文件：`bazi_ziwei_app/app.py`
5. 配置环境变量（可选）：
   ```
   MINGSHU_RUNTIME_MODE=public
   MOONSHOT_API_KEY=你的密钥
   ```
6. 点击 Deploy

详细部署指南：[DEPLOYMENT_GUIDE.md](./bazi_ziwei_app/DEPLOYMENT_GUIDE.md)

### Docker 部署

```bash
cd bazi_ziwei_app
docker-compose up -d
```

### VPS 部署

```bash
cd bazi_ziwei_app
bash deploy.sh
```

## 🔒 隐私与安全

- **公网模式**: 不保存用户数据，会话 30 分钟自动失效
- **本地模式**: 数据保存在本地数据库，完全私密
- **AI 问答**: 不发送姓名、生日等敏感信息
- **开源透明**: 所有代码公开可审计

详见：[PRIVACY.md](./bazi_ziwei_app/PRIVACY.md)

## 📚 文档

- [项目介绍](./bazi_ziwei_app/README.md)
- [部署指南](./bazi_ziwei_app/DEPLOYMENT_GUIDE.md)
- [更新日志](./bazi_ziwei_app/CHANGELOG.md)
- [隐私政策](./bazi_ziwei_app/PRIVACY.md)

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request！

## 📄 开源协议

本项目遵循 MIT 协议

## ⚠️ 免责声明

本项目提供的命理分析仅供传统文化研究和个人参考，不应作为医疗、法律、投资、婚姻等重大决策的唯一依据。

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/你的用户名/mingshu-research-lab/issues)
- 邮箱: your.email@example.com

---

<div align="center">

**如果觉得项目有用，请给个 ⭐ Star 吧！**

Made with ❤️ by [你的名字]

</div>
