"""学习资源包生成服务：题目 / 总结 / 文章 / 资料 / 思维导图 / 一键全套。

双路径设计（重要）
------------------
* 知识库路径（始终可用）：从 services/subject_knowledge.py 的结构化数据生成，
  内容与「高等数学上册」严格对应，题目自带标准答案与解析。
* 大模型路径（配置密钥后自动启用）：请求当前激活的文心一言 / Kimi / GPT / Claude /
  自定义兼容接口，要求返回严格 JSON，解析成功后作为「AI 增补」并入结果；
  模型未配置、超时、限流或返回格式不合法时静默回退，接口永远返回可用内容。
"""
import json
import re
from datetime import datetime

from agents.factory import get_provider, get_active_provider_name
from services import subject_knowledge as kb
from services import mindmap as mm
from services import course

MAX_COUNT = 30


def _norm_subject(subject: str) -> str:
    name = kb.resolve(subject) or kb.TEXTBOOK
    return name


def _llm_enabled(provider_name: str = None) -> bool:
    """仅当激活的是真实厂商且密钥可用时才走大模型路径。"""
    name = provider_name or get_active_provider_name()
    if not name or name == "demo":
        return False
    try:
        return bool(get_provider(name).is_available())
    except Exception:
        return False


def _llm_raw(system: str, user: str, provider_name: str = None):
    """调用真实模型；返回文本，失败返回 None。"""
    if not _llm_enabled(provider_name):
        return None
    try:
        reply = get_provider(provider_name).complete(
            system, [{"role": "user", "content": user}])
    except Exception:
        return None
    if not reply:
        return None
    # 厂商级错误文案（如「接口调用失败，已回退演示模式」）不能当作有效内容
    if reply.startswith("（") and ("失败" in reply or "未配置" in reply):
        return None
    return reply


def _llm_json(system: str, user: str, provider_name: str = None):
    """解析模型的 JSON 输出，容忍 ```json 代码块与前后缀说明文字。"""
    raw = _llm_raw(system, user, provider_name)
    if not raw:
        return None
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.I | re.M).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    starts = [p for p in (text.find("{"), text.find("[")) if p >= 0]
    if not starts:
        return None
    start = min(starts)
    end = max(text.rfind("}"), text.rfind("]"))
    if end <= start:
        return None
    try:
        return json.loads(text[start:end + 1])
    except Exception:
        return None


def _grounding(subject: str, chapters: list) -> str:
    parts = ["教材/科目：%s" % subject, "章节与知识点（回答必须严格限定在此范围内）："]
    for c in chapters:
        parts.append("- %s：%s" % (c["title"], "、".join(t["name"] for t in c["topics"])))
        parts.append("  核心公式：%s" % "；".join(c["formulas"][:2])[:400])
    return "\n".join(parts)


# ---------------------------------------------------------------- 目录
def catalog() -> dict:
    return kb.catalog()


# ---------------------------------------------------------------- 题目
def quiz(subject: str, chapter: str = "", count: int = 5,
         difficulty: str = "", provider_name: str = None, with_answer: bool = True) -> dict:
    name = _norm_subject(subject)
    chapters = kb.get_chapters(name, chapter)
    try:
        count = max(1, min(int(count), MAX_COUNT))
    except (TypeError, ValueError):
        count = 5

    pool = []
    for c in chapters:
        for q in c["questions"]:
            item = dict(q)
            item["chapter"] = c["title"]
            item["origin"] = "knowledge_base"
            pool.append(item)
    if difficulty:
        hit = [q for q in pool if q.get("difficulty") == difficulty]
        if hit:
            pool = hit
    selected = pool[:count]
    source = "knowledge_base"

    if _llm_enabled(provider_name):
        system = ("你是高校命题老师。只输出 JSON，不要任何解释文字，格式："
                  '{"questions":[{"type":"计算题","difficulty":"中等","stem":"题干",'
                  '"answer":"标准答案","analysis":"分步解析","points":["考点"],"chapter":"所属章节"}]}')
        user = (_grounding(name, chapters) +
                "\n\n请依据上述范围，原创 %d 道%s难度的练习题，覆盖不同题型；"
                "数学表达式用纯文本书写，答案与解析必须正确、可核对。" %
                (count, difficulty or "混合"))
        data = _llm_json(system, user, provider_name)
        extra = (data or {}).get("questions") if isinstance(data, dict) else None
        if isinstance(extra, list):
            for q in extra:
                if isinstance(q, dict) and q.get("stem") and q.get("answer"):
                    item = {
                        "type": q.get("type", "练习题"), "difficulty": q.get("difficulty", "中等"),
                        "stem": str(q["stem"]), "answer": str(q["answer"]),
                        "analysis": str(q.get("analysis", "")),
                        "points": q.get("points") if isinstance(q.get("points"), list) else [],
                        "chapter": q.get("chapter") or chapters[0]["title"],
                        "origin": "llm",
                    }
                    selected.append(item)
            if any(q.get("origin") == "llm" for q in selected):
                source = "hybrid(knowledge_base + llm)"

    if not with_answer:
        selected = [{k: v for k, v in q.items() if k not in ("answer", "analysis")} for q in selected]
    return {
        "subject": name, "scope": chapter or "全部章节",
        "count": len(selected), "requested_count": count,
        "available_in_scope": len(pool),
        "difficulty": difficulty or "混合",
        "source": source, "provider": provider_name or get_active_provider_name(),
        "questions": selected,
    }


