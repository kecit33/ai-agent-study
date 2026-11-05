# 从选题到上线：我做了一款「把大模型嵌进课程场景」的校园学习陪伴助手（附完整验收数据）

> 这是智能体开发课程作业的完整复盘。项目叫 **AI 校园学习陪伴助手**，是一款 B/S 架构的 Web 应用：把 GPT / 文心一言 / Kimi / Claude 以**可插拔**方式接进自己写的系统里，围绕「课程」做记忆隔离与错题闭环，最后真正上线跑通给师生验收。
>
> 本文所有功能、代码、截图与数据都来自实际运行的项目，不是设计稿。`demo_results.json` 里存着每一个 HTTP 请求的真实响应，文末给出复现命令。项目于 2026-11-09 答辩。

![项目标志](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/logo.png)

---

## 一、为什么做：五个来自身边的真实痛点

作业要求"选题必须来自真实调研，禁止虚构"。我没有编一份问卷数据，而是从身边同学日常复习的实际过程里梳理出五条高频痛点（这也是选题报告里的原文）：

| # | 调研发现的痛点 | 项目里的对应功能 | 实现要点 |
|---|---|---|---|
| 1 | 上课笔记零散、课件看不懂，想快速提炼知识点并生成复习提纲 | 课件总结 | 按句切分提取知识点 + 五段式考点提纲 |
| 2 | 遇到难题缺少引导式讲解，容易直接抄答案或无从下手 | 习题辅导 | 系统提示词强制「先给思路、不甩答案」 |
| 3 | 考前不知道怎么规划复习，难以安排节奏 | 复习计划 | 科目 + 剩余天数 → 按天分阶段排期 |
| 4 | 通用大模型不了解本校课件和授课重点，回答容易跑偏 | **课程记忆智能体** | 按 `course_id` 隔离资料，作为 system 上下文注入 |
| 5 | 复习缺少错题整理与自测的一体化工具，过程没有闭环 | **AI 错题本** | 录题 → 错因诊断 → 定向变式题 → 标记掌握 |

第 4 和第 5 条是关键的差异化判断：**通用聊天框不缺，缺的是"绑定我这门课"的垂直场景**。所以我没有做一个套壳聊天页，而是让课程成为系统里的一等公民——先建课程、传资料，再问答；错题也挂在课程下，形成学习闭环。

![功能思维导图](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/mindmap.png)

*图 1　功能思维导图：基础功能、杀手级功能、技术架构、硬件联动与创新价值五条主线。*

---

## 二、先看成品：一个浏览器里就能跑的 Web 应用

![应用首页](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/ui-home.png)

*图 2　应用首页（真实运行截图）。顶部是智能体状态徽标，导航共 8 个模块，课程选择器在所有需要上下文的模块间共享。*

八个模块分别是：智能问答、课件总结、习题辅导、复习计划、课程记忆、错题本、硬件联动、设置。前端是**原生 HTML/CSS/JS**，没有 Vue/React、没有构建步骤，一个 `static/` 目录就是全部前端资源。

选择原生前端不是偷懒，而是这个项目的验收场景很特殊：答辩机房、老师临时用自己的手机打开链接、助教在没网的环境里本地起服务。零构建意味着零意外。

---

## 三、系统架构：分层清晰，但有一个"双后端"

![系统架构图](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/architecture.png)

*图 3　需求文档中的系统架构图。图中「Flask 后端 (app.py)」是设计阶段的方案；**实际部署的默认入口是等价的 `server.py`**（纯标准库实现），两者共用同一套业务层、暴露完全相同的 REST API，可以随时互换，详见第七节。*

分层如下：

