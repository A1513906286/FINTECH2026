# 🏦 Fintech2026 虚拟信用卡系统

<div align="center">

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-3.0.0-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)
![AI](https://img.shields.io/badge/AI-Powered-red.svg)

**一个基于 Flask 的智能虚拟信用卡管理系统，专为旅游场景设计**

集成 Face ID、PDF 智能识别、AI 信用评估、盲盒抽奖和 AI 旅游推荐功能

[快速开始](#-快速开始) • [功能特性](#-核心功能) • [文档](#-详细文档) • [常见问题](#-常见问题)

</div>

---

## ✨ 核心功能

### 🎴 智能信用卡管理
- **Face ID 认证** - 人脸识别注册与登录 ([详细说明](./docs/Face_ID使用说明.md))
- **PDF 智能识别** - 自动提取银行流水和余额证明
- **AI 信用评估** - XGBoost 模型预测授信额度
- **16 位卡号生成** - 可定制后 8 位卡号

### 💰 消费与积分系统
- **多币种支持** - 实时汇率转换（AED ⇄ CNY）
- **WECoin 积分** - 消费获得积分奖励
- **消费记录追踪** - 详细账单统计与分析

### 🎁 AI 盲盒抽奖
- **智能概率算法** - 基于用户行为动态调整中奖率
- **多种奖品** - 消费券、汇率券、商户券
- **奖品包管理** - 查看和使用优惠券

### 🌍 AI 旅游推荐（新功能）
- **本地 LLM 驱动** - 使用 Ollama + Llama3.2 模型
- **智能搜索** - DuckDuckGo 实时搜索阿布扎比景点
- **个性化推荐** - AI 生成旅游、美食、购物建议
- **完全免费** - 无需 API Key，本地运行

### 📱 iOS 风格 UI
- **灵动岛设计** - 流畅动画效果
- **毛玻璃效果** - 现代化界面
- **响应式布局** - 完美适配移动端

---

## 🚀 快速开始

### 📋 环境要求

| 组件 | 版本要求 | 说明 |
|------|---------|------|
| **Python** | 3.8+ | 必需 |
| **Ollama** | 最新版 | AI 推荐功能必需 |
| **Clash/代理** | 可选 | 访问 DuckDuckGo（国内用户推荐） |
| **Conda** | 推荐 | 便于安装 dlib |

### ⚡ 方法一：一键启动（推荐）

**Windows 用户**：
```bash
# 双击运行启动脚本
启动项目.bat
```

脚本会自动完成：
1. ✅ 检查 Python 环境
2. ✅ 安装所有依赖
3. ✅ 初始化数据库
4. ✅ 启动服务器

### 🔧 方法二：手动启动

#### Step 1: 克隆项目

```bash
git clone https://github.com/your-repo/Fintech2026.git
cd Fintech2026
```

#### Step 2: 安装 Python 依赖

**推荐使用 Conda（避免 dlib 安装问题）**：
```bash
# 创建虚拟环境
conda create -n fintech python=3.8 -y
conda activate fintech

# 安装 dlib（使用 conda 最可靠）
conda install -c conda-forge dlib -y

# 安装其他依赖
pip install -r requirements.txt
```

**或使用 pip**：
```bash
pip install -r requirements.txt
```

**国内用户加速**：
```bash
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

#### Step 3: 安装 Ollama（AI 推荐功能）

**Windows**：
1. 访问 [Ollama 官网](https://ollama.com/download) 下载安装包
2. 安装后运行：
```powershell
ollama pull llama3.2:3b
```

**验证安装**：
```powershell
ollama list
# 应该看到 llama3.2:3b 模型
```

#### Step 4: 配置代理（可选，国内用户推荐）

如果需要访问 DuckDuckGo 搜索，请配置代理：

1. 启动 Clash 或其他代理工具（默认端口 7890）
2. 修改 `app.py` 第 35 行：
```python
abu_dhabi_service = AbuDhabiService(
    model_name="llama3.2:3b",
    use_proxy=True,  # 启用代理
    proxy_url="http://127.0.0.1:7890"  # Clash 默认端口
)
```

**不使用代理**：
```python
use_proxy=False  # 改为 False
```

详细说明：[代理配置文档](./docs/代理配置说明.md)

#### Step 5: 初始化数据库

```bash
python utils/init_db.py
```

执行后会：
- 创建 `instance/fintech.db` 数据库
- 创建 8 个数据表
- 插入测试用户数据（用户名: Yogurt）
- 插入初始奖品和消费记录

#### Step 6: 启动服务

**启动 Ollama 服务**（新终端窗口）：
```powershell
ollama serve
```

**启动 Flask 应用**：
```bash
python app.py
```

启动成功后会看到：
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
✅ Ollama客户端初始化成功，模型: llama3.2:3b
```

#### Step 7: 访问应用

- 🏠 **主页**：http://127.0.0.1:5000/
- 🔐 **登录**：http://127.0.0.1:5000/login
- 📝 **注册**：http://127.0.0.1:5000/register

---

## 📁 项目结构

```
Fintech2026/
├── app.py                      # Flask 主应用
├── requirements.txt            # Python 依赖列表
├── 启动项目.bat                # 一键启动脚本（Windows）
│
├── services/                   # 业务服务层
│   ├── face_service.py        # Face ID 服务
│   ├── pdf_service.py         # PDF 识别服务
│   ├── credit_limit_service.py # 信用评估服务
│   ├── register.py            # 注册管理
│   ├── lottery.py             # 抽奖核心逻辑
│   ├── lottery_prob.py        # AI 概率算法
│   └── abu_dhabi_service.py   # 🆕 AI 旅游推荐服务
│
├── models/                     # 机器学习模型
│   └── xgboost_simple_model.pkl  # XGBoost 信用评估模型（2 特征）
│
├── utils/                      # 工具类
│   ├── database.py            # 数据库操作
│   └── init_db.py             # 数据库初始化
│
├── config/                     # 配置文件
│   └── lottery_rules.py       # 抽奖规则配置
│
├── templates/                  # 前端页面
│   ├── index.html             # 主页（包含 AI 推荐）
│   ├── login.html             # 登录页
│   ├── register.html          # 注册页
│   └── static/                # 静态资源
│
├── uploads/                    # 上传文件
│   ├── faces/                 # 人脸照片
│   └── pdfs/                  # PDF 文件
│
├── instance/                   # 数据库
│   └── fintech.db             # SQLite 数据库
│
├── docs/                       # 📚 文档目录
│   ├── 环境配置指南.md         # Python、dlib 安装
│   ├── Ollama配置指南.md       # AI 推荐配置
│   ├── Face_ID使用说明.md      # 人脸识别说明
│   └── 代理配置说明.md         # 代理配置（可选）
│
├── tests/                      # 测试文件
│   ├── test_pdf.py
│   ├── test_face_recognition.py
│   └── install_dependencies.py
│
└── data/                       # 测试数据
    └── 消费流水.pdf
```

---

## 🎯 核心特性详解

### 1. 🔐 Face ID 人脸识别
- ✅ 注册时录入人脸（支持多角度）
- ✅ 登录时 Face ID 认证
- ✅ 完全免费（基于 face_recognition 库）
- ✅ 离线可用（本地处理，保护隐私）
- ✅ 高准确率（基于 dlib 深度学习模型）

**技术栈**：`face_recognition` + `dlib` + `opencv-python`

### 2. 📄 PDF 智能识别
- ✅ 自动提取银行流水（收入/支出/余额）
- ✅ 按月份分组统计
- ✅ 支持多种 PDF 格式
- ✅ 智能识别交易类型
- ✅ 自动计算月度收支

**技术栈**：`pdfplumber` + 正则表达式

### 3. 🤖 AI 信用评估
- ✅ XGBoost 简化模型（仅需 2 个特征）
- ✅ 快速预测（< 1 秒）
- ✅ 直接预测授信额度
- ✅ 基于收入和余额评估

**技术栈**：`XGBoost` + `scikit-learn` + `numpy`

**注册流程**：
```
上传银行流水 → 提取收入/支出/余额 → 上传余额证明 →
更新余额 → 模型预测 [收入, 余额] → 返回授信额度
```

### 4. 🎁 AI 盲盒抽奖
- ✅ 基于用户行为动态调整概率
- ✅ 新用户专属奖品
- ✅ 高消费用户获得更好奖品
- ✅ 智能权重衰减算法
- ✅ 防作弊机制

**算法特点**：
- 新用户权重加成：+30%
- 高消费用户权重加成：最高 +50%
- 动态概率调整：基于历史中奖记录

### 5. 🌍 AI 旅游推荐（新功能）

**核心技术**：
- **本地 LLM**：Ollama + Llama3.2:3b 模型
- **实时搜索**：DuckDuckGo HTML 搜索
- **智能翻译**：中文查询自动翻译为英文
- **个性化生成**：AI 根据搜索结果生成推荐

**功能亮点**：
- ✅ 完全免费（无需 API Key）
- ✅ 本地运行（保护隐私）
- ✅ 实时搜索（最新信息）
- ✅ 智能推荐（景点、美食、购物）
- ✅ 中英文支持

**推荐类型**：
1. 🏛️ **旅游景点** - 博物馆、地标、公园
2. 🍽️ **美食餐厅** - 当地特色、米其林餐厅
3. 🛍️ **购物中心** - 奢侈品、传统市集

**技术实现**：
```python
# 搜索流程
用户输入 → 中文翻译 → DuckDuckGo 搜索 → 提取结果 → Ollama AI 生成推荐
```

---

## 📚 详细文档

### 快速开始
- 🚀 [QUICKSTART.md](./QUICKSTART.md) - 5 分钟快速部署指南

### 配置指南
- 🔧 [环境配置指南](./docs/环境配置指南.md) - Python、dlib、依赖安装
- 🤖 [Ollama 配置指南](./docs/Ollama配置指南.md) - AI 推荐功能配置
- 🌐 [代理配置说明](./docs/代理配置说明.md) - 国内用户代理配置（可选）

### 功能说明
- 👤 [Face ID 使用说明](./docs/Face_ID使用说明.md) - 人脸识别功能详细说明

### API 接口文档

#### 1. 生成盲盒卡片
```http
POST /api/generate_blind_box
Content-Type: application/json

Response:
{
  "success": true,
  "cards": [
    {"id": 1, "prize_id": 5, "is_flipped": false},
    ...
  ]
}
```

#### 2. 翻开卡片
```http
POST /api/flip_card
Content-Type: application/json

{
  "card_id": 1
}

Response:
{
  "success": true,
  "prize": {
    "name": "消费券",
    "value": 50,
    "icon": "🎫"
  }
}
```

#### 3. 上传银行流水
```http
POST /api/upload_bank_statement
Content-Type: multipart/form-data

file: <PDF文件>

Response:
{
  "success": true,
  "data": {
    "monthly_data": [...],
    "total_income": 50000,
    "total_expense": 30000
  }
}
```

#### 4. 预测信用额度
```http
POST /api/predict_credit_limit
Content-Type: application/json

{
  "total_income": 90000,
  "balance": 50000
}

Response:
{
  "success": true,
  "credit_limit": 100000
}
```

#### 5. 🆕 获取 AI 旅游推荐
```http
GET /api/abu_dhabi_recommendations

Response:
{
  "success": true,
  "recommendations": [
    {
      "title": "Sheikh Zayed Grand Mosque",
      "description": "阿布扎比最著名的地标...",
      "url": "https://...",
      "icon": "🕌"
    },
    ...
  ],
  "timestamp": "2025-11-15T22:00:00"
}
```

---

## 🧪 测试账号

初始化数据库后，可使用以下测试账号：

| 字段 | 值 |
|------|-----|
| **用户名** | Yogurt |
| **用户 ID** | 1 |
| **卡号** | 5210 7132 0767 1316 |
| **WECoin** | 200 |
| **抽奖次数** | 10 |
| **授信额度** | ¥100,000 |

---

## 🔧 技术栈

### 后端
- **Web 框架**：Flask 3.0.0
- **数据库**：SQLite3（内置）
- **AI/ML**：
  - XGBoost 2.0.3（信用评估 - 2 特征简化模型）
  - face_recognition 1.3.0（人脸识别 - 基于 dlib）
  - Ollama + Llama3.2:3b（旅游推荐 - 本地 LLM）
- **PDF 处理**：pdfplumber 0.10.3
- **搜索引擎**：DuckDuckGo + BeautifulSoup4 4.12.2

### 前端
- **UI 框架**：原生 HTML5 + CSS3 + JavaScript
- **设计风格**：iOS 风格（灵动岛、毛玻璃效果）
- **响应式布局**：移动优先（390×844px）

---

## ❓ 常见问题

### 1. 数据库文件不存在
**问题**：`sqlite3.OperationalError: unable to open database file`

**解决**：
```bash
python utils/init_db.py
```

### 2. Flask 未安装
**问题**：`ModuleNotFoundError: No module named 'flask'`

**解决**：
```bash
pip install flask
# 或
pip install -r requirements.txt
```

### 3. dlib 安装失败
**问题**：`ERROR: Could not build wheels for dlib`

**解决**：
```bash
# 使用 conda 安装（推荐）
conda install -c conda-forge dlib -y

# 或下载预编译包（Windows）
pip install dlib-19.24.0-cp38-cp38-win_amd64.whl
```

### 4. Ollama 502 错误
**问题**：`❌ 生成推荐失败: (status code: 502)`

**解决**：
```powershell
# 1. 检查 Ollama 是否运行
ollama list

# 2. 确认模型已下载
ollama pull llama3.2:3b

# 3. 测试模型
ollama run llama3.2:3b "你好"

# 4. 重启 Ollama 服务
# 关闭当前 ollama serve，然后重新运行
ollama serve
```

### 5. DuckDuckGo 搜索失败
**问题**：`⚠️ 搜索未找到结果`

**解决**：
```python
# 方法 1: 启用代理（国内用户）
# 修改 app.py 第 35 行
use_proxy=True
proxy_url="http://127.0.0.1:7890"  # Clash 默认端口

# 方法 2: 检查网络连接
# 在浏览器访问 https://duckduckgo.com 测试
```

详细说明：[代理配置文档](./docs/代理配置说明.md)

### 6. 端口被占用
**问题**：`OSError: [Errno 48] Address already in use`

**解决**：
```powershell
# Windows 查找占用 5000 端口的进程
netstat -ano | findstr :5000

# 杀死进程
taskkill /PID <进程ID> /F

# 或修改端口
# 在 app.py 最后一行修改
app.run(debug=True, port=5001)
```

### 7. WECoin 不足
**问题**：翻卡时提示 WECoin 不足

**解决**：
```python
# 在 Python 控制台手动增加 WECoin
from utils.database import Database
db = Database('instance/fintech.db')
db.add_wecoin(user_id=1, amount=100)
```

### 8. 模型加载失败
**问题**：`❌ 模型加载失败`

**解决**：
```bash
# 确认模型文件存在
ls models/xgboost_simple_model.pkl

# 安装 xgboost
pip install xgboost
# 或
conda install -c conda-forge xgboost
```

### 9. Face ID 识别失败
**问题**：登录时人脸识别失败

**解决**：
- ✅ 确保光线充足
- ✅ 正面面对摄像头
- ✅ 移除眼镜、帽子等遮挡物
- ✅ 重新注册人脸（多角度录入）

### 10. PDF 识别失败
**问题**：上传 PDF 后无法提取数据

**解决**：
- ✅ 确保 PDF 是文本格式（非扫描件）
- ✅ 检查 PDF 格式是否符合银行流水格式
- ✅ 使用测试文件 `data/消费流水.pdf` 验证功能

---

## 📞 技术支持

遇到问题请检查：
1. ✅ Python 版本 ≥ 3.8
2. ✅ 所有依赖是否正确安装
3. ✅ 数据库是否已初始化
4. ✅ 端口 5000 是否被占用
5. ✅ 模型文件是否在正确位置
6. ✅ Ollama 服务是否运行
7. ✅ 代理配置是否正确（如需要）

**调试模式**：
```bash
# 启用详细日志
export FLASK_DEBUG=1
python app.py
```

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🙏 致谢

- [Flask](https://flask.palletsprojects.com/) - Web 框架
- [face_recognition](https://github.com/ageitgey/face_recognition) - 人脸识别
- [XGBoost](https://xgboost.readthedocs.io/) - 机器学习
- [Ollama](https://ollama.com/) - 本地 LLM 部署
- [DuckDuckGo](https://duckduckgo.com/) - 搜索引擎

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

**开始使用**: 双击 `启动项目.bat` 或运行 `python app.py`

**详细文档**: 查看 [docs/](./docs/) 目录

Made with ❤️ by Fintech2026 Team

</div>


