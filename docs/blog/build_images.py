"""生成博客园文章配图：矢量图转 PNG + 真实运行界面截图。

依赖：本机 Chrome / Edge（headless 截图）、本地 Web 服务已运行在 5000 端口。
用法：python docs/blog/build_images.py
输出：docs/blog/assets/*.png
"""
import os
import pathlib
import shutil
import struct
import subprocess
import tempfile
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"
ASSETS = DOCS / "blog" / "assets"
STATIC = ROOT / "static"
BASE = "http://127.0.0.1:5000"

BROWSERS = [
    pathlib.Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
    pathlib.Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
]
CHROME = next((p for p in BROWSERS if p.exists()), None)
if CHROME is None:
    raise SystemExit("未找到 Chrome / Edge，无法生成截图")


def shot(url, out_path, width, height, budget=6000):
    """用 headless 浏览器把 URL 截成指定尺寸的 PNG。"""
    udd = tempfile.mkdtemp(prefix="wb-shot-")
    cmd = [
        str(CHROME), "--headless=new", "--disable-gpu", "--no-sandbox",
        "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
        "--disable-extensions", "--disable-dev-shm-usage",
        "--force-device-scale-factor=1",
        f"--user-data-dir={udd}",
        f"--window-size={width},{height}",
        f"--virtual-time-budget={budget}",
        f"--screenshot={out_path}",
        url,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    shutil.rmtree(udd, ignore_errors=True)
    if not out_path.exists() or out_path.stat().st_size < 1000:
        raise RuntimeError("截图失败 %s: %s" % (url, (r.stderr or "")[-400:]))
    return out_path.stat().st_size


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def svg_to_png(tmp):
    """把项目里的 SVG 矢量图栅格化为 PNG（内联到 HTML 避免文件权限问题）。"""
    items = [
        ("logo", 640, 220),
        ("mindmap", 960, 620),
        ("classdiagram", 1000, 700),
        ("architecture", 960, 460),
    ]
    for name, w, h in items:
        svg = (DOCS / (name + ".svg")).read_text(encoding="utf-8")
        page = tmp / (name + ".html")
        page.write_text(
            '<!doctype html><html><head><meta charset="utf-8">'
            '<style>html,body{margin:0;padding:0;background:#fff}'
            'svg{display:block}</style></head><body>' + svg + "</body></html>",
            encoding="utf-8",
        )
        out = ASSETS / (name + ".png")
        size = shot(page.as_uri(), out, w, h, budget=3000)
        print("[SVG] %-14s %4dx%-4d %7d bytes" % (name, *png_size(out), size))


CAPTURE_HTML = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<style>html,body{margin:0;padding:0;background:#fff;overflow:hidden}
iframe{border:0;display:block;width:1280px;height:900px}</style></head><body>
<iframe id="f" src="/"></iframe>
<script>
const q = new URLSearchParams(location.search);
const f = document.getElementById('f');
f.addEventListener('load', () => {
  setTimeout(() => {
    const d = f.contentDocument;
    if (!d) return;
    const tab = q.get('tab');
    if (tab) { const b = d.querySelector('.tab[data-tab="' + tab + '"]'); if (b) b.click(); }
    const fill = q.get('fill');
    if (fill) { try { const m = JSON.parse(fill);
      for (const k in m) { const el = d.getElementById(k); if (el) el.value = m[k]; }
    } catch (e) {} }
    const click = q.get('click');
    if (click) { setTimeout(() => {
      const btn = d.getElementById(click); if (btn) btn.click();
    }, 400); }
  }, 900);
});
</script></body></html>"""


def ui_shots(capture_url):
    """截取真实运行中的 Web 界面；fill/click 会真的调用后端 API。"""
    cases = [
        ("ui-home", "chat", None, None),
        ("ui-settings", "settings", None, None),
        ("ui-wrong", "wrong", None, None),
        ("ui-chat-reply", "chat",
         {"chatInput": "完全二叉树有什么特点？"}, "sendChat"),
        ("ui-summarize", "summarize",
         {"sumText": "栈是后进先出的线性结构。队列是先进先出。二叉搜索树的中序遍历序列有序，查找平均时间复杂度为 O(log n)。哈希表支持 O(1) 平均查找。"},
         "doSummarize"),
        ("ui-plan", "plan", {"planSubject": "数据结构", "planDays": "10"}, "doPlan"),
    ]
    for name, tab, fill, click in cases:
        params = {"tab": tab}
        if fill:
            params["fill"] = __import__("json").dumps(fill, ensure_ascii=False)
        if click:
            params["click"] = click
        url = capture_url + "?" + urllib.parse.urlencode(params)
        out = ASSETS / (name + ".png")
        try:
            size = shot(url, out, 1280, 900, budget=9000)
            print("[UI ] %-14s %4dx%-4d %7d bytes" % (name, *png_size(out), size))
        except Exception as e:
            print("[UI ] %-14s 失败: %s" % (name, str(e)[:150]))


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    print("浏览器:", CHROME)
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="wb-blog-"))
    try:
        svg_to_png(tmp)
        capture = STATIC / "_blog_capture.html"
        capture.write_text(CAPTURE_HTML, encoding="utf-8")
        try:
            ui_shots(BASE + "/static/_blog_capture.html")
        finally:
            try:
                capture.unlink()
            except OSError:
                pass
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("输出目录:", ASSETS)


if __name__ == "__main__":
    main()
