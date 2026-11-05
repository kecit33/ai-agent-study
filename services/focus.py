"""番茄钟专注记录与学习概览统计。"""
from datetime import datetime

from db import get_conn


def _now():
    return datetime.now().isoformat(timespec="seconds")


def record_session(minutes: int, course_id=None, note: str = "",
                   started_at: str = "", ended_at: str = "") -> dict:
    minutes = int(minutes or 0)
    if minutes <= 0:
        raise ValueError("专注时长需大于 0 分钟")
    if minutes > 24 * 60:
        raise ValueError("单次专注时长异常（超过 24 小时）")
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO focus_sessions(course_id, minutes, note, started_at, ended_at, created_at) "
        "VALUES(?,?,?,?,?,?)",
        (course_id, minutes, (note or "").strip(), started_at or "", ended_at or "", _now()),
    )
    conn.commit()
    sid = cur.lastrowid
    conn.close()
    return {"id": sid, "minutes": minutes}


def list_sessions(limit: int = 10) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT f.*, c.name AS course_name FROM focus_sessions f "
        "LEFT JOIN courses c ON c.id=f.course_id ORDER BY f.id DESC LIMIT ?",
        (int(limit),),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def overview() -> dict:
    """学习概览：课程/资料/错题掌握率/专注时长/待复习任务，一屏看清学习状态。"""
    today = datetime.now().date().isoformat()
    conn = get_conn()
    q = lambda sql, args=(): conn.execute(sql, args).fetchone()[0]

    courses = q("SELECT COUNT(*) FROM courses")
    materials = q("SELECT COUNT(*) FROM course_materials")
    wq_total = q("SELECT COUNT(*) FROM wrong_questions")
    wq_mastered = q("SELECT COUNT(*) FROM wrong_questions WHERE mastered=1")
    focus_today = q("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions WHERE created_at LIKE ?",
                    (today + "%",))
    focus_total = q("SELECT COALESCE(SUM(minutes),0) FROM focus_sessions")
    focus_count = q("SELECT COUNT(*) FROM focus_sessions")
    pending_tasks = q("SELECT COUNT(*) FROM review_tasks WHERE notified=0")
    conn.close()

    return {
        "courses": courses,
        "materials": materials,
        "wrong_total": wq_total,
        "wrong_mastered": wq_mastered,
        "wrong_unmastered": wq_total - wq_mastered,
        "mastery_rate": round(wq_mastered * 100.0 / wq_total, 1) if wq_total else 0.0,
        "focus_today_minutes": focus_today,
        "focus_total_minutes": focus_total,
        "focus_count": focus_count,
        "pending_tasks": pending_tasks,
        "today": today,
        "recent_sessions": list_sessions(5),
    }
