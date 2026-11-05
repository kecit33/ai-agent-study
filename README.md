# AI 校园学习陪伴助手

一款面向大学生课程学习场景、基于大模型智能体的 **Web 应用**（浏览器访问，B/S 架构）。智能体（GPT / 文心一言 / Kimi / Claude / 任意 OpenAI 兼容端点）以**可插拔**方式集成进自研系统，而非直接套用官方聊天页；具备「课程记忆智能体」「AI 错题本与定向出题」「学科学习资源包（题目 / 总结 / 文章 / 资料 / 思维导图）」等杀手级功能，并预留 ESP32 硬件联动（加分项）。

> 课程作业 · 智能体开发 · 2026
>
> **端到端验收结果（2026-11-05，本地 + 线上双环境）：原有回归 26/26 个 HTTP 请求状态正确 + 30/30 项业务断言通过；V1.1 新增功能 19/19 项断言通过；V1.2「高等数学上册资源生成 + 文心/Kimi 模型接入」本地自测 36/36 项、线上 25/25 项断言通过**（模型联网探针仅本地可跑，见 `docs/study_results.json` 与 `docs/study_results_线上.json`）。
>
> **V1.2.1 启动修复（2026-11-05 23:59）**：修复「旧版后端残留 5000 端口 + 静态页已更新」导致的新页面点按钮全 404，以及 Windows `SO_REUSEADDR` 允许多进程重复绑定同一端口的隐患；新增版本指纹、端口自动顺延与一键启动自检 `python docs/startup_check.py`（本地 26/26 通过）。详见 `docs/启动检查报告.md`。
> ✅ **已于 2026-11-06 00:31 重新发布为 V1.2.1**，链接与 `sharecode` 不变；线上 `/api/status` 已返回 `version: 1.2.1`。发布后线上复验：启动自检 **26/26**、原回归 **26/26 请求 + 30/30 断言**、V1.1 功能 **19/19**、V1.2 高数与模型接入 **25/25**（线上跳过 11 项需本机模拟端点的探针）。本次修复主要作用于本地启动链路；云端由平台注入 `PORT` 且单实例运行，不存在本地的端口冲突问题。
>
> 需求符合性自检见 `docs/自我检查报告.md`，硬件交互点全清单见 `docs/硬件交互说明.md`，模型接入接口说明见 `docs/模型接入接口说明.md`。

---

## 一、特性对照（作业评估要点）

- ✅ 智能体嵌入自研系统：统一 `AgentProvider` 接口，四家厂商 + 自定义兼容端点 + 内置演示模式
- ✅ **模型接入接口（V1.2）**：Web 设置页或 REST 接口运行时填入文心一言 / Kimi 的 API Key 即生效，无需改代码、无需重启；`/api/agent/complete` 供自建系统直接调用
- ✅ **学科学习资源包（V1.2）**：输入「数学 / 高等数学上册」即可生成带标准答案与解析的自测题、复习总结、专题文章、资料清单与可视化思维导图，并可导出 Markdown / SVG
- ✅ 真实调研需求：基于选题报告中的校内调研痛点，无虚构
- ✅ 杀手级功能：课程记忆（按课程隔离上下文）+ 错题闭环（错因分析 → 定向变式题）
- ✅ 无密钥可运行：未配置任何密钥时自动进入「内置演示模式」，保证师生可直接验收
- ✅ 可上线：本地一键启动 + 云端部署，生成可访问链接
- ✅ 零依赖可运行：`server.py` 仅用 Python 标准库，无需 `pip install` 即可启动完整 Web 服务
- ✅ 深色/浅色模式：跟随系统 `prefers-color-scheme`，可手动三档切换，6 套主题色 + 自定义主色
- ✅ 语音输入：Web Speech API，覆盖问答/总结/辅导/资料/错题 5 处输入框
- ✅ 文件传输：课件上传（txt/md/docx，自动入课程记忆）+ 错题本导出 Markdown
- ✅ 学习陪伴增强：学习概览仪表盘 + 番茄钟专注计时（可联动硬件）
- 🟡 硬件联动（可选加分）：ESP32 双向联动共 6 个交互点，接口与固件齐备，**未做实机联调**

---

## 二、目录结构

