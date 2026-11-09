# -*- coding: utf-8 -*-
"""V1.5.0 墨刀原型页面单一源（前台应用 + 后台管理 + 界面线框 + 页面互链）。

改原型只改本文件的 PAGES / MPAGES 数据，然后：
    python gen_modao_v150.py
产出 modao_v150/*.html、modao_v150/html_list.json（供墨刀 import_to_proto）、
以及 原型需求核对表.md（供第二次作业按需求项核对）。
事实源：docs/软件需求规格说明书.md、static/index.html、server.py、version.py。

设计约束：
1. 作业要求「前台应用与后台管理原型」——前台 10 页与后台管理 5 页同处一个工程、
   共用同一在线预览链接；作业原文未要求「独立后台站点」，不虚构登录 / 权限 / 用户管理。
2. 后台管理页只重组 V1.5.0 真实存在的管理操作与真实 REST 路由，不新增未实现功能。
3. 每页含界面线框（真实 UI 结构）、字段 / 组件表、交互状态、流程、规则与走查路径。
4. 页面名统一 V1.5.0_页号_页面名(标识)；组件统一 v15- 前缀；版本标识统一 V1.5.0。
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
    ".hd{background:#1E4FA8;color:#fff;padding:14px 22px}.hd b{font-size:18px}"
    ".bv{background:#fff;color:#1E4FA8;padding:3px 8px;border-radius:3px;font-size:12px;font-weight:bold}"
    ".bar{padding:7px 22px;background:#E8EFF8;font-size:12px;color:#3B4A63;line-height:1.9}"
    ".bar b{color:#1E4FA8}a{color:#1E4FA8;text-decoration:none}a:hover{text-decoration:underline}"
    ".w{margin:12px 22px;background:#fff;border:1px solid #D6DCE5;border-radius:6px;padding:14px}"
    "h2{font-size:17px;color:#1E4FA8;margin:0 0 6px}h3{font-size:14px;margin:12px 0 6px}"
    "p{line-height:1.6;margin:6px 0;color:#3B4A63}"
    "table{width:100%;border-collapse:collapse;font-size:12px}"
    "th,td{border:1px solid #DCE3EE;padding:5px 6px;text-align:left;vertical-align:top}"
    "th{background:#F0F4FB;color:#1E4FA8}"
    ".t{display:inline-block;background:#E8EFF8;color:#1E4FA8;padding:2px 6px;margin:0 4px 4px 0;border-radius:3px;font-size:12px}"
    ".tw{background:#FFF6E5;color:#8A5A00}"
    ".f{background:#F7F9FC;border-left:3px solid #1E4FA8;padding:9px 10px;font-size:12px;line-height:1.7}"
    ".ft{margin:12px 22px;background:#1E4FA8;color:#fff;border-radius:6px;padding:11px 14px;font-size:12px;line-height:1.7}"
    ".mut{color:#5A6B85}"
    ".frame{border:1px solid #C9D6EA;border-radius:5px;overflow:hidden;margin:8px 0;background:#fff}"
    ".frame-top{background:#1E4FA8;color:#fff;padding:8px 12px;font-size:12px}"
    ".frame-body{display:flex;min-height:118px}"
    ".frame-side{width:148px;background:#F0F4FB;border-right:1px solid #DCE3EE;padding:8px;font-size:11px;line-height:1.7;color:#3B4A63}"
    ".frame-side span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0 4px}"
    ".frame-side .on{background:#1E4FA8;color:#fff;border-radius:3px;padding:1px 5px;display:block}"
    ".frame-side .grp{margin-top:5px;border-top:1px dashed #C9D6EA;padding-top:4px;color:#5A6B85}"
    ".frame-main{flex:1;padding:10px 12px}"
    ".fw-h{font-size:13px;font-weight:bold;color:#1E4FA8;margin-bottom:8px}"
    ".fw-row{margin:5px 0;font-size:12px;color:#3B4A63}"
    ".fw-in{display:inline-block;border:1px solid #C9D6EA;border-radius:3px;padding:5px 8px;background:#F7F9FC;color:#5A6B85;min-width:190px;margin-right:6px}"
    ".fw-ta{border:1px solid #C9D6EA;border-radius:3px;padding:6px 8px;background:#F7F9FC;color:#5A6B85;height:30px;font-size:12px}"
    ".fw-btn{display:inline-block;background:#1E4FA8;color:#fff;border-radius:3px;padding:5px 10px;margin:0 5px 5px 0;font-size:11px}"
    ".fw-btn.gray{background:#93A4BF}"
    ".fw-card{display:inline-block;border:1px solid #DCE3EE;border-left:3px solid #1E4FA8;border-radius:3px;padding:6px 9px;margin:0 6px 6px 0;font-size:11px;min-width:92px}"
    ".fw-list{border:1px solid #DCE3EE;border-radius:3px;padding:6px 8px;font-size:11px;color:#3B4A63;background:#F7F9FC;margin:5px 0}"
    ".fw-tag{display:inline-block;background:#E8EFF8;color:#1E4FA8;border-radius:3px;padding:2px 6px;margin:0 4px 4px 0;font-size:11px}"
    ".fw-warn{background:#FFF6E5;color:#8A5A00;border-radius:3px;padding:5px 8px;font-size:11px;margin:5px 0}"
    "</style>"
)

# 前台 10 个真实 data-tab（static/index.html）
NAV = [
    ("dashboard", "学习概览"), ("chat", "智能问答"), ("study", "学习资源包"),
    ("summarize", "课件总结"), ("tutor", "习题辅导"), ("plan", "复习计划"),
    ("memory", "课程记忆"), ("wrong", "错题本"), ("hardware", "硬件联动"),
    ("settings", "设置"),
]

# no, tab, name, fa, acc, lead, comps[(组件, 字段/控件, 文案或规则)],
# states[(状态, 说明)], flow, rules, ui[(控件类型, 文案)], next(下一走查页)
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
         rules="空任务名回落默认名（F32 / A35）；统计与列表统一转义（F31 / A34）。",
         ui=[("card", "课程数 3"), ("card", "资料 5"), ("card", "错题 2"), ("card", "待复习 1"),
             ("card", "掌握率 暂无"), ("card", "今日专注 50 分"),
             ("input", "任务名，如：复习数据结构第 3 章"), ("btn", "添加"), ("btn-gray", "完成"),
             ("tag", "番茄钟 25:00"), ("list", "最近专注记录：数据结构 · 25 分钟")],
         next="P02"),
    dict(no="P02", tab="chat", name="智能问答", fa="F01 · F06 · F25 · F27 · F28 · F33 · F34",
         acc="A05 · A06 · A28 · A30 · A31 · A36 · A37",
         lead="课程内问答：切换课程即切换课程记忆，是本项目杀手级功能的界面入口。",
         comps=[("v15-mode-banner", "演示模式提示条", "未配置密钥或调用异常时回退 demo，响应带 fallback 标记（F23 / A26）"),
                ("v15-chat-log", "对话区", "回答按安全 Markdown 渲染，先转义再解析（F27 / A30）"),
                ("v15-chat-input", "chatInput 文本域", "placeholder：输入课程问题，或点右侧 🎤 语音输入（Chrome / Edge）…"),
                ("v15-mic-btn", "语音输入按钮", "Web Speech API，data-mic-target=chatInput（F25 / A28）"),
                ("v15-send-btn", "发送按钮", "请求期间禁用并提示，结束恢复（F28 / A31）"),
                ("v15-course-bar", "课程选择条", "切换时清空对话；过期异步响应丢弃（F34 / A37）")],
         states=[("默认态", "对话区空、输入可用"), ("忙碌态", "发送按钮禁用并显示状态"),
                 ("回退态", "演示模式提示条 + fallback 标记"), ("切课程态", "对话清空、上下文重建")],
         flow="选择课程 → build_course_context(course_id) 拼入该课程资料全文 → 交给 AgentProvider.complete() → 安全 Markdown 渲染回答。",
         rules="单份资料 4000 字、总量 12000 字预算，超出按序保留并提示（F33 / A36）；课程记忆为全文拼接，不是检索增强。",
         ui=[("warn", "演示模式：未配置密钥，回答由内置规则生成（fallback）"),
             ("list", "学生：请概括第 3 章树的遍历"),
             ("list", "助手：依据「第 3 章 树与二叉树」资料，先序 / 中序 / 后序…"),
             ("input", "输入课程问题，或点右侧 🎤 语音输入（Chrome / Edge）…"),
             ("btn", "🎤 语音"), ("btn", "发送"), ("tag", "课程：高等数学 ▾")],
         next="P03"),
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
         rules="思维导图输出树 JSON + SVG + Markdown 大纲 + Mermaid（F17 / A20）；一键全套走 POST /api/study/pack（F18 / A21）。",
         ui=[("input", "如：数学 / 高等数学上册（默认 高等数学上册）"),
             ("input", "章节 / 题量 / 难度"),
             ("btn", "自测题"), ("btn", "总结"), ("btn", "文章"), ("btn", "资料"),
             ("btn", "思维导图"), ("btn", "一键全套"), ("btn-gray", "导出 Markdown"),
             ("list", "结果五区：题目｜总结｜专题文章｜资料清单｜思维导图")],
         next="P04"),
    dict(no="P04", tab="summarize", name="课件总结", fa="F02 · F25 · F27 · F30", acc="A07 · A28 · A30 · A33",
         lead="粘贴课件文本，输出关键知识点与复习考点提纲。",
         comps=[("v15-big-textarea", "sumText 文本域", "placeholder：在此粘贴课件或笔记文字…"),
                ("v15-mic-btn", "语音输入", "Web Speech API，data-mic-target=sumText（F25 / A28）"),
                ("v15-action-btn", "生成总结按钮", "POST /api/summarize，请求中禁用（F28 / A31）"),
                ("v15-result", "富文本结果区", "安全 Markdown 排版：关键知识点 / 复习考点提纲")],
         states=[("默认态", "文本框为空可输入"), ("忙碌态", "按钮禁用并显示生成中"),
                 ("空值拦截态", "空内容不发起请求"), ("异常降级态", "失败逐模块提示，页面仍可操作")],
         flow="粘贴课件 → 点击生成 → 后端返回结构化总结 → 安全 Markdown 渲染。",
         rules="结果文本统一转义（F31 / A34）；任一 API 失败不使整页变砖（F30 / A33）。",
         ui=[("ta", "在此粘贴课件或笔记文字…"), ("btn", "🎤 语音"), ("btn", "生成总结"),
             ("list", "关键知识点 / 复习考点提纲（安全 Markdown 排版）")],
         next="P05"),
    dict(no="P05", tab="tutor", name="习题辅导", fa="F03 · F25 · F27 · F30", acc="A08 · A28 · A30 · A33",
         lead="引导式辅导：给分步思路与提示，不直接给最终答案。",
         comps=[("v15-big-textarea", "tutorText 文本域", "placeholder：在此粘贴题目…"),
                ("v15-mic-btn", "语音输入", "Web Speech API，data-mic-target=tutorText（F25 / A28）"),
                ("v15-action-btn", "「辅导一下」按钮", "POST /api/tutor，请求中禁用"),
                ("v15-result", "结果区", "分步思路 + 提示，按安全 Markdown 排版")],
         states=[("默认态", "题目输入区可用"), ("忙碌态", "按钮禁用"),
                 ("结果态", "展示分步思路与提示"), ("异常降级态", "逐模块错误提示")],
         flow="粘贴题目 → 点击辅导一下 → 返回分步思路与提示 → 安全 Markdown 渲染。",
         rules="与课件总结页共享输入组件 v15-big-textarea 与状态规则，保持组件命名与表现一致。",
         ui=[("ta", "在此粘贴题目…"), ("btn", "🎤 语音"), ("btn", "辅导一下"),
             ("list", "分步思路 ① … ② …｜提示：先画出树的形状，再判断遍历次序")],
         next="P06"),
    dict(no="P06", tab="plan", name="复习计划", fa="F04 · F12 · F27", acc="A09 · A15 · A30",
         lead="按科目与天数生成逐日复习安排。",
         comps=[("v15-input", "planSubject 输入框", "placeholder：考试科目，如：数据结构"),
                ("v15-input", "天数输入", "生成「第 1 天」至「第 N 天」逐日安排"),
                ("v15-action-btn", "生成计划按钮", "POST /api/review-plan"),
                ("v15-result", "结果区", "安全 Markdown 排版逐日计划")],
         states=[("默认态", "科目与天数待填"), ("忙碌态", "按钮禁用"),
                 ("结果态", "逐日安排可 30 秒扫描完"), ("异常降级态", "失败提示不影响其他模块")],
         flow="填科目与天数 → 生成计划 → 逐日安排渲染 → 可结合复习任务到点提醒（F12 / A15）。",
         rules="后台线程每 30 秒扫描到期任务；计划文本按安全 Markdown 渲染（F27 / A30）。",
         ui=[("input", "考试科目，如：数据结构"), ("input", "天数 7"), ("btn", "生成计划"),
             ("list", "第 1 天 … 第 N 天 逐日安排")],
         next="P07"),
    dict(no="P07", tab="memory", name="课程记忆", fa="F05 · F07 · F08 · F25 · F32 · F33",
         acc="A10 · A11 · A12 · A28 · A35 · A36",
         lead="课程资料全文沉淀处，也是杀手级功能 F06 / F33 的数据入口。",
         comps=[("v15-input", "matTitle 输入框", "placeholder：资料标题（可选）"),
                ("v15-big-textarea", "matContent 文本域", "placeholder：粘贴本课程课件、笔记、重点…"),
                ("v15-mic-btn", "语音输入", "Web Speech API，data-mic-target=matContent（F25 / A28）"),
                ("v15-upload", "文件上传区", "白名单 .txt / .md / .markdown / .docx，≤ 2 MB、≤ 2 万字"),
                ("v15-material-list", "已上传资料列表", "每条含「查看全文 / 收起」与「下载 .md」（F07 / A11）"),
                ("v15-course-bar", "课程选择条", "新建 / 切换课程，课程名唯一非空（F05 / A10）")],
         states=[("默认态", "显示真实资料，如「第 3 章 树与二叉树」"), ("空态", "无资料时列表提示"),
                 ("上传中态", "按钮禁用与进度提示"), ("展开态", "全文安全渲染 / 收起"),
                 ("校验失败态", "课程不存在返回 400；类型或大小不合规逐项提示（F32 / A35）")],
         flow="选课程 → 粘贴或上传资料 → 保存进该课程 → 资料全文拼入问答上下文 → 切换课程即切换记忆。",
         rules="单份 4000 字、总量 12000 字预算（F33 / A36）；docx 全实体还原、SQLite 并发等待（F36 / A39）。",
         ui=[("tag", "课程：数据结构 ▾　＋新建课程"),
             ("input", "资料标题（可选）"), ("ta", "粘贴本课程课件、笔记、重点…"),
             ("btn", "🎤 语音"), ("btn", "选择文件 .txt/.md/.docx"), ("btn", "保存资料"),
             ("list", "第 3 章 树与二叉树　查看全文 / 收起　下载 .md")],
         next="P08"),
    dict(no="P08", tab="wrong", name="错题本", fa="F09 – F11 · F25 · F31 · F36",
         acc="A13 · A14 · A28 · A34 · A39",
         lead="录入 → 错因分析 + 变式题 → 标记掌握 → 筛选 → 导出，形成复习闭环。",
         comps=[("v15-big-textarea", "wqQuestion 文本域", "placeholder：错题题目"),
                ("v15-mic-btn", "语音输入", "Web Speech API，data-mic-target=wqQuestion（F25 / A28）"),
                ("v15-input", "wqUser 输入框", "placeholder：我的答案（可选）"),
                ("v15-input", "wqCorrect 输入框", "placeholder：正确答案（可选）"),
                ("v15-filter", "掌握状态筛选下拉", "GET /api/wrong-questions，按状态筛选（F09 / A13）"),
                ("v15-action-btn", "错因分析 / 变式题 / 标记掌握 / 导出", "POST .../analyze、POST .../master、GET .../export"),
                ("v15-wrong-list", "错题列表", "全部字段统一转义（F31 / A34）")],
         states=[("默认态", "错题列表有值"), ("空态", "筛选无结果显示空列表"),
                 ("忙碌态", "分析与导出按钮禁用"), ("校验失败态", "课程不存在拒绝写入（F32 / A35）")],
         flow="录入题干 / 我的答案 / 正确答案 → 错因分析 + 生成同类变式题 → 标记掌握 → 按状态筛选 → 导出 Markdown。",
         rules="导出走 blob 下载，失败不替换页面；docx 解析健壮性见 F36 / A39。",
         ui=[("ta", "错题题目"), ("btn", "🎤 语音"), ("input", "我的答案（可选）"),
             ("input", "正确答案（可选）"), ("btn", "录入"), ("btn-gray", "全部 / 未掌握 / 已掌握"),
             ("list", "错题 1｜错因分析｜变式题｜标记掌握｜导出 Markdown")],
         next="P09"),
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
         rules="本页为可选加分项，明确不列入验收；不得把连接图或界面截图当作实物照片。",
         ui=[("input", "复习任务名，如：复习第3章"), ("btn", "创建任务"), ("btn", "测试提醒"),
             ("btn-gray", "专注灯"),
             ("list", "6 点硬件交互清单：到点提醒｜手动提醒｜番茄钟提醒｜专注灯｜状态看板｜通用下发"),
             ("warn", "未配置 ESP32_ENDPOINT：sent=false（未实机联调）")],
         next="P10"),
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
         rules="配置优先级：运行时 SQLite ＞ .env ＞ demo；本项目无真实厂商 API Key，演示模式是规则化应答而非大模型推理。",
         ui=[("tag", "跟随系统｜浅色｜深色｜6 套预设色"),
             ("input", "agentKey（密码框，回显仅掩码）"), ("input", "agentModel（可留空）"),
             ("input", "agentBaseUrl（可选）"), ("btn", "保存"), ("btn", "连通性自检"),
             ("btn-gray", "清除配置"),
             ("list", "6 个 Provider 状态卡：OpenAI｜文心一言｜Kimi｜Claude｜自定义｜演示模式 ✔")],
         next="M01"),
]

# 后台管理原型：作业原文「前台应用与后台管理原型」。只重组 V1.5.0 真实管理操作，
# 不虚构登录 / 权限 / 用户管理；与前台共用同一在线预览链接。
MPAGES = [
    dict(no="M01", tab="m01", name="课程与资料管理", fa="F05 · F07 · F08 · F32 · F33",
         acc="A04 · A10 · A11 · A12 · A35 · A36",
         lead="管理课程与课程资料：新建 / 切换课程，资料录入、上传、查看全文与下载；是课程记忆隔离的数据入口。",
         src="前台「课程记忆」页 #memory 与顶栏课程选择条；GET/POST /api/courses、GET/POST /api/courses/{id}/materials、POST .../upload。",
         comps=[("v15-course-bar", "课程选择 / 新建", "课程名唯一非空，空名返回 400（F05 / A10 / A04）"),
                ("v15-input / v15-big-textarea", "matTitle / matContent", "资料标题可选；正文必填；全文安全渲染（F07 / A11）"),
                ("v15-upload", "文件上传区", ".txt/.md/.markdown/.docx，≤ 2 MB、≤ 2 万字（F08 / A12）"),
                ("v15-material-list", "资料清单", "查看全文 / 收起、下载 .md；按课程隔离"),
                ("v15-mic-btn", "matContent 语音输入", "Web Speech API（F25 / A28）")],
         states=[("默认态", "课程与资料列表有值"), ("空态", "无资料时列表提示"),
                 ("校验失败态", "课程不存在 / 空课程名 / 类型或大小不合规逐项提示（F32 / A35）"),
                 ("上传中态", "按钮禁用与进度提示")],
         flow="新建或选择课程 → 粘贴 / 上传资料 → 校验课程存在与文件白名单 → 落库到该课程 → 列表刷新 → 资料全文进入该课程问答上下文。",
         rules="课程是记忆隔离单元；资料与错题写入前显式校验课程存在，拒绝孤儿数据。无 DELETE 路由，暂不提供在线删除；本页不新增未实现的权限或用户管理。",
         ui=[("tag", "课程：数据结构 ▾　＋新建课程"), ("input", "资料标题（可选）"),
             ("ta", "粘贴本课程课件、笔记、重点…"), ("btn", "上传 .txt/.md/.docx"), ("btn", "保存"),
             ("list", "资料清单：第 3 章 树与二叉树｜查看全文｜下载 .md"),
             ("warn", "课程名不可为空；资料 ≤ 2 MB / 2 万字")],
         next="M02"),
    dict(no="M02", tab="m02", name="智能体运行配置", fa="F20 – F24 · F30 · F31",
         acc="A23 – A27 · A33 · A34",
         lead="管理 6 类 Provider 的运行时凭据、激活项与连通性自检；密钥只回掩码。",
         src="前台「设置」页 #settings；/api/agent/providers、/api/agent/credentials、/api/agent/credentials/clear、/api/agent/test。",
         comps=[("v15-provider-card × 6", "Provider 状态卡", "OpenAI / 文心一言 / Kimi / Claude / 自定义 / 演示模式（F20 / A23）"),
                ("v15-input × 5", "agentKey / agentSecret / agentModel / agentBaseUrl / agentTokenUrl", "密钥密码框；状态接口只回掩码（F31 / A34）"),
                ("v15-action-btn", "保存 / 自检 / 清除", "运行时写入 SQLite 即时生效，无需重启（F21 / A24）"),
                ("v15-mode-banner", "演示模式提示条", "未配置或调用异常自动回退 demo（F23 / A26）")],
         states=[("默认态", "演示模式激活，表单可填"), ("配置生效态", "写入即生效（F21 / A24）"),
                 ("自检态", "真实探针返回可用 / 不可用（F22 / A25）"),
                 ("回退态", "清除或异常后自动回退 demo（F23 / A26）"), ("掩码态", "只回密钥掩码")],
         flow="选 Provider → 填密钥 / 模型 / 地址 → 保存或自检 → 激活项写入运行时 SQLite → 未配置或异常自动回退演示模式。",
         rules="配置优先级：运行时 SQLite ＞ .env ＞ demo；未知 Provider 或必填不全返回明确错误且不切换激活项。本项目无真实厂商密钥，演示模式为规则化应答。",
         ui=[("list", "6 个 Provider 状态卡：演示模式 ✔（当前激活）"),
             ("input", "agentKey（密码框，只读掩码）"), ("input", "agentModel（可留空）"),
             ("input", "agentBaseUrl（可选）"), ("btn", "保存"), ("btn", "连通性自检"),
             ("btn-gray", "清除配置"), ("warn", "未配置密钥时自动回退演示模式，功能流程不中断")],
         next="M03"),
    dict(no="M03", tab="m03", name="运行状态与硬件看板", fa="F26 · F29 · F37（可选）",
         acc="A01 · A29 · A32（F37 不列入验收）",
         lead="查看版本指纹、Provider 可用性、待复习 / 待掌握 / 专注状态，并手动下发硬件提醒。",
         src="前台「硬件联动」页 #hardware 与「学习概览」页 #dashboard；GET /api/status、/api/providers、/api/hardware/status、/api/hardware/test、/api/focus/state。",
         comps=[("v15-status-board", "状态看板", "version 来自 version.py，动态接口 Cache-Control: no-store（A01）"),
                ("v15-hw-table", "6 点硬件交互清单", "下行提醒 / 专注灯 + 上行状态看板共 6 个交互点"),
                ("v15-action-btn", "测试提醒 / 专注灯", "POST /api/hardware/test；未配置端点返回 sent: false 与原因"),
                ("v15-stat-card", "待复习 / 待掌握 / 专注状态", "无误题显示「暂无」而非 0.0%（F26 / A29）")],
         states=[("默认态", "看板与清单可见"), ("未配置态", "sent: false 与原因说明"),
                 ("边界声明态", "ESP32 未实机联调，物理声光效果未验证")],
         flow="打开看板 → 拉取 /api/status 与 /api/hardware/status → 渲染版本指纹与状态 → 可选手动下发提醒 → 主体功能不受影响。",
         rules="F37 为可选加分项、不列入验收；动态接口禁用缓存避免「页面新、接口旧」。本页不宣称已完成物理联调。",
         ui=[("card", "version 1.5.0"), ("card", "active_provider demo"), ("card", "待复习 1"),
             ("card", "待掌握 2"), ("card", "专注 25 分"),
             ("list", "6 点硬件交互清单与实时状态 JSON"),
             ("warn", "未配置 ESP32_ENDPOINT：sent=false（未实机联调）")],
         next="M04"),
    dict(no="M04", tab="m04", name="复习任务与专注管理", fa="F04 · F12 · F26 · F29",
         acc="A09 · A15 · A29 · A32",
         lead="管理待复习任务、到点提醒、逐日复习计划与专注记录。",
         src="前台「学习概览」页 #dashboard 与「复习计划」页 #plan；GET/POST /api/review-tasks、POST /api/review-tasks/{id}/done、/api/focus/sessions、/api/focus/state、POST /api/review-plan。",
         comps=[("v15-quick-task", "taskName 输入框", "空任务名回落默认名（F32 / A35）"),
                ("v15-action-btn", "添加 / 标记完成", "POST /api/review-tasks、POST /api/review-tasks/{id}/done"),
                ("v15-input", "planSubject / 天数", "生成「第 1 天」至「第 N 天」逐日安排（F04 / A09）"),
                ("v15-pomodoro", "番茄钟与专注记录", "GET/POST /api/focus/sessions、GET /api/focus/state"),
                ("v15-task-list", "待复习任务列表", "后台守护线程每 30 秒扫描到期任务并下发提醒（F12 / A15）")],
         states=[("默认态", "任务与计划有值"), ("空态", "无任务显示「暂无」"),
                 ("忙碌态", "生成中按钮禁用"), ("异常降级态", "单接口失败逐模块提示（F30 / A33）")],
         flow="添加任务或生成计划 → 写入 review_tasks / 展示逐日安排 → 后台每 30 秒扫描到期任务 → 标记完成 → 专注记录回写概览统计。",
         rules="任务 course_id 可空；计划文本按安全 Markdown 渲染；统计与列表统一转义（F31 / A34）。",
         ui=[("input", "任务名，如：复习数据结构第 3 章"), ("btn", "添加"), ("btn-gray", "标记完成"),
             ("input", "考试科目 / 天数"), ("btn", "生成计划"),
             ("list", "待复习任务：第 3 章树与二叉树（今日）｜第 1 天 … 第 N 天"),
             ("tag", "番茄钟 25:00　最近专注 50 分")],
         next="M05"),
    dict(no="M05", tab="m05", name="错题与归档管理", fa="F09 – F11 · F25 · F31 · F36",
         acc="A13 · A14 · A28 · A34 · A39",
         lead="管理错题录入、错因与变式题、掌握状态、筛选与 Markdown 归档导出。",
         src="前台「错题本」页 #wrong；GET/POST /api/wrong-questions、/analyze、/master、/export。",
         comps=[("v15-big-textarea", "wqQuestion + 语音输入", "data-mic-target=wqQuestion（F25 / A28）"),
                ("v15-input × 2", "wqUser / wqCorrect", "我的答案（可选）/ 正确答案（可选）"),
                ("v15-filter", "掌握状态筛选", "按全部 / 未掌握 / 已掌握筛选（F09 / A13）"),
                ("v15-action-btn", "错因分析 / 变式题 / 标记掌握 / 导出", "POST .../analyze、POST .../master、GET .../export"),
                ("v15-wrong-list", "错题归档列表", "全部字段统一转义（F31 / A34）")],
         states=[("默认态", "错题列表有值"), ("空态", "筛选无结果显示空列表"),
                 ("忙碌态", "分析与导出按钮禁用"), ("校验失败态", "课程不存在拒绝写入（F32 / A35）")],
         flow="录入错题 → 错因分析 + 同类变式题 → 标记掌握 → 按状态筛选 → 导出 Markdown 归档。",
         rules="导出走 fetch + blob，失败只提示、不替换页面（F36 / A39）；无 DELETE 路由，不提供在线删除；导出内容不含密钥明文。",
         ui=[("ta", "错题题目"), ("btn", "🎤 语音"), ("input", "我的答案 / 正确答案"),
             ("btn", "录入"), ("btn-gray", "全部 / 未掌握 / 已掌握"),
             ("list", "错题归档：错因分析｜变式题｜标记掌握｜导出 Markdown")],
         next="P00"),
]

# 全局验收项（SRS 第 6 章，非页面级），在 P00 索引给出归属
GLOBAL_ACC = [
    ("A01", "GET /api/status 返回 version = 1.5.0", "P00 索引 / M03 状态看板 / P10 设置"),
    ("A02", "不执行 pip install，python server.py 可启动并提供首页与 API", "全局启动项；非页面功能，见 SRS 与 README"),
    ("A03", "active_provider = demo 时全部功能流程可走通、无 5xx", "P02 回退态 / P10 演示模式"),
    ("A04", "新建课程返回 id；列表包含该课程；空课程名返回 400", "P07 课程记忆 / M01 课程与资料管理"),
]

# 跨页功能 F25 / A28 的 5 处真实承载（static/index.html 的 data-mic-target）
CROSS_F25 = [
    ("P02 智能问答", "chatInput"), ("P04 课件总结", "sumText"), ("P05 习题辅导", "tutorText"),
    ("P07 课程记忆 / M01", "matContent"), ("P08 错题本 / M05", "wqQuestion"),
]

OLD_TERMS = ["Flask", "app.py", "V1.2", "V1.3", "V1.4", "四大厂商",
             "F1–F22", "A1–A24", "6 张表", "8 模块", "多用户已实现", "检索增强已实现"]


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace('"', "&quot;"))


def page_name(p):
    return "%s_%s_%s(%s)" % (VERSION, p["no"], p["name"], p["tab"])


def file_name(name):
    return re.sub(r"[()（）]", "_", name).replace(" ", "") + ".html"


ALL = PAGES + MPAGES
BY_NO = {p["no"]: p for p in ALL}
BY_NO["P00"] = dict(no="P00", tab="index", name="原型总览与需求索引")
INDEX_NAME = "%s_P00_原型总览与需求索引" % VERSION


def nav_html(cur):
    """页面树用唯一页号作链接文本（完整页面名见 P00 索引表），避免长行折行。"""
    parts = ['<a href="%s">P00</a>' % file_name(INDEX_NAME)]
    for p in PAGES:
        parts.append("<b>%s</b>" % p["no"] if p["no"] == cur
                     else '<a href="%s">%s</a>' % (file_name(page_name(p)), p["no"]))
    parts.append('<span class="mut">｜ 后台管理：</span>')
    for p in MPAGES:
        parts.append("<b>%s</b>" % p["no"] if p["no"] == cur
                     else '<a href="%s">%s</a>' % (file_name(page_name(p)), p["no"]))
    return " ".join(parts)


def fw_controls(p):
    out = []
    for kind, text in p["ui"]:
        if kind == "input":
            out.append('<div class="fw-row"><span class="fw-in">%s</span></div>' % esc(text))
        elif kind == "ta":
            out.append('<div class="fw-ta">%s</div>' % esc(text))
        elif kind == "btn":
            out.append('<span class="fw-btn">%s</span>' % esc(text))
        elif kind == "btn-gray":
            out.append('<span class="fw-btn gray">%s</span>' % esc(text))
        elif kind == "card":
            out.append('<span class="fw-card">%s</span>' % esc(text))
        elif kind == "list":
            out.append('<div class="fw-list">%s</div>' % esc(text))
        elif kind == "tag":
            out.append('<span class="fw-tag">%s</span>' % esc(text))
        elif kind == "warn":
            out.append('<div class="fw-warn">%s</div>' % esc(text))
    return "".join(out)


def wireframe(p):
    side = []
    for tab, label in NAV[:4]:
        side.append('<span class="on">%s</span>' % label if tab == p["tab"] else "<span>%s</span>" % label)
    if p["tab"] in [m["tab"] for m in MPAGES]:
        side.append('<span class="grp">… 共 10 个前台页签</span>')
    else:
        if [t for t, _ in NAV].index(p["tab"]) >= 4:
            side.append('<span class="on">%s</span>' % p["name"])
        side.append('<span class="grp">… 共 10 个前台页签</span>')
    side.append('<span class="grp">后台管理视图（5 页）</span>')
    side.append('<span class="on">%s</span>' % p["name"] if p["tab"] in [m["tab"] for m in MPAGES]
                else '<span class="grp">M01 – M05 见 P00 索引</span>')
    return (
        '<div class="frame"><div class="frame-top">%s　｜　<span class="bv">%s</span>'
        '　课程：数据结构 ▾　｜　主题 ◐　｜　Provider 徽标</div>'
        '<div class="frame-body"><div class="frame-side">%s</div>'
        '<div class="frame-main"><div class="fw-h">%s · %s</div>%s'
        '<div class="fw-row mut" style="font-size:11px">线框按 static/index.html 的真实结构绘制；'
        '控件文案取自页面字段表，非效果图。</div></div></div></div>' %
        (APP, VERSION, "".join(side), p["no"], esc(p["name"]), fw_controls(p))
    )


def page_html(p):
    name = page_name(p)
    group = "前台应用" if p in PAGES else "后台管理原型"
    comps = "".join(
        '<tr data-comp="%s"><td>%s</td><td>%s</td><td>%s</td></tr>' %
        (esc(c[0]), esc(c[0]), esc(c[1]), esc(c[2])) for c in p["comps"])
    states = "".join(
        '<span class="t%s">%s：%s</span>' %
        (" tw" if ("失败" in s[0] or "异常" in s[0] or "未配置" in s[0] or "边界" in s[0]) else "",
         esc(s[0]), esc(s[1])) for s in p["states"])
    src = ('<h3>真实承载位置</h3><div class="f">%s</div>' % esc(p["src"])) if p.get("src") else ""
    nxt = p["next"]
    nxt_label = "P00 总览与需求索引" if nxt == "P00" else (
        "%s %s" % (nxt, BY_NO[nxt]["name"]) if nxt in BY_NO else nxt)
    nxt_href = file_name(INDEX_NAME) if nxt == "P00" else file_name(page_name(BY_NO[nxt]))
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<title>%s</title>%s</head><body>'
        '<div class="hd"><b>%s</b>　<span class="bv">%s</span>　'
        '<span style="font-size:12px">%s · %s · %s</span></div>'
        '<div class="bar">页面树：%s</div>'
        '<div class="bar">分组 <b>%s</b>　｜　功能编号 <b>%s</b>　｜　验收编号 <b>%s</b>　｜　版本标识 <b>%s</b></div>'
        '<div class="w"><h2>%s %s（%s）</h2><p>%s</p>%s'
        '<h3>界面线框 · %s 真实结构</h3>%s'
        '<h3>字段 · 组件 · 文案与规则</h3>'
        '<table><tr><th>组件（统一前缀 v15-）</th><th>字段 / 控件</th><th>文案或规则</th></tr>%s</table>'
        '<h3>交互状态</h3><div>%s</div>'
        '<h3>业务流程</h3><div class="f">%s</div>'
        '<h3>规则与边界</h3><p class="mut">%s</p>'
        '<h3>走查路径</h3><div class="f"><a href="%s">P00 总览与需求索引</a>　→　'
        '本页（%s）　→　<a href="%s">%s</a>；'
        '按需求编号逐项核对见 P00 索引与 原型需求核对表.md。</div></div>'
        '<div class="ft"><b>需求核对卡 · %s</b><br>'
        '页面名：%s<br>分组：%s　｜　功能：%s　｜　验收：%s<br>'
        '组件命名：v15- 前缀 + 语义名；状态命名：默认 / 忙碌 / 空 / 异常降级 / 回退 / 校验失败。<br>'
        '版本：%s ｜ 单一零依赖后端 + 原生前端 + SQLite 8 张表 ｜ 不含其他版本或未确认内容。</div>'
        '</body></html>' %
        (esc(name), CSS, APP, VERSION, p["no"], esc(p["name"]), group, nav_html(p["no"]),
         group, esc(p["fa"]), esc(p["acc"]), VERSION,
         p["no"], esc(p["name"]), p["tab"], esc(p["lead"]), src,
         VERSION, wireframe(p), comps, states,
         esc(p["flow"]), esc(p["rules"]),
         file_name(INDEX_NAME), esc(name), nxt_href, esc(nxt_label),
         p["no"], esc(name), group, esc(p["fa"]), esc(p["acc"]), VERSION)
    )


def index_html():
    def rows(pages, group):
        return "".join(
            '<tr><td><a href="%s">%s</a></td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' %
            (file_name(page_name(p)), p["no"], group, esc(p["name"]), p["tab"],
             esc(p["fa"]), esc(p["acc"])) for p in pages)
    cross = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b)) for a, b in CROSS_F25)
    gacc = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" %
                   (a, esc(b), esc(c)) for a, b, c in GLOBAL_ACC)
    fnums = "、".join("F%02d" % n for n in range(1, 38))
    total = len(PAGES) + len(MPAGES) + 1
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
        '<title>%s</title>%s</head><body>'
        '<div class="hd"><b>%s</b>　<span class="bv">%s</span>　'
        '<span style="font-size:12px">P00 · 原型总览与需求索引（评审索引页，非功能页）</span></div>'
        '<div class="bar">页面树：%s</div>'
        '<div class="bar">作业要求「前台应用与后台管理原型」两部分同处一个工程、共用同一在线预览链接；'
        '版本基线 %s，不引入其他版本或未确认页面。</div>'
        '<div class="w"><h2>页面树与需求项对照</h2>'
        '<p>点击页号可跳转到该原型页；每页含界面线框、字段 / 组件表、交互状态、业务流程、规则边界、'
        '需求核对卡与走查路径。</p>'
        '<table><tr><th>页号</th><th>分组</th><th>页面名</th><th>标识</th><th>功能编号</th><th>验收编号</th></tr>'
        '%s%s</table>'
        '<h3>跨页功能承载矩阵（F25 / A28 语音输入）</h3>'
        '<p class="mut">F25 / A28 为跨页功能，在下列 5 处真实输入框重复承载（static/index.html 的 data-mic-target），'
        '逐页表已分别标注，避免核对时漏项。</p>'
        '<table><tr><th>承载页</th><th>输入字段</th></tr>%s</table>'
        '<h3>全局验收项归属（A01 – A04）</h3>'
        '<table><tr><th>验收项</th><th>定义（SRS 第 6 章）</th><th>原型承载位置</th></tr>%s</table>'
        '<h3>需求编号全集</h3><div class="f">功能：%s<br>验收：A01 – A39（每条给出可判定条件）<br>'
        '杀手级功能：F06 / F33 课程记忆绑定、隔离与上下文预算，对应 A05 / A06 / A36。</div>'
        '<h3>交互状态图例</h3><div>'
        '<span class="t">默认态</span><span class="t">忙碌态（F28 / A31）</span>'
        '<span class="t">空态</span><span class="t tw">异常降级态（F30 / A33）</span>'
        '<span class="t">回退态（F23 / A26）</span><span class="t tw">校验失败态（F32 / A35）</span></div>'
        '<h3>后台管理原型边界（不额外假设）</h3>'
        '<p class="mut">作业原文要求「前台应用与后台管理原型」，未要求「独立后台站点」。M01 – M05 只重组 %s '
        '真实存在的管理操作与真实 REST 路由（课程与资料、运行配置、状态看板、任务与专注、错题归档），'
        '与前台同源、共用同一在线预览链接；不虚构登录、权限、用户管理、多租户或统计大盘。'
        '系统按单机单用户设计，暂无登录与权限。</p>'
        '<h3>版本边界（不画大饼）</h3>'
        '<p class="mut">无真实厂商 API Key，演示模式是规则化应答而非大模型推理；课程记忆为全文拼接，不是检索增强；'
        'ESP32 未实机联调（F37 不列入验收）；长文档记忆与多用户属愿景中的未来期望，不是 %s 已实现能力。</p>'
        '<h3>排除的旧版口径</h3><p class="mut">不引入其他版本的页面、字段、接口与交互；'
        '本原型不出现双后端、旧厂商数量、旧功能编号段或旧库表数量等表述。</p></div>'
        '<div class="ft"><b>版本标识：%s ｜ 页面 %d 张（P00 索引 + P01 – P10 前台 + M01 – M05 后台管理）</b><br>'
        '命名规范：V1.5.0_页号_页面名(标识)；组件统一 v15- 前缀；字段与文案取自 static/index.html。<br>'
        '事实源：docs/软件需求规格说明书.md、static/index.html、server.py、version.py；生成源：gen_modao_v150.py。</div>'
        '</body></html>' %
        (INDEX_NAME, CSS, APP, VERSION, nav_html("P00"), VERSION,
         rows(PAGES, "前台应用"), rows(MPAGES, "后台管理原型"), cross, gacc, fnums,
         VERSION, VERSION, VERSION, total)
    )


def build():
    os.makedirs(OUT, exist_ok=True)
    items = [{"name": INDEX_NAME, "html": index_html()}]
    for p in ALL:
        items.append({"name": page_name(p), "html": page_html(p)})
    for it in items:
        io.open(os.path.join(OUT, file_name(it["name"])), "w", encoding="utf-8").write(it["html"])
        for bad in OLD_TERMS:
            assert bad not in it["html"], "旧版口径污染 %s: %s" % (it["name"], bad)
        assert VERSION in it["html"], "缺版本标识 " + it["name"]
        assert it["html"].count("<table") >= 1, "缺表格 " + it["name"]
        assert 'class="frame"' in it["html"] or it["name"] == INDEX_NAME, "缺界面线框 " + it["name"]
        assert '<a href=' in it["html"], "缺页面互链 " + it["name"]
    io.open(os.path.join(OUT, "html_list.json"), "w", encoding="utf-8").write(
        json.dumps(items, ensure_ascii=False, separators=(",", ":")))

    lines = ["# V1.5.0 墨刀原型 · 需求项核对表", "",
             "> 事实源：`docs/软件需求规格说明书.md`、`static/index.html`、`server.py`、`version.py`；"
             "生成源：`gen_modao_v150.py`。本表用于评审时按需求项逐条核对。", "",
             "## 1 前台应用原型（P01 – P10）", "",
             "| 页号 | 页面名 | 标识 | 功能编号 | 验收编号 | 关键状态 |",
             "|---|---|---|---|---|---|"]
    for p in PAGES:
        lines.append("| %s | %s | %s | %s | %s | %s |" %
                     (p["no"], p["name"], p["tab"], p["fa"], p["acc"],
                      " / ".join(s[0] for s in p["states"])))
    lines += ["", "## 2 后台管理原型（M01 – M05）", "",
              "| 页号 | 页面名 | 标识 | 真实承载位置 | 功能编号 | 验收编号 | 关键状态 |",
              "|---|---|---|---|---|---|---|"]
    for p in MPAGES:
        lines.append("| %s | %s | %s | %s | %s | %s | %s |" %
                     (p["no"], p["name"], p["tab"], p["src"], p["fa"], p["acc"],
                      " / ".join(s[0] for s in p["states"])))
    lines += ["", "## 3 跨页功能 F25 / A28 承载矩阵", "",
              "| 承载页 | 输入字段（data-mic-target） |", "|---|---|"]
    lines += ["| %s | `%s` |" % (a, b) for a, b in CROSS_F25]
    lines += ["", "## 4 全局验收项 A01 – A04 归属", "",
              "| 验收项 | 定义（SRS 第 6 章） | 原型承载位置 |", "|---|---|---|"]
    lines += ["| %s | %s | %s |" % (a, b, c) for a, b, c in GLOBAL_ACC]
    lines += ["", "## 5 版本与边界", "",
              "- 版本标识统一 `V1.5.0`；页面名 `V1.5.0_页号_页面名(标识)`；组件统一 `v15-` 前缀。",
              "- 页面范围：P00 索引 + P01 – P10 前台应用 + M01 – M05 后台管理，共 %d 页，同处一个墨刀工程、共用同一在线预览链接。" %
              (len(ALL) + 1),
              "- 每页含界面线框、字段 / 组件表、交互状态、业务流程、规则边界、需求核对卡与页面互链。",
              "- 作业原文要求「前台应用与后台管理原型」，未要求「独立后台站点」；M01 – M05 只重组 V1.5.0 真实管理操作，不虚构登录 / 权限 / 用户管理。",
              "- 系统按单机单用户设计，暂无登录与权限；不列入验收：真实厂商密钥、检索增强、ESP32 实机、多用户。", ""]
    io.open("原型需求核对表.md", "w", encoding="utf-8").write("\n".join(lines))
    print("页面数:", len(items))
    print("HTML 总字节:", sum(len(i["html"].encode("utf-8")) for i in items))
    print("版本标识 / 旧版口径 / 组件表 / 界面线框 / 页面互链 校验: 全部通过")
    for i in items:
        print("  ", i["name"], len(i["html"].encode("utf-8")), "B")


if __name__ == "__main__":
    build()
