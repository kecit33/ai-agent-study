# -*- coding: utf-8 -*-
"""生成第二次团队作业所需的 UML / ER / 连接图矢量源（单一源）。

用法：python docs/第二次团队作业/gen_diagrams.py
输出：assets/*.svg（纯 SVG，离线可渲染，Chrome 打印 PDF 时保持矢量）。
图内模块名、编号与《软件需求规格说明书》V1.5.0 及两份说明书正文逐字一致。
"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "assets")
os.makedirs(OUT, exist_ok=True)

FONT = "Microsoft YaHei, PingFang SC, SimHei, sans-serif"
BLUE = "#2F6FED"
DEEP = "#1B3A78"
INK = "#1F2937"
GRAY = "#5B6B8C"
LINE = "#7C93BF"
BORDER = "#C7D7F5"
PALE = "#EEF4FF"
WHITE = "#FFFFFF"
WARN = "#B45309"


def T(x, y, s, size=14, anchor="start", weight="normal", fill=INK, style=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}" '
            f'font-weight="{weight}" fill="{fill}" font-family="{FONT}" {style}>'
            f'{escape(str(s))}</text>')


def R(x, y, w, h, fill=WHITE, stroke=BORDER, rx=8, sw=1.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')


def E(x, y, rx, ry, fill=PALE, stroke=BLUE, sw=1.4, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="{sw}"{d}/>')


def DIA(x, y, w, h, fill="#FFF7E6", stroke="#D9A441"):
    cx, cy = x + w / 2, y + h / 2
    return (f'<polygon points="{cx},{y} {x+w},{cy} {cx},{y+h} {x},{cy}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="1.4"/>')


def L(x1, y1, x2, y2, arrow=True, dash=None, color=LINE, sw=1.4, label=None,
      lx=None, ly=None, lsize=12):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    mk = ' marker-end="url(#ar)"' if arrow else ""
    out = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
           f'stroke-width="{sw}"{d}{mk}/>')
    if label:
        out += T(lx if lx is not None else (x1 + x2) / 2,
                 ly if ly is not None else (y1 + y2) / 2 - 6,
                 label, lsize, "middle", "normal", GRAY)
    return out


def POLY(points, arrow=True, dash=None, color=LINE, sw=1.4, label=None, lx=0, ly=0):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    mk = ' marker-end="url(#ar)"' if arrow else ""
    pts = " ".join(f"{x},{y}" for x, y in points)
    out = (f'<polyline points="{pts}" fill="none" stroke="{color}" '
           f'stroke-width="{sw}"{d}{mk}/>')
    if label:
        out += T(lx, ly, label, 12, "middle", "normal", GRAY)
    return out


def HEAD():
    return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'width="{{W}}" height="{{H}}" viewBox="0 0 {{W}} {{H}}">'
            f'<defs><marker id="ar" markerWidth="10" markerHeight="8" refX="9" refY="4" '
            f'orient="auto" markerUnits="strokeWidth"><path d="M0,0 L10,4 L0,8 z" '
            f'fill="{LINE}"/></marker></defs>'
            f'<rect x="0" y="0" width="{{W}}" height="{{H}}" fill="{WHITE}"/>')


def save(name, w, h, body, caption):
    # 图内说明文字下方留白，避免页脚与说明行重叠。
    total_h = h + 36
    svg = (HEAD().format(W=w, H=total_h) + body
           + T(24, total_h - 14, caption, 12, "start", "normal", GRAY) + "</svg>")
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)
    print("生成", name, w, "x", total_h)


def actor(x, y, label):
    cx, cy = x, y
    b = E(cx, cy - 22, 11, 11, WHITE, GRAY)
    b += L(cx, cy - 11, cx, cy + 16, False, color=GRAY)
    b += L(cx - 16, cy, cx + 16, cy, False, color=GRAY)
    b += L(cx, cy + 16, cx - 13, cy + 34, False, color=GRAY)
    b += L(cx, cy + 16, cx + 13, cy + 34, False, color=GRAY)
    b += T(cx, cy + 52, label, 13, "middle", "bold", DEEP)
    return b


# ---------------------------------------------------------------- 用例图
def usecase():
    W, H = 1000, 660
    b = T(24, 34, "图 1  用例图（需求分析视角 · V1.5.0）", 18, "start", "bold", DEEP)
    b += R(220, 58, 570, 530, "#FBFCFF", BLUE, 10, 1.6)
    b += T(505, 84, "系统边界：AI 校园学习陪伴助手（ACC）", 15, "middle", "bold", BLUE)

    left = [
        ("课程与资料管理", "F05 · F07 · F08"),
        ("课程内智能问答", "F01 · F06"),
        ("课件总结", "F02"),
        ("引导式习题辅导", "F03"),
        ("复习计划与任务提醒", "F04 · F12"),
        ("错题闭环与导出", "F09 – F11"),
    ]
    right = [
        ("学习资源包", "F13 – F19"),
        ("知识思维导图", "F17"),
        ("学习概览与番茄钟", "F26"),
        ("模型接入与运行时配置", "F20 – F23"),
        ("硬件联动（可选）", "F37 · 不列入验收"),
        ("逐项验收与回归复现", "A01 – A39"),
    ]
    ys = [132, 205, 278, 351, 424, 497]
    for (n, fa), y in zip(left, ys):
        b += E(365, y, 128, 30, PALE, BLUE)
        b += T(365, y - 2, n, 13, "middle", "bold", INK)
        b += T(365, y + 15, fa, 11, "middle", "normal", GRAY)
    for (n, fa), y in zip(right, ys):
        b += E(645, y, 128, 30, PALE, BLUE)
        b += T(645, y - 2, n, 13, "middle", "bold", INK)
        b += T(645, y + 15, fa, 11, "middle", "normal", GRAY)

    b += actor(90, 250, "在校学生")
    b += actor(90, 470, "教师 / 助教")
    b += actor(920, 470, "开发者 / 维护者")
    b += T(90, 326, "主要用户", 11, "middle", "normal", GRAY)
    b += T(90, 550, "验收者", 11, "middle", "normal", GRAY)
    b += T(920, 550, "维护者", 11, "middle", "normal", GRAY)

    # 参与者关联（代表性连线，其余由正文的参与者—用例矩阵完整给出）
    for y in (205, 351, 424):
        b += L(112, 262, 237, y, False, color=LINE, sw=1.1)
    b += L(112, 482, 517, 497, False, color=LINE, sw=1.1)
    b += L(898, 482, 773, 424, False, color=LINE, sw=1.1)
    b += L(898, 482, 517, 497, False, color=LINE, sw=1.1, dash="4 3")

    # include / extend：标注移到说明行，避免压在用例椭圆上。
    b += L(365, 235, 365, 175, True, dash="5 4")
    b += L(645, 132, 645, 102, False, dash="5 4")
    b += POLY([(645, 102), (500, 102), (500, 205), (493, 205)], True, dash="5 4")
    b += T(24, 608, "说明：学生参与除「逐项验收」外的全部用例；虚线中「课程内智能问答」include「课程与资料管理」，「模型接入与运行时配置」extend「课程内智能问答」。",
           12, "start", "normal", GRAY)
    b += T(24, 630, "编号 F / A 与 SRS 第 4、10 章一致。", 12, "start", "normal", GRAY)
    save("用例图.svg", W, H, b, "无言以对 · 第二次团队作业 · 原型设计+概要设计")


# ---------------------------------------------------------------- 活动图
def activity():
    W, H = 1000, 790
    b = T(24, 34, "图 2  活动图（课程复习主业务流程）", 18, "start", "bold", DEEP)
    b += E(500, 62, 15, 15, DEEP, DEEP)
    cx = 500
    steps = [
        (96, "选择或新建课程", "F05 / A04"),
        (158, "粘贴文本或上传课件资料", "F07 · F08 / A10 – A12"),
        (286, "生成课程记忆上下文（单份 4000 字 / 总 12000 字）", "F06 · F33 / A05 · A06 · A36"),
        (528, "生成复习计划与复习任务", "F04 · F12 / A09 · A15"),
        (590, "后台每 30 秒扫描到期任务并下发提醒", "F12 · F37（可选）"),
        (652, "标记掌握 / 导出错题本与资源包", "F11 · F18 / A13 · A14 · A21"),
    ]
    for y, name, fa in steps:
        b += R(cx - 250, y, 500, 46, PALE, BLUE, 10)
        b += T(cx, y + 20, name, 14, "middle", "bold", INK)
        b += T(cx, y + 38, fa, 11, "middle", "normal", GRAY)

    # 判定：资料合法
    b += DIA(430, 218, 140, 56)
    b += T(500, 252, "资料校验通过?", 12, "middle", "bold", INK)
    b += L(500, 204, 500, 218)
    b += L(500, 274, 500, 286)
    b += R(790, 220, 170, 52, "#FFF7E6", "#D9A441", 8)
    b += T(875, 240, "返回 400 与明确文案", 12, "middle", "bold", WARN)
    b += T(875, 258, "表单保留已填内容", 11, "middle", "normal", GRAY)
    b += L(570, 246, 790, 246, True, label="否", lx=680, ly=238)
    b += POLY([(875, 272), (875, 300), (750, 300), (750, 181), (700, 181)], True,
              label="是 / 重新上传", lx=800, ly=294)
    b += T(500, 210, "", 11, "middle", "normal", GRAY)

    # 三分支（问答 / 资源包 / 错题）
    b += L(500, 332, 500, 356)
    b += L(180, 356, 820, 356, False)
    branches = [
        (180, "课程内智能问答", "F01 · F06", "切换课程即切换记忆"),
        (500, "总结与学习资源包", "F02 · F13 – F19", "内置知识库 + 模型双路径"),
        (820, "录入并分析错题", "F09 – F11", "错因 → 变式题 → 掌握"),
    ]
    for x, name, fa, note in branches:
        b += L(x, 356, x, 382)
        b += R(x - 140, 382, 280, 80, WHITE, BORDER, 8)
        b += T(x, 406, name, 14, "middle", "bold", DEEP)
        b += T(x, 426, fa, 11, "middle", "normal", BLUE)
        b += T(x, 446, note, 11, "middle", "normal", GRAY)
        b += L(x, 462, x, 490)
    b += L(180, 490, 820, 490, False)
    b += L(500, 490, 500, 528)
    b += T(850, 486, "汇聚", 12, "start", "bold", GRAY)
    b += L(500, 574, 500, 590)
    b += L(500, 636, 500, 652)
    b += L(500, 698, 500, 720)
    b += E(500, 736, 15, 15, WHITE, DEEP, 2)
    b += E(500, 736, 9, 9, DEEP, DEEP)
    b += T(24, 760, "说明：菱形为判定，圆角为活动，实心圆/双圆为开始/结束；失败路径只返回提示不中断主流程（F30 / A33）。",
           12, "start", "normal", GRAY)
    save("活动图.svg", W, H, b, "无言以对 · 第二次团队作业 · 原型设计+概要设计")


# ---------------------------------------------------------------- 时序图
def sequence():
    W, H = 1160, 830
    b = T(24, 34, "图 3  时序图（重要算法模块：课程记忆智能问答 F01 / F06 / F33）", 18, "start", "bold", DEEP)
    names = ["学生", "前端 app.js", "Handler\nserver.py", "services\ntasks.py",
             "services\ncourse.py", "db.py\nSQLite", "AgentProvider\nfactory", "DemoProvider\n/ 厂商"]
    xs = [70, 215, 365, 515, 665, 815, 965, 1100]
    xs = [70, 220, 370, 520, 670, 820, 970, 1100]
    for x, n in zip(xs, names):
        parts = n.split("\n")
        b += R(x - 72, 56, 144, 48, PALE, BLUE, 6)
        for k, part in enumerate(parts):
            b += T(x, 76 + k * 17, part, 12, "middle", "bold", DEEP)
        b += L(x, 104, x, 780, False, dash="4 4", color=BORDER, sw=1.1)

    msgs = [
        (1, 0, 1, "① 选择课程并输入提问", False),
        (2, 1, 2, "② POST /api/chat {course_id, message}", False),
        (3, 2, 3, "③ 路由分发 chat()", False),
        (4, 3, 4, "④ build_course_context(course_id)", False),
        (5, 4, 5, "⑤ SELECT ... WHERE course_id = ?", False),
        (6, 5, 4, "⑥ 返回课程资料行集", True),
        (7, 4, 3, "⑦ system prompt（单份 4000 / 总 12000 字，超预算提示）", True),
        (8, 3, 6, "⑧ complete(system_prompt, messages)", False),
    ]
    y0, dy = 132, 44
    for idx, (no, a, c, label, ret) in enumerate(msgs):
        y = y0 + idx * dy
        b += L(xs[a], y, xs[c], y, True, dash="5 4" if ret else None, color=LINE, sw=1.5)
        b += T((xs[a] + xs[c]) / 2, y - 8, label, 11.5, "middle", "normal", INK)

    # alt 组合片段
    ay = y0 + 8 * dy - 16
    b += R(905, ay, 235, 142, "#FBFCFF", "#9AAEDB", 6, 1.2)
    b += T(1022, ay + 20, "«alt» 模型可用性", 12, "middle", "bold", DEEP)
    b += L(905, ay + 32, 1140, ay + 32, False, color="#9AAEDB", sw=1)
    b += T(915, ay + 54, "有密钥：厂商 HTTP 调用", 11, "start", "normal", INK)
    b += L(905, ay + 68, 1140, ay + 68, False, dash="4 3", color="#9AAEDB", sw=1)
    b += T(915, ay + 90, "无密钥 / 异常：自动回退", 11, "start", "normal", WARN)
    b += T(915, ay + 108, "响应带 fallback 标记（C05 / F23）", 10.5, "start", "normal", GRAY)

    tail = [
        (9, 6, 3, "⑨ 回复文本（或降级文案）", True),
        (10, 3, 5, "⑩ INSERT conversations（参数绑定）", False),
        (11, 5, 3, "⑪ 写入完成", True),
        (12, 3, 2, "⑫ JSON 响应 {reply, provider, fallback}", True),
        (13, 2, 1, "⑬ 200 + application/json", True),
        (14, 1, 0, "⑭ 安全 Markdown 渲染并展示（F27 / F31）", True),
    ]
    for k, (no, a, c, label, ret) in enumerate(tail):
        y = y0 + (8 + k) * dy + 62
        b += L(xs[a], y, xs[c], y, True, dash="5 4" if ret else None, color=LINE, sw=1.5)
        b += T((xs[a] + xs[c]) / 2, y - 8, label, 11.5, "middle", "normal", INK)
    b += T(24, 810, "说明：虚线为返回消息；alt 片段对应约束 C05「无密钥可运行」；业务层只依赖 AgentProvider 抽象（C03）。",
           12, "start", "normal", GRAY)
    save("时序图.svg", W, H, b, "无言以对 · 第二次团队作业 · 原型设计+概要设计")


# ---------------------------------------------------------------- 协作图
def collaboration():
    W, H = 1000, 660
    b = T(24, 34, "图 4  协作图（通信图）：一键生成学习资源包 F18", 18, "start", "bold", DEEP)
    objs = [
        (60, 90, 210, 54, "前端 StudyPanel", "static/js/app.js"),
        (395, 90, 210, 54, "Handler", "server.py · ROUTES"),
        (730, 90, 210, 54, "services/study.py", "pack()"),
        (730, 265, 210, 54, "subject_knowledge.py", "7 章 / 28 题知识库"),
        (730, 440, 210, 54, "AgentProvider", "get_provider()"),
        (395, 440, 210, 54, "services/mindmap.py", "树 / SVG / Mermaid"),
        (60, 440, 210, 54, "db.py · SQLite", "course_materials"),
        (60, 265, 210, 54, "下载 / 渲染", "blob · 安全 Markdown"),
    ]
    for x, y, w, h, n, sub in objs:
        b += R(x, y, w, h, PALE, BLUE, 6)
        b += T(x + w / 2, y + 24, n, 13, "middle", "bold", DEEP)
        b += T(x + w / 2, y + 43, sub, 11, "middle", "normal", GRAY)

    def c(i):
        x, y, w, h = objs[i][0], objs[i][1], objs[i][2], objs[i][3]
        return x + w / 2, y + h / 2

    # 链接（对象间的通信路径）
    links = [(0, 1), (1, 2), (2, 3), (2, 4), (2, 5), (5, 6), (6, 0), (0, 7), (7, 2)]
    for a, d in links:
        x1, y1 = c(a)
        x2, y2 = c(d)
        b += L(x1, y1, x2, y2, False, color=BORDER, sw=1.6)

    # 标注放在对象之间的空白处，避免覆盖对象名称。
    notes = [
        (327, 70, "1: POST /api/study/pack"),
        (670, 70, "2: pack(course, chapter, count)"),
        (845, 205, "3: 读取章节题目"),
        (845, 375, "4: 可选追加模型原创"),
        (545, 535, "5: 生成思维导图"),
        (170, 535, "6: save_to_course 回写"),
        (155, 375, "7: 返回五件套 JSON"),
        (275, 245, "8: 渲染 / 导出 Markdown"),
    ]
    for x, y, s in notes:
        w = max(122, len(s) * 8.2 + 16)
        b += R(x - w / 2, y - 14, w, 26, WHITE, BORDER, 4, 1)
        b += T(x, y + 4, s, 11.5, "middle", "bold", INK)
    b += T(24, 620, "说明：序号表示消息时序，连线表示对象间链接；第 4 步在模型不可用或超时时静默回退内置知识库，接口不返回空结果（F18 / A21）。",
           12, "start", "normal", GRAY)
    save("协作图.svg", W, H, b, "无言以对 · 第二次团队作业 · 原型设计+概要设计")


# ---------------------------------------------------------------- ER 图
def er():
    W, H = 1120, 760
    b = T(24, 34, "图 5  ER 图（8 个实体 · 联系与基数）", 18, "start", "bold", DEEP)

    ents = [
        (50, 80, 250, 128, "Course / courses", ["PK  id INTEGER", "UK  name TEXT", "    created_at TEXT"]),
        (390, 66, 258, 148, "CourseMaterial / course_materials",
         ["PK  id INTEGER", "FK  course_id INTEGER", "    title TEXT", "    content TEXT", "    created_at TEXT"]),
        (390, 246, 258, 128, "Conversation / conversations",
         ["PK  id INTEGER", "FK  course_id INTEGER", "    role / content TEXT", "    created_at TEXT"]),
        (390, 404, 258, 148, "WrongQuestion / wrong_questions",
         ["PK  id INTEGER", "FK  course_id INTEGER", "    question TEXT", "    user_answer / correct_answer",
          "    error_reason / mastered", "    created_at TEXT"]),
        (740, 66, 268, 128, "ReviewTask / review_tasks",
         ["PK  id INTEGER", "FK  course_id INTEGER（可空）", "    task_name / due_time", "    notified / created_at"]),
        (740, 226, 268, 128, "FocusSession / focus_sessions",
         ["PK  id INTEGER", "FK  course_id INTEGER（可空）", "    minutes / note", "    started_at / ended_at"]),
        (50, 430, 250, 118, "Setting / settings",
         ["PK  key TEXT", "    value TEXT", "active_provider / focus_active"]),
        (740, 430, 268, 118, "ProviderCredential / provider_credentials",
         ["PK  provider TEXT", "    data TEXT（JSON）", "    updated_at TEXT"]),
    ]
    for x, y, w, h, name, fields in ents:
        b += R(x, y, w, h, WHITE, BLUE, 6, 1.6)
        b += R(x, y, w, 30, PALE, BLUE, 6, 1.2)
        b += T(x + w / 2, y + 20, name, 12.5, "middle", "bold", DEEP)
        for k, f in enumerate(fields):
            b += T(x + 12, y + 50 + k * 17, f, 11, "start", "normal", INK)

    # 联系（1:N）
    b += L(300, 144, 390, 140, True, label="所属 1 : N", lx=345, ly=130, lsize=11)
    b += L(300, 144, 390, 300, True, label="记录 1 : N", lx=345, ly=250, lsize=11)
    b += L(300, 144, 390, 462, True, label="归属 1 : N", lx=345, ly=390, lsize=11)
    b += L(648, 140, 740, 140, True, label="1 : N", lx=694, ly=128, lsize=11)
    b += L(648, 290, 740, 276, True, label="1 : N", lx=694, ly=270, lsize=11)
    b += T(24, 600, "独立实体：settings（全局键值配置）与 provider_credentials（运行时模型密钥）不与课程建立外键联系。",
           12.5, "start", "normal", INK)
    b += T(24, 624, "完整性说明：SQLite 默认未启用外键约束；course_materials 与 wrong_questions 由业务层显式校验课程存在性，拒绝孤儿数据（F32 / A35）。",
           12.5, "start", "normal", INK)
    b += T(24, 648, "全部 SQL 使用参数绑定；review_tasks.course_id 与 focus_sessions.course_id 允许为空。",
           12.5, "start", "normal", GRAY)
    b += T(24, 700, "约定：PK 主键 · FK 外键 · UK 唯一约束；「1 : N」表示一门课程对多条子记录。",
           12, "start", "normal", GRAY)
    save("ER图.svg", W, H, b, "无言以对 · 第二次团队作业 · 原型设计+概要设计")


# ---------------------------------------------------------------- 后端分层图
def backend():
    W, H = 1000, 600
    b = T(24, 34, "图 6  后端分层与请求分发设计图", 18, "start", "bold", DEEP)
    layers = [
        (60, 70, 880, 72, "客户端层", "浏览器：static/index.html · style.css · app.js（10 个模块，无框架、无 CDN）"),
        (60, 162, 880, 72, "HTTP 接入层", "server.py：ThreadingHTTPServer · Handler · ROUTES 正则表（40 条 /api/*）· multipart · Download / Raw"),
        (60, 254, 880, 92, "业务服务层（8 模块）",
         "course · tasks · wrong_questions · files · focus · subject_knowledge · study · mindmap"),
        (60, 366, 420, 92, "智能体层", "AgentProvider 抽象 · factory 注册 6 个 Provider · credentials · http_client(urllib)"),
        (500, 366, 440, 92, "数据层", "db.py · SQLite data/companion.db（8 张表）· 参数绑定 · busy_timeout"),
        (60, 478, 880, 72, "可选硬件层", "hardware/esp32.py · esp32_firmware.ino · ESP32_ENDPOINT（未实机联调，不列入验收）"),
    ]
    for x, y, w, h, title, desc in layers:
        b += R(x, y, w, h, WHITE if "可选" not in title else "#FFFBF2", BLUE if "可选" not in title else "#D9A441", 8, 1.5)
        b += R(x, y, 170, h, PALE if "可选" not in title else "#FFF1D6", BORDER, 8, 1.2)
        b += T(x + 85, y + h / 2 + 5, title, 13, "middle", "bold", DEEP)
        lines = desc.split(" · ")
        for k, seg in enumerate(lines):
            b += T(x + 186, y + 24 + k * 17, seg, 11.5, "start", "normal", INK)
    for y in (142, 234, 346, 458):
        b += L(500, y, 500, y + 20, True, color=BLUE, sw=1.8)
    b += T(24, 578, "侧路：后台守护线程每 30 秒 check_due_tasks()；/api/status 暴露版本指纹；静态资源由 Handler 单独分支返回。",
           12, "start", "normal", GRAY)
    save("后端分层图.svg", W, H, b, "无言以对 · 第二次团队作业 · 原型设计+概要设计")


# ---------------------------------------------------------------- 硬件连接图
def hardware():
    W, H = 1000, 420
    b = T(24, 34, "图 7  硬件原型连接图（ESP32 联动 · 接口与固件已齐备，未实机联调）", 18, "start", "bold", DEEP)
    b += R(40, 100, 210, 96, PALE, BLUE, 8)
    b += T(145, 132, "前端「硬件联动」页", 13, "middle", "bold", DEEP)
    b += T(145, 154, "6 点清单表 + 状态看板", 11, "middle", "normal", GRAY)
    b += T(145, 174, "F37（可选）", 11, "middle", "normal", BLUE)

    b += R(300, 100, 250, 96, WHITE, BORDER, 8)
    b += T(425, 128, "server.py", 14, "middle", "bold", DEEP)
    b += T(425, 150, "/api/hardware/test", 11, "middle", "normal", INK)
    b += T(425, 168, "/api/hardware/status", 11, "middle", "normal", INK)
    b += T(425, 186, "/api/focus/state", 11, "middle", "normal", INK)

    b += R(610, 100, 160, 96, "#FFFBF2", "#D9A441", 8)
    b += T(690, 130, "Wi-Fi / HTTP", 13, "middle", "bold", WARN)
    b += T(690, 152, "ESP32_ENDPOINT", 11, "middle", "normal", GRAY)
    b += T(690, 172, "Webhook 双向", 11, "middle", "normal", GRAY)

    b += R(820, 100, 150, 96, WHITE, BLUE, 8)
    b += T(895, 130, "ESP32 固件", 13, "middle", "bold", DEEP)
    b += T(895, 152, "esp32_firmware.ino", 10.5, "middle", "normal", GRAY)
    b += T(895, 172, "监听 /remind /focus", 10.5, "middle", "normal", GRAY)

    b += L(250, 148, 300, 148, True, label="REST", lx=275, ly=138, lsize=11)
    b += L(550, 148, 610, 148, True, label="下行", lx=580, ly=138, lsize=11)
    b += L(770, 148, 820, 148, True, label="下行", lx=795, ly=138, lsize=11)
    b += POLY([(895, 196), (895, 250), (690, 250), (690, 196)], True,
              label="上行：状态看板轮询", lx=790, ly=242)

    b += R(820, 275, 150, 60, "#FFF7E6", "#D9A441", 8)
    b += T(895, 300, "LED / 蜂鸣器", 12, "middle", "bold", WARN)
    b += T(895, 320, "声光表现未实机验证", 10.5, "middle", "normal", GRAY)
    b += L(895, 196, 895, 275, False, color="#D9A441")

    b += T(24, 365, "6 个交互点：任务到点提醒 · 手动测试提醒 · 番茄钟提醒 · 专注状态灯 · 学习状态看板 · 通用消息下发预留。",
           12, "start", "normal", INK)
    b += T(24, 388, "物理照片：【重点 · R04】未提供（见《交付合规检查表与缺口清单》R04）；当前仅提供接口、固件与连接图，LED / 蜂鸣器与 Wi-Fi 连通性未做实机联调。",
           12, "start", "normal", WARN)
    save("硬件连接图.svg", W, H, b, "无言以对 · 第二次团队作业 · 原型设计+概要设计")


if __name__ == "__main__":
    usecase()
    activity()
    sequence()
    collaboration()
    er()
    backend()
    hardware()
    print("全部图源生成完毕")
