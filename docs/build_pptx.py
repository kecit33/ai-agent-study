# -*- coding: utf-8 -*-
"""手写 OOXML 生成《AI 校园学习陪伴助手》答辩 PPT（16:9）。
嵌入 SVG 矢量图（项目标志/思维导图/架构图/类图），并附 1x1 PNG 兜底以保证兼容。
"""
import os, zipfile, base64, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "AI校园学习陪伴助手_答辩.pptx")
SLIDE_W, SLIDE_H = 12192000, 6858000

NS = ('xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
      'xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/svg"')

def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))

def pt(sz): return int(sz * 100)

# 1x1 透明 PNG 兜底
PNG1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42tNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")

# ---------- 文本工具 ----------
def run(text, sz=18, bold=False, color="1F2733"):
    b = ' b="1"' if bold else ''
    return (f'<a:r><a:rPr lang="zh-CN" sz="{pt(sz)}"{b}><a:solidFill>'
            f'<a:srgbClr val="{color}"/></a:solidFill></a:rPr>'
            f'<a:t>{esc(text)}</a:t></a:r>')

def para(runs, align="l", bullet=False, space_after=600):
    if isinstance(runs, str):
        runs = [run(runs)]
    bp = f'<a:pPr algn="{align}">' + ('<a:buChar char="•"/>' if bullet else '') + f'<a:spcBef><a:spcPts val="{space_after}"/></a:spcBef></a:pPr>'
    return f'<a:p>{bp}' + ''.join(runs) + '</a:p>'

def textbox(idn, x, y, w, h, paragraphs, anchor="t", fill=None):
    fillxml = f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>' if fill else '<a:noFill/>'
    body = ''.join(paragraphs) if isinstance(paragraphs, list) else paragraphs
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{idn}" name="tb{idn}"/>'
            f'<p:cNvSpPr txBox="1"/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>{fillxml}'
            f'<a:ln><a:noFill/></a:ln></p:spPr>'
            f'<p:txBody><a:bodyPr wrap="square" lIns="91440" tIns="45720" rIns="91440" bIns="45720" anchor="{anchor}"/>'
            f'<a:lstStyle/>{body}</p:txBody></p:sp>')

def rect(idn, x, y, w, h, fill, line=None):
    linexml = f'<a:ln><a:solidFill><a:srgbClr val="{line}"/></a:solidFill><a:w val="12700"/></a:ln>' if line else '<a:ln><a:noFill/></a:ln>'
    return (f'<p:sp><p:nvSpPr><p:cNvPr id="{idn}" name="r{idn}"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr>'
            f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
            f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            f'<a:solidFill><a:srgbClr val="{fill}"/></a:solidFill>{linexml}</p:spPr>'
            f'<p:txBody><a:bodyPr/><a:lstStyle/><a:p/></p:txBody></p:sp>')

# ---------- 图片 ----------
media = []   # (name, bytes)
img_rels = []  # per slide: list of (rid, target, type, contenttype, bytes)
def picture(idn, x, y, w, h, svg_bytes, name):
    rid_i = f"rIdImg_{name}"
    rid_p = f"rIdPng_{name}"
    media.append((name + ".svg", svg_bytes))
    media.append((name + ".png", PNG1x1))
    # 返回 pic xml，并把关系登记到全局，最后按 slide 聚合
    pic = (f'<p:pic><p:nvPicPr><p:cNvPr id="{idn}" name="{name}"/><p:cNvPicPr/><p:nvPr/></p:nvPicPr>'
           f'<p:blipFill><a:blip r:embed="{rid_i}"><a:extLst>'
           f'<a:ext uri="{{96DAC541-7B7A-43D3-8B79-8D1A8339B2E1}}">'
           f'<asvg:svgBlip r:embed="{rid_p}"/></a:ext></a:extLst></a:blip>'
           f'<a:stretch><a:fillRect/></a:stretch></p:blipFill>'
           f'<p:spPr><a:xfrm><a:off x="{x}" y="{y}"/><a:ext cx="{w}" cy="{h}"/></a:xfrm>'
           f'<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></p:spPr></p:pic>')
    return pic, [(rid_i, name + ".svg", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "image/svg+xml", svg_bytes),
                (rid_p, name + ".png", "http://schemas.openxmlformats.org/officeDocument/2006/relationships/image", "image/png", PNG1x1)]