- **表现层**：`static/index.html` + `style.css` + `app.js`，8 个 tab 切换，通过 `fetch` 调 `/api/*`。
- **服务层**：`server.py`（默认）或 `app.py`（Flask 版），负责路由、静态文件、参数校验、统一 JSON 响应、复习任务到点调度（30 秒轮询一次）。
- **业务层** `services/`：`course.py`（课程与课程记忆上下文）、`tasks.py`（问答/总结/辅导/计划/错因/变式）、`wrong_questions.py`（错题闭环）。
- **智能体层** `agents/`：`AgentProvider` 抽象 + 四个真实厂商实现 + `DemoProvider` 兜底 + `factory.py` 工厂。
- **数据层**：SQLite，6 张表 —— `courses`、`course_materials`、`conversations`、`wrong_questions`、`review_tasks`、`settings`。
- **硬件层**（可选）：`hardware/esp32.py` 下发 Webhook，配 `esp32_firmware.ino` 固件点亮 LED + 蜂鸣器。

目录结构（摘自我的 README）：

```text
ai-campus-companion/
├─ server.py              # 【默认入口】零依赖 Web 服务器（Python 标准库）
├─ app.py                 # Flask 版后端（需 pip install，生产可选）
├─ config.py / db.py      # 配置中心 / SQLite 初始化
├─ agents/                # 可插拔智能体层
│  ├─ base.py             #   AgentProvider 抽象基类
│  ├─ openai_provider.py  #   GPT
│  ├─ qianfan_provider.py #   文心一言
│  ├─ moonshot_provider.py#   Kimi
│  ├─ claude_provider.py  #   Claude
│  ├─ demo_provider.py    #   内置演示模式（无密钥兜底）
│  └─ factory.py          #   工厂 + 自动回退
├─ services/              # 业务服务层
├─ hardware/              # ESP32 接口 + Arduino 固件
├─ static/                # 原生前端
├─ docs/                  # 需求文档、PPT、验收脚本与数据
├─ render.yaml            # Render Blueprint
└─ deploy/pythonanywhere_wsgi.py
```

技术选型上刻意保持"低门槛"：`Flask + 原生前端 + SQLite`。理由很直接——作业要交付的是**能跑起来、能被检查**的系统，不是技术栈展示；三个人以内的课程小组，任何一种引入消息队列、向量库、前端工程化的方案都会显著抬高失败概率。

---

## 四、核心设计一：可插拔的智能体接口

作业明确要求"智能体必须嵌入自研系统"，而不是给一个官方聊天页链接。我的做法是先定义一个极小的抽象，让业务层**只认识接口，不认识厂商**：

![类图](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/classdiagram.png)

*图 4　类图：Provider 抽象、四个真实实现、演示实现、工厂，以及服务层与数据实体。*

```python
# agents/base.py
class AgentProvider:
    """统一智能体接口。"""
    name = "base"
    label = "基础提供商"

    def complete(self, system_prompt: str, messages: list) -> str:
        """给定系统提示与对话历史，返回智能体回复文本。"""
        raise NotImplementedError

    def is_available(self) -> bool:
        """该提供商当前是否可用（如是否配置了密钥）。"""
        return True
```

所有业务函数都只写 `provider.complete(system, messages)`。厂商差异被完全关在各自的实现里：

| 厂商 | 接口地址 | 认证方式 | 消息格式差异 |
|---|---|---|---|
| OpenAI GPT | `api.openai.com/v1/chat/completions` | `Authorization: Bearer` | `system` 作为 messages 首条 |
| Kimi (Moonshot) | `api.moonshot.cn/v1/chat/completions` | `Authorization: Bearer` | OpenAI 兼容格式 |
| Anthropic Claude | `api.anthropic.com/v1/messages` | `x-api-key` + `anthropic-version: 2023-06-01` | **`system` 是顶层字段**，messages 只放 user/assistant |
| 百度文心一言 | `aip.baidubce.com/.../chat/completions` | 先用 AK/SK 换 `access_token`（内存缓存），作为参数附在 URL 上 | 自有格式，需单独适配 |

工厂负责按配置选择并兜底，这是"师生不用申请密钥也能验收"的关键：

```python
# agents/factory.py（节选）
def get_provider(name: str = None) -> AgentProvider:
    if name is None:
        name = get_active_provider_name()        # 从 settings 表读
    provider_cls = _PROVIDERS.get(name, DemoProvider)
    provider = provider_cls()
    if provider.is_available():
        return provider
    # 不可用时回退到内置演示模式，保证系统永远可响应
    return DemoProvider()
```

