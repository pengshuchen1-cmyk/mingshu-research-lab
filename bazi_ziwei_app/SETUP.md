# 启动指南

## 正确启动方式

```bash
cd bazi_ziwei_app
source .venv/bin/activate
streamlit run app.py
```

或者直接双击 `start.command`（macOS）。

## 常见故障：ModuleNotFoundError: No module named 'ui'

### 根因
直接调用 `.venv/bin/python3 -m streamlit run app.py` 启动会导致 Python 模块路径解析失败。必须 **先 source activate** 再启动。

### 正确做法 ✓
```bash
# 正确的启动方式
source .venv/bin/activate
streamlit run app.py

# 或首次运行（自动创建环境、安装依赖）
bash run_mac.sh
```

### 错误做法 ✗
```bash
# 这会报 ModuleNotFoundError: No module named 'ui'
.venv/bin/python3 -m streamlit run app.py
```

`source .venv/bin/activate` 会设置 `VIRTUAL_ENV`、`PATH`、`PYTHONHOME` 等环境变量，
确保 Python 的模块解析路径正确。直接调用 `.venv/bin/python3` 会跳过这些设置。

## 试错验证
如果启动后报错，清除 Streamlit 缓存再试：

```bash
rm -rf ~/.streamlit/
```
