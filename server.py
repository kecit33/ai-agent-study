"""AI 校园学习陪伴助手 —— Web 服务器（仅 Python 标准库，零第三方依赖）。

设计目的：
1. 本机或云环境无法 pip install 时，仍可一键启动真实可访问的 Web 应用；
2. 答辩现场 / 师生验收时无需任何密钥、无需联网安装依赖；
3. Render 等平台可直接以 `python server.py` 启动（尊重 PORT 环境变量）。

启动：python server.py    访问：http://localhost:5000
"""
import json
import mimetypes
import os
import re
import socket
import sys
import threading
import time
import traceback
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import db
from agents import credentials, factory
from agents.factory import (
    get_active_provider_name, set_active_provider, list_providers_status,
)
from services import course, tasks, wrong_questions, focus, files as filesvc
from services import study
from hardware import esp32
from version import APP_NAME, APP_VERSION

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")

db.init_db()


# ---------------- 业务处理函数：返回 dict，或抛出 HttpError ----------------
class HttpError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


def _status():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "active_provider": get_active_provider_name(),
        "providers": list_providers_status(),
    }


def _set_provider(body):
    ok = set_active_provider(body.get("name", ""))
    return {"ok": ok, "active_provider": get_active_provider_name()}


def _create_course(body):
    return course.create_course(body.get("name", ""))


def _add_material(cid, body):
    return course.add_material(cid, body.get("title", ""), body.get("content", ""))


def _chat(body):
    cid = body.get("course_id")
    if not cid:
        raise HttpError(400, "请选择课程")
    return {"reply": tasks.chat(int(cid), body.get("message", ""))}


def _add_wq(body):
    return wrong_questions.add_wrong_question(
        int(body.get("course_id", 0)), body.get("question", ""),
        body.get("user_answer", ""), body.get("correct_answer", ""),
        body.get("error_reason", ""),
    )


def _mark_mastered(wid, body):
    wrong_questions.mark_mastered(wid, bool(body.get("mastered", True)))
    return {"ok": True}


def _review_task(body):
    due = body.get("due_time") or datetime.now().isoformat(timespec="seconds")
    conn = db.get_conn()
    cur = conn.execute(
        "INSERT INTO review_tasks(course_id, task_name, due_time, notified, created_at) "
        "VALUES(?, ?, ?, 0, ?)",
        (body.get("course_id"), body.get("task_name", "复习任务"),
         due, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    fired = None
    if body.get("fire_now"):
        fired = esp32.notify_esp32(body.get("task_name", "复习任务"))
    return {"id": tid, "fired": fired}


def _list_review_tasks():
    """待复习任务列表（含课程名），供学习概览直接查看与勾选完成。"""
    conn = db.get_conn()
    rows = conn.execute(
        "SELECT r.id, r.task_name, r.due_time, r.notified, r.created_at, "
        "c.name AS course_name FROM review_tasks r "
        "LEFT JOIN courses c ON c.id = r.course_id "
        "ORDER BY (r.notified = 0) DESC, r.due_time ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def _mark_task_done(tid):
    """标记复习任务为已完成（notified=1 复用为完成状态）。"""
    conn = db.get_conn()
    conn.execute("UPDATE review_tasks SET notified = 1 WHERE id = ?", (tid,))
    conn.commit()
    conn.close()
    return {"ok": True, "id": tid}


class Download:
    """非 JSON 响应：以附件形式下载文本（如错题本 / 学习资源包 Markdown 导出）。"""

    def __init__(self, filename, text, ctype="text/markdown; charset=utf-8"):
        self.filename = filename
        self.data = text.encode("utf-8") if isinstance(text, str) else text
        self.ctype = ctype


class Raw:
    """非 JSON 响应：直接内联返回字节（如思维导图 SVG）。"""

    def __init__(self, text, ctype="image/svg+xml; charset=utf-8"):
        self.data = text.encode("utf-8") if isinstance(text, str) else text
        self.ctype = ctype


def _agent_test(body):
    """模型连通性测试；mode=validate 时只校验配置、不发起外部请求。"""
    name = (body.get("provider") or get_active_provider_name()).strip().lower()
    if name == "demo":
        return {"ok": True, "provider": "demo", "mode": body.get("mode", "probe"),
                "reply": "内置演示模式已就绪，无需外部模型"}
    if name not in credentials.PROVIDER_FIELDS:
        raise HttpError(400, "未知提供商：%s" % name)
    c = credentials.get(name)
    ok, reason = credentials.validate(name, c)
    if body.get("mode") == "validate":
        return {"ok": ok, "provider": name, "mode": "validate", "reason": reason,
                "configured": ok, "model": c.get("model", ""),
                "base_url": c.get("base_url", ""), "masked": credentials.status(name)["masked"]}
    if not ok:
        return {"ok": False, "provider": name, "mode": "probe", "reason": reason,
                "configured": False, "error": "配置不完整：" + reason}
    return factory.probe(name)


def _agent_complete(body):
    """通用模型透传：自建系统可直接调用当前配置的文心 / Kimi / 自定义模型。"""
    msgs = body.get("messages")
    if not isinstance(msgs, list) or not msgs:
        msgs = [{"role": "user", "content": body.get("message", "你好")}]
    msgs = [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))}
            for m in msgs if isinstance(m, dict)]
    return factory.direct_complete(
        str(body.get("system_prompt", "你是校园学习陪伴助手，请简洁、准确地回答。")),
        msgs, (body.get("provider") or None),
    )


