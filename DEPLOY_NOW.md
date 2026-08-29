# 🎯 立即部署到 Streamlit Cloud

## ✅ 准备工作已完成

你的项目已经准备好部署了！

- ✅ 代码已推送到 GitHub
- ✅ 仓库地址：`https://github.com/pengshuchen1-cmyk/mingshu-research-lab`
- ✅ Streamlit 配置已完成
- ✅ 依赖文件已准备

## 🚀 现在开始部署（5 分钟）

### 步骤 1：打开 Streamlit Cloud

点击这个链接：**https://share.streamlit.io**

或者复制链接到浏览器打开。

### 步骤 2：登录

- 点击 **"Sign up"** 或 **"Sign in"**
- 选择 **"Continue with GitHub"**
- 使用你的 GitHub 账号（pengshuchen1-cmyk）登录

### 步骤 3：创建新应用

1. 登录成功后，点击右上角 **"Create app"** 或 **"New app"** 按钮

2. 在弹出的表单中填写：

   **Repository**（仓库）：
   ```
   pengshuchen1-cmyk/mingshu-research-lab
   ```

   **Branch**（分支）：
   ```
   main
   ```

   **Main file path**（主文件路径）：
   ```
   bazi_ziwei_app/app.py
   ```

   **App URL**（应用地址，可选）：
   ```
   mingshu-lab
   ```
   或者你喜欢的其他名字，这将成为你的应用网址的一部分

### 步骤 4：配置环境变量（重要！）

点击 **"Advanced settings"** 展开高级设置。

在 **"Secrets"** 文本框中，粘贴以下内容：

```toml
# 运行模式配置（必须）
MINGSHU_RUNTIME_MODE = "public"

# === 以下为 AI 问答配置（可选）===
# 如果你有 Kimi API Key，可以配置以下内容启用 AI 问答
# 如果没有，也可以正常使用，系统会使用本地规则回答

# MOONSHOT_API_KEY = "sk-在这里填入你的Kimi密钥"
# MINGSHU_AI_PROVIDER = "kimi"
# MINGSHU_AI_MODEL = "kimi-k3"
# MINGSHU_AI_BASE_URL = "https://api.moonshot.cn/v1"
# MINGSHU_AI_REASONING = "low"
# MINGSHU_AI_TIMEOUT_SECONDS = 90
```

**如何获取 Kimi API Key：**
1. 访问 https://platform.moonshot.cn/
2. 注册/登录账号
3. 在 "API Keys" 页面创建新密钥
4. 复制密钥，替换上面的 `sk-在这里填入你的Kimi密钥`
5. 取消注释（删除 # 号）

> 💡 **提示**：不配置 AI 密钥也可以使用，只是 AI 问答功能会使用本地规则，不会调用云端 AI

### 步骤 5：开始部署

确认所有信息正确后，点击底部的 **"Deploy!"** 按钮。

### 步骤 6：等待部署完成

- 部署过程约需 **2-5 分钟**
- 你会看到实时日志：
  ```
  📦 Installing system packages...
  📦 Installing Python dependencies...
  🔧 Building app...
  🚀 Launching app...
  ✅ Your app is live!
  ```

## 🎉 部署成功！

部署完成后，你会看到：

- **应用地址**：`https://你的应用名.streamlit.app`
- **状态**：✅ Running
- **自动打开**：浏览器会自动打开你的应用

## 📱 分享你的应用

你的命数研究室现在已经在线了！可以：

- 📋 复制应用链接分享给朋友
- 🔗 在社交媒体上分享
- 📧 通过邮件发送链接

## 🔧 管理应用

在 https://share.streamlit.io 你可以：

- 📊 查看访问统计
- 📝 查看运行日志
- ⚙️ 修改配置
- 🔄 重启应用
- ❌ 删除应用

## 🔄 更新应用

以后每次修改代码后：

```bash
# 1. 提交代码
git add .
git commit -m "更新说明"
git push origin main

# 2. Streamlit Cloud 会自动检测并重新部署（2-3 分钟）
```

## ❓ 常见问题

### Q: 部署失败怎么办？

**A:** 查看部署日志中的错误信息：
- 如果是路径错误，确认 `bazi_ziwei_app/app.py`
- 如果是依赖错误，检查 `requirements.txt`
- 如果是内存错误，可能需要优化代码

### Q: 应用很慢怎么办？

**A:** 免费版资源有限，可以：
- 优化代码性能
- 使用缓存 `@st.cache_data`
- 升级到付费计划（$20/月）

### Q: 可以绑定自己的域名吗？

**A:** 可以，但需要：
- 升级到 Team 或 Enterprise 计划
- 添加自定义 CNAME 记录

### Q: 数据会保存吗？

**A:** 不会，因为使用了 `public` 模式：
- 用户数据只在会话中（30 分钟）
- 刷新或关闭页面后数据清除
- 这样更安全，适合公开网站

### Q: 如何查看有多少人访问？

**A:** 在 Streamlit Cloud 管理页面：
- 点击你的应用
- 查看 "Analytics" 标签
- 可以看到访问量、用户数等

## 📞 需要帮助？

- 📖 详细文档：[STREAMLIT_CLOUD_DEPLOY.md](./STREAMLIT_CLOUD_DEPLOY.md)
- 💬 Streamlit 社区：https://discuss.streamlit.io
- 🐛 GitHub Issues：https://github.com/pengshuchen1-cmyk/mingshu-research-lab/issues

## 🎁 额外功能

### 1. 添加应用图标

在 `bazi_ziwei_app/app.py` 中：
```python
st.set_page_config(
    page_title="命数研究室",
    page_icon="🔮",  # 你的图标
    layout="wide"
)
```

### 2. 自定义主题

编辑 `bazi_ziwei_app/.streamlit/config.toml`：
```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
```

### 3. 添加社交分享

在应用中添加分享按钮：
```python
st.sidebar.markdown("""
### 分享应用
- [分享到微博](...)
- [分享到微信](...)
""")
```

## 🎊 恭喜！

你已经成功将命数研究室部署到云端！

现在你有了：
- ✅ 一个可以随时访问的在线应用
- ✅ 自动更新的部署流程
- ✅ 专业的 URL 地址
- ✅ 完全免费的托管服务

**立即访问你的应用并分享给朋友吧！** 🚀

---

**快速链接：**
- 🌐 Streamlit Cloud：https://share.streamlit.io
- 📦 GitHub 仓库：https://github.com/pengshuchen1-cmyk/mingshu-research-lab
- 📖 项目文档：[README.md](./README.md)