# ---------- 读取 SVG ----------
def read_svg(n):
    return open(os.path.join(HERE, n + ".svg"), "rb").read()

# 各页关系登记
slide_defs = []  # (slide_xml, [ (rid, target, type, ct, bytes) ])

def make_slide(inner_xml, rels_extra):
    # inner_xml 为 spTree 内容（不含 <p:spTree> 标签）
    sld = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           f'<p:sld {NS}><p:cSld><p:spTree>'
           f'<p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
           f'<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
           + inner_xml +
           '</p:spTree></p:cSld><p:clrMapOvr><a:overrideClrMapping '
           'bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" '
           'accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" '
           'hlink="hlink" folHlink="folHlink"/></p:clrMapOvr></p:sld>')
    # 关系：layout + 图片
    rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>']
    rid = 2
    for (rid_i, target, typ, ct, _b) in rels_extra:
        rels.append(f'<Relationship Id="{rid_i}" Type="{typ}" Target="../media/{target}"/>')
    rels.append('</Relationships>')
    slide_defs.append((sld, rels_extra, "".join(rels)))

def bg(hexcol):
    return (f'<p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>')

TITLE_Y = 350000
TITLE_H = 900000

# ===================== 各页 =====================
# ---- 01 封面 ----
cover_inner = (
    rect(2, 0, 0, SLIDE_W, SLIDE_H, "2F6FED") +
    textbox(3, 1500000, 2300000, 9192000, 1200000,
            [para([run("AI 校园学习陪伴助手", 54, True, "FFFFFF")], align="ctr")], anchor="ctr") +
    textbox(4, 1500000, 3650000, 9192000, 700000,
            [para([run("基于大模型智能体的校园学习 Web 应用", 22, False, "E8F0FF")], align="ctr")], anchor="ctr") +
    textbox(5, 1500000, 4800000, 9192000, 500000,
            [para([run("第 X 开发组（占位）   ·   课程作业答辩   ·   2026-11-09", 18, False, "FFFFFF")], align="ctr")], anchor="ctr")
)
make_slide(cover_inner, [])

# ---- 02 团队展示 ----
def card(idn, x, title, lines, members):
    w = 2600000; h = 3600000; y = 1500000
    inner = (rect(idn, x, y, w, h, "EAF1FF", "2F6FED") +
             textbox(idn+1, x+120000, y+200000, w-240000, 500000, [para([run(title, 22, True, "2F6FED")], align="ctr")], anchor="ctr") +
             textbox(idn+2, x+120000, y+800000, w-240000, 2000000, [para([run(l, 16, False, "41506A")]) for l in lines]) +
             textbox(idn+3, x+120000, y+3000000, w-240000, 500000, [para([run(members, 14, False, "6B7686")], align="ctr")], anchor="ctr"))
    return inner

team_inner = (
    textbox(2, 600000, TITLE_Y, 8000000, TITLE_H, [para([run("团队展示", 36, True, "1F2733")])]) +
    card(3, 600000, "产品经理", ["需求调研 · 文档撰写", "答辩统筹"], "成员：____（占位）") +
    card(9, 3400000, "前端开发", ["原生 HTML/CSS/JS", "九模块 + 深浅色主题"], "成员：____（占位）") +
    card(15, 6200000, "后端开发", ["Flask · 智能体可插拔", "课程记忆 · 错题闭环"], "成员：____（占位）") +
    card(21, 9000000, "测试与部署", ["验收标准 · 上线", "硬件联动"], "成员：____（占位）")
)
make_slide(team_inner, [])

