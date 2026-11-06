# -*- coding: utf-8 -*-
"""由 Markdown 单一源生成《软件需求规格说明书》.docx。

用法：python docs/build_docx.py

- 内容源：docs/软件需求规格说明书.md（可直接导入语雀 / 腾讯文档协作）
- 结构：GB/T 9385-2008 / GB/T 8567-2006（引言、总体描述、具体需求、验收标准、附录）
- 封面 + 静态目录 + 正文；表格自适应列宽；嵌入 SVG 矢量图并附 PNG 兜底
- 直接手写 OOXML，零第三方依赖；不改动 Markdown 之外的内容源
"""
import os
import re
import zipfile
import base64
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "软件需求规格说明书.md")
OUT = os.path.join(HERE, "软件需求规格说明书.docx")

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"')

TABLE_W = 9360  # A4 + 2cm 边距下的可用宽度（twips）

PNG1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42tNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


# ---------------- 行内渲染（**粗体** / `代码`） ----------------
TOKEN_RE = re.compile(r'(\*\*[^*]+\*\*|`[^`]+`)')


def runs_xml(text, color=None, italic=False, force_code=False):
    """把一段 Markdown 行内文本转成若干 <w:r>。"""
    out = []
    pieces = [(text, 'code')] if force_code else TOKEN_RE.split(text)
    for piece in pieces:
        if not piece:
            continue
        if isinstance(piece, tuple):
            piece, style = piece
        else:
            style = 'code' if force_code else None
        if not piece:
            continue
        if style is None and piece.startswith('**') and piece.endswith('**') and len(piece) > 4:
            style, piece = 'b', piece[2:-2]
        elif style is None and piece.startswith('`') and piece.endswith('`') and len(piece) > 2:
            style, piece = 'code', piece[1:-1]
        rpr = []
        if color:
            rpr.append(f'<w:color w:val="{color}"/>')
        if italic:
            rpr.append('<w:i/>')
        if style == 'b':
            rpr.append('<w:b/>')
        if style == 'code':
            rpr.insert(0, '<w:rFonts w:ascii="Consolas" w:eastAsia="Consolas" w:hAnsi="Consolas"/>')
            rpr.append('<w:sz w:val="19"/>')
            rpr.append('<w:shd w:val="clear" w:color="auto" w:fill="EEF2F8"/>')
        rpr_xml = f'<w:rPr>{"".join(rpr)}</w:rPr>' if rpr else ''
        out.append(f'<w:r>{rpr_xml}<w:t xml:space="preserve">{esc(piece)}</w:t></w:r>')
    return "".join(out) or f'<w:r><w:t xml:space="preserve"></w:t></w:r>'


# ---------------- 段落构建 ----------------
body = []
RELATIONS = []      # (rid, target, type)
MEDIA = []          # (name, bytes)
_docpr_id = [10]


def para(text, style=None, align=None, color=None, italic=False,
         shade=None, indent=None, spacing_after=120, force_code=False):
    ppr = []
    if style:
        ppr.append(f'<w:pStyle w:val="{style}"/>')
    if shade:
        ppr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>')
    if indent is not None:
        ppr.append(f'<w:ind w:left="{indent}"/>')
    if align:
        ppr.append(f'<w:jc w:val="{align}"/>')
    ppr.append(f'<w:spacing w:after="{spacing_after}"/>')
    body.append(f'<w:p><w:pPr>{"".join(ppr)}</w:pPr>'
                f'{runs_xml(text, color=color, italic=italic, force_code=force_code)}</w:p>')


def heading(text, level):
    style = {1: "H1", 2: "H2", 3: "H3"}[level]
    body.append(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr>'
                f'<w:r><w:t xml:space="preserve">{esc(text)}</w:t></w:r></w:p>')


def display_width(s):
    """估算字符串显示宽度：CJK 记 2，ASCII 记 1。"""
    return sum(2 if ord(c) > 0x2E80 else 1 for c in re.sub(r'\*\*|`', '', s))


