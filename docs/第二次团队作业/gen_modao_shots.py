# -*- coding: utf-8 -*-
"""为墨刀 V1.5.0 原型页生成同源页面截图。

事实源：modao_v150/*.html（与 import_to_proto 导入墨刀的 html_list.json 完全一致）。
用途：补齐「习题辅导 / 课程记忆 / 硬件联动」3 张原型工具载体版页面图（R05），
并额外导出 P00 评审索引页。截图由无头 Chrome 渲染本地同源 HTML 得到，
不冒充墨刀客户端「导出图片」功能的产物。

运行：python gen_modao_shots.py
"""
import glob
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "modao_v150")
ASSETS = os.path.join(HERE, "assets")

TARGETS = [
    ("V1.5.0_P00_原型总览与需求索引.html", "原型_总览与需求索引.png", 1150),
    ("V1.5.0_P05_习题辅导_tutor_.html", "原型_习题辅导.png", 900),
    ("V1.5.0_P07_课程记忆_memory_.html", "原型_课程记忆.png", 900),
    ("V1.5.0_P09_硬件联动_hardware_.html", "原型_硬件联动.png", 900),
]

CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def find_chrome():
    for p in CHROME_CANDIDATES:
        if os.path.isfile(p):
            return p
    return shutil.which("chrome") or shutil.which("msedge")


def main():
    chrome = find_chrome()
    if not chrome:
        raise SystemExit("未找到 Chrome / Edge，无法生成原型截图")
    os.makedirs(ASSETS, exist_ok=True)
    for src_name, out_name, height in TARGETS:
        src = os.path.join(SRC, src_name)
        if not os.path.isfile(src):
            raise SystemExit("缺原型页：" + src)
        out = os.path.join(ASSETS, out_name)
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--no-first-run", "--no-default-browser-check",
            "--force-device-scale-factor=1", "--window-size=1280,%d" % height,
            "--virtual-time-budget=2500", "--screenshot=" + out,
            "file:///" + src.replace("\\", "/"),
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if not os.path.isfile(out) or os.path.getsize(out) < 5000:
            raise SystemExit("截图失败 %s：%s" % (out_name, r.stderr[-500:]))
        print("已生成", out_name, os.path.getsize(out), "B")
    print("原型截图共", len(glob.glob(os.path.join(ASSETS, "原型_*.png"))), "张")


if __name__ == "__main__":
    main()
