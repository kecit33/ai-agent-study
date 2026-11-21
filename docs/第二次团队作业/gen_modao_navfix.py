# -*- coding: utf-8 -*-
"""为 V1.5.0 墨刀交互版工程补全原生页号跳转。

问题：16 页均为整页 wCode 代码组件，页面没有 rResCanvas，hotAttr.interactions 为空；
HTML 里的 <a href> 只是文本链接，编辑态点击只会选中外层组件，预览态也不跳页。

修复（不改变原型内容与交互逻辑，只补结构层与热区）：
1. 每页补一个标准 rResCanvas，承载该页原有 wCode；
2. wCode 移入画布，页面 defaultCanvasKey 指向该画布；
3. 页号热区改由 gen_modao_hotzones.py 按真实渲染坐标精确覆盖，本脚本只负责画布层。

输出：modao_ops/navfix_01/02_canvas_*.json 与 modao_ops/navfix_map.json。
事实源：get_proto_details 的 50 节点工程详情；墨刀 modao-proto skill 的
update-contract / navigation-tree-pagination / proto2-special-semantics。
"""
import io
import json
import os
import random
import re
import time

BASE = os.path.dirname(os.path.abspath(__file__))
OPS = os.path.join(BASE, "modao_ops")
DETAIL = r"C:\Users\kecit\.workbuddy\projects\c-Users-kecit-WorkBuddy-2026-11-05-17-01-51\63bca78c-7bb8-48dc-b435-39999ff746d5\tool-results\mcp-modao-ai-get_proto_details-1795270100779-990b2f.txt"

CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
RND = random.Random(20261121)
USED = set()


def key():
    while True:
        k = "llm" + "".join(RND.choice(CHARS) for _ in range(14))
        if k not in USED:
            USED.add(k)
            return k


def page_no(name):
    m = re.search(r"_(P\d\d|M\d\d)_", name)
    return m.group(1) if m else None


def base62(value, chars):
    if value == 0:
        return "0"
    out = ""
    while value > 0:
        out = chars[value % 62] + out
        value //= 62
    return out


def load_tree():
    raw = io.open(DETAIL, encoding="utf-8").read()
    return json.loads(raw)["json"]["tree"]


CANVAS_TPL = {
    "alignH": [], "alignV": [], "asOverlay": False,
    "border": {"bdrColor": 3149642751, "bdrIsVisible": False, "bdrStyle": "solid", "bdrWidth": 1},
    "borderRadius": 0, "borderRadiusIsVisible": True,
    "borderVisibility": {"bdrIsVisibleB": True, "bdrIsVisibleL": True, "bdrIsVisibleR": True, "bdrIsVisibleT": True},
    "device": "customize",
    "fill": {"fill": "solid", "fillIsVisible": False, "solidColor": 4294967295},
    "h": 1024, "interactions": [], "isClipContent": False, "isLock": False,
    "isLockAspect": False, "isVisible": True,
    "layoutGrid": {"colCount": 10, "colGutter": 10, "gridSize": 10, "isColLayout": False,
                   "isGridLayout": False, "isRowLayout": False, "rowGutter": 10, "rowHeight": 20},
    "name": "", "order": 1, "orientation": "portrait", "r": 0,
    "shadow": {"blurRadius": 6, "offsetX": 0, "offsetY": 2, "shadowColor": 102,
               "shadowIsVisible": False, "spreadRadius": 0, "type": "box_shadow"},
    "stickyFooterHeight": 0, "stickyHeaderHeight": 0, "type": "rResCanvas",
    "w": 1440, "x": 720, "y": 512, "zIndex": 1,
}

