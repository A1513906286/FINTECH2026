# 📚 Fintech2026 文档中心

欢迎来到 Fintech2026 虚拟信用卡系统的文档中心！

---

## 🚀 快速开始

### 新手入门
如果你是第一次使用本项目，建议按以下顺序阅读：

1. **[QUICKSTART.md](../QUICKSTART.md)** - 5 分钟快速部署
2. **[环境配置指南.md](./环境配置指南.md)** - 详细的环境配置
3. **[Ollama配置指南.md](./Ollama配置指南.md)** - AI 推荐功能配置

---

## 📖 文档列表

### 配置指南

#### 1. [环境配置指南.md](./环境配置指南.md)
**适用人群**：所有用户

**内容概览**：
- ✅ 系统要求
- ✅ Python 环境配置（Conda / pip）
- ✅ dlib 安装（3 种方法）
- ✅ 依赖安装
- ✅ 数据库初始化
- ✅ 验证安装

**阅读时间**：10 分钟

---

#### 2. [Ollama配置指南.md](./Ollama配置指南.md)
**适用人群**：需要使用 AI 旅游推荐功能的用户

**内容概览**：
- ✅ Ollama 是什么
- ✅ 安装 Ollama（Windows / macOS / Linux）
- ✅ 下载模型（llama3.2:3b）
- ✅ 启动服务
- ✅ 验证配置
- ✅ 性能优化
- ✅ 常见问题

**阅读时间**：15 分钟

---

#### 3. [代理配置说明.md](./代理配置说明.md)
**适用人群**：国内用户（可选）

**内容概览**：
- ✅ 为什么需要代理
- ✅ Clash 安装和配置
- ✅ 代理验证
- ✅ 项目中启用代理
- ✅ 不使用代理的替代方案

**阅读时间**：5 分钟

---

### 功能说明

#### 4. [Face_ID使用说明.md](./Face_ID使用说明.md)
**适用人群**：所有用户

**内容概览**：
- ✅ Face ID 功能概述
- ✅ 安装依赖（dlib + face_recognition）
- ✅ 注册流程（录入人脸）
- ✅ 登录流程（Face ID 认证）
- ✅ 技术原理
- ✅ 常见问题

**阅读时间**：10 分钟

---

## 🎯 按场景查找文档

### 场景 1: 我是新手，想快速体验项目
👉 阅读顺序：
1. [QUICKSTART.md](../QUICKSTART.md)
2. [环境配置指南.md](./环境配置指南.md)

### 场景 2: 我想使用 AI 旅游推荐功能
👉 阅读顺序：
1. [Ollama配置指南.md](./Ollama配置指南.md)
2. [代理配置说明.md](./代理配置说明.md)（国内用户）

### 场景 3: 我想了解 Face ID 功能
👉 直接阅读：
- [Face_ID使用说明.md](./Face_ID使用说明.md)

### 场景 4: 我遇到了安装问题
👉 查看：
- [环境配置指南.md](./环境配置指南.md) - 常见问题部分
- [Ollama配置指南.md](./Ollama配置指南.md) - 故障排查部分
- [主 README.md](../README.md) - 常见问题部分

---

## 🔧 技术文档

### API 接口文档
详见 [主 README.md - API 接口文档](../README.md#-api-接口文档)

### 项目结构
详见 [主 README.md - 项目结构](../README.md#-项目结构)

### 技术栈
详见 [主 README.md - 技术栈](../README.md#-技术栈)

---

## 📞 获取帮助

### 遇到问题？

1. **查看常见问题**：[主 README.md - 常见问题](../README.md#-常见问题)
2. **检查配置**：确保按照文档正确配置环境
3. **查看日志**：运行时的错误日志通常会提示问题所在

### 调试模式

启用详细日志：
```bash
export FLASK_DEBUG=1  # Linux/macOS
set FLASK_DEBUG=1     # Windows CMD
$env:FLASK_DEBUG=1    # Windows PowerShell

python app.py
```

---

## 📝 文档贡献

发现文档错误或有改进建议？欢迎提交 Issue 或 Pull Request！

---

<div align="center">

**🏠 返回主页**: [README.md](../README.md)

**🚀 快速开始**: [QUICKSTART.md](../QUICKSTART.md)

Made with ❤️ by Fintech2026 Team

</div>

