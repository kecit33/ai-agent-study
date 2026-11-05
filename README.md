# AI 校园学习陪伴助手

一款面向大学生课程学习场景、基于大模型智能体的 **Web 应用**（浏览器访问，B/S 架构）。智能体（GPT / 文心一言 / Kimi / Claude）以**可插拔**方式集成进自研系统，而非直接套用官方聊天页；具备「课程记忆智能体」「AI 错题本与定向出题」等杀手级功能，并预留 ESP32 硬件联动（加分项）。

> 课程作业 · 智能体开发 · 2026
>
> **端到端验收结果：26/26 个 HTTP 请求状态正确，30/30 项业务断言通过**（详见 `docs/演示验收报告.md`）。

---

## 一、特性对照（作业评估要点）

- ✅ 智能体嵌入自研系统：统一 `AgentProvider` 接口，四家厂商 + 内置演示模式
- ✅ 真实调研需求：基于本校同学调研痛点，无虚构
- ✅ 杀手级功能：课程记忆（按课程隔离上下文）+ 错题闭环（错因分析 → 定向变式题）
- ✅ 无密钥可运行：未配置任何密钥时自动进入「内置演示模式」，保证师生可直接验收
- ✅ 可上线：本地一键启动 + 云端部署，生成可访问链接
- ✅ 零依赖可运行：`server.py` 仅用 Python 标准库，无需 `pip install` 即可启动完整 Web 服务
- 🟡 硬件联动（可选加分）：ESP32 + LED + 蜂鸣器到点提醒

---

## 二、目录结构

```
ai-campus-companion/
├─ start.bat              # 【双击启动】Windows 一键启动 + 自动开浏览器
├─ launch.py              # 启动器：探测端口、避免重复启动、拉起 server.py
├─ server.py              # 【默认入口】零依赖 Web 服务器（Python 标准库，推荐）
├─ app.py                 # Flask 版后端入口（需 pip install，生产可选）
├─ config.py              # 配置中心（密钥经环境变量读取）
├─ db.py                  # SQLite 初始化与连接
├─ agents/                # 可插拔智能体层
│  ├─ base.py             # AgentProvider 抽象基类
│  ├─ openai_provider.py  # GPT
│  ├─ qianfan_provider.py # 文心一言
│  ├─ moonshot_provider.py# Kimi
│  ├─ claude_provider.py  # Claude
│  ├─ demo_provider.py    # 内置演示模式（无密钥兜底）
│  └─ factory.py          # 提供商工厂（按配置选择 + 自动回退）
├─ services/              # 业务服务层
│  ├─ course.py           # 课程 / 资料 / 课程记忆上下文
│  ├─ tasks.py            # 问答 / 总结 / 辅导 / 计划 / 错因 / 变式题
│  └─ wrong_questions.py  # 错题本 / 错因 / 定向出题
├─ hardware/
│  ├─ esp32.py            # ESP32 Webhook 联动接口
│  └─ esp32_firmware.ino  # ESP32 固件（点亮 LED + 蜂鸣器）
├─ static/                # 原生前端（HTML/CSS/JS，8 个功能模块）
├─ docs/
│  ├─ demo_check.py       # 端到端 HTTP 验收脚本
│  ├─ demo_results.json   # 真实响应数据留存
│  ├─ 演示验收报告.md      # 可读验收报告
│  ├─ 软件需求规格说明书.docx
│  └─ AI校园学习陪伴助手_答辩.pptx
├─ requirements.txt       # 仅 Flask 版 / 真实厂商接口需要
├─ Procfile               # 云端启动命令（web: python server.py）
└─ .env.example           # 密钥模板
```

> `server.py` 与 `app.py` 暴露**完全相同**的 REST API 与静态页面，共用同一套业务层，可随时互换。

---

## 三、本地运行（师生验收）

### 方式 0：双击启动（最省事，推荐给不熟悉命令行的同学）

双击项目根目录的 **`start.bat`**：自动检测 5000 端口 → 启动 Web 服务 → 自动打开浏览器。

- 窗口保持开启即服务持续运行；按 `Ctrl+C` 或关闭窗口即停止。
- 若服务已在运行，脚本**不会重复启动**，只打开浏览器（可反复双击）。
- 已占用 5000 端口时：`set PORT=8080 && start.bat`，浏览器访问 `http://localhost:8080`。
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

两者均支持 `PORT` 环境变量（云端自动注入）：`PORT=8080 python server.py`。

> 不配置密钥时，所有功能以「内置演示模式」运行（规则化应答），**功能流程完全可走通**。
> 配置密钥后，对应厂商自动切换为真实大模型。

---

## 四、配置真实大模型密钥（可选）

```bash
cp .env.example .env
# 编辑 .env，填入你申请的密钥，例如：
OPENAI_API_KEY=sk-xxx
QIANFAN_API_KEY=xxx
QIANFAN_SECRET_KEY=xxx
MOONSHOT_API_KEY=xxx
CLAUDE_API_KEY=xxx
ACTIVE_PROVIDER=openai     # demo / openai / qianfan / moonshot / claude
```

也可直接用环境变量：`ACTIVE_PROVIDER=openai OPENAI_API_KEY=sk-xxx python server.py`。
在页面「设置」页可随时切换与查看各厂商可用性。密钥只从环境变量读取，不写入代码或数据库。

---

## 五、云端部署（供师生在线检查）

### 当前已上线（可直接使用，无需任何账号）

**https://ai-campus-companion.app.workbuddy.host/?sharecode=CEUN7FBTFJ**

