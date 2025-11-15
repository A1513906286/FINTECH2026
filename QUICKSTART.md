# ⚡ Fintech2026 快速开始指南

5 分钟快速部署 Fintech2026 虚拟信用卡系统！

---

## 🎯 一键启动（Windows 用户）

```bash
# 双击运行
启动项目.bat
```

就这么简单！脚本会自动完成所有配置。

---

## 🔧 手动启动（3 步完成）

### Step 1: 安装依赖（2 分钟）

```bash
# 使用 conda（推荐）
conda create -n fintech python=3.8 -y
conda activate fintech
conda install -c conda-forge dlib -y
pip install -r requirements.txt

# 或使用 pip
pip install -r requirements.txt
```

### Step 2: 安装 Ollama（1 分钟）

```bash
# 1. 下载安装 Ollama
# Windows: https://ollama.com/download

# 2. 下载模型
ollama pull llama3.2:3b

# 3. 启动服务（新终端窗口）
ollama serve
```

### Step 3: 启动应用（1 分钟）

```bash
# 初始化数据库
python utils/init_db.py

# 启动应用
python app.py
```

**访问**: http://127.0.0.1:5000/

---

## ✅ 验证安装

### 测试 1: 检查依赖
```bash
python -c "import flask, face_recognition, xgboost; print('✅ 依赖安装成功')"
```

### 测试 2: 检查 Ollama
```bash
ollama list
# 应该看到 llama3.2:3b
```

### 测试 3: 测试 AI 推荐
访问: http://127.0.0.1:5000/test_recommendations

---

## 🎮 快速体验

### 1. 登录系统
- 访问: http://127.0.0.1:5000/login
- 用户名: `Yogurt`
- 使用 Face ID 或密码登录

### 2. 查看信用卡
- 卡号: `5210 7132 0767 1316`
- 额度: ¥100,000
- WECoin: 200

### 3. 抽奖体验
- 点击"生成盲盒"
- 消耗 10 WECoin 翻卡
- 获得优惠券奖励

### 4. AI 推荐
- 滚动到"探索阿布扎比"板块
- 查看 AI 生成的旅游推荐
- 点击推荐查看详情

### 5. 上传 PDF
- 点击"上传银行流水"
- 选择 `data/消费流水.pdf`
- 查看 AI 信用评估结果

---

## 🔥 核心功能速览

| 功能 | 说明 | 技术 |
|------|------|------|
| 🔐 Face ID | 人脸识别登录 | face_recognition |
| 📄 PDF 识别 | 自动提取银行流水 | pdfplumber |
| 🤖 信用评估 | AI 预测授信额度 | XGBoost |
| 🎁 盲盒抽奖 | 智能概率算法 | Python |
| 🌍 AI 推荐 | 旅游景点推荐 | Ollama + Llama3.2 |

---

## 🚨 常见问题速查

### ❌ dlib 安装失败
```bash
conda install -c conda-forge dlib -y
```

### ❌ Ollama 502 错误
```bash
# 确保 Ollama 服务运行
ollama serve

# 确保模型已下载
ollama pull llama3.2:3b
```

### ❌ 搜索失败（国内用户）
```python
# 修改 app.py 第 35 行
use_proxy=True
proxy_url="http://127.0.0.1:7890"  # 启动 Clash
```

### ❌ 端口被占用
```bash
# 修改 app.py 最后一行
app.run(debug=True, port=5001)
```

---

## 📚 详细文档

- 📖 [完整 README](./README.md)
- 🔧 [环境配置指南](./docs/环境配置指南.md)
- 🔐 [Face ID 使用说明](./docs/Face_ID使用说明.md)
- 🌐 [代理配置说明](./docs/代理配置说明.md)

---

## 🎯 下一步

1. ✅ 阅读 [README.md](./README.md) 了解所有功能
2. ✅ 查看 [环境配置指南](./docs/环境配置指南.md) 深入配置
3. ✅ 尝试注册新用户并上传人脸
4. ✅ 上传自己的银行流水 PDF
5. ✅ 自定义抽奖规则和奖品

---

<div align="center">

**🚀 开始使用**: `python app.py`

**💬 遇到问题**: 查看 [常见问题](#-常见问题速查) 或阅读 [详细文档](#-详细文档)

Made with ❤️ by Fintech2026 Team

</div>

