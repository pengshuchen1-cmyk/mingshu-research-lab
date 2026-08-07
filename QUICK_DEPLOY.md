# 🚀 5 分钟快速部署到 Streamlit Cloud

## ✅ 前置检查

```bash
# 1. 确认在项目根目录
pwd
# 应该看到：/Users/hongzezhang/workspace/mingshu-research-lab

# 2. 确认代码已提交
git status
# 应该看到：nothing to commit, working tree clean

# 3. 确认远程仓库
git remote -v
# 应该看到你的 GitHub 仓库地址
```

如果还没有远程仓库：

```bash
# 创建 GitHub 仓库后（在 GitHub 网站上操作）
git remote add origin https://github.com/你的用户名/mingshu-research-lab.git
git branch -M main
git push -u origin main
```

## 📝 部署步骤

### 第 1 步：推送最新代码

```bash
# 添加所有文件
git add .

# 提交更改
git commit -m "准备部署到 Streamlit Cloud"

# 推送到 GitHub
git push origin main
```

### 第 2 步：访问 Streamlit Cloud

在浏览器中打开：**https://share.streamlit.io**

### 第 3 步：登录

- 点击 **"Sign up"** 或 **"Log in"**
- 选择 **"Continue with GitHub"**
- 授权 Streamlit 访问你的仓库

### 第 4 步：创建应用

1. 点击右上角的 **"New app"** 按钮

2. 填写配置：
   ```
   Repository: 选择 "你的用户名/mingshu-research-lab"
   Branch: main
   Main file path: bazi_ziwei_app/app.py
   App URL: mingshu-lab（或其他你喜欢的名字）
   ```

3. 点击 **"Advanced settings"** 展开高级配置

4. 在 **"Secrets"** 中粘贴以下内容：

   ```toml
   # 基础配置（必须）
   MINGSHU_RUNTIME_MODE = "public"
   
   # AI 配置（可选，如果你有 Kimi API Key）
   # MOONSHOT_API_KEY = "sk-你的密钥"
   # MINGSHU_AI_PROVIDER = "kimi"
   # MINGSHU_AI_MODEL = "kimi-k3"
   ```

   > 💡 提示：如果没有 Kimi API Key，不用配置 AI 相关的变量，应用仍可正常使用本地规则

5. 点击 **"Deploy!"** 按钮

### 第 5 步：等待部署

- 首次部署约需 **2-5 分钟**
- 可以看到实时日志：
  ```
  📦 Installing system packages...
  📦 Installing Python dependencies...
  🔧 Building app...
  🚀 Launching app...
  ```

### 第 6 步：访问应用

部署成功后：
- 浏览器会自动打开你的应用
- 地址格式：`https://你的应用名.streamlit.app`
- 状态显示：**✅ Your app is live!**

## 🎉 完成！

你的命数研究室现在已经在线上运行了！

**分享你的应用：**
- 应用地址：`https://你的应用名.streamlit.app`
- 可以发给朋友使用
- 完全免费托管

## 🔄 后续更新

每次更新代码后：

```bash
# 1. 提交更改
git add .
git commit -m "更新说明"

# 2. 推送到 GitHub
git push origin main

# 3. Streamlit Cloud 会自动检测并重新部署（2-3 分钟）
```

## ⚙️ 管理应用

访问 https://share.streamlit.io 可以：
- 查看应用状态
- 查看访问日志
- 修改配置
- 重启应用
- 删除应用

## ❓ 遇到问题？

### 部署失败

1. 查看部署日志（红色错误信息）
2. 常见问题：
   - 路径错误：确认是 `bazi_ziwei_app/app.py`
   - 依赖问题：检查 `requirements.txt`
   - 内存不足：优化代码或升级方案

### 应用打不开

1. 检查应用状态（应显示 "Running"）
2. 尝试刷新页面
3. 查看错误日志

### 功能异常

1. 检查 Secrets 配置是否正确
2. 确认环境变量格式（TOML 格式）
3. 重启应用试试

## 💡 优化建议

### 1. 自定义域名（付费功能）

Streamlit Cloud 支持绑定自定义域名：
- 进入应用设置
- 添加 CNAME 记录
- 等待 DNS 生效

### 2. 提升性能

```python
# 在 app.py 中添加缓存
import streamlit as st

@st.cache_data(ttl=3600)
def expensive_computation():
    # 耗时操作
    pass
```

### 3. 添加分析

```python
# 可选：添加访问统计
import streamlit as st

st.write(f"欢迎访问！当前有 {st.session_state.get('visitors', 0)} 位访客")
```

## 📚 更多资源

- 详细部署指南：[STREAMLIT_CLOUD_DEPLOY.md](./STREAMLIT_CLOUD_DEPLOY.md)
- 项目文档：[bazi_ziwei_app/README.md](./bazi_ziwei_app/README.md)
- Streamlit 官方文档：https://docs.streamlit.io

---

**需要帮助？**
- 查看详细文档：`STREAMLIT_CLOUD_DEPLOY.md`
- 提交 Issue：GitHub Issues
- Streamlit 社区：https://discuss.streamlit.io

---

**恭喜你完成部署！🎊**
