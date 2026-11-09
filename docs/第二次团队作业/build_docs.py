# -*- coding: utf-8 -*-
"""由 Markdown 单一源生成两份可交付 PDF。

用法：python docs/第二次团队作业/build_docs.py

链路：.md 正文 → 自包含 HTML（图片转 data URI，零外链）→ Chrome / Edge 无头打印 PDF。
改动正文只改 .md 后重跑本脚本；不要直接编辑 PDF 或中间 HTML。
"""
import os
import re
import base64
import html
import shutil
import tempfile
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "assets")

DOCS = [
    ("无言以对_系统设计说明书.md", "无言以对_系统设计说明书.pdf", "系统设计说明书"),
    ("无言以对_数据库设计说明书.md", "无言以对_数据库设计说明书.pdf", "数据库设计说明书"),
]

CSS = """
@page { size: A4; margin: 20mm 18mm 18mm 18mm; }
* { box-sizing: border-box; }
body {
  font-family: "Microsoft YaHei", "PingFang SC", "SimHei", sans-serif;
  font-size: 10.5pt; line-height: 1.75; color: #1F2937; margin: 0;
}
h1 { font-size: 22pt; color: #1B3A78; text-align: center; margin: 0 0 14pt;
     padding-bottom: 10pt; border-bottom: 2.5pt solid #2F6FED; }
h2 { font-size: 15pt; color: #1B3A78; margin: 20pt 0 9pt; padding: 5pt 0 5pt 9pt;
     border-left: 4pt solid #2F6FED; background: #F3F7FF; page-break-after: avoid; }
h3 { font-size: 12.5pt; color: #2F6FED; margin: 14pt 0 7pt; page-break-after: avoid; }
h4 { font-size: 11pt; color: #1B3A78; margin: 11pt 0 5pt; page-break-after: avoid; }
p { margin: 6pt 0; text-align: justify; }
strong { color: #1B3A78; }
code { font-family: Consolas, "Courier New", monospace; font-size: 9pt;
       background: #F1F4F9; padding: 0 2pt; border-radius: 2pt; color: #B03A5B; }
pre { background: #F7F9FC; border: 1px solid #DCE4F0; border-left: 3pt solid #2F6FED;
      border-radius: 4pt; padding: 8pt 10pt; margin: 8pt 0; page-break-inside: avoid;
      white-space: pre-wrap; word-wrap: break-word; font-size: 8.8pt; line-height: 1.5; }
pre code { background: none; padding: 0; color: #243044; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 12pt;
        font-size: 9pt; page-break-inside: auto; }
thead { display: table-header-group; }
tr { page-break-inside: avoid; }
th { background: #2F6FED; color: #FFFFFF; font-weight: bold; text-align: left;
     padding: 5pt 6pt; border: 1px solid #B9CBE9; }
td { padding: 4pt 6pt; border: 1px solid #D5DEEC; vertical-align: top;
     word-wrap: break-word; }
tbody tr:nth-child(even) { background: #F7FAFF; }
blockquote { margin: 8pt 0; padding: 6pt 10pt; background: #FFFBEF;
             border-left: 3pt solid #E0A93B; color: #5B4A22; font-size: 9.5pt; }
ul, ol { margin: 6pt 0 8pt; padding-left: 20pt; }
li { margin: 3pt 0; }
hr { border: none; border-top: 1px solid #D5DEEC; margin: 14pt 0; }
a { color: #2F6FED; text-decoration: none; }
img { display: block; max-width: 100%; height: auto; margin: 8pt auto 2pt;
      border: 1px solid #E3E9F3; page-break-inside: avoid; }
.cap { text-align: center; font-size: 8.8pt; color: #5B6B8C; margin: 0 0 10pt; }
.todo { background: #FFF1DC; color: #A4530B; padding: 0 2pt; border-radius: 2pt;
        font-weight: bold; }
.center { text-align: center; color: #1B3A78; font-size: 11pt; line-height: 1.9; }
.center p { text-align: center; }
.running { position: fixed; bottom: -8mm; left: 0; right: 0; text-align: center;
           font-size: 8pt; color: #8795AE; border-top: 1px solid #D5DEEC; padding-top: 3pt; }
@media print { .running { position: fixed; } }
"""


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', s)
    s = re.sub(r"(【待填写：[^】]*】)", r'<span class="todo">\1</span>', s)
    return s