# ---- 03 选题报告 ----
pain = (
    rect(2, 600000, 1500000, 5500000, 4600000, "FFF3F0", "FFD9CF") +
    rect(8, 6300000, 1500000, 5500000, 4600000, "EAF7EF", "B6E3C8") +
    textbox(3, 800000, 1650000, 5100000, 500000, [para([run("真实调研痛点", 22, True, "C0392B")])]) +
    textbox(4, 800000, 2200000, 5100000, 3800000, [para([run(t, 17, False, "41506A")], bullet=True) for t in [
        "笔记零散、课件看不懂，缺复习提纲", "作业遇难题缺引导式讲解，易抄答案",
        "考前不会规划复习、难整理考点", "通用大模型不懂本校课程重点",
        "缺背诵自测与错题整理一体化工具"]]) +
    textbox(9, 6500000, 1650000, 5100000, 500000, [para([run("选题价值", 22, True, "1AA260")])]) +
    textbox(10, 6500000, 2200000, 5100000, 3800000, [para([run(t, 17, False, "41506A")], bullet=True) for t in [
        "垂直课程场景，比通用 AI 更聚焦", "杀手级功能：课程记忆 + 错题闭环",
        "浏览器即用，使用门槛低", "可上线运行，师生直接验收",
        "预留硬件联动，争取加分"]])
)
make_slide(pain, [])

# ---- 04 功能思维导图 ----
pic4, r4 = picture(2, 1400000, 1300000, 9400000, 5200000, read_svg("mindmap"), "mindmap")
mm_inner = (textbox(1, 600000, TITLE_Y, 9000000, TITLE_H, [para([run("需求分析：功能思维导图", 32, True, "1F2733")])]) + pic4)
make_slide(mm_inner, r4)

# ---- 05 系统架构与技术栈 ----
pic5, r5 = picture(3, 500000, 1400000, 7200000, 4700000, read_svg("architecture"), "architecture")
arch_inner = (
    textbox(1, 600000, TITLE_Y, 9000000, TITLE_H, [para([run("需求分析：系统架构与技术栈", 32, True, "1F2733")])]) +
    pic5 +
    rect(9, 8000000, 1500000, 3800000, 4600000, "F5F8FF", "CDD9EE") +
    textbox(10, 8150000, 1650000, 3500000, 500000, [para([run("技术栈", 20, True, "2F6FED")])]) +
    textbox(11, 8150000, 2200000, 3500000, 3800000, [para([run(t, 16, False, "41506A")]) for t in [
        "前端：原生 HTML/CSS/JS", "后端：标准库 / Flask 双入口", "存储：SQLite",
        "智能体：GPT/文心/Kimi/Claude 可插拔", "部署：Render / PythonAnywhere",
        "硬件：ESP32（可选）"]])
)
make_slide(arch_inner, r5)

# ---- 06 核心功能 ----
core_inner = (
    textbox(2, 600000, TITLE_Y, 9000000, TITLE_H, [para([run("核心功能：杀手级能力", 36, True, "1F2733")])]) +
    rect(3, 600000, 1500000, 5500000, 4600000, "EAF1FF", "2F6FED") +
    textbox(4, 820000, 1700000, 5100000, 500000, [para([run("课程记忆智能体", 24, True, "2F6FED")])]) +
    textbox(5, 820000, 2300000, 5100000, 3600000, [para([run(t, 18, False, "41506A")]) for t in [
        "为每门课上传资料，智能体绑定该课程上下文；",
        "之后所有问答严格限定在已上传资料范围内，",
        "避免答非所问、超纲跑偏；",
        "切换课程自动切换记忆上下文。"]]) +
    rect(9, 6300000, 1500000, 5500000, 4600000, "EAF7EF", "1AA260") +
    textbox(10, 6520000, 1700000, 5100000, 500000, [para([run("AI 错题本与定向出题", 24, True, "1AA260")])]) +
    textbox(11, 6520000, 2300000, 5100000, 3600000, [para([run(t, 18, False, "41506A")]) for t in [
        "录入错题，智能体分析错误原因；",
        "一段时间后自动生成同类变式题用于自测，",
        "定向巩固薄弱知识点，",
        "形成「提问—做题—错题归档—定向复习」闭环。"]])
)
make_slide(core_inner, [])

