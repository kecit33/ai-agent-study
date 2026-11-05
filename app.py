"""AI 校园学习陪伴助手 —— Flask 后端入口。

智能体（GPT/文心一言/Kimi/Claude）以可插拔方式接入；未配置密钥时自动回退内置演示模式，
保证无密钥也能完整运行、师生可直接测试。预留 ESP32 硬件联动接口（可选加分项）。
"""
import threading
import time

try:
    from flask import Flask, jsonify, request, send_from_directory
    from flask_cors import CORS
except ImportError as exc:
    raise SystemExit(
        "\n[启动失败] Flask 版后端缺少依赖：%s\n"
        "本机 pip 源不可用（或尚未联网安装 requirements.txt）时，请改用零依赖入口：\n"
        "    python server.py\n"
        "然后访问 http://localhost:5000 —— 功能与 Flask 版完全一致。\n"
        "如需使用 Flask 版，请先执行：pip install -r requirements.txt\n" % exc
    )

import db
from agents import credentials, factory
from agents.factory import (
    get_provider, get_active_provider_name, set_active_provider, list_providers_status,
)
from services import course, tasks, wrong_questions, focus, files as filesvc
from services import study
from hardware import esp32
from version import APP_NAME, APP_VERSION

db.init_db()

app = Flask(__name__, static_folder="static")
CORS(app)

ROOT = db.BASE_DIR if hasattr(db, "BASE_DIR") else "."


# ---------------- 静态页面 ----------------
@app.route("/")
def index():
    return send_from_directory("static", "index.html")


# ---------------- 系统状态 ----------------
@app.route("/api/status")
def api_status():
    return jsonify({
        "app": APP_NAME,
        "version": APP_VERSION,
        "active_provider": get_active_provider_name(),
        "providers": list_providers_status(),
    })


@app.route("/api/providers")
def api_providers():
    return jsonify(list_providers_status())


@app.route("/api/settings/provider", methods=["POST"])
def api_set_provider():
    name = (request.json or {}).get("name", "")
    ok = set_active_provider(name)
    return jsonify({"ok": ok, "active_provider": get_active_provider_name()})


# ---------------- 课程 / 课程记忆 ----------------
@app.route("/api/courses", methods=["GET"])
def api_courses():
    return jsonify(course.list_courses())


@app.route("/api/courses", methods=["POST"])
def api_create_course():
    try:
        c = course.create_course((request.json or {}).get("name", ""))
        return jsonify(c)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/courses/<int:cid>/materials", methods=["GET"])
def api_materials(cid):
    return jsonify(course.list_materials(cid))


@app.route("/api/courses/<int:cid>/materials", methods=["POST"])
def api_add_material(cid):
    try:
        body = request.json or {}
        m = course.add_material(cid, body.get("title", ""), body.get("content", ""))
        return jsonify(m)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


# ---------------- 智能体功能 ----------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    body = request.json or {}
    cid = body.get("course_id")
    msg = body.get("message", "")
    if not cid:
        return jsonify({"error": "请选择课程"}), 400
    return jsonify({"reply": tasks.chat(int(cid), msg)})


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    text = (request.json or {}).get("text", "")
    return jsonify({"result": tasks.summarize(text)})


@app.route("/api/tutor", methods=["POST"])
def api_tutor():
    problem = (request.json or {}).get("problem", "")
    return jsonify({"result": tasks.tutor(problem)})


@app.route("/api/review-plan", methods=["POST"])
def api_review_plan():
    body = request.json or {}
    return jsonify({"result": tasks.review_plan(body.get("subject", ""), body.get("days", 7))})


# ---------------- 错题本 ----------------
@app.route("/api/wrong-questions", methods=["GET"])
def api_wq_list():
    cid = request.args.get("course_id", type=int)
    un = request.args.get("unmastered", "0") == "1"
    return jsonify(wrong_questions.list_wrong_questions(course_id=cid, only_unmastered=un))


@app.route("/api/wrong-questions", methods=["POST"])
def api_wq_add():
    try:
        body = request.json or {}
        w = wrong_questions.add_wrong_question(
            int(body.get("course_id", 0)), body.get("question", ""),
            body.get("user_answer", ""), body.get("correct_answer", ""),
            body.get("error_reason", ""),
        )
        return jsonify(w)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wrong-questions/<int:wid>/analyze", methods=["POST"])
