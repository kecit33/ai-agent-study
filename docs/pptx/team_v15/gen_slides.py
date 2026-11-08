# -*- coding: utf-8 -*-
"""生成 28 页 .slide 源文件（团队展示 / 选题报告 / 成果展示 / 需求分析）。

内容取自用户本次提供的真实团队资料与 docs/软件需求规格说明书.md（V1.5.0 验收基线）。
配图全部为项目真实资产（docs/svg_fallback、docs/blog/assets），无 AI 生图、无编造数据。
成果展示章节含 7 个单图页：每页一张真实运行截图 + 对应需求 F 编号与文字说明。
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

# ---------------- P02 目录 ----------------
rows = ""
for idx, (n, name, pg, en, kw) in enumerate([
        ("01", "团队展示", "P03 – P07", "Team", "队名 · 分工 · 队员风采 · 愿景"),
        ("02", "选题报告", "P08 – P11", "Topic", "备考痛点 · 能力全景 · 零依赖架构"),
        ("03", "成果展示", "P12 – P21", "Achievements", "已上线系统 · 7 页真实界面 · 回归实测"),
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
def MEMBER(num, name, sid, role, traits, skills, hobbies, duty, chapter, page):
    badge = B(
        T(name[0], 96, WHITE, True, 1.0, align="center")
        + T("无言以对队  ·  队员 " + num, 15, "#CADCFC", False, 1.3, 12, align="center"),
        "width: 300, height: 238, background: '#1E4FA8', borderRadius: 6, "
        "flexDirection: 'column', alignItems: 'center', justifyContent: 'center'")
    left = (
        B(NUM(num) + T(name, 36, INK, True, 1.2, 14),
          "width: 300, height: 90, flexDirection: 'row', alignItems: 'center', gap: 14")
        + T("学号  " + sid, 18, GRAY, False, 1.4, 8)
        + B(T(role, 19, BLUE, True, 1.3),
            "width: 300, height: 40, background: '#E8EFF8', flexDirection: 'row', "
            "alignItems: 'center', padding: 12, marginTop: 14")
        + B(badge, "width: 300, marginTop: 18, flexDirection: 'column'"))
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
    "01 · Team", 5))

PAGES.append(MEMBER(
    "02", "邓文炜", "3124004505", "前端开发",
    "想法活跃，重视用户体验；耐心打磨交互细节，善于发现界面隐性问题。",
    "原生 HTML/CSS/JS、Markdown 渲染、页面状态管理、前端故障排查。",
    "UI 交互设计、截图做原型、研究 Web 安全前端风险。",
    "全部前端页面、10 个导航模块实现、安全 Markdown 渲染器、忙碌态交互、资料查看 / 下载功能、XSS 前端验证、页面截图素材输出。",
    "01 · Team", 6))

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
    B(frame,
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
            + T("V1.5.0 首页概览  ·  真实运行截图", 14, LIGHT, False, 1.3, 8),
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
    + B(B(IMG("ui_study_pack.png", 300, 190)
          + T("学习资源包生成 · 能力 06 · 真实界面", 13, LIGHT, False, 1.3, 6),
          "width: 310, flexDirection: 'column'")
        + B(IMG("ui_wrong.png", 300, 190)
          + T("AI 错题本闭环 · 能力 05 · 真实界面", 13, LIGHT, False, 1.3, 6),
          "width: 310, flexDirection: 'column'")
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

# ---------------- P12 章节 03 成果展示 ----------------
PAGES.append(SECTION("03", "成果展示", "已上线系统  ·  真实界面  ·  回归实测"))

# ---------------- P13 已上线成果总览 ----------------
ach_url = B(
    T("已发布 · 可直接访问（V1.5.0 验收基线）", 17, "#CADCFC", False, 1.3)
    + T("ai-campus-companion.app.workbuddy.host", 27, WHITE, True, 1.3, 8)
    + T("?sharecode=CEUN7FBTFJ   ·   浏览器 / 手机直接打开，无需安装、无需密钥", 16, PALE, False, 1.3, 8),
    "width: 1160, height: 132, background: '#1E4FA8', padding: 20, flexDirection: 'column'")
ach_metrics = [
    ("40", "条 REST 路由"), ("37", "项功能 F01–F37"), ("39", "条验收 A01–A39"),
    ("8", "张 SQLite 表"), ("6", "个可插拔 Provider"), ("10", "个前端模块"),
]
ach_grid = ""
for v, lab in ach_metrics:
    ach_grid += B(T(v, 40, BLUE, True, 1.0) + T(lab, 17, GRAY, False, 1.3, 4),
                  "width: 372, height: 106, background: '#F7F9FC', "
                  "border: '1px solid #D6DCE5', padding: 14, flexDirection: 'column'")
body_ach1 = (
    B(ach_url, "width: 1160, flexDirection: 'column'")
    + B(B(ach_grid, "width: 1160, flexDirection: 'row', flexWrap: 'wrap', gap: 12"),
        "width: 1160, marginTop: 16")
    + B(BAR("版本 1.5.0  ·  app.js 47665 字节与本地一致  ·  active_provider = demo", 48),
        "width: 1160, marginTop: 16"))
PAGES.append(CONTENT("已上线成果总览", "03 · Achievements", 13, body_ach1))

# ---------------- P14 – P20 真实界面展示（每页一图 + 文字说明） ----------------
def SHOWCASE(item, page, idx, total):
    left = B(
        B(IMG(item["img"], 640, 440),
          "width: 640, height: 440, background: '#F7F9FC', border: '1px solid #D6DCE5', "
          "borderRadius: 6, flexDirection: 'row', alignItems: 'center', justifyContent: 'center'")
        + T("真实运行界面截图  ·  非示意图、非 AI 生成图", 13, LIGHT, False, 1.3, 10),
        "width: 660, flexDirection: 'column'")
    pts = ""
    for k, v in item["points"]:
        pts += B(T("▪  " + k, 18, BLUE, True, 1.3) + T(v, 15, GRAY, False, 1.45, 4),
                 "width: 460, flexDirection: 'column', marginTop: 12")
    right = B(
        T(item["title"], 26, INK, True, 1.25)
        + B(T(item["fa"], 15, BLUE, True, 1.3),
            "width: 440, height: 34, background: '#E8EFF8', flexDirection: 'row', "
            "alignItems: 'center', padding: 10, marginTop: 12")
        + T(item["desc"], 17, INK, False, 1.55, 14)
        + pts
        + B(T("真实界面  %d / %d" % (idx, total), 13, WHITE, True, 1.3),
            "width: 190, height: 32, background: '#1E4FA8', borderRadius: 4, "
            "flexDirection: 'row', alignItems: 'center', justifyContent: 'center', marginTop: 16"),
        "width: 480, flexDirection: 'column'")
    body = B(left + right, "width: 1160, height: 497, flexDirection: 'row', gap: 20")
    return CONTENT("成果展示 · " + item["title"], "03 · Achievements", page, body)


showcase = [
    dict(img="ui_home.png", title="学习概览与专注统计",
         fa="对应需求 F26 学习概览与番茄钟 · 验收 A29",
         desc="打开即用的课程工作台：问答、总结、错题、复习、专注等统计按课程一屏聚合，待复习任务置顶聚焦。",
         points=[("课程维度统计", "六项统计聚合呈现，薄弱知识点与待复习任务优先展示。"),
                 ("待复习聚焦", "到期复习任务卡片置顶，完成后即时更新状态。"),
                 ("键盘可达", "统计卡片支持 Tab / Enter / Space 与焦点样式（F29）。")]),
    dict(img="ui_chat.png", title="课程内智能问答",
         fa="对应需求 F01 问答 · F06 记忆绑定 · 验收 A05–A06",
         desc="每次提问自动携带当前课程资料上下文；切换课程即切换记忆，不再从零交代背景。",
         points=[("课程记忆隔离", "资料全文拼入 system prompt；单份 4000 字、总量 12000 字预算（F33）。"),
                 ("安全 Markdown", "回答按 escape-first 富文本渲染，防存储型 XSS（F27 / F31）。"),
                 ("防重复提交", "请求中按钮禁用并提示，结束后恢复（F28）。")]),
    dict(img="ui_summarize.png", title="课件总结",
         fa="对应需求 F02 课件总结 · F08 文件解析 · 验收 A07 / A12",
         desc="粘贴或上传课件文本，一键输出知识点与考点提纲，结果可下载 .md 归档复习。",
         points=[("多格式上传", "txt / md / markdown / docx 上传即入课程记忆，docx 实体全还原（F36）。"),
                 ("结构化输出", "知识点与考点提纲分层呈现，直接用于复习。"),
                 ("演示可复现", "演示模式即可完整跑通，答辩现场可直接演示。")]),
    dict(img="ui_plan.png", title="复习计划",
         fa="对应需求 F04 复习计划 · F12 到点提醒 · 验收 A09 / A15",
         desc="按科目与剩余天数生成逐日安排：基础回顾 → 重点突破 → 真题演练 → 查漏补缺 → 冲刺。",
         points=[("逐日计划", "每日 2–3 小时粒度，配合错题本安排复盘。"),
                 ("到点提醒", "后台守护线程每 30 秒扫描到期复习任务（F12）。"),
                 ("演示可跑通", "演示模式即可生成；配置真实密钥后结合课程资料个性化。")]),
    dict(img="ui_study_pack.png", title="学习资源包",
         fa="对应需求 F18 一键全套与导出 · 验收 A21",
         desc="一次生成六类产出：定向自测题、复习总结、专题文章、资料清单、思维导图与错题关联。",
         points=[("一键全套", "五件套一次生成，结果可回写课程记忆。"),
                 ("导出健壮", "blob 下载失败不替换整页；资料链接协议白名单（F35 / F36）。"),
                 ("学科适配", "内置学科返回结构化章节；自定义科目给出提示（F19）。")]),
    dict(img="ui_wrong.png", title="AI 错题本",
         fa="对应需求 F09 – F11 错题闭环 · 验收 A13 – A14",
         desc="录入 → 错因分析 → 同类变式题 → 掌握标记 → 导出，形成完整错题闭环。",
         points=[("录入与筛选", "题干 / 我的答案 / 正确答案三段录入，按掌握状态筛选。"),
                 ("错因与变式", "分析错因并生成同类变式题，针对薄弱点强化（F10）。"),
                 ("导出归档", "一键导出 Markdown 错题本（F11）。")]),
    dict(img="ui_model_settings.png", title="模型接入与运行时配置",
         fa="对应需求 F20 – F23 智能体接入 · 验收 A23 – A26",
         desc="6 个可插拔 Provider：OpenAI / 文心一言 / Kimi / Claude / 自定义 / 演示模式。",
         points=[("运行时配置", "Web 或 REST 写入密钥与模型地址，即时生效无需重启（F21）。"),
                 ("连通性自检", "配置校验与真实探针；自建系统可直接透传调用（F22）。"),
                 ("自动回退", "未配置或调用异常时回退演示模式，响应带 fallback 标记（F23）。")]),
]
for si, item in enumerate(showcase):
    PAGES.append(SHOWCASE(item, 14 + si, si + 1, len(showcase)))

# ---------------- P21 实测证据与交付物 ----------------
ach_dlv = [
    ("需求规格说明书", "GB/T 9385 口径；.md 单一源 + .docx 验收主件"),
    ("答辩演示文稿", "本 PPT 28 页，四部分结构与真实图资产"),
    ("博客园复盘长文", "13 节 + 13 张图，已同步 V1.5.0 口径"),
    ("四套回归与证据", "startup / demo / feature / study + 本地与线上 JSON"),
    ("自我检查报告", "12 节，三轮自查与 11 项修复记录"),
    ("README 与图资产", "40 条路由、架构图 / 思维导图 / 类图"),
]
ach_rows = ""
for i, (k, v) in enumerate(ach_dlv):
    ach_rows += B(
        T(k, 19, BLUE, True, 1.3, width=200) + T(v, 17, GRAY, False, 1.35, width=470),
        "width: 700, height: 52, flexDirection: 'row', alignItems: 'center', gap: 10"
        + (", borderBottom: '1px solid #E5E7EB'" if i < 5 else ""))
ach_right = B(
    T("四套回归全绿", 26, WHITE, True, 1.3)
    + T("本地  26/26 · 26/26+30/30 · 19/19 · 36/36", 17, WHITE, False, 1.5, 14)
    + T("线上  26/26 · 26/26+30/30 · 19/19 · 25/25", 17, WHITE, False, 1.5, 6)
    + T("线上 25/25 非漏测：11 项需本机模拟厂商端点", 16, "#CADCFC", False, 1.4, 14)
    + T("成果边界：无真实厂商 Key、ESP32 未实机、团队合照待补", 15, "#CADCFC", False, 1.4, 16),
    "width: 420, height: 312, background: '#1E4FA8', padding: 20, flexDirection: 'column'")
body_ach3 = (
    B(T("交付物与可复核证据", 22, BLUE, True, 1.4),
      "width: 1160, height: 40, flexDirection: 'column'")
    + B(B(ach_rows, "width: 700, height: 312, flexDirection: 'column'") + ach_right,
        "width: 1160, height: 312, flexDirection: 'row', "
        "justifyContent: 'space-between', gap: 20, marginTop: 8")
    + B(BAR("全部数字可由 docs/*_results.json 与需求文档 10.5 节复核；答辩现场可打开线上链接逐项走查。", 46),
        "width: 1160, marginTop: 14"))
PAGES.append(CONTENT("实测证据与交付物", "03 · Achievements", 21, body_ach3))

# ---------------- P22 章节 04 需求分析 ----------------
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
PAGES.append(CONTENT("依据、迭代记录与项目标志", "04 · Requirements", 23, body13))

# ---------------- P24 思维导图与类图 ----------------
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
PAGES.append(CONTENT("思维导图与类图", "04 · Requirements", 24, body14))

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
body15 = (
    B(B(kpis, "width: 1160, height: 112, flexDirection: 'row', justifyContent: 'space-between'"),
      "width: 1160")
    + B(B(B(fe, "width: 350, flexDirection: 'column'") + B(be, "width: 350, flexDirection: 'column'"),
          "width: 720, height: 290, flexDirection: 'row', justifyContent: 'space-between', gap: 16")
        + B(IMG("ui_chat.png", 400, 256)
            + T("课程内智能问答 · 真实界面", 13, LIGHT, False, 1.3, 6),
          "width: 410, flexDirection: 'column'"),
        "width: 1160, height: 290, flexDirection: 'row', justifyContent: 'space-between', gap: 20, marginTop: 12")
    + B(BAR("每项功能都能在代码、接口表与测试报告中逐条追溯。", 46), "width: 1160, marginTop: 10"))
PAGES.append(CONTENT("功能描述与前后端详述", "04 · Requirements", 25, body15))

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
PAGES.append(CONTENT("验收标准与实测结果", "04 · Requirements", 26, body16))

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
PAGES.append(CONTENT("范围边界与不予承诺", "04 · Requirements", 27, body17))

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
