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
- **PDF 智能识别** - 自动提取银行流水和余额证明（支持12个核心财务指标）
- **AI 信用评估** - Home Credit XGBoost模型 + EV优化算法
  - 违约概率预测（PD Model）
  - 额度利用率预测（Utilization Model）
  - 基于期望价值最大化的额度优化
  - 智能杠杆率调整机制
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
│   ├── pdf_service.py         # PDF 识别服务（提取交易数据）
│   ├── feature_engineering_service.py # 特征工程（13个指标）
│   ├── pd_model_service.py    # 违约概率预测模型
│   ├── utilization_model_service.py # 利用率预测模型
│   ├── credit_optimizer_service.py # 额度优化器（EV最大化）
│   ├── credit_limit_service.py # 信用评估服务（主入口）
│   ├── register.py            # 注册管理
│   ├── lottery.py             # 抽奖核心逻辑
│   ├── lottery_prob.py        # AI 概率算法
│   ├── search_service.py      # 搜索服务
│   └── abu_dhabi_service.py   # AI 旅游推荐服务
│
├── models/                     # 机器学习模型
│   ├── hc_pd_model.pkl        # 违约概率模型（13特征）
│   └── hc_utilization_model.pkl # 利用率模型（13特征）
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

### 3. 🤖 AI 信用评估（Home Credit完整模型系统）

**核心组件**：
- ✅ **PDF解析服务** - 提取银行流水交易数据
- ✅ **特征工程服务** - 计算13个核心财务指标
- ✅ **违约概率模型 (PD)** - XGBoost预测违约风险
- ✅ **利用率模型** - XGBoost预测额度使用率
- ✅ **额度优化器** - 基于EV最大化原则计算最优额度

**13个核心特征**：
1. **收入能力** (3个) - 3个月平均收入、收入方差、总收入
2. **支出能力** (3个) - 大额支出、月消费、收支比
3. **偿还能力** (5个) - 当前余额、余额收入比、最低余额、还款压力、大额取现比
4. **额度相关** (2个) - 候选额度、杠杆率（额度/收入比）

**预测指标**：
- **违约概率 (PD)** - 预测用户违约风险，额度越高→PD越高（指数增长）
- **利用率** - 预测额度使用率，额度越大→利用率越低（指数衰减）
- **预期价值 (EV)** - 计算公式：`EV = 利息收入 - 预期损失`
  - 利息收入 = 额度 × 利用率 × APR (36%)
  - 预期损失 = 额度 × 利用率 × PD × LGD (80%)

**优化策略**：
- 候选额度范围：余额的 **1x - 10x**
- 选择预期价值最高的额度作为最优授信额度
- 智能杠杆率调整机制确保风险随额度增长

**技术栈**：`XGBoost` + `scikit-learn` + `numpy` + `pandas`

**注册流程**：
```
上传银行流水PDF → 提取交易数据 → 计算13个指标 →
PD模型预测 → 利用率模型预测 → EV优化 → 返回最优授信额度
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

## 💡 信用评估系统详解

### 系统架构

```
PDF上传 → PDF解析 → 特征工程 → 模型预测 → 额度优化 → 返回结果
```

### 1. PDF解析服务 (`pdf_service.py`)
**功能**：从银行流水PDF中提取交易数据
- 识别交易类型（收入/支出/ATM取现/POS消费/转账）
- 按月份分组统计
- 计算基础财务指标

### 2. 特征工程服务 (`feature_engineering_service.py`)
**功能**：将PDF数据转换为13个模型特征

| 类别 | 特征 | 说明 |
|------|------|------|
| **收入能力** | avg_income_3m | 过去3个月平均收入 |
| | income_variance_3m | 3个月收入方差（稳定性） |
| | total_income | 总收入 |
| **支出能力** | avg_large_spending | 大额支出平均值 |
| | avg_monthly_consumption | 平均月消费 |
| | income_consumption_ratio | 收入/消费比 |
| **偿还能力** | current_balance | 当前余额 |
| | balance_income_ratio | 余额/收入比 |
| | min_balance_12m | 12个月最低余额 |
| | payday_plus_5_drop | 发薪日后5天余额下降 |
| | large_withdrawal_ratio | 大额取现比例 |
| **额度相关** | credit_amount | 候选额度 |
| | credit_to_income_ratio | 杠杆率（额度/收入） |

### 3. 违约概率模型 (`pd_model_service.py`)
**功能**：预测用户违约概率（PD）

**核心机制**：
```python
# 基础预测
base_PD = XGBoost模型预测(13个特征)

