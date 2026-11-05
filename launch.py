"""双击启动入口：检测端口 -> 已在运行则直接开浏览器；否则启动服务并自动打开。

设计目标：让不熟悉命令行的同学也能在答辩现场 / 机房一键启动验收。
仅依赖 Python 3.8+ 标准库，不需要 pip install、不需要密钥、不需要联网。
"""
import os
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # server.py 的静态资源使用相对路径，必须切到项目根目录
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PORT = int(os.getenv("PORT", "5000"))
URL = "http://localhost:%d" % PORT


def is_alive():
    try:
        req = urllib.request.Request(URL + "/api/status", headers={"User-Agent": "launcher"})
        with urllib.request.urlopen(req, timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def open_browser_later():
    time.sleep(1.5)  # 等 HTTP 服务完成 bind
    try:
        webbrowser.open(URL)
    except Exception:
        pass


def main():
    print("=" * 60)
    print("  AI 校园学习陪伴助手 · 本地验收启动器")
    print("=" * 60)

    if is_alive():
        print("[OK] 服务已在运行：%s" % URL)
        print("     正在打开浏览器……此窗口可直接关闭，服务不会停止。")
        try:
            webbrowser.open(URL)
        except Exception:
            print("     （未能自动打开浏览器，请手动访问上面的地址）")
        return 0

    print("[..] 正在启动本地服务：%s" % URL)
    print("     保持本窗口开启即可持续验收；按 Ctrl+C 或关闭窗口即停止服务。")
    print("     无需联网、无需密钥（当前为内置演示模式）。")
    print("-" * 60)

    threading.Thread(target=open_browser_later, daemon=True).start()
    import server
    server.main()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n服务已停止")