def _study_args(body, query=None):
    """从 POST body 或 GET query 提取学习资源包公共参数。"""
    query = query or {}
    def val(k, default=""):
        if k in body:
            return body[k]
        return query.get(k, [default])[0]
    try:
        count = int(val("count", 6))
    except (TypeError, ValueError):
        count = 6
    return {
        "subject": val("subject", "高等数学上册"),
        "chapter": val("chapter", ""),
        "count": count,
        "difficulty": val("difficulty", ""),
        "provider_name": val("provider", "") or None,
    }


def _s_quiz(b, q=None):
    a = _study_args(b or {}, q)
    return study.quiz(a["subject"], a["chapter"], a["count"],
                      a["difficulty"], a["provider_name"])


def _s_summary(b, q=None):
    a = _study_args(b or {}, q)
    return study.summary(a["subject"], a["chapter"], a["provider_name"])


def _s_article(b, q=None):
    a = _study_args(b or {}, q)
    return study.article(a["subject"], a["chapter"], a["provider_name"])


def _s_resources(b, q=None):
    a = _study_args(b or {}, q)
    return study.resources(a["subject"], a["chapter"])


def _s_mindmap(b, q=None):
    a = _study_args(b or {}, q)
    return study.mindmap(a["subject"], a["chapter"], a["provider_name"])


def _s_pack(b, save=False):
    a = _study_args(b or {})
    return study.pack(a["subject"], a["chapter"], a["count"], a["difficulty"],
                      a["provider_name"], save_to_course=save)


def _s_export(q):
    a = _study_args({}, q)
    return study.export_markdown(a["subject"], a["chapter"], a["count"],
                                 a["provider_name"])


def _upload_material(cid, body):
    """处理课程资料文件上传：提取文本后入库，返回提取摘要。"""
    upload = (body.get("__files__") or [None])[0]
    if not upload:
        raise HttpError(400, "未收到文件，请使用 multipart/form-data 上传字段 file")
    info = filesvc.extract_text(upload["filename"], upload["data"])
    result = course.add_material(cid, info["title"], info["text"])
    result.update({
        "filename": upload["filename"], "chars": info["chars"],
        "truncated": info["truncated"], "preview": info["text"][:200],
    })
    return result


def _record_focus(body):
    """番茄钟结束：记录专注时长，并联动 ESP32 声光提醒 + 熄灭专注灯。"""
    result = focus.record_session(
        body.get("minutes", 0), course_id=body.get("course_id"),
        note=body.get("note", ""), started_at=body.get("started_at", ""),
        ended_at=body.get("ended_at", ""),
    )
    esp32.set_focus_state(False)
    result["reminder"] = esp32.notify_esp32(
        "专注完成", message="本次专注 %s 分钟已完成，休息一下吧！" % result["minutes"])
    return result