# ---------------------------------------------------------------- 总结
def summary(subject: str, chapter: str = "", provider_name: str = None) -> dict:
    name = _norm_subject(subject)
    chapters = kb.get_chapters(name, chapter)
    lines = ["# 《%s》复习总结%s" % (name, "（%s）" % chapter if chapter else "（全册）"), "",
             "> 生成时间：%s ｜ 章节数：%d ｜ 数据来源：内置学科知识库" %
             (datetime.now().strftime("%Y-%m-%d %H:%M"), len(chapters)), ""]
    for c in chapters:
        lines += ["## %s" % c["title"], "", "**本章定位**：%s" % c["overview"], "",
                  "### 知识点清单"]
        for i, t in enumerate(c["topics"], 1):
            lines.append("%d. **%s** — %s" % (i, t["name"], t["detail"]))
        lines += ["", "### 公式 / 定理速查"]
        lines += ["- `%s`" % f for f in c["formulas"]]
        lines += ["", "### 高频易错点"]
        lines += ["- %s" % p for p in c["pitfalls"]]
        lines += ["", "### 学法与考点", "- 学法：%s" % c["method"],
                  "- 常考：%s" % c["exam"], ""]
    md = "\n".join(lines)

    ai_extra = ""
    if _llm_enabled(provider_name):
        system = "你是高校助教。请基于给定教材范围写一段 300 字左右的复习提要，用 Markdown，突出知识主线与备考优先级。"
        text = _llm_raw(system, _grounding(name, chapters), provider_name)
        if text and len(text) >= 60 and not text.startswith("（"):
            ai_extra = text
            md += "\n## AI 增补摘要（由 %s 生成）\n\n%s\n" % (
                provider_name or get_active_provider_name(), text)
    return {
        "subject": name, "scope": chapter or "全部章节", "chapter_count": len(chapters),
        "markdown": md, "source": "hybrid(knowledge_base + llm)" if ai_extra else "knowledge_base",
        "provider": provider_name or get_active_provider_name(),
    }


