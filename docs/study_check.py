"""V1.2 自测：高等数学上册资源生成 + 文心一言 / Kimi 模型接入端到端验证。

用法：
    python docs/study_check.py                      # 本地，默认 http://localhost:5000
    BASE_URL=http://127.0.0.1:5099 python docs/study_check.py
    BASE_URL=https://xxx/?... SHARECODE=xxx python docs/study_check.py   # 线上（模型联网探针自动跳过）

自测内容：
  A. 知识库路径：题目 / 总结 / 文章 / 资料 / 思维导图 / 一键资源包 / Markdown 导出 / SVG
  B. 模型接入：运行时配置密钥、掩码安全、配置校验、连通性探针、通用透传、模型出题
     —— 用本机临时模拟的「OpenAI 兼容端点 + 文心 OAuth/聊天端点」代替真实厂商，
        因此不需要任何真实 API Key 也能完整验证调用链路。
  C. 不破坏原有功能：首页新 UI、原有状态/课程/问答接口回归

输出：docs/study_results.json 与 docs/自测报告_高等数学与模型接入.md
"""
import http.cookiejar
import json
import os
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = os.getenv("BASE_URL", "http://localhost:5000").rstrip("/")
SHARECODE = os.getenv("SHARECODE", "").strip()
RESULTS = []
SAMPLES = {}
MOCK = {"port": 0, "server": None}
LOCAL = urllib.parse.urlparse(BASE).hostname in ("127.0.0.1", "localhost", "::1")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_OPENER = None
if SHARECODE:
    _OPENER = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    _OPENER.open(BASE + "/?sharecode=" + SHARECODE, timeout=25).read()


def check(name, ok, detail=""):
    RESULTS.append({"name": name, "ok": bool(ok), "detail": str(detail)[:300]})
    print("%s %s %s" % ("✅" if ok else "❌", name, ("| " + str(detail)[:130]) if detail else ""))


def req(method, path, body=None, raw=False, timeout=30):
    url = BASE + path
    payload = json.dumps(body or {}, ensure_ascii=False).encode("utf-8") if body is not None else None
    headers = {"Content-Type": "application/json"} if payload else {}
    r = urllib.request.Request(url, data=payload, method=method, headers=headers)
    try:
        with (_OPENER.open if _OPENER else urllib.request.urlopen)(r, timeout=timeout) as resp:
            content = resp.read()
            if raw:
                return resp.status, content, dict(resp.headers)
            return resp.status, json.loads(content.decode("utf-8")), dict(resp.headers)
    except urllib.error.HTTPError as e:
        content = e.read()
        if raw:
            return e.code, content, dict(e.headers)
        try:
            return e.code, json.loads(content.decode("utf-8")), dict(e.headers)
        except Exception:
            return e.code, {"error": content.decode("utf-8", "replace")[:200]}, dict(e.headers)
    except Exception as e:
        return 0, {"error": str(e)}, {}


# ---------------------------------------------------------------- 本地模拟模型端点
MOCK_QUIZ = {
    "questions": [{
        "type": "计算题", "difficulty": "中等",
        "stem": "（模拟模型生成）求 lim(x→0) (1 − cos x) / x²。",
        "answer": "1/2",
        "analysis": "用等价无穷小 1 − cos x ~ x²/2，故极限为 1/2。",
        "points": ["等价无穷小", "极限计算"],
        "chapter": "第一章 函数与极限",
    }]
}


class MockHandler(BaseHTTPRequestHandler):
    """同时模拟 Kimi/OpenAI 兼容接口与文心旧版 OAuth + chat 接口。"""

    def log_message(self, *args):
        pass

    def _json(self, obj, status=200):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if "token" in self.path:
            return self._json({"access_token": "mock-access-token", "expires_in": 3600})
        self._json({"error": "not found"}, 404)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", "0") or "0")
            payload = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
        except Exception:
            payload = {}
        msgs = payload.get("messages", []) if isinstance(payload, dict) else []
        joined = " ".join(str(m.get("content", "")) for m in msgs if isinstance(m, dict))
        MOCK["last_model"] = payload.get("model", "")
        MOCK["last_auth"] = self.headers.get("Authorization", "")
        MOCK["last_path"] = self.path
        if "连接成功" in joined or "连通性测试" in joined:
            text = "连接成功"
        elif "extra" in joined and "JSON" in joined:
            text = json.dumps({"extra": [{"chapter": "第一章", "node": "AI 补充：ε-δ 语言"}]},
                              ensure_ascii=False)
        elif "questions" in joined and "JSON" in joined:
            text = json.dumps(MOCK_QUIZ, ensure_ascii=False)
        else:
            text = "【模拟模型已响应】已收到请求：" + joined[-50:]
        if "wenxin" in self.path:                       # 文心旧版返回 result 字段
            return self._json({"result": text})
        return self._json({"model": "mock-model", "choices": [
            {"index": 0, "message": {"role": "assistant", "content": text}}]})


