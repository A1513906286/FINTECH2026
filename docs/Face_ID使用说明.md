# Face ID 功能使用说明

## 🎯 功能概述

已成功集成开源免费的人脸识别功能到注册和登录流程：

- ✅ **注册时录入Face ID** - 在注册流程第一步录入人脸
- ✅ **登录时Face ID认证** - 点击Face ID图标即可刷脸登录
- ✅ **完全免费** - 基于face_recognition库，无需API密钥
- ✅ **离线可用** - 所有处理在本地完成

---

## 📦 安装依赖

### 使用conda（推荐）

```bash
# 1. 安装dlib
conda install -c conda-forge dlib -y

# 2. 安装其他依赖
pip install face_recognition opencv-python numpy Pillow

# 3. 初始化数据库
python init_db.py

# 4. 启动服务器
python app.py
```

### 使用pip

```bash
# 1. 安装所有依赖
pip install face_recognition opencv-python numpy Pillow

# 2. 初始化数据库
python init_db.py

# 3. 启动服务器
python app.py
```

**注意**: Windows用户安装dlib可能遇到问题，推荐使用conda。

---

## 🚀 使用流程

### 注册时录入Face ID

1. 访问注册页面：`http://127.0.0.1:5000/register`
2. 在第一步"录入FaceID信息"：
   - 点击"启动摄像头"
   - 正对摄像头，确保光线充足
   - 点击"拍照录入"
   - 等待识别完成（约1-2秒）
   - 自动进入下一步
3. 完成其他注册步骤
4. Face ID会随注册信息一起保存

### 登录时使用Face ID

1. 访问登录页面：`http://127.0.0.1:5000/login`
2. 点击中间的"Face ID"图标
3. 允许浏览器访问摄像头
4. 系统自动拍照并识别（约1-2秒）
5. 识别成功后自动登录

---

## 🔌 API接口说明

### 1. 注册Face ID

**接口**: `POST /api/register_face`

**请求体**:
```json
{
    "image": "base64编码的图片",
    "user_id": 1
}
```

**响应**:
```json
{
    "success": true,
    "message": "Face ID注册成功！"
}
```

### 2. Face ID登录

**接口**: `POST /api/login_with_face`

**请求体**:
```json
{
    "image": "base64编码的图片"
}
```

**响应**:
```json
{
    "success": true,
    "user_id": 1,
    "similarity": 95.6,
    "message": "识别成功，相似度: 95.6%"
}
```

### 3. 检查Face ID状态

**接口**: `GET /api/check_face_id/<user_id>`

**响应**:
```json
{
    "success": true,
    "has_face_id": true
}
```

---

## 📊 数据库设计

### user 表新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| face_encoding | TEXT | 人脸特征编码（128维向量，JSON格式） |
| face_image_path | TEXT | 人脸照片存储路径 |
| face_registered_at | DATETIME | Face ID注册时间 |

### face_login_logs 表（新增）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| user_id | INTEGER | 用户ID |
| similarity_score | REAL | 相似度分数 |
| login_time | DATETIME | 登录时间 |
| login_success | INTEGER | 是否成功（1成功，0失败） |
| ip_address | TEXT | IP地址 |

---

## 🎨 前端集成示例

### HTML - 摄像头控制

```html
<video id="video" autoplay></video>
<button onclick="startCamera()">启动摄像头</button>
<button onclick="registerFace()">注册Face ID</button>
```

### JavaScript - 拍照并注册

```javascript
// 启动摄像头
async function startCamera() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    document.getElementById('video').srcObject = stream;
}

// 拍照并转Base64
function capturePhoto() {
    const video = document.getElementById('video');
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0);
    return canvas.toDataURL('image/jpeg').split(',')[1];
}

// 注册Face ID
async function registerFace() {
    const imageBase64 = capturePhoto();
    
    const response = await fetch('/api/register_face', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            image: imageBase64,
            user_id: 1
        })
    });
    
    const result = await response.json();
    alert(result.message);
}
```

---

## ⚙️ 配置参数

在 `face_service.py` 中可以调整：

```python
class FaceRecognitionService:
    def __init__(self):
        # 相似度阈值（距离越小越相似）
        # 默认0.6，可调整范围：0.4-0.7
        # 0.4 = 更严格，0.7 = 更宽松
        self.tolerance = 0.6
```

---

## 🔧 故障排除

### 问题1：dlib安装失败

**解决方案**：
```bash
# 使用conda安装
conda install -c conda-forge dlib

# 或下载预编译wheel
# https://github.com/z-mahmud22/Dlib_Windows_Python3.x
```

### 问题2：摄像头无法启动

**解决方案**：
- 检查浏览器权限（允许访问摄像头）
- 使用HTTPS或localhost
- 检查其他程序是否占用摄像头

### 问题3：识别失败

**可能原因**：
- 光线不足 → 在明亮处拍摄
- 角度不正 → 正面拍摄
- 距离太远/太近 → 调整距离
- 人脸被遮挡 → 移除口罩/墨镜

### 问题4：相似度过低

**解决方案**：
- 调整 `tolerance` 参数（增大到0.7）
- 重新注册人脸（在更好的光线条件下）
- 确保注册和登录时的角度相似

---

## 📈 性能优化

### 1. 加速人脸检测

```python
# 使用更快的检测模型（准确率略低）
face_locations = face_recognition.face_locations(image, model="cnn")  # 默认
face_locations = face_recognition.face_locations(image, model="hog")  # 更快
```

### 2. 减少图片尺寸

```python
# 在前端压缩图片
canvas.width = 640;  # 降低分辨率
canvas.height = 480;
```

### 3. 缓存人脸特征

当前实现已经缓存了所有用户的人脸特征在数据库中，登录时只需比对，无需重新提取。

---

## 🎯 下一步

1. ✅ **已完成**: Face ID注册和登录功能
2. 🔄 **进行中**: 集成到注册页面和登录页面
3. 📋 **待完成**: 护照OCR识别
4. 📋 **待完成**: PDF文件解析

---

## 📚 参考资料

- [face_recognition 官方文档](https://github.com/ageitgey/face_recognition)
- [dlib 官方文档](http://dlib.net/)
- [OpenCV 官方文档](https://opencv.org/)

---

## 💡 提示

- 人脸照片存储在 `uploads/faces/` 目录
- 人脸特征编码存储在数据库的 `face_encoding` 字段（JSON格式）
- 每次登录都会记录日志到 `face_login_logs` 表
- 相似度阈值可以根据实际情况调整

需要帮助？查看 `test_face_id.html` 的完整示例代码！