def table(headers, rows, row_idx=[0]):
    n = len(headers)
    if not rows:
        return
    weights = []
    for i in range(n):
        cells = [headers[i]] + [r[i] for r in rows if i < len(r)]
        weights.append(max(6, min(max(display_width(c) for c in cells), 62)))
    total = sum(weights)
    min_w = 560
    widths = [max(min_w, int(TABLE_W * w / total)) for w in weights]
    overflow = sum(widths) - TABLE_W
    if overflow > 0:
        for j in sorted(range(n), key=lambda k: -widths[k]):
            take = min(overflow, widths[j] - min_w)
            widths[j] -= take
            overflow -= take
            if overflow <= 0:
                break
    widths[-1] += TABLE_W - sum(widths)

    def cell(text, w, header=False, fill=None):
        shd = f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>' if fill else ''
        color = "FFFFFF" if header else None
        return (f'<w:tc><w:tcPr><w:tcW w:w="{w}" w:type="dxa"/>{shd}'
                f'<w:vAlign w:val="center"/></w:tcPr>'
                f'<w:p><w:pPr><w:spacing w:before="40" w:after="40"/></w:pPr>'
                f'{runs_xml(text, color=color)}</w:p></w:tc>')

    trh = ('<w:tr><w:trPr><w:tblHeader/></w:trPr>'
           + ''.join(cell(h, widths[i], header=True, fill="2F6FED")
                     for i, h in enumerate(headers)) + '</w:tr>')
    trs = []
    for k, r in enumerate(rows):
        fill = "F5F8FE" if k % 2 == 1 else None
        cells = [(r[i] if i < len(r) else "") for i in range(n)]
        trs.append('<w:tr><w:trPr><w:cantSplit/></w:trPr>'
                   + ''.join(cell(c, widths[i], fill=fill) for i, c in enumerate(cells))
                   + '</w:tr>')
        row_idx[0] += 1
    borders = ''.join(
        f'<w:{e} w:val="single" w:sz="4" w:space="0" w:color="B7C6DF"/>'
        for e in ["top", "left", "bottom", "right", "insideH", "insideV"])
    grid = "".join('<w:gridCol w:w="%d"/>' % w for w in widths)
    body.append(
        f'<w:tbl><w:tblPr><w:tblW w:w="{TABLE_W}" w:type="dxa"/>'
        f'<w:tblBorders>{borders}</w:tblBorders>'
        f'<w:tblCellMar><w:top w:w="60" w:type="dxa"/><w:left w:w="90" w:type="dxa"/>'
        f'<w:bottom w:w="60" w:type="dxa"/><w:right w:w="90" w:type="dxa"/></w:tblCellMar>'
        f'</w:tblPr><w:tblGrid>{grid}</w:tblGrid>'
        + trh + ''.join(trs) + '</w:tbl><w:p/>')


def image(name, emu_w=5486400):
    svg_path = os.path.join(HERE, name)
    with open(svg_path, "rb") as f:
        svg_bytes = f.read()
    head = svg_bytes[:600].decode("utf-8", "ignore")
    mw = re.search(r'\bwidth="(\d+(?:\.\d+)?)"', head)
    mh = re.search(r'\bheight="(\d+(?:\.\d+)?)"', head)
    if not (mw and mh):
        vb = re.search(r'viewBox="0\s+0\s+([\d.]+)\s+([\d.]+)"', head)
        w_px, h_px = (float(vb.group(1)), float(vb.group(2))) if vb else (960.0, 600.0)
    else:
        w_px, h_px = float(mw.group(1)), float(mh.group(1))
    emu_h = int(emu_w * h_px / w_px)
    rid_svg = "rId_" + name.replace(".", "_") + "_svg"
    rid_png = "rId_" + name.replace(".", "_") + "_png"
    did = _docpr_id[0]
    _docpr_id[0] += 1
    drawing = f'''<w:p><w:pPr><w:jc w:val="center"/></w:pPr><w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"
      xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
      xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"
      xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"
      xmlns:asvg="http://schemas.microsoft.com/office/drawing/2016/svg">
      <wp:extent cx="{emu_w}" cy="{emu_h}"/><wp:effectExtent l="0" t="0" r="0" b="0"/>
      <wp:docPr id="{did}" name="{esc(name)}"/><wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>
      <a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
        <pic:pic><pic:nvPicPr><pic:cNvPr id="{did}" name="{esc(name)}"/><pic:cNvPicPr/></pic:nvPicPr>
        <pic:blipFill><a:blip r:embed="{rid_svg}">
          <a:extLst><a:ext uri="{{96DAC541-7B7A-43D3-8B79-8D1A8339B2E1}}">
            <asvg:svgBlip r:embed="{rid_png}"/></a:ext></a:extLst></a:blip>
          <a:stretch><a:fillRect/></a:stretch></pic:blipFill>
        <pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu_w}" cy="{emu_h}"/></a:xfrm>
          <a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>
      </a:graphicData></a:graphic></wp:inline></w:drawing></w:r></w:p>'''
    body.append(drawing)
    RELATIONS.append((rid_svg, f"media/{name}", "image/svg+xml"))
    RELATIONS.append((rid_png, f"media/{name}.png", "image/png"))
    MEDIA.append((name, svg_bytes))
    MEDIA.append((name + ".png", PNG1x1))


def page_break():
    body.append('<w:p><w:r><w:br w:type="page"/></w:r></w:p>')


# ---------------- Markdown 解析 ----------------
with open(SRC, "r", encoding="utf-8") as f:
    lines = f.read().lstrip("\ufeff").splitlines()

