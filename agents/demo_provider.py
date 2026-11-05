"""内置演示模式提供商。

无需任何 API 密钥即可运行：基于规则与文本处理生成贴合「校园学习陪伴」场景的回答，
保证老师/同学在无密钥情况下也能完整体验全部功能。当配置了真实厂商密钥时，系统自动切换。

各任务通过 system_prompt 中的 【MODE:xxx】 标记区分，避免不同任务互相串味。
"""
import re
from datetime import datetime, timedelta

from .base import AgentProvider


class DemoProvider(AgentProvider):
    name = "demo"
    label = "内置演示模式（无需密钥）"

    _MODE_RE = re.compile(r"【MODE:(\w+)】")
    _INSTRUCTION_RE = re.compile(r"^(请总结|请辅导|请基于|请分析|以下是|用户消息)")

    def is_available(self):
        return True

    def complete(self, system_prompt: str, messages: list) -> str:
        mode = "chat"
        m = self._MODE_RE.search(system_prompt or "")
        if m:
            mode = m.group(1)

        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_user = msg.get("content", "")
                break

        handlers = {
            "summarize": self._summarize,
            "tutor": self._tutor,
            "review_plan": lambda t: self._review_plan(system_prompt, t),
            "quiz": self._quiz,
            "error_analysis": self._error_analysis,
            "chat": lambda t: self._chat(system_prompt, t),
        }
        return handlers.get(mode, lambda t: self._chat(system_prompt, t))(last_user)

    # ---------- 各模式实现 ----------
    def _summarize(self, text: str) -> str:
        text = (text or "").strip()
        if len(text) < 20:
            return "（演示模式）请粘贴更多课件文字，我将为你提炼知识点与考点提纲。"
        sentences = [s.strip() for s in re.split(r"[。；;！!？?\n]", text) if len(s.strip()) >= 8]
        sentences = [s for s in sentences if not self._INSTRUCTION_RE.match(s)]
        key_points = sentences[:6] if sentences else [text[:60]]
        outline = [
            "一、核心概念梳理",
            "二、重点公式 / 定理（请结合课件补充）",
            "三、易混淆点对比",
            "四、典型例题思路",
            "五、考前速记清单",
        ]
        lines = ["【演示模式 · 课件总结】", "", "📌 提取的关键知识点："]
        for i, kp in enumerate(key_points, 1):
            lines.append(f"  {i}. {kp}")
        lines += ["", "📝 建议的复习考点提纲："] + [f"  {o}" for o in outline]
        lines.append("（配置真实大模型密钥后，总结将由 AI 结合语义深度生成。）")
        return "\n".join(lines)

    def _tutor(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return "（演示模式）请把题目贴给我，我会先给思路，再分步引导，不直接甩答案。"
        return (
            "【演示模式 · 习题辅导】\n\n"
            "我先不直接给答案，按「引导式讲解」帮你理清思路：\n\n"
            f"1. 题意复述：这道题考查的是——「{text[:40]}…」相关的知识点。\n"
            "2. 破题思路：先明确已知条件和所求目标，判断它属于哪一类典型题型。\n"
            "3. 第一步：列出你能直接得出的结论或公式。\n"
            "4. 第二步：把问题拆成更小的子问题，逐个突破。\n"
            "5. 自检：把结果代回原题验证是否成立。\n\n"
            "👉 你先按这个步骤试一下，卡在哪一步告诉我，我再针对性提示。"
        )

    def _review_plan(self, system_prompt: str, text: str) -> str:
        subject = "指定科目"
        days = 7
        sm = re.search(r"科目[:：]\s*([^\n,，」]+)", text or system_prompt or "")
        dm = re.search(r"(\d+)\s*天", text or system_prompt or "")
        if sm:
            subject = sm.group(1).strip()
        if dm:
            days = int(dm.group(1))
        days = max(1, min(days, 30))
        lines = [f"【演示模式 · 复习计划】科目：{subject}　剩余：{days} 天\n"]
        phase = ["基础回顾", "重点突破", "真题/例题演练", "查漏补缺", "冲刺复盘"]
        per = max(1, days // len(phase))
        d = 1
        for p in phase:
            for _ in range(per):
                if d > days:
                    break
                lines.append(f"· 第 {d} 天：{subject} — {p}（每日 2~3 小时，配合错题本）")
                d += 1
        if d <= days:
            lines.append(f"· 第 {d}~{days} 天：机动复盘 + 模拟自测")
        lines.append("\n（配置真实大模型密钥后，计划将结合你的课程资料个性化生成。）")
        return "\n".join(lines)

    def _quiz(self, text: str) -> str:
        text = (text or "").strip()
        m = re.search(r"题目[:：]\s*([^\n]+)", text)
        base = (m.group(1).strip() if m else text)[:60] or "该错题对应的知识点"
        return (
            "【演示模式 · 定向变式题】\n\n"
            f"基于你之前的错题「{base}…」生成同类变式题，用于定向巩固：\n\n"
            "变式 1：改变已知条件，请你用相同思路重新求解。\n"
            "变式 2：把选择题改为简答题，训练完整表述。\n"
            "变式 3：给出错误做法，请你指出错因并改正。\n\n"
            "考查知识点：该错题对应的核心概念与适用条件；"
            "答案要点：先明确方法选择依据，再给出推导过程并做边界自检。\n\n"
            "做完后把答案发我，我帮你批改并标注薄弱点。"
        )

    def _error_analysis(self, text: str) -> str:
        """错因诊断：与错题本「分析错因」按钮对应，输出结构化诊断而非通用问答。"""
        def field(label):
            m = re.search(rf"{label}[:：]\s*([^\n]*)", text or "")
            return (m.group(1).strip() if m else "")

        question = field("题目") or text[:60]
        user_ans = field("我的答案") or "（未填写）"
        correct = field("正确答案") or "（未填写）"
        return (
            "【演示模式 · 错因分析】\n\n"
            f"· 题目：{question}\n"
            f"· 你的答案：{user_ans}\n"
            f"· 参考答案：{correct}\n\n"
            "🔍 可能的错因归类：\n"
            "  1. 方法选择：直接套用了最直观的解法，未评估其在本题输入规模下的代价。\n"
            "  2. 概念边界：对该知识点适用条件与前提的理解不够完整。\n"
            "  3. 复杂度 / 边界意识：未检查解法在规模增大或边界输入下是否仍成立。\n\n"
            "📌 薄弱知识点定位：建议回到该知识点的基础定义、复杂度分析与典型例题重新过一遍。\n"
            "✅ 改进建议：先列出候选解法并比较代价 → 用小样本手算验证 → 再做同类题巩固。\n\n"
            "（配置真实大模型密钥后，错因将由 AI 结合题目语义精准诊断。）"
        )

    def _chat(self, system_prompt: str, text: str) -> str:
        course = "当前课程"
        cm = re.search(r"课程[:：]\s*([^\n,，」]+)", system_prompt or "")
        if cm:
            course = cm.group(1).strip()
        text = (text or "").strip()
        if not text:
            return f"（演示模式）已进入「{course}」上下文，有什么课程问题尽管问我～"
        return (
            f"（演示模式 · 课程记忆已绑定「{course}」）\n\n"
            f"你问的是：{text}\n\n"
            "基于已上传的课程资料，我的回答会限定在该课程范围内，避免超纲跑偏。"
            "（配置真实大模型密钥后，这里会由 AI 结合你的课件内容给出精准解答。）"
        )
