# Streamlit Cloud 部署指南

## 📋 部署前准备

### 1. 确认代码已推送到 GitHub

```bash
# 检查当前分支
git branch

# 查看远程仓库
git remote -v

# 推送代码（如果还没推送）
git add .
git commit -m "准备部署到 Streamlit Cloud"
git push origin main
```

### 2. 确认项目结构

你的项目应该有以下文件：

```
mingshu-research-lab/
├── bazi_ziwei_app/
│   ├── app.py              ← 主程序入口
│   ├── requirements.txt    ← Python 依赖
│   ├── packages.txt        ← 系统依赖（可选）
│   ├── .streamlit/
│   │   └── config.toml     ← Streamlit 配置
│   ├── core/               ← 核心代码
│   ├── ui/                 ← UI 界面
│   ├── utils/              ← 工具函数
│   └── rules/              ← 规则库
└── README.md
```

## 🚀 部署步骤

### 步骤 1：访问 Streamlit Cloud

打开浏览器访问：https://share.streamlit.io

### 步骤 2：登录/注册

- 点击 **"Sign up"** 或 **"Log in"**
- 使用 GitHub 账号登录
- 授权 Streamlit 访问你的仓库

### 步骤 3：创建新应用

1. 点击 **"New app"** 按钮
2. 在弹出的窗口中填写：

   - **Repository**: `你的用户名/mingshu-research-lab`
   - **Branch**: `main`（或你的主分支名）
   - **Main file path**: `bazi_ziwei_app/app.py`
   - **App URL** (optional): 自定义你的应用地址（如 `mingshu-lab`）

### 步骤 4：配置环境变量（可选但推荐）

点击 **"Advanced settings"**，然后配置 **Secrets**：

#### 基础配置（必须）
```toml
# 运行模式：public（公网）或 local（本地）
MINGSHU_RUNTIME_MODE = "public"
```

#### AI 问答配置（可选）
```toml
# 如果要启用 AI 问答功能，添加以下配置：
MINGSHU_AI_PROVIDER = "kimi"
MOONSHOT_API_KEY = "sk-你的Kimi密钥"
MINGSHU_AI_MODEL = "kimi-k3"
MINGSHU_AI_BASE_URL = "https://api.moonshot.cn/v1"
MINGSHU_AI_REASONING = "low"
MINGSHU_AI_TIMEOUT_SECONDS = 90
```

**获取 Kimi API Key：**
1. 访问 [Kimi 开放平台](https://platform.moonshot.cn/)
2. 注册/登录账号
3. 创建 API Key
4. 复制密钥到上面的配置中

> ⚠️ 注意：不配置 API Key 也可以正常使用，系统会自动使用本地规则回答

### 步骤 5：部署应用

1. 检查所有配置无误
2. 点击 **"Deploy!"** 按钮
3. 等待 2-5 分钟（首次部署较慢）

### 步骤 6：查看部署状态

部署过程中可以看到：
- 📦 Installing dependencies（安装依赖）
- 🔧 Building app（构建应用）
- 🚀 Launching app（启动应用）

## ✅ 部署成功

部署成功后，你会看到：

- ✅ 应用运行状态：**Running**
- 🌐 应用地址：`https://你的应用名.streamlit.app`
- 📊 使用统计和日志

## 🔧 配置管理

### 查看/编辑应用

1. 访问 https://share.streamlit.io
2. 找到你的应用
3. 点击应用名称进入管理页面

### 更新环境变量

1. 进入应用管理页面
2. 点击 **"⚙️ Settings"**
3. 选择 **"Secrets"**
4. 编辑配置
5. 点击 **"Save"**（应用会自动重启）

### 查看日志

1. 进入应用管理页面
2. 点击 **"Manage app"**
3. 查看 **"Logs"** 标签

## 🔄 更新部署

当你更新代码后：

```bash
# 提交更改
git add .
git commit -m "更新功能"
git push origin main
```

Streamlit Cloud 会自动检测到更新并重新部署（约 2-3 分钟）

### 手动重启

如果需要手动重启：
1. 进入应用管理页面
2. 点击 **"⋮"** 菜单
3. 选择 **"Reboot app"**

## ⚠️ 常见问题

### 问题 1：ModuleNotFoundError

**原因**：缺少依赖包

**解决**：
1. 检查 `requirements.txt` 是否包含所需的包
2. 确保版本号正确
3. 推送更新后等待重新部署

### 问题 2：应用无法启动

**排查步骤**：
1. 查看部署日志
2. 确认 `app.py` 路径正确
3. 检查环境变量配置
4. 本地测试是否能运行

### 问题 3：内存不足

**原因**：Streamlit Cloud 免费版限制 1GB 内存

**解决**：
- 优化代码，减少内存占用
- 使用 `@st.cache_data` 缓存数据
- 考虑升级到付费计划

### 问题 4：访问速度慢

**原因**：服务器在国外

**解决**：
- 使用 CDN 加速（付费功能）
- 考虑部署到国内服务器
- 使用 Docker 自行部署

### 问题 5：Secrets 不生效

**检查**：
1. Secrets 格式是否为 TOML
2. 变量名是否正确（区分大小写）
3. 保存后是否重启了应用

## 📊 资源限制

Streamlit Cloud 免费版限制：

| 资源 | 限制 |
|------|------|
| CPU | 共享 |
| 内存 | 1 GB |
| 存储 | 不持久化 |
| 带宽 | 无限制 |
| 应用数量 | 1 个公开应用 |

## 💡 优化建议

### 1. 加快启动速度

```python
# 在 app.py 中使用缓存
import streamlit as st

@st.cache_data
def load_rules():
    # 加载规则库
    pass

@st.cache_resource
def init_models():
    # 初始化模型
    pass
```

### 2. 减少内存占用

```python
# 及时清理大对象
import gc

def process_large_data():
    # 处理数据
    result = ...
    gc.collect()  # 手动触发垃圾回收
    return result
```

### 3. 优化依赖包

只安装必需的包，减小镜像大小：

```txt
# requirements.txt
streamlit>=1.35.0
pandas>=2.0.0
lunar_python>=1.4.8
# 其他必需的包...
```

## 🔒 安全建议

1. **不要提交密钥到代码**
   - 使用 Secrets 管理敏感信息
   - 确保 `.gitignore` 包含 `.streamlit/secrets.toml`

2. **使用公网模式**
   ```toml
   MINGSHU_RUNTIME_MODE = "public"
   ```
   这样可以避免保存用户数据

3. **定期更新依赖**
   ```bash
   pip list --outdated
   pip install --upgrade 包名
   ```

## 📞 获取帮助

- Streamlit 文档：https://docs.streamlit.io
- Streamlit 论坛：https://discuss.streamlit.io
- GitHub Issues：提交问题到项目仓库

## ✨ 部署清单

部署前确认：

- [ ] 代码已推送到 GitHub
- [ ] `requirements.txt` 包含所有依赖
- [ ] `app.py` 路径正确
- [ ] `.streamlit/config.toml` 配置完成
- [ ] 环境变量已配置（如需要）
- [ ] 本地测试通过
- [ ] `.gitignore` 配置正确

部署后验证：

- [ ] 应用能正常访问
- [ ] 界面显示正常
- [ ] 功能测试通过
- [ ] AI 问答可用（如配置）
- [ ] 报告导出正常

---

**🎉 恭喜！你的命数研究室已成功部署到云端！**

分享你的应用地址：`https://你的应用名.streamlit.app`
