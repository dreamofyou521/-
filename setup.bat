@echo off
chcp 65001 >nul
echo ==========================================
echo      修复 Python 环境 (Windows)
echo ==========================================

cd /d "%~dp0"

echo [1/4] 清理旧环境...
if exist .venv (
    rmdir /s /q .venv
    echo 已删除旧 .venv 文件夹
) else (
    echo 旧 .venv 不存在，跳过清理
)

echo [2/4] 创建新虚拟环境...
python -m venv .venv
if errorlevel 1 (
    echo 错误: 创建虚拟环境失败。请确保您已安装 Python 并将其添加到 PATH。
    echo 您可以在命令行输入 python --version 检查。
    pause
    exit /b
)

echo [3/4] 激活环境并安装依赖...
call .venv\Scripts\activate
python -m pip install --upgrade pip
if exist requirements.txt (
    pip install -r requirements.txt
    echo 依赖安装完成。
) else (
    echo 警告: 未找到 requirements.txt，跳过依赖安装。
)

echo [4/4] 完成！
echo ==========================================
echo 请在 PyCharm 中重新选择解释器：
echo 1. 打开 PyCharm 设置 (File - Settings)
echo 2. Project: 事件网络生成器 - Python Interpreter
echo 3. 点击右侧齿轮图标 - Add Interpreter - Add Local Interpreter
echo 4. 选择 "Existing" (现有)
echo 5. 浏览并选择本目录下的: .venv\Scripts\python.exe
echo ==========================================
pause