# ---------------- 路由表 ----------------
# (HTTP 方法, 路径正则, 处理函数)。处理函数签名：handler(match, body, query) -> dict
ROUTES = [
    ("GET", r"^/api/status$",
     lambda m, b, q: _status()),
    ("GET", r"^/api/providers$",
     lambda m, b, q: list_providers_status()),
    ("POST", r"^/api/settings/provider$",
     lambda m, b, q: _set_provider(b)),

    ("GET", r"^/api/courses$",
     lambda m, b, q: course.list_courses()),
    ("POST", r"^/api/courses$",
     lambda m, b, q: _create_course(b)),
    ("GET", r"^/api/courses/(\d+)/materials$",
     lambda m, b, q: course.list_materials(int(m.group(1)))),
    ("POST", r"^/api/courses/(\d+)/materials$",
     lambda m, b, q: _add_material(int(m.group(1)), b)),

    ("POST", r"^/api/chat$",
     lambda m, b, q: _chat(b)),
    ("POST", r"^/api/summarize$",
     lambda m, b, q: {"result": tasks.summarize(b.get("text", ""))}),
    ("POST", r"^/api/tutor$",
     lambda m, b, q: {"result": tasks.tutor(b.get("problem", ""))}),
    ("POST", r"^/api/review-plan$",
     lambda m, b, q: {"result": tasks.review_plan(b.get("subject", ""), int(b.get("days", 7) or 7))}),

    ("GET", r"^/api/wrong-questions$",
     lambda m, b, q: wrong_questions.list_wrong_questions(
         course_id=int(q.get("course_id", [0])[0]) if q.get("course_id") else None,
         only_unmastered=q.get("unmastered", ["0"])[0] == "1")),
    ("POST", r"^/api/wrong-questions$",
     lambda m, b, q: _add_wq(b)),
    ("POST", r"^/api/wrong-questions/(\d+)/analyze$",
     lambda m, b, q: wrong_questions.analyze_and_variant(int(m.group(1)), provider_name=b.get("provider"))),
    ("POST", r"^/api/wrong-questions/(\d+)/master$",
     lambda m, b, q: _mark_mastered(int(m.group(1)), b)),

    ("POST", r"^/api/review-tasks$",
     lambda m, b, q: _review_task(b)),
    ("GET", r"^/api/review-tasks$",
     lambda m, b, q: _list_review_tasks()),
    ("POST", r"^/api/review-tasks/(\d+)/done$",
     lambda m, b, q: _mark_task_done(int(m.group(1)))),
    ("POST", r"^/api/hardware/test$",
     lambda m, b, q: esp32.notify_esp32(b.get("task_name", "测试提醒"),
                                        b.get("message", "硬件联动测试"))),

    # ---- 文件上传 / 导出 ----
    ("POST", r"^/api/courses/(\d+)/materials/upload$",
     lambda m, b, q: _upload_material(int(m.group(1)), b)),
    ("GET", r"^/api/wrong-questions/export$",
     lambda m, b, q: Download(
         "wrong-questions.md",
         wrong_questions.export_markdown(
             int(q["course_id"][0]) if q.get("course_id") else None))),

    # ---- 学习概览 / 番茄钟 ----
    ("GET", r"^/api/overview$",
     lambda m, b, q: focus.overview()),
    ("GET", r"^/api/focus/sessions$",
     lambda m, b, q: focus.list_sessions(int(q.get("limit", [10])[0]))),
    ("POST", r"^/api/focus/sessions$",
     lambda m, b, q: _record_focus(b)),
    ("POST", r"^/api/focus/state$",
     lambda m, b, q: esp32.set_focus_state(
         bool(b.get("active")), int(b.get("minutes", 0) or 0))),

    # ---- 硬件状态看板（ESP32 轮询） ----
    ("GET", r"^/api/hardware/status$",
     lambda m, b, q: esp32.hardware_status()),

    # ---- 学习资源包：题目 / 总结 / 文章 / 资料 / 思维导图 ----
    ("GET", r"^/api/study/catalog$",
     lambda m, b, q: study.catalog()),
    ("POST", r"^/api/study/quiz$",
     lambda m, b, q: _s_quiz(b)),
    ("POST", r"^/api/study/summary$",
     lambda m, b, q: _s_summary(b)),
    ("POST", r"^/api/study/article$",
     lambda m, b, q: _s_article(b)),
    ("POST", r"^/api/study/resources$",
     lambda m, b, q: _s_resources(b)),
    ("POST", r"^/api/study/mindmap$",
     lambda m, b, q: _s_mindmap(b)),
    ("POST", r"^/api/study/pack$",
     lambda m, b, q: _s_pack(b, bool(b.get("save_to_course")))),
    ("GET", r"^/api/study/mindmap\.svg$",
     lambda m, b, q: Raw(_s_mindmap({}, q)["svg"])),
    ("GET", r"^/api/study/pack/export$",
     lambda m, b, q: Download("study-pack.md", _s_export(q))),

    # ---- 模型接入接口：文心一言 / Kimi / 自定义兼容端点，运行时配置 ----
    ("GET", r"^/api/agent/providers$",
     lambda m, b, q: {"active_provider": get_active_provider_name(),
                      "providers": list_providers_status(),
                      "credentials": credentials.list_status()}),
    ("POST", r"^/api/agent/credentials$",
     lambda m, b, q: factory.configure(
         (b.get("provider") or "").strip().lower(), b.get("config") or b,
         activate=bool(b.get("activate")))),
    ("POST", r"^/api/agent/credentials/clear$",
     lambda m, b, q: factory.clear((b.get("provider") or "").strip().lower())),
    ("POST", r"^/api/agent/test$",
     lambda m, b, q: _agent_test(b)),
    ("POST", r"^/api/agent/complete$",
     lambda m, b, q: _agent_complete(b)),
]