def image_tag(path, alt):
    full = os.path.join(HERE, path)
    if not os.path.isfile(full):
        return f'<p style="color:#B00020">[缺失图资产] {html.escape(path)}</p>'
    ext = os.path.splitext(full)[1].lower()
    mime = "image/svg+xml" if ext == ".svg" else "image/png"
    with open(full, "rb") as f:
        data = base64.b64encode(f.read()).decode("ascii")
    # 图注统一由正文紧跟的「图 N　...」段落给出，避免重复；alt 仅用于无障碍。
    return f'<img src="data:{mime};base64,{data}" alt="{html.escape(alt)}"/>'


def render(md_text, running_text):
    lines = md_text.split("\n")
    out = [f'<div class="running">{html.escape(running_text)}</div>']
    i = 0
    list_type = None
    in_code = False

    def close_list():
        nonlocal list_type
        if list_type:
            out.append(f"</{list_type}>")
            list_type = None

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        s = line.strip()

        # 代码块
        if s.startswith("```"):
            close_list()
            if in_code:
                out.append("</code></pre>")
                in_code = False
            else:
                out.append("<pre><code>")
                in_code = True
            i += 1
            continue
        if in_code:
            out.append(html.escape(raw, quote=False))
            i += 1
            continue

        # 原生 HTML 块（封面居中块）
        if s.startswith("<") and not s.startswith("<!--"):
            close_list()
            if "align=\"center\"" in s:
                s = s.replace("align=\"center\"", 'class="center"')
            out.append(s)
            i += 1
            continue

        if not s:
            close_list()
            i += 1
            continue

        if s == "---":
            close_list()
            out.append("<hr/>")
            i += 1
            continue

        # 表格
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1]):
            close_list()
            header = [c.strip() for c in s.strip("|").split("|")]
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in header) + "</tr></thead><tbody>")
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                out.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in cells) + "</tr>")
                i += 1
            out.append("</tbody></table>")
            continue

        # 标题
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            close_list()
            lvl = len(m.group(1))
            out.append(f"<h{lvl}>{inline(m.group(2))}</h{lvl}>")
            i += 1
            continue

        # 图片
        m = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", s)
        if m:
            close_list()
            out.append(image_tag(m.group(2), m.group(1)))
            i += 1
            continue

        # 引用
        if s.startswith(">"):
            close_list()
            out.append(f"<blockquote>{inline(s.lstrip('> ').strip())}</blockquote>")
            i += 1
            continue

        # 列表
        m = re.match(r"^[-*]\s+(.*)$", s)
        if m:
            if list_type != "ul":
                close_list()
                out.append("<ul>")
                list_type = "ul"
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue
        m = re.match(r"^\d+[.)]\s+(.*)$", s)
        if m:
            if list_type != "ol":
                close_list()
                out.append("<ol>")
                list_type = "ol"
            out.append(f"<li>{inline(m.group(1))}</li>")
            i += 1
            continue

        close_list()
        out.append(f"<p>{inline(s)}</p>")
        i += 1

    close_list()
    if in_code:
        out.append("</code></pre>")
    return ("<!doctype html><html><head><meta charset=\"utf-8\"><style>" + CSS +
            "</style></head><body>" + "\n".join(out) + "</body></html>")


def browser():
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    found = shutil.which("chrome") or shutil.which("msedge")
    if found:
        return found
    raise RuntimeError("未找到 Chrome / Edge，无法导出 PDF")


def main():
    exe = browser()
    tmp = tempfile.mkdtemp(prefix="acc_docs_")
    try:
        for src, dst, label in DOCS:
            md_path = os.path.join(HERE, src)
            pdf_path = os.path.join(HERE, dst)
            with open(md_path, "r", encoding="utf-8") as f:
                md = f.read()
            html_text = render(md, f"无言以对 · 第二次团队作业 · {label} · 对应 V1.5.0 验收基线")
            html_path = os.path.join(tmp, src.replace(".md", ".html"))
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_text)
            cmd = [exe, "--headless", "--disable-gpu", "--no-sandbox",
                   "--no-pdf-header-footer", "--allow-file-access-from-files",
                   "--virtual-time-budget=5000",
                   f"--print-to-pdf={pdf_path}",
                   "file:///" + html_path.replace("\\", "/")]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
            if not os.path.isfile(pdf_path):
                raise RuntimeError(f"PDF 导出失败 {dst}: {r.stderr[-500:]}")
            with open(pdf_path, "rb") as f:
                head = f.read(5)
            if head != b"%PDF-":
                raise RuntimeError(f"PDF 文件头异常 {dst}: {head!r}")
            print(f"已导出 {dst}  HTML {len(html_text):,} 字符  PDF {os.path.getsize(pdf_path):,} 字节")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