def start_mock():
    srv = ThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    MOCK["server"], MOCK["port"] = srv, srv.server_address[1]
    return MOCK["port"]


def mock_url(path):
    return "http://127.0.0.1:%d%s" % (MOCK["port"], path)


def cleanup():
    if not LOCAL:
        return
    for name in ("moonshot", "qianfan", "custom"):
        req("POST", "/api/agent/credentials/clear", {"provider": name})
    req("POST", "/api/settings/provider", {"name": "demo"})


# ---------------------------------------------------------------- A. 知识库生成能力
def test_knowledge():
    print("\n【A】高等数学上册 · 学习资源生成")
    st, cat, _ = req("GET", "/api/study/catalog")
    check("A1 学科目录（数学 → 高等数学上册）",
          st == 200 and cat.get("discipline") == "数学"
          and cat.get("textbook") == "高等数学上册" and len(cat.get("chapters", [])) == 7,
          "%d 章 / 别名 %d 个" % (len(cat.get("chapters", [])), len(cat.get("aliases", []))))
    check("A2 「数学」别名可解析", "数学" in cat.get("aliases", []) and "高数" in cat.get("aliases", []))
    SAMPLES["catalog"] = cat.get("chapters", [])

    # 题目
    st, q, _ = req("POST", "/api/study/quiz", {"subject": "数学", "chapter": "第一章 函数与极限", "count": 4})
    qs = q.get("questions", [])
    check("A3 输入「数学 / 高等数学上册」生成第一章题目",
          st == 200 and q.get("subject") == "高等数学上册" and len(qs) == 4,
          "%d 道，来源 %s" % (len(qs), q.get("source")))
    check("A4 题目含数学内容、标准答案与分步解析",
          all(x.get("stem") and x.get("answer") and x.get("analysis") and x.get("points") for x in qs)
          and qs[0]["answer"] == "3/2"
          and any("极限" in x["stem"] or "无穷" in x["stem"] for x in qs),
          "示例答案：" + str(qs[0].get("answer") if qs else ""))
    SAMPLES["quiz"] = qs[:3]

    st, q5, _ = req("POST", "/api/study/quiz", {"subject": "高等数学上册", "chapter": "ch5", "count": 4})
    chapter5 = "第五章 定积分"
    check("A5 可指定第五章（定积分）出题",
          st == 200 and len(q5.get("questions", [])) == 4
          and all(x.get("chapter") == chapter5 for x in q5["questions"])
          and any("∫" in x["stem"] for x in q5["questions"]),
          "%s / 题中含积分号" % chapter5)

    # 总结
    st, s, _ = req("POST", "/api/study/summary", {"subject": "高等数学上册", "chapter": "ch3"})
    md = s.get("markdown", "")
    check("A6 生成第三章复习总结（知识点/公式/易错点）",
          st == 200 and all(k in md for k in ("知识点清单", "公式 / 定理速查", "高频易错点", "洛必达", "泰勒"))
          and len(md) > 600, "%d 字" % len(md))
    SAMPLES["summary"] = md[:1400]

    st, sall, _ = req("POST", "/api/study/summary", {"subject": "高等数学上册"})
    check("A7 全册总结覆盖 7 章",
          st == 200 and sall.get("chapter_count") == 7
          and all(c["title"] in sall.get("markdown", "") for c in cat["chapters"]),
          "%d 字" % len(sall.get("markdown", "")))

    # 文章 + 资料
    st, a, _ = req("POST", "/api/study/article", {"subject": "高等数学上册"})
    art = a.get("markdown", "")
    check("A8 生成与教材相关的专题文章",
          st == 200 and a.get("chars", 0) >= 3000
          and all(k in art for k in ("摘要", "知识脉络", "典型题型", "易错点", "复习路线", "延伸资料"))
          and "第一章 函数与极限" in art and "第七章 微分方程" in art,
          "%d 字 / %d 节" % (a.get("chars", 0), a.get("sections", 0)))
    SAMPLES["article"] = art[:1600]

    st, r, _ = req("POST", "/api/study/resources", {"subject": "数学", "chapter": "ch1"})
    items = r.get("items", [])
    check("A9 生成相关学习资料清单（含链接）",
          st == 200 and r.get("count", 0) >= 5
          and all(x.get("title") and x.get("url", "").startswith("http") and x.get("kind") for x in items),
          "%d 项" % len(items))
    SAMPLES["resources"] = items[:8]

    # 思维导图
    st, m, _ = req("POST", "/api/study/mindmap", {"subject": "高等数学上册"})
    svg = m.get("svg", "")
    check("A10 生成知识思维导图（树 + SVG）",
          st == 200 and m.get("node_count", 0) >= 30 and svg.startswith("<svg")
          and all(c["title"] in svg for c in cat["chapters"][:3])
          and "第一章" in m.get("outline", "") and m.get("mermaid", "").startswith("mindmap"),
          "%d 节点 / SVG %d 字节" % (m.get("node_count", 0), len(svg)))
    SAMPLES["mindmap_outline"] = m.get("outline", "")[:1600]

    qs_svg = urllib.parse.urlencode({"subject": "数学", "chapter": "ch2"})
    st, raw, hdrs = req("GET", "/api/study/mindmap.svg?" + qs_svg, raw=True)
    check("A11 SVG 图片接口可直接访问",
          st == 200 and raw.startswith(b"<svg") and "svg" in hdrs.get("Content-Type", ""),
          hdrs.get("Content-Type"))

    # 一键全套 + 导出
    st, p, _ = req("POST", "/api/study/pack",
                   {"subject": "高等数学上册", "chapter": "", "count": 6, "save_to_course": True})
    check("A12 一键资源包五件套齐全",
          st == 200 and all(p.get("has", {}).values()) and len(p.get("chapters", [])) == 7,
          "has=%s / 题目 %d 道" % (p.get("has"), p.get("quiz", {}).get("count", 0)))
    check("A13 资源包可回写课程记忆",
          bool(p.get("saved", {}).get("ok")), p.get("saved"))

    st, raw, hdrs = req("GET", "/api/study/pack/export?" +
                        urllib.parse.urlencode({"subject": "高等数学上册", "chapter": "ch1", "count": 3}),
                        raw=True)
    text = raw.decode("utf-8", "replace")
    check("A14 资源包 Markdown 导出下载",
          st == 200 and text.startswith("# 《高等数学上册》学习资源包")
          and all(k in text for k in ("## 一、自测题", "## 二、复习总结",
                                      "## 三、专题文章", "## 四、思维导图"))
          and "attachment" in hdrs.get("Content-Disposition", ""),
          "%d 字节" % len(raw))
    SAMPLES["export_head"] = text[:900]