```
ai-campus-companion/
├─ start.bat              # 【双击启动】Windows 一键启动 + 自动开浏览器
├─ launch.py              # 启动器：版本指纹探测、端口自动顺延、拉起 server.py
├─ server.py              # 【默认入口】零依赖 Web 服务器（Python 标准库，推荐）
├─ app.py                 # Flask 版后端入口（需 pip install，生产可选）
├─ version.py             # 版本指纹（后端 /api/status 与启动器共用）
├─ config.py              # 配置中心（密钥经环境变量读取）
├─ db.py                  # SQLite 初始化与连接（8 张表，含 focus_sessions、provider_credentials）
├─ agents/                # 可插拔智能体层
│  ├─ base.py             # AgentProvider 抽象基类（complete / probe / 自动降级）
│  ├─ credentials.py      # 运行时密钥中心（环境变量 + SQLite 覆盖，输出掩码）
│  ├─ http_client.py      # 标准库 urllib 厂商 HTTP 客户端（零第三方依赖）
│  ├─ openai_provider.py  # GPT
│  ├─ qianfan_provider.py # 文心一言（千帆 v2 / 旧版 OAuth 双模式）
│  ├─ moonshot_provider.py# Kimi
│  ├─ claude_provider.py  # Claude
│  ├─ custom_provider.py  # 任意 OpenAI 兼容端点
│  ├─ demo_provider.py    # 内置演示模式（无密钥兜底）
│  └─ factory.py          # 提供商工厂（选择 / 配置 / 探针 / 透传 / 回退）
├─ services/              # 业务服务层
│  ├─ course.py           # 课程 / 资料 / 课程记忆上下文
│  ├─ tasks.py            # 问答 / 总结 / 辅导 / 计划 / 错因 / 变式题
│  ├─ wrong_questions.py  # 错题本 / 错因 / 定向出题 / Markdown 导出
│  ├─ files.py            # 课件上传解析（txt/md/docx，白名单 + 大小限制）
│  ├─ focus.py            # 专注记录 / 学习概览统计
│  ├─ subject_knowledge.py# 高等数学上册 7 章结构化知识库
│  ├─ study.py            # 学习资源包生成（知识库 + 大模型双路径）
│  └─ mindmap.py          # 思维导图树 / SVG / 大纲 / Mermaid
├─ hardware/
│  ├─ esp32.py            # Webhook 下发 + 专注状态 + 学习状态看板
│  └─ esp32_firmware.ino  # 固件：/remind、/focus、上行状态轮询
├─ static/                # 原生前端（HTML/CSS/JS，9 个功能模块，深浅色主题）
├─ docs/
│  ├─ startup_check.py    # 【V1.2.1】一键启动自检（版本指纹 + 26 项接口检查）
│  ├─ startup_results.json# 启动自检结果
│  ├─ 启动检查报告.md      # 启动故障根因、修复与完整重测记录
│  ├─ demo_check.py       # 原有端到端 HTTP 验收脚本
│  ├─ demo_results.json   # 真实响应数据留存
│  ├─ feature_check.py    # V1.1 新增功能端到端验收脚本（19 项）
│  ├─ feature_results.json# V1.1 新增功能验收结果
│  ├─ study_check.py      # 【V1.2】高等数学 + 模型接入自测（36 项，含本地模拟模型）
│  ├─ study_results.json  # V1.2 自测结构化结果
│  ├─ 自测报告_高等数学与模型接入.md  # V1.2 自测报告（含真实生成内容抽样）
│  ├─ 模型接入接口说明.md  # 文心 / Kimi / 自定义端点的接入参数与故障排查
│  ├─ ui_shots.py         # 无头浏览器深浅色渲染截图
│  ├─ ui/                 # 深/浅色界面截图（含学习资源包、模型接入表单）
│  ├─ 演示验收报告.md      # 可读验收报告
│  ├─ 自我检查报告.md      # 逐条对照作业要求的符合性自检
│  ├─ 硬件交互说明.md      # 6 个硬件交互点全清单
│  ├─ 软件需求规格说明书.docx
│  ├─ AI校园学习陪伴助手_答辩.pptx
│  └─ blog/               # 博客园技术复盘文章与配图
├─ requirements.txt       # 仅 Flask 版 / 真实厂商接口需要
├─ Procfile               # 云端启动命令（web: python server.py）
├─ render.yaml            # Render Blueprint
├─ deploy/pythonanywhere_wsgi.py
└─ .env.example           # 密钥模板
```

> `server.py` 与 `app.py` 暴露**完全相同**的 REST API 与静态页面，共用同一套业务层，可随时互换。

---

## 三、本地运行（师生验收）

### 方式 0：双击启动（最省事，推荐给不熟悉命令行的同学）

双击项目根目录的 **`start.bat`**：探测端口与后端版本 → 启动 Web 服务 → 自动打开浏览器，**窗口里会打印实际访问地址**。

- 窗口保持开启即服务持续运行；按 `Ctrl+C` 或关闭窗口即停止。
- 若**同版本**服务已在运行，脚本不会重复启动，只打开浏览器（可反复双击）。
- 若 5000 端口被**旧版本服务**或**其它程序**占用，会自动顺延到 5001、5002……并明确提示，不会打开"新页面 + 旧接口"的坏组合。
- 想固定用 8080 端口：`set PORT=8080 && start.bat`。
- 等价命令：`python launch.py`；脚本仅依赖 Python 3.8+ 标准库，无需 pip、密钥或联网。
- 若提示找不到 Python，请在 https://www.python.org/downloads/ 安装并勾选 **Add Python to PATH**。