![设置页：五个提供商](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/ui-settings.png)

*图 5　设置页真实截图：四家厂商 + 内置演示模式共 5 个可选项，未配置密钥的会明确标注「将使用演示模式」，切换即时生效。*

这里必须坦白一件事，避免误导读者：**「演示模式」是规则化的模板应答，不是真的大模型推理**。它的价值是让系统在没有任何密钥、没有外网、没有 pip 包的环境里仍能把**全部业务流程**走通——建课程、传资料、问答、总结、错题闭环一个不少。填入任意一家密钥后，同一个 `complete()` 调用就会换成真实模型输出。`/api/status` 的真实响应也如实反映了这一点：

```json
{
  "active_provider": "demo",
  "providers": [
    {"name": "openai",   "label": "OpenAI GPT",                "available": false, "active": false},
    {"name": "moonshot", "label": "Kimi (Moonshot)",           "available": false, "active": false},
    {"name": "claude",   "label": "Anthropic Claude",          "available": false, "active": false},
    {"name": "qianfan",  "label": "百度文心一言",                "available": false, "active": false},
    {"name": "demo",     "label": "内置演示模式（无需密钥）",     "available": true,  "active": true}
  ]
}
```

密钥一律从环境变量（`.env`）读取，不写进代码、不落数据库，仓库里只有占位符模板 `.env.example`。

---

## 五、核心设计二：课程记忆 = 按课程隔离的上下文注入

这是我认为最值得写的一个设计。所谓"长期记忆"，在这里没有用向量数据库，而是**把课程资料拼进 system prompt**，用结构化标记划清边界：

```python
# services/course.py（节选）
def build_course_context(course_id: int) -> str:
    course = conn.execute("SELECT name FROM courses WHERE id=?", (course_id,)).fetchone()
    mats = conn.execute(
        "SELECT title, content FROM course_materials WHERE course_id=? ORDER BY id",
        (course_id,)).fetchall()
    cname = course["name"] if course else "未知课程"
    parts = [f"【课程记忆】课程：{cname}",
             f"你是一款校园学习陪伴助手，当前绑定的课程是「{cname}」。" ]
    parts.append("以下是该课程学生已上传的学习资料（你的回答必须严格限定在此课程范围内，"
                 "不超纲、不跑偏；若资料未覆盖，请说明并建议复习方向）：\n")
    for i, m in enumerate(mats, 1):
        parts.append(f"（资料{i}：{m['title']}）\n" + m["content"][:4000])
    ...
    return "\n".join(parts)
```

问答时再叠加最近 12 条对话历史：

```python
# services/tasks.py（节选）
def chat(course_id: int, message: str, provider_name: str = None) -> str:
    system = "【MODE:chat】\n" + build_course_context(course_id)
    history = _history(course_id)                       # 最近 12 轮
    provider = get_provider(provider_name)
    reply = provider.complete(system, history + [{"role": "user", "content": message}])
    _save_turn(course_id, "user", message)
    _save_turn(course_id, "assistant", reply)
    return reply
```

有两个细节是**跑起来之后才补上的**，很值得记一笔：

1. `【课程记忆】课程：{cname}` 这个结构化标记不能省。最初只有自然语言描述，演示模式解析不出课程名，界面上的回复一直显示"当前课程"这种含糊字样。
2. **任务指令必须放进 system，user 消息只放原始内容**。我一开始把「请总结以下课件：」直接拼在用户文本前面，结果演示模式把这句指令本身也当成知识点提取出来了，总结结果第一行赫然是"请总结以下课件"。现在每个任务都用 `【MODE:xxx】` 在 system 里标明类型：

```python
system = ("【MODE:summarize】你是课件总结助手。用户消息即为课件原文。"
          "请提炼关键知识点，并生成结构化的复习考点提纲。")
```

![课程记忆问答真实截图](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/ui-chat-reply.png)

*图 6　真实交互截图：在「示例课程：数据结构」下提问「完全二叉树有什么特点？」，回复首行明确显示课程记忆已绑定到该课程。右上角徽标为「内置演示模式（无需密钥）」。*

