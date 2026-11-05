"""ESP32 硬件联动（可选加分项）。

Web 端设置的复习任务到点后，向 ESP32 开发板下发的 HTTP 接口发送提醒，
ESP32 收到后点亮 LED 并触发蜂鸣器，在桌面形成实物提醒。

该模块仅为「接口联动」：无需硬件也能运行主体功能；配置了 ESP32_ENDPOINT 后自动启用。
"""
from config import ESP32_ENDPOINT
from db import get_conn


def notify_esp32(task_name: str, message: str = "") -> dict:
    """向 ESP32 下发复习提醒。返回发送结果。"""
    if not ESP32_ENDPOINT:
        return {"sent": False, "reason": "未配置 ESP32_ENDPOINT（硬件联动为可选加分项，不影响主体功能）"}
    import requests
    payload = {"task": task_name, "message": message or f"该复习啦：{task_name}", "ts": _now()}
    try:
        resp = requests.post(ESP32_ENDPOINT, json=payload, timeout=5)
        return {"sent": True, "status_code": resp.status_code, "endpoint": ESP32_ENDPOINT}
    except Exception as e:
        return {"sent": False, "reason": f"下发失败：{e}"}


def _now():
    from datetime import datetime
    return datetime.now().isoformat(timespec="seconds")


def check_due_tasks() -> list:
    """扫描到期且未提醒的复习任务，逐一下发并标记。返回本次下发的任务列表。"""
    from datetime import datetime
    now = datetime.now().isoformat(timespec="seconds")
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM review_tasks WHERE notified=0 AND due_time<=?", (now,)
    ).fetchall()
    fired = []
    for r in rows:
        res = notify_esp32(r["task_name"])
        conn.execute("UPDATE review_tasks SET notified=1 WHERE id=?", (r["id"],))
        fired.append({"id": r["id"], "task": r["task_name"], "result": res})
    conn.commit()
    conn.close()
    return fired


# ---------------- 专注状态灯（番茄钟联动） ----------------

def set_focus_state(active: bool, minutes: int = 0) -> dict:
    """记录专注状态并推送 ESP32：专注中 LED 常亮，结束熄灭。"""
    conn = get_conn()
    conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES('focus_active', ?)",
                 ("1" if active else "0",))
    conn.execute("INSERT OR REPLACE INTO settings(key, value) VALUES('focus_since', ?)",
                 (_now() if active else "",))
    conn.commit()
    conn.close()
    pushed = _push_focus(active, minutes)
    return {"active": active, "pushed": pushed}


def _push_focus(active: bool, minutes: int) -> dict:
    """向 ESP32 的 /focus 端点推送专注状态；未配置或失败不影响主体。"""
    if not ESP32_ENDPOINT:
        return {"sent": False, "reason": "未配置 ESP32_ENDPOINT，专注状态仅在 Web 端展示"}
    import requests
    url = ESP32_ENDPOINT.rsplit("/", 1)[0] + "/focus"
    try:
        resp = requests.post(url, json={"active": bool(active), "minutes": int(minutes), "ts": _now()}, timeout=5)
        return {"sent": True, "status_code": resp.status_code, "endpoint": url}
    except Exception as e:
        return {"sent": False, "reason": "专注状态下发失败：%s" % e}


def hardware_status() -> dict:
    """供 ESP32 轮询的学习状态看板：待复习任务、待掌握错题、专注状态。

    ESP32 定时 GET /api/hardware/status，可把这三项显示在 OLED / 串口，
    让开发板成为桌面「学习状态屏」，形成双向联动（下行提醒 + 上行状态）。
    """
    conn = get_conn()
    pending = conn.execute("SELECT COUNT(*) FROM review_tasks WHERE notified=0").fetchone()[0]
    unmastered = conn.execute("SELECT COUNT(*) FROM wrong_questions WHERE mastered=0").fetchone()[0]
    row = conn.execute("SELECT value FROM settings WHERE key='focus_active'").fetchone()
    since = conn.execute("SELECT value FROM settings WHERE key='focus_since'").fetchone()
    conn.close()
    return {
        "pending_tasks": pending,
        "unmastered_wrong": unmastered,
        "focus_active": bool(row and row["value"] == "1"),
        "focus_since": since["value"] if since else "",
        "server_time": _now(),
        "display": "待复习 %d | 待掌握错题 %d | %s" % (
            pending, unmastered, "专注中" if (row and row["value"] == "1") else "空闲"),
    }