# ---- 07 类图 ----
pic7, r7 = picture(2, 2200000, 1300000, 8000000, 5200000, read_svg("classdiagram"), "classdiagram")
cls_inner = (textbox(1, 600000, TITLE_Y, 9000000, TITLE_H, [para([run("需求分析：系统类图", 32, True, "1F2733")])]) + pic7)
make_slide(cls_inner, r7)

# ---- 08 创新点与交付 ----
deliv_inner = (
    textbox(2, 600000, TITLE_Y, 9000000, TITLE_H, [para([run("创新点与交付", 36, True, "1F2733")])]) +
    rect(3, 600000, 1500000, 3700000, 4600000, "F5F8FF", "CDD9EE") +
    textbox(4, 800000, 1650000, 3300000, 500000, [para([run("创新点", 20, True, "2F6FED")])]) +
    textbox(5, 800000, 2200000, 3300000, 3800000, [para([run(t, 16, False, "41506A")]) for t in [
        "场景垂直：聚焦校内课程", "带长期记忆的智能体", "闭环学习（提问-做题-错因-定向复习）"]]) +
    rect(9, 4500000, 1500000, 3500000, 4600000, "FFF7EC", "FFE0B0") +
    textbox(10, 4700000, 1650000, 3100000, 500000, [para([run("进度与验收", 20, True, "E08A00")])]) +
    textbox(11, 4700000, 2200000, 3100000, 3800000, [para([run(t, 16, False, "41506A")]) for t in [
        "五阶段已完成至 V1.2", "24 项验收标准全部可测", "无密钥演示模式保证可跑通"]]) +
    rect(15, 8300000, 1500000, 3500000, 4600000, "EAF7EF", "B6E3C8") +
    textbox(16, 8500000, 1650000, 3100000, 500000, [para([run("部署", 20, True, "1AA260")])]) +
    textbox(17, 8500000, 2200000, 3100000, 3800000, [para([run(t, 16, False, "41506A")]) for t in [
        "本地：零依赖一键启动", "云端：Render / PythonAnywhere", "生成可访问链接供师生验收"]])
)
make_slide(deliv_inner, [])


# ---- 09 V1.1 体验增强 ----
enh_inner = (
    textbox(2, 600000, TITLE_Y, 9000000, TITLE_H, [para([run("V1.1 体验增强：更好用", 36, True, "1F2733")])]) +
    rect(3, 600000, 1500000, 5500000, 4600000, "EAF1FF", "2F6FED") +
    textbox(4, 820000, 1700000, 5100000, 500000, [para([run("外观与陪伴", 24, True, "2F6FED")])]) +
    textbox(5, 820000, 2300000, 5100000, 3600000, [para([run(t, 18, False, "41506A")]) for t in [
        "跟随系统深/浅色，可手动三档切换",
        "6 套主题色 + 自定义主色，本地保存",
        "学习概览：掌握率 / 今日专注 / 待复习",
        "番茄钟：自定义时长，到点声光提醒",
        "10 个模块，URL hash 一键直达"]]) +
    rect(9, 6300000, 1500000, 5500000, 4600000, "EAF7EF", "1AA260") +
    textbox(10, 6520000, 1700000, 5100000, 500000, [para([run("输入与文件", 24, True, "1AA260")])]) +
    textbox(11, 6520000, 2300000, 5100000, 3600000, [para([run(t, 18, False, "41506A")]) for t in [
        "语音输入：5 处输入框，说话即成文",
        "课件上传：txt / md / docx 自动解析",
        "上传即入课程记忆，问答直接引用",
        "错题本一键导出 Markdown",
        "类型白名单 + 2 MB 上限 + 400 拦截"]])
)
make_slide(enh_inner, [])

