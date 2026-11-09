# -*- coding: utf-8 -*-
"""V1.5.0 墨刀原型页面单一源。

改原型只改本文件的 PAGES 数据，然后：
    python gen_modao_v150.py
产出 modao_v150/*.html、modao_v150/html_list.json（供墨刀 import_to_proto）、
以及 原型需求核对表.md（供第二次作业按需求项核对）。
事实源：docs/软件需求规格说明书.md、static/index.html、version.py。
"""
import io
import json
import os
import re

VERSION = "V1.5.0"
APP = "AI 校园学习陪伴助手"
OUT = "modao_v150"

CSS = (
    "<style>body{font:13px 'Microsoft YaHei',Arial,sans-serif;margin:0;background:#F5F7FB;color:#1B2430}"
    ".hd{background:#1E4FA8;color:#fff;padding:16px 24px}.hd b{font-size:18px}"
    ".bv{background:#fff;color:#1E4FA8;padding:3px 8px;border-radius:3px;font-size:12px;font-weight:bold}"
    ".bar{padding:8px 24px;background:#E8EFF8;font-size:12px;color:#3B4A63}"
    ".bar b{color:#1E4FA8}.w{margin:14px 24px;background:#fff;border:1px solid #D6DCE5;"
    "border-radius:6px;padding:16px}h2{font-size:17px;color:#1E4FA8;margin:0 0 6px}"
    "h3{font-size:14px;margin:14px 0 6px}p{line-height:1.6;margin:6px 0;color:#3B4A63}"
    "table{width:100%;border-collapse:collapse;font-size:12px}"
    "th,td{border:1px solid #DCE3EE;padding:6px;text-align:left;vertical-align:top}"
    "th{background:#F0F4FB;color:#1E4FA8}"
    ".t{display:inline-block;background:#E8EFF8;color:#1E4FA8;padding:2px 6px;margin:0 4px 4px 0;"
    "border-radius:3px;font-size:12px}.tw{background:#FFF6E5;color:#8A5A00}"
    ".f{background:#F7F9FC;border-left:3px solid #1E4FA8;padding:10px;font-size:12px;line-height:1.7}"
    ".ft{margin:14px 24px;background:#1E4FA8;color:#fff;border-radius:6px;padding:12px 16px;"
    "font-size:12px;line-height:1.7}.mut{color:#5A6B85}</style>"
)

NAV = [
    ("dashboard", "学习概览"), ("chat", "智能问答"), ("study", "学习资源包"),
    ("summarize", "课件总结"), ("tutor", "习题辅导"), ("plan", "复习计划"),
    ("memory", "课程记忆"), ("wrong", "错题本"), ("hardware", "硬件联动"),
    ("settings", "设置"),
]

