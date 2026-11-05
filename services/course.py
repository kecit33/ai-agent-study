"""课程与「课程记忆」服务：按课程隔离上下文，是杀手级功能的底座。"""
from datetime import datetime

from db import get_conn


def list_courses() -> list:
    conn = get_conn()
    rows = conn.execute("SELECT id, name, created_at FROM courses ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_course(name: str) -> dict:
    name = (name or "").strip()
    if not name:
        raise ValueError("课程名不能为空")
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO courses(name, created_at) VALUES(?, ?)",
                           (name, datetime.now().isoformat(timespec="seconds")))
        conn.commit()
        cid = cur.lastrowid
    except Exception as e:
        conn.close()
        raise ValueError("课程名可能已存在") from e
    conn.close()
    return {"id": cid, "name": name}


def add_material(course_id: int, title: str, content: str) -> dict:
    content = (content or "").strip()
    if not content:
        raise ValueError("资料内容不能为空")
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO course_materials(course_id, title, content, created_at) VALUES(?, ?, ?, ?)",
        (course_id, (title or "").strip(), content, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    mid = cur.lastrowid
    conn.close()
    return {"id": mid, "course_id": course_id}


def list_materials(course_id: int) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, course_id, title, content, created_at FROM course_materials WHERE course_id=? ORDER BY id",
        (course_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def build_course_context(course_id: int) -> str:
    """拼接该课程已上传的资料，作为智能体系统提示的「课程记忆」上下文。"""
    conn = get_conn()
    course = conn.execute("SELECT name FROM courses WHERE id=?", (course_id,)).fetchone()
    mats = conn.execute(
        "SELECT title, content FROM course_materials WHERE course_id=? ORDER BY id", (course_id,)
    ).fetchall()
    conn.close()
    cname = course["name"] if course else "未知课程"
    # 结构化课程标记：供演示模式解析，也让真实模型明确当前课程边界
    parts = [f"【课程记忆】课程：{cname}",
             f"你是一款校园学习陪伴助手，当前绑定的课程是「{cname}」。"]
    parts.append("以下是该课程学生已上传的学习资料（你的回答必须严格限定在此课程范围内，"
                 "不超纲、不跑偏；若资料未覆盖，请说明并建议复习方向）：\n")
    for i, m in enumerate(mats, 1):
        t = f"（资料{i}：{m['title']}）\n" if m["title"] else f"（资料{i}）\n"
        # 控制上下文长度，避免超长
        content = m["content"][:4000]
        parts.append(t + content)
    if not mats:
        parts.append("（该课程暂无上传资料，请基于通用课程知识作答，并提醒学生上传资料以获得更精准的回答。）")
    return "\n".join(parts)