# 杠杆率调整（确保额度越高→PD越高）
leverage_ratio = credit_amount / total_income
scaled_base = base_PD × 0.7  # 缩小基础PD
multiplier = exp(1.0 × leverage_ratio)  # 指数增长
adjusted_PD = scaled_base × multiplier
adjusted_PD = clip(adjusted_PD, 0, 0.70)  # 上限70%
```

**效果示例**（假设base_PD = 40%）：
- 杠杆率 0.1 → PD ≈ 31%
- 杠杆率 0.5 → PD ≈ 46%
- 杠杆率 1.0 → PD ≈ 76% → 限制为70%
- 杠杆率 2.0 → PD ≈ 70%（触及上限）

### 4. 利用率模型 (`utilization_model_service.py`)
**功能**：预测额度使用率

**核心机制**：
```python
# 基础预测
base_utilization = XGBoost模型预测(13个特征)

# 杠杆率调整（确保额度越大→利用率越低）
leverage_ratio = credit_amount / total_income
multiplier = exp(-0.35 × leverage_ratio)  # 指数衰减
adjusted_utilization = base_utilization × multiplier
adjusted_utilization = clip(adjusted_utilization, 0.30, 0.95)
```

**效果示例**：
- 杠杆率 0.1 → 利用率 ≈ 85-90%（额度小，容易用满）
- 杠杆率 0.5 → 利用率 ≈ 70-75%
- 杠杆率 1.0 → 利用率 ≈ 55-60%
- 杠杆率 2.0 → 利用率 ≈ 40-45%（额度大，用不完）

### 5. 额度优化器 (`credit_optimizer_service.py`)
**功能**：基于EV最大化原则计算最优额度

**优化算法**：
```python
# 候选额度：余额的1x到10x
candidate_amounts = [balance × 1.0, balance × 1.5, ..., balance × 10.0]

# 对每个候选额度计算EV
for amount in candidate_amounts:
    PD = pd_model.predict(features)
    utilization = utilization_model.predict(features)

    # 计算预期价值
    exposure = amount × utilization
    interest_income = exposure × APR (36%)
    expected_loss = exposure × PD × LGD (80%)
    expected_value = interest_income - expected_loss

# 选择EV最大的额度
optimal_amount = max(candidate_amounts, key=lambda x: EV(x))
```

**风险参数**：
- **APR（年化利率）**：36%
- **LGD（违约损失率）**：80%
- **候选倍数**：[1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]

### 预测结果示例

**输入**：
- 总收入：¥74,707.66
- 当前余额：¥4,204.74

**输出**：
```
所有候选额度的评估结果:
------------------------------------------------------------
倍数      额度         违约概率    利用率      预期价值
------------------------------------------------------------
1.0x  ¥  4,204.74    14.79%    80.81%  ¥    821.22
1.5x  ¥  6,307.11    15.21%    80.02%  ¥  1,202.72
2.0x  ¥  8,409.48    15.65%    79.23%  ¥  1,564.76
2.5x  ¥ 10,511.85    16.09%    78.46%  ¥  1,907.32
...
10.0x ¥ 42,047.40    23.90%    67.68%  ¥  4,803.33
------------------------------------------------------------

最优额度: ¥42,047.40 (10.0x余额)
预期价值: ¥4,803.33
违约概率: 23.90%
风险等级: 较高风险
```

---

## 📚 详细文档

### 快速开始
- 🚀 [QUICKSTART.md](./QUICKSTART.md) - 3分钟快速部署指南
- 📋 [PROJECT_SUMMARY.md](./PROJECT_SUMMARY.md) - 项目总结

### 配置指南
- 🔧 [环境配置指南](./docs/环境配置指南.md) - Python、dlib、依赖安装
- 🤖 [Ollama 配置指南](./docs/Ollama配置指南.md) - AI 推荐功能配置
- 🌐 [代理配置说明](./docs/代理配置说明.md) - 国内用户代理配置（可选）

### 功能说明
- 👤 [Face ID 使用说明](./docs/Face_ID使用说明.md) - 人脸识别功能详细说明

### API 文档
- 📡 [API_REFERENCE.md](./API_REFERENCE.md) - 完整API参考文档

### 测试脚本
- 🧪 [test_pdf_features.py](./test_pdf_features.py) - PDF提取和信用评估测试



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
  - XGBoost 2.0.3（信用评估 - Home Credit完整模型，13特征）
  - face_recognition 1.3.0（人脸识别 - 基于 dlib）
  - Ollama + Llama3.2:3b（旅游推荐 - 本地 LLM）
- **PDF 处理**：pdfplumber 0.10.3
- **数据处理**：pandas 2.0.0, numpy 1.24.0
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