# no, tab, name, fa, acc, lead, comps[(组件, 字段/控件, 文案或规则)], states[(状态, 说明)], flow, rules
PAGES = [
    dict(no="P01", tab="dashboard", name="学习概览", fa="F12 · F26 · F29", acc="A15 · A29 · A32",
         lead="一屏聚合课程复习状态；六项统计、待复习任务、番茄钟与最近专注记录。",
         comps=[("v15-stat-card × 6", "统计卡片（可聚焦）", "Tab / Enter / Space 激活；无误题显示「暂无」而非 0.0%"),
                ("v15-quick-task", "quickTask 输入框", "placeholder：任务名，如：复习数据结构第 3 章"),
                ("v15-quick-task", "添加 / 完成按钮", "POST /api/review-tasks、POST /api/review-tasks/{id}/done"),
                ("v15-pomodoro", "番茄钟与专注状态", "GET /api/focus/state、GET/POST /api/focus/sessions"),
                ("v15-course-bar", "顶栏课程选择条", "全局生效，切换课程刷新本页统计")],
         states=[("默认态", "六项统计与待复习列表有值"), ("空态", "无误题显示「暂无」"),
                 ("键盘焦点态", "统计卡片与上传区有 focus-visible 焦点样式"),
                 ("异常降级态", "单个接口失败逐模块提示，页面仍可操作（F30 / A33）")],
         flow="进入页面 → 拉取 /api/overview 与复习任务 → 六项统计渲染 → 添加 / 完成任务 → 后台每 30 秒扫描到期任务并下发提醒。",
         rules="空任务名回落默认名（F32 / A35）；统计与列表统一转义（F31 / A34）。"),
    dict(no="P02", tab="chat", name="智能问答", fa="F01 · F06 · F27 · F28 · F33 · F34", acc="A05 · A06 · A30 · A31 · A36 · A37",
         lead="课程内问答：切换课程即切换课程记忆，是本项目杀手级功能的界面入口。",
         comps=[("v15-mode-banner", "演示模式提示条", "未配置密钥或调用异常时回退 demo，响应带 fallback 标记（F23 / A26）"),
                ("v15-chat-log", "对话区", "回答按安全 Markdown 渲染，先转义再解析（F27 / A30）"),
                ("v15-chat-input", "chatInput 文本域", "placeholder：输入课程问题，或点右侧 🎤 语音输入（Chrome / Edge）…"),
                ("v15-mic-btn", "语音输入按钮", "Web Speech API，覆盖 5 处输入（F25 / A28）"),
                ("v15-send-btn", "发送按钮", "请求期间禁用并提示，结束恢复（F28 / A31）"),
                ("v15-course-bar", "课程选择条", "切换时清空对话；过期异步响应丢弃（F34 / A37）")],
         states=[("默认态", "对话区空、输入可用"), ("忙碌态", "发送按钮禁用并显示状态"),
                 ("回退态", "演示模式提示条 + fallback 标记"), ("切课程态", "对话清空、上下文重建")],
         flow="选择课程 → build_course_context(course_id) 拼入该课程资料全文 → 交给 AgentProvider.complete() → 安全 Markdown 渲染回答。",
         rules="单份资料 4000 字、总量 12000 字预算，超出按序保留并提示（F33 / A36）；课程记忆为全文拼接，不是检索增强。"),
    dict(no="P03", tab="study", name="学习资源包", fa="F13 – F19 · F27 · F35", acc="A16 – A22 · A30 · A38",
         lead="按教材 / 章节 / 题量 / 难度生成五件套，支持一键全套与导出。",
         comps=[("v15-study-param", "studySubject 输入框", "默认值：高等数学上册；placeholder：如：数学 / 高等数学上册"),
                ("v15-study-param", "章节 / 题量 / 难度", "学科目录与别名解析，未内置学科返回 discipline=自定义科目（F13 · F19）"),
                ("v15-action-btn × 7", "自测题 / 总结 / 文章 / 资料 / 思维导图 / 一键全套 / 导出", "5 个生成按钮统一忙碌态"),
                ("v15-result × 5", "题目 / 总结 / 专题文章 / 资料清单 / 思维导图", "题目含标准答案、分步解析与考点（F14）"),
                ("v15-export", "导出 Markdown", "blob 下载失败不替换页面（F36 / A39）")],
         states=[("默认态", "参数区可编辑、五区待生成"), ("忙碌态", "5 个按钮同时禁用"),
                 ("部分失败态", "双请求独立判错，资料链接协议白名单（F35 / A38）"),
                 ("直达态", "/?autopack=1#study 打开即自动生成全套资源")],
         flow="选学科与章节 → 单动作生成或一键五件套 → 五区分别渲染 → 可回写课程记忆 → 导出 Markdown。",
         rules="思维导图输出树 JSON + SVG + Markdown 大纲 + Mermaid（F17 / A20）；一键全套走 POST /api/study/pack（F18 / A21）。"),
    dict(no="P04", tab="summarize", name="课件总结", fa="F02 · F27 · F30", acc="A07 · A30 · A33",
         lead="粘贴课件文本，输出关键知识点与复习考点提纲。",
         comps=[("v15-big-textarea", "sumText 文本域", "placeholder：在此粘贴课件或笔记文字…"),
                ("v15-mic-btn", "语音输入", "Web Speech API（F25 / A28）"),
                ("v15-action-btn", "生成总结按钮", "POST /api/summarize，请求中禁用（F28 / A31）"),
                ("v15-result", "富文本结果区", "安全 Markdown 排版：关键知识点 / 复习考点提纲")],
         states=[("默认态", "文本框为空可输入"), ("忙碌态", "按钮禁用并显示生成中"),
                 ("空值拦截态", "空内容不发起请求"), ("异常降级态", "失败逐模块提示，页面仍可操作")],
         flow="粘贴课件 → 点击生成 → 后端返回结构化总结 → 安全 Markdown 渲染。",
         rules="结果文本统一转义（F31 / A34）；任一 API 失败不使整页变砖（F30 / A33）。"),
    dict(no="P05", tab="tutor", name="习题辅导", fa="F03 · F27 · F30", acc="A08 · A30 · A33",
         lead="引导式辅导：给分步思路与提示，不直接给最终答案。",
         comps=[("v15-big-textarea", "tutorText 文本域", "placeholder：在此粘贴题目…"),
                ("v15-mic-btn", "语音输入", "Web Speech API（F25 / A28）"),
                ("v15-action-btn", "「辅导一下」按钮", "POST /api/tutor，请求中禁用"),
                ("v15-result", "结果区", "分步思路 + 提示，按安全 Markdown 排版")],
         states=[("默认态", "题目输入区可用"), ("忙碌态", "按钮禁用"),
                 ("结果态", "展示分步思路与提示"), ("异常降级态", "逐模块错误提示")],
         flow="粘贴题目 → 点击辅导一下 → 返回分步思路与提示 → 安全 Markdown 渲染。",
         rules="与课件总结页共享输入组件 v15-big-textarea 与状态规则，保持组件命名与表现一致。"),
    dict(no="P06", tab="plan", name="复习计划", fa="F04 · F12 · F27", acc="A09 · A15 · A30",
         lead="按科目与天数生成逐日复习安排。",
         comps=[("v15-input", "planSubject 输入框", "placeholder：考试科目，如：数据结构"),
                ("v15-input", "天数输入", "生成「第 1 天」至「第 N 天」逐日安排"),
                ("v15-action-btn", "生成计划按钮", "POST /api/review-plan"),
                ("v15-result", "结果区", "安全 Markdown 排版逐日计划")],
         states=[("默认态", "科目与天数待填"), ("忙碌态", "按钮禁用"),
                 ("结果态", "逐日安排可 30 秒扫描完"), ("异常降级态", "失败提示不影响其他模块")],
         flow="填科目与天数 → 生成计划 → 逐日安排渲染 → 可结合复习任务到点提醒（F12 / A15）。",
         rules="后台线程每 30 秒扫描到期任务；计划文本按安全 Markdown 渲染（F27 / A30）。"),
    dict(no="P07", tab="memory", name="课程记忆", fa="F05 · F07 · F08 · F32 · F33", acc="A10 · A11 · A12 · A35 · A36",
         lead="课程资料全文沉淀处，也是杀手级功能 F06 / F33 的数据入口。",
         comps=[("v15-input", "matTitle 输入框", "placeholder：资料标题（可选）"),
                ("v15-big-textarea", "matContent 文本域", "placeholder：粘贴本课程课件、笔记、重点…"),
                ("v15-upload", "文件上传区", "白名单 .txt / .md / .markdown / .docx，≤ 2 MB、≤ 2 万字"),
                ("v15-material-list", "已上传资料列表", "每条含「查看全文 / 收起」与「下载 .md」（F07 / A11）"),
                ("v15-course-bar", "课程选择条", "新建 / 切换课程，课程名唯一非空（F05 / A10）")],
         states=[("默认态", "显示真实资料，如「第 3 章 树与二叉树」"), ("空态", "无资料时列表提示"),
                 ("上传中态", "按钮禁用与进度提示"), ("展开态", "全文安全渲染 / 收起"),
                 ("校验失败态", "课程不存在返回 400；类型或大小不合规逐项提示（F32 / A35）")],
         flow="选课程 → 粘贴或上传资料 → 保存进该课程 → 资料全文拼入问答上下文 → 切换课程即切换记忆。",
         rules="单份 4000 字、总量 12000 字预算（F33 / A36）；docx 全实体还原、SQLite 并发等待（F36 / A39）。"),
    dict(no="P08", tab="wrong", name="错题本", fa="F09 – F11 · F31 · F36", acc="A13 · A14 · A34 · A39",
         lead="录入 → 错因分析 + 变式题 → 标记掌握 → 筛选 → 导出，形成复习闭环。",
         comps=[("v15-input", "wqQuestion 文本域", "placeholder：错题题目"),
                ("v15-input", "wqUser 输入框", "placeholder：我的答案（可选）"),
                ("v15-input", "wqCorrect 输入框", "placeholder：正确答案（可选）"),
                ("v15-filter", "掌握状态筛选下拉", "GET /api/wrong-questions，按状态筛选（F09 / A13）"),
                ("v15-action-btn", "错因分析 / 变式题 / 标记掌握 / 导出", "POST .../analyze、POST .../master、GET .../export"),
                ("v15-wrong-list", "错题列表", "全部字段统一转义（F31 / A34）")],
         states=[("默认态", "错题列表有值"), ("空态", "筛选无结果显示空列表"),
                 ("忙碌态", "分析与导出按钮禁用"), ("校验失败态", "课程不存在拒绝写入（F32 / A35）")],
         flow="录入题干 / 我的答案 / 正确答案 → 错因分析 + 生成同类变式题 → 标记掌握 → 按状态筛选 → 导出 Markdown。",
         rules="导出走 blob 下载，失败不替换页面；docx 解析健壮性见 F36 / A39。"),
    dict(no="P09", tab="hardware", name="硬件联动", fa="F37（可选，不列入验收）", acc="不列入验收",
         lead="ESP32 接口清单与状态看板；仅表达连接设计，不代表物理验证已完成。",
         comps=[("v15-input", "hwTask 输入框", "placeholder：复习任务名，如：复习第3章"),
                ("v15-action-btn", "创建任务 / 测试提醒 / 专注灯", "POST /api/hardware/test、GET /api/hardware/status"),
                ("v15-hw-table", "6 点硬件交互清单表", "下行提醒 / 专注灯 + 上行状态看板共 6 个交互点"),
                ("v15-status-board", "状态看板", "展示版本指纹、Provider 状态、待复习 / 待掌握 / 专注状态")],
         states=[("默认态", "清单表与看板可见"),
                 ("未配置态", "未配置 ESP32_ENDPOINT 返回 sent: false 与原因"),
                 ("边界声明态", "ESP32 未实机联调，物理声光效果未验证")],
         flow="创建任务 / 测试提醒 → 后端尝试下发 → 未配置端点时返回 sent: false 与原因 → 主体功能不受影响。",
         rules="本页为可选加分项，明确不列入验收；不得把连接图或界面截图当作实物照片。"),
    dict(no="P10", tab="settings", name="设置", fa="F20 – F24 · F30 · F31", acc="A23 – A27 · A33 · A34",
         lead="主题三档 + 六类 Provider 运行时配置，无密钥自动回退演示模式。",
         comps=[("v15-theme", "主题三档与 6 套色板", "跟随系统 / 手动三档、自定义主色、本地持久化（F24 / A27）"),
                ("v15-input", "agentKey 密码框", "placeholder：必填，如 sk-… / 千帆 API Key"),
                ("v15-input", "agentSecret 密码框", "placeholder：仅文心旧版 WenxinWorkshop 需要"),
                ("v15-input", "agentModel 输入框", "placeholder：留空用默认：ernie-3.5-8k / moonshot-v1-8k"),
                ("v15-input", "agentBaseUrl 输入框", "placeholder：可选；千帆 v2 或自定义端点必填"),
                ("v15-input", "agentTokenUrl 输入框", "placeholder：仅文心旧版需要，可留空"),
                ("v15-provider-card", "6 个 Provider 状态卡", "OpenAI / 文心一言 / Kimi / Claude / 自定义 / 演示模式（F20 / A23）"),
                ("v15-action-btn", "保存 / 连通性自检 / 清除", "POST /api/agent/credentials、/test、/credentials/clear")],
         states=[("默认态", "演示模式激活，表单可填"), ("配置生效态", "运行时写入即时生效，无需重启（F21 / A24）"),
                 ("自检态", "真实探针校验并提示结果（F22 / A25）"),
                 ("回退态", "清除配置或调用异常后自动回退 demo（F23 / A26）"),
                 ("掩码态", "状态接口只返回密钥掩码，不回明文（F31 / A34）")],
         flow="选择 Provider → 填密钥 / 模型 / 地址 → 保存或自检 → 激活项写入运行时 SQLite → 未配置或异常自动回退演示模式。",
         rules="配置优先级：运行时 SQLite ＞ .env ＞ demo；本项目无真实厂商 API Key，演示模式是规则化应答而非大模型推理。"),
]

