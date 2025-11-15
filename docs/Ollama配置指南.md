# 🤖 Ollama 配置指南

本文档详细介绍如何配置 Ollama 本地 LLM 服务，为 Fintech2026 提供 AI 旅游推荐功能。

---

## 📋 目录

1. [什么是 Ollama](#什么是-ollama)
2. [安装 Ollama](#安装-ollama)
3. [下载模型](#下载模型)
4. [启动服务](#启动服务)
5. [验证配置](#验证配置)
6. [性能优化](#性能优化)
7. [常见问题](#常见问题)

---

## 什么是 Ollama

**Ollama** 是一个本地运行大语言模型（LLM）的工具，类似于 Docker 但专为 AI 模型设计。

### 为什么选择 Ollama？

✅ **完全免费** - 无需 API Key，无使用限制  
✅ **本地运行** - 保护隐私，数据不上传  
✅ **离线可用** - 无需网络连接  
✅ **易于使用** - 一键安装，简单命令  
✅ **多模型支持** - Llama, Mistral, Gemma 等  

### Fintech2026 如何使用 Ollama？

```
用户查询 → DuckDuckGo 搜索 → Ollama AI 分析 → 生成推荐
```

例如：
- 输入："阿布扎比购物中心"
- 搜索：DuckDuckGo 返回 5 条结果
- AI 分析：Ollama 理解内容并生成推荐
- 输出：3 条精选推荐（景点、美食、购物）

---

## 安装 Ollama

### Windows

#### 方法一：官方安装包（推荐）

1. 访问 [Ollama 官网](https://ollama.com/download)
2. 点击 "Download for Windows"
3. 运行 `OllamaSetup.exe`
4. 安装完成后，Ollama 会自动启动

#### 方法二：命令行安装

```powershell
# 使用 winget
winget install Ollama.Ollama
```

#### 验证安装

```powershell
ollama --version
# 输出: ollama version is 0.x.x
```

### macOS

```bash
# 使用 Homebrew
brew install ollama

# 或下载安装包
# https://ollama.com/download
```

### Linux

```bash
# 一键安装脚本
curl -fsSL https://ollama.com/install.sh | sh

# 或手动安装
# Ubuntu/Debian
sudo apt-get install ollama

# Fedora
sudo dnf install ollama
```

---

## 下载模型

### 推荐模型：Llama3.2 3B

```bash
ollama pull llama3.2:3b
```

**特点**：
- 大小：2.0 GB
- 速度：快速响应（1-3 秒）
- 质量：高质量中文支持
- 显存：需要 4GB+ VRAM（或 8GB+ RAM）

### 其他模型选择

#### 1. 更小的模型（更快，但效果稍差）

```bash
# Llama3.2 1B - 仅 1GB
ollama pull llama3.2:1b
```

#### 2. 量化模型（节省显存）

```bash
# 4-bit 量化版本
ollama pull llama3.2:3b-q4_0

# 8-bit 量化版本
ollama pull llama3.2:3b-q8_0
```

#### 3. 其他语言模型

```bash
# Mistral 7B（英文更好）
ollama pull mistral:7b

# Gemma 2B（Google 出品）
ollama pull gemma:2b

# Qwen 7B（中文优化）
ollama pull qwen:7b
```

### 查看已安装的模型

```bash
ollama list
```

输出示例：
```
NAME           ID              SIZE      MODIFIED
llama3.2:3b    a80c4f17acd5    2.0 GB    2 hours ago
```

### 删除模型

```bash
ollama rm llama3.2:3b
```

---

## 启动服务

### 方法一：自动启动（Windows）

安装后 Ollama 会自动在后台运行，无需手动启动。

**检查服务状态**：
```powershell
# 访问 API
curl http://127.0.0.1:11434/api/tags
```

### 方法二：手动启动

```bash
ollama serve
```

**输出示例**：
```
time=2025-11-15T22:42:48.959+08:00 level=INFO msg="Listening on 127.0.0.1:11434"
time=2025-11-15T22:42:50.052+08:00 level=INFO msg="inference compute" name=CUDA0 description="NVIDIA GeForce RTX 4060"
```

**注意**：
- 保持终端窗口打开
- 服务运行在 `http://127.0.0.1:11434`
- 按 `Ctrl+C` 停止服务

### 方法三：后台运行（Linux/macOS）

```bash
# 使用 systemd（Linux）
sudo systemctl start ollama
sudo systemctl enable ollama  # 开机自启

# 使用 nohup（通用）
nohup ollama serve > ollama.log 2>&1 &
```

---

## 验证配置

### 1. 测试 API 连接

```bash
curl http://127.0.0.1:11434/api/tags
```

应该返回已安装的模型列表。

### 2. 测试模型推理

```bash
ollama run llama3.2:3b "你好，请介绍一下阿布扎比"
```

应该返回中文回复。

### 3. 测试 HTTP API

```bash
curl -X POST http://127.0.0.1:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.2:3b",
    "messages": [
      {"role": "user", "content": "你好"}
    ],
    "stream": false
  }'
```

### 4. 在 Fintech2026 中测试

1. 启动 Ollama 服务：`ollama serve`
2. 启动 Flask 应用：`python app.py`
3. 访问测试页面：http://127.0.0.1:5000/test_recommendations
4. 应该看到 "✅ 成功获取 3 条推荐！"

---

## 性能优化

### 1. GPU 加速

**检查 GPU 是否被使用**：
```bash
ollama serve
# 日志中应该看到：
# level=INFO msg="inference compute" name=CUDA0 description="NVIDIA ..."
```

**如果没有检测到 GPU**：
- 确保安装了 NVIDIA 驱动
- 确保安装了 CUDA Toolkit
- 重启 Ollama 服务

### 2. 调整并发数

编辑 `app.py` 中的 Ollama 配置：

```python
# 在 abu_dhabi_service.py 的 generate_recommendations 方法中
payload = {
    "model": self.model_name,
    "messages": [...],
    "stream": False,
    "options": {
        'temperature': 0.7,  # 降低温度提高一致性
        'num_predict': 300,  # 减少生成长度提高速度
        'num_ctx': 2048,     # 减少上下文长度节省显存
    }
}
```

### 3. 使用量化模型

```bash
# 下载 4-bit 量化模型（速度更快，显存占用更少）
ollama pull llama3.2:3b-q4_0

# 修改 app.py 第 34 行
model_name="llama3.2:3b-q4_0"
```

### 4. 预加载模型

```bash
# 预先加载模型到内存
ollama run llama3.2:3b ""
```

---

## 常见问题

### 1. 端口被占用

**问题**：`Error: listen tcp 127.0.0.1:11434: bind: address already in use`

**原因**：Ollama 已经在运行

**解决**：
```powershell
# 无需重复启动，直接使用即可

# 或杀死进程重启
taskkill /F /IM ollama.exe
ollama serve
```

### 2. 模型下载失败

**问题**：下载速度慢或失败

**解决**：
```bash
# 使用代理下载
set HTTP_PROXY=http://127.0.0.1:7890
set HTTPS_PROXY=http://127.0.0.1:7890
ollama pull llama3.2:3b

# 或手动下载模型文件
# 访问 https://ollama.com/library/llama3.2
```

### 3. 显存不足

**问题**：`failed to allocate memory`

**解决**：
```bash
# 方法 1: 使用更小的模型
ollama pull llama3.2:1b

# 方法 2: 使用量化模型
ollama pull llama3.2:3b-q4_0

# 方法 3: 使用 CPU 运行
# 设置环境变量
set OLLAMA_NUM_GPU=0
ollama serve
```

### 4. 响应速度慢

**问题**：生成推荐需要 10+ 秒

**解决**：
- ✅ 使用 GPU 加速
- ✅ 使用更小的模型（llama3.2:1b）
- ✅ 减少生成长度（num_predict=200）
- ✅ 预加载模型到内存

### 5. 中文乱码

**问题**：返回的中文显示为乱码

**解决**：
```python
# 确保 Python 文件使用 UTF-8 编码
# 在文件开头添加
# -*- coding: utf-8 -*-
```

---

## 高级配置

### 1. 修改默认端口

```bash
# 设置环境变量
set OLLAMA_HOST=0.0.0.0:11435
ollama serve
```

### 2. 启用调试日志

```bash
set OLLAMA_DEBUG=1
ollama serve
```

### 3. 限制显存使用

```bash
# 限制使用 4GB 显存
set OLLAMA_GPU_OVERHEAD=4096
ollama serve
```

---

## 下一步

✅ Ollama 配置完成后：
1. 阅读 [代理配置说明](./代理配置说明.md) 配置 DuckDuckGo 访问
2. 启动 Flask 应用测试 AI 推荐功能
3. 尝试不同的模型和参数优化性能

---

<div align="center">

**🚀 开始使用**: `ollama serve` + `python app.py`

**💬 遇到问题**: 查看 [常见问题](#常见问题) 或访问 [Ollama 官方文档](https://ollama.com/docs)

</div>

