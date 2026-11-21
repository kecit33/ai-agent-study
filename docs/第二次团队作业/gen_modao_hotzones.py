# -*- coding: utf-8 -*-
"""按真实渲染坐标，为墨刀工程中的页号文字生成原生点击热区。

做法：用无头 Chrome 测量 html_list.json 每页中每个 <a href> 的像素矩形，
在与整页 wCode 完全一致坐标系（1440×1024）上创建透明 wRect 热区，
zIndex=20 覆盖代码组件，绑定 interactionType=1 指向目标页面画布。

这样点击的是原型里真实可见的 P01 / P02 / 页面名文字，而不是新增一条导航条；
编辑器中点中的是热区本身，预览时触发墨刀原生跳页。

依赖：先运行 gen_modao_navfix.py 生成画布，并已把 navfix_*.json 写入工程。
输出：modao_ops/hotzone_XX.json（每批 6 个操作）与 hotzone_map.json。
"""
import io
import json
import os
import re
import subprocess
import sys

BASE = os.path.dirname(os.path.abspath(__file__))
OPS = os.path.join(BASE, "modao_ops")
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
TMP = os.path.join(BASE, "_hotzone_probe.html")
DOM = os.path.join(BASE, "_hotzone_dom.html")
BATCH = 6

sys.path.insert(0, BASE)
from gen_modao_navfix import CHIP_TPL  # noqa: E402

CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"


def hkey(seq):
    """确定性的 createKey('llm') 形态：llm + 14 位 base62。"""
    n = 20261121000000 + seq * 7919
    s = ""
    while n > 0:
        s = CHARS[n % 62] + s
        n //= 62
    return ("llm" + s)[:17].ljust(17, "0")

PROBE = ("<script>(function(){var r=[].slice.call(document.querySelectorAll('a[href]')).map(function(e){"
         "var b=e.getBoundingClientRect();return {href:e.getAttribute('href'),t:e.textContent.trim(),"
         "x:Math.round(b.left+b.width/2),y:Math.round(b.top+b.height/2),"
         "w:Math.round(b.width),h:Math.round(b.height)}});"
         "document.documentElement.setAttribute('data-rects',JSON.stringify(r))})()</script>")


def measure(html):
    io.open(TMP, "w", encoding="utf-8").write(html.replace("</body>", PROBE + "</body>"))
    url = "file:///" + TMP.replace("\\", "/")
    with io.open(DOM, "w", encoding="utf-8") as out:
        subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-first-run",
                        "--window-size=1440,1024", "--virtual-time-budget=2000",
                        "--dump-dom", url], stdout=out, stderr=subprocess.DEVNULL, check=True)
    s = io.open(DOM, encoding="utf-8", errors="ignore").read()
    m = re.search(r'data-rects="([^"]*)"', s)
    if not m:
        raise RuntimeError("未读到链接坐标")
    return json.loads(m.group(1).replace("&quot;", '"'))


def target_of(href):
    m = re.search(r"_(P\d\d|M\d\d)_", href or "")
    if not m:
        raise RuntimeError("无法解析跳转目标: %s" % href)
    return m.group(1)


def make_hotzone(name, rect, target_no, mapdata, source_no, seq):
    ha = json.loads(json.dumps(CHIP_TPL))
    ha["name"] = "热区-%s→%s-%s" % (source_no, target_no, rect["t"])
    ha["x"] = rect["x"]
    ha["y"] = rect["y"]
    ha["w"] = max(16, rect["w"] + 6)
    ha["h"] = max(16, rect["h"] + 6)
    ha["zIndex"] = 20
    ha["fill"]["fillIsVisible"] = False  # 透明，不改变页面外观
    ha["textV1"] = {"blocks": {}, "entityMap": {}}
    ha["animation"]["aniDelay"] = "0s"
    page = mapdata["pages"][target_no]
    src = mapdata["pages"][source_no]
    ha["interactions"] = [{
        "key": "hz_%s_%03d" % (source_no.lower(), seq),
        "interactionType": 1,
        "interactionTrigger": "tap",
        "order": 0,
        "!validVersion": 2,
        "triggerDisable": False,
        "actionDisable": False,
        "targetRBPageKey": page["page"],
        "targetResCanvasKey": page["canvas"],
        "transition": "none",
        "transitionDelay": "0s",
        "transitionDuration": "0s",
        "transitionEasing": "linear",
        "resetTargetCanvasScrollOffset": True,
        "resetTargetSubWidgetsState": True,
    }]
    item = {"op": "create", "item": {"key": mapdata["hotzone_keys"][str(seq)],
                                     "hotAttr": ha, "sub": [], "sup": src["canvas"]}}
    return item


def build():
    mapdata = json.load(io.open(os.path.join(OPS, "navfix_map.json"), encoding="utf-8"))
    items = json.load(io.open(os.path.join(BASE, "modao_v150", "html_list.json"), encoding="utf-8"))
    page_no = lambda n: re.search(r"_(P\d\d|M\d\d)_", n).group(1)

    ops = []
    records = []
    seq = 0
    for entry in items:
        source = page_no(entry["name"])
        rects = measure(entry["html"])
        for i, r in enumerate(rects):
            tgt = target_of(r["href"])
            assert tgt in mapdata["pages"], (source, tgt)
            # 超出画布的链接不建热区（当前全部在 1024 内）
            if r["y"] + r["h"] / 2 > 1024:
                continue
            seq += 1
            mapdata.setdefault("hotzone_keys", {})[str(seq)] = hkey(seq)
            op = make_hotzone(entry["name"], r, tgt, mapdata, source, seq)
            ops.append(op)
            records.append({"seq": seq, "source": source, "target": tgt, "text": r["t"],
                            "x": r["x"], "y": r["y"], "w": r["w"], "h": r["h"],
                            "key": op["item"]["key"]})

    io.open(os.path.join(OPS, "hotzone_map.json"), "w", encoding="utf-8").write(
        json.dumps(records, ensure_ascii=False, indent=1))
    io.open(os.path.join(OPS, "navfix_map.json"), "w", encoding="utf-8").write(
        json.dumps(mapdata, ensure_ascii=False, indent=1))

    for start in range(0, len(ops), BATCH):
        idx = start // BATCH + 1
        path = os.path.join(OPS, "hotzone_%02d.json" % idx)
        io.open(path, "w", encoding="utf-8").write(
            json.dumps({"mode": "update", "operations": ops[start:start + BATCH]},
                       ensure_ascii=False, indent=1))
        print(path, len(ops[start:start + BATCH]), os.path.getsize(path))
    print("hotzones", len(ops))
    for f in (TMP, DOM):
        if os.path.exists(f):
            os.remove(f)


if __name__ == "__main__":
    build()