OLD_TERMS = ["Flask", "app.py", "V1.2", "V1.3", "V1.4", "四大厂商",
             "F1–F22", "A1–A24", "6 张表", "8 模块", "多用户已实现", "检索增强已实现"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def nav_html(cur):
    items = []
    for tab, label in NAV:
        items.append("<b>%s</b>" % label if tab == cur else label)
    return "　|　".join(items)


def page_html(p):
    name = "%s_%s_%s(%s)" % (VERSION, p["no"], p["name"], p["tab"])
    comps = "".join(
        "<tr data-comp=\"%s\"><td>%s</td><td>%s</td><td>%s</td></tr>" %
        (esc(c[0]), esc(c[0]), esc(c[1]), esc(c[2])) for c in p["comps"])
    states = "".join(
        "<span class=\"t%s\">%s：%s</span>" %
        (" tw" if ("态" in s and ("失败" in s or "异常" in s or "未配置" in s or "边界" in s)) else "",
         esc(s[0]), esc(s[1])) for s in p["states"])
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<title>%s</title>%s</head><body>"
        "<div class=\"hd\"><b>%s</b>　<span class=\"bv\">%s</span>　"
        "<span style=\"font-size:12px\">%s · %s</span></div>"
        "<div class=\"bar\">页面树：%s</div>"
        "<div class=\"bar\">功能编号 <b>%s</b>　｜　验收编号 <b>%s</b>　｜　版本标识 <b>%s</b></div>"
        "<div class=\"w\"><h2>%s %s（%s）</h2><p>%s</p>"
        "<h3>字段 · 组件 · 文案与规则</h3>"
        "<table><tr><th>组件（统一前缀 v15-）</th><th>字段 / 控件</th><th>文案或规则</th></tr>%s</table>"
        "<h3>交互状态</h3><div>%s</div>"
        "<h3>业务流程</h3><div class=\"f\">%s</div>"
        "<h3>规则与边界</h3><p class=\"mut\">%s</p></div>"
        "<div class=\"ft\"><b>需求核对卡 · %s</b><br>"
        "页面名：%s<br>功能：%s　｜　验收：%s<br>"
        "组件命名：v15- 前缀 + 语义名；状态命名：默认 / 忙碌 / 空 / 异常降级 / 回退 / 校验失败。<br>"
        "版本：%s ｜ 单一零依赖后端 + 原生前端 + SQLite 8 张表 ｜ 不含其他版本或未确认内容。</div>"
        "</body></html>" %
        (esc(name), CSS, APP, VERSION, p["no"], esc(p["name"]), nav_html(p["tab"]),
         esc(p["fa"]), esc(p["acc"]), VERSION,
         p["no"], esc(p["name"]), p["tab"], esc(p["lead"]), comps, states,
         esc(p["flow"]), esc(p["rules"]), p["no"], esc(name),
         esc(p["fa"]), esc(p["acc"]), VERSION)
    )