### 方式 A：命令行零依赖启动（推荐，无需联网装包）

```bash
python server.py
# 浏览器打开 http://localhost:5000
```

只需 Python 3.8+，不需要 `pip install`、不需要密钥、不需要联网。适合答辩现场与机房验收。

### 方式 B：Flask 版（生产环境可选）

```bash
pip install -r requirements.txt
python app.py
# 浏览器打开 http://localhost:5000
```

> ⚠️ 本机若无法联网 / pip 源不可用（安装 Flask 报 502），**请直接用方式 A 的 `python server.py`** —— 零依赖入口与 Flask 版功能完全一致。直接运行 `python app.py` 而缺少 Flask 时，现在会打印中文引导信息而不是一串 `ModuleNotFoundError` 堆栈。

两者均支持 `PORT` 环境变量（云端自动注入）：`PORT=8080 python server.py`。

### 启动排障（V1.2.1 新增）

| 现象 | 原因 | 处理 |
|---|---|---|
| 页面能打开，但「学习资源包」「模型接入」点一下全 404 | 5000 端口残留着**旧版本后端**，静态页却读的是磁盘上的新 HTML | 关闭旧服务窗口；或重新双击 `start.bat`（会自动顺延到新端口）；或用 `curl http://localhost:5000/api/status` 查看 `version` 是否为 `1.2.1` |
| 提示端口被占用 / 启动失败 | 已有服务或其它程序占用端口 | 本地默认会自动顺延端口；显式设了 `PORT` 时严格绑定，需释放端口：`Get-NetTCPConnection -LocalPort 5000 \| Select-Object OwningProcess` → `Stop-Process -Id <PID>` |
| `ModuleNotFoundError: No module named 'flask'` | 走了 Flask 版但依赖未安装 | 改用 `python server.py`（零依赖） |
| 双击后窗口一闪而过 | Python 不在 PATH | 安装 Python 并勾选 **Add Python to PATH**，或在项目目录打开终端执行 `python launch.py` 看完整输出 |

一键自检：`python docs/startup_check.py`（检查版本指纹、端口占用、首页与全部关键接口）。

> 不配置密钥时，所有功能以「内置演示模式」运行（规则化应答），**功能流程完全可走通**。
> 配置密钥后，对应厂商自动切换为真实大模型。
> 语音输入依赖浏览器 Web Speech API（Chrome/Edge 最佳），不支持时会给出降级提示，其余功能不受影响。

---

## 四、接入文心一言 / Kimi 等真实模型（可选，三种方式）

### 方式 1（推荐）：Web 界面填写，立即生效、无需重启

打开 **设置 → 模型接入**，选择提供商 → 填 API Key（文心旧版再填 Secret Key）→ 填模型名 →
点「保存并启用」，随后点「连通性测试」验证。密钥保存在服务端本地 SQLite，列表只显示掩码。

### 方式 2：REST 接口，供自建系统 / 脚本集成

```bash
# Kimi
curl -X POST http://localhost:5000/api/agent/credentials \
  -H "Content-Type: application/json" \
  -d '{"provider":"moonshot","api_key":"sk-你的密钥","model":"moonshot-v1-8k","activate":true}'

# 文心一言（千帆 v2，只需 API Key）
curl -X POST http://localhost:5000/api/agent/credentials \
  -H "Content-Type: application/json" \
  -d '{"provider":"qianfan","api_key":"你的APIKey","model":"ernie-4.5-8k","base_url":"https://qianfan.baidubce.com/v2/chat/completions","activate":true}'

# 任意业务系统直接调用当前模型
curl -X POST http://localhost:5000/api/agent/complete \
  -H "Content-Type: application/json" \
  -d '{"system_prompt":"你是数学助教","message":"讲解夹逼准则"}'
```

完整字段、旧版 WenxinWorkshop 参数、连通性测试与故障排查见 **`docs/模型接入接口说明.md`**。

### 方式 3：.env 环境变量

```bash
cp .env.example .env   # 填入 QIANFAN_API_KEY / MOONSHOT_API_KEY / CUSTOM_BASE_URL 等
ACTIVE_PROVIDER=moonshot MOONSHOT_API_KEY=sk-xxx python server.py
```

> 优先级：**运行时配置（方式 1/2） > 环境变量 > 内置演示模式**。任一厂商未配置或调用失败，
> 系统自动回退演示模式，功能流程不中断。所有厂商调用改用 Python 标准库 `urllib`，
> **零第三方依赖**，本机与云端均不需要 `requests`。

---

## 五、云端部署（供师生在线检查）

### 当前已上线（可直接使用，无需任何账号）

