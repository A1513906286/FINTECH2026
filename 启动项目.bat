@echo off
chcp 65001 >nul
echo ========================================
echo   Fintech2026 虚拟信用卡项目启动脚本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [✓] Python已安装
python --version
echo.

REM 检查Flask是否安装
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Flask未安装，正在安装...
    pip install flask
    if %errorlevel% neq 0 (
        echo [错误] Flask安装失败
        pause
        exit /b 1
    )
    echo [✓] Flask安装成功
) else (
    echo [✓] Flask已安装
)
echo.

REM 检查数据库是否存在
if not exist "instance\fintech.db" (
    echo [!] 数据库不存在，正在初始化...
    python utils\init_db.py
    if %errorlevel% neq 0 (
        echo [错误] 数据库初始化失败
        pause
        exit /b 1
    )
    echo [✓] 数据库初始化成功
) else (
    echo [✓] 数据库已存在
)
echo.

REM 检查 Ollama 是否安装（AI 推荐功能需要）
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Ollama 未安装（AI 推荐功能将不可用）
    echo [提示] 下载地址: https://ollama.com/download
    echo [提示] 安装后运行: ollama pull llama3.2:3b
    echo.
) else (
    echo [✓] Ollama 已安装
    ollama --version

    REM 检查模型是否下载
    ollama list | findstr "llama3.2:3b" >nul 2>&1
    if %errorlevel% neq 0 (
        echo [!] Llama3.2:3b 模型未下载
        echo [提示] 运行命令下载: ollama pull llama3.2:3b
        echo.
    ) else (
        echo [✓] Llama3.2:3b 模型已就绪

        REM 检查 Ollama 服务是否运行
        curl -s http://127.0.0.1:11434/api/tags >nul 2>&1
        if %errorlevel% neq 0 (
            echo [!] Ollama 服务未运行
            echo [提示] 请在新终端窗口运行: ollama serve
            echo.
        ) else (
            echo [✓] Ollama 服务运行中
        )
    )
)
echo.

echo ========================================
echo   启动Flask服务器...
echo ========================================
echo.
echo 服务器地址: http://127.0.0.1:5000
echo 主页: http://127.0.0.1:5000/
echo 登录页: http://127.0.0.1:5000/login
echo 注册页: http://127.0.0.1:5000/register
echo.
echo 按 Ctrl+C 停止服务器
echo ========================================
echo.

REM 启动Flask应用
python app.py

pause