def index_html():
    rows = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" %
        (p["no"], esc(p["name"]), p["tab"], esc(p["fa"]), esc(p["acc"])) for p in PAGES)
    fnums = "、".join("F%02d" % n for n in range(1, 38))
    anums = "A01 – A39"
    return (
        "<!doctype html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<title>%s_P00_原型总览与需求索引</title>%s</head><body>"
        "<div class=\"hd\"><b>%s</b>　<span class=\"bv\">%s</span>　"
        "<span style=\"font-size:12px\">P00 · 原型总览与需求索引（评审索引页，非功能页）</span></div>"
        "<div class=\"bar\">本原型仅覆盖 %s 已确认页面范围：10 个前台功能页 + 本索引页；"
        "单机单用户课程作业原型，不设独立后台站点。</div>"
        "<div class=\"w\"><h2>页面树与需求项对照</h2>"
        "<p>下表可直接按需求项逐条核对；每页右下角另有「需求核对卡」。</p>"
        "<table><tr><th>页号</th><th>页面名</th><th>data-tab</th><th>功能编号</th><th>验收编号</th></tr>%s</table>"
        "<h3>需求编号全集</h3><div class=\"f\">功能：%s<br>验收：%s（每条给出可判定条件）<br>"
        "杀手级功能：F06 / F33 课程记忆绑定、隔离与上下文预算，对应 A05 / A06 / A36。</div>"
        "<h3>交互状态图例</h3><div>"
        "<span class=\"t\">默认态</span><span class=\"t\">忙碌态（F28 / A31）</span>"
        "<span class=\"t\">空态</span><span class=\"t tw\">异常降级态（F30 / A33）</span>"
        "<span class=\"t\">回退态（F23 / A26）</span><span class=\"t tw\">校验失败态（F32 / A35）</span></div>"
        "<h3>版本边界（不画大饼）</h3>"
        "<p class=\"mut\">无真实厂商 API Key，演示模式是规则化应答而非大模型推理；课程记忆为全文拼接，不是检索增强；"
        "ESP32 未实机联调（F37 不列入验收）；系统按单机单用户设计，暂无登录与权限；"
        "长文档记忆与多用户属愿景中的未来期望，不是 %s 已实现能力。</p>"
        "<h3>排除的旧版口径</h3><p class=\"mut\">不引入其他版本的页面、字段、接口与交互；"
        "本原型不出现双后端、旧厂商数量、旧功能编号段或旧库表数量等表述。</p></div>"
        "<div class=\"ft\"><b>版本标识：%s ｜ 页面 11 张（P00 索引 + P01 – P10 功能页）</b><br>"
        "命名规范：V1.5.0_页号_页面名(data-tab)；组件统一 v15- 前缀；字段与文案取自 static/index.html。<br>"
        "事实源：docs/软件需求规格说明书.md、static/index.html、version.py；生成源：gen_modao_v150.py。</div>"
        "</body></html>" % (VERSION, CSS, APP, VERSION, VERSION, rows, fnums, anums, VERSION, VERSION)
    )