# ---------------- HTTP 处理器 ----------------
class Handler(BaseHTTPRequestHandler):
    server_version = "CampusCompanion/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status, payload):
        data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path, status=200):
        try:
            with open(path, "rb") as f:
                data = f.read()
        except OSError:
            self._send_json(404, {"error": "Not Found"})
            return
        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        if ctype.startswith("text/") or ctype in ("application/javascript", "application/json"):
            ctype += "; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self._cors()
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _serve_static(self, path):
        if path == "/" or path == "/index.html":
            self._send_file(os.path.join(STATIC_DIR, "index.html"))
            return
        if path.startswith("/static/"):
            rel = path[len("/static/"):]
            # 防目录穿越
            full = os.path.abspath(os.path.join(STATIC_DIR, rel))
            if not full.startswith(os.path.abspath(STATIC_DIR) + os.sep):
                self._send_json(403, {"error": "Forbidden"})
                return
            self._send_file(full)
            return
        self._send_json(404, {"error": "Not Found"})
        return

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        if length > 2 * 1024 * 1024:
            raise HttpError(413, "请求体过大")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8")) or {}
        except (ValueError, UnicodeDecodeError):
            raise HttpError(400, "请求体不是合法 JSON")

    def _read_multipart(self):
        """解析 multipart/form-data（Python 3.13 已移除 cgi，这里自行解析）。

        仅用于课程资料上传；限制 4 MB，逐段提取字段与文件内容。
        """
        ctype = self.headers.get("Content-Type", "")
        m = re.search(r'boundary="?([^";]+)"?', ctype)
        if not m:
            raise HttpError(400, "multipart 请求缺少 boundary")
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            length = 0
        if length <= 0:
            raise HttpError(400, "上传内容为空")
        if length > 4 * 1024 * 1024:
            raise HttpError(413, "上传内容超过 4 MB 上限")
        raw = self.rfile.read(length)
        boundary = m.group(1).encode()
        fields, upload_files = {}, []
        for part in raw.split(b"--" + boundary):
            part = part.strip(b"\r\n")
            if not part or part == b"--" or b"\r\n\r\n" not in part:
                continue
            header_blob, content = part.split(b"\r\n\r\n", 1)
            headers = header_blob.decode("utf-8", "replace")
            disp = re.search(r'name="([^"]*)"(?:;\s*filename="([^"]*)")?', headers)
            if not disp:
                continue
            name, filename = disp.group(1), disp.group(2)
            if filename is not None:
                upload_files.append({"field": name, "filename": filename, "data": content})
            else:
                fields[name] = content.decode("utf-8", "replace")
        return {"__fields__": fields, "__files__": upload_files}

    def _send_download(self, dl):
        from urllib.parse import quote
        self.send_response(200)
        self.send_header("Content-Type", dl.ctype)
        self.send_header("Content-Length", str(len(dl.data)))
        self.send_header("Content-Disposition",
                         "attachment; filename*=UTF-8''" + quote(dl.filename))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(dl.data)

    def _send_raw(self, raw):
        self.send_response(200)
        self.send_header("Content-Type", raw.ctype)
        self.send_header("Content-Length", str(len(raw.data)))
        self.send_header("Cache-Control", "no-store")
        self._cors()
        self.end_headers()
        self.wfile.write(raw.data)

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        path = parsed.path
        query = parse_qs(parsed.query)

        if method == "GET" and not path.startswith("/api/"):
            self._serve_static(path)
            return

        for verb, pattern, handler in ROUTES:
            if verb != method:
                continue
            m = re.match(pattern, path)
            if not m:
                continue
            if method == "POST":
                ctype = self.headers.get("Content-Type", "")
                body = self._read_multipart() if ctype.startswith("multipart/form-data") else self._read_body()
            else:
                body = {}
            result = handler(m, body, query)
            if isinstance(result, Download):
                self._send_download(result)
            elif isinstance(result, Raw):
                self._send_raw(result)
            else:
                self._send_json(200, result)
            return

        self._send_json(404, {"error": "接口不存在", "path": path})

    def _handle(self, method):
        try:
            self._dispatch(method)
        except HttpError as e:
            self._send_json(e.status, {"error": e.message})
        except ValueError as e:
            self._send_json(400, {"error": str(e)})
        except BrokenPipeError:
            pass
        except Exception as e:
            traceback.print_exc()
            self._send_json(500, {"error": "服务端异常：%s" % e})

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