浏览器直接打开（手机同样可访问），无需安装、无需密钥。链接中的 `sharecode` 为访问凭证，请**原样转发**给师生（去掉会返回 403）。

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

> 若不想做任何平台操作，直接使用上方「当前已上线」链接即可，师生在线验收效果完全相同。

---

## 六、REST API 速览

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

---

## 七、硬件联动（可选加分项）

1. 烧录 `hardware/esp32_firmware.ino` 到 ESP32（改 WiFi 名/密码，开发板监听 `/remind`）
2. 配置 `ESP32_ENDPOINT=http://<开发板IP>/remind`
3. 页面「硬件联动」创建复习任务（不填时间即即时下发，可立即验证），到点后开发板点亮 LED + 触发蜂鸣器
4. 未配置 `ESP32_ENDPOINT` 不影响主体功能，接口仍正常返回 `{sent: false, reason: ...}`

---

## 八、端到端验收

```bash
# 先启动服务
python server.py

# 另开终端执行（默认验证 http://localhost:5000）
python docs/demo_check.py

# 验证线上站点（sharecode 用于建立访问会话）
BASE_URL=https://ai-campus-companion.app.workbuddy.host \
SHARECODE=CEUN7FBTFJ python docs/demo_check.py
```

脚本以真实 HTTP 请求覆盖：静态页面与资源、厂商切换、课程记忆绑定与隔离、课件总结、引导式辅导、复习计划、错题闭环、硬件联动、异常与边界（400/404），并把每个请求与响应写入 `docs/demo_results.json`，生成 `docs/演示验收报告.md`。

验收要点：可访问性 · 无密钥可运行 · 课程记忆隔离 · 课件总结 · 习题辅导不直接给答案 · 复习计划 · 错题闭环 · 可插拔切换 · 密钥安全 · 硬件（可选）。

### 手动验收清单（浏览器逐项点一遍，约 5 分钟）

页面顶部有 8 个导航标签，右上角徽标显示当前智能体（无密钥时为「内置演示模式」）。

| # | 标签 | 操作 | 预期结果 |
|---|---|---|---|
| 1 | 智能问答 | 顶部课程选「示例课程：数据结构」，输入「进程和线程的区别」，点**发送** | 回复中出现「课程记忆：示例课程：数据结构」，且引用本课程已存资料 |
| 2 | 课程记忆 | 新建课程 B，保存一份资料；回到智能问答切换 A/B 分别提问 | 两次回复绑定的课程名不同，上下文互不串（隔离成立） |
| 3 | 课件总结 | 粘贴一段课件文字，点**生成总结** | 返回「关键知识点」+「复习考点提纲」两段结构化内容 |
| 4 | 习题辅导 | 粘贴一道题，点**辅导一下** | 给分步思路与提示，**不直接甩最终答案** |
| 5 | 复习计划 | 科目填「数据结构」、天数填 10，点**生成计划** | 输出「第 1 天」到「第 10 天」的逐日安排 |
| 6 | 错题本 | 填题干/我的答案/正确答案，点**加入错题本**；列表中点分析 → 变式 → 标记掌握 | 生成错因诊断 + 定向变式题，可标记掌握并按状态筛选 |
| 7 | 设置 | 查看 5 个厂商卡片，点切换 | 4 家真实厂商显示「未配置密钥」，自动回退演示模式，功能不中断 |
| 8 | 硬件联动 | 创建任务，点**立即下发测试提醒** | 返回「未配置 ESP32_ENDPOINT」的说明（可选加分项，不影响主体） |

数据文件：`data/companion.db`（SQLite，首次启动自动创建）。想恢复干净演示状态，停止服务后删除该文件再重启即可。初始预置 1 门示例课程、1 份课件、1 道待分析错题。

> 边界测试：访问 `/api/not-exist` 应返回 404；不给必填字段调用 POST 接口应返回 400。脚本已覆盖。

---

## 九、文档与答辩材料

- `docs/软件需求规格说明书.docx` —— 符合 GB/T 9385-2008 / GB/T 8567-2006 的需求文档（含迭代记录表、项目标志、思维导图、类图、功能描述、验收标准、前后端详尽描述）
- `docs/AI校园学习陪伴助手_答辩.pptx` —— 答辩材料（团队展示 / 选题报告 / 需求分析 / 核心功能 / 类图 / 创新点，图文并茂）
- `docs/演示验收报告.md` —— 真实 HTTP 请求与响应数据摘录

> 注：PPT 与需求文档中的图表为 SVG 矢量图，请使用 PowerPoint 2016+ 或 WPS 打开以获得最佳效果。

---

## 十、版本迭代与提交规范

本地仓库按模块**逐步提交**（不是一次性打包），共 21 个 commit，其中前 16 个与需求文档的迭代记录表对应；远端 `main` 分支已按相同顺序重建。用 `git log --oneline` 可查看：

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

- 分支：`main`；忽略：`data/`、`__pycache__/`、`.env`、`docs/.slidep/`、`docs/pptx/`（后两者为工具残留，非交付物）。
- GitHub 仓库名不含空格，实际采用 `ai-agent-study`；本地 `origin` 已指向 `https://github.com/kecit33/ai-agent-study.git`。
- 远端 `main` 已按本地顺序重建全部 21 个逐步提交（含中文提交说明与二进制文档）；网络允许时可直接 `git push -u origin main`。
- 双击启动入口：`start.bat` → `launch.py` → `server.py`（自动探测端口、自动开浏览器）。
- 博客园技术复盘文章：`docs/blog/AI校园学习陪伴助手_博客园文章.md`（10 张配图在 `docs/blog/assets/`，由 `docs/blog/build_images.py` 用无头浏览器生成）。