CHIP_TPL = {
    "!ffVersion": 1,
    "animation": {"aniCount": "1", "aniDelay": "0s", "aniDuration": "1s", "aniName": "none"},
    "border": {"bdrColor": 4294967295, "bdrIsVisible": True, "bdrStyle": "solid", "bdrWidth": 1},
    "borderRadius": {"radiusBL": 3, "radiusBR": 3, "radiusTL": 3, "radiusTR": 3},
    "borderRadiusIsVisible": True,
    "borderVisibility": {"bdrIsVisibleB": True, "bdrIsVisibleL": True, "bdrIsVisibleR": True, "bdrIsVisibleT": True},
    "fill": {"fill": "solid", "fillIsVisible": True, "solidColor": 4279717792},  # #1750A8 蓝底
    "fixPosTo": "none", "h": 20, "interactions": [], "isLock": False,
    "isLockAspect": False, "isVisible": True, "name": "", "opacity": 1, "r": 0,
    "richTextMetric": {"boundingBoxHeight": 0, "boundingBoxLeft": 0, "boundingBoxTop": 0, "boundingBoxWidth": 0},
    "richTextV1": {
        "!lhVersion": 3, "!wbiVersion": 3, "bold": True,
        "fontDirection": "horizontal-tb", "fontFamily": "Microsoft YaHei", "fontSize": 11,
        "fontWeight": "regular", "horizontalAlign": "center", "isClipText": True,
        "italic": False, "letterSpacing": 0, "lineHeight": 13, "padding": 0,
        "paddingTuple": {"pB": 1, "pL": 2, "pR": 2, "pT": 1},
        "paraSpacing": 0, "sizeType": 0, "strikethrough": False,
        "textColor": "rgb(255, 255, 255)", "underline": False, "verticalAlign": "center",
    },
    "shadow": {"blurRadius": 6, "offsetX": 0, "offsetY": 2, "shadowColor": 102,
               "shadowIsVisible": False, "spreadRadius": 0, "type": "box_shadow"},
    "stickyOffset": None, "styleType": "fill_light",
    "textV1": {"blocks": {}, "entityMap": {}},
    "type": "wRect", "w": 58, "x": 0, "y": 18, "zIndex": 10,
}


def write(name, operations):
    path = os.path.join(OPS, name)
    io.open(path, "w", encoding="utf-8").write(
        json.dumps({"mode": "update", "operations": operations}, ensure_ascii=False, separators=(",", ":")))
    return path, len(operations), os.path.getsize(path)


def build():
    os.makedirs(OPS, exist_ok=True)
    tree = load_tree()
    pages = {}
    for k, v in tree.items():
        ha = v.get("hotAttr", {})
        if ha.get("type") == "rResBunch" and ha.get("bunch") == "rbPage":
            no = page_no(ha.get("name", ""))
            if no:
                child = v["sub"][0]
                pages[no] = {"key": k, "name": ha["name"], "code": child, "code_key": tree[child]["hotAttr"].get("name", child)}
    order = ["P00"] + ["P%02d" % i for i in range(1, 11)] + ["M%02d" % i for i in range(1, 6)]
    assert sorted(pages) == sorted(order), "页面集合不符: %s" % sorted(pages)
    assert len(pages) == 16

    # 画布 key 映射（页号热区由 gen_modao_hotzones.py 生成）
    canvas = {no: key() for no in order}
    mapping = {
        "project_cid": "pb2mcpVbc0AcCTz0QuMv",
        "pages": {no: {"page": pages[no]["key"], "code": pages[no]["code"],
                       "canvas": canvas[no], "name": pages[no]["name"]} for no in order},
    }
    io.open(os.path.join(OPS, "navfix_map.json"), "w", encoding="utf-8").write(
        json.dumps(mapping, ensure_ascii=False, indent=1))

    # 阶段 1：画布 + 代码组件迁移 + 页面默认画布
    stage1 = []
    for no in order:
        p = pages[no]
        ha = json.loads(json.dumps(CANVAS_TPL))
        ha["name"] = p["name"]
        stage1.append({"op": "create", "item": {"key": canvas[no], "hotAttr": ha, "sub": [], "sup": p["key"]}})
    # 顺手修正 P00 代码组件相对画布下移 24px 的历史偏差，须在迁移前完成
    stage1.append({"op": "update", "item": {"key": pages["P00"]["code"], "hotAttr": {"y": 512}}})
    for no in order:
        stage1.append({"op": "move", "key": pages[no]["code"], "nextKeySup": canvas[no]})
    for no in order:
        stage1.append({"op": "update", "item": {"key": pages[no]["key"], "hotAttr": {"defaultCanvasKey": canvas[no]}}})

    half = len(stage1) // 2
    print(write("navfix_01_canvas_a.json", stage1[:half]))
    print(write("navfix_02_canvas_b.json", stage1[half:]))

    print("pages", len(pages), "canvases", len(canvas), "total_ops", len(stage1))


if __name__ == "__main__":
    build()