验收脚本专门构造了 A、B 两门课程验证隔离，两次 `/api/chat` 的真实响应：

```text
POST /api/chat  {"course_id": 12, "message": "完全二叉树有什么特点？"}
→ （演示模式 · 课程记忆已绑定「验收课程A_数据结构_1793874678」）
  你问的是：完全二叉树有什么特点？…

POST /api/chat  {"course_id": 13, "message": "进程和线程的区别？"}
→ （演示模式 · 课程记忆已绑定「验收课程B_操作系统_1793874678」）
  你问的是：进程和线程的区别？…
```

两个 `course_id` 各自绑定各自课程，互不串味——隔离断言通过。

---

## 六、核心设计三：AI 错题本不是"存个题"，是一个闭环

很多同类项目做到"录入错题 + 列表展示"就停了。我把学习闭环补齐成四步：

```text
录入题目/我的答案/正确答案
        ↓
POST /api/wrong-questions/{id}/analyze
        ↓  【MODE:error_analysis】独立诊断，定位薄弱知识点
        ↓  【MODE:variant】按原题生成同类变式题
        ↓
定向重做 → POST /api/wrong-questions/{id}/master 标记掌握
        ↓
GET /api/wrong-questions?unmastered=1 只剩还没吃透的题
```

实现上，`analyze_and_variant()` 会先检查该题是否已有错因，没有才调用智能体推断，并把结果**落库**，避免重复请求：

```python
# services/wrong_questions.py（节选）
def analyze_and_variant(wid: int, provider_name: str = None) -> dict:
    row = ...  # 取错题
    text = f"题目：{row['question']}\n我的答案：{row['user_answer']}\n正确答案：{row['correct_answer']}\n"
    if not row["error_reason"]:
        reason = analyze_error(text, provider_name=provider_name)   # 独立 MODE
        # UPDATE wrong_questions SET error_reason=? 落库
    else:
        reason = row["error_reason"]
    variant = generate_variant(text, provider_name=provider_name)
    return {"id": wid, "error_reason": reason, "variant": variant}
```

这里也踩过一个坑：最初错因分析复用了普通 `chat()`，因为它带的是 `【MODE:chat】`，返回的是一段通用课程问答，**根本不是错因诊断**。后来拆出独立的 `analyze_error()` 与 `【MODE:error_analysis】` 才修正。

一道真实错题的诊断结果（摘自 `demo_results.json`）：

```text
题目：求斐波那契数列第 n 项，n=40
我的答案：直接递归 f(n)=f(n-1)+f(n-2)
正确答案：使用记忆化或递推，时间复杂度 O(n)

🔍 可能的错因归类：
  1. 方法选择：直接套用了最直观的解法，未评估其在本题输入规模下的代价。
  2. 概念边界：对该知识点适用条件与前提的理解不够完整。
  3. 复杂度 / 边界意识：未检查解法在规模增大或边界输入下是否仍成立。

📌 薄弱知识点定位：建议回到该知识点的基础定义、复杂度分析与典型例题重新过一遍。
✅ 改进建议：先列出候选解法并比较代价 → 用小样本手算验证 → 再做同类题巩固。
```

同时生成的定向变式题会改变已知条件、把选择题改简答、给出错误做法让 student 找错，用于"同类题巩固"。

![错题本页面](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/ui-wrong.png)

*图 7　错题本模块界面：录题、按课程归档、错因分析、变式题与「标记已掌握」都挂在同一个页面。*

---

## 七、一次真实翻车：为什么又多写了一个 `server.py`

这一节我想如实写，因为它比功能清单更有价值。

项目第一版是 Flask 后端。开发机上 `pip install -r requirements.txt` 被网络代理拦截（502），装不上 Flask。当时我做了"全量 `py_compile` + 直接调用业务函数"的验证，六个功能都返回了非空结果，于是我认为系统没问题，交付了。

