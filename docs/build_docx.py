# -*- coding: utf-8 -*-
"""手写 OOXML 生成《软件需求规格说明书》docx。
- 符合 GB/T 9385-2008 / GB/T 8567-2006 结构
- 嵌入 SVG 矢量图（项目标志 / 思维导图 / 类图 / 架构图），并附 1x1 PNG 兜底
"""
import os, zipfile, base64, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "软件需求规格说明书.docx")

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))

# 1x1 透明 PNG（作为 SVG 在不支持时的兜底栅格图）
PNG1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42tNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

EMU_IN = 914400
def img_block(path, emu_w):
    name = os.path.basename(path)
    w_px, h_px = SIZES[name]
    emu_h = int(emu_w * h_px / w_px)
    rid_svg = "rId_" + name.replace(".", "_") + "_svg"
    rid_png = "rId_" + name.replace(".", "_") + "_png"
    drawing = f'''<w:p><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"
      xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
      xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/svg">
      <wp:extent cx="{emu_w}" cy="{emu_h}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
      <wp:docPr id="1" name="{name}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
      <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic><pic:nvPicPr><pic:cNvPr id="1" name="{name}"/><pic:cNvPicPr/></pic:nvPicPr>
        <pic:blipFill><a:blip r:embed="{rid_svg}">
          <a:extLst><a:ext uri="{{96DAC541-7B7A-43D3-8B79-8D1A8339B2E1}}">
            <asvg:svgBlip r:embed="{rid_png}"/></a:ext></a:extLst></a:blip>
          <a:stretch><a:fillRect/></a:stretch></pic:blipFill>
        <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>
      </a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''
    return drawing, rid_svg, rid_png, name

SIZES = {
    "logo.svg": (640, 220),
    "mindmap.svg": (960, 620),
    "classdiagram.svg": (1000, 700),
    "architecture.svg": (960, 460),
}

# ---------------- 内容构建 ----------------
body = []
def title(t): body.append(f'<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')
def h1(t): body.append(f'<w:p><w:pPr><w:pStyle w:val="H1"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')
def h2(t): body.append(f'<w:p><w:pPr><w:pStyle w:val="H2"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')
def h3(t): body.append(f'<w:p><w:pPr><w:pStyle w:val="H3"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')
def p(t): body.append(f'<w:p><w:pPr><w:spacing w:after="120"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')
def bullet(t): body.append(f'<w:p><w:pPr><w:pStyle w:val="ListBullet"/></w:pPr><w:r><w:t xml:space="preserve">{esc(t)}</w:t></w:r></w:p>')

def table(headers, rows, widths=None):
    n = len(headers)
    if widths is None:
        widths = [int(9360 / n)] * n
    cells = []
    def cell(text, w, bold=False, fill=None):
        shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ''
        b = '<w:b/>' if bold else ''
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}</w:tcPr>'
                f'<w:p><w:r><w:rPr>{b}</w:rPr><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p></w:tc>')
    trh = '<w:tr>' + ''.join(cell(h, widths[i], bold=True, fill="2F6FED") for i, h in enumerate(headers)) + '</w:tr>'
    trs = []
    for r in rows:
        trs.append('<w:tr>' + ''.join(cell(c, widths[i]) for i, c in enumerate(r)) + '</w:tr>')
    tbl = ('<w:tbl><w:tblPr><w:tblW w:w="9360" w:type="dxa"/>'
           '<w:tblBorders>'
           + ''.join(f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="9FB3D6"/>'
                     for e in ["top","left","bottom","right","insideH","insideV"]) +
           '</w:tblBorders></w:tblPr>'
           '<w:tblGrid>' + ''.join(f'<w:gridCol w:w="{w}"/>' for w in widths) + '</w:tblGrid>'
           + trh + ''.join(trs) + '</w:tbl>')
    body.append(tbl)
    body.append('<w:p/>')

RELATIONS = []  # (rid, target, type)
MEDIA = []      # (name, bytes)
def image(name, emu_w=5486400):
    svg_path = os.path.join(HERE, name)
    with open(svg_path, "rb") as f:
        svg_bytes = f.read()
    drawing, rid_svg, rid_png, fname = img_block(svg_path, emu_w)
    body.append(drawing)
    RELATIONS.append((rid_svg, f"media/{fname}", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "image/svg+xml"))
    RELATIONS.append((rid_png, f"media/{fname}.png", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "image/png"))
    MEDIA.append((fname, svg_bytes))
    MEDIA.append((fname + ".png", PNG1x1))

# ================= 文档正文 =================
today = datetime.date.today().isoformat()
title("软件需求规格说明书")
p("AI 校园学习陪伴助手（AI Campus Learning Companion）")
p(f"版本：V1.1    日期：{today}    编写：第X开发组（占位）")

h1("文档信息与迭代记录表")
table(["版本", "日期", "迭代内容", "负责人（占位）"],
      [["V0.1", "选题调研", "真实需求调研、确定选题与价值", "产品"],
       ["V0.5", "需求与架构", "功能设计、可插拔智能体架构、数据模型", "后端"],
       ["V0.8", "核心实现", "Flask 后端、原生前端、课程记忆与错题闭环", "全组"],
       ["V0.9", "硬件接口", "ESP32 Webhook 联动接口与固件（可选加分）", "硬件"],
       ["V1.0", "上线与交付", "部署指南、需求文档、答辩材料", "全组"],
       ["V1.1", "体验增强", "深浅色主题与主题色、语音输入、文件上传/导出、学习概览、番茄钟、硬件双向联动、12 项新接口", "全组"]],
      widths=[1400, 1800, 4560, 1600])

h1("项目标志")
image("logo.svg", emu_w=3600000)
p("图 1 项目标志：以书页与「AI」组合，体现“学习陪伴 + 智能体”的定位。")

h1("一、引言")
h2("1.1 编写目的")
p("本文档依据 GB/T 9385-2008《计算机软件需求说明编制指南》与 GB/T 8567-2006《计算机软件文档编制规范》编写，"
  "明确“AI 校园学习陪伴助手”的功能需求、数据需求、接口需求、验收标准与前后端设计，作为开发、测试、验收与答辩的依据。")
h2("1.2 背景与需求来源")
p("本选题源于智能体开发课程作业，并基于对本校同学的真实调研：课堂笔记零散、作业缺乏引导式讲解、"
  "考前不知如何规划复习、通用大模型不了解本校课程重点、缺少背诵自测与错题整理的一体化工具。"
  "项目面向本校学生，提供嵌入大模型智能体的轻量级学习助手，杜绝虚构需求。")
h2("1.3 术语定义")
bullet("智能体（Agent）：本文指 GPT / 文心一言 / Kimi / Claude 等大模型能力，通过开放接口嵌入本系统。")
bullet("课程记忆智能体：按课程隔离上下文，使问答严格限定在已上传课程资料范围内。")
bullet("错题闭环：提问—做题—错题归档—定向复习的学习闭环。")
h2("1.4 参考资料")
bullet("GB/T 9385-2008 计算机软件需求说明编制指南")
bullet("GB/T 8567-2006 计算机软件文档编制规范")
bullet("选题报告《AI 校园学习陪伴助手》（见答辩材料）")

h1("二、总体描述")
h2("2.1 产品前景")
p("产品是一款面向大学生课程学习场景、基于大模型智能体的 Web 应用，帮助用户高效完成课程学习与复习，"
  "核心价值在于垂直场景定制与“课程记忆 + 错题闭环”的杀手级功能。")
h2("2.2 用户特征")
bullet("本校学生：直接使用问答、总结、辅导、计划、错题本等功能，使用门槛低。")
bullet("教师 / 助教：检查系统功能、验证课程记忆与定向出题效果。")
h2("2.3 运行环境")
bullet("前端：任意现代浏览器（Chrome / Edge / Firefox / Safari）。")
bullet("后端：Python 3.8+；默认入口 server.py 仅用标准库，零依赖可运行；app.py 为等价 Flask 版。")
bullet("数据存储：SQLite（轻量、零配置）。")
bullet("部署：PythonAnywhere / Render 等免费平台，生成可访问链接。")
bullet("可选硬件：ESP32 开发板 + LED + 蜂鸣器（硬件联动加分项）。")
h2("2.4 设计与实现约束")
bullet("智能体接口必须可插拔集成至自建系统，严禁直接套用官方聊天页面。")
bullet("API 密钥经环境变量注入，禁止硬编码。")
bullet("未配置密钥时系统自动进入内置演示模式，保证无密钥也可完整运行与验收。")
h2("2.5 假设与依赖")
bullet("依赖厂商开放接口可达；任一厂商不可用时自动回退演示模式，系统永不断联。")
bullet("部署平台提供 Python 运行环境与公网访问。")

h1("三、具体需求")
h2("3.1 功能需求（思维导图）")
image("mindmap.svg", emu_w=5600000)
p("图 2 功能思维导图：以“基础功能 / 杀手级功能 / 技术架构 / 硬件联动 / 创新价值”五大分支组织。")
table(["编号", "功能", "说明", "优先级"],
      [["F1", "智能问答", "按课程隔离上下文的智能问答", "高"],
       ["F2", "课件总结", "粘贴课件文字，提炼知识点并生成考点提纲", "高"],
       ["F3", "习题辅导", "引导式讲解，先给思路与分步推导，不直接甩答案", "高"],
       ["F4", "复习计划", "输入科目与剩余天数，生成每日复习安排", "中"],
       ["F5", "课程记忆智能体", "按课程上传资料并隔离上下文，切换课程自动切换记忆", "高（杀手级）"],
       ["F6", "AI 错题本与定向出题", "录入错题、分析错因、生成同类变式题巩固", "高（杀手级）"],
       ["F7", "硬件联动提醒", "复习任务到点向 ESP32 下发 LED+蜂鸣器提醒（可选）", "低（加分）"],
       ["F8", "智能体可插拔切换", "GPT/文心/Kimi/Claude 可切换，无密钥回退演示", "高"],
       ["F9", "深浅色主题与主题色", "跟随系统 + 手动三档 + 6 套主题色与自定义主色，本地持久化", "中"],
       ["F10", "语音输入", "Web Speech API，覆盖问答/总结/辅导/资料/错题 5 处输入", "中"],
       ["F11", "文件上传与导出", "txt/md/docx 课件上传自动入课程记忆；错题本导出 Markdown", "中"],
       ["F12", "学习概览", "课程/资料/掌握率/今日专注/待复习/最近记录聚合看板", "中"],
       ["F13", "番茄钟专注", "自定义时长、开始/暂停/重置、到点记录并联动硬件", "中"],
       ["F14", "硬件双向联动", "下行提醒与专注灯 + 上行学习状态轮询，共 6 个交互点", "低（加分）"]],
      widths=[900, 2200, 4960, 1300])

h2("3.2 智能体可插拔接口需求")
bullet("系统定义统一的 AgentProvider 接口（complete(system, messages) / is_available()）。")
bullet("内置四类真实实现：OpenAIProvider、QianFanProvider（文心一言）、MoonshotProvider（Kimi）、ClaudeProvider。")
bullet("内置 DemoProvider：无需密钥的规则化应答，作为兜底。")
bullet("ProviderFactory 按配置选择当前提供商；若所选厂商不可用或调用异常，自动回退 DemoProvider。")
bullet("所有密钥从环境变量读取，提供 .env.example 说明。")

h2("3.3 数据需求（类图）")
image("classdiagram.svg", emu_w=5600000)
p("图 3 类图：展示 AgentProvider 抽象及其四类实现与 DemoProvider、ProviderFactory、服务层、"
  "SQLite 数据实体与 Flask 路由之间的关系。")
table(["数据实体", "主要字段", "说明"],
      [["Course", "id, name", "课程，作为上下文隔离单元"],
       ["CourseMaterial", "course_id, title, content", "课程上传资料"],
       ["Conversation", "course_id, role, content", "课程内对话历史"],
       ["WrongQuestion", "course_id, question, error_reason, mastered", "错题与错因、掌握状态"],
       ["ReviewTask", "course_id, task_name, due_time, notified", "复习任务与提醒状态"],
       ["Setting", "key, value", "当前激活提供商等设置"]],
      widths=[2000, 3960, 3400])

h2("3.4 性能需求")
bullet("单次智能体应答（演示模式）本地处理 < 1s；真实接口受厂商延迟影响，目标 < 15s。")
bullet("并发：课程演示场景下支持数十人同时在线。")
bullet("数据规模：单课程资料、对话、错题量在千级以内，SQLite 完全满足。")

h2("3.5 接口需求（REST API）")
table(["方法", "路径", "说明"],
      [["GET", "/api/status", "系统状态与提供商列表"],
       ["GET/POST", "/api/courses", "课程列表 / 新建课程"],
       ["POST", "/api/courses/<id>/materials", "为课程上传资料"],
       ["POST", "/api/chat", "课程记忆智能体问答"],
       ["POST", "/api/summarize", "课件总结"],
       ["POST", "/api/tutor", "习题引导式辅导"],
       ["POST", "/api/review-plan", "复习计划生成"],
       ["GET/POST", "/api/wrong-questions", "错题列表 / 新增错题"],
       ["POST", "/api/wrong-questions/<id>/analyze", "错因分析 + 变式出题"],
       ["POST", "/api/review-tasks", "创建复习任务（可即时/到点下发）"],
       ["POST", "/api/hardware/test", "向 ESP32 下发测试提醒"],
       ["POST", "/api/courses/<id>/materials/upload", "课件文件上传（multipart）"],
       ["GET", "/api/wrong-questions/export", "导出错题本 Markdown"],
       ["GET", "/api/overview", "学习概览统计"],
       ["GET/POST", "/api/focus/sessions", "专注记录列表 / 新增专注"],
       ["POST", "/api/focus/state", "设置专注状态并推送硬件"],
       ["GET", "/api/hardware/status", "学习状态看板（供 ESP32 轮询）"]],
      widths=[1200, 3600, 4560])

h2("3.6 硬件联动需求（可选加分）")
bullet("后端提供 review_tasks 到点扫描（每 30s），到期任务向 ESP32_ENDPOINT 发送 JSON 提醒。")
bullet("ESP32 固件（hardware/esp32_firmware.ino）监听 /remind，收到后点亮 LED 并触发蜂鸣器。")
bullet("未配置 ESP32_ENDPOINT 时不影响主体功能，仅在设置页提示。")

h2("3.7 安全性需求")
bullet("API 密钥仅存于环境变量 / .env，禁止写入源码与数据库。")
bullet("用户输入在展示层做转义，避免 XSS；SQL 使用参数化查询，防注入。")

h2("3.8 系统架构图")
image("architecture.svg", emu_w=5600000)
p("图 4 系统架构：前端经 REST 调用 Flask 后端；后端经 ProviderFactory 调度可插拔智能体；"
  "数据持久化至 SQLite；可选经 Webhook 联动 ESP32。")

h1("四、验收标准")
table(["编号", "验收项", "可测标准"],
      [["A1", "可访问性", "部署后师生通过浏览器打开链接即可使用全部功能"],
       ["A2", "无密钥可运行", "未配置任何密钥时，全部功能以演示模式完整跑通"],
       ["A3", "课程记忆隔离", "为课程 A 上传资料后，A 的问答限定在 A 资料内；切换课程上下文随之切换"],
       ["A4", "课件总结", "粘贴课件可输出“知识点 + 考点提纲”两部分"],
       ["A5", "习题辅导", "返回内容包含思路/分步引导，且不直接给出最终答案"],
       ["A6", "复习计划", "输入科目+天数可生成按天安排"],
       ["A7", "错题闭环", "可录入错题、查看错因、生成变式题、标记掌握"],
       ["A8", "可插拔切换", "在设置页切换提供商，未配置密钥者回退演示，系统不报错"],
       ["A9", "密钥安全", "源码与数据库均不含任何明文密钥"],
       ["A10", "硬件（可选）", "配置 ESP32 后，复习任务到点可触发 LED+蜂鸣器（演示用 fire_now 可即时验证）"]],
      widths=[900, 2200, 6260])

h1("五、前后端详尽描述")
h2("5.1 前端")
bullet("技术：原生 HTML + CSS + JavaScript，无框架，轻量、易上线。")
bullet("结构：顶部品牌栏、智能体徽标与主题切换按钮；9 个功能模块以标签页切换，支持 URL hash 直达。")
bullet("模块：智能问答（课程隔离对话）、课件总结、习题辅导、复习计划、课程记忆（资料上传）、"
      "错题本（错因+变式）、硬件联动、设置（提供商切换与配置说明）。")
bullet("交互：课程下拉选择影响问答/记忆/错题；所有请求通过 fetch 调用 REST API，结果渲染到页面。")
h2("5.2 后端")
bullet("技术：双后端入口，server.py（Python 标准库，零依赖，默认）与 app.py（Flask，可选）；SQLite 存储；后台 30s 调度扫描到期复习任务。")
bullet("目录：agents/（可插拔智能体）、services/（业务服务）、hardware/（ESP32）、db.py（数据层）、app.py（路由入口）。")
bullet("服务层：CourseService（课程/资料/上下文）、TaskService（问答/总结/辅导/计划）、"
      "WrongQuestionService（错题/变式）、HardwareService（提醒下发）。")
bullet("数据访问：全部使用参数化 SQL，防止注入；数据库文件位于 data/companion.db，首次启动自动初始化。")
h2("5.3 部署与运行")
p("详见随附《README 部署指南》：默认零依赖启动 `python server.py`（或双击 start.bat），"
  "访问 http://localhost:5000；Flask 版需 `pip install -r requirements.txt && python app.py`；"
  "云端按 Render Blueprint / PythonAnywhere WSGI 配置即可生成访问链接。")


h1("六、功能描述（V1.1 增量）")
p("本章为 V1.1 迭代新增功能的详细描述，与第三章基础需求共同构成完整功能描述；"
  "对应迭代记录表 V1.1 行。本章所有条目均已实现，并有真实 HTTP 验证数据（见 6.7）。")

h2("6.1 主题与外观配置")
bullet("深/浅色跟随系统：依据 CSS 媒体查询 prefers-color-scheme 自动切换，并监听系统主题变化事件实时跟随；首屏渲染前读取本地偏好，避免闪白。")
bullet("手动三档：浅色 / 深色 / 跟随系统，顶栏一键循环与「设置」页分段控件双入口，选择写入 localStorage 持久化。")
bullet("主题色：6 套预设（蓝/青/紫/橙/粉/绿）与自定义主色拾色器，改写 CSS 变量即时生效。")
bullet("上传区、番茄钟、统计卡、硬件看板、语音按钮等新增组件全部适配暗色，文字对比度可读。")

h2("6.2 语音输入")
bullet("基于浏览器 Web Speech API（webkitSpeechRecognition），识别语言 zh-CN，结果写入对应输入框。")
bullet("覆盖智能问答、课件总结、习题辅导、课程资料、错题题干共 5 处输入。")
bullet("不支持该 API 的浏览器给出明确降级提示；切换标签页时停止识别并释放麦克风，不影响其余功能。")

h2("6.3 文件传输")
bullet("上传：POST /api/courses/<id>/materials/upload，multipart/form-data 由标准库手写解析，无第三方依赖。")
bullet("类型白名单 .txt/.md/.markdown/.docx；.docx 通过 zipfile 读取 document.xml 提取正文；UTF-8/GBK 双解码；单文件上限 2 MB；非法类型返回 400。")
bullet("上传成功后资料自动写入该课程记忆，后续问答即可引用，形成「上传即记忆」闭环。")
bullet("导出：GET /api/wrong-questions/export 导出错题本 Markdown，Content-Disposition 携带 UTF-8 编码文件名。")

h2("6.4 学习概览与番茄钟")
bullet("学习概览：课程数、资料数、错题掌握率、今日专注分钟、待复习任务数、最近专注记录，均由参数化 SQL 聚合得出。")
bullet("番茄钟：自定义时长、开始/暂停/重置；计时结束写入 focus_sessions 表，并可选向 ESP32 下发休息提醒。")
bullet("专注状态同步写入 settings 表，供 Web 概览、服务端与开发板状态灯三处读取，保持一致。")

h2("6.5 硬件双向联动（6 个交互点）")
table(["编号", "交互点", "方向 / 接口", "硬件表现"],
      [["H1", "复习任务到点提醒", "服务端每 30s 扫描 → POST {ESP32}/remind", "LED 亮 + 蜂鸣器响 1.5s"],
       ["H2", "手动测试提醒", "POST /api/hardware/test → /remind", "同上，答辩现场即时演示"],
       ["H3", "番茄钟到点提醒", "POST /api/focus/sessions → /remind", "专注完成时声光提醒休息"],
       ["H4", "专注状态灯", "POST /api/focus/state → POST {ESP32}/focus", "专注中 LED 常亮，结束熄灭"],
       ["H5", "学习状态看板（上行）", "ESP32 每 60s GET /api/hardware/status", "OLED/串口显示待复习数、待掌握错题数、专注状态"],
       ["H6", "通用消息下发（预留）", "esp32.notify_esp32(task, message)", "可扩展打卡、考试倒计时提醒"]],
      widths=[700, 2100, 3800, 2760])
p("说明：固件与服务端接口均已实现并通过自动化验证；本机无 ESP32 开发板，LED/蜂鸣器的物理表现与 WiFi 连通性未做实机联调，答辩时如实说明。")

h2("6.6 新增数据实体")
table(["数据实体", "主要字段", "说明"],
      [["FocusSession", "id, minutes, course_id, note, created_at", "一次专注记录，用于今日专注分钟与最近记录"],
       ["Setting（扩展）", "key, value（focus_active / focus_since）", "专注状态与起始时间，供硬件看板读取"]],
      widths=[2000, 3960, 3400])

h2("6.7 增量验收标准")
table(["编号", "验收项", "可测标准"],
      [["A11", "深浅色跟随系统", "切换操作系统主题时页面自动跟随；手动三档与主题色刷新后保持"],
       ["A12", "语音输入", "支持的浏览器中点击麦克风可将语音转为文字填入输入框"],
       ["A13", "文件上传", "txt/md/docx 上传成功并进入课程记忆；非法类型返回 400；超 2 MB 被拒绝"],
       ["A14", "错题导出", "GET 导出接口返回 Markdown 附件且 Content-Disposition 正确"],
       ["A15", "概览与番茄钟", "统计数字与数据库一致；专注记录可写入并在看板中反映专注状态"],
       ["A16", "硬件状态看板", "GET /api/hardware/status 返回待复习数、待掌握错题数、专注状态与可读 display 文本"]],
      widths=[900, 2200, 6260])
p("实测结果（2026-11-05，目标 http://localhost:5000，真实 HTTP 请求）：原有回归 26/26 个请求状态正确、30/30 项业务断言通过；"
  "新增功能 19/19 项断言通过；全量 Python 源码编译通过；无头浏览器深/浅色渲染截图 5 张，人工复核无重叠、乱码与裁切。"
  "数据留存于 docs/demo_results.json、docs/feature_results.json 与 docs/演示验收报告.md。")

# ================= 打包 =================
document_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               f'<w:document {NS}><w:body>' + "".join(body) +
               '<w:sectPr><w:pgSz w:w="11906" w:h="16838"/>'
               '<w:pgMar w:top="1440" w:bottom="1440" w:left="1440" w:right="1440"/></w:sectPr>'
               '</w:body></w:document>')

styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:eastAsia="SimSun" w:hAnsi="Calibri"/></w:rPr></w:rPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:sz w:val="21"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:jc w:val="center"/><w:rPr><w:b/><w:sz w:val="40"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="H1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="30"/><w:color w:val="2F6FED"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="H2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="26"/><w:color w:val="1F4FC0"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="H3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:rPr><w:b/><w:sz w:val="23"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:ind w:left="420"/><w:rPr><w:sz w:val="21"/></w:rPr></w:style>
</w:styles>'''

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Default Extension="svg" ContentType="image/svg+xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>'''

root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

# 文档关系：styles + 图片
doc_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '<Relationship Id="rIdStyles" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>']
rid_counter = 100
for rid, target, rtype, _ in RELATIONS:
    doc_rels.append(f'<Relationship Id="{rid}" Type="{rtype}" Target="{target}"/>')
doc_rels.append('</Relationships>')
doc_rels_xml = "".join(doc_rels)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", root_rels)
    z.writestr("word/document.xml", document_xml)
    z.writestr("word/styles.xml", styles_xml)
    z.writestr("word/_rels/document.xml.rels", doc_rels_xml)
    for name, data in MEDIA:
        z.writestr(f"word/media/{name}", data)

print("生成成功：", OUT, "大小", os.path.getsize(OUT), "字节")
print("嵌入媒体：", [m[0] for m in MEDIA])
