# -*- coding: utf-8 -*-
"""
白洞计划 v3.0 — 桌面启动入口（pywebview 封装）
直接运行：python main.py
"""

import sys
import os
import subprocess
import threading
import time
import socket
import urllib.request

# 依赖请通过 `pip install -r requirements.txt` 安装；启动时不再自动 pip install。
try:
    import webview  # noqa: E402
except ImportError as exc:  # pragma: no cover - runtime environment hint
    raise SystemExit("缺少 pywebview，请先运行：pip install -r requirements.txt") from exc
from api.pywebview_api import Api  # noqa: E402
from core.config import APP_TITLE, STREAMLIT_START_TIMEOUT  # noqa: E402


def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def kill_existing_streamlit():
    """保留兼容函数名，但开源版不再全局杀死其他 Streamlit 进程。

    旧保护包会扫描并结束所有命令行包含 "streamlit" 的进程。
    这对开源用户不友好，因为可能误杀用户正在运行的其他项目。
    当前版本使用随机空闲端口启动，因此不需要清理全局进程。
    """
    return None


def start_streamlit(port: int) -> subprocess.Popen:
    """启动 Streamlit 子进程，返回 Popen 对象。"""
    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.dirname(__file__)
    return subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.port", str(port),
            "--server.address", "localhost",
            "--server.headless", "true",
            "--server.enableWebsocketCompression", "false",
            "--server.maxMessageSize", "104857600",
            "--browser.gatherUsageStats", "false",
        ],
        env=env,
    )


def wait_for_streamlit(port: int, timeout: int = STREAMLIT_START_TIMEOUT) -> bool:
    """
    等待 Streamlit 健康检查端点就绪。
    ✅ 修复：加入超时防止永久挂起。
    """
    url = f"http://localhost:{port}/_stcore/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=3)
            return True
        except Exception:
            time.sleep(1)
    return False


def main():
    kill_existing_streamlit()
    port = get_free_port()

    print(f"[白洞计划 v3.0] 正在启动 Streamlit（端口 {port}）…")
    process = start_streamlit(port)

    if not wait_for_streamlit(port):
        print("❌ Streamlit 启动超时，请检查依赖是否完整安装")
        process.kill()
        sys.exit(1)

    print(f"[白洞计划 v3.0] Streamlit 就绪，正在打开窗口…")
    api = Api()
    webview.create_window(
        APP_TITLE,
        f"http://localhost:{port}",
        width=1680,
        height=1000,
        resizable=True,
        js_api=api,
    )
    try:
        webview.start()
    finally:
        process.kill()


if __name__ == "__main__":
    main()