**但这个 Web 服务其实一次都没有真正启动过。** 我只测了 Python 函数，没测 HTTP 层：路由、静态文件、JSON 解析、状态码、Cookie、并发，全都没验证过。老师一句"我要检查的是 Web 应用"就把它戳穿了。

补救分两步：

**第一步，补一个零依赖运行层。** `server.py` 用 Python 标准库 `ThreadingHTTPServer` 实现，与 Flask 版共用 `db / agents / services / hardware`，暴露同一套 API 和页面，尊重 `PORT` 环境变量、绑定 `0.0.0.0`：

```python
# server.py（节选）
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
...
    def _dispatch(self, method):
        parsed = urlparse(self.path)
        path, query = parsed.path, parse_qs(parsed.query)
        if method == "GET" and not path.startswith("/api/"):
            self._serve_static(path)
            return
        for verb, pattern, handler in ROUTES:
            if verb == method and re.match(pattern, path):
                body = self._read_body() if method == "POST" else {}
                self._send_json(200, handler(m, body, query))
                return
        self._send_json(404, {"error": "接口不存在", "path": path})
```

于是 `python server.py` 就能起服务：Python 3.8+ 即可，**不需要 pip、不需要密钥、不需要联网**。答辩现场、机房、老师的电脑上都能直接跑。

**第二步，真正发 HTTP 请求。** 服务一起来，前面说的三个 bug 立刻暴露：

| # | 现象 | 根因 | 修复 |
|---|---|---|---|
| 1 | 课程记忆回复只显示"当前课程" | 上下文里缺可解析的结构化 `课程：名称` 标记 | `build_course_context()` 增加 `【课程记忆】课程：{cname}` |
| 2 | 课件总结把"请总结以下课件："当成知识点 | 任务指令拼进了 user 文本 | 指令统一移入 system，用 `【MODE:xxx】` 区分 |
| 3 | 错因分析返回一段通用闲聊 | 复用了 `chat()` 的 MODE | 新增 `analyze_error()` 与 `【MODE:error_analysis】` |

这三个问题，只测函数永远发现不了——因为函数都"正常返回了字符串"。**结论：可运行 ≠ 跑过 HTTP；验收要打真实请求。**

---

## 八、演示结果：26 个真实请求、30 项断言

线上地址（浏览器直接打开，手机也可以）：

```
https://ai-campus-companion.app.workbuddy.host/?sharecode=CEUN7FBTFJ
```

`sharecode` 是访问凭证，转发给师生时请原样保留，去掉会返回 403。

我写了 `docs/demo_check.py`，用标准库 `urllib` 发真实 HTTP 请求并逐项断言，结果落到 `docs/demo_results.json`、可读版落到 `docs/演示验收报告.md`。**本地与线上各跑一遍，结果一致**：

| 环境 | HTTP 请求状态 | 业务断言 |
|---|---|---|
| 本地 `localhost:5000` | 26 / 26 正确 | 30 / 30 通过 |
| 线上公网站点 | **26 / 26 正确** | **30 / 30 通过** |

26 个请求覆盖了完整链路（含异常分支）：

| 分组 | 请求 | 验证点 |
|---|---|---|
| 静态与状态 | `GET /`、`/static/css/*`、`/static/js/*`、`/api/status`、`/api/providers` | 页面/资源可访问，返回 5 个提供商 |
| 配置 | `POST /api/settings/provider` | 切换即时生效 |
| 课程记忆 | 新建课程 A/B、上传资料、读取资料、两门课各问答一次 | 上下文绑定正确、A/B 隔离成功 |
| 四大任务 | `/api/summarize`、`/api/tutor`、`/api/review-plan` | 含知识点与提纲、引导式不甩答案、逐日排期 |
| 错题闭环 | 录题 → 按课程查询 → 错因+变式 → 标记掌握 → 筛选未掌握 | 五步全部通过 |
| 硬件与调度 | `/api/review-tasks`、`/api/hardware/test` | 到点下发接口正常 |
| 异常分支 | 缺参数 400、重名 400、未知接口 404 | 参数校验与错误处理 |

几个真实响应摘录：