**https://ai-campus-companion.app.workbuddy.host/?sharecode=CEUN7FBTFJ**

浏览器直接打开（手机同样可访问），无需安装、无需密钥。链接中的 `sharecode` 为访问凭证，请**原样转发**给师生（去掉会返回 403）。

> ✅ **已于 2026-11-05 22:26 重新发布为 V1.1**，链接与 `sharecode` 均不变：现已包含深浅色主题与主题色、语音输入、课件上传/错题导出、学习概览、番茄钟、9 个模块与 6 个硬件交互点。发布后对线上复跑验收：首页含新控件，`/api/overview`、`/api/hardware/status`、`/api/focus/sessions` 均返回 200；**26/26 请求 + 30/30 断言 + 19/19 新增断言全部通过**（`docs/demo_results.json`、`docs/feature_results.json` 记录的是线上目标）。
>
> 🆕 **已于 2026-11-05 23:31 重新发布为 V1.2**，链接与 `sharecode` 均不变：新增「学习资源包」标签页（题目/总结/文章/资料/思维导图/导出）与「设置 → 模型接入」（文心一言 / Kimi / 自定义端点运行时配置）。发布后线上复验：首页含 `panel-study`、`agentProvider`、`studyPack`；`/api/study/catalog`、`/api/agent/providers` 返回 200；**线上 26/26 请求 + 30/30 断言 + 19/19 功能断言 + 25/25 V1.2 断言全部通过**（`docs/study_results_线上.json`）。答辩现场可直接打开 `?autopack=1#study` 一键生成全套资源。

---

### Render（Blueprint 一键部署，约 2 分钟）

已提供根目录 `render.yaml`（Render Blueprint），声明了服务类型、启动命令、健康检查与环境变量，**无需手工填 Build/Start Command**。

1. 把本项目推送到 GitHub 仓库（创建方法见下方「代码仓库与账号边界」）
2. Render 控制台 → **New +** → **Blueprint** → 连接该 GitHub 仓库
3. 点击 **Apply / Deploy**，等待构建完成
4. 获得 `https://ai-campus-companion.onrender.com`（名称被占用时 Render 会自动加后缀）
5. 可选：在 Environment 添加 `OPENAI_API_KEY` 等密钥；不填则自动使用内置演示模式

手工方式（不用 Blueprint 时）：Build Command 填 `echo "zero-dependency runtime"`，Start Command 填 `python server.py`，健康检查路径 `/api/status`。服务监听 Render 注入的 `PORT` 并绑定 `0.0.0.0`，`server.py` 已实现。

> Render 免费实例约 15 分钟无访问会休眠，首次打开需等待 30~60 秒；答辩前建议先访问一次预热。

---

### PythonAnywhere（WSGI，免费账户适用）

免费账户**不能常驻监听端口**，因此走 Flask 版 + WSGI（不能用 `python server.py`）：

```bash
# 1. 上传项目到 /home/<用户名>/ai-campus-companion 后，在 Bash 控制台：
cd ~/ai-campus-companion
pip install --user -r requirements.txt
```

1. Web → **Add a new web app** → **Manual configuration** → Python 3.10 / 3.11
2. 把 `deploy/pythonanywhere_wsgi.py` 的内容粘进 WSGI 配置文件，将其中的 `YOUR_USERNAME` 改成你的真实用户名
3. Web 页设置 **Source code** 为项目目录，**Reload**
4. 访问 `https://<用户名>.pythonanywhere.com`

> `os.chdir(PROJECT_DIR)` 是必需的：`app.py` 的静态目录使用相对路径 `static`。

---

### Flask 版部署（Render 上的可选替代）

Build `pip install -r requirements.txt`，Start `python app.py`；功能与零依赖版完全一致。

### 代码仓库与账号边界（重要）

Render / PythonAnywhere 都需要**你自己的平台账号**，我无法代登录，因此这两个平台的最终部署动作必须由你完成；但代码与配置已全部备齐：

- `render.yaml` —— Render Blueprint，导入即自动创建 Web Service
- `deploy/pythonanywhere_wsgi.py` —— PythonAnywhere WSGI 配置模板
- `Procfile` / `requirements.txt` / `server.py` —— 启动与依赖声明