# ---- 10 硬件双向联动与验收数据 ----
hw_inner = (
    textbox(2, 600000, TITLE_Y, 10000000, TITLE_H, [para([run("硬件双向联动 · 真实验收数据", 34, True, "1F2733")])]) +
    rect(3, 600000, 1500000, 6900000, 4600000, "FFF7EC", "FFE0B0") +
    textbox(4, 820000, 1700000, 6500000, 500000, [para([run("ESP32 共 6 个交互点", 22, True, "E08A00")])]) +
    textbox(5, 820000, 2300000, 6500000, 3600000, [para([run(t, 17, False, "41506A")]) for t in [
        "下行：复习任务到点 / 手动测试 / 番茄钟到点 → LED + 蜂鸣器",
        "下行：专注状态灯 → 专注中 LED 常亮，结束熄灭",
        "上行：每 60s 轮询学习状态看板（待复习 / 待掌握 / 专注中）",
        "预留：通用消息下发，可扩展打卡与考试倒计时",
        "未接硬件不影响任何主体功能；实机联调待补（如实说明）"]]) +
    rect(9, 7700000, 1500000, 4100000, 4600000, "EAF1FF", "2F6FED") +
    textbox(10, 7900000, 1700000, 3700000, 500000, [para([run("真实验收", 22, True, "2F6FED")])]) +
    textbox(11, 7900000, 2300000, 3700000, 3600000, [para([run(t, 18, False, "41506A")]) for t in [
        "26 / 26  HTTP 请求状态正确",
        "30 / 30  原业务断言通过",
        "19 / 19  V1.1 功能断言通过",
        "36 / 36  V1.2 自测断言通过",
        "公网链接可直接验收"]])
)
make_slide(hw_inner, [])

# ---- 11 V1.2 学科资源包与模型接入 ----
v12_inner = (
    textbox(2, 600000, TITLE_Y, 10500000, TITLE_H,
            [para([run("V1.2 学科资源包 + 模型接入接口", 32, True, "1F2733")])]) +
    rect(3, 600000, 1500000, 5500000, 4600000, "EAF1FF", "2F6FED") +
    textbox(4, 820000, 1700000, 5100000, 500000,
            [para([run("以「数学 → 高等数学上册」为例", 22, True, "2F6FED")])]) +
    textbox(5, 820000, 2300000, 5100000, 3600000, [para([run(t, 17, False, "41506A")]) for t in [
        "28 道带标准答案与解析的分章自测题",
        "单章 / 全册复习总结：知识点 + 公式 + 易错点",
        "8 千字专题文章 + 8 项教材/课程资料清单",
        "42 节点思维导图（SVG 跟随深浅色）",
        "一键全套 · Markdown 导出 · 回写课程记忆"]]) +
    rect(9, 6300000, 1500000, 5500000, 4600000, "EAF7EF", "1AA260") +
    textbox(10, 6520000, 1700000, 5100000, 500000,
            [para([run("文心一言 / Kimi 即填即用", 22, True, "1AA260")])]) +
    textbox(11, 6520000, 2300000, 5100000, 3600000, [para([run(t, 17, False, "41506A")]) for t in [
        "设置页或 REST 写入 Key，立即生效免重启",
        "文心：千帆 v2 / 旧版 OAuth 双模式适配",
        "Kimi / GPT / 自定义 OpenAI 兼容端点统一",
        "/api/agent/complete 供自建系统直接调用",
        "连通性测试 + 失败自动降级，密钥仅显示掩码"]])
)
make_slide(v12_inner, [])

# ===================== 打包 =====================
n_slides = len(slide_defs)
# presentation
sldIdLst = "".join(
    f'<p:sldId id="{256+i}" r:id="rId{i+2}"/>' for i in range(n_slides))
presentation = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<p:presentation xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" saveSubsetFonts="1">'
    f'<p:sldMasterIdLst><p:sldMasterId id="2147483648" r:id="rId1"/></p:sldMasterIdLst>'
    f'<p:sldIdLst>{sldIdLst}</p:sldIdLst>'
    '<p:sldSz cx="12192000" cy="6858000" type="screen16x9"/>'
    '<p:notesSz cx="6858000" cy="9144000"/></p:presentation>')

pres_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>']
for i in range(n_slides):
    pres_rels.append(f'<Relationship Id="rId{i+2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide{i+1}.xml"/>')
