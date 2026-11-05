"""双击启动入口：版本探测 -> 选择可用端口 -> 启动服务 -> 自动打开浏览器。

设计目标：让不熟悉命令行的同学也能在答辩现场 / 机房一键启动验收。
仅依赖 Python 3.8+ 标准库，不需要 pip install、不需要密钥、不需要联网。

v1.2.1 修复：过去只判断「端口上有没有 HTTP 200」，如果 5000 端口残留着
旧版本后端，会被误判成「服务已在运行」，结果浏览器打开的是新页面 + 旧接口
（学习资源包、模型接入等按钮全部 404）。现在通过 /api/status 的 version
指纹识别版本，遇到旧版或异种服务会自动顺延端口，保证一定能打开可用的新版。
"""
import json
import os
import socket
import sys
import threading
import time
import traceback
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)  # server.py 的静态资源使用相对路径，必须切到项目根目录
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from version import APP_NAME, APP_VERSION  # noqa: E402

DEFAULT_PORT = int(os.getenv("PORT", "5000"))
MAX_PORT_TRIES = 20


def _tcp_open(port):
    """端口上是否已有监听者（不能只靠 HTTP 探测或 bind 判断）。"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.4)
    try:
        return sock.connect_ex(("127.0.0.1", port)) == 0
    except OSError:
        return False
    finally:
        sock.close()


def probe(port):
    """探测端口，返回 (kind, version)。

    kind: ok=当前版本服务已运行 / stale=旧版本本项目后端 /
          foreign=其它程序 / free=端口空闲
    """
    if not _tcp_open(port):
        return "free", ""
    req = urllib.request.Request(
        "http://127.0.0.1:%d/api/status" % port,
        headers={"User-Agent": "campus-companion-launcher"})
    try:
        with urllib.request.urlopen(req, timeout=2) as r:
            if r.status != 200:
                return "foreign", ""
            data = json.loads(r.read().decode("utf-8", "replace"))
    except Exception:
        # 端口有人监听但不是 HTTP 服务（或不是本项目），一律不可复用
        return "foreign", ""
    if not isinstance(data, dict) or "active_provider" not in data:
        return "foreign", ""
    ver = str(data.get("version", ""))
    return ("ok", ver) if ver == APP_VERSION else ("stale", ver)


def open_browser_later(url):
    time.sleep(1.5)  # 等 HTTP 服务完成 bind
    try:
        webbrowser.open(url)
    except Exception:
        pass


def print_release_hint(port):
    print("       若想固定用 %d 端口，先关闭占用它的旧窗口；或 PowerShell 执行：" % port)
    print("       Get-NetTCPConnection -LocalPort %d | Select-Object OwningProcess" % port)
    print("       Stop-Process -Id <上一步查到的 PID>")


def main():
    print("=" * 62)
    print("  %s · 本地验收启动器  V%s" % (APP_NAME, APP_VERSION))
    print("=" * 62)

    chosen = None
    blocked = []
    for port in range(DEFAULT_PORT, DEFAULT_PORT + MAX_PORT_TRIES):
        kind, ver = probe(port)
        if kind == "ok":
            url = "http://localhost:%d" % port
            print("[OK] 本版本服务已在运行：%s" % url)
            print("     正在打开浏览器……此窗口可直接关闭，服务不会停止。")
            if blocked:
                print("     （已跳过被占用的端口：%s）"
                      % ", ".join(str(p) for p in blocked))
            try:
                webbrowser.open(url)
            except Exception:
                print("     （未能自动打开浏览器，请手动访问上面的地址）")
            return 0
        if kind == "free":
            chosen = port
            break
        blocked.append(port)
        if kind == "stale":
            print("[注意] 端口 %d 上是旧版本后端（version=%s），不能复用。"
                  % (port, ver or "无版本字段"))
            print("       旧后端会导致页面是新的、接口却全部 404，已自动跳过。")
        else:
            print("[注意] 端口 %d 被其它程序占用，已跳过。" % port)

    if chosen is None:
        print("[启动失败] %d~%d 端口均被占用，请先关闭旧服务后重试。"
              % (DEFAULT_PORT, DEFAULT_PORT + MAX_PORT_TRIES - 1))
        print_release_hint(DEFAULT_PORT)
        return 1

    if chosen != DEFAULT_PORT:
        print_release_hint(DEFAULT_PORT)

    os.environ["PORT"] = str(chosen)
    url = "http://localhost:%d" % chosen
    print("-" * 62)
    print("[..] 正在启动 Web 服务：%s" % url)
    print("     保持本窗口开启即可持续验收；按 Ctrl+C 或关闭窗口即停止服务。")
    print("     无需联网、无需密钥（当前为内置演示模式）。")
    print("-" * 62)

    threading.Thread(target=open_browser_later, args=(url,), daemon=True).start()
    try:
        import server
        server.main()
    except SystemExit:
        raise
    except Exception:
        traceback.print_exc()
        print("[启动失败] 服务初始化异常，请把上面的报错信息反馈给开发者。")
        return 1
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n服务已停止")
