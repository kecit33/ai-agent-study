"""思维导图生成：树形 JSON + 自适应 SVG + Markdown 大纲 + Mermaid 源码。

SVG 使用 CSS 变量并附带浅色回退值：内联进页面时自动跟随系统深浅色与主题色，
单独下载/外链时也有可读的默认配色。
"""
from html import escape

PALETTE = ["#2f6fed", "#0d9488", "#7c3aed", "#ea580c", "#16a34a", "#db2777", "#0891b2"]


def build_tree(subject: str, chapters: list) -> dict:
    root = {"id": "root", "label": subject, "children": []}
    for i, c in enumerate(chapters):
        node = {"id": c["id"], "label": c["title"], "children": []}
        for j, t in enumerate(c["topics"]):
            node["children"].append({
                "id": "%s-t%d" % (c["id"], j),
                "label": t["name"],
                "detail": t.get("detail", ""),
                "children": [],
            })
        root["children"].append(node)
    return root


def _count(node: dict) -> int:
    return 1 + sum(_count(c) for c in node.get("children", []))


def to_outline(root: dict, level: int = 0) -> str:
    lines = ["  " * level + ("- " if level else "# ") + root["label"]]
    for child in root.get("children", []):
        lines.append(to_outline(child, level + 1))
    return "\n".join(lines)


def to_mermaid(root: dict) -> str:
    lines = ["mindmap", "  root((%s))" % root["label"].replace("(", "（").replace(")", "）")]

    def walk(node, depth):
        for child in node.get("children", []):
            lines.append("  " * (depth + 2) + "(%s)" % child["label"])
            walk(child, depth + 1)

    walk(root, 0)
    return "\n".join(lines)


def to_svg(root: dict, chapters: list) -> str:
    x_root, w_root, h_root = 24, 190, 48
    x_ch, w_ch, h_ch = 268, 224, 40
    x_tp, w_tp, h_tp = 548, 306, 36
    gap, top = 44, 76

    pos_ch, pos_tp = [], []
    y = top
    for c in chapters:
        topics = c["topics"]
        block_h = max(len(topics) * gap, 72)
        cy = y + block_h / 2
        pos_ch.append(cy - h_ch / 2)
        ys = []
        for i in range(len(topics)):
            ys.append(y + i * gap + (gap - h_tp) / 2)
        pos_tp.append(ys)
        y += block_h + 26

    height = int(y + 28)
    width = x_tp + w_tp + 28
    root_y = height / 2 - h_root / 2

    out = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="100%%" '
        'height="%d" role="img" aria-label="%s 思维导图" '
        'font-family="Microsoft YaHei, PingFang SC, Segoe UI, sans-serif">'
        % (width, height, height, escape(root["label"], quote=True)),
        "<style>",
        ".mm-bg{fill:var(--panel,#ffffff)}",
        ".mm-title{fill:var(--text,#1f2937);font-size:19px;font-weight:700}",
        ".mm-sub{fill:var(--muted,#64748b);font-size:12px}",
        ".mm-node{fill:var(--panel,#ffffff);stroke-width:1.6}",
        ".mm-text{fill:var(--text,#1f2937);font-size:13px}",
        ".mm-small{fill:var(--muted,#64748b);font-size:11.5px}",
        ".mm-link{fill:none;stroke-width:1.6;opacity:.65}",
        ".mm-root{fill:var(--primary,#2f6fed);stroke:none}",
        ".mm-root-text{fill:#ffffff;font-size:15px;font-weight:700}",
        "</style>",
        '<rect class="mm-bg" x="0" y="0" width="%d" height="%d" rx="14"/>' % (width, height),
        '<text class="mm-title" x="24" y="34">%s · 知识思维导图</text>' % escape(root["label"]),
        '<text class="mm-sub" x="24" y="56">%d 个章节 · %d 个知识节点 · 由 AI 校园学习陪伴助手生成</text>'
        % (len(chapters), _count(root) - 1),
    ]

    # 连线：根节点 → 章节 → 知识点
    root_right = x_root + w_root
    for ci, cy in enumerate(pos_ch):
        color = PALETTE[ci % len(PALETTE)]
        cxc, cyc = x_ch, cy + h_ch / 2
        out.append('<path class="mm-link" stroke="%s" d="M %d %d C %d %d, %d %d, %d %d"/>'
                   % (color, root_right, height / 2, root_right + 40, height / 2,
                      cxc - 40, cyc, cxc, cyc))
        for ti, ty in enumerate(pos_tp[ci]):
            topic = chapters[ci]["topics"][ti]
            end_y = ty + h_tp / 2
            out.append('<path class="mm-link" stroke="%s" '
                       'd="M %d %d C %d %d, %d %d, %d %d"/>'
                       % (color, x_ch + w_ch, cyc, x_ch + w_ch + 34, cyc,
                          x_tp - 34, end_y, x_tp, end_y))
            detail = escape((topic.get("detail") or "")[:60], quote=True)
            out.append('<rect class="mm-node" stroke="%s" x="%d" y="%d" width="%d" height="%d" rx="8">'
                       '<title>%s</title></rect>' % (color, x_tp, ty, w_tp, h_tp, detail))
            out.append('<text class="mm-text" x="%d" y="%d">%s</text>'
                       % (x_tp + 12, ty + 23, escape(topic["name"])))

    # 节点（后画，覆盖连线端点）
    out.append('<rect class="mm-root" x="%d" y="%d" width="%d" height="%d" rx="12"/>'
               % (x_root, root_y, w_root, h_root))
    out.append('<text class="mm-root-text" x="%d" y="%d">%s</text>'
               % (x_root + 16, root_y + 30, escape(root["label"][:11])))
    for ci, cy in enumerate(pos_ch):
        color = PALETTE[ci % len(PALETTE)]
        title = chapters[ci]["title"]
        out.append('<rect class="mm-node" stroke="%s" x="%d" y="%d" width="%d" height="%d" rx="9"/>'
                   % (color, x_ch, cy, w_ch, h_ch))
        out.append('<circle cx="%d" cy="%d" r="4" fill="%s"/>'
                   % (x_ch + 14, cy + h_ch / 2, color))
        out.append('<text class="mm-text" x="%d" y="%d">%s</text>'
                   % (x_ch + 26, cy + 25, escape(title)))
    out.append("</svg>")
    return "\n".join(out)


def generate(subject: str, chapters: list) -> dict:
    root = build_tree(subject, chapters)
    return {
        "subject": subject,
        "root": root,
        "node_count": _count(root),
        "chapter_count": len(chapters),
        "svg": to_svg(root, chapters),
        "outline": to_outline(root),
        "mermaid": to_mermaid(root),
    }