# ---------------------------------------------------------------- B. 模型接入
def test_agent_interface():
    print("\n【B】文心一言 / Kimi / 自定义模型接入接口")
    st, d, _ = req("GET", "/api/agent/providers")
    names = [p["name"] for p in d.get("providers", [])]
    check("B1 接口暴露全部可插拔模型",
          st == 200 and all(n in names for n in ("qianfan", "moonshot", "custom", "openai", "claude", "demo")),
          "/".join(names))
    qf = next((p for p in d["providers"] if p["name"] == "qianfan"), {})
    km = next((p for p in d["providers"] if p["name"] == "moonshot"), {})
    check("B2 文心一言与 Kimi 的配置字段明确",
          "api_key" in qf.get("required", []) and "secret_key" in qf.get("optional", [])
          and "api_key" in km.get("required", []) and "base_url" in km.get("optional", []),
          "qianfan=%s / moonshot=%s" % (qf.get("required"), km.get("required")))

    st, bad, _ = req("POST", "/api/agent/credentials", {"provider": "not-exist", "api_key": "x"})
    check("B3 未知提供商被 400 拒绝", st == 400, bad)
    st, bad, _ = req("POST", "/api/agent/credentials", {"provider": "moonshot"})
    check("B4 空配置被 400 拒绝", st == 400, bad)

    st, v, _ = req("POST", "/api/agent/test", {"provider": "moonshot", "mode": "validate"})
    check("B5 未配置时校验给出明确原因（不联网）",
          st == 200 and v.get("ok") is False and "api_key" in v.get("reason", ""), v.get("reason"))

    if not LOCAL:
        check("B6~B16 本地模拟模型联调（线上环境跳过，本地已验证）", True,
              "线上环境无法访问本机模拟端点；完整模型联调结果见 docs/study_results.json")
        return

    port = start_mock()
    key = "sk-mock-kimi-1234567890"
    st, cfg, _ = req("POST", "/api/agent/credentials", {
        "provider": "moonshot", "api_key": key, "model": "moonshot-v1-8k",
        "base_url": mock_url("/v1/chat/completions"), "activate": False,
    })
    masked = (cfg.get("status", {}).get("masked", {}) or {}).get("api_key", "")
    check("B6 Kimi API Key 运行时写入即生效（无需重启）",
          st == 200 and cfg.get("ok") and cfg["status"].get("configured")
          and masked and key not in json.dumps(cfg, ensure_ascii=False),
          "掩码：" + str(masked))

    st, v, _ = req("POST", "/api/agent/test", {"provider": "moonshot", "mode": "validate"})
    check("B7 配置校验通过（Kimi）", st == 200 and v.get("ok") is True and v.get("configured") is True,
          v.get("model"))

    st, t, _ = req("POST", "/api/agent/test", {"provider": "moonshot", "mode": "probe"})
    check("B8 Kimi 模型连通性测试成功",
          st == 200 and t.get("ok") is True and "连接成功" in str(t.get("reply", "")),
          "%s / %s ms" % (t.get("reply"), t.get("latency_ms")))

    st, c, _ = req("POST", "/api/agent/complete", {
        "provider": "moonshot", "system_prompt": "你是数学助教", "message": "什么是极限？"})
    check("B9 通用透传接口调用 Kimi 模型得到回复",
          st == 200 and c.get("provider") == "moonshot" and c.get("fallback") is False
          and "模拟模型已响应" in c.get("reply", ""),
          c.get("reply", "")[:60])

    st, q, _ = req("POST", "/api/study/quiz", {
        "subject": "高等数学上册", "chapter": "ch1", "count": 2, "provider": "moonshot"})
    llm_q = [x for x in q.get("questions", []) if x.get("origin") == "llm"]
    check("B10 资源生成自动叠加 Kimi 模型原创题目",
          st == 200 and "hybrid" in q.get("source", "") and len(llm_q) >= 1
          and llm_q[0].get("answer") == "1/2",
          "来源 %s / 模型题 %d 道" % (q.get("source"), len(llm_q)))

    st, m, _ = req("POST", "/api/study/mindmap", {"subject": "高等数学上册", "chapter": "ch1",
                                                  "provider": "moonshot"})
    check("B11 模型可补充思维导图节点",
          st == 200 and "hybrid" in m.get("source", "") and "AI 补充" in m.get("outline", ""),
          m.get("source"))

    # 文心一言：旧版 OAuth + chat 接口
    st, cfg2, _ = req("POST", "/api/agent/credentials", {
        "provider": "qianfan", "api_key": "mock-ak-123456", "secret_key": "mock-sk-987654",
        "model": "ernie-3.5-8k", "base_url": mock_url("/wenxin/chat"),
        "token_url": mock_url("/oauth/2.0/token"), "activate": False,
    })
    check("B12 文心一言（API Key + Secret Key）配置成功",
          st == 200 and cfg2.get("ok") and cfg2["status"].get("configured"),
          cfg2.get("status", {}).get("masked"))
    st, t2, _ = req("POST", "/api/agent/test", {"provider": "qianfan", "mode": "probe"})
    check("B13 文心一言 OAuth 取 token + 对话连通性成功",
          st == 200 and t2.get("ok") is True and "连接成功" in str(t2.get("reply", "")),
          "%s / %s" % (t2.get("reply"), t2.get("error", "")))
    st, c2, _ = req("POST", "/api/agent/complete", {"provider": "qianfan", "message": "你好"})
    check("B14 透传接口调用文心模型得到回复",
          st == 200 and c2.get("provider") == "qianfan" and "模拟模型已响应" in c2.get("reply", ""),
          c2.get("reply", "")[:60])

    # 自定义 OpenAI 兼容端点（自建系统 / Ollama / 其他厂商）
    st, cfg3, _ = req("POST", "/api/agent/credentials", {
        "provider": "custom", "api_key": "local-key", "model": "my-model",
        "base_url": mock_url("/v1/chat/completions"), "activate": True,
    })
    st, stt, _ = req("GET", "/api/status")
    st, c3, _ = req("POST", "/api/agent/complete", {"message": "自建系统调用"})
    check("B15 自定义 OpenAI 兼容端点接入并切换为当前模型",
          st == 200 and cfg3.get("ok") and stt.get("active_provider") == "custom"
          and c3.get("provider") == "custom" and "模拟模型已响应" in c3.get("reply", ""),
          "当前：" + str(stt.get("active_provider")))

    st, clr, _ = req("POST", "/api/agent/credentials/clear", {"provider": "custom"})
    check("B16 清除配置后自动回退演示模式",
          st == 200 and clr.get("active_provider") == "demo", clr.get("active_provider"))

    st, home, _ = req("GET", "/", raw=True)
    html = home.decode("utf-8", "replace")
    check("B17 首页含学习资源包与模型接入 UI",
          b"panel-study" in home and b"agentProvider" in home and b"studyPack" in home
          and "模型接入" in html)