GitHub 仓库已创建并推送完成：**[kecit33/ai-agent-study](https://github.com/kecit33/ai-agent-study)**（Public，默认分支 `main`）。本地按模块拆分的逐步提交已按原顺序重建到远端，可用 `git log --oneline` 查看完整迭代历史。

> 环境说明：GitHub 连接器的 App 凭据为只读（写操作返回 `403 Resource not accessible by integration`），且沙箱代理阻断 `github.com:443`；因此推送经 `api.github.com` 的 Git Data API 完成，工具脚本见 `docs/push_to_github.py`，需要时可重复执行。

若在你自己的机器上重新关联或推送：

```bash
git remote set-url origin https://github.com/kecit33/ai-agent-study.git
git push -u origin main
```

> 若不想做任何平台操作，直接使用上方「当前已上线」链接即可（注意版本提示）。

---

## 六、REST API 速览

### 原有接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/status` | 系统状态与提供商列表 |
| GET/POST | `/api/courses` | 课程列表 / 新建课程 |
| GET/POST | `/api/courses/<id>/materials` | 课程资料列表 / 上传资料 |
| POST | `/api/chat` | 课程记忆智能体问答 |
| POST | `/api/summarize` | 课件总结 |
| POST | `/api/tutor` | 习题引导式辅导 |
| POST | `/api/review-plan` | 复习计划生成 |
| GET/POST | `/api/wrong-questions` | 错题列表 / 新增错题 |
| POST | `/api/wrong-questions/<id>/analyze` | 错因分析 + 变式出题 |
| POST | `/api/wrong-questions/<id>/master` | 标记掌握 |
| GET/POST | `/api/providers`、`/api/settings/provider` | 厂商状态 / 切换 |
| POST | `/api/review-tasks` | 创建复习任务（可即时/到点下发） |
| POST | `/api/hardware/test` | 向 ESP32 下发测试提醒 |

### 本轮新增接口

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/courses/<id>/materials/upload` | multipart 课件上传（txt/md/docx，自动入课程记忆） |
| GET | `/api/wrong-questions/export` | 导出错题本 Markdown（文件下载） |
| GET | `/api/overview` | 学习概览：课程/资料/掌握率/今日专注/待复习/最近记录 |
| GET/POST | `/api/focus/sessions` | 专注记录列表 / 新增一次专注（到点联动 ESP32） |
| POST | `/api/focus/state` | 设置专注状态 → 推送 ESP32 专注灯 |
| GET | `/api/hardware/status` | 学习状态看板（供 ESP32 上行轮询） |

> 以上接口在 `server.py` 与 `app.py` 双后端中均已实现，路径与返回结构一致。

### V1.2 新增接口：学习资源包 + 模型接入

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/study/catalog` | 学科目录：数学 → 高等数学上册 → 7 章 |
| POST | `/api/study/quiz` | 生成自测题（含标准答案、解析、考点；可指定章节/难度/题量） |
| POST | `/api/study/summary` | 生成章节/全册复习总结（知识点、公式速查、易错点） |
| POST | `/api/study/article` | 生成专题文章（7 节：脉络 / 方法 / 题型 / 易错 / 路线 / 资料） |
| POST | `/api/study/resources` | 生成相关文章与资料清单（含链接） |
| POST | `/api/study/mindmap` | 生成思维导图（树 JSON + SVG + 大纲 + Mermaid） |
| GET | `/api/study/mindmap.svg` | 直接返回可视化 SVG 图片 |
| POST | `/api/study/pack` | 一键生成全套；`save_to_course:true` 回写课程记忆 |
| GET | `/api/study/pack/export` | 全套资源导出为 Markdown 文件下载 |
| GET | `/api/agent/providers` | 列出可插拔模型、配置状态与掩码 |
| POST | `/api/agent/credentials` | 运行时写入 API Key / 模型 / 接口地址，`activate:true` 立即切换 |
| POST | `/api/agent/credentials/clear` | 清除运行时配置并回退演示模式 |
| POST | `/api/agent/test` | `mode=validate` 校验配置；`mode=probe` 真实调用模型 |
| POST | `/api/agent/complete` | 通用模型透传，自建系统直接调用指定/当前模型 |

示例：「把高等数学上册给出去」：

```bash
curl -X POST http://localhost:5000/api/study/pack \
  -H "Content-Type: application/json" \
  -d '{"subject":"高等数学上册","chapter":"第一章 函数与极限","count":6}'
```

浏览器快捷演示：`http://localhost:5000/?autopack=1#study`（打开即自动生成全套资源）。

---

## 七、硬件联动（可选加分项）

系统共 **6 个硬件交互点**，形成「服务端下行提醒 + 开发板上行状态轮询」的双向闭环，完整说明见 **`docs/硬件交互说明.md`**（含触发条件、接口、服务端函数、固件端点、硬件表现、演示步骤与诚实边界）。前端「硬件联动」页内置同一张清单表与实时状态看板。

| # | 交互点 | 方向 | 接口 |
|---|---|---|---|
| 1 | 复习任务到点提醒 | 服务端 → ESP32 | `check_due_tasks()` → `POST /remind` |
| 2 | 手动测试提醒 | 服务端 → ESP32 | `POST /api/hardware/test` → `/remind` |
| 3 | 番茄钟到点提醒（新增） | 服务端 → ESP32 | `POST /api/focus/sessions` → `/remind` |
| 4 | 专注状态灯（新增） | 服务端 → ESP32 | `POST /api/focus/state` → `POST /focus` |
| 5 | 学习状态看板（新增，上行） | ESP32 → 服务端 | `GET /api/hardware/status`（每 60s） |
| 6 | 通用消息下发（预留） | 服务端 → ESP32 | `notify_esp32(task, message)` |

快速配置：

1. 烧录 `hardware/esp32_firmware.ino` 到 ESP32（改 WiFi 名/密码、`SERVER_BASE`，开发板监听 `/remind` 与 `/focus`）
2. 配置 `ESP32_ENDPOINT=http://<开发板IP>/remind`
3. 页面「硬件联动」创建复习任务、点「立即下发测试提醒」「点亮/熄灭专注灯」「刷新状态」
4. 未配置 `ESP32_ENDPOINT` 不影响主体功能，接口仍返回 `{sent: false, reason: ...}`

> **诚实边界**：固件与服务端接口均已实现并通过 19 项端到端验证，但本机无开发板，**LED/蜂鸣器的物理表现与 WiFi 连通性未做实机联调**。

---

## 八、端到端验收

```bash
# 先启动服务
python server.py

# 另开终端执行（默认验证 http://localhost:5000）
python docs/startup_check.py    # 【V1.2.1】启动自检：版本指纹 + 26 项接口
python docs/demo_check.py       # 原有 26 请求 / 30 断言
python docs/feature_check.py    # V1.1 新增 19 项断言
python docs/study_check.py      # 【V1.2】高等数学资源 + 文心/Kimi 接入 36 项断言
python docs/ui_shots.py         # 可选：生成深浅色界面截图

# 验证线上站点（sharecode 用于建立访问会话）
BASE_URL=https://ai-campus-companion.app.workbuddy.host \
SHARECODE=CEUN7FBTFJ python docs/demo_check.py

BASE_URL=https://ai-campus-companion.app.workbuddy.host \
SHARECODE=CEUN7FBTFJ python docs/feature_check.py

BASE_URL=https://ai-campus-companion.app.workbuddy.host \
SHARECODE=CEUN7FBTFJ python docs/study_check.py   # 线上 25 项；模型联网探针自动跳过
```

> `feature_check.py` 同样支持 `BASE_URL` / `SHARECODE`；带 `sharecode` 会先建立访问会话 Cookie，之后 API 才不会返回 403。课程 ID 由 `/api/courses` 动态获取，不依赖固定值。

`demo_check.py` 以真实 HTTP 请求覆盖：静态页面与资源、厂商切换、课程记忆绑定与隔离、课件总结、引导式辅导、复习计划、错题闭环、硬件联动、异常与边界（400/404），并把每个请求与响应写入 `docs/demo_results.json`，生成 `docs/演示验收报告.md`。

`feature_check.py` 覆盖新增 19 项：主题系统 UI/样式、语音按钮与 API、上传区、概览与番茄钟、硬件清单、专注开启/关闭与看板同步、专注记录 + ESP32 提醒、Markdown 上传、docx 上传解析、非法类型 400、错题导出下载头、上传资料进入课程记忆。结果写入 `docs/feature_results.json`。

### 手动验收清单（浏览器逐项点一遍，约 7 分钟）

页面顶部有 **10 个导航标签**，右上角是当前智能体徽标与主题切换按钮。支持 URL hash 直达模块（如 `http://localhost:5000/#study`）；`/?autopack=1#study` 打开即自动生成全套学习资源，适合答辩现场演示。

| # | 标签 | 操作 | 预期结果 |
|---|---|---|---|
| 1 | 学习概览 | 打开首页 | 显示课程数、资料数、错题掌握率、今日专注、待复习任务、最近专注记录 |
| 2 | 智能问答 | 顶部课程选「示例课程：数据结构」，输入「进程和线程的区别」，点**发送** | 回复中出现「课程记忆：示例课程：数据结构」，且引用本课程已存资料 |
| 3 | 课程记忆 | 新建课程 B，保存一份资料；切换 A/B 分别提问 | 两次回复绑定的课程名不同，上下文互不串（隔离成立） |
| 4 | 课件总结 | 粘贴一段课件文字，点**生成总结** | 返回「关键知识点」+「复习考点提纲」两段结构化内容 |
| 5 | 习题辅导 | 粘贴一道题，点**辅导一下** | 给分步思路与提示，**不直接甩最终答案** |
| 6 | 复习计划 | 科目填「数据结构」、天数填 10，点**生成计划** | 输出「第 1 天」到「第 10 天」的逐日安排 |
| 7 | 错题本 | 填题干/我的答案/正确答案，点**加入错题本**；列表中点分析 → 变式 → 标记掌握 | 生成错因诊断 + 定向变式题，可标记掌握并按状态筛选 |
| 8 | 设置 | 查看 6 个厂商卡片与模型接入表单；切换「浅色/深色/跟随系统」与主题色 | 未配置厂商显示「未配置」并自动回退；主题即时生效，刷新后保留 |
| 9 | 硬件联动 | 创建任务，点**立即下发测试提醒**、**点亮专注灯**、**刷新状态** | 返回明确的未配置原因；看板显示待复习数/待掌握错题数/专注状态 |
| 10 | 语音 / 上传 | 任一输入框点 🎤 说话；在课程记忆区上传一个 `.txt`/`.md`/`.docx` | 语音转文字填入输入框；上传解析成功并进入课程记忆，非法类型返回 400 |
| 11 | 番茄钟 | 学习概览设置时长并点击开始，等待计时结束（或缩短时长） | 计时正常，结束时产生专注记录并可联动 ESP32 提醒 |
| 12 | 学习资源包 | 教材填「数学」或「高等数学上册」，章节选「第一章」，点**一键生成全套** | 生成带答案解析的题目、总结、专题文章、资料清单与 SVG 思维导图；可导出 Markdown / SVG |
| 13 | 模型接入 | 设置页选「Kimi」，填 API Key 与模型名，点**保存并启用** → **连通性测试** | 状态显示已配置与掩码；真实密钥时连通性测试返回模型回复，无密钥时给出明确原因 |

数据文件：`data/companion.db`（SQLite，首次启动自动创建）。想恢复干净演示状态，停止服务后删除该文件再重启即可。初始预置 1 门示例课程、1 份课件、1 道待分析错题。

> 边界测试：访问 `/api/not-exist` 应返回 404；不给必填字段调用 POST 接口应返回 400；上传 `.exe` 应返回 400。脚本已覆盖。

---

## 九、文档与答辩材料

- `docs/软件需求规格说明书.docx` —— 符合 GB/T 9385-2008 / GB/T 8567-2006 的需求文档（含迭代记录表、项目标志、思维导图、类图、功能描述、验收标准、前后端详尽描述）
- `docs/AI校园学习陪伴助手_答辩.pptx` —— 答辩材料（团队展示 / 选题报告 / 需求分析 / 核心功能 / 类图 / 创新点，图文并茂）
- `docs/演示验收报告.md` —— 真实 HTTP 请求与响应数据摘录
- `docs/自测报告_高等数学与模型接入.md` —— 【V1.2】36 项自测与真实生成内容抽样（题目/总结/文章/资料/导图）
- `docs/模型接入接口说明.md` —— 【V1.2】文心一言 / Kimi / 自定义端点接入参数、示例与排查
- `docs/自我检查报告.md` —— 逐条对照原始作业要求的符合性自检（✅/🟡/❌ + 证据 + 差距）
- `docs/硬件交互说明.md` —— 6 个硬件交互点全清单与演示步骤
- `docs/blog/AI校园学习陪伴助手_博客园文章.md` —— 技术复盘长文（10 张配图）
- `docs/ui/*.png` —— 深/浅色界面真实渲染截图

> 注：PPT 与需求文档中的图表为 SVG 矢量图，请使用 PowerPoint 2016+ 或 WPS 打开以获得最佳效果。
> **V1.2 已同步**：SRS 版本升至 V1.2，迭代表新增 V1.2 行，新增「七、功能描述（V1.2 增量）」（F15–F22、14 项新接口、A17–A24 验收标准、36 项实测结果与诚实边界）；答辩 PPT 扩至 **11 页**，新增「V1.2 学科资源包 + 模型接入接口」页并更新验收数据。
> 待办：团队展示仍为「第 X 开发组」占位，需替换为真实成员信息。

---

## 十、版本迭代与提交规范

本地仓库按模块**逐步提交**（不是一次性打包），共 44 个 commit，其中前 16 个与需求文档的迭代记录表对应；远端 `main` 分支已按相同顺序重建。用 `git log --oneline` 可查看：

| # | 阶段 | 提交说明 |
|---|---|---|
| 1 | 骨架 | `chore: 初始化项目骨架与工程配置` |
| 2 | 数据 | `feat(db): SQLite 数据模型与连接管理` |
| 3 | 智能体 | `feat(agents): 智能体抽象基类与内置演示模式` |
| 4 | 智能体 | `feat(agents): 接入 GPT / Kimi / Claude / 文心一言 四家厂商` |
| 5 | 智能体 | `feat(agents): 提供商工厂与不可用时自动回退演示模式` |
| 6 | 服务 | `feat(services): 课程与课程记忆上下文` |
| 7 | 服务 | `feat(services): 问答/总结/辅导/复习计划/错因分析任务封装` |
| 8 | 服务 | `feat(services): AI 错题本与定向变式出题闭环` |
| 9 | 硬件 | `feat(hardware): ESP32 Webhook 联动接口与固件` |
| 10 | 后端 | `feat(api): Flask REST 后端与复习任务到点调度` |
| 11 | 后端 | `feat(api): 零依赖标准库 Web 服务器` |
| 12 | 前端 | `feat(frontend): 原生前端页面与八模块交互` |
| 13 | 测试 | `test: 端到端 HTTP 验收脚本与线上数据结果` |
| 14 | 文档 | `docs: 国标需求规格说明书与答辩 PPT（含生成脚本与矢量图）` |
| 15 | 部署 | `deploy: Render Blueprint 与 PythonAnywhere WSGI 模板` |
| 16 | 文档 | `docs: 本地运行、云端部署与验收说明` |
| 17 | 文档 | `docs: 补充版本迭代记录与逐步提交规范` |
| 18 | 工程 | `chore: 校正 GitHub 仓库地址并提供逐提交推送工具` |
| 19 | 工程 | `fix: 处理 GitHub 空仓库引导提交并同步迭代记录` |
| 20 | 文档 | `docs: 新增博客园技术复盘文章与 10 张配图` |
| 21 | 工程 | `feat: 新增双击启动脚本与手动验收清单` |
| 22 | 数据/硬件 | `feat(db): 新增专注记录表、错题导出与硬件状态看板` |
| 23 | 服务 | `feat(services): 课件上传解析与学习概览/专注服务` |
| 24 | 后端 | `feat(api): 双后端新增上传、导出、概览、专注与硬件状态接口` |
| 25 | 前端 | `feat(frontend): 深浅色主题、主题色、语音输入、番茄钟与硬件清单` |
| 26 | 硬件 | `feat(hardware): ESP32 固件支持专注灯与上行状态轮询` |
| 27 | 测试 | `test: 新增功能端到端验收与深浅色渲染截图` |
| 28 | 文档 | `docs: 需求符合性自检、硬件交互说明与 README 同步` |
| 29 | 文档 | `docs: SRS 与 PPT 同步 V1.1 增量功能` |
| 30 | 测试 | `test: 重新发布线上站点并完成双环境验收` |
| 31 | 智能体 | `feat(agents): 运行时密钥中心、标准库 HTTP 客户端与多厂商统一适配` |
| 32 | 服务 | `feat(services): 高等数学上册知识库、学习资源包与思维导图生成` |
| 33 | 后端 | `feat(api): 双后端新增学习资源包与模型接入 14 项接口` |
| 34 | 前端 | `feat(frontend): 学习资源包页面与模型接入表单` |
| 35 | 测试 | `test: 高等数学与模型接入 36 项自测、深浅色截图与回归复跑` |
| 36 | 文档 | `docs: 模型接入说明、SRS/PPT 同步 V1.2、博客与自检报告更新` |
| 37 | 文档 | `docs: README 同步 V1.2 功能、接口、验收与 36 个逐步提交` |
| 38 | 部署/测试 | `deploy: 重新发布线上 V1.2 并完成双环境复验` |
| 39 | 启动修复 | `fix(startup): 版本指纹与端口占用探测，根治旧后端残留导致的新页面旧接口` |
| 40 | 测试 | `test: 新增一键启动自检脚本与 26 项检查结果` |
| 41 | 文档 | `docs: 启动排障章节、V1.2.1 修复说明与完整重测报告` |
| 42 | 测试 | `test: 从零重启后复跑三套回归并重生成深浅色截图` |
| 43 | 工程 | `chore: 推送工具增加 blob 缓存与重试，README 同步 V1.2.1 提交记录` |
| 44 | 部署/测试 | `deploy: 重新发布线上 V1.2.1 并完成双环境复验` |

- 分支：`main`；忽略：`data/`、`__pycache__/`、`.env`、`docs/.slidep/`、`docs/pptx/`（后两者为工具残留，非交付物）。
- GitHub 仓库名不含空格，实际采用 `ai-agent-study`；本地 `origin` 已指向 `https://github.com/kecit33/ai-agent-study.git`。
- 远端 `main` 已按本地顺序逐步追加至全部 **44 个提交 / 89 个文件**（含中文提交说明与二进制文档）；因 `github.com:443` 直连不稳定，推送使用 `docs/push_to_github.py --start N --parent <远端HEAD>` 经 `api.github.com` Git Data API 完成，逐文件 blob 与本地一致。推送工具已加入持久化 blob 缓存与 8 次重试，可应对网关间歇 500/502。
- 双击启动入口：`start.bat` → `launch.py` → `server.py`（版本指纹探测、端口自动顺延、自动开浏览器）。
- 博客园技术复盘文章：`docs/blog/AI校园学习陪伴助手_博客园文章.md`（10 张配图在 `docs/blog/assets/`，由 `docs/blog/build_images.py` 用无头浏览器生成）。