# ---------------------------------------------------------------- 文章 + 资料
def article(subject: str, chapter: str = "", provider_name: str = None) -> dict:
    name = _norm_subject(subject)
    chapters = kb.get_chapters(name, chapter)
    scope = chapter or "全册"
    lines = ["# 从零理清《%s》（%s）：知识主线、典型题型与复习路线" % (name, scope), ""]
    lines.append("> 本文由「AI 校园学习陪伴助手」依据结构化课程知识库自动编排，"
                 "可直接作为预习笔记、复习讲义或课件讲义初稿使用。")
    lines += ["", "## 摘要", "",
              "《%s》%s 共梳理 %d 个章节、%d 个知识节点、%d 道带解析的自测题。"
              "全文按「为什么学 → 知识脉络 → 核心方法 → 典型题型 → 易错点 → 复习路线 → 参考资料」组织，"
              "目标是让读者在有限时间内建立可迁移的解题框架，而不是零散地背公式。" %
              (name, scope, len(chapters), sum(len(c["topics"]) for c in chapters),
               sum(len(c["questions"]) for c in chapters)), "",
              "## 一、为什么这部分内容值得单独花时间", ""]
    for c in chapters[:3]:
        lines.append("**%s**：%s" % (c["title"], c["overview"]))
        lines.append("")
    lines += ["这些内容前后依赖明显：极限是导数的定义基础，导数与不定积分互为逆运算，"
              "牛顿—莱布尼茨公式把两者打通，定积分的元素法又直接支撑微分方程建模。"
              "任何一环松动，都会在后面的综合题里集中暴露。", "",
              "## 二、知识脉络（按章展开）", ""]
    for c in chapters:
        lines += ["### %s" % c["title"], "", c["overview"], "",
                  "学习抓手：%s" % c["method"], "", "| 知识点 | 要点 |", "| --- | --- |"]
        for t in c["topics"]:
            lines.append("| %s | %s |" % (t["name"], t["detail"].replace("|", "／")))
        lines.append("")
    lines += ["## 三、核心方法与公式速查", ""]
    for c in chapters:
        lines += ["**%s**" % c["title"], ""]
        lines += ["- %s" % f for f in c["formulas"][:3]]
        lines.append("")
    lines += ["## 四、典型题型示例（节选）", ""]
    for c in chapters[:4]:
        lines.append("**%s**" % c["title"])
        for q in c["questions"][:2]:
            lines.append("- （%s·%s）%s → 答案：%s" % (q["type"], q["difficulty"], q["stem"], q["answer"]))
        lines.append("")
    lines += ["## 五、高频易错点清单", ""]
    n = 0
    for c in chapters:
        for p in c["pitfalls"][:2]:
            n += 1
            lines.append("%d. 【%s】%s" % (n, c["title"], p))
    lines += ["", "## 六、七天复习路线建议", "",
              "| 天数 | 任务 | 产出 |", "| --- | --- | --- |"]
    plan = [("第 1 天", "通读知识脉络 + 背记公式速查表", "一页纸知识框架"),
            ("第 2 天", "逐章重做基础题，标注卡壳步骤", "错题清单"),
            ("第 3 天", "专攻中等题，按题型归纳解题模板", "题型—方法对照表"),
            ("第 4 天", "证明题与中值定理专项", "辅助函数构造笔记"),
            ("第 5 天", "综合计算题限时训练", "限时自测卷"),
            ("第 6 天", "回看易错点清单与错题本", "错因归类表"),
            ("第 7 天", "全真模拟 + 思维导图复述", "可复述的思维导图")]
    for r in plan:
        lines.append("| %s | %s | %s |" % r)
    lines += ["", "## 七、延伸资料与工具", ""]
    for r in resources(name, chapter)["items"][:8]:
        lines.append("- **%s**（%s）：%s %s" % (r["title"], r["kind"], r["desc"], r["url"]))
    lines += ["", "## 结语", "",
              "把「看懂」变成「会做」的唯一办法是限时输出：每学完一章，"
              "先合上资料复述思维导图，再做本系统生成的自测题，最后用错题本定位薄弱点。"
              "这也是本助手把题目、总结、文章、资料与思维导图放在同一条链路上的原因。", ""]
    md = "\n".join(lines)

    ai_extra = ""
    if _llm_enabled(provider_name):
        system = "你是科普专栏作者。写一段 250 字左右的导言，语言通俗、有画面感，用 Markdown，不要列表。"
        text = _llm_raw(system, _grounding(name, chapters), provider_name)
        if text and len(text) >= 60 and not text.startswith("（"):
            ai_extra = text
            md = md.replace("## 摘要", "## 摘要\n\n> AI 导言（%s）：%s\n" %
                            (provider_name or get_active_provider_name(), text.replace("\n", " ")), 1)
    return {
        "subject": name, "scope": scope, "title": lines[0].lstrip("# "),
        "markdown": md, "chars": len(md), "sections": 7,
        "source": "hybrid(knowledge_base + llm)" if ai_extra else "knowledge_base",
        "provider": provider_name or get_active_provider_name(),
    }


def resources(subject: str, chapter: str = "") -> dict:
    name = _norm_subject(subject)
    chapters = kb.get_chapters(name, chapter)
    seen, items = set(), []
    for c in chapters:
        idx = c.get("resources") or list(range(len(kb.COMMON_RESOURCES)))
        for r in kb.get_resources(idx):
            if r["title"] in seen:
                continue
            seen.add(r["title"])
            r = dict(r)
            r["chapter"] = c["title"]
            items.append(r)
    if not items:
        items = [dict(r) for r in kb.COMMON_RESOURCES]
    return {
        "subject": name, "scope": chapter or "全部章节", "count": len(items),
        "items": items,
        "reading_order": ["教材对应章节", "公开课视频建立直觉", "带解析的自测题",
                          "可视化工具验证结论", "错题本回看"],
        "source": "knowledge_base",
    }


