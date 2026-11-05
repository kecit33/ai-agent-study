"""启动自检：一次确认「服务真的能完整启动并运行」。

用法：
    python docs/startup_check.py
    BASE_URL=http://127.0.0.1:5000 python docs/startup_check.py
    BASE_URL=https://xxx.app.workbuddy.host SHARECODE=xxxx python docs/startup_check.py

检查内容：
  1. /api/status 的版本指纹是否与磁盘上的 version.py 一致（识别旧后端残留）；
  2. 首页与静态资源是否可访问；
  3. V1.1 / V1.2 的全部关键 GET、POST 接口是否返回 200；
  4. 首页是否包含「学习资源包」「模型接入」等 V1.2 界面元素。

只依赖 Python 标准库；全通过退出码 0，否则 1。结果写入 docs/startup_results.json。
"""
import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from version import APP_NAME, APP_VERSION  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
SHARECODE = os.getenv("SHARECODE", "").strip()
OUT = ROOT / "docs" / "startup_results.json"

_opener = urllib.request.build_opener(
    urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
if SHARECODE:
    try:
        _opener.open(BASE + "/?sharecode=" + SHARECODE, timeout=25).read()
    except Exception as exc:
        print("[警告] 建立 sharecode 会话失败：%s" % exc)

checks = []


def req(path, body=None):
    data = json.dumps(body).encode("utf-8") if body is not None else None
    request = urllib.request.Request(
        BASE + path, data=data,
        headers={"Content-Type": "application/json"},
        method="POST" if data is not None else "GET")
    try:
        with _opener.open(request, timeout=25) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return 0, str(e).encode("utf-8"), {}


def check(name, ok, detail=""):
    checks.append({"name": name, "ok": bool(ok), "detail": str(detail)})
    print("%s %s%s" % ("✅" if ok else "❌", name,
                       (" | " + str(detail)) if detail else ""))


def main():
    print("=" * 66)
    print("  %s · 启动自检  V%s" % (APP_NAME, APP_VERSION))
    print("  目标：%s" % BASE)
    print("=" * 66)

    st, raw, _ = req("/api/status")
    try:
        status = json.loads(raw.decode("utf-8"))
    except Exception:
        status = {}
    remote_ver = str(status.get("version", ""))
    check("S1 服务可访问（/api/status 200）", st == 200, "HTTP %s" % st)
    check("S2 后端版本与磁盘版本一致", remote_ver == APP_VERSION,
          "远端 %s / 期望 %s" % (remote_ver or "无版本字段", APP_VERSION))
    if st == 200 and remote_ver != APP_VERSION:
        print("   ⚠️ 端口上跑的是旧版本后端：页面是新的、接口会 404。")
        print("      请关闭旧服务窗口，或重新双击 start.bat 自动顺延端口。")
    check("S3 智能体提供商列表正常", isinstance(status.get("providers"), list)
          and len(status.get("providers", [])) >= 6,
          "%d 项" % len(status.get("providers", [])))

    st, raw, _ = req("/")
    html = raw.decode("utf-8", "replace")
    check("S4 首页可访问", st == 200, "HTTP %s / %d 字节" % (st, len(raw)))
    check("S5 首页含 V1.2 界面元素",
          all(k in html for k in ("panel-study", "agentProvider", "studyPack")),
          "学习资源包 / 模型接入 / 一键生成")
    for path in ("/static/css/style.css", "/static/js/app.js"):
        st, raw, _ = req(path)
        check("S6 静态资源 %s" % path, st == 200 and len(raw) > 1000,
              "HTTP %s / %d 字节" % (st, len(raw)))

    gets = [
        "/api/providers", "/api/agent/providers", "/api/study/catalog",
        "/api/overview", "/api/hardware/status", "/api/focus/sessions",
        "/api/courses", "/api/courses/1/materials", "/api/wrong-questions",
        "/api/study/mindmap.svg?subject=math",
        "/api/study/pack/export?subject=math&count=2",
    ]
    for path in gets:
        st, raw, _ = req(path)
        check("S7 GET %s" % path, st == 200, "HTTP %s / %d 字节" % (st, len(raw)))

    posts = [
        ("/api/study/quiz", {"subject": "数学", "chapter": "第一章", "count": 3}),
        ("/api/study/summary", {"subject": "高等数学上册", "chapter": "ch1"}),
        ("/api/study/article", {"subject": "高等数学上册"}),
        ("/api/study/resources", {"subject": "数学"}),
        ("/api/study/mindmap", {"subject": "数学", "chapter": "ch1"}),
        ("/api/study/pack", {"subject": "数学", "chapter": "ch1", "count": 2}),
        ("/api/agent/test", {"provider": "moonshot", "mode": "validate"}),
        ("/api/agent/complete", {"message": "启动自检"}),
    ]
    for path, body in posts:
        st, raw, _ = req(path, body)
        check("S8 POST %s" % path, st == 200, "HTTP %s / %d 字节" % (st, len(raw)))

    passed = sum(1 for c in checks if c["ok"])
    total = len(checks)
    print("=" * 66)
    print("  启动自检：%d/%d 通过" % (passed, total))
    print("=" * 66)
    OUT.write_text(json.dumps({
        "app": APP_NAME, "expected_version": APP_VERSION,
        "remote_version": remote_ver, "base_url": BASE,
        "time": datetime.now().isoformat(timespec="seconds"),
        "passed": passed, "total": total, "checks": checks,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print("  结果已保存：docs/startup_results.json")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
