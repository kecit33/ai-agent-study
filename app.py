"""AI 校园学习陪伴助手 —— Flask 后端入口。

智能体（GPT/文心一言/Kimi/Claude）以可插拔方式接入；未配置密钥时自动回退内置演示模式，
保证无密钥也能完整运行、师生可直接测试。预留 ESP32 硬件联动接口（可选加分项）。
"""
import threading
import time

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import db
from agents.factory import (
    get_provider, get_active_provider_name, set_active_provider, list_providers_status,
)
from services import course, tasks, wrong_questions
from hardware import esp32

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