def mindmap(subject: str, chapter: str = "", provider_name: str = None) -> dict:
    name = _norm_subject(subject)
    chapters = kb.get_chapters(name, chapter)
    result = mm.generate(name, chapters)
    result.update({"scope": chapter or "全部章节", "source": "knowledge_base",
                   "provider": provider_name or get_active_provider_name()})

    if _llm_enabled(provider_name):
        system = ('你是课程设计助手。只输出 JSON：{"extra":[{"chapter":"章节标题关键字",'
                  '"node":"补充的知识点名称"}]}，最多 5 条。')
        data = _llm_json(system, _grounding(name, chapters), provider_name)
        extras = (data or {}).get("extra") if isinstance(data, dict) else None
        added = 0
        if isinstance(extras, list):
            for ex in extras[:5]:
                if not isinstance(ex, dict) or not ex.get("node"):
                    continue
                key, label = str(ex.get("chapter", "")), str(ex["node"])[:24]
                for node in result["root"]["children"]:
                    if not key or key in node["label"]:
                        node["children"].append({"id": "llm-%d" % added, "label": label,
                                                 "detail": "由大模型补充的知识节点", "children": []})
                        added += 1
                        break
        if added:
            result["svg"] = mm.to_svg(result["root"], chapters)
            result["outline"] = mm.to_outline(result["root"])
            result["mermaid"] = mm.to_mermaid(result["root"])
            result["node_count"] = mm._count(result["root"])
            result["source"] = "hybrid(knowledge_base + llm)"
    return result


# ---------------------------------------------------------------- 一键全套
def pack(subject: str, chapter: str = "", count: int = 6, difficulty: str = "",
         provider_name: str = None, save_to_course: bool = False) -> dict:
    name = _norm_subject(subject)
    q = quiz(name, chapter, count, difficulty, provider_name)
    s = summary(name, chapter, provider_name)
    a = article(name, chapter, provider_name)
    r = resources(name, chapter)
    m = mindmap(name, chapter, provider_name)
    result = {
        "subject": name, "discipline": kb.DISCIPLINE if kb.is_builtin(name) else "自定义科目",
        "scope": chapter or "全部章节",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "provider": provider_name or get_active_provider_name(),
        "chapters": [{"id": c["id"], "title": c["title"]} for c in kb.get_chapters(name, chapter)],
        "quiz": q, "summary": s, "article": a, "resources": r, "mindmap": m,
        "has": {"quiz": bool(q["questions"]), "summary": bool(s["markdown"]),
                "article": bool(a["markdown"]), "resources": bool(r["items"]),
                "mindmap": bool(m["svg"])},
    }
    if save_to_course:
        result["saved"] = save_to_memory(name, s["markdown"], a["markdown"])
    return result


def export_markdown(subject: str, chapter: str = "", count: int = 6,
                    provider_name: str = None) -> str:
    name = _norm_subject(subject)
    p = pack(name, chapter, count, provider_name=provider_name)
    q, s, a, r, m = p["quiz"], p["summary"], p["article"], p["resources"], p["mindmap"]
    lines = ["# 《%s》学习资源包" % name, "",
             "> 范围：%s ｜ 生成时间：%s ｜ 智能体：%s ｜ 来源：%s" %
             (p["scope"], p["generated_at"], p["provider"], q["source"]), "",
             "---", "", "## 一、自测题（%d 道）" % q["count"], ""]
    for i, item in enumerate(q["questions"], 1):
        lines += ["### %d. %s" % (i, item["stem"]), "",
                  "- 题型/难度：%s · %s ｜ 章节：%s ｜ 来源：%s" %
                  (item["type"], item["difficulty"], item["chapter"], item["origin"]),
                  "- 考查：%s" % "、".join(item.get("points") or []), "",
                  "**答案**：%s" % item["answer"], "",
                  "**解析**：%s" % item["analysis"], ""]
    lines += ["---", "", "## 二、复习总结", "", s["markdown"],
              "---", "", "## 三、专题文章与资料", "", a["markdown"], "",
              "### 资料清单（%d 项）" % r["count"], ""]
    for item in r["items"]:
        lines.append("- **%s**（%s）— %s <%s>" %
                     (item["title"], item["kind"], item["desc"], item["url"]))
    lines += ["", "---", "", "## 四、思维导图（大纲）", "", "```markdown", m["outline"], "```", "",
              "### Mermaid 源码（可粘贴到支持 Mermaid 的编辑器）", "", "```mermaid", m["mermaid"], "```", "",
              "> 可视化 SVG 请访问 `/api/study/mindmap.svg?subject=...` 或在页面「学习资源包」中查看。", ""]
    return "\n".join(lines)


def save_to_memory(subject: str, summary_md: str, article_md: str) -> dict:
    """把生成结果写回该课程的「课程记忆」，供后续智能问答引用。"""
    try:
        exists = next((c for c in course.list_courses() if c["name"] == subject), None)
        cid = exists["id"] if exists else course.create_course(subject)["id"]
        course.add_material(cid, "AI 生成：复习总结", summary_md[:20000])
        course.add_material(cid, "AI 生成：专题文章", article_md[:20000])
        return {"ok": True, "course_id": cid, "materials": 2}
    except Exception as e:
        return {"ok": False, "error": str(e)}
