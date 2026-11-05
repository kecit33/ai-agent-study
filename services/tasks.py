"""智能体任务封装：问答 / 课件总结 / 习题辅导 / 复习计划 / 错因分析 / 定向出题。

统一通过 providers 工厂获取（可插拔）提供商，并保证无密钥时回退演示模式。
约定：任务指令放在 system prompt，user 消息只放原始内容，
避免指令文本污染演示模式的文本处理结果与真实模型的上下文。
"""
from db import get_conn
from agents.factory import get_provider
from services.course import build_course_context


def _history(course_id: int, limit: int = 12) -> list:
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content FROM conversations WHERE course_id=? ORDER BY id DESC LIMIT ?",
        (course_id, limit),
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]


def _save_turn(course_id: int, role: str, content: str):
    from datetime import datetime
    conn = get_conn()
    conn.execute(
        "INSERT INTO conversations(course_id, role, content, created_at) VALUES(?, ?, ?, ?)",
        (course_id, role, content, datetime.now().isoformat(timespec="seconds")),
    )
    conn.commit()
    conn.close()


def chat(course_id: int, message: str, provider_name: str = None) -> str:
    """课程记忆智能体：带课程隔离上下文的问答。"""
    message = (message or "").strip()
    if not message:
        return "（请输入你的问题）"
    system = "【MODE:chat】\n" + build_course_context(course_id)
    history = _history(course_id)
    provider = get_provider(provider_name)
    reply = provider.complete(system, history + [{"role": "user", "content": message}])
    _save_turn(course_id, "user", message)
    _save_turn(course_id, "assistant", reply)
    return reply


def summarize(text: str, provider_name: str = None) -> str:
    """课件总结：提炼知识点 + 生成考点提纲。"""
    text = (text or "").strip()
    if len(text) < 10:
        return "（请粘贴更多课件文字后再总结）"
    system = ("【MODE:summarize】你是课件总结助手。用户消息即为课件原文。"
              "请提炼关键知识点，并生成结构化的复习考点提纲。"
              "输出分两部分：①关键知识点（要点列表）②复习考点提纲（章节化）。")
    provider = get_provider(provider_name)
    return provider.complete(system, [{"role": "user", "content": text}])


def tutor(problem: str, provider_name: str = None) -> str:
    """习题辅导：引导式讲解，先给思路与分步推导，不直接给最终答案。"""
    problem = (problem or "").strip()
    if not problem:
        return "（请把题目贴给我）"
    system = ("【MODE:tutor】你是习题辅导老师。用户消息即为题目原文。"
              "坚持『引导式讲解』：先复述题意、给出破题思路与分步推导框架，"
              "鼓励学生先尝试，绝不一次性甩出标准答案；仅在学生卡住时给针对性提示。")
    provider = get_provider(provider_name)
    return provider.complete(system, [{"role": "user", "content": problem}])


def review_plan(subject: str, days: int, provider_name: str = None) -> str:
    """复习计划：根据科目与剩余天数生成每日安排。"""
    subject = (subject or "未命名科目").strip()
    try:
        days = int(days)
    except Exception:
        days = 7
    system = (f"【MODE:review_plan】你是复习规划助手。请为「科目：{subject}，剩余 {days} 天」"
              f"生成一份按天安排的复习计划，合理分配基础回顾、重点突破、演练、查漏、冲刺阶段。")
    provider = get_provider(provider_name)
    return provider.complete(
        system, [{"role": "user", "content": f"科目：{subject}，剩余 {days} 天"}]
    )


def analyze_error(text: str, provider_name: str = None) -> str:
    """错因分析：依据题目、学生答案与正确答案诊断薄弱知识点。

    使用独立的 MODE 标记，避免落入普通课程问答分支。
    """
    text = (text or "").strip()
    if not text:
        return "（错题内容为空，无法分析）"
    system = ("【MODE:error_analysis】你是学习诊断老师。用户消息包含题目、学生的答案与正确答案。"
              "请指出具体错因（概念混淆 / 方法选择 / 复杂度与边界 / 审题遗漏），"
              "定位薄弱知识点，并给出针对性改进建议。输出简洁分点，不要出题。")
    provider = get_provider(provider_name)
    return provider.complete(system, [{"role": "user", "content": text}])


def generate_variant(wrong_question_text: str, provider_name: str = None) -> str:
    """定向出题：基于错题生成同类变式题。"""
    wrong_question_text = (wrong_question_text or "").strip()
    system = ("【MODE:quiz】你是出题老师。用户消息为一道错题的结构化描述。"
              "请生成 2~3 道同类变式题用于定向巩固，说明考查的知识点，并附简要答案要点。")
    provider = get_provider(provider_name)
    return provider.complete(system, [{"role": "user", "content": wrong_question_text}])
