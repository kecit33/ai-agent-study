"""AI 错题本服务：录题、错误原因、掌握状态、定向变式出题。"""
from datetime import datetime

from db import get_conn
from services.tasks import generate_variant, analyze_error


def add_wrong_question(course_id: int, question: str, user_answer: str = "",
                       correct_answer: str = "", error_reason: str = "") -> dict:
    question = (question or "").strip()
    if not question:
        raise ValueError("错题内容不能为空")
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO wrong_questions(course_id, question, user_answer, correct_answer, error_reason, mastered, created_at) "
        "VALUES(?, ?, ?, ?, ?, 0, ?)",
        (course_id, question, user_answer, correct_answer, error_reason,
         datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    wid = cur.lastrowid
    conn.close()
    return {"id": wid, "course_id": course_id}


def list_wrong_questions(course_id: int = None, only_unmastered: bool = False) -> list:
    conn = get_conn()
    sql = "SELECT * FROM wrong_questions"
    args = []
    where = []
    if course_id:
        where.append("course_id=?")
        args.append(course_id)
    if only_unmastered:
        where.append("mastered=0")
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"
    rows = conn.execute(sql, args).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def analyze_and_variant(wid: int, provider_name: str = None) -> dict:
    """分析错因并生成变式题：若未填错因，则用智能体推断；同时生成定向变式题。"""
    conn = get_conn()
    row = conn.execute("SELECT * FROM wrong_questions WHERE id=?", (wid,)).fetchone()
    conn.close()
    if not row:
        raise ValueError("错题不存在")
    text = f"题目：{row['question']}\n我的答案：{row['user_answer']}\n正确答案：{row['correct_answer']}\n"
    if not row["error_reason"]:
        # 用独立的「错因诊断」模式，避免落到普通课程问答
        reason = analyze_error(text, provider_name=provider_name)
        conn = get_conn()
        conn.execute("UPDATE wrong_questions SET error_reason=? WHERE id=?", (reason, wid))
        conn.commit()
        conn.close()
    else:
        reason = row["error_reason"]
    variant = generate_variant(text, provider_name=provider_name)
    return {"id": wid, "error_reason": reason, "variant": variant}


def mark_mastered(wid: int, mastered: bool = True) -> bool:
    conn = get_conn()
    conn.execute("UPDATE wrong_questions SET mastered=? WHERE id=?", (1 if mastered else 0, wid))
    conn.commit()
    conn.close()
    return True


def export_markdown(course_id: int = None) -> str:
    """导出错题本为 Markdown，便于打印或导入笔记软件复盘。"""
    rows = list_wrong_questions(course_id=course_id)
    lines = ["# AI 错题本导出", "",
             "> 导出错题 %d 道 · 生成时间 %s" % (len(rows), datetime.now().isoformat(timespec="seconds")), ""]
    if not rows:
        lines.append("（暂无错题，先去录入一道错题吧）")
    for i, w in enumerate(rows, 1):
        lines += [
            "## %d. 错题 #%d %s" % (i, w["id"], "（已掌握）" if w["mastered"] else "（待掌握）"),
            "",
            "**题目**：" + (w["question"] or ""),
            "",
        ]
        if w["user_answer"]:
            lines += ["**我的答案**：" + w["user_answer"], ""]
        if w["correct_answer"]:
            lines += ["**正确答案**：" + w["correct_answer"], ""]
        if w["error_reason"]:
            lines += ["**错因分析**：", "", w["error_reason"], ""]
        lines += ["- 录入时间：%s" % w["created_at"], "", "---", ""]
    return "\n".join(lines)
