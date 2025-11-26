# ⚡ Fintech2026 快速开始指南

**3分钟快速部署 Fintech2026 虚拟信用卡系统！**

---

## 🎯 方法一：一键启动（推荐）

### Windows 用户
```bash
# 双击运行
启动项目.bat
```

脚本会自动完成：
- ✅ 检查 Python 环境
- ✅ 安装所有依赖
- ✅ 初始化数据库
- ✅ 启动服务器

---

## 🔧 方法二：手动启动

### Step 1: 安装依赖
```bash
# 使用 conda（推荐，避免 dlib 安装问题）
conda create -n fintech python=3.8 -y
conda activate fintech
conda install -c conda-forge dlib -y
pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### Step 2: 安装 Ollama（AI推荐功能）
```bash
# 1. 下载安装 Ollama: https://ollama.com/download

# 2. 下载模型
ollama pull llama3.2:3b

# 3. 启动服务（新终端）
ollama serve
```

### Step 3: 启动应用
```bash
# 初始化数据库
python utils/init_db.py

# 启动应用
python app.py
```

**访问**: http://127.0.0.1:5000/

---

## ✅ 快速验证

```bash
# 测试依赖
python -c "import flask, face_recognition, xgboost, pandas; print('✅ 所有依赖安装成功')"

# 测试 Ollama
ollama list  # 应该看到 llama3.2:3b
```

---

## 🎮 快速体验

### 1. 登录系统
- 访问: http://127.0.0.1:5000/login
- 测试账号: `Yogurt`
- 使用 Face ID 或密码登录

### 2. 查看信用卡
- 卡号: `5210 7132 0767 1316`
- 额度: ¥100,000
- WECoin: 200

### 3. 信用评估
- 注册新用户
- 上传银行流水PDF
- 查看AI预测的授信额度
- 系统会显示：
  - 13个财务指标
  - 违约概率 (PD)
  - 额度利用率
  - 候选额度评估表
  - 最优授信额度

### 4. 盲盒抽奖
- 点击"生成盲盒"
- 消耗 10 WECoin 翻卡
- 获得优惠券奖励

### 5. AI 旅游推荐
- 滚动到"探索阿布扎比"板块
- 查看 AI 生成的旅游推荐

---

## 🔥 核心功能

| 功能 | 说明 | 技术栈 |
|------|------|--------|
| 🔐 Face ID | 人脸识别登录 | face_recognition + dlib |
| 📄 PDF 识别 | 提取银行流水交易数据 | pdfplumber |
| 🤖 信用评估 | 13特征 + PD模型 + 利用率模型 + EV优化 | XGBoost + pandas |
| 🎁 盲盒抽奖 | 智能概率算法 | Python |
| 🌍 AI 推荐 | 旅游景点推荐 | Ollama + Llama3.2 |

---

## 🚨 常见问题

### ❌ dlib 安装失败
```bash
conda install -c conda-forge dlib -y
```

### ❌ Ollama 502 错误
```bash
ollama serve  # 确保服务运行
ollama pull llama3.2:3b  # 确保模型已下载
```

### ❌ 搜索失败（国内用户）
```python
# 修改 app.py 第 35 行，启用代理
use_proxy=True
proxy_url="http://127.0.0.1:7890"
```

### ❌ 端口被占用
```bash
# 修改 app.py 最后一行
app.run(debug=True, port=5001)
```

---

## 📚 详细文档

- 📖 [完整 README](./README.md) - 所有功能详解
- 🔧 [环境配置指南](./docs/环境配置指南.md)
- 🔐 [Face ID 使用说明](./docs/Face_ID使用说明.md)
- 🌐 [代理配置说明](./docs/代理配置说明.md)

---

<div align="center">

**🚀 开始使用**: `python app.py`

**📖 详细文档**: [README.md](./README.md)

Made with ❤️ by Fintech2026 Team

</div>