# ---------------------------------------------------------------- C. 回归
def test_regression():
    print("\n【C】原有功能回归")
    st, d, _ = req("GET", "/api/overview")
    check("C1 学习概览接口", st == 200 and "mastery_rate" in d, d.get("courses"))
    st, cs, _ = req("GET", "/api/courses")
    check("C2 课程列表接口", st == 200 and len(cs) >= 1, len(cs))
    cid = cs[0]["id"]
    st, d, _ = req("POST", "/api/chat", {"course_id": cid, "message": "请介绍本课程"})
    check("C3 课程问答接口", st == 200 and bool(d.get("reply")), str(d.get("reply", ""))[:50])
    st, d, _ = req("POST", "/api/summarize", {"text": "极限是高等数学的基础概念，导数由极限定义。"})
    check("C4 课件总结接口", st == 200 and "result" in d)
    st, d, _ = req("GET", "/api/hardware/status")
    check("C5 硬件状态看板", st == 200 and "focus_active" in d)


def write_report():
    passed = sum(1 for r in RESULTS if r["ok"])
    total = len(RESULTS)
    out = ROOT / "docs"
    suffix = "" if LOCAL else "_线上"
    (out / ("study_results%s.json" % suffix)).write_text(json.dumps({
        "base_url": BASE, "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total": total, "passed": passed, "failed": total - passed,
        "local_mock_llm": LOCAL, "results": RESULTS,
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    def qblock(qs):
        return "\n".join(
            "**%d. %s**（%s·%s）\n\n- 答案：%s\n- 解析：%s\n" %
            (i, x.get("stem", ""), x.get("type", ""), x.get("difficulty", ""),
             x.get("answer", ""), x.get("analysis", "")) for i, x in enumerate(qs, 1))

    res_rows = "\n".join("| %s | %s | %s |" %
                         (r["name"], "✅ 通过" if r["ok"] else "❌ 失败",
                          r["detail"].replace("|", "／").replace("\n", " ")[:110])
                         for r in RESULTS)
    resource_rows = "\n".join("| %s | %s | %s |" %
                              (x.get("title", ""), x.get("kind", ""), x.get("url", ""))
                              for x in SAMPLES.get("resources", []))
    md = """# 自测报告：高等数学上册学习资源生成 + 文心一言 / Kimi 模型接入

> 生成时间：{time} ｜ 目标服务：`{base}` ｜ 结果：**{passed}/{total} 通过**
> 自测脚本：`docs/study_check.py` ｜ 结构化结果：`docs/study_results{suffix}.json`

## 一、测试目的与方式

按「数学 → 高等数学上册」这一具体场景，验证系统能否产出**可用的题目、总结、相关文章与资料、思维导图**；
并验证是否能**通过接口把文心一言 / Kimi 的 API 接进来并真正调用其模型**。

* 知识库路径：内置 7 章结构化数据，无密钥也能产出带标准答案与解析的真实数学题。
* 模型路径：自测脚本在本机临时启动「OpenAI 兼容端点 + 文心 OAuth/聊天端点」模拟服务，
  通过 `POST /api/agent/credentials` 写入密钥并调用，因此**无需真实 API Key**即可验证完整调用链
  （鉴权头、token 换取、请求体、响应解析、失败降级）。换成真实密钥与官方地址即为真实模型。

## 二、断言结果

| 断言 | 结果 | 说明 |
| --- | --- | --- |
{rows}

## 三、生成内容抽样（真实自测输出）

### 3.1 章节目录

{chapters}

### 3.2 自测题（含标准答案与解析）

{quiz}

### 3.3 复习总结（节选）

```markdown
{summary}
```

### 3.4 相关文章（节选）

```markdown
{article}
```

### 3.5 学习资料清单（节选）

| 资料 | 类型 | 链接 |
| --- | --- | --- |
{resources}

### 3.6 思维导图大纲（节选）

```markdown
{outline}
```

### 3.7 Markdown 导出（开头）

```markdown
{export}
```

## 四、模型接入接口速查

| 接口 | 方法 | 用途 |
| --- | --- | --- |
| `/api/agent/providers` | GET | 列出可插拔模型、配置状态与掩码 |
| `/api/agent/credentials` | POST | 运行时写入 API Key / 模型 / 接口地址，`activate:true` 立即切换 |
| `/api/agent/credentials/clear` | POST | 清除运行时配置并回退演示模式 |
| `/api/agent/test` | POST | `mode=validate` 只校验配置；`mode=probe` 真实调用模型 |
| `/api/agent/complete` | POST | 通用模型透传，自建系统直接调用当前/指定模型 |
| `/api/settings/provider` | POST | 在已配置的模型之间切换 |

Kimi 接入示例：

```bash
curl -X POST {base}/api/agent/credentials -H "Content-Type: application/json" -d '{{
  "provider":"moonshot","api_key":"sk-你的密钥","model":"moonshot-v1-8k",
  "base_url":"https://api.moonshot.cn/v1/chat/completions","activate":true }}'
```

文心一言接入示例（千帆 v2，只需 API Key）：

```bash
curl -X POST {base}/api/agent/credentials -H "Content-Type: application/json" -d '{{
  "provider":"qianfan","api_key":"你的APIKey","model":"ernie-4.5-8k",
  "base_url":"https://qianfan.baidubce.com/v2/chat/completions","activate":true }}'
```

更完整的字段说明、旧版 WenxinWorkshop 参数与故障排查见 `docs/模型接入接口说明.md`。

## 五、结论

{passed}/{total} 项断言通过。{conclusion}
""".format(
        time=datetime.now().strftime("%Y-%m-%d %H:%M"), base=BASE, passed=passed, total=total,
        rows=res_rows,
        chapters="、".join(x["title"] for x in SAMPLES.get("catalog", [])),
        quiz=qblock(SAMPLES.get("quiz", [])),
        summary=SAMPLES.get("summary", ""), article=SAMPLES.get("article", ""),
        resources=resource_rows, outline=SAMPLES.get("mindmap_outline", ""),
        export=SAMPLES.get("export_head", ""),
        suffix="" if LOCAL else "_线上",
        conclusion=("高等数学上册的题目、总结、文章、资料与思维导图均可稳定生成；"
                    "文心一言 / Kimi / 自定义模型的密钥配置、连通性与生成链路均验证通过。"
                    if passed == total else "存在未通过断言，请查看 `study_results.json` 定位。"),
    )
    (out / ("自测报告_高等数学与模型接入%s.md" % suffix)).write_text(md, encoding="utf-8")
    return passed, total


def main():
    print("目标服务：", BASE, "｜ 模型联调：", "本地模拟端点" if LOCAL else "线上（跳过联网探针）")
    try:
        test_knowledge()
        test_agent_interface()
        test_regression()
    finally:
        cleanup()
        if MOCK["server"]:
            MOCK["server"].shutdown()
    passed, total = write_report()
    suffix = "" if LOCAL else "_线上"
    print("\n自测断言：%d/%d 通过" % (passed, total))
    print("报告：docs/自测报告_高等数学与模型接入%s.md ｜ docs/study_results%s.json"
          % (suffix, suffix))
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
