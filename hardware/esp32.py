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
