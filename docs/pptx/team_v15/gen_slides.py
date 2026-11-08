# -*- coding: utf-8 -*-
"""生成 18 页 .slide 源文件。

内容取自用户本次提供的真实团队资料与 docs/软件需求规格说明书.md（V1.5.0 验收基线）。
配图全部为项目真实资产（docs/svg_fallback、docs/blog/assets），无 AI 生图、无编造数据。
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
        + T("%02d / 18" % num, 14, LIGHT, False, 1.3),
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


PAGES = []

# ---------------- P01 封面 ----------------
chips = ""
for n, label in [("01", "团队展示"), ("02", "选题报告"), ("03", "需求分析")]:
    chips += B(T(n, 38, "#CADCFC", True, 1.0) + T(label, 22, WHITE, False, 1.3),
               "width: 310, height: 96, flexDirection: 'row', alignItems: 'center', gap: 22, "
               "padding: 20, background: '#2E5FBB'")
PAGES.append(
    "<Slide padding={60} style={{ background: '#1E4FA8', fontFamily: 'Microsoft YaHei', "
    "flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>"
    + B(T("智能体开发课程作业  ·  V1.5.0 验收基线", 18, "#CADCFC", False, 1.4)
        + T("AI 校园学习<br />陪伴助手", 64, WHITE, True, 1.18, 30)
        + T("团队展示  ·  选题报告  ·  需求分析", 26, PALE, False, 1.4, 26)
        + T("无言以对队   ｜   陈明凯 · 邓文炜   ｜   2026-11", 16, "#CADCFC", False, 1.4, 62),
        "width: 720, flexDirection: 'column', justifyContent: 'center'")
    + B(chips, "width: 310, flexDirection: 'column', gap: 16")
    + "</Slide>")

# ---------------- P02 目录 ----------------
rows = ""
for idx, (n, name, pg, en) in enumerate([
        ("01", "团队展示", "P03 – P07", "Team"),
        ("02", "选题报告", "P08 – P11", "Topic"),
        ("03", "需求分析", "P12 – P17", "Requirements")]):
    rows += B(
        B(T(n, 34, WHITE, True, 1.0, align="center"),
          "width: 66, height: 66, background: '#1E4FA8', flexDirection: 'row', "
          "alignItems: 'center', justifyContent: 'center'")
        + B(T(name + "   " + en, 32, INK, True, 1.2) + T(pg, 16, LIGHT, False, 1.3, 6),
            "flexDirection: 'column', marginLeft: 28")
        + B(T(pg, 18, GRAY, False, 1.3),
            "marginLeft: 'auto', flexDirection: 'row', alignItems: 'center'"),
        "width: 1160, height: 108, flexDirection: 'row', alignItems: 'center'")
    if idx < 2:
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

# ---------------- P03 章节 01 ----------------
PAGES.append(SECTION("01", "团队展示", "2 人小队  ·  后端与测试 / 前端双线分工"))

# ---------------- P04 队名与团队构成 ----------------
mem1 = CARD(
    T("陈明凯", 30, INK, True, 1.2) + T("3124004503", 17, LIGHT, False, 1.3, 4)
    + T("后端开发 · 测试工程师", 20, BLUE, True, 1.4, 14)
    + T("架构设计、server.py、agents 抽象层、四套回归脚本、三轮自查修复、项目文档", 18, GRAY, False, 1.45, 10),
    560, 220)
mem2 = CARD(
    T("邓文炜", 30, INK, True, 1.2) + T("3124004505", 17, LIGHT, False, 1.3, 4)
    + T("前端开发", 20, BLUE, True, 1.4, 14)
    + T("全部前端页面、10 个导航模块、安全 Markdown 渲染器、忙碌态交互、资料查看与下载、XSS 前端验证", 18, GRAY, False, 1.45, 10),
    560, 220)
body04 = (
    B(T("队名", 16, LIGHT, False, 1.3) + T("无言以对", 62, BLUE, True, 1.15, 4)
      + T("2 人小队，覆盖架构、后端、前端、测试与文档全链路", 20, GRAY, False, 1.4, 8),
      "width: 1160, height: 150, flexDirection: 'column'")
    + B(mem1 + mem2, "width: 1160, height: 220, flexDirection: 'row', justifyContent: 'space-between', marginTop: 16")
    + B(BAR("分工不重叠：后端与质量保障 / 前端与交互体验；项目按课程作业原型推进", 50),
        "width: 1160, marginTop: 20"))
PAGES.append(CONTENT("队名与团队构成", "01 · Team", 4, body04))


# ---------------- P05 / P06 队员风采 ----------------
def MEMBER(num, name, sid, role, traits, skills, hobbies, duty, img, img_h, chapter, page):
    left = (
        B(NUM(num) + T(name, 36, INK, True, 1.2, 14),
          "width: 300, height: 90, flexDirection: 'row', alignItems: 'center', gap: 14")
        + T("学号  " + sid, 18, GRAY, False, 1.4, 8)
        + B(T(role, 19, BLUE, True, 1.3),
            "width: 300, height: 40, background: '#E8EFF8', flexDirection: 'row', "
            "alignItems: 'center', padding: 12, marginTop: 14")
        + B(IMG(img, 280, img_h), "width: 300, marginTop: 18, flexDirection: 'column'"))
    fields = [
        ("成员性格", traits),
        ("擅长的技术", skills),
        ("兴趣爱好", hobbies),
        ("主要负责", duty),
    ]
    right = ""
    for i, (k, v) in enumerate(fields):
        right += B(T(k, 22, BLUE, True, 1.3) + T(v, 19, INK, False, 1.45, 6),
                   "width: 800, flexDirection: 'column'" + (", marginTop: 14" if i else ""))
    body = B(B(left, "width: 320, flexDirection: 'column'")
             + B(right, "width: 810, height: 480, flexDirection: 'column', "
                 "borderLeft: '1px solid #D6DCE5', padding: 24"),
             "width: 1160, height: 497, flexDirection: 'row', gap: 16")
    return CONTENT("队员风采 · " + name, chapter, page, body)


PAGES.append(MEMBER(
    "01", "陈明凯", "3124004503", "后端开发 · 测试工程师",
    "严谨细致，善于复盘问题；遇到 bug 喜欢完整复现根因，做事踏实，注重工程质量。",
    "Python 后端开发、标准库 HTTP 服务、SQLite 数据库、接口设计、自动化测试脚本编写。",
    "阅读技术博客、调试开源项目、整理项目文档。",
    "系统整体架构设计、server.py 后端、agents 智能体抽象层、四套回归测试脚本、三轮自查漏洞修复、项目文档撰写。",
    "ui_model_settings.png", 230, "01 · Team", 5))

PAGES.append(MEMBER(
    "02", "邓文炜", "3124004505", "前端开发",
    "想法活跃，重视用户体验；耐心打磨交互细节，善于发现界面隐性问题。",
    "原生 HTML/CSS/JS、Markdown 渲染、页面状态管理、前端故障排查。",
    "UI 交互设计、截图做原型、研究 Web 安全前端风险。",
    "全部前端页面、10 个导航模块实现、安全 Markdown 渲染器、忙碌态交互、资料查看 / 下载功能、XSS 前端验证、页面截图素材输出。",
    "ui_summarize.png", 197, "01 · Team", 6))

# ---------------- P07 合照 + 愿景 ----------------
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
body07 = B(
    B(frame + T("图：团队首次合照占位，拿到照片后替换本页相框", 14, LIGHT, False, 1.3, 10),
      "width: 640, flexDirection: 'column'")
    + B(T("团队项目愿景", 28, BLUE, True, 1.3)
        + T("未来期望 · 非 V1.5.0 已实现能力", 14, LIGHT, False, 1.3, 2)
        + T(vision, 20, INK, False, 1.6, 20)
        + B(T("不做泛化闲聊  ·  形成复习闭环", 20, WHITE, True, 1.4),
            "width: 470, height: 52, background: '#1E4FA8', flexDirection: 'row', "
            "alignItems: 'center', padding: 14, marginTop: 24"),
        "width: 480, flexDirection: 'column'"),
    "width: 1160, height: 497, flexDirection: 'row', gap: 24")
PAGES.append(CONTENT("首次合照与项目愿景", "01 · Team", 7, body07))

# ---------------- P08 章节 02 ----------------
PAGES.append(SECTION("02", "选题报告", "真实备考痛点  ·  能力全景  ·  零依赖架构"))

# ---------------- P09 选题背景 ----------------
pains = [
    ("课程上下文缺失", "通用大模型聊天工具不区分课程，每次提问都要从零交代背景。"),
    ("资料难以沉淀", "课件、错题散落在各处，无法形成可复用的复习上下文。"),
    ("复习缺少闭环", "复习计划靠手工安排，错题录入、诊断、变式、掌握之间没有串起来。"),
]
pain_rows = ""
for i, (k, v) in enumerate(pains):
    pain_rows += B(NUM("0" + str(i + 1)) + B(T(k, 22, INK, True, 1.3) + T(v, 19, GRAY, False, 1.45, 6),
                                            "flexDirection: 'column', marginLeft: 14"),
                   "width: 700, height: 108, flexDirection: 'row', alignItems: 'flex-start'"
                   + (", marginTop: 12" if i else ""))
body09 = (
    B(B(T("核心问题：能否把「课程」作为一等对象，让智能体在真实备考流程中持续可用？", 21, WHITE, True, 1.4),
        "width: 1160, height: 62, background: '#1E4FA8', flexDirection: 'row', "
        "alignItems: 'center', padding: 18"), "width: 1160")
    + B(B(pain_rows, "width: 700, flexDirection: 'column'")
        + B(IMG("ui_home.png", 400, 281)
            + T("图：V1.5.0 首页概览（真实页面截图）", 14, LIGHT, False, 1.3, 8),
            "width: 420, flexDirection: 'column'"),
        "width: 1160, height: 340, flexDirection: 'row', justifyContent: 'space-between', marginTop: 20")
    + B(BAR("三条痛点共同指向一件事：学习上下文必须按课程被系统记住，而不是靠用户反复输入。", 48),
        "width: 1160, marginTop: 14"))
PAGES.append(CONTENT("选题背景与核心问题", "02 · Topic", 9, body09))

# ---------------- P10 项目规划与能力全景 ----------------
caps = [
    ("课件总结", False), ("习题引导辅导", False), ("自动生成复习计划", False),
    ("课程记忆上下文隔离", False), ("AI 错题本闭环", False), ("学习资源包生成", False),
    ("番茄专注计时", False), ("ESP32 联动", True),
]
grid = ""
for i, (name, warn) in enumerate(caps):
    c = RED if warn else BLUE
    sub = "可选 · 未实机 · 不列入验收" if warn else "已实现并可复现"
    grid += B(T("0" + str(i + 1) + "  " + name, 20, INK, True, 1.3)
              + T(sub, 15, c, False, 1.3, 8),
              "width: 281, height: 100, background: '#F7F9FC', border: '1px solid #D6DCE5', "
              "padding: 14, flexDirection: 'column'")
body10 = (
    B(T("一套浏览器可直接访问的 Web 应用；区别于通用聊天工具，把「课程」作为一等核心对象。",
        20, INK, False, 1.4), "width: 1160, height: 40, flexDirection: 'column'")
    + B(B(grid, "width: 1160, height: 208, flexDirection: 'row', flexWrap: 'wrap', gap: 12"),
        "width: 1160, marginTop: 14")
    + B(B(IMG("ui_study_pack.png", 300, 211), "width: 310, flexDirection: 'column'")
        + B(IMG("ui_wrong.png", 300, 211), "width: 310, flexDirection: 'column'")
        + B(T("八项能力对应真实页面与接口", 24, BLUE, True, 1.3)
            + T("课件总结、习题辅导、复习计划、课程记忆、错题闭环、资源包、番茄钟均由 REST 接口驱动；"
                "ESP32 联动接口与固件齐备但未实机联调，按需求文档第 11 章不列入验收。",
                19, GRAY, False, 1.5, 12),
            "width: 500, flexDirection: 'column'"),
        "width: 1160, height: 220, flexDirection: 'row', justifyContent: 'space-between', marginTop: 12"))
PAGES.append(CONTENT("项目规划与能力全景", "02 · Topic", 10, body10))

# ---------------- P11 技术选型与系统架构 ----------------
choices = [
    ("零依赖后端", "Python 标准库 ThreadingHTTPServer 实现单一 server.py；V1.3.0 起移除 Flask。"),
    ("原生前端", "HTML / CSS / JS 无构建工具，10 个导航模块由 app.js 直接驱动。"),
    ("数据与调度", "SQLite 8 张表；后台守护线程每 30 秒扫描到期复习任务。"),
    ("可插拔智能体", "6 个 Provider；无密钥时自动降级 DemoProvider，离线跑通全流程。"),
]
ch_rows = ""
for i, (k, v) in enumerate(choices):
    ch_rows += B(T(k, 22, BLUE, True, 1.3) + T(v, 18, GRAY, False, 1.45, 6),
                 "width: 460, flexDirection: 'column'" + (", marginTop: 14" if i else ""))
body11 = (
    B(B(IMG("architecture.png", 660, 336), "width: 670, flexDirection: 'column'")
      + B(ch_rows, "width: 470, flexDirection: 'column', padding: 10"),
      "width: 1160, height: 400, flexDirection: 'row', justifyContent: 'space-between', gap: 20")
    + B(T("图 2  V1.5.0 系统架构（单一零依赖后端）", 14, LIGHT, False, 1.3),
        "width: 1160, height: 24, flexDirection: 'column', marginTop: 4")
    + B(BAR("一条 python server.py 即可启动，适配答辩机房与离线演示场景。", 50),
        "width: 1160, marginTop: 12"))
PAGES.append(CONTENT("技术选型与系统架构", "02 · Topic", 11, body11))

# ---------------- P12 章节 03 ----------------
PAGES.append(SECTION("03", "需求分析", "国标依据  ·  前后端详述  ·  可判定验收"))

# ---------------- P13 依据、迭代记录、项目标志 ----------------
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
for i, (v, d, c) in enumerate(iters):
    hot = v == "V1.5.0"
    itable += B(T(v, 17, BLUE if hot else INK, hot, 1.3, width=110)
                + T(d, 16, GRAY, False, 1.3, width=130)
                + T(c, 17, INK, hot, 1.3, width=480),
                "width: 780, height: 50, flexDirection: 'row', alignItems: 'center', "
                "padding: 10, borderBottom: '1px solid #E5E7EB'")
body13 = (
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
PAGES.append(CONTENT("依据、迭代记录与项目标志", "03 · Requirements", 13, body13))

# ---------------- P14 思维导图与类图 ----------------
body14 = (
    B(B(IMG("mindmap.png", 550, 380)
        + T("图 3  功能思维导图：六大分支覆盖第 4 章全部功能需求", 15, GRAY, False, 1.3, 10),
        "width: 560, flexDirection: 'column'")
      + B(IMG("classdiagram.png", 550, 400)
          + T("图 4  类图：Provider 抽象 / 8 服务模块 / 8 张表 / 10 前端模块", 15, GRAY, False, 1.3, 10),
          "width: 560, flexDirection: 'column'"),
      "width: 1160, height: 440, flexDirection: 'row', justifyContent: 'space-between', gap: 20")
    + B(BAR("两张图均由仓库 docs/*.svg 矢量源渲染，与需求文档图 3、图 4 一一对应。", 46),
        "width: 1160, marginTop: 10"))
PAGES.append(CONTENT("思维导图与类图", "03 · Requirements", 14, body14))

# ---------------- P15 功能描述与前后端详述 ----------------
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
body15 = (
    B(B(kpis, "width: 1160, height: 112, flexDirection: 'row', justifyContent: 'space-between'"),
      "width: 1160")
    + B(B(B(fe, "width: 350, flexDirection: 'column'") + B(be, "width: 350, flexDirection: 'column'"),
          "width: 720, height: 290, flexDirection: 'row', justifyContent: 'space-between', gap: 16")
        + B(IMG("ui_chat.png", 400, 281), "width: 410, flexDirection: 'column'"),
        "width: 1160, height: 290, flexDirection: 'row', justifyContent: 'space-between', gap: 20, marginTop: 12")
    + B(BAR("每项功能都能在代码、接口表与测试报告中逐条追溯。", 46), "width: 1160, marginTop: 10"))
PAGES.append(CONTENT("功能描述与前后端详述", "03 · Requirements", 15, body15))

# ---------------- P16 验收标准与实测结果 ----------------
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
body16 = (
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
PAGES.append(CONTENT("验收标准与实测结果", "03 · Requirements", 16, body16))

# ---------------- P17 范围边界与不予承诺 ----------------
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
body17 = (
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
PAGES.append(CONTENT("范围边界与不予承诺", "03 · Requirements", 17, body17))

# ---------------- P18 封底 ----------------
PAGES.append(
    "<Slide padding={60} style={{ background: '#1E4FA8', fontFamily: 'Microsoft YaHei', "
    "flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>"
    + T("谢谢，请指正", 60, WHITE, True, 1.2)
    + T("无言以对队   ·   AI 校园学习陪伴助手   ·   V1.5.0", 22, PALE, False, 1.4, 30)
    + T("ai-campus-companion.app.workbuddy.host", 17, "#CADCFC", False, 1.4, 14)
    + "</Slide>")

assert len(PAGES) == 18, len(PAGES)
for i, s in enumerate(PAGES, 1):
    assert s.lstrip().startswith("<Slide"), i
    assert s.rstrip().endswith("</Slide>"), i
    with open(os.path.join(OUT, "%02d.slide" % i), "w", encoding="utf-8") as f:
        f.write(s)
print("已生成 %d 个页面源文件 -> %s" % (len(PAGES), OUT))
