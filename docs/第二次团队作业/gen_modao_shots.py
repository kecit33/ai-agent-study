# -*- coding: utf-8 -*-
"""为 V1.5.0 原型页生成同源页面截图（前台 + 后台管理）。

事实源：modao_v150/*.html（与 html_list.json 中的导入载荷逐页一致）。
用途：补齐作业要求的「习题辅导 / 课程记忆 / 硬件联动」3 张原型截图，
并额外导出 P00 评审索引页与 2 张后台管理原型页。截图由无头 Chrome
渲染本地同源 HTML 得到，不冒充墨刀客户端「导出图片」功能的产物。

运行：python gen_modao_shots.py
"""
import glob
import os
import shutil
import struct
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "modao_v150")
ASSETS = os.path.join(HERE, "assets")

# (原型页 HTML, 输出 PNG, 初始窗口高度)
TARGETS = [
    ("V1.5.0_P00_原型总览与需求索引.html", "原型_总览与需求索引.png", 2300),
    ("V1.5.0_P05_习题辅导_tutor_.html", "原型_习题辅导.png", 1500),
    ("V1.5.0_P07_课程记忆_memory_.html", "原型_课程记忆.png", 1500),
    ("V1.5.0_P09_硬件联动_hardware_.html", "原型_硬件联动.png", 1500),
    ("V1.5.0_M01_课程与资料管理_m01_.html", "原型_后台管理_课程与资料.png", 1500),
    ("V1.5.0_M02_智能体运行配置_m02_.html", "原型_后台管理_运行配置.png", 1500),
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


def png_size(path):
    """只读 PNG 头部取宽高，不依赖第三方图像库。"""
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


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
        print("已生成", out_name, os.path.getsize(out), "B", png_size(out))
    print("原型截图共", len(glob.glob(os.path.join(ASSETS, "原型_*.png"))), "张")


if __name__ == "__main__":
    main()