**课件总结**（`POST /api/summarize`）—— 提取 6 条知识点并给出五段式提纲：

```text
📌 提取的关键知识点：
  1. 栈是一种后进先出的线性结构     2. 队列是先进先出的线性结构
  3. 树是非线性层次结构             4. 图由顶点和边组成
  5. 哈希表支持平均O(1)查找         6. 二叉搜索树中序遍历有序
📝 建议的复习考点提纲：
  一、核心概念梳理  二、重点公式/定理  三、易混淆点对比
  四、典型例题思路  五、考前速记清单
```

**引导式习题辅导**（`POST /api/tutor`）—— 明确不给最终答案：

```text
我先不直接给答案，按「引导式讲解」帮你理清思路：
1. 题意复述… 2. 破题思路… 3. 第一步… 4. 第二步… 5. 自检…
👉 你先按这个步骤试一下，卡在哪一步告诉我，我再针对性提示。
```

**10 天复习计划**（`POST /api/review-plan`）—— 分阶段排期：

```text
第 1~2 天：基础回顾  第 3~4 天：重点突破  第 5~6 天：真题/例题演练
第 7~8 天：查漏补缺  第 9~10 天：冲刺复盘（每日 2~3 小时，配合错题本）
```

![课件总结界面](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/ui-summarize.png)

*图 8　课件总结：左侧粘贴课件文字，下方实时显示提取的知识点与考点提纲（真实演示模式输出）。*

![复习计划界面](https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/ui-plan.png)

*图 9　按科目与天数生成逐日复习计划。*

复现命令（无需任何第三方库）：

```bash
# 本地
python server.py
python docs/demo_check.py

# 线上
BASE_URL=https://ai-campus-companion.app.workbuddy.host \
SHARECODE=CEUN7FBTFJ python docs/demo_check.py
```

> 线上链接带分享鉴权：`demo_check.py` 会先用 `sharecode` 打开首页建立会话 Cookie，再带着 Cookie 调 API，和浏览器行为一致。

---

## 九、上线、开源与「逐步提交」

- **在线应用**：上面的公网链接，用 `python server.py` 启动，Build 阶段不需要装任何依赖。
- **代码仓库**：https://github.com/kecit33/ai-agent-study （Public，`main` 分支，40 个文件）。
- **部署配置**：根目录 `render.yaml` 是 Render Blueprint，声明了服务类型、`python server.py`、健康检查 `/api/status` 与 `ACTIVE_PROVIDER=demo`，在 Render 里关联仓库点 Apply 即可；另附 `deploy/pythonanywhere_wsgi.py` 给 PythonAnywhere 的 WSGI 场景。
- **需求与答辩材料**：`docs/软件需求规格说明书.docx`（含迭代记录表、项目标志、思维导图、类图、验收标准）、`docs/AI校园学习陪伴助手_答辩.pptx`（8 页）。

提交历史按模块拆成 **19 个独立 commit**，不是一次性打包：`骨架 → 数据层 → 智能体抽象/四厂商/工厂 → 业务服务 → 硬件 → Flask API → 零依赖 server → 前端 → 验收脚本 → 文档 → 部署配置 → README → 迭代记录 → 工程修复`。`git log --oneline` 能完整看到演进过程。

推送到 GitHub 时也遇到一串真实环境问题，顺手记录一下，供遇到同类情况的同学参考：连接器用的 GitHub App 凭据是**只读**的（写任何仓库都返回 `403 Resource not accessible by integration`），沙箱代理又只放行 `api.github.com` 而拦截 `github.com:443`，所以常规 `git push` 走不通。最后用本机已登录的 GitHub CLI 取 PAT，经 Git Data API 逐 commit 重建历史；空仓库下该 API 会返回 `409 Git Repository is empty`，需要先用 Contents API 建一个引导提交，再强制把 `main` 指向重建出的链尾。工具留在 `docs/push_to_github.py`。

---

## 十、诚实复盘：这个项目还差什么

写技术博客如果只写好话，价值就折半了。当前版本的局限：

