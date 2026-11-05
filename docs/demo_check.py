"""端到端 HTTP 验收脚本：对运行中的 Web 应用逐条发起真实请求并留存数据结果。

用法：
    python docs/demo_check.py                      # 默认验证 http://localhost:5000
    BASE_URL=https://xxx.example.com python docs/demo_check.py   # 验证线上站点

产出：docs/demo_results.json（原始响应）、docs/演示验收报告.md（可读报告）
"""
import http.cookiejar
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

BASE = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
SHARECODE = os.getenv("SHARECODE", "")  # 线上分享链接的 sharecode，用于建立访问会话
OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS = []

# 使用 CookieJar 模拟浏览器：带 sharecode 打开首页后，后续 API 请求自动携带会话 Cookie
_JAR = http.cookiejar.CookieJar()
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_JAR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def init_session():
    if not SHARECODE:
        return
    url = BASE + "/?sharecode=" + urllib.parse.quote(SHARECODE)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (demo-check)"})
    with _OPENER.open(req, timeout=25) as r:
        r.read()
    print(f"  已通过 sharecode 建立访问会话（Cookie: "
          f"{', '.join(c.name for c in _JAR) or '无'}）")


def call(method, path, payload=None, expect=200, note=""):
    url = BASE + path
    data = None
    headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0 (demo-check)"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    status, body, raw = None, None, None
    try:
        with _OPENER.open(req, timeout=25) as r:
            status = r.status
            raw = r.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        status = e.code
        raw = e.read().decode("utf-8", errors="replace")
    except Exception as e:
        RESULTS.append({"name": note or path, "method": method, "path": path,
                        "status": "ERR", "ok": False, "error": str(e), "response": None})
        print(f"  [FAIL] {note or path}: 连接失败 {e}")
        return None
    try:
        body = json.loads(raw)
    except ValueError:
        body = raw
    ok = (status == expect)
    RESULTS.append({
        "name": note or path, "method": method, "path": path,
        "request": payload, "status": status, "ok": ok, "response": body,
    })
    preview = ""
    if isinstance(body, dict):
        preview = json.dumps(body, ensure_ascii=False)[:110]
    elif isinstance(body, str):
        preview = body[:110].replace("\n", " ")
    print(f"  [{'PASS' if ok else 'FAIL'}] {note or path}  HTTP {status}  {preview}")
    return body


def text_of(resp, key):
    return (resp or {}).get(key, "") if isinstance(resp, dict) else ""


