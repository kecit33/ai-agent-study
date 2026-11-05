"""新增功能端到端验证：主题静态资源 / 语音 UI / 文件上传 / 导出 / 番茄钟 / 硬件看板。

用法：python docs/feature_check.py   （需先启动 server.py，默认 http://localhost:5000）
"""
import io
import json
import os
import sys
import urllib.request
import urllib.error
import uuid
import zipfile

BASE = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
RESULTS = []

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print("%s %s %s" % ("✅" if ok else "❌", name, ("| " + str(detail)[:110]) if detail else ""))


def req(method, path, body=None, raw=False, headers=None, data=None):
    url = BASE + path
    if data is not None:
        payload, hdr = data, dict(headers or {})
    else:
        payload = json.dumps(body or {}).encode("utf-8") if body is not None else None
        hdr = {"Content-Type": "application/json"}
        hdr.update(headers or {})
    r = urllib.request.Request(url, data=payload, method=method, headers=hdr)
    try:
        with urllib.request.urlopen(r, timeout=20) as resp:
            content = resp.read()
            if raw:
                return resp.status, content, dict(resp.headers)
            return resp.status, json.loads(content.decode("utf-8")), dict(resp.headers)
    except urllib.error.HTTPError as e:
        content = e.read()
        if raw:
            return e.code, content, dict(e.headers)
        try:
            return e.code, json.loads(content.decode("utf-8")), dict(e.headers)
        except Exception:
            return e.code, {"error": content.decode("utf-8", "replace")[:200]}, dict(e.headers)


def multipart(filename, content):
    boundary = "----ccb" + uuid.uuid4().hex
    body = (
        ("--" + boundary + "\r\n").encode()
        + ('Content-Disposition: form-data; name="file"; filename="%s"\r\n' % filename).encode()
        + b"Content-Type: application/octet-stream\r\n\r\n"
        + content + ("\r\n--" + boundary + "--\r\n").encode()
    )
    return body, {"Content-Type": "multipart/form-data; boundary=" + boundary}


def make_docx(text):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("word/document.xml",
                   '<?xml version="1.0"?><w:document xmlns:w="ns"><w:body><w:p><w:r><w:t>'
                   + text + "</w:t></w:r></w:p></w:body></w:document>")
    return buf.getvalue()


def main():
    print("目标：", BASE)
    st, page, _ = req("GET", "/", raw=True)
    html = page.decode("utf-8")
    check("首页可访问", st == 200, st)
    check("主题系统 UI（跟随系统/深色/浅色）", "themeSeg" in html and "跟随系统" in html and "data-theme" in html)
    check("语音输入按钮", html.count("data-mic-target") >= 4, html.count("data-mic-target"))
    check("文件上传区", "uploadZone" in html and ".docx" in html)
    check("学习概览与番茄钟", "panel-dashboard" in html and "pomoTime" in html)
    check("硬件交互点清单", "硬件交互点清单" in html and "/api/hardware/status" in html)
    st, css, _ = req("GET", "/static/css/style.css", raw=True)
    check("深色模式样式", st == 200 and b'[data-theme="dark"]' in css)
    st, js, _ = req("GET", "/static/js/app.js", raw=True)
    check("语音 API 与系统偏好监听", b"SpeechRecognition" in js and b"prefers-color-scheme" in js)

    st, d, _ = req("GET", "/api/overview")
    check("学习概览", st == 200 and "mastery_rate" in d and "focus_today_minutes" in d,
          "课程%s 掌握率%s" % (d.get("courses"), d.get("mastery_rate")))

    st, d, _ = req("POST", "/api/focus/state", {"active": True, "minutes": 25})
    check("专注状态开启", st == 200 and d.get("active") is True)
    st, d, _ = req("GET", "/api/hardware/status")
    check("硬件看板反映专注中", d.get("focus_active") is True, d.get("display"))
    st, d, _ = req("POST", "/api/focus/state", {"active": False})
    st, d, _ = req("GET", "/api/hardware/status")
    check("专注关闭后看板空闲", d.get("focus_active") is False)

    st, d, _ = req("POST", "/api/focus/sessions", {"minutes": 25, "note": "HTTP 端到端验证"})
    check("番茄钟记录+ESP32提醒", st == 200 and d.get("minutes") == 25 and "reminder" in d)
    st, d, _ = req("GET", "/api/focus/sessions")
    check("专注记录列表", st == 200 and len(d) >= 1, len(d))

    body, hdr = multipart("进程与线程.md", "进程是资源分配单位；线程是CPU调度单位。".encode("utf-8"))
    st, d, _ = req("POST", "/api/courses/1/materials/upload", data=body, headers=hdr)
    check("Markdown 上传", st == 200 and d.get("chars", 0) > 0, d.get("chars") or d)

    body, hdr = multipart("第三章.docx", make_docx("满二叉树与完全二叉树的区别。"))
    st, d, _ = req("POST", "/api/courses/1/materials/upload", data=body, headers=hdr)
    check("docx 上传并解析", st == 200 and "满二叉树" in (d.get("preview") or ""), d.get("preview") or d)

    body, hdr = multipart("hack.exe", b"MZ\x90\x00")
    st, d, _ = req("POST", "/api/courses/1/materials/upload", data=body, headers=hdr)
    check("非法类型被 400 拦截", st == 400 and "仅支持" in str(d), st)

    st, content, hdrs = req("GET", "/api/wrong-questions/export?course_id=1", raw=True)
    check("错题导出 Markdown 下载",
          st == 200 and content.decode("utf-8").startswith("# AI 错题本导出")
          and "attachment" in hdrs.get("Content-Disposition", ""),
          hdrs.get("Content-Disposition"))

    st, d, _ = req("GET", "/api/courses/1/materials")
    check("上传资料已进入课程记忆", st == 200 and any("第三章" in (m.get("title") or "") for m in d), len(d))

    passed = sum(1 for _, ok, _ in RESULTS if ok)
    print("\n新增功能断言：%d/%d 通过" % (passed, len(RESULTS)))
    with open(os.path.join(os.path.dirname(__file__), "feature_results.json"), "w", encoding="utf-8") as f:
        json.dump({"base_url": BASE, "total": len(RESULTS), "passed": passed,
                   "results": [{"name": n, "ok": ok, "detail": str(dt)[:200]} for n, ok, dt in RESULTS]},
                  f, ensure_ascii=False, indent=2)
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