def build():
    os.makedirs(OUT, exist_ok=True)
    items = [{"name": "%s_P00_原型总览与需求索引" % VERSION, "html": index_html()}]
    for p in PAGES:
        items.append({"name": "%s_%s_%s(%s)" % (VERSION, p["no"], p["name"], p["tab"]),
                      "html": page_html(p)})
    for it in items:
        fn = re.sub(r"[()（）]", "_", it["name"]).replace(" ", "") + ".html"
        io.open(os.path.join(OUT, fn), "w", encoding="utf-8").write(it["html"])
        for bad in OLD_TERMS:
            assert bad not in it["html"], "旧版口径污染 %s: %s" % (it["name"], bad)
        assert VERSION in it["html"], "缺版本标识 " + it["name"]
        assert it["html"].count("<table") >= 1, "缺组件表 " + it["name"]
    io.open(os.path.join(OUT, "html_list.json"), "w", encoding="utf-8").write(
        json.dumps(items, ensure_ascii=False, separators=(",", ":")))

    lines = ["# V1.5.0 墨刀原型 · 需求项核对表", "",
             "> 事实源：`docs/软件需求规格说明书.md`、`static/index.html`、`version.py`；"
             "生成源：`gen_modao_v150.py`。本表用于评审时按需求项逐条核对。", "",
             "| 页号 | 页面名 | data-tab | 功能编号 | 验收编号 | 关键状态 |",
             "|---|---|---|---|---|---|"]
    for p in PAGES:
        lines.append("| %s | %s | %s | %s | %s | %s |" %
                     (p["no"], p["name"], p["tab"], p["fa"], p["acc"],
                      " / ".join(s[0] for s in p["states"])))
    lines += ["", "## 版本与边界", "",
              "- 版本标识统一 `V1.5.0`；页面名 `V1.5.0_页号_页面名(data-tab)`；组件统一 `v15-` 前缀。",
              "- 页面范围：P00 评审索引页（非功能页）+ P01 – P10 共 10 个 V1.5.0 真实功能页。",
              "- 单机单用户课程作业原型，不设独立后台站点；管理操作由前台 5 处页面与 REST 接口承载。",
              "- 不列入验收：真实厂商密钥、检索增强、ESP32 实机、多用户与登录权限。", ""]
    io.open("原型需求核对表.md", "w", encoding="utf-8").write("\n".join(lines))
    print("页面数:", len(items))
    print("HTML 总字节:", sum(len(i["html"].encode("utf-8")) for i in items))
    print("版本标识 / 旧版口径 / 组件表 校验: 全部通过")
    for i in items:
        print("  ", i["name"], len(i["html"].encode("utf-8")), "B")


if __name__ == "__main__":
    build()