pres_rels.append('</Relationships>')

master = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<p:sldMaster xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
    '<p:cSld><p:bg><p:bgRef idx="1001"><a:schemeClr val="bg1"/></p:bgRef></p:bg>'
    '<p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
    '</p:spTree></p:cSld>'
    '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
    'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>'
    '<p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>'
    '<p:txStyles><p:titleStyle><a:lvl1pPr><a:defRPr sz="4400"/></a:lvl1pPr></p:titleStyle>'
    '<p:bodyStyle><a:lvl1pPr><a:defRPr sz="1800"/></a:lvl1pPr></p:bodyStyle>'
    '<p:otherStyle/></p:txStyles></p:sldMaster>')
master_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>'
    '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>'
    '</Relationships>')

layout = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<p:sldLayout xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main" '
    'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" type="blank" preserve="1">'
    '<p:cSld name="Blank"><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>'
    '<p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>'
    '</p:spTree></p:cSld>'
    '<p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" '
    'accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/></p:sldLayout>')
layout_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>'
    '</Relationships>')

theme = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme">'
    '<a:themeElements><a:clrScheme name="Office">'
    '<a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
    '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1>'
    '<a:dk2><a:srgbClr val="1F2733"/></a:dk2><a:lt2><a:srgbClr val="EAF1FF"/></a:lt2>'
    '<a:accent1><a:srgbClr val="2F6FED"/></a:accent1><a:accent2><a:srgbClr val="1AA260"/></a:accent2>'
    '<a:accent3><a:srgbClr val="E08A00"/></a:accent3><a:accent4><a:srgbClr val="5B8DEF"/></a:accent4>'
    '<a:accent5><a:srgbClr val="C0392B"/></a:accent5><a:accent6><a:srgbClr val="6B7686"/></a:accent6>'
    '<a:hlink><a:srgbClr val="2F6FED"/></a:hlink><a:folHlink><a:srgbClr val="1F4FC0"/></a:folHlink>'
    '</a:clrScheme>'
    '<a:fontScheme name="Office"><a:majorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>'
    '<a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont></a:fontScheme>'
    '<a:fmtScheme name="Office"><a:fillStyleLst>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:fillStyleLst>'
    '<a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
    '<a:ln w="19050"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst>'
    '<a:effectStyleLst><a:effectStyle><a:effectLst/></a:effectStyle>'
    '<a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle></a:effectStyleLst>'
    '<a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
    '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:bgFillStyleLst>'
    '</a:fmtScheme></a:themeElements></a:theme>')

content_types = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '<Default Extension="png" ContentType="image/png"/>'
    '<Default Extension="svg" ContentType="image/svg+xml"/>'
    '<Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>'
    '<Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>'
    '<Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>'
    '<Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>'
    + "".join(f'<Override PartName="/ppt/slides/slide{i+1}.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>' for i in range(n_slides))
    + '</Types>')

root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>'
    '</Relationships>')

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", root_rels)
    z.writestr("ppt/presentation.xml", presentation)
    z.writestr("ppt/_rels/presentation.xml.rels", "".join(pres_rels))
    z.writestr("ppt/slideMasters/slideMaster1.xml", master)
    z.writestr("ppt/slideMasters/_rels/slideMaster1.xml.rels", master_rels)
    z.writestr("ppt/slideLayouts/slideLayout1.xml", layout)
    z.writestr("ppt/slideLayouts/_rels/slideLayout1.xml.rels", layout_rels)
    z.writestr("ppt/theme/theme1.xml", theme)
    for i, (sld, rels_extra, rels_xml) in enumerate(slide_defs):
        z.writestr(f"ppt/slides/slide{i+1}.xml", sld)
        z.writestr(f"ppt/slides/_rels/slide{i+1}.xml.rels", rels_xml)
    # media
    seen = set()
    for name, data in media:
        if name in seen:
            continue
        seen.add(name)
        z.writestr(f"ppt/media/{name}", data)

print("生成成功：", OUT, os.path.getsize(OUT), "字节，共", n_slides, "页")