# 先收集标题，用于生成静态目录（不依赖 Word 域更新）
toc = []
for ln in lines:
    m = re.match(r'^(#{2,3})\s+(.+)$', ln)
    if m:
        toc.append((len(m.group(1)), re.sub(r'\*\*|`', '', m.group(2)).strip()))

# 封面
title_text = lines[0].lstrip('# ').strip()
body.append(f'<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr>'
            f'<w:r><w:t xml:space="preserve">{esc(title_text)}</w:t></w:r></w:p>')

i = 1
cover_done = False
in_fence = False
fence_buf = []
warnings = []


def flush_fence():
    global fence_buf
    for code_line in fence_buf:
        body.append(
            '<w:p><w:pPr><w:shd w:val="clear" w:color="auto" w:fill="F4F6FA"/>'
            '<w:ind w:left="240"/><w:spacing w:after="0"/></w:pPr>'
            + runs_xml(code_line if code_line else " ", force_code=True) + '</w:p>')
    if fence_buf:
        body.append('<w:p/>')
    fence_buf = []


while i < len(lines):
    raw = lines[i]
    ln = raw.rstrip()
    stripped = ln.strip()

    # 代码围栏
    if stripped.startswith('```'):
        if in_fence:
            flush_fence()
            in_fence = False
        else:
            in_fence = True
            fence_buf = []
        i += 1
        continue
    if in_fence:
        fence_buf.append(raw.replace('\t', '    '))
        i += 1
        continue

    # 首个 H1 之前为封面信息块（副标题 / 元信息）
    if not cover_done and re.match(r'^##\s+', ln):
        cover_done = True
        page_break()
        body.append('<w:p><w:pPr><w:pStyle w:val="TOCHead"/></w:pPr>'
                    '<w:r><w:t xml:space="preserve">目　录</w:t></w:r></w:p>')
        for lvl, txt in toc:
            body.append(
                f'<w:p><w:pPr><w:pStyle w:val="TOC{lvl - 1}"/></w:pPr>'
                f'<w:r><w:t xml:space="preserve">{esc(txt)}</w:t></w:r></w:p>')
        page_break()

    # 表格
    if stripped.startswith('|') and stripped.endswith('|'):
        block = []
        while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
            block.append(lines[i].strip())
            i += 1
        parsed = []
        for b in block:
            cells = [c.strip() for c in b.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c or '') for c in cells):
                continue
            parsed.append(cells)
        if parsed:
            n = len(parsed[0])
            for r in parsed:
                if len(r) != n:
                    warnings.append(f"表格列数不一致：期望 {n}，实际 {len(r)}：{r[:3]}")
                while len(r) < n:
                    r.append("")
                del r[n:]
            table(parsed[0], parsed[1:])
        continue

    # 图片
    m = re.match(r'^!\[([^\]]*)\]\(([^)]+)\)\s*$', stripped)
    if m:
        fname = m.group(2)
        if not os.path.exists(os.path.join(HERE, fname)):
            warnings.append(f"图片不存在：{fname}")
        else:
            image(fname, emu_w=5800000)
        i += 1
        continue

    # 标题
    m = re.match(r'^(#{1,4})\s+(.+)$', ln)
    if m:
        lvl = len(m.group(1))
        if lvl == 1:
            body.append(f'<w:p><w:pPr><w:pStyle w:val="Title"/></w:pPr>'
                        f'<w:r><w:t xml:space="preserve">{esc(m.group(2))}</w:t></w:r></w:p>')
        else:
            heading(re.sub(r'\*\*|`', '', m.group(2)).strip(), lvl - 1)
        i += 1
        continue

    # 引用 / 提示块
    if stripped.startswith('>'):
        text = stripped.lstrip('>').strip()
        para(text, style="Note", shade="F1F6FF", indent=200, italic=False)
        i += 1
        continue

    # 分隔线
    if re.fullmatch(r'-{3,}', stripped):
        body.append('<w:p><w:pPr><w:pBdr><w:bottom w:val="single" w:sz="6" '
                    'w:space="1" w:color="B7C6DF"/></w:pBdr></w:pPr></w:p>')
        i += 1
        continue

    # 列表
    m = re.match(r'^[-*]\s+(.+)$', stripped)
    if m:
        para(m.group(1), style="ListBullet", spacing_after=60)
        i += 1
        continue
    m = re.match(r'^(\d+)\.\s+(.+)$', stripped)
    if m:
        para(m.group(1) + '. ' + m.group(2), style="ListBullet", spacing_after=60)
        i += 1
        continue

    # 空行
    if not stripped:
        i += 1
        continue

    # 普通段落（封面区居中）
    if not cover_done:
        para(stripped, align="center", spacing_after=100)
    else:
        para(stripped)
    i += 1

