# -*- coding: utf-8 -*-
"""为墨刀结构化写入接口生成分批 operations。

背景：import_to_proto 的多页导入当前返回「原型不存在或您没有查看权限」，
单页导入可用；故先导入 P00 建立工程，再用 process_proto_json 逐批补入 P01–P10 / M01–M05。

输入：modao_v150/html_list.json（交互精简版导入载荷，16 项）
输出：modao_ops/batch_XX.json（每批 2 页），内容为 {"mode":"update","operations":[...]}
键使用 modao-proto skill 的 createKey('llm') 语义：llm + base62 时间戳 + base62 随机后缀。
"""
import io
import json
import os
import random
import string
import subprocess
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "modao_v150", "html_list.json")
OUTDIR = os.path.join(HERE, "modao_ops")
KEY_HELPER = r"C:\Users\kecit\.workbuddy\skills\modao-proto\scripts\create-key.mjs"
BATCH = 2

BUNCH_TPL = {
    "!version": 1, "alignH": [], "alignV": [], "asFolder": False, "bunch": "rbPage",
    "defaultCanvasKey": "", "deleteInfo": {"deleteTime": 0, "deleteUserName": ""},
    "device": "customize", "deviceH": 1024, "deviceOrientation": "portrait",
    "deviceScroll": "hide", "deviceW": 1440,
    "fill": {"fill": "solid", "fillIsVisible": False, "solidColor": 4294967295},
    "h": 1024, "icon": "", "isShowDeviceGuide": True, "layout": "row", "libKey": "",
    "mtime": 0, "scroll": 1, "showScrollBar": 3, "type": "rResBunch", "w": 1440, "zIndex": 1,
}
WCODE_TPL = {
    "animation": {"aniCount": "1", "aniDelay": "0", "aniDuration": "1s", "aniName": "none"},
    "createMethod": "code-widget", "fixPosTo": "none", "h": 1024, "injection": "",
    "interactions": [], "isLock": False, "isLockAspect": True, "isVisible": True,
    "opacity": 1, "r": 0, "stickyOffset": None, "type": "wCode", "w": 1440,
    "x": 720, "y": 512, "zIndex": 1,
}
EXT_TPL = {
    "extCodeInfo": {"contentType": "html", "createdAt": "1795265759467",
                    "creator": "7112629", "fromPath": ""},
    "extType": "extCode", "type": "rResExt", "zIndex": 0,
}


def make_keys(n):
    """优先调用 skill 的 create-key.mjs；不可用时用等价 base62 规则生成。"""
    try:
        out = subprocess.run(["node", KEY_HELPER, str(n)], capture_output=True,
                             text=True, timeout=20, check=True)
        keys = json.loads(out.stdout)
        if len(keys) == n:
            return keys
    except Exception:
        pass
    alphabet = string.digits + string.ascii_uppercase + string.ascii_lowercase

    def b62(num, width=9):
        s = ""
        while num:
            num, r = divmod(num, 62)
            s = alphabet[r] + s
        return s.zfill(width)

    base = int(time.time() * 1000)
    return ["llm" + b62(base + i) + "".join(random.choice(alphabet) for _ in range(6))
            for i in range(n)]


def build_ops(item, keys):
    """keys: bunch, widget, ext, nav"""
    bunch_key, widget_key, ext_key, nav_key = keys
    name = item["name"]
    bunch = dict(BUNCH_TPL)
    bunch["name"] = name
    widget = dict(WCODE_TPL)
    widget["name"] = name
    widget["navOptions"] = [{"active": True, "children": [], "cid": nav_key,
                             "codeRef": ext_key, "name": name, "patch": ""}]
    ext = dict(EXT_TPL)
    ext["name"] = name
    ext["extData"] = item["html"]
    return [
        {"op": "create", "item": {"key": ext_key, "hotAttr": ext, "sub": [], "sup": "B@ext"}},
        {"op": "create", "item": {"key": bunch_key, "hotAttr": bunch, "sub": [], "sup": "B@main"}},
        {"op": "create", "item": {"key": widget_key, "hotAttr": widget, "sub": [], "sup": bunch_key}},
    ]


def main():
    items = json.load(io.open(SRC, encoding="utf-8"))
    assert len(items) == 16, "导入载荷应为 16 页"
    todo = items[1:]  # P00 已由单页导入建立工程
    os.makedirs(OUTDIR, exist_ok=True)
    all_keys = make_keys(len(todo) * 4)
    assert len(set(all_keys)) == len(all_keys), "键重复"
    batches = []
    for i in range(0, len(todo), BATCH):
        chunk = todo[i:i + BATCH]
        ops = []
        for j, item in enumerate(chunk):
            ks = all_keys[(i + j) * 4:(i + j + 1) * 4]
            ops.extend(build_ops(item, ks))
        payload = {"mode": "update", "operations": ops}
        path = os.path.join(OUTDIR, "batch_%02d.json" % (len(batches) + 1))
        io.open(path, "w", encoding="utf-8").write(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        batches.append((path, [x["name"] for x in chunk], os.path.getsize(path)))
    for path, names, size in batches:
        print(os.path.basename(path), size, "B", " + ".join(n[:22] for n in names))
    print("批次数:", len(batches), "页面数:", len(todo))


if __name__ == "__main__":
    main()
