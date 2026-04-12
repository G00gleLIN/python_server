@echo off
REM 设置控制台代码页为 UTF-8
chcp 65001 >nul

REM 启动积木解析 WebSocket 服务
echo ========================================
echo 启动积木解析 WebSocket 服务
echo ========================================
echo.

REM 激活虚拟环境
if exist "venv\Scripts\activate.bat" (
    echo ✅ 激活虚拟环境...
    call venv\Scripts\activate.bat
    echo.
) else (
    echo ❌ 错误: 未找到虚拟环境
    echo 请确保 venv 目录存在
    pause
    exit /b 1
)

REM 检查是否安装了 websockets
echo 🔍 检查依赖...
python -c "import websockets" 2>nul
if errorlevel 1 (
    echo ⚠️  未安装 websockets 库，正在安装...
    pip install websockets
    if errorlevel 1 (
        echo ❌ 安装失败，请检查网络或手动安装: pip install websockets
        pause
        exit /b 1
    )
    echo ✅ websockets 安装成功
    echo.
) else (
    echo ✅ websockets 已安装
    echo.
)

echo 🚀 启动 WebSocket 服务...
echo 💡 按 Ctrl+C 停止服务
echo.

REM 启动 Python 服务
python block_server.py %1

echo.
pause
