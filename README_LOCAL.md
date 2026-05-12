# 本地运行指南 (脱离 Google AI)

本项目已修改为支持 **本地大模型 (Local LLM)**，默认使用 **Ollama**。这意味着您不需要 Google API Key，所有数据都在本地处理。

## 🚀 快速开始

### 1. 准备本地模型 (Ollama)
这是核心步骤。您需要安装 Ollama 来运行本地 AI 模型。

1.  **下载 Ollama**: 访问 [https://ollama.com/](https://ollama.com/) 下载并安装。
2.  **下载模型**: 打开终端 (Terminal) 或命令提示符，运行以下命令下载一个中文能力较好的模型（推荐 Qwen 2.5 或 Llama 3）：
    ```bash
    ollama run qwen2.5
    ```
    *(或者 `ollama run llama3`)*
3.  **保持运行**: 确保 Ollama 在后台运行（通常安装后会自动运行，或者在终端输入 `ollama serve`）。

### 2. 在 PyCharm 中运行

#### 方式 A: 使用启动脚本 (推荐)
1.  在 PyCharm 中右键点击 `run_local.py`。
2.  选择 **Run 'run_local'**。
3.  脚本会自动安装依赖 (`streamlit`, `openai`, `graphviz`) 并启动网页。

#### 方式 B: 手动运行
1.  打开 PyCharm 终端。
2.  安装依赖: `pip install -r requirements.txt`
3.  运行应用: `streamlit run event_net_gen.py`

### 3. 使用说明

1.  应用启动后，浏览器会自动打开。
2.  在左侧侧边栏，确认 **API Base URL** 为 `http://localhost:11434/v1` (这是 Ollama 的默认地址)。
3.  确认 **模型名称** 与您在 Ollama 中下载的模型一致 (例如 `qwen2.5` 或 `qwen2.5:latest`)。
4.  输入故事梗概，点击“构建事件网络”。

## 📦 依赖说明

-   **Streamlit**: 用于构建 Web 界面。
-   **OpenAI (Python SDK)**: 用于连接 Ollama (Ollama 兼容 OpenAI 的 API 格式)。
-   **Graphviz**: 用于绘制流程图。
    -   *注意*: 如果图表无法显示，请确保您的电脑安装了 Graphviz 软件 (不仅仅是 pip 包)。
    -   Windows: [下载安装包](https://graphviz.org/download/)
    -   Mac: `brew install graphviz`

## 常见问题

**Q: 报错 "CreateProcess error=2, 系统找不到指定的文件"?**
A: 这是因为 PyCharm 记录的 Python 环境路径失效了。
**解决方法**:
1.  在项目文件夹中找到我为您生成的 `setup.bat` 文件。
2.  双击运行它。它会删除旧的 `.venv` 文件夹并重新创建一个全新的环境。
3.  回到 PyCharm，点击右下角的解释器设置 (通常显示为 `<No Interpreter>` 或 `Python 3.x`)。
4.  选择 **Add New Interpreter** -> **Add Local Interpreter**。
5.  选择 **Existing**，然后浏览到项目目录下的 `.venv\Scripts\python.exe`。

**Q: 报错 "Connection refused" 或 "无法连接"?**
A: 请检查 Ollama 是否正在运行。在浏览器访问 `http://localhost:11434`，如果显示 "Ollama is running"，则说明正常。

**Q: 生成的 JSON 格式错误?**
A: 本地小模型（如 7B 参数以下）遵循指令的能力可能不如云端大模型。尝试使用更强的模型（如 `qwen2.5:14b` 或 `llama3:8b`），或者多试几次。