1. **演示模式是规则化应答，不是真推理**。它保证流程可验，但内容质量不代表大模型能力；填密钥后才是真实模型输出。这一点在所有截图与响应里都标注了。
2. **课程记忆是"拼接 + 截断"**，每份资料取前 4000 字，没有分块、向量检索或 RAG。资料一多就会丢信息，长课件场景需要换成检索式上下文。
3. **SQLite 单文件、单实例**，没有用户体系、没有权限隔离、没有并发压测。目前是课程作业规模的原型，不是多租户 SaaS。
4. **ESP32 联动只做到接口 + 固件 + Webhook 下发测试**，没有实机联调截图，属于可选加分项，不影响主体功能。
5. **测试覆盖是端到端黑盒**（26 请求 / 30 断言），没有单元测试与前端自动化测试；异常分支只覆盖了参数校验、重名与 404。
6. 前后端没有做鉴权与速率限制，公网链接依赖平台侧的分享码保护，不能直接当生产系统用。

如果继续做，优先级会是：接一家真实密钥跑通完整链路并录屏 → 用检索替换全文拼接 → 补登录与多用户数据隔离 → 把 `demo_check.py` 扩成 CI 里的回归测试。

---

## 十一、一键复现

```bash
git clone https://github.com/kecit33/ai-agent-study.git
cd ai-agent-study
python server.py                 # 零依赖，访问 http://localhost:5000
python docs/demo_check.py        # 26 请求 / 30 断言
```

想接真实模型：

```bash
cp .env.example .env             # 填入任一厂商密钥
# ACTIVE_PROVIDER=openai / qianfan / moonshot / claude
python server.py
```

主要 API 一览：

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/status` `/api/providers` | 当前智能体与厂商可用性 |
| POST | `/api/settings/provider` | 切换智能体 |
| GET/POST | `/api/courses` | 课程列表 / 新建课程 |
| POST/GET | `/api/courses/{id}/materials` | 上传 / 读取课程资料 |
| POST | `/api/chat` | 带课程记忆的问答 |
| POST | `/api/summarize` `/api/tutor` `/api/review-plan` | 总结 / 引导辅导 / 复习计划 |
| GET/POST | `/api/wrong-questions` | 错题列表 / 录题 |
| POST | `/api/wrong-questions/{id}/analyze` | 错因诊断 + 定向变式题 |
| POST | `/api/wrong-questions/{id}/master` | 标记掌握 |
| GET/POST | `/api/review-tasks` | 复习任务与到点提醒 |
| POST | `/api/hardware/test` | ESP32 下发测试 |

---

## 附：配图清单与博客园发布说明

本文共 10 张图，全部是**项目实拍或项目内矢量图导出**，源文件在仓库 `docs/blog/assets/`：

| 文件 | 用途 |
|---|---|
| `logo.png` | 项目标志 |
| `mindmap.png` | 功能思维导图 |
| `architecture.png` | 系统架构图 |
| `classdiagram.png` | 类图 |
| `ui-home.png` | 应用首页 |
| `ui-chat-reply.png` | 课程记忆问答真实交互 |
| `ui-summarize.png` | 课件总结输出 |
| `ui-plan.png` | 复习计划输出 |
| `ui-wrong.png` | 错题本界面 |
| `ui-settings.png` | 五个智能体提供商 |

文章中的图片用的是 GitHub 仓库外链。**如果博客园里外链加载不出来**（部分网络环境访问 `raw.githubusercontent.com` 不稳定），把 `docs/blog/assets/` 下这 10 张 PNG 上传到博客园图床，再把文中的链接前缀

```text
https://raw.githubusercontent.com/kecit33/ai-agent-study/main/docs/blog/assets/
```

批量替换成博客园返回的图片地址即可，文件名保持不变。配图由 `docs/blog/build_images.py` 用无头浏览器自动生成（4 张 SVG 栅格化 + 6 张真实界面截图），可重复执行。

---

*项目为 2026 年智能体开发课程作业，答辩时间 2026-11-09。本文所有数据来自 `docs/demo_results.json`（执行时间 2026-11-05 18:31:24），欢迎在评论区指出问题。*
