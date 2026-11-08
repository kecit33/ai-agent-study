# -*- coding: utf-8 -*-
"""生成 28 页 .slide 源文件（团队展示 / 选题报告 / 成果展示 / 需求分析）。

V1.5.0 答辩演示 · 整体优化版（2026-11-08）
- 原独立「技术选型与系统架构」页删除，架构结论压缩进「选题依据」页；
- 第一部分由 5 页精简为 3 页（队名/分工/队员风采合并，保留合照与愿景原文）；
- 第二部分扩充选题背景、选题依据、选题价值，能力全景按复习闭环重排；
- 第三部分压缩单图页文字冗余，7 页真实界面拆为 4+3 两组，中间插入成果亮点页，章末收束为成果结论。

内容取自用户提供的真实团队资料与 docs/软件需求规格说明书.md（V1.5.0 验收基线）。
配图全部为项目真实资产，无 AI 生图、无编造数据。
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "slides")
os.makedirs(OUT, exist_ok=True)

BLUE = "#1E4FA8"
BLUE2 = "#2E5FBB"
MID = "#3D7BD9"
PALE = "#E8EFF8"
PALE2 = "#F7F9FC"
INK = "#1A2230"
GRAY = "#4A5568"
LIGHT = "#8B97A8"
LINE = "#E5E7EB"
RED = "#D9534F"
WHITE = "#FFFFFF"


def T(s, size=20, color=INK, bold=False, lh=1.5, mt=0, align=None, width=None):
    fw = "'bold'" if bold else "'normal'"
    ex = ""
    if align:
        ex += ", textAlign: '%s'" % align
    if width:
        ex += ", width: %d" % width
    return ("<Text style={{ fontSize: %d, color: '%s', fontWeight: %s, lineHeight: %s, "
            "margin: 0, marginTop: %d%s }}>%s</Text>"
            % (size, color, fw, lh, mt, ex, s))


def B(inner, style):
    return "<Box style={{ %s }}>%s</Box>" % (style, inner)


def IMG(src, w, h, fit="contain"):
    return ("<Image src=\"assets/%s\" style={{ width: %d, height: %d, objectFit: '%s' }} />"
            % (src, w, h, fit))


def RULE(w=1160, color=LINE):
    return B("", "width: %d, height: 1, background: '%s'" % (w, color))


def CONTENT(title, chapter, num, body):
    head = B(
        T(title, 34, WHITE, True, 1.2) + T(chapter, 16, "#CADCFC", False, 1.2),
        "width: '100%', height: 72, flexDirection: 'row', alignItems: 'center', "
        "justifyContent: 'space-between', padding: 24, background: '#1E4FA8'")
    main = B(body, "width: '100%', height: 497, flexDirection: 'column'")
    foot = B(
        T("AI 校园学习陪伴助手  ·  课程作业答辩", 14, LIGHT, False, 1.3)
        + T("%02d / 28" % num, 14, LIGHT, False, 1.3),
        "width: '100%', height: 30, flexDirection: 'row', alignItems: 'center', "
        "justifyContent: 'space-between'")
    return ("<Slide padding={60} style={{ background: '#FFFFFF', fontFamily: 'Microsoft YaHei', "
            "flexDirection: 'column' }}>" + head + RULE() + main + foot + "</Slide>")


def SECTION(num, name, kw):
    return ("<Slide padding={60} style={{ background: '#FFFFFF', fontFamily: 'Microsoft YaHei', "
            "flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>"
            + B(T(num, 180, BLUE, True, 1.0),
                "width: 420, height: 320, background: '#E8EFF8', flexDirection: 'row', "
                "alignItems: 'center', justifyContent: 'center'")
            + B(T(name, 52, INK, True, 1.2) + T(kw, 20, GRAY, False, 1.5, 26),
                "width: 640, flexDirection: 'column'")
            + "</Slide>")


def NUM(n):
    return B(T(n, 18, WHITE, True, 1.0, align="center"),
             "width: 30, height: 30, background: '#1E4FA8', flexDirection: 'row', "
             "alignItems: 'center', justifyContent: 'center'")


def CARD(inner, w, h, bg=WHITE, pad=18):
    return B(inner, "width: %d, height: %d, background: '%s', border: '1px solid #D6DCE5', "
             "borderRadius: 6, padding: %d, flexDirection: 'column'" % (w, h, bg, pad))


def BAR(text, h=48, bg=PALE, color=INK, size=19):
    return B(T(text, size, color, False, 1.4),
             "width: 1160, height: %d, background: '%s', flexDirection: 'row', "
             "alignItems: 'center', padding: 16" % (h, bg))


def HL(text):
    """蓝色一句话亮点条，用于成果展示单图页。"""
    return B(T(text, 17, WHITE, True, 1.4),
             "width: 440, height: 46, background: '#1E4FA8', flexDirection: 'row', "
             "alignItems: 'center', padding: 12")


PAGES = []

# ---------------- P01 封面 ----------------
chips = ""
for n, label in [("01", "团队展示"), ("02", "选题报告"),
                 ("03", "成果展示"), ("04", "需求分析")]:
    chips += B(T(n, 38, "#CADCFC", True, 1.0) + T(label, 22, WHITE, False, 1.3),
               "width: 310, height: 96, flexDirection: 'row', alignItems: 'center', gap: 22, "
               "padding: 20, background: '#2E5FBB'")
PAGES.append(
    "<Slide padding={60} style={{ background: '#1E4FA8', fontFamily: 'Microsoft YaHei', "
    "flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>"
    + B(T("智能体开发课程作业  ·  V1.5.0 验收基线", 18, "#CADCFC", False, 1.4)
        + T("AI 校园学习<br />陪伴助手", 64, WHITE, True, 1.18, 30)
        + T("团队展示  ·  选题报告  ·  成果展示  ·  需求分析", 25, PALE, False, 1.4, 26)
        + T("无言以对队   ｜   陈明凯 · 邓文炜   ｜   2026-11", 16, "#CADCFC", False, 1.4, 62),
        "width: 720, flexDirection: 'column', justifyContent: 'center'")
    + B(chips, "width: 310, flexDirection: 'column', gap: 16")
    + "</Slide>")

# ---------------- P02 目录（页码区间随新结构同步） ----------------
rows = ""
for idx, (n, name, pg, en, kw) in enumerate([
        ("01", "团队展示", "P03 – P05", "Team", "队名 · 分工与队员风采 · 合照与愿景"),
        ("02", "选题报告", "P06 – P10", "Topic", "选题背景 · 选题依据 · 选题价值 · 能力全景"),
        ("03", "成果展示", "P11 – P21", "Achievements", "已上线系统 · 7 页真实界面 · 亮点与结论"),
        ("04", "需求分析", "P22 – P27", "Requirements", "国标依据 · 前后端详述 · 可判定验收")]):
    rows += B(
        B(T(n, 34, WHITE, True, 1.0, align="center"),
          "width: 66, height: 66, background: '#1E4FA8', flexDirection: 'row', "
          "alignItems: 'center', justifyContent: 'center'")
        + B(T(name + "   " + en, 32, INK, True, 1.2) + T(kw, 16, LIGHT, False, 1.3, 6),
            "flexDirection: 'column', marginLeft: 28")
        + B(T(pg, 18, GRAY, False, 1.3),
            "marginLeft: 'auto', flexDirection: 'row', alignItems: 'center'"),
        "width: 1160, height: 88, flexDirection: 'row', alignItems: 'center'")
    if idx < 3:
        rows += RULE()
PAGES.append(
    "<Slide padding={60} style={{ background: '#FFFFFF', fontFamily: 'Microsoft YaHei', "
    "flexDirection: 'column' }}>"
    + B(T("目录", 46, BLUE, True, 1.2) + T("CONTENTS", 18, LIGHT, False, 1.3, 8),
        "width: 1160, height: 96, flexDirection: 'column'")
    + RULE()
    + B(rows, "width: 1160, height: 400, flexDirection: 'column', marginTop: 24")
    + T("智能体开发课程作业答辩  ·  无言以对队", 16, GRAY, False, 1.4, 20)
    + "</Slide>")

# ================= 01 团队展示（精简：5 页 -> 3 页） =================
PAGES.append(SECTION("01", "团队展示", "2 人小队  ·  分工与项目愿景"))

# ---------------- P04 队名 · 分工 · 队员风采（合并原 P04/P05/P06） ----------------
def TEAM_CARD(name, sid, role, trait, skill, duty):
    head = B(
        B(T(name[0], 32, WHITE, True, 1.0, align="center"),
          "width: 54, height: 54, background: '#1E4FA8', flexDirection: 'row', "
          "alignItems: 'center', justifyContent: 'center'")
        + B(T(name, 26, INK, True, 1.2) + T("学号 " + sid, 15, LIGHT, False, 1.3, 2),
            "flexDirection: 'column', marginLeft: 14"),
        "width: 520, height: 58, flexDirection: 'row', alignItems: 'center'")
    rolebar = B(T(role, 18, BLUE, True, 1.3),
                "width: 520, height: 34, background: '#E8EFF8', flexDirection: 'row', "
                "alignItems: 'center', padding: 10, marginTop: 8")
    fields = [("性格与兴趣", trait), ("擅长的技术", skill), ("主要负责", duty)]
    txt = ""
    for i, (k, v) in enumerate(fields):
        txt += B(T(k, 17, BLUE, True, 1.3) + T(v, 15, GRAY, False, 1.4, 3),
                 "width: 520, flexDirection: 'column'" + (", marginTop: 10" if i else ""))
    return CARD(head + rolebar + txt, 560, 360, PALE2, 16)


body04 = (
    B(B(T("队名", 15, LIGHT, False, 1.3) + T("无言以对", 42, BLUE, True, 1.15, 2),
        "width: 270, flexDirection: 'column'")
      + B(T("2 人小队，按后端与质量保障 / 前端与交互体验双线分工，覆盖架构、后端、前端、测试与文档全链路。",
            19, INK, False, 1.45),
          "width: 860, flexDirection: 'column', justifyContent: 'center'"),
      "width: 1160, height: 76, flexDirection: 'row', alignItems: 'center', gap: 30")
    + B(TEAM_CARD(
        "陈明凯", "3124004503", "后端开发 · 测试工程师",
        "严谨细致，善于复盘；阅读技术博客、调试开源项目、整理文档。",
        "Python 后端、标准库 HTTP 服务、SQLite、接口设计、自动化测试。",
        "系统架构、server.py、agents 抽象层、四套回归脚本、三轮自查修复、项目文档。")
       + TEAM_CARD(
        "邓文炜", "3124004505", "前端开发",
        "想法活跃，重视体验；UI 交互设计、截图原型、Web 安全前端风险。",
        "原生 HTML/CSS/JS、Markdown 渲染、页面状态管理、前端故障排查。",
        "全部前端页面、10 个导航模块、安全 Markdown 渲染器、忙碌态、资料查看与下载、XSS 验证。"),
       "width: 1160, height: 360, flexDirection: 'row', justifyContent: 'space-between', marginTop: 10")
    + B(BAR("必要背景到此为止：分工不重叠，成果由两条线共同交付；以下进入选题依据与成果。", 40),
        "width: 1160, marginTop: 6"))
PAGES.append(CONTENT("队名 · 分工 · 队员风采", "01 · Team", 4, body04))

# ---------------- P05 合照 + 愿景（愿景原文逐字保留） ----------------
frame = B(
    T("团队首次合照", 26, GRAY, True, 1.3)
    + T("此处放团队首次合照", 20, BLUE, False, 1.4, 18)
    + T("（待补：团队首次线下合照）", 16, LIGHT, False, 1.4, 8),
    "width: 620, height: 400, border: '2px dashed #D6DCE5', borderRadius: 8, "
    "flexDirection: 'column', alignItems: 'center', justifyContent: 'center'")
vision = (
    "我们希望 AI 校园学习陪伴助手，能真正服务在校学生的课程复习场景。"
    "不做泛化闲聊，而是贴合课堂课件、作业错题，提供引导式学习辅助。"
    "未来期望优化长文档记忆与多用户能力，让它成为轻量化、易部署的课堂学习工具，"
    "帮助同学理清薄弱知识点，形成完整复习闭环。")
body05 = B(
    B(frame, "width: 640, flexDirection: 'column'")
    + B(T("团队项目愿景", 28, BLUE, True, 1.3)
        + T("未来期望 · 非 V1.5.0 已实现能力", 14, LIGHT, False, 1.3, 2)
        + T(vision, 20, INK, False, 1.6, 20)
        + B(T("不做泛化闲聊  ·  形成复习闭环", 20, WHITE, True, 1.4),
            "width: 470, height: 52, background: '#1E4FA8', flexDirection: 'row', "
            "alignItems: 'center', padding: 14, marginTop: 24"),
        "width: 480, flexDirection: 'column'"),
    "width: 1160, height: 497, flexDirection: 'row', gap: 24")
PAGES.append(CONTENT("首次合照与项目愿景", "01 · Team", 5, body05))

# ================= 02 选题报告（扩充：3 内容页 -> 4 内容页；原架构独立页删除） =================
PAGES.append(SECTION("02", "选题报告", "从备考痛点到依据，再到价值与能力"))

# ---------------- P07 选题背景（增强场景与核心问题） ----------------
pains = [
    ("课程上下文缺失", "通用聊天工具不区分课程，每次提问都要重新交代教材、进度与薄弱点。"),
    ("资料难以沉淀", "课件、作业、错题散落在本地与聊天记录里，无法形成可复用的复习上下文。"),
    ("复习缺少闭环", "计划靠手工安排，错题录入、错因诊断、变式练习与掌握确认彼此断开。"),
]
pain_rows = ""
for i, (k, v) in enumerate(pains):
    pain_rows += B(NUM("0" + str(i + 1)) + B(T(k, 22, INK, True, 1.3) + T(v, 18, GRAY, False, 1.45, 6),
                                            "flexDirection: 'column', marginLeft: 14"),
                   "width: 700, height: 90, flexDirection: 'row', alignItems: 'flex-start'"
                   + (", marginTop: 10" if i else ""))
chain = [("课件与资料", "按课程上传"), ("提问与总结", "带上下文"),
         ("错题与计划", "沉淀复用"), ("到点提醒", "闭环收口")]
chain_rows = ""
for i, (k, v) in enumerate(chain):
    chain_rows += B(T("0" + str(i + 1), 18, BLUE, True, 1.2, width=36)
                    + T(k, 19, INK, True, 1.3, width=190) + T(v, 16, GRAY, False, 1.3, width=150),
                    "width: 400, height: 62, flexDirection: 'row', alignItems: 'center', "
                    "background: '#F7F9FC', borderBottom: '1px solid #E5E7EB', padding: 10"
                    + (", marginTop: 10" if i else ""))
body07 = (
    B(B(T("核心问题：能否把「课程」作为一等对象，让智能体在真实备考流程中持续可用？", 21, WHITE, True, 1.4),
        "width: 1160, height: 62, background: '#1E4FA8', flexDirection: 'row', "
        "alignItems: 'center', padding: 18"), "width: 1160")
    + B(B(T("真实备考场景的三个断点", 20, BLUE, True, 1.3)
          + B(pain_rows, "width: 700, flexDirection: 'column', marginTop: 10"),
          "width: 700, flexDirection: 'column'")
        + B(T("期望的复习链路", 20, BLUE, True, 1.3)
            + B(chain_rows, "width: 420, flexDirection: 'column', marginTop: 10"),
            "width: 420, flexDirection: 'column'"),
        "width: 1160, height: 340, flexDirection: 'row', justifyContent: 'space-between', marginTop: 18")
    + B(BAR("背景结论：学习上下文必须按课程被系统记住，而不是靠用户每次重新输入。", 46),
        "width: 1160, marginTop: 12"))
PAGES.append(CONTENT("选题背景 · 课程复习中的三个断点", "02 · Topic", 7, body07))

# ---------------- P08 选题依据（新增；吸收原 P11 架构结论，不再单独占页） ----------------
basis_rows = [
    ("需求依据", "课程作业要求交付可运行系统与可验收文档；需求文档按 GB/T 9385-2008 口径编写。"),
    ("技术依据", "Python 标准库 ThreadingHTTPServer 单一 server.py + SQLite 8 张表；原生前端无构建，6 个 Provider 可插拔。"),
    ("验证依据", "A01–A39 每条给出可判定条件；startup / demo / feature / study 四套回归与 JSON 证据可复核。"),
]
b_rows = ""
for i, (k, v) in enumerate(basis_rows):
    b_rows += B(T(k, 21, BLUE, True, 1.3) + T(v, 17, GRAY, False, 1.5, 6),
                "width: 470, flexDirection: 'column'" + (", marginTop: 16" if i else ""))
body08 = (
    B(B(IMG("architecture.png", 620, 316)
        + T("图 1  V1.5.0 系统架构：单一零依赖后端 / 8 张表 / 30 秒调度", 14, LIGHT, False, 1.3, 8),
        "width: 640, flexDirection: 'column'")
      + B(b_rows, "width: 480, flexDirection: 'column', padding: 8"),
      "width: 1160, height: 372, flexDirection: 'row', justifyContent: 'space-between', gap: 20")
    + B(BAR("技术约束：一条 python server.py 即可启动，适配答辩机房与离线演示；未配置密钥时自动降级演示模式。", 48),
        "width: 1160, marginTop: 12")
    + B(T("依据结论：选题不依赖外部商业服务，也不依赖专用硬件，具备在课程作业范围内做完并验明的条件。",
          18, INK, True, 1.4), "width: 1160, height: 34, flexDirection: 'column', marginTop: 10"))
PAGES.append(CONTENT("选题依据 · 需求、技术与可验证性", "02 · Topic", 8, body08))

# ---------------- P09 选题价值（新增；定性价值，不列与成果重复的规格数字） ----------------
values = [
    ("对在校学生", "把课件、错题与计划收进同一课程空间；提问不再从零开始，复习按日推进，薄弱点可反复回看。"),
    ("对课程助教", "同一套演示模式可在无密钥环境复现全流程；逐日计划、错因分析与导出结果便于核对辅导效果。"),
    ("对课程验收", "功能、接口、验收判据与回归证据一一对应；未实现项在第 11 章单列，不做无法兑现的承诺。"),
]
v_cards = ""
for i, (k, v) in enumerate(values):
    v_cards += B(NUM("0" + str(i + 1))
                 + T(k, 24, BLUE, True, 1.3)
                 + T(v, 18, INK, False, 1.55, 14),
                 "width: 372, height: 272, background: '#F7F9FC', border: '1px solid #D6DCE5', "
                 "padding: 20, flexDirection: 'column'")
body09 = (
    B(T("价值不在于做一个更会聊天的机器人，而在于让智能体贴着课程与复习流程发挥作用。",
        20, INK, False, 1.4), "width: 1160, height: 40, flexDirection: 'column'")
    + B(B(v_cards, "width: 1160, height: 272, flexDirection: 'row', "
          "justifyContent: 'space-between', gap: 12"), "width: 1160, marginTop: 14")
    + B(BAR("价值边界：以上是 V1.5.0 已实现能力带来的用途；长文档记忆、多用户等仍属未来期望（见 P05 愿景）。", 48),
        "width: 1160, marginTop: 14")
    + B(T("价值结论：轻量化、易部署、可逐条验收，比功能数量更适合作为课程作业的选题落点。",
          18, INK, True, 1.4), "width: 1160, height: 34, flexDirection: 'column', marginTop: 10"))
PAGES.append(CONTENT("选题价值 · 谁会用到它", "02 · Topic", 9, body09))

# ---------------- P10 项目规划与能力全景（按复习闭环重排，去掉与成果重复的双截图） ----------------
stages = [
    ("01 资料输入", [("课件总结", "F02 / F08"), ("课程记忆", "F06 / F33")]),
    ("02 理解与练习", [("习题引导辅导", "F05"), ("课程内智能问答", "F01")]),
    ("03 计划与执行", [("自动生成复习计划", "F04 / F12"), ("番茄专注计时", "F26")]),
    ("04 复盘与产出", [("AI 错题本闭环", "F09 – F11"), ("学习资源包", "F18 / F19")]),
]
stage_rows = ""
for i, (stage, caps2) in enumerate(stages):
    chips2 = ""
    for name, fa in caps2:
        chips2 += B(T(name, 18, INK, True, 1.3) + T(fa + "  已实现", 14, BLUE, False, 1.3, 4),
                    "width: 455, height: 64, background: '#F7F9FC', border: '1px solid #D6DCE5', "
                    "padding: 8, flexDirection: 'column'")
    stage_rows += B(T(stage, 21, BLUE, True, 1.3, width=210)
                    + B(chips2, "width: 930, flexDirection: 'row', justifyContent: 'space-between', gap: 14"),
                    "width: 1160, height: 76, flexDirection: 'row', alignItems: 'center', "
                    "borderBottom: '1px solid #E5E7EB'" + (", marginTop: 10" if i else ""))
body10 = (
    B(T("规划：一套浏览器可直接访问的 Web 应用，把「课程」作为一等核心对象，八项能力按复习闭环四阶段串起来。",
        20, INK, False, 1.4), "width: 1160, height: 44, flexDirection: 'column'")
    + B(B(stage_rows, "width: 1160, flexDirection: 'column'"),
        "width: 1160, marginTop: 10")
    + B(BAR("范围说明：ESP32 联动（F37）接口与固件齐备但未实机联调，标注「可选 · 未实机 · 不列入验收」。", 46),
        "width: 1160, marginTop: 12")
    + B(T("衔接：以上背景、依据与价值，最终落为可运行的能力；下一章逐页展示真实界面与实测成果。",
          18, INK, True, 1.4), "width: 1160, height: 34, flexDirection: 'column', marginTop: 10"))
PAGES.append(CONTENT("项目规划与能力全景", "02 · Topic", 10, body10))

# ================= 03 成果展示（压缩冗余 + 强化亮点与结论） =================
PAGES.append(SECTION("03", "成果展示", "已上线系统  ·  真实界面  ·  亮点与结论"))

# ---------------- P12 已上线成果总览（换成成果视角数字，避免与 P25 规格数字重复） ----------------
ach_url = B(
    T("已发布 · 可直接访问（V1.5.0 验收基线）", 17, "#CADCFC", False, 1.3)
    + T("ai-campus-companion.app.workbuddy.host", 27, WHITE, True, 1.3, 8)
    + T("?sharecode=CEUN7FBTFJ   ·   浏览器 / 手机直接打开，无需安装、无需密钥", 16, PALE, False, 1.3, 8),
    "width: 1160, height: 138, background: '#1E4FA8', padding: 20, flexDirection: 'column'")
ach_metrics = [
    ("V1.5.0", "当前上线与验收版本"), ("7", "页可演示的真实界面"),
    ("A01–A39", "条可判定验收"), ("4", "套回归全部通过"),
]
ach_grid = ""
for v, lab in ach_metrics:
    sz = 36 if len(v) > 4 else 44
    ach_grid += B(T(v, sz, BLUE, True, 1.0) + T(lab, 17, GRAY, False, 1.3, 4),
                  "width: 281, height: 118, background: '#F7F9FC', "
                  "border: '1px solid #D6DCE5', padding: 14, flexDirection: 'column'")
body12 = (
    B(ach_url, "width: 1160, flexDirection: 'column'")
    + B(T("成果定位：已上线、可演示、可复核的一套课程复习原型；下列数字为成果侧口径，规格数字见需求分析章节。",
          18, INK, False, 1.45), "width: 1160, height: 44, flexDirection: 'column', marginTop: 14")
    + B(B(ach_grid, "width: 1160, flexDirection: 'row', justifyContent: 'space-between', gap: 12"),
        "width: 1160, marginTop: 8")
    + B(BAR("版本 1.5.0  ·  app.js 47665 字节与本地一致  ·  active_provider = demo", 48),
        "width: 1160, marginTop: 14"))
PAGES.append(CONTENT("已上线成果总览", "03 · Achievements", 12, body12))

# ---------------- P13–P16 / P18–P20 真实界面（每页一图 + 文字说明，文字压缩） ----------------
def SHOWCASE(item, page, idx, total):
    left = B(
        B(IMG(item["img"], 640, 420),
          "width: 640, height: 420, background: '#F7F9FC', border: '1px solid #D6DCE5', "
          "borderRadius: 6, flexDirection: 'row', alignItems: 'center', justifyContent: 'center'")
        + T("真实运行界面截图  ·  非示意图、非 AI 生成图", 13, LIGHT, False, 1.3, 10),
        "width: 660, flexDirection: 'column'")
    pts = ""
    for k, v in item["points"]:
        pts += B(T("▪  " + k, 18, BLUE, True, 1.3) + T(v, 16, GRAY, False, 1.45, 4),
                 "width: 460, flexDirection: 'column', marginTop: 14")
    right = B(
        T(item["title"], 26, INK, True, 1.25)
        + B(T(item["fa"], 15, BLUE, True, 1.3),
            "width: 440, height: 34, background: '#E8EFF8', flexDirection: 'row', "
            "alignItems: 'center', padding: 10, marginTop: 12")
        + B(HL(item["hl"]), "width: 440, marginTop: 12, flexDirection: 'column'")
        + T(item["desc"], 17, INK, False, 1.55, 14)
        + B(pts, "width: 460, flexDirection: 'column'")
        + B(T("真实界面  %d / %d" % (idx, total), 13, WHITE, True, 1.3),
            "width: 190, height: 32, background: '#1E4FA8', borderRadius: 4, "
            "flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 16"),
        "width: 480, flexDirection: 'column'")
    body = B(left + right, "width: 1160, height: 497, flexDirection: 'row', gap: 20")
    return CONTENT("成果展示 · " + item["title"], "03 · Achievements", page, body)


showcase = [
    dict(img="ui_home.png", title="学习概览与专注统计",
         fa="F26 学习概览与番茄钟 · 验收 A29",
         hl="亮点：一屏按课程聚合，待复习任务置顶",
         desc="问答、总结、错题、复习与专注统计按课程一屏聚合，打开即可进入复习。",
         points=[("一屏可见", "六项统计与待复习卡片同屏，薄弱知识点优先展示。"),
                 ("键盘可达", "统计卡片支持 Tab / Enter / Space 与焦点样式（F29）。")]),
    dict(img="ui_chat.png", title="课程内智能问答",
         fa="F01 问答 · F06 记忆绑定 · 验收 A05 – A06",
         hl="亮点：切换课程即切换记忆，不再从零交代",
         desc="每次提问自动携带当前课程资料上下文；回答按 escape-first 富文本渲染。",
         points=[("上下文可见", "资料全文拼入 system prompt；单份 4000 字、总量 12000 字预算（F33）。"),
                 ("交互可靠", "安全 Markdown 防注入（F27 / F31），请求中按钮禁用防重复提交（F28）。")]),
    dict(img="ui_summarize.png", title="课件总结",
         fa="F02 课件总结 · F08 文件解析 · 验收 A07 / A12",
         hl="亮点：上传即入课程记忆，结果可下载归档",
         desc="粘贴或上传课件文本，一键输出知识点与考点提纲，结果可下载 .md 归档。",
         points=[("多格式上传", "txt / md / docx 上传即入课程记忆，docx 实体全还原（F36）。"),
                 ("演示可复现", "结构化输出分层呈现，演示模式即可完整跑通。")]),
    dict(img="ui_plan.png", title="复习计划",
         fa="F04 复习计划 · F12 到点提醒 · 验收 A09 / A15",
         hl="亮点：逐日安排由后台调度自动提醒",
         desc="按科目与剩余天数生成逐日安排：基础回顾 → 重点突破 → 真题演练 → 冲刺。",
         points=[("逐日计划", "每日 2–3 小时粒度，配合错题本安排复盘。"),
                 ("到点提醒", "后台线程每 30 秒扫描到期复习任务（F12），演示模式可跑通。")]),
    dict(img="ui_study_pack.png", title="学习资源包",
         fa="F18 一键全套与导出 · 验收 A21",
         hl="亮点：一次生成六类产出，可回写课程记忆",
         desc="一次生成自测题、复习总结、专题文章、资料清单、思维导图与错题关联。",
         points=[("一键全套", "六类产出一次生成，结果可回写课程记忆。"),
                 ("导出健壮", "blob 下载失败不替换整页；资料链接协议白名单（F35 / F36）。")]),
    dict(img="ui_wrong.png", title="AI 错题本",
         fa="F09 – F11 错题闭环 · 验收 A13 – A14",
         hl="亮点：录入到导出，形成完整闭环",
         desc="录入 → 错因分析 → 同类变式题 → 掌握标记 → 导出，串起复习最后一环。",
         points=[("录入与筛选", "题干 / 我的答案 / 正确答案三段录入，按掌握状态筛选。"),
                 ("错因与变式", "分析错因并生成同类变式题（F10），一键导出 Markdown（F11）。")]),
    dict(img="ui_model_settings.png", title="模型接入与运行时配置",
         fa="F20 – F23 智能体接入 · 验收 A23 – A26",
         hl="亮点：6 个 Provider 热切换，无密钥自动回退",
         desc="OpenAI / 文心一言 / Kimi / Claude / 自定义 / 演示模式，统一由工厂注册。",
         points=[("运行时配置", "Web 或 REST 写入密钥与模型地址，即时生效无需重启（F21）。"),
                 ("连通性自检", "配置校验与真实探针（F22）；异常时回退演示模式并带 fallback 标记（F23）。")]),
]
SHOWCASE_PAGES = [13, 14, 15, 16, 18, 19, 20]
showcase_iter = iter(SHOWCASE_PAGES)

# 第一组：P13 – P16
for si, item in enumerate(showcase[:4]):
    PAGES.append(SHOWCASE(item, next(showcase_iter), si + 1, len(showcase)))

# ---------------- P17 成果亮点（新增；节奏断点，把 7 连页拆成 4 + 3） ----------------
highlights = [
    ("课程记忆按课程隔离", "F06 / F33",
     "资料全文进入 prompt，切换课程即切换上下文；单份 4000 字、总量 12000 字预算，避免长资料挤占窗口。",
     "证据：study_check.py 本地 36/36"),
    ("安全 Markdown 渲染", "F27 / F31",
     "前端 escape-first 先转义再解析富文本，资料与回答中的标签不会被执行；三轮自查中完成 XSS 复测。",
     "证据：自我检查报告 12 节"),
    ("可插拔智能体与自动回退", "F20 – F23",
     "AgentProvider 抽象 + 工厂注册 6 个实现；未配置密钥或调用异常时降级演示模式，离线也能走通全流程。",
     "证据：demo_check.py 30/30"),
]
h_cards = ""
for i, (k, fa, desc, ev) in enumerate(highlights):
    h_cards += B(NUM("0" + str(i + 1))
                 + T(k, 23, BLUE, True, 1.3)
                 + B(T(fa, 15, WHITE, True, 1.3),
                     "width: 200, height: 30, background: '#1E4FA8', flexDirection: 'row', "
                     "alignItems: 'center', justifyContent: 'center', marginTop: 12")
                 + T(desc, 17, INK, False, 1.55, 14)
                 + T(ev, 16, GRAY, True, 1.4, 12),
                 "width: 372, height: 328, background: '#F7F9FC', border: '1px solid #D6DCE5', "
                 "padding: 18, flexDirection: 'column'")
body17 = (
    B(T("把前面四个界面与后面三个界面串起来的，是这三项可验证的实现要点。",
        20, INK, False, 1.4), "width: 1160, height: 40, flexDirection: 'column'")
    + B(B(h_cards, "width: 1160, height: 328, flexDirection: 'row', "
          "justifyContent: 'space-between', gap: 12"), "width: 1160, marginTop: 12")
    + B(BAR("亮点不写成口号：每一项都给出需求编号与可复核证据，答辩现场可现场验证。", 46),
        "width: 1160, marginTop: 12"))
PAGES.append(CONTENT("成果亮点 · 三个可验证的技术点", "03 · Achievements", 17, body17))

# 第二组：P18 – P20
for si, item in enumerate(showcase[4:], start=4):
    PAGES.append(SHOWCASE(item, next(showcase_iter), si + 1, len(showcase)))

# ---------------- P21 成果结论 · 交付物与可复核证据（合并原 P21，删与 P26 重复的回归数字） ----------------
ach_dlv = [
    ("需求规格说明书", "GB/T 9385 口径；.md 单一源 + .docx 验收主件"),
    ("答辩演示文稿", "四章 28 页，全部配图取自项目真实资产"),
    ("博客园复盘长文", "13 节 + 13 张图，已同步 V1.5.0 口径"),
    ("四套回归与证据", "startup / demo / feature / study + 本地与线上 JSON"),
    ("自查与说明文档", "自我检查报告 12 节、README 与架构 / 思维导图 / 类图"),
]
ach_rows = ""
for i, (k, v) in enumerate(ach_dlv):
    ach_rows += B(
        T(k, 19, BLUE, True, 1.3, width=200) + T(v, 17, GRAY, False, 1.35, width=470),
        "width: 700, height: 58, flexDirection: 'row', alignItems: 'center', gap: 10"
        + (", borderBottom: '1px solid #E5E7EB'" if i < 4 else ""))
concl = B(
    T("三条结论", 26, WHITE, True, 1.3)
    + T("① 已上线：浏览器直接访问，无需安装与密钥。", 17, WHITE, False, 1.5, 14)
    + T("② 可复核：四套回归结果与 A01 – A39 逐条对应。", 17, WHITE, False, 1.5, 8)
    + T("③ 有边界：无真实厂商 Key、ESP32 未实机、团队合照待补。", 17, WHITE, False, 1.5, 8)
    + T("边界项一律排除在验收范围外，详见第 04 章。", 15, "#CADCFC", False, 1.4, 16),
    "width: 420, height: 300, background: '#1E4FA8', padding: 20, flexDirection: 'column'")
body21 = (
    B(T("交付物与可复核证据", 22, BLUE, True, 1.4),
      "width: 1160, height: 40, flexDirection: 'column'")
    + B(B(ach_rows, "width: 700, height: 300, flexDirection: 'column'") + concl,
        "width: 1160, height: 300, flexDirection: 'row', "
        "justifyContent: 'space-between', gap: 20, marginTop: 8")
    + B(BAR("复核路径：docs/*_results.json、需求文档 10.5 节；答辩现场可打开线上链接逐项走查。", 46),
        "width: 1160, marginTop: 12")
    + B(B(T("章节结论：V1.5.0 是一套可运行、可演示、可逐条验收的课程复习原型；下一章按国标口径给出需求与验收依据。",
            18, WHITE, True, 1.45),
          "width: 1160, height: 52, background: '#1E4FA8', flexDirection: 'row', "
          "alignItems: 'center', padding: 16"), "width: 1160, marginTop: 10"))
PAGES.append(CONTENT("成果结论 · 交付物与可复核证据", "03 · Achievements", 21, body21))

# ================= 04 需求分析（结构与页码不变，做去重与表述一致性微调） =================
PAGES.append(SECTION("04", "需求分析", "国标依据  ·  前后端详述  ·  可判定验收"))

# ---------------- P23 依据、迭代记录、项目标志 ----------------
basis = CARD(
    T("编写依据", 24, BLUE, True, 1.3)
    + T("GB/T 9385-2008《计算机软件需求说明编制指南》", 18, INK, False, 1.45, 14)
    + T("GB/T 8567-2006《计算机软件文档编制规范》", 18, INK, False, 1.45, 8)
    + RULE(320)
    + T("协作方式", 22, BLUE, True, 1.3, 14)
    + T("Markdown 单一内容源，可直接导入语雀 / 腾讯文档；同名 docx 由 build_docx.py 生成。",
        17, GRAY, False, 1.5, 8),
    340, 340)
iters = [
    ("V1.2.1", "2026-11-06", "启动修复：版本指纹与端口自动顺延"),
    ("V1.3.0", "2026-11-06", "架构收敛：移除 Flask，仅保留 server.py"),
    ("V1.4.0", "2026-11-06", "安全 Markdown、忙碌态、概览空态优化"),
    ("V1.4.1", "2026-11-06", "课程资料「上传后打不开」修复"),
    ("V1.5.0", "2026-11-06", "当前验收基线：第三轮自查 11 项修复"),
]
itable = B(T("版本", 17, BLUE, True, 1.2, width=110)
           + T("日期", 17, BLUE, True, 1.2, width=130)
           + T("阶段 / 迭代内容", 17, BLUE, True, 1.2, width=480),
           "width: 780, height: 44, flexDirection: 'row', alignItems: 'center', background: '#E8EFF8', padding: 10")
for v, d, c in iters:
    hot = v == "V1.5.0"
    itable += B(T(v, 17, BLUE if hot else INK, hot, 1.3, width=110)
                + T(d, 16, GRAY, False, 1.3, width=130)
                + T(c, 17, INK, hot, 1.3, width=480),
                "width: 780, height: 50, flexDirection: 'row', alignItems: 'center', "
                "padding: 10, borderBottom: '1px solid #E5E7EB'")
body23 = (
    B(B(basis, "width: 350, flexDirection: 'column'")
      + B(itable, "width: 790, flexDirection: 'column'"),
      "width: 1160, height: 356, flexDirection: 'row', justifyContent: 'space-between', gap: 20")
    + B(B(IMG("logo.png", 260, 89), "width: 280, flexDirection: 'column'")
        + B(T("项目标志与标识", 22, BLUE, True, 1.3)
            + T("ACC · AI Campus Learning Companion  ｜  版本 1.5.0  ｜  验收基线", 18, INK, False, 1.4, 8)
            + T("线上入口：ai-campus-companion.app.workbuddy.host", 16, GRAY, False, 1.4, 6),
            "width: 840, flexDirection: 'column'"),
        "width: 1160, height: 110, flexDirection: 'row', alignItems: 'center', "
        "background: '#F7F9FC', padding: 14, marginTop: 16"))
PAGES.append(CONTENT("依据、迭代记录与项目标志", "04 · Requirements", 23, body23))

# ---------------- P24 思维导图与类图 ----------------
body24 = (
    B(B(IMG("mindmap.png", 550, 380)
        + T("图 2  功能思维导图：六大分支覆盖第 4 章全部功能需求", 15, GRAY, False, 1.3, 10),
        "width: 560, flexDirection: 'column'")
      + B(IMG("classdiagram.png", 550, 400)
          + T("图 3  类图：Provider 抽象 / 8 服务模块 / 8 张表 / 10 前端模块", 15, GRAY, False, 1.3, 10),
          "width: 560, flexDirection: 'column'"),
      "width: 1160, height: 440, flexDirection: 'row', justifyContent: 'space-between', gap: 20")
    + B(BAR("两张图均由仓库 docs/*.svg 矢量源渲染，与需求文档图 3、图 4 一一对应；系统架构图见 P08。", 46),
        "width: 1160, marginTop: 10"))
PAGES.append(CONTENT("思维导图与类图", "04 · Requirements", 24, body24))

# ---------------- P25 功能描述与前后端详述 ----------------
kpis = ""
for val, label in [("37", "项功能 F01–F37"), ("40", "条 REST 路由"), ("8", "张 SQLite 表")]:
    kpis += B(T(val, 68, BLUE, True, 1.0) + T(label, 19, GRAY, False, 1.3, 4),
              "width: 370, height: 110, flexDirection: 'column', alignItems: 'center'")
fe = (T("前端 · 10 个模块", 23, BLUE, True, 1.3)
      + T("概览、问答、课程记忆、错题本、学习资源包、专注、设置、硬件等；"
          "api() 响应归一化、init() 容错、courseLoadSeq 竞态防护、escape-first Markdown 渲染。",
          18, INK, False, 1.5, 10))
be = (T("后端 · 8 个服务模块", 23, BLUE, True, 1.3)
      + T("server.py 按 ROUTES 正则分发；6 个 Provider 可插拔；课程记忆单份 4000 字、"
          "总预算 12000 字；30 秒调度扫描复习任务。",
          18, INK, False, 1.5, 10))
body25 = (
    B(B(kpis, "width: 1160, height: 112, flexDirection: 'row', justifyContent: 'space-between'"),
      "width: 1160")
    + B(B(B(fe, "width: 350, flexDirection: 'column'") + B(be, "width: 350, flexDirection: 'column'"),
          "width: 720, height: 290, flexDirection: 'row', justifyContent: 'space-between', gap: 16")
        + B(IMG("ui_chat.png", 400, 256)
            + T("课程内智能问答 · 真实界面", 13, LIGHT, False, 1.3, 6),
          "width: 410, flexDirection: 'column'"),
        "width: 1160, height: 290, flexDirection: 'row', justifyContent: 'space-between', gap: 20, marginTop: 12")
    + B(BAR("每项功能都能在代码、接口表与测试报告中逐条追溯；此处为规格口径，成果口径见 P12。", 46),
        "width: 1160, marginTop: 10"))
PAGES.append(CONTENT("功能描述与前后端详述", "04 · Requirements", 25, body25))

# ---------------- P26 验收标准与实测结果 ----------------
criteria = (T("验收标准 A01 – A39", 24, BLUE, True, 1.3)
            + T("每条含可判定条件与复现方式；四条通过判据同时满足方可判定 V1.5.0 通过。",
                19, INK, False, 1.5, 10)
            + T("版本指纹 1.5.0、四套回归全绿、静态 app.js 与本地字节级一致（47665 字节）、"
                "课程记忆隔离与导出结果可复核。", 18, GRAY, False, 1.5, 12))
reg = [
    ("回归脚本", "本地", "线上"),
    ("startup_check.py", "26/26", "26/26"),
    ("demo_check.py", "26/26 + 30/30", "26/26 + 30/30"),
    ("feature_check.py", "19/19", "19/19"),
    ("study_check.py", "36/36", "25/25"),
]
rtable = ""
for i, (a, b, c) in enumerate(reg):
    head = i == 0
    rtable += B(T(a, 17, BLUE if head else INK, head, 1.3, width=340)
                + T(b, 17, INK, head, 1.3, width=250)
                + T(c, 17, RED if (i == 4) else INK, head or i == 4, 1.3, width=200),
                "width: 800, height: 38, flexDirection: 'row', alignItems: 'center', padding: 8"
                + (", background: '#E8EFF8'" if head else ", borderBottom: '1px solid #E5E7EB'"))
body26 = (
    B(B(criteria, "width: 700, flexDirection: 'column'")
      + B(T("36/36", 64, BLUE, True, 1.0)
          + T("本地 study_check 全量断言", 17, GRAY, False, 1.3, 4)
          + T("25/25", 44, RED, True, 1.0, 16)
          + T("线上跳过 11 项需模拟端点的探针", 16, GRAY, False, 1.3, 2),
          "width: 420, height: 230, flexDirection: 'column', alignItems: 'center', "
          "justifyContent: 'center', background: '#F7F9FC'"),
      "width: 1160, height: 230, flexDirection: 'row', justifyContent: 'space-between', gap: 20")
    + B(rtable, "width: 1160, height: 200, flexDirection: 'column', marginTop: 14")
    + B(BAR("线上 25/25 不是漏测：11 项需本机临时模拟厂商端点，已在本地 36/36 中完整验证。", 46),
        "width: 1160, marginTop: 8"))
PAGES.append(CONTENT("验收标准与实测结果", "04 · Requirements", 26, body26))

# ---------------- P27 范围边界与不予承诺 ----------------
bounds = [
    "真实厂商 API Key 缺失，仅用本机模拟端点验证",
    "DemoProvider 为规则化应答，不是大模型推理",
    "课程记忆为全文拼接，非 RAG / 向量检索",
    "仅高等数学上册为完整 7 章结构化数据",
    "ESP32 未实机联调，不承诺物理声光效果",
    "课程资料无删除入口，后端无 DELETE 路由",
    "/api/agent/* 公网配置接口未加鉴权",
    "无登录与权限，按单机单用户原型说明",
    "部署整目录上传会覆盖线上 SQLite 数据",
    "GitHub 远端可能落后于本地与线上",
    "语音输入依赖浏览器 Web Speech API",
]
left_items = ""
for i, s in enumerate(bounds[:6]):
    left_items += B(T("· " + s, 17, INK, False, 1.4),
                    "width: 360, flexDirection: 'column'" + (", marginTop: 12" if i else ""))
right_items = ""
for i, s in enumerate(bounds[6:]):
    right_items += B(T("· " + s, 17, INK, False, 1.4),
                     "width: 360, flexDirection: 'column'" + (", marginTop: 12" if i else ""))
body27 = (
    B(T("以下 11 项明确排除在验收范围外，答辩不得宣称已完成", 22, BLUE, True, 1.4),
      "width: 1160, height: 44, flexDirection: 'column'")
    + B(B(left_items, "width: 370, height: 350, flexDirection: 'column'")
        + B(right_items, "width: 370, height: 350, flexDirection: 'column'")
        + B(T("不画大饼", 30, WHITE, True, 1.3)
            + T("需求文档第 11 章逐项列出现状与影响；"
                "F37 硬件联动标注「可选 · 未实机 · 不列入验收」。",
                19, WHITE, False, 1.5, 14)
            + T("未实现、未实测、依赖外部条件的能力，一律不作为验收项。",
                17, "#CADCFC", False, 1.5, 16),
            "width: 380, height: 300, background: '#1E4FA8', padding: 20, flexDirection: 'column'"),
        "width: 1160, height: 360, flexDirection: 'row', justifyContent: 'space-between', "
        "gap: 12, marginTop: 12")
    + B(BAR("诚实报告局限，比藏着更专业；这一页本身就是「不画大饼」的证明。", 46),
        "width: 1160, marginTop: 10"))
PAGES.append(CONTENT("范围边界与不予承诺", "04 · Requirements", 27, body27))

# ---------------- P28 封底 ----------------
PAGES.append(
    "<Slide padding={60} style={{ background: '#1E4FA8', fontFamily: 'Microsoft YaHei', "
    "flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>"
    + T("谢谢，请指正", 60, WHITE, True, 1.2)
    + T("无言以对队   ·   AI 校园学习陪伴助手   ·   V1.5.0", 22, PALE, False, 1.4, 30)
    + T("ai-campus-companion.app.workbuddy.host", 17, "#CADCFC", False, 1.4, 14)
    + "</Slide>")

assert len(PAGES) == 28, len(PAGES)
for i, s in enumerate(PAGES, 1):
    assert s.lstrip().startswith("<Slide"), i
    assert s.rstrip().endswith("</Slide>"), i
    with open(os.path.join(OUT, "%02d.slide" % i), "w", encoding="utf-8") as f:
        f.write(s)
print("已生成 %d 个页面源文件 -> %s" % (len(PAGES), OUT))
