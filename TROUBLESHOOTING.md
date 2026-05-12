# 故障排查：为什么无法访问页面？

如果浏览器显示“无法访问此页面”或“连接被拒绝”，请按照以下步骤检查：

## 1. 检查控制台输出
请回到 PyCharm 的运行控制台（Run 窗口），查看是否有报错信息。

- **正常情况**：应该看到类似下面的信息：
  ```
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
  ```
- **如果程序已退出**：说明启动失败了。请检查控制台的错误日志（例如 `ModuleNotFoundError` 或 `Ollama connection failed`）。

## 2. 确认访问地址
Streamlit 默认端口是 **8501**。
- 请尝试访问：[http://localhost:8501](http://localhost:8501)
- 如果 8501 被占用，它可能会自动切换到 **8502**，请尝试：[http://localhost:8502](http://localhost:8502)

## 3. 检查 Ollama 是否运行
如果应用启动时尝试连接 Ollama 失败，可能会导致页面加载不出来。
- 请在浏览器访问：[http://localhost:11434](http://localhost:11434)
- 如果显示 `Ollama is running`，说明模型服务正常。
- 如果无法访问，请先启动 Ollama 软件。

## 4. 手动启动尝试
如果 `run_local.py` 脚本有问题，请尝试在 PyCharm 的 **Terminal** (终端) 中手动运行：

1. 确保虚拟环境已激活（命令行前有 `(.venv)` 字样）。如果没有，输入 `.venv\Scripts\activate`。
2. 输入命令：
   ```bash
   streamlit run event_net_gen.py
   ```
3. 观察终端输出的错误信息。

## 5. 端口被占用？
有时候旧的进程没有完全关闭。
- 尝试关闭 PyCharm 的所有运行窗口。
- 打开任务管理器，结束所有 `python.exe` 进程。
- 重新运行项目。