def _scheduler():
    """复习任务到点自动下发 ESP32 提醒（未配置硬件时为空操作）。"""
    while True:
        try:
            esp32.check_due_tasks()
        except Exception:
            pass
        time.sleep(30)


def _port_in_use(host, port):
    """主动探测端口上是否已有服务在监听。

    Windows 下 HTTPServer 默认开启 SO_REUSEADDR，第二个进程 bind 同一端口
    竟然会「成功」，于是两个版本的服务同时监听 5000，请求随机落到旧进程上
    （页面是新的、接口却 404）。因此不能只依赖 bind 是否抛异常，必须先做
    TCP 连接探测。
    """
    probe_host = "127.0.0.1" if host in ("0.0.0.0", "", "::") else host
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.4)
    try:
        return sock.connect_ex((probe_host, port)) == 0
    except OSError:
        return False
    finally:
        sock.close()


def _bind_server(host, start_port, strict):
    """绑定监听端口。

    本地默认启动（未显式设置 PORT）时，若端口被旧进程占用则自动顺延，
    保证「双击就能跑」；云端或用户显式指定 PORT 时严格绑定，避免平台健康
    检查指向错误端口。
    """
    attempts = 1 if strict else 20
    port = start_port
    for i in range(attempts):
        if _port_in_use(host, port):
            if strict:
                raise OSError("端口 %d 上已有服务在运行" % port)
            print("[提示] 端口 %d 已有服务在运行，自动尝试 %d ……"
                  % (port, port + 1), flush=True)
            port += 1
            continue
        try:
            return ThreadingHTTPServer((host, port), Handler), port
        except OSError as exc:
            if strict or i == attempts - 1:
                raise
            print("[提示] 端口 %d 绑定失败，自动尝试 %d ……（%s）"
                  % (port, port + 1, exc), flush=True)
            port += 1
    raise OSError("无可用端口")


def main():
    raw_port = os.getenv("PORT")
    start_port = int(raw_port or "5000")
    strict = bool(raw_port)
    host = os.getenv("HOST", "0.0.0.0")
    try:
        srv, port = _bind_server(host, start_port, strict)
    except OSError as exc:
        print("=" * 60, flush=True)
        print("[启动失败] 无法在端口 %d 上启动 Web 服务：%s" % (start_port, exc), flush=True)
        print("最常见原因：之前启动的旧版本服务还占着这个端口。", flush=True)
        print("解决办法（任选其一）：", flush=True)
        print("  1. 关闭之前那个黑色的服务窗口；", flush=True)
        print("  2. PowerShell 执行：Get-NetTCPConnection -LocalPort %d | "
              "Select-Object OwningProcess" % start_port, flush=True)
        print("     再执行：Stop-Process -Id <上一步查到的PID>", flush=True)
        print("  3. 换端口启动：set PORT=8080 && python server.py", flush=True)
        print("=" * 60, flush=True)
        raise SystemExit(1)

    srv.daemon_threads = True
    threading.Thread(target=_scheduler, daemon=True).start()
    print("=" * 56, flush=True)
    print("  %s · Web 服务已启动（零依赖模式）" % APP_NAME, flush=True)
    print("  版本：V%s" % APP_VERSION, flush=True)
    print("  本机访问：http://localhost:%d" % port, flush=True)
    print("  局域网访问：http://<本机IP>:%d" % port, flush=True)
    print("  数据文件：%s" % db.DB_PATH, flush=True)
    print("  智能体：%s（未配置密钥自动演示模式）" % get_active_provider_name(), flush=True)
    print("=" * 56, flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止", flush=True)
        srv.shutdown()


if __name__ == "__main__":
    main()