def api_wq_analyze(wid):
    provider = (request.json or {}).get("provider")
    try:
        return jsonify(wrong_questions.analyze_and_variant(wid, provider_name=provider))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wrong-questions/<int:wid>/master", methods=["POST"])
def api_wq_master(wid):
    mastered = (request.json or {}).get("mastered", True)
    wrong_questions.mark_mastered(wid, bool(mastered))
    return jsonify({"ok": True})


# ---------------- 硬件联动 / 复习任务 ----------------
@app.route("/api/review-tasks", methods=["POST"])
def api_review_task():
    body = request.json or {}
    from datetime import datetime
    from db import get_conn
    due = body.get("due_time") or datetime.now().isoformat(timespec="seconds")
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO review_tasks(course_id, task_name, due_time, notified, created_at) VALUES(?, ?, ?, 0, ?)",
        (body.get("course_id"), body.get("task_name", "复习任务"),
         due, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    tid = cur.lastrowid
    conn.close()
    # 支持立即测试下发（用于无真实到点时的演示）
    fired = None
    if body.get("fire_now"):
        from hardware.esp32 import notify_esp32
        fired = notify_esp32(body.get("task_name", "复习任务"))
    return jsonify({"id": tid, "fired": fired})


@app.route("/api/hardware/test", methods=["POST"])
def api_hardware_test():
    body = request.json or {}
    res = esp32.notify_esp32(body.get("task_name", "测试提醒"), body.get("message", "硬件联动测试"))
    return jsonify(res)


# ---------------- 文件上传 / 错题导出 ----------------
@app.route("/api/courses/<int:cid>/materials/upload", methods=["POST"])
def api_upload_material(cid):
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "未收到文件，请使用 multipart 字段 file"}), 400
    try:
        info = filesvc.extract_text(f.filename, f.read())
        result = course.add_material(cid, info["title"], info["text"])
        result.update({"filename": f.filename, "chars": info["chars"],
                       "truncated": info["truncated"], "preview": info["text"][:200]})
        return jsonify(result)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/wrong-questions/export")
def api_wq_export():
    from flask import Response
    cid = request.args.get("course_id", type=int)
    md = wrong_questions.export_markdown(course_id=cid)
    return Response(md, mimetype="text/markdown; charset=utf-8", headers={
        "Content-Disposition": "attachment; filename=wrong-questions.md"})


# ---------------- 学习概览 / 番茄钟 ----------------
@app.route("/api/overview")
def api_overview():
    return jsonify(focus.overview())


@app.route("/api/focus/sessions", methods=["GET"])
def api_focus_sessions():
    return jsonify(focus.list_sessions(request.args.get("limit", 10, type=int)))


@app.route("/api/focus/sessions", methods=["POST"])
def api_focus_record():
    body = request.json or {}
    try:
        result = focus.record_session(
            body.get("minutes", 0), course_id=body.get("course_id"),
            note=body.get("note", ""), started_at=body.get("started_at", ""),
            ended_at=body.get("ended_at", ""))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    esp32.set_focus_state(False)
    result["reminder"] = esp32.notify_esp32(
        "专注完成", message="本次专注 %s 分钟已完成，休息一下吧！" % result["minutes"])
    return jsonify(result)


@app.route("/api/focus/state", methods=["POST"])
def api_focus_state():
    body = request.json or {}
    return jsonify(esp32.set_focus_state(bool(body.get("active")), int(body.get("minutes", 0) or 0)))


@app.route("/api/hardware/status")
def api_hardware_status():
    return jsonify(esp32.hardware_status())


# ---------------- 学习资源包：题目 / 总结 / 文章 / 资料 / 思维导图 ----------------
def _study_args(body=None, query=None):
    body, query = body or {}, query or {}

    def val(key, default=""):
        if key in body:
            return body[key]
        return query.get(key, default)

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


@app.route("/api/study/catalog")
def api_study_catalog():
    return jsonify(study.catalog())


@app.route("/api/study/quiz", methods=["POST"])
def api_study_quiz():
    a = _study_args(request.json)
    return jsonify(study.quiz(a["subject"], a["chapter"], a["count"],
                             a["difficulty"], a["provider_name"]))


@app.route("/api/study/summary", methods=["POST"])
def api_study_summary():
    a = _study_args(request.json)
    return jsonify(study.summary(a["subject"], a["chapter"], a["provider_name"]))