if in_fence:
    flush_fence()

# ---------------- 打包 ----------------
document_xml = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                f'<w:document {NS}><w:body>' + "".join(body) +
                '<w:sectPr><w:footerReference w:type="default" r:id="rIdFooter"/>'
                '<w:pgSz w:w="11906" w:h="16838"/>'
                '<w:pgMar w:top="1418" w:bottom="1418" w:left="1134" w:right="1134" '
                'w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
                '</w:body></w:document>')

styles_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:eastAsia="Microsoft YaHei" w:hAnsi="Calibri"/><w:sz w:val="21"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:line="300" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:sz w:val="21"/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:jc w:val="center"/><w:spacing w:before="1200" w:after="400"/><w:rPr><w:b/><w:sz w:val="44"/><w:color w:val="1F4FC0"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOCHead"><w:name w:val="TOC Heading"/><w:basedOn w:val="Normal"/><w:jc w:val="center"/><w:spacing w:before="240" w:after="360"/><w:rPr><w:b/><w:sz w:val="32"/><w:color w:val="1F4FC0"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOC1"><w:name w:val="TOC 1"/><w:basedOn w:val="Normal"/><w:spacing w:before="120" w:after="60"/><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="1F2733"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="TOC2"><w:name w:val="TOC 2"/><w:basedOn w:val="Normal"/><w:ind w:left="360"/><w:spacing w:after="40"/><w:rPr><w:sz w:val="20"/><w:color w:val="41506A"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="H1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:keepNext/><w:spacing w:before="360" w:after="180"/><w:pBdr><w:bottom w:val="single" w:sz="8" w:space="4" w:color="2F6FED"/></w:pBdr><w:rPr><w:b/><w:sz w:val="30"/><w:color w:val="2F6FED"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="H2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:keepNext/><w:spacing w:before="260" w:after="120"/><w:rPr><w:b/><w:sz w:val="25"/><w:color w:val="1F4FC0"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="H3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:keepNext/><w:spacing w:before="200" w:after="100"/><w:rPr><w:b/><w:sz w:val="22"/><w:color w:val="2F4D8A"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:ind w:left="420" w:hanging="220"/><w:rPr><w:sz w:val="21"/></w:rPr></w:style>
<w:style w:type="paragraph" w:styleId="Note"><w:name w:val="Note"/><w:basedOn w:val="Normal"/><w:ind w:left="200"/><w:spacing w:before="100" w:after="160"/><w:rPr><w:sz w:val="20"/><w:color w:val="33456B"/></w:rPr></w:style>
</w:styles>'''

footer_xml = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:p><w:pPr><w:jc w:val="center"/></w:pPr>
<w:r><w:rPr><w:sz w:val="18"/><w:color w:val="8A97AB"/></w:rPr><w:t xml:space="preserve">AI 校园学习陪伴助手 · 软件需求规格说明书 V1.5.0　　— 第 </w:t></w:r>
<w:fldSimple w:instr="PAGE"><w:r><w:t>1</w:t></w:r></w:fldSimple>
<w:r><w:rPr><w:sz w:val="18"/><w:color w:val="8A97AB"/></w:rPr><w:t xml:space="preserve"> 页 —</w:t></w:r>
</w:p></w:ftr>'''

content_types = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Default Extension="svg" ContentType="image/svg+xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/footer.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
</Types>'''

root_rels = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

REL_BASE = "http://schemas.openxmlformats.org/officeDocument/2006/relationships/"
doc_rels = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>',
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">',
            f'<Relationship Id="rIdStyles" Type="{REL_BASE}styles" Target="styles.xml"/>',
            f'<Relationship Id="rIdFooter" Type="{REL_BASE}footer" Target="footer.xml"/>']
for rid, target, _ in RELATIONS:
    doc_rels.append(f'<Relationship Id="{rid}" Type="{REL_BASE}image" Target="{target}"/>')
doc_rels.append('</Relationships>')

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", content_types)
    z.writestr("_rels/.rels", root_rels)
    z.writestr("word/document.xml", document_xml)
    z.writestr("word/styles.xml", styles_xml)
    z.writestr("word/footer.xml", footer_xml)
    z.writestr("word/_rels/document.xml.rels", "".join(doc_rels))
    for name, data in MEDIA:
        z.writestr(f"word/media/{name}", data)

print("生成成功：", OUT, "大小", os.path.getsize(OUT), "字节")
print("目录条目：", len(toc), " 嵌入媒体：", [m[0] for m in MEDIA])
if warnings:
    print("警告：")
    for w in warnings:
        print("  -", w)
else:
    print("结构检查：表格列数一致、图片引用全部存在")
print("生成日期：", datetime.date.today().isoformat())
