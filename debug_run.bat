@echo off
chcp 65001 >nul
echo ==========================================
echo      调试模式启动 (Debug Run)
echo ==========================================

cd /d "%~dp0"

if not exist .venv (
    echo 错误: 未找到 .venv 环境。请先运行 setup.bat。
    pause
    exit /b
)

echo 正在激活虚拟环境...
call .venv\Scripts\activate

echo 正在检查依赖...
pip install -r requirements.txt

echo.
echo 正在启动 Streamlit...
echo ==========================================
echo 如果启动失败，请查看下方的错误信息 (Error)
echo ==========================================
streamlit run event_net_gen.py
echo ==========================================
echo 程序已退出。
pause