@app.route("/api/study/article", methods=["POST"])
def api_study_article():
    a = _study_args(request.json)
    return jsonify(study.article(a["subject"], a["chapter"], a["provider_name"]))


@app.route("/api/study/resources", methods=["POST"])
def api_study_resources():
    a = _study_args(request.json)
    return jsonify(study.resources(a["subject"], a["chapter"]))


@app.route("/api/study/mindmap", methods=["POST"])
def api_study_mindmap():
    a = _study_args(request.json)
    return jsonify(study.mindmap(a["subject"], a["chapter"], a["provider_name"]))


@app.route("/api/study/mindmap.svg")
def api_study_mindmap_svg():
    a = _study_args(query=request.args)
    svg = study.mindmap(a["subject"], a["chapter"], a["provider_name"])["svg"]
    return Response(svg, mimetype="image/svg+xml")


@app.route("/api/study/pack", methods=["POST"])
def api_study_pack():
    body = request.json or {}
    a = _study_args(body)
    return jsonify(study.pack(a["subject"], a["chapter"], a["count"], a["difficulty"],
                             a["provider_name"], save_to_course=bool(body.get("save_to_course"))))


@app.route("/api/study/pack/export")
def api_study_export():
    from flask import Response
    a = _study_args(query=request.args)
    md = study.export_markdown(a["subject"], a["chapter"], a["count"], a["provider_name"])
    return Response(md, mimetype="text/markdown; charset=utf-8", headers={
        "Content-Disposition": "attachment; filename=study-pack.md"})


# ---------------- 模型接入：文心一言 / Kimi / 自定义端点，运行时可配置 ----------------
@app.route("/api/agent/providers")
def api_agent_providers():
    return jsonify({"active_provider": get_active_provider_name(),
                    "providers": list_providers_status(),
                    "credentials": credentials.list_status()})


@app.route("/api/agent/credentials", methods=["POST"])
def api_agent_credentials():
    body = request.json or {}
    try:
        return jsonify(factory.configure(
            (body.get("provider") or "").strip().lower(),
            body.get("config") or body, activate=bool(body.get("activate"))))
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/agent/credentials/clear", methods=["POST"])
def api_agent_credentials_clear():
    body = request.json or {}
    try:
        return jsonify(factory.clear((body.get("provider") or "").strip().lower()))
    except ValueError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/agent/test", methods=["POST"])
def api_agent_test():
    body = request.json or {}
    name = (body.get("provider") or get_active_provider_name()).strip().lower()
    if name == "demo":
        return jsonify({"ok": True, "provider": "demo", "mode": body.get("mode", "probe"),
                        "reply": "内置演示模式已就绪，无需外部模型"})
    if name not in credentials.PROVIDER_FIELDS:
        return jsonify({"ok": False, "error": "未知提供商：%s" % name}), 400
    c = credentials.get(name)
    ok, reason = credentials.validate(name, c)
    if body.get("mode") == "validate":
        return jsonify({"ok": ok, "provider": name, "mode": "validate", "reason": reason,
                        "configured": ok, "model": c.get("model", ""),
                        "base_url": c.get("base_url", ""),
                        "masked": credentials.status(name)["masked"]})
    if not ok:
        return jsonify({"ok": False, "provider": name, "mode": "probe", "reason": reason,
                        "configured": False, "error": "配置不完整：" + reason})
    return jsonify(factory.probe(name))


@app.route("/api/agent/complete", methods=["POST"])
def api_agent_complete():
    body = request.json or {}
    msgs = body.get("messages")
    if not isinstance(msgs, list) or not msgs:
        msgs = [{"role": "user", "content": body.get("message", "你好")}]
    msgs = [{"role": str(m.get("role", "user")), "content": str(m.get("content", ""))}
            for m in msgs if isinstance(m, dict)]
    return jsonify(factory.direct_complete(
        str(body.get("system_prompt", "你是校园学习陪伴助手，请简洁、准确地回答。")),
        msgs, body.get("provider") or None))


# ---------------- 到点提醒后台调度（轻量） ----------------
def _scheduler():
    while True:
        try:
            esp32.check_due_tasks()
        except Exception:
            pass
        time.sleep(30)


if __name__ == "__main__":
    t = threading.Thread(target=_scheduler, daemon=True)
    t.start()
    port = int(__import__("os").getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
