import subprocess
import sys
import time
import os
import requests

def install_dependencies():
    """Install required packages from requirements.txt"""
    print("正在检查依赖...")
    required_packages = [
        "streamlit",
        "openai",
        "streamlit-agraph",
        "networkx"
    ]
    
    # Check if requirements.txt exists, if not create it
    if not os.path.exists("requirements.txt"):
        with open("requirements.txt", "w") as f:
            for package in required_packages:
                f.write(f"{package}\n")
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("依赖安装完成。")
    except subprocess.CalledProcessError as e:
        print(f"依赖安装失败: {e}")
        sys.exit(1)

def check_ollama_status(base_url="http://localhost:11434"):
    """Check if Ollama is running"""
    print(f"正在检查 Ollama 服务状态 ({base_url})...")
    try:
        response = requests.get(base_url)
        if response.status_code == 200:
            print("Ollama 服务正常运行。")
            return True
    except requests.exceptions.ConnectionError:
        print("错误: 无法连接到 Ollama 服务。")
        print("请确保您已安装并启动了 Ollama (https://ollama.com/)。")
        print("在终端运行 'ollama serve' 或直接运行 Ollama 应用程序。")
        return False
    return False

def run_streamlit_app():
    """Run the Streamlit application"""
    print("正在启动 Streamlit 应用...")
    app_path = "event_net_gen.py"
    
    if not os.path.exists(app_path):
        print(f"错误: 找不到应用文件 {app_path}")
        sys.exit(1)
        
    cmd = [sys.executable, "-m", "streamlit", "run", app_path]
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n应用已停止。")
    except subprocess.CalledProcessError as e:
        print(f"应用运行出错: {e}")

if __name__ == "__main__":
    print("=== 本地事件网络生成器启动脚本 ===")
    
    # 1. Install dependencies
    install_dependencies()
    
    # 2. Check Ollama
    if not check_ollama_status():
        # Optional: Ask user if they want to continue anyway (e.g. if using remote Ollama)
        choice = input("Ollama 未检测到。如果您使用的是远程服务或稍后启动，请输入 'y' 继续，否则按任意键退出: ")
        if choice.lower() != 'y':
            sys.exit(1)
    
    # 3. Run App
    run_streamlit_app()
