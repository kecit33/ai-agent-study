"""用无头 Chrome 截取新 UI 的真实渲染图，验证深/浅色模式与新功能界面。"""
import json
import os
import pathlib
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
STATIC = ROOT / "static"
OUT = ROOT / "docs" / "ui"
OUT.mkdir(exist_ok=True)
BASE = os.getenv("BASE_URL", "http://127.0.0.1:5000")

CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
BROWSER = next((p for p in CANDIDATES if os.path.exists(p)), None)

SHOTS = [
    ("dashboard-light", "light", "/#dashboard", 9000),
    ("dashboard-dark", "dark", "/#dashboard", 9000),
    ("hardware-dark", "dark", "/#hardware", 9000),
    ("settings-dark", "dark", "/#settings", 9000),
    ("settings-model-light", "light", "/#settings", 9000),
    ("memory-light", "light", "/#memory", 9000),
    ("study-light", "light", "/?autopack=1#study", 14000),
    ("study-dark", "dark", "/?autopack=1#study", 14000),
]

if not BROWSER:
    raise SystemExit("未找到 Chrome / Edge")

for name, mode, path, budget in SHOTS:
    cap = STATIC / ("_cap_%s.html" % name)
    cap.write_text(
        "<script>localStorage.setItem('cc-theme-mode','%s');"
        "localStorage.setItem('cc-accent','#2f6fed');location.replace(%s);</script>"
        % (mode, json.dumps(path)),
        encoding="utf-8")
    target = OUT / (name + ".png")
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [BROWSER, "--headless=new", "--disable-gpu",
               "--screenshot=" + str(target), "--window-size=1280,1050",
               "--virtual-time-budget=%d" % budget, "--user-data-dir=" + tmp,
               BASE + "/static/_cap_%s.html" % name]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    cap.unlink(missing_ok=True)
    ok = target.exists() and target.stat().st_size > 10000
    print(("OK  " if ok else "FAIL"), name, target.stat().st_size if target.exists() else "no file")
print("输出目录：", OUT)