def main():
    init_session()
    print("=" * 70)
    print("  AI 校园学习陪伴助手 · Web 应用端到端验收")
    print("  目标站点：" + BASE)
    print("  执行时间：" + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 70)

    checks = []

    print("\n【1】静态 Web 页面与资源")
    html = call("GET", "/", note="首页 HTML")
    checks.append(("首页标题正确", isinstance(html, str) and "AI 校园学习陪伴助手" in html))
    checks.append(("前端脚本已引用", isinstance(html, str) and "/static/js/app.js" in html))
    css = call("GET", "/static/css/style.css", note="样式表")
    checks.append(("样式表可访问", isinstance(css, str) and len(css) > 200))
    js = call("GET", "/static/js/app.js", note="前端脚本")
    checks.append(("前端脚本可访问", isinstance(js, str) and "loadCourses" in js))

    print("\n【2】系统状态 / 智能体可插拔接口")
    st = call("GET", "/api/status", note="系统状态")
    checks.append(("返回激活的提供商", isinstance(st, dict) and bool(st.get("active_provider"))))
    providers = call("GET", "/api/providers", note="厂商列表")
    checks.append(("四厂商 + 自定义兼容接口 + 演示模式共 6 项",
                   isinstance(providers, list) and len(providers) == 6
                   and {p.get("name") for p in providers} >=
                   {"openai", "qianfan", "moonshot", "claude", "custom", "demo"}))
    if isinstance(providers, list):
        print("       厂商：" + "、".join(p.get("label", p.get("name", "")) for p in providers))
    sw = call("POST", "/api/settings/provider", {"name": "demo"}, note="切换为演示模式")
    checks.append(("提供商切换生效", isinstance(sw, dict) and sw.get("active_provider") == "demo"))

    print("\n【3】课程与课程记忆（核心功能）")
    stamp = int(time.time())
    name_a = f"验收课程A_数据结构_{stamp}"
    name_b = f"验收课程B_操作系统_{stamp}"
    ca = call("POST", "/api/courses", {"name": name_a}, note="新建课程A")
    cb = call("POST", "/api/courses", {"name": name_b}, note="新建课程B")
    checks.append(("课程创建返回 ID", isinstance(ca, dict) and ca.get("id", 0) > 0))
    cid = ca["id"] if isinstance(ca, dict) else 0
    cid_b = cb["id"] if isinstance(cb, dict) else 0
    courses = call("GET", "/api/courses", note="课程列表")
    checks.append(("课程列表包含新建课程", isinstance(courses, list)
                   and any(c.get("name") == name_a for c in courses)))

    mat = call("POST", f"/api/courses/{cid}/materials",
               {"title": "第3章 树与二叉树",
                "content": "二叉树第 i 层最多有 2^(i-1) 个结点；深度为 k 的二叉树最多有 2^k-1 个结点。满二叉树与完全二叉树的区别在于最后一层的排列方式。"},
               note="上传课程A资料")
    checks.append(("资料上传返回 ID", isinstance(mat, dict) and mat.get("id", 0) > 0))
    mats = call("GET", f"/api/courses/{cid}/materials", note="读取课程A资料")
    checks.append(("资料按课程持久化", isinstance(mats, list) and len(mats) >= 1))

    chat_a = call("POST", "/api/chat", {"course_id": cid, "message": "完全二叉树有什么特点？"},
                  note="课程A问答（记忆绑定）")
    chat_b = call("POST", "/api/chat", {"course_id": cid_b, "message": "进程和线程的区别？"},
                  note="课程B问答（记忆隔离）")
    ra, rb = text_of(chat_a, "reply"), text_of(chat_b, "reply")
    checks.append(("问答返回非空回复", len(ra) > 20))
    checks.append(("课程A上下文绑定正确", name_a in ra))
    checks.append(("课程B上下文独立（隔离成功）", name_b in rb and name_a not in rb))

    print("\n【4】AI 三大辅助功能")
    summ = call("POST", "/api/summarize",
                {"text": "栈是一种后进先出的线性结构。队列是先进先出的线性结构。树是非线性层次结构。图由顶点和边组成。哈希表支持平均O(1)查找。二叉搜索树中序遍历有序。"},
                note="课件总结")
    rs = text_of(summ, "result")
    checks.append(("总结含关键知识点", "关键知识点" in rs))
    checks.append(("总结含考点提纲", "复习考点提纲" in rs))
    tutor = call("POST", "/api/tutor", {"problem": "用迪杰斯特拉算法求 A 到 D 的最短路径"},
                 note="引导式习题辅导")
    rt = text_of(tutor, "result")
    checks.append(("辅导为引导式不直接给答案", "思路" in rt and "不直接给答案" in rt))
    plan = call("POST", "/api/review-plan", {"subject": "数据结构", "days": 10},
                note="复习计划")
    rp = text_of(plan, "result")
    checks.append(("计划含逐日安排", "第 1 天" in rp))
    checks.append(("计划科目正确", "数据结构" in rp))

    print("\n【5】AI 错题本闭环")
    wq = call("POST", "/api/wrong-questions",
              {"course_id": cid, "question": "求斐波那契数列第 n 项，n=40",
               "user_answer": "直接递归 f(n)=f(n-1)+f(n-2)",
               "correct_answer": "使用记忆化或递推，时间复杂度 O(n)"},
              note="录入错题")
    wid = wq.get("id", 0) if isinstance(wq, dict) else 0
    checks.append(("错题录入返回 ID", wid > 0))
    wqs = call("GET", f"/api/wrong-questions?course_id={cid}", note="按课程查询错题")
    checks.append(("错题按课程归档", isinstance(wqs, list) and any(w.get("id") == wid for w in wqs)))
    ana = call("POST", f"/api/wrong-questions/{wid}/analyze", {}, note="分析错因+定向变式题")
    checks.append(("错因分析非空", bool(text_of(ana, "error_reason"))))
    checks.append(("变式题非空", bool(text_of(ana, "variant"))))
    master = call("POST", f"/api/wrong-questions/{wid}/master", {"mastered": True},
                  note="标记已掌握")
    checks.append(("标记掌握接口正常", isinstance(master, dict) and master.get("ok") is True))
    wqs2 = call("GET", f"/api/wrong-questions?course_id={cid}&unmastered=1",
                note="筛选未掌握错题")
    checks.append(("掌握后从未掌握列表移除", isinstance(wqs2, list)
                   and all(w.get("id") != wid for w in wqs2)))

    print("\n【6】硬件联动 / 复习任务（可选加分项）")
    task = call("POST", "/api/review-tasks",
                {"course_id": cid, "task_name": "复习第3章 树与二叉树", "fire_now": True},
                note="创建复习任务并立即下发")
    checks.append(("任务创建返回 ID", isinstance(task, dict) and task.get("id", 0) > 0))
    hw = call("POST", "/api/hardware/test", {"task_name": "课堂演示提醒"}, note="硬件下发测试")
    checks.append(("硬件接口正常响应", isinstance(hw, dict) and "sent" in hw))

    print("\n【7】异常与边界")
    e1 = call("POST", "/api/chat", {"message": "缺少课程"}, expect=400,
              note="缺少课程参数应返回 400")
    checks.append(("参数校验返回 400", isinstance(e1, dict) and "error" in e1))
    e2 = call("POST", "/api/courses", {"name": name_a}, expect=400, note="重复课程名应被拦截")
    checks.append(("重名拦截返回 400", isinstance(e2, dict) and "error" in e2))
    e3 = call("GET", "/api/not-exist", expect=404, note="未知接口返回 404")
    checks.append(("未知接口返回 404", isinstance(e3, dict) and "error" in e3))

    # ---------- 汇总 ----------
    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    http_total = len(RESULTS)
    http_ok = sum(1 for r in RESULTS if r.get("ok"))
    print("\n" + "=" * 70)
    print(f"  HTTP 请求：{http_ok}/{http_total} 状态正确")
    print(f"  业务断言：{passed}/{total} 通过")
    for label, ok in checks:
        print(f"    {'✓' if ok else '✗'} {label}")
    print("=" * 70)

    with open(os.path.join(OUT_DIR, "demo_results.json"), "w", encoding="utf-8") as f:
        json.dump({
            "base_url": BASE,
            "run_at": datetime.now().isoformat(timespec="seconds"),
            "http_requests_total": http_total,
            "http_requests_ok": http_ok,
            "assertions_total": total,
            "assertions_passed": passed,
            "checks": [{"name": n, "passed": bool(o)} for n, o in checks],
            "requests": RESULTS,
        }, f, ensure_ascii=False, indent=2)

    lines = [
        "# AI 校园学习陪伴助手 · Web 应用演示验收报告",
        "",
        f"- 验收站点：`{BASE}`",
        f"- 执行时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- HTTP 请求：**{http_ok}/{http_total}** 状态正确",
        f"- 业务断言：**{passed}/{total}** 通过",
        "- 运行方式：`python docs/demo_check.py`；`BASE_URL` 指定站点，`SHARECODE` 用于线上分享链接建立访问会话",
        "",
        "## 一、逐项验收结果",
        "",
        "| # | 验收项 | 结果 |",
        "| --- | --- | --- |",
    ]
    lines += [f"| {i} | {n} | {'✅ 通过' if o else '❌ 未通过'} |"
              for i, (n, o) in enumerate(checks, 1)]
    lines += ["", "## 二、真实响应数据摘录", "",
              "以下均取自本次 HTTP 请求的真实响应（完整数据见 `demo_results.json`）。", ""]

    def quote(s, limit=460):
        s = (s or "").replace("\r", "")
        return "\n".join("> " + ln for ln in (s[:limit] + ("…" if len(s) > limit else "")).splitlines())

    sections = [
        ("课程记忆问答（课程A）", ra),
        ("课程记忆隔离（课程B）", rb),
        ("课件总结", rs),
        ("引导式习题辅导", rt),
        ("10 天复习计划", rp),
        ("错因分析", text_of(ana, "error_reason")),
        ("定向变式题", text_of(ana, "variant")),
    ]
    for title, body in sections:
        lines += [f"### {title}", "", quote(body), ""]
    lines += ["## 三、结论", "",
              f"本次以真实 HTTP 请求对运行中的 Web 服务完成端到端验证，"
              f"{http_ok}/{http_total} 个请求返回预期状态，{passed}/{total} 项业务断言通过。"
              "前端页面、静态资源、REST API、课程记忆隔离、AI 辅助功能、错题闭环、"
              "硬件联动与异常处理均已覆盖。", ""]
    with open(os.path.join(OUT_DIR, "演示验收报告.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  数据已保存：{os.path.join(OUT_DIR, 'demo_results.json')}")
    print(f"  报告已保存：{os.path.join(OUT_DIR, '演示验收报告.md')}")
    return 0 if (passed == total and http_ok == http_total) else 1


if __name__ == "__main__":
    sys.exit(main())
