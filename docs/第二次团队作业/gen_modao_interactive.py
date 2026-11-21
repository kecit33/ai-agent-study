# -*- coding: utf-8 -*-
"""V1.5.0 墨刀原型「交互版」单一源。

与 gen_modao_v150.py 的分工：
- gen_modao_v150.py 只保留页面 / 组件 / 需求数据（PAGES、MPAGES、NAV 等事实源）；
- 本文件负责渲染：信息架构与页面层级、应用界面分镜、交互动作→状态反馈→跳转、
  状态切换演示，以及一份浏览器可直接点击操作的「可交互走查版」。

产物（写入 modao_v150/）：
- V1.5.0_P00_原型总览与需求索引.html（重构为信息架构 + 核心场景流程页）
- V1.5.0_P01..P10 / M01..M05 *.html（重构为应用界面 + 交互分镜页）
- 交互走查版.html（本地可交互单文件，JS 模拟状态，不调用真实接口）
- html_list.json（墨刀 import_to_proto 载荷，仍为 16 页）
- 原型需求核对表.md（增加交互动作 / 跳转关系 / 状态反馈核对）

运行：python gen_modao_v150.py（其 main 已委托本文件的 build）。
事实源：docs/软件需求规格说明书.md、static/index.html、server.py、version.py。
边界：墨刀 HTML 导入不保留脚本，故在线工程用「状态分镜 + 可点击页面链接」表达交互；
      真实点击与状态切换由同目录「交互走查版.html」在浏览器本地演示。
"""
import io
import json
import os

from gen_modao_v150 import (
    ALL, BY_NO, CROSS_F25, GLOBAL_ACC, INDEX_NAME, MPAGES, NAV, OLD_TERMS,
    PAGES, VERSION, esc, file_name, nav_html, page_name,
)

APP = "AI 校园学习陪伴助手"
OUT = "modao_v150"

CSS = """<style>
*{box-sizing:border-box}
body{font:13px/1.6 'Microsoft YaHei',Arial,sans-serif;margin:0;background:#F4F7FC;color:#1B2430}
a{color:#1750A8;text-decoration:none}a:hover{text-decoration:underline}
.hd{background:#173E7E;color:#fff;padding:13px 22px}.hd b{font-size:18px}
.bv{background:#fff;color:#173E7E;padding:3px 8px;border-radius:3px;font-size:12px;font-weight:bold}
.bar{padding:7px 22px;background:#E7EFFA;font-size:12px;color:#35465F;line-height:1.9}
.bar b{color:#1750A8}
.w{margin:12px 22px;background:#fff;border:1px solid #D5DEEC;border-radius:6px;padding:14px}
h2{font-size:17px;color:#173E7E;margin:0 0 8px}h3{font-size:14px;margin:14px 0 7px;color:#173E7E}
p{line-height:1.65;margin:6px 0;color:#3B4A63}
.mut{color:#60708C;font-size:12px}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{border:1px solid #DCE3EE;padding:6px 7px;text-align:left;vertical-align:top}
th{background:#EEF3FB;color:#173E7E}
.t{display:inline-block;background:#E7EFFA;color:#1750A8;padding:3px 7px;margin:0 5px 5px 0;border-radius:3px;font-size:12px}
.tw{background:#FFF1D9;color:#8A5A00}.tok{background:#E5F5EC;color:#1D7A43}
.f{background:#F6F9FD;border-left:3px solid #1750A8;padding:9px 11px;font-size:12px;line-height:1.7}
.ft{margin:12px 22px;background:#173E7E;color:#fff;border-radius:6px;padding:11px 14px;font-size:12px;line-height:1.7}
.ft a{color:#BBD6FF}
/* 应用界面分镜 */
.screen{border:1px solid #C4D3E8;border-radius:6px;overflow:hidden;background:#fff;margin:8px 0}
.s-top{background:#173E7E;color:#fff;padding:8px 12px;font-size:12px;display:flex;gap:12px;align-items:center}
.s-top .sp{flex:1}
.s-badge{background:#fff;color:#173E7E;border-radius:3px;padding:2px 7px;font-size:11px;font-weight:bold}
.s-body{display:flex;min-height:150px}
.s-side{width:150px;background:#F0F4FB;border-right:1px solid #DCE3EE;padding:8px;font-size:11px;line-height:1.8;color:#415170;flex:none}
.s-side span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;padding:0 5px}
.s-side .on{background:#1750A8;color:#fff;border-radius:3px;padding:1px 5px}
.s-side .grp{margin-top:5px;border-top:1px dashed #C4D3E8;padding-top:4px;color:#60708C}
.s-main{flex:1;padding:10px 12px;min-width:0}
.s-h{font-size:13px;font-weight:bold;color:#173E7E;margin-bottom:7px}
.fw-row{margin:5px 0;font-size:12px;color:#3B4A63}
.fw-in{display:inline-block;border:1px solid #C4D3E8;border-radius:3px;padding:5px 8px;background:#F8FAFD;color:#60708C;min-width:190px;margin-right:6px}
.fw-ta{border:1px solid #C4D3E8;border-radius:3px;padding:6px 8px;background:#F8FAFD;color:#60708C;height:30px;font-size:12px}
.fw-btn{display:inline-block;background:#1750A8;color:#fff;border-radius:3px;padding:5px 10px;margin:0 5px 5px 0;font-size:11px}
.fw-btn.gray{background:#8FA2BE}
.fw-card{display:inline-block;border:1px solid #DCE3EE;border-left:3px solid #1750A8;border-radius:3px;padding:6px 9px;margin:0 6px 6px 0;font-size:11px;min-width:92px}
.fw-list{border:1px solid #DCE3EE;border-radius:3px;padding:6px 8px;font-size:11px;color:#3B4A63;background:#F8FAFD;margin:5px 0}
.fw-tag{display:inline-block;background:#E7EFFA;color:#1750A8;border-radius:3px;padding:2px 6px;margin:0 4px 4px 0;font-size:11px}
.fw-warn{background:#FFF1D9;color:#8A5A00;border-radius:3px;padding:5px 8px;font-size:11px;margin:5px 0}
/* 状态分镜 */
.story{display:flex;align-items:stretch;gap:0;flex-wrap:wrap;margin:8px 0}
.scene{border:1px solid #D5DEEC;border-top:3px solid #1750A8;border-radius:4px;padding:8px 10px;min-width:150px;max-width:220px;flex:1;background:#FBFCFF}
.scene.warn{border-top-color:#D18B00;background:#FFFCF6}
.scene.ok{border-top-color:#1D7A43;background:#F7FCF9}
.scene b{display:block;color:#173E7E;font-size:12px;margin-bottom:3px}
.scene span{font-size:11px;color:#4C5B75;line-height:1.55;display:block}
.arrow{align-self:center;color:#8FA2BE;font-size:18px;padding:0 7px}
/* 信息架构 */
.ia{border:1px solid #D5DEEC;border-radius:5px;padding:11px 13px;background:#FBFCFF}
.ia .root{font-weight:bold;color:#173E7E;margin-bottom:7px}
.ia .lv1{margin:6px 0 4px;font-weight:bold;color:#1750A8}
.ia .lv2{margin:3px 0 3px 18px;color:#415170}
.ia .lv3{margin:3px 0 3px 36px;color:#60708C}
.ia a{display:inline-block;background:#E7EFFA;color:#1750A8;border-radius:3px;padding:2px 7px;margin:2px 4px 2px 0;font-size:12px}
.flow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:8px 0}
.step{border:1px solid #C4D3E8;border-radius:5px;padding:8px 10px;min-width:135px;background:#fff}
.step b{color:#173E7E;display:block;font-size:12px}
.step span{font-size:11px;color:#60708C;display:block;line-height:1.5}
.flowarr{color:#8FA2BE;font-size:17px}
.hint{background:#EFF5FF;border:1px solid #C9DDFB;border-left:4px solid #1750A8;border-radius:4px;padding:9px 11px;font-size:12px;color:#27436E;line-height:1.7;margin:8px 0}
.alert{background:#FFF4E2;border:1px solid #F0D6A2;border-left:4px solid #D18B00;border-radius:4px;padding:9px 11px;font-size:12px;color:#7C5200;line-height:1.7;margin:8px 0}
</style>"""


# 交互动作：(动作, 触发控件, 状态反馈, 目标页)
ACTS = {
    "P01": [
        ("查看待复习任务", "统计卡片「待复习 1」", "卡片进入键盘焦点态并高亮，列表定位到任务行", "P06"),
        ("添加复习任务", "任务名输入 + 「添加」", "列表新增一行；空名回落默认名；提示「已添加」", "P01"),
        ("标记任务完成", "任务行「完成」", "任务状态变「已完成」，待复习数 -1", "P01"),
        ("启动番茄钟", "「开始专注」", "25:00 倒计时启动，状态徽标变「专注中」", "P09"),
        ("切换课程", "顶栏课程选择条", "六项统计按当前课程刷新，避免跨课程串数", "P01"),
    ],
    "P02": [
        ("选定课程记忆", "顶栏课程：数据结构", "对话区清空，上下文徽标显示「数据结构 · 3 份资料」", "P07"),
        ("发起课程内提问", "输入问题 + 「发送」", "按钮禁用并显示「思考中…」；回答卡按安全 Markdown 渲染", "P02"),
        ("查看回答依据", "回答卡「查看依据资料」", "跳到该课程资料列表，核对回答来源", "P07"),
        ("语音输入", "「🎤 语音」", "进入听写态，文字回填输入框后可继续编辑", "P02"),
        ("切课验证隔离", "顶栏课程：高等数学", "对话清空、上下文重建；旧课程回答不跨课出现", "P02"),
        ("无密钥回退", "Provider 徽标 demo", "提示条显示演示模式，回答带 fallback 标记", "P10"),
    ],
    "P03": [
        ("填写生成参数", "教材 / 章节 / 题量 / 难度", "未内置学科回落「自定义科目」，不报错中断", "P03"),
        ("一键全套", "「一键全套」", "5 个生成按钮同时禁用，五区依次填充结果", "P03"),
        ("查看自测题", "结果区「题目」", "展示标准答案、分步解析与考点", "P05"),
        ("回写课程记忆", "结果区「存入课程记忆」", "提示「已存入数据结构」，课程记忆资料数 +1", "P07"),
        ("导出 Markdown", "「导出 Markdown」", "blob 下载；失败只提示不替换页面", "P03"),
    ],
    "P04": [
        ("粘贴课件", "大文本框 / 语音输入", "空内容点击生成被拦截并提示", "P04"),
        ("生成总结", "「生成总结」", "按钮禁用并显示「生成中…」，结果区输出知识点与考点提纲", "P04"),
        ("接口异常", "模拟 /api/summarize 失败", "本模块显示错误提示，其他模块仍可操作", "P04"),
    ],
    "P05": [
        ("粘贴题目", "大文本框 / 语音输入", "输入框可编辑，语音结果回填", "P05"),
        ("引导式辅导", "「辅导一下」", "按钮禁用；输出分步思路与提示，不给最终答案", "P05"),
        ("转入错题本", "结果区「记入错题本」", "带题干跳转到错题录入框", "P08"),
    ],
    "P06": [
        ("生成计划", "科目 + 天数 + 「生成计划」", "按钮禁用；结果区渲染第 1 天至第 N 天安排", "P06"),
        ("加入复习任务", "结果行「加入任务」", "提示「已加入复习任务」，概览待复习数 +1", "P01"),
        ("到点提醒", "后台 30 秒扫描到期任务", "状态徽标变「即将到期」，可链接硬件测试", "M04"),
    ],
    "P07": [
        ("新建 / 切换课程", "课程选择条「＋新建课程」", "课程名唯一非空；空名返回 400 提示", "M01"),
        ("保存课程资料", "标题 / 正文 + 「保存资料」", "资料列表新增一行；上下文预算条按字数更新", "P07"),
        ("文件上传", "「选择文件」", "校验 .txt/.md/.markdown/.docx、≤2 MB、≤2 万字，按钮禁用显示上传中", "P07"),
        ("查看全文 / 收起", "资料行「查看全文」", "展开全文安全渲染，再点收起回到列表", "P07"),
        ("下载 .md", "资料行「下载 .md」", "触发 Markdown 文件下载，页面不跳转", "P07"),
        ("带入问答", "资料行「用于问答」", "跳到智能问答并把该课程资料拼入上下文", "P02"),
    ],
    "P08": [
        ("录入错题", "题干 / 我的答案 / 正确答案 + 「录入」", "列表新增未掌握错题", "P08"),
        ("错因与变式题", "错题行「错因分析 / 变式题」", "按钮禁用；展开错因与同类变式题", "P05"),
        ("标记掌握", "错题行「标记掌握」", "状态由「未掌握」变「已掌握」，掌握率刷新", "P08"),
        ("状态筛选", "筛选下拉：全部 / 未掌握 / 已掌握", "列表按状态过滤，空结果显示空态而非 0.0%", "P08"),
        ("导出归档", "「导出 Markdown」", "blob 下载；失败只提示不替换页面", "M05"),
    ],
    "P09": [
        ("创建提醒任务", "任务名 + 「创建任务」", "列表新增任务，状态看板待复习数更新", "M04"),
        ("测试提醒", "「测试提醒」", "未配置端点返回 sent:false 与原因，主体功能不中断", "M03"),
        ("专注灯", "「专注灯」", "展示下发状态；不宣称已完成实机联调", "M03"),
        ("查看 6 点清单", "硬件交互清单表", "下行提醒 / 专注灯 + 上行状态看板共 6 点", "M03"),
    ],
    "P10": [
        ("切换 Provider", "6 个 Provider 状态卡", "表单显示对应必填字段，当前激活项高亮", "M02"),
        ("保存配置", "密钥 / 模型 / 地址 + 「保存」", "运行时写入立即生效；状态只回密钥掩码", "M02"),
        ("连通性自检", "「连通性自检」", "按钮禁用并显示探针结果；失败不切换激活项", "M02"),
        ("清除配置", "「清除配置」", "自动回退 demo，提示条重新出现", "P02"),
        ("主题切换", "跟随系统 / 浅色 / 深色 + 色板", "主题即时切换并本地持久化", "P01"),
    ],
    "M01": [
        ("新建课程", "课程名 + 「新建」", "课程列表新增；空名 / 重名返回 400 提示", "P07"),
        ("资料入库", "标题 / 正文 / 文件 + 「保存」", "校验课程存在与文件白名单后落库并刷新列表", "P07"),
        ("查看全文", "资料行「查看全文」", "全文安全渲染；再点「收起」回到列表", "P07"),
        ("孤儿数据拦截", "模拟不存在的 course_id", "写入被拒绝并提示课程不存在", "M01"),
    ],
    "M02": [
        ("选择 Provider", "Provider 卡片", "激活项高亮，表单切换对应字段", "P10"),
        ("保存 / 自检 / 清除", "三个动作按钮", "保存即生效；自检出探针结果；清除回退 demo", "P10"),
        ("密钥掩码", "状态接口返回", "只显示掩码，不回明文", "M02"),
    ],
    "M03": [
        ("查看版本指纹", "状态看板 version", "显示 1.5.0，动态接口 no-store 避免页面新接口旧", "P00"),
        ("查看 Provider 状态", "状态看板 active_provider", "无密钥显示 demo，回答走规则化回退", "P10"),
        ("手动下发提醒", "「测试提醒」", "未配置端点返回 sent:false 与原因", "P09"),
        ("无误题显示", "必备掌握数卡片", "显示「暂无」而非 0.0%", "P01"),
    ],
    "M04": [
        ("添加任务", "任务名 + 「添加」", "列表新增；空任务名回落默认名", "P01"),
        ("标记完成", "任务行「完成」", "状态变已完成，待复习数 -1", "P01"),
        ("生成计划", "科目 + 天数", "逐日安排渲染到任务视图", "P06"),
        ("查看专注记录", "番茄钟 / 最近专注", "展示 25:00 与累计专注分钟", "P09"),
    ],
    "M05": [
        ("筛选错题", "掌握状态下拉", "列表按状态过滤，空结果显示空态", "P08"),
        ("标记掌握", "错题行「标记掌握」", "状态变已掌握，概览掌握率刷新", "P08"),
        ("导出归档", "「导出 Markdown」", "blob 下载，失败只提示", "P08"),
    ],
}


def target_href(no):
    if no == "P00":
        return file_name(INDEX_NAME)
    if no in BY_NO:
        return file_name(page_name(BY_NO[no]))
    return "#"


def group_of(p):
    return "后台管理原型" if p in MPAGES else "前台应用"


def side_html(p):
    out = []
    for tab, label in NAV[:4]:
        out.append('<span class="on">%s</span>' % label if tab == p["tab"] else "<span>%s</span>" % label)
    if p["tab"] in [m["tab"] for m in MPAGES]:
        out.append('<span class="grp">前台共 10 页，见 P00</span>')
    else:
        idx = [t for t, _ in NAV].index(p["tab"])
        if idx >= 4:
            out.append('<span class="on">%s</span>' % p["name"])
        out.append('<span class="grp">前台共 10 页，见 P00</span>')
    out.append('<span class="grp">后台管理视图（5 页）</span>')
    out.append('<span class="on">%s</span>' % p["name"] if p["tab"] in [m["tab"] for m in MPAGES]
               else '<span class="grp">M01 – M05 见 P00</span>')
    return "".join(out)


def screen_controls(p):
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


def screen_html(p):
    return (
        '<div class="screen"><div class="s-top"><b>%s</b><span class="s-badge">%s</span>'
        '<span class="sp"></span>课程：数据结构 ▾<span class="s-badge">上下文已绑定</span>'
        '<span class="s-badge">Provider：demo</span></div>'
        '<div class="s-body"><div class="s-side">%s</div>'
        '<div class="s-main"><div class="s-h">%s %s · 应用界面</div>%s'
        '<div class="fw-row mut">界面控件取自 static/index.html 的真实字段与文案；'
        '本页在墨刀中用分镜表达操作后的状态，浏览器点击演示见「交互走查版.html」。</div>'
        '</div></div></div>' %
        (APP, VERSION, side_html(p), p["no"], esc(p["name"]), screen_controls(p))
    )


def story_html(p):
    scenes = []
    for i, (name, desc) in enumerate(p["states"]):
        cls = " warn" if ("失败" in name or "异常" in name or "未配置" in name or "边界" in name) else (
            " ok" if ("生效" in name or "结果" in name or "展开" in name or "直达" in name) else "")
        scenes.append('<div class="scene%s"><b>%s</b><span>%s</span></div>' %
                      (cls, esc(name), esc(desc)))
        if i < len(p["states"]) - 1:
            scenes.append('<div class="arrow">→</div>')
    return '<div class="story">%s</div>' % "".join(scenes)


def acts_html(p):
    rows = []
    for act, trigger, feedback, target in ACTS.get(p["no"], []):
        rows.append('<tr><td>%s</td><td>%s</td><td>%s</td><td><a href="%s">%s</a></td></tr>' %
                    (esc(act), esc(trigger), esc(feedback), target_href(target), esc(target)))
    return (
        '<table><tr><th>用户动作</th><th>触发控件</th><th>状态反馈</th><th>跳转页（可点击）</th></tr>%s</table>' %
        "".join(rows)
    )


def page_html(p):
    no = p["no"]
    group = group_of(p)
    nxt = p["next"]
    nxt_label = "P00 信息架构" if nxt == "P00" else (
        "%s %s" % (nxt, BY_NO[nxt]["name"]) if nxt in BY_NO else nxt)
    comps = "".join('<tr><td>%s</td><td>%s</td><td>%s</td></tr>' %
                    (esc(c[0]), esc(c[1]), esc(c[2])) for c in p["comps"])
    src = ('<h3>真实承载位置</h3><div class="f">%s</div>' % esc(p["src"])) if p.get("src") else ""
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>%s</title>%s</head><body>'
        '<div class="hd"><b>%s</b>　<span class="bv">%s</span>　'
        '<span style="font-size:12px">%s · %s · %s</span></div>'
        '<div class="bar">页面树：%s</div>'
        '<div class="bar">分组 <b>%s</b>　｜　功能 <b>%s</b>　｜　验收 <b>%s</b>　｜　'
        '层级 <b>应用 / %s / %s</b>　｜　版本 <b>%s</b></div>'
        '<div class="w"><h2>%s %s · 应用界面与交互分镜</h2><p>%s</p>%s'
        '<h3>① 应用界面（真实字段与文案）</h3>%s'
        '<h3>② 状态切换分镜（左 → 右依次演示）</h3>%s'
        '<h3>③ 交互动作 → 状态反馈 → 页面跳转</h3>%s'
        '<div class="hint">上表「跳转页」为可点击页面链接；墨刀 HTML 导入不保留脚本，'
        '因此在线工程以状态分镜 + 页面链接表达交互。需要真实点击体验时，打开同目录 '
        '<b>交互走查版.html</b>（浏览器本地 JS 模拟，不调用真实接口）。</div>'
        '<h3>④ 字段 · 组件 · 文案与规则</h3>'
        '<table><tr><th>组件（v15- 前缀）</th><th>字段 / 控件</th><th>文案或规则</th></tr>%s</table>'
        '<h3>⑤ 业务流程与规则边界</h3><div class="f">%s</div><p class="mut">%s</p>'
        '<h3>⑥ 走查路径</h3><div class="f"><a href="%s">P00 信息架构与核心流程</a>　→　本页（%s）　→　'
        '<a href="%s">%s</a>；按需求编号逐项核对见 P00 与《原型需求核对表.md》。</div></div>'
        '<div class="ft"><b>需求核对卡 · %s</b><br>页面名：%s<br>分组：%s ｜ 功能：%s ｜ 验收：%s<br>'
        '交互：%d 条动作，%d 个状态分镜，全部标注触发控件与反馈；状态命名沿用默认 / 忙碌 / 空 / 异常降级 / 回退 / 校验失败。<br>'
        '版本：%s ｜ 单一零依赖后端 + 原生前端 + SQLite 8 张表 ｜ 不含其他版本或未确认内容。</div>'
        '</body></html>' %
        (esc(page_name(p)), CSS, APP, VERSION, no, esc(p["name"]), group,
         nav_html(no), group, esc(p["fa"]), esc(p["acc"]), group, esc(p["name"]), VERSION,
         no, esc(p["name"]), esc(p["lead"]), src,
         screen_html(p), story_html(p), acts_html(p), comps,
         esc(p["flow"]), esc(p["rules"]),
         file_name(INDEX_NAME), esc(page_name(p)), target_href(nxt), esc(nxt_label),
         no, esc(page_name(p)), group, esc(p["fa"]), esc(p["acc"]),
         len(ACTS.get(no, [])), len(p["states"]), VERSION)
    )


def index_html():
    def link(no, text=None):
        return '<a href="%s">%s</a>' % (target_href(no), esc(text or no))

    def rows(pages, group):
        return "".join(
            '<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>' %
            (link(p["no"]), group, esc(p["name"]), p["tab"], esc(p["fa"]), esc(p["acc"]))
            for p in pages)

    cross = "".join("<tr><td>%s</td><td>%s</td></tr>" % (esc(a), esc(b)) for a, b in CROSS_F25)
    gacc = "".join("<tr><td>%s</td><td>%s</td><td>%s</td></tr>" %
                   (a, esc(b), esc(c)) for a, b, c in GLOBAL_ACC)
    fnums = "、".join("F%02d" % n for n in range(1, 38))
    total = len(ALL) + 1
    ia = (
        '<div class="ia"><div class="root">%s（%s）· 单一应用入口</div>'
        '<div class="lv1">├─ 前台应用工作区 · 10 页（对应 static/index.html 的 10 个 data-tab）</div>'
        '<div class="lv2">│　├─ 学习入口：%s %s</div>'
        '<div class="lv2">│　├─ AI 陪伴核心：%s %s %s %s %s</div>'
        '<div class="lv2">│　├─ 课程知识底座：%s %s（杀手功能 F06 / F33 入口）</div>'
        '<div class="lv2">│　└─ 复习闭环与辅助：%s %s %s</div>'
        '<div class="lv1">└─ 后台管理视图 · 5 页（只重组真实管理操作，不虚构登录 / 权限）</div>'
        '<div class="lv2">　　├─ 数据入口：%s %s</div>'
        '<div class="lv2">　　├─ 运行配置与看板：%s %s</div>'
        '<div class="lv2">　　└─ 任务与归档：%s %s</div></div>' %
        (APP, VERSION, link("P01"), link("P01", "学习概览"),
         link("P02"), link("P03"), link("P04"), link("P05"), link("P06"),
         link("P07"), link("P07", "课程记忆"),
         link("P08"), link("P09"), link("P10"),
         link("M01"), link("M05"), link("M02"), link("M03"), link("M04"), link("M05"))
    )
    steps = [
        ("1 进入应用", "P01", "学习概览确认课程与复习状态"),
        ("2 绑定课程资料", "P07", "把课件 / 笔记存入指定课程"),
        ("3 切课验证隔离", "P07", "切换课程，确认资料不串课"),
        ("4 发起课程内提问", "P02", "数据结构的资料拼入上下文"),
        ("5 观察反馈与回退", "P02", "忙碌态、回答卡、fallback 标记"),
        ("6 形成复习闭环", "P08", "错题分析 → 掌握 → 计划任务"),
    ]
    flow = "".join(
        '<div class="step"><b>%s</b><span>%s</span>%s</div><div class="flowarr">→</div>' %
        (esc(t), esc(d), link(p, "打开")) for t, p, d in steps)
    jump_rows = "".join(
        '<tr><td>%s</td><td>%d</td><td>%s</td></tr>' %
        (link(p["no"]), len(ACTS.get(p["no"], [])),
         "、".join(dict.fromkeys(a[3] for a in ACTS.get(p["no"], []))) or "本页反馈")
        for p in ALL)
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>%s</title>%s</head><body>'
        '<div class="hd"><b>%s</b>　<span class="bv">%s</span>　'
        '<span style="font-size:12px">P00 · 信息架构与核心使用场景（评审索引页，非功能页）</span></div>'
        '<div class="bar">页面树：%s</div>'
        '<div class="bar">本页不是 PPT 目录，而是按真实使用场景组织的页面层级与走查入口；'
        '前台 10 页与后台 5 页同处一个工程、共用同一在线预览链接。</div>'
        '<div class="w"><h2>① 信息架构与页面层级</h2>%s'
        '<h2>② 核心使用场景：从进入应用到用上 AI 陪伴</h2>'
        '<div class="flow">%s</div>'
        '<div class="hint">杀手功能走查要点：在第 2 步把资料存入「数据结构」，第 3 步切到「高等数学」确认资料不跟随，'
        '第 4 步回到「数据结构」提问，回答只引用该课程资料；无密钥时第 5 步出现演示模式与 fallback 标记。</div>'
        '<h2>③ 页面跳转关系（按页汇总，点击页号进入）</h2>'
        '<table><tr><th>页面</th><th>交互动作数</th><th>可跳转目标</th></tr>%s</table>'
        '<h2>④ 页面清单与需求索引</h2>'
        '<table><tr><th>页号</th><th>分组</th><th>页面名</th><th>标识</th><th>功能编号</th><th>验收编号</th></tr>'
        '%s%s</table>'
        '<h3>跨页功能承载矩阵（F25 / A28 语音输入）</h3>'
        '<table><tr><th>承载页</th><th>输入字段</th></tr>%s</table>'
        '<h3>全局验收项归属（A01 – A04）</h3>'
        '<table><tr><th>验收项</th><th>定义（SRS 第 6 章）</th><th>原型承载位置</th></tr>%s</table>'
        '<h3>需求编号全集与状态图例</h3>'
        '<div class="f">功能：%s<br>验收：A01 – A39（每条给出可判定条件）<br>'
        '杀手级功能：F06 / F33 课程记忆绑定、隔离与上下文预算，对应 A05 / A06 / A36。</div>'
        '<div><span class="t">默认态</span><span class="t">忙碌态（F28 / A31）</span>'
        '<span class="t">空态</span><span class="t tw">异常降级态（F30 / A33）</span>'
        '<span class="t">回退态（F23 / A26）</span><span class="t tw">校验失败态（F32 / A35）</span>'
        '<span class="tok">配置生效 / 结果态</span></div>'
        '<h3>后台管理原型边界（不额外假设）</h3>'
        '<p class="mut">作业原文要求「前台应用与后台管理原型」，未要求「独立后台站点」。M01 – M05 只重组 %s '
        '真实存在的管理操作与 REST 路由，与前台同源；不虚构登录、权限、用户管理、多租户或统计大盘。系统按单机单用户设计，暂无登录与权限。</p>'
        '<h3>版本边界（不画大饼）</h3>'
        '<p class="mut">无真实厂商 API Key，演示模式是规则化应答而非大模型推理；课程记忆为全文拼接，不是检索增强；'
        'ESP32 未实机联调（F37 不列入验收）；长文档记忆与多用户属愿景中的未来期望，不是 %s 已实现能力。</p>'
        '<div class="alert"><b>交互表达口径：</b>墨刀 HTML 导入不保留 JavaScript，'
        '在线工程用「状态分镜 + 可点击页面链接」表达交互动作与跳转；'
        '同目录 <b>交互走查版.html</b> 是浏览器可直接点击操作的本地演示版，含完整状态切换与核心流程一键走查，'
        '不调用真实接口、不产生真实数据。</div></div>'
        '<div class="ft"><b>版本标识：%s ｜ 页面 %d 张（P00 信息架构 + P01 – P10 前台 + M01 – M05 后台管理）</b><br>'
        '页面名：V1.5.0_页号_页面名(标识)；组件统一 v15- 前缀；字段与文案取自 static/index.html。<br>'
        '事实源：docs/软件需求规格说明书.md、static/index.html、server.py、version.py；生成源：gen_modao_v150.py + gen_modao_interactive.py。</div>'
        '</body></html>' %
        (INDEX_NAME, CSS, APP, VERSION, nav_html("P00"), ia, flow, jump_rows,
         rows(PAGES, "前台应用"), rows(MPAGES, "后台管理原型"), cross, gacc, fnums,
         VERSION, VERSION, VERSION, total)
    )


INTERACTIVE_HTML = r"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>V1.5.0 AI 校园学习陪伴助手 · 可交互走查版</title>
<style>
*{box-sizing:border-box}
body{font:13px/1.6 'Microsoft YaHei',Arial,sans-serif;margin:0;background:#F3F6FB;color:#1B2430}
button{font-family:inherit;cursor:pointer}
.top{background:#173E7E;color:#fff;padding:10px 18px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.top b{font-size:17px}
.top select,.top button{background:#fff;color:#173E7E;border:0;border-radius:3px;padding:5px 9px;font-size:12px}
.badge{background:#fff;color:#173E7E;border-radius:3px;padding:3px 8px;font-size:11px;font-weight:bold}
.sp{flex:1}
.wrap{display:flex;min-height:calc(100vh - 52px)}
.side{width:246px;background:#fff;border-right:1px solid #D6DFEC;padding:12px;flex:none}
.grp{font-size:11px;color:#71809A;margin:12px 0 6px;border-top:1px dashed #D6DFEC;padding-top:8px;letter-spacing:.5px}
.nav{display:block;width:100%;text-align:left;border:0;background:transparent;color:#35465F;padding:6px 9px;border-radius:4px;font-size:12px;margin:2px 0}
.nav:hover{background:#EDF3FC}
.nav.on{background:#1750A8;color:#fff}
.stepbtn{display:block;width:100%;text-align:left;border:1px solid #D6DFEC;background:#FBFCFF;color:#27436E;border-radius:4px;padding:6px 8px;font-size:11px;margin:4px 0}
.stepbtn.on{border-color:#1750A8;background:#EFF5FF;font-weight:bold}
.stepbtn.done{border-color:#1D7A43;background:#F1FAF4}
.stepbtn span{display:block;color:#71809A;font-weight:normal}
main{flex:1;padding:16px 20px;min-width:0}
.card{background:#fff;border:1px solid #D6DFEC;border-radius:6px;padding:14px;margin-bottom:12px}
h2{font-size:17px;color:#173E7E;margin:0 0 4px}h3{font-size:14px;color:#173E7E;margin:12px 0 6px}
p{color:#4C5B75;margin:5px 0}
.mut{color:#71809A;font-size:12px}
.btn{border:0;border-radius:4px;background:#1750A8;color:#fff;padding:7px 13px;font-size:12px;margin:0 6px 6px 0}
.btn:hover{background:#123E82}
.btn:disabled{background:#9CADC4;cursor:not-allowed}
.btn.ghost{background:#E7EFFA;color:#1750A8}
.btn.warn{background:#D18B00}
.btn.ok{background:#1D7A43}
input,textarea,select{border:1px solid #C6D2E3;border-radius:4px;padding:7px 9px;font-size:12px;font-family:inherit;background:#fff;color:#1B2430}
input:focus,textarea:focus,select:focus{outline:2px solid #BBD6FF;border-color:#1750A8}
textarea{width:100%;min-height:74px;resize:vertical}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin:6px 0}
.stats{display:flex;flex-wrap:wrap;gap:9px}
.stat{border:1px solid #D6DFEC;border-left:3px solid #1750A8;border-radius:4px;padding:8px 11px;min-width:118px;background:#FBFCFF}
.stat b{display:block;color:#173E7E;font-size:17px}
.stat span{font-size:11px;color:#71809A}
.list{border:1px solid #E0E6F0;border-radius:4px;background:#FBFCFF;padding:8px 10px;margin:6px 0;font-size:12px}
.list .r{display:flex;gap:8px;align-items:center;justify-content:space-between;border-bottom:1px dashed #E0E6F0;padding:5px 0}
.list .r:last-child{border-bottom:0}
.tag{display:inline-block;background:#E7EFFA;color:#1750A8;border-radius:3px;padding:2px 7px;font-size:11px;margin-right:5px}
.tag.g{background:#E5F5EC;color:#1D7A43}.tag.y{background:#FFF1D9;color:#8A5A00}
.banner{background:#FFF1D9;border:1px solid #F0D6A2;color:#7C5200;border-radius:4px;padding:8px 11px;font-size:12px;margin:8px 0}
.info{background:#EFF5FF;border:1px solid #C9DDFB;color:#27436E;border-radius:4px;padding:8px 11px;font-size:12px;margin:8px 0}
.err{background:#FDECEC;border:1px solid #F3C4C4;color:#9B2C2C;border-radius:4px;padding:8px 11px;font-size:12px;margin:8px 0}
.msg{border-left:3px solid #1750A8;background:#F8FAFD;border-radius:4px;padding:7px 10px;margin:6px 0;font-size:12px}
.msg.me{border-left-color:#1D7A43}
.msg.wait{border-left-color:#D18B00;color:#8A5A00}
.bar{height:9px;border:1px solid #D6DFEC;border-radius:5px;background:#fff;overflow:hidden}
.bar i{display:block;height:100%;background:#1750A8}
#toast{position:fixed;right:18px;bottom:18px;z-index:9;display:flex;flex-direction:column;gap:7px}
.tst{background:#173E7E;color:#fff;border-radius:4px;padding:9px 13px;font-size:12px;box-shadow:0 3px 12px #173E7E44;max-width:330px}
.tst.ok{background:#1D7A43}.tst.warn{background:#D18B00}.tst.err{background:#A73030}
.scenes{display:flex;flex-wrap:wrap;gap:7px;align-items:center}
.scene{border:1px solid #D6DFEC;border-top:3px solid #1750A8;border-radius:4px;padding:7px 9px;min-width:138px;flex:1;font-size:11px;background:#FBFCFF}
.scene b{display:block;color:#173E7E}
.scene.y{border-top-color:#D18B00;background:#FFFCF5}
.scene.g{border-top-color:#1D7A43;background:#F8FCF9}
code{background:#EEF3FB;color:#27436E;border-radius:3px;padding:1px 4px}
</style></head><body>
<div class="top">
  <b>AI 校园学习陪伴助手</b><span class="badge">V1.5.0</span>
  <span>课程：</span><select id="course"></select>
  <span class="badge" id="ctxbadge">上下文：—</span>
  <span class="badge" id="provider">Provider：demo</span>
  <span class="sp"></span>
  <button id="runflow">▶ 一键走查核心流程</button>
  <button id="reset">重置演示</button>
</div>
<div class="wrap">
<aside class="side">
  <div class="grp">核心使用场景（逐步走查）</div><div id="flownav"></div>
  <div class="grp">前台应用 · 10 页</div><div id="frontnav"></div>
  <div class="grp">后台管理 · 5 页</div><div id="adminnav"></div>
  <div class="grp">说明</div>
  <p class="mut" style="margin:0">本页为浏览器本地交互演示，所有数据与回答均为原型模拟，不调用后端、不写入真实数据库。</p>
</aside>
<main id="main"></main>
</div>
<div id="toast"></div>
<script>
var COURSES=['数据结构','高等数学','大学英语'];
var FRONT=[['dashboard','学习概览'],['chat','智能问答'],['study','学习资源包'],['summarize','课件总结'],['tutor','习题辅导'],['plan','复习计划'],['memory','课程记忆'],['wrong','错题本'],['hardware','硬件联动'],['settings','设置']];
var ADMIN=[['m01','课程与资料管理'],['m02','智能体运行配置'],['m03','运行状态与硬件看板'],['m04','复习任务与专注管理'],['m05','错题与归档管理']];
var FLOW=[['进入应用','dashboard','从学习概览确认课程与复习状态'],['绑定课程资料','memory','把课件/笔记存入指定课程'],['切课验证隔离','memory','切换课程，确认资料不跟随'],['发起课程内提问','chat','数据结构的资料拼入上下文'],['观察反馈与回退','chat','忙碌态、回答卡、fallback 标记'],['形成复习闭环','wrong','错题分析 → 掌握 → 加入任务']];
var LABEL={};FRONT.concat(ADMIN).forEach(function(x){LABEL[x[0]]=x[1]});
function blank(){
  var m={},c={};COURSES.forEach(function(x){m[x]=[];c[x]=[]});
  m['数据结构']=[{t:'第 3 章 树与二叉树',s:'先序遍历：根-左-右；中序：左-根-右；后序：左-右-根。',open:false}];
  return {course:'数据结构',tab:'dashboard',provider:'demo',materials:m,chat:c,
    tasks:[{n:'复习数据结构第 3 章',done:false}],wrong:[{q:'中序遍历二叉树的结果是什么？',mine:'根左右',right:'左根右',mastered:false}],
    focus:'空闲',busy:false,step:-1,done:[],theme:'跟随系统',lastAnswer:'',filter:'全部'};
}
var S=blank();
function $(id){return document.getElementById(id)}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function toast(msg,type){var d=document.createElement('div');d.className='tst '+(type||'');d.textContent=msg;$('toast').appendChild(d);setTimeout(function(){d.remove()},3200)}
function sleep(ms){return new Promise(function(r){setTimeout(r,ms)})}
function budget(){var n=0;S.materials[S.course].forEach(function(x){n+=x.s.length});return n}
function ctx(){var n=S.materials[S.course].length;var b=budget();$('ctxbadge').textContent='上下文：'+S.course+' · '+n+' 份 / '+b+' 字';$('provider').textContent='Provider：'+S.provider}
function renderNav(){
  $('course').innerHTML=COURSES.map(function(c){return '<option'+(c===S.course?' selected':'')+'>'+esc(c)+'</option>'}).join('');
  function build(arr,box){$(box).innerHTML=arr.map(function(x){return '<button class="nav'+(S.tab===x[0]?' on':'')+'" onclick="go(\''+x[0]+'\')">'+esc(x[1])+'</button>'}).join('')}
  build(FRONT,'frontnav');build(ADMIN,'adminnav');
  $('flownav').innerHTML=FLOW.map(function(x,i){var cls=i===S.step?' on':(S.done.indexOf(i)>=0?' done':'');return '<button class="stepbtn'+cls+'" onclick="flow('+i+')">'+(i+1)+'. '+esc(x[0])+'<span>'+esc(x[2])+'</span></button>'}).join('');
}
function go(tab){S.tab=tab;render()}
function setCourse(c){S.course=c;S.chat[c]=S.chat[c]||[];ctx();render();toast('已切换到「'+c+'」，课程记忆与对话已隔离','ok')}
function head(title,sub,extra){return '<div class="card"><h2>'+esc(title)+'</h2><p class="mut">'+esc(sub)+'</p>'+(extra||'')+'</div>'}
function render(){
  renderNav();ctx();
  var f={dashboard:vDashboard,chat:vChat,study:vStudy,summarize:vSummarize,tutor:vTutor,plan:vPlan,memory:vMemory,wrong:vWrong,hardware:vHardware,settings:vSettings,m01:vM01,m02:vM02,m03:vM03,m04:vM04,m05:vM05};
  $('main').innerHTML=(f[S.tab]||vDashboard)();
}
function scenes(arr){return '<div class="scenes">'+arr.map(function(x,i){return (i?'<span class="flowarr">→</span>':'')+'<div class="scene '+(x[2]||'')+'"><b>'+esc(x[0])+'</b><span>'+esc(x[1])+'</span></div>'}).join('')+'</div>'}
function vDashboard(){var t=S.tasks.filter(function(x){return !x.done}).length;var m=S.materials[S.course].length;
  return head('学习概览','一屏聚合当前课程的复习状态；统计与任务随课程切换刷新。')+
  '<div class="card"><h3>六项统计</h3><div class="stats"><div class="stat"><b>'+COURSES.length+'</b><span>课程数</span></div><div class="stat"><b>'+m+'</b><span>本科程资料</span></div><div class="stat"><b>'+S.wrong.length+'</b><span>错题</span></div><div class="stat"><b>'+t+'</b><span>待复习任务</span></div><div class="stat"><b>'+(S.wrong.length?Math.round(S.wrong.filter(function(x){return x.mastered}).length/S.wrong.length*100)+'%':'暂无')+'</b><span>错题掌握率</span></div><div class="stat"><b>'+(S.focus==='专注中'?'25:00':'50 分')+'</b><span>今日专注</span></div></div></div>'+
  '<div class="card"><h3>待复习任务</h3><div class="row"><input id="taskname" style="width:270px" placeholder="任务名，如：复习数据结构第 3 章"><button class="btn" onclick="addTask()">添加</button><button class="btn ghost" onclick="go(\'plan\')">生成计划</button></div>'+
  '<div class="list">'+(S.tasks.length?S.tasks.map(function(x,i){return '<div class="r"><span>'+esc(x.n)+' <span class="tag '+(x.done?'g':'y')+'">'+(x.done?'已完成':'待复习')+'</span></span><button class="btn ghost" onclick="doneTask('+i+')">完成</button></div>'}).join(''):'暂无复习任务')+'</div></div>'+
  '<div class="card"><h3>番茄钟</h3><p>状态：<span class="tag '+(S.focus==='专注中'?'g':'y')+'">'+S.focus+'</span></p><button class="btn" onclick="startFocus()">开始专注 25:00</button><button class="btn ghost" onclick="go(\'hardware\')">查看硬件看板</button>'+
  scenes([['默认态','统计与任务有值'],['键盘焦点态','统计卡片可 Tab / Enter 激活'],['空态','无错题显示「暂无」而非 0.0%','y'],['异常降级态','单接口失败逐模块提示','y']])+'</div>';
}
function addTask(){var v=$('taskname').value.trim()||'未命名复习任务';S.tasks.push({n:v,done:false});toast('已添加任务：'+v,'ok');render()}
function doneTask(i){S.tasks[i].done=true;toast('任务已标记完成','ok');render()}
function startFocus(){S.focus='专注中';toast('番茄钟已启动：25:00','ok');render()}
function vChat(){
  var log=S.chat[S.course]||[];var m=S.materials[S.course].length;
  return head('智能问答 · 课程内陪伴','杀手功能 F06 / F33 的界面入口：切换课程即切换课程记忆。')+
  (S.provider==='demo'?'<div class="banner">演示模式：未配置密钥，回答由内置规则生成（fallback），不是真实大模型推理。<button class="btn ghost" onclick="go(\'settings\')">去配置</button></div>':'')+
  '<div class="card"><h3>对话区 · '+esc(S.course)+'</h3><div class="info">当前上下文：本科程 '+m+' 份资料，单份上限 4000 字、总量 12000 字；全文拼接，不是检索增强。</div>'+
  (log.length?log.map(function(x){return '<div class="msg '+(x.me?'me':'')+'"><b>'+(x.me?'学生':'助手')+'：</b>'+x.t+(x.fb?' <span class="tag y">fallback</span>':'')+'</div>'}).join(''):'<p class="mut">对话区为空，输入一个课程问题开始。</p>')+
  '<div class="row"><textarea id="q" style="flex:1" placeholder="输入课程问题，或点语音按钮…">请概括第 3 章树的遍历</textarea></div>'+
  '<div class="row"><button class="btn" id="send" onclick="send()"'+(S.busy?' disabled':'')+'>'+(S.busy?'思考中…':'发送')+'</button><button class="btn ghost" onclick="mic(\'q\')">🎤 语音</button><button class="btn ghost" onclick="go(\'memory\')">查看依据资料</button><button class="btn warn" onclick="switchDemo()">切课验证隔离</button></div>'+
  scenes([['默认态','输入框可用、对话区为空'],['忙碌态','发送按钮禁用并显示「思考中…」','y'],['结果态','安全渲染回答卡 + fallback 标记','g'],['切课程态','对话清空、上下文按课程重建']])+'</div>';
}
async function send(){
  if(S.busy)return;var q=$('q').value.trim();if(!q){toast('请输入问题','warn');return}
  S.busy=true;render();await sleep(850);
  var m=S.materials[S.course];var ans;
  if(m.length){var src=m[0].t;ans='依据「'+esc(src)+'」：'+esc(m[0].s)+'（本科程共 '+m.length+' 份资料已进入上下文）'}
  else{ans='当前课程「'+esc(S.course)+'」暂无课程记忆资料，无法给出基于资料的回答；可先到课程记忆上传资料。'}
  S.chat[S.course].push({me:true,t:esc(q)});S.chat[S.course].push({me:false,t:ans,fb:S.provider==='demo'});
  S.lastAnswer=ans;S.busy=false;render();toast('回答已生成（演示模式规则化应答）','ok');
}
function switchDemo(){var next=COURSES[(COURSES.indexOf(S.course)+1)%COURSES.length];setCourse(next);toast('旧课程回答未跨课程出现，隔离验证通过','ok')}
function mic(id){toast('语音输入态：识别结果回填输入框（原型模拟）');var el=$(id);if(el&&!el.value)el.value='请概括本章重点';render()}
function vStudy(){
  return head('学习资源包','按教材 / 章节 / 题量 / 难度生成五件套，可回写课程记忆并导出。')+
  '<div class="card"><div class="row"><input id="sub" style="width:210px" value="高等数学上册" placeholder="学科，如：数学 / 高等数学上册"><input id="chap" style="width:150px" placeholder="章节"><input id="num" style="width:90px" value="10" placeholder="题量"><input id="lv" style="width:90px" value="中等" placeholder="难度"></div>'+
  '<div class="row"><button class="btn" onclick="genPack()">一键全套</button><button class="btn ghost" onclick="genOne(\'题目\')">自测题</button><button class="btn ghost" onclick="genOne(\'总结\')">总结</button><button class="btn ghost" onclick="genOne(\'专题文章\')">文章</button><button class="btn ghost" onclick="genOne(\'资料清单\')">资料</button><button class="btn ghost" onclick="genOne(\'思维导图\')">思维导图</button><button class="btn ghost" onclick="download(\'资源包.md\',\'# 学习资源包\\n五件套演示内容\')">导出 Markdown</button></div>'+
  '<div id="pack"></div>'+scenes([['默认态','参数可编辑、五区待生成'],['忙碌态','5 个按钮同时禁用','y'],['结果态','五区分别填充','g'],['部分失败态','双请求独立判错','y']])+'</div>';
}
async function genPack(){toast('一键全套开始，5 个生成按钮禁用');await sleep(700);$('pack').innerHTML=['题目','总结','专题文章','资料清单','思维导图'].map(function(k){return '<div class="list"><b>'+k+'</b>　已生成（含标准答案 / 分步解析 / 考点）<button class="btn ghost" onclick="go(\'memory\')">存入课程记忆</button></div>'}).join('');toast('五件套已生成','ok')}
function genOne(k){toast(k+'生成中（按钮禁用）');setTimeout(function(){var d=$('pack');d.innerHTML=d.innerHTML+'<div class="list"><b>'+k+'</b>　已生成</div>';toast(k+'已生成','ok')},600)}
function vSummarize(){return head('课件总结','粘贴课件或笔记，输出关键知识点与复习考点提纲。')+'<div class="card"><textarea id="sum" placeholder="在此粘贴课件或笔记文字…"></textarea><div class="row"><button class="btn" onclick="mkResult(\'sumresult\',\'关键知识点 / 复习考点提纲\')">生成总结</button><button class="btn ghost" onclick="mic(\'sum\')">🎤 语音</button></div><div id="sumresult"></div>'+scenes([['默认态','文本框为空可输入'],['忙碌态','按钮禁用并显示生成中','y'],['结果态','安全 Markdown 排版','g'],['空值拦截态','空内容不发起请求','y']])+'</div>'}
function vTutor(){return head('习题辅导','引导式辅导：给分步思路与提示，不直接给最终答案。')+'<div class="card"><textarea id="tut" placeholder="在此粘贴题目…"></textarea><div class="row"><button class="btn" onclick="mkResult(\'tutresult\',\'分步思路 ① … ② …｜提示：先画出树的形状，再判断遍历次序\')">辅导一下</button><button class="btn ghost" onclick="mic(\'tut\')">🎤 语音</button><button class="btn ghost" onclick="go(\'wrong\')">记入错题本</button></div><div id="tutresult"></div>'+scenes([['默认态','题目输入区可用'],['忙碌态','按钮禁用','y'],['结果态','分步思路 + 提示','g']])+'</div>'}
function mkResult(id,text){var el=$(id);if(!el)return;el.innerHTML='<div class="info">生成中…</div>';setTimeout(function(){el.innerHTML='<div class="list">'+esc(text)+'</div>'},650)}
function vPlan(){return head('复习计划','按科目与天数生成逐日复习安排，并可加入复习任务。')+'<div class="card"><div class="row"><input id="ps" style="width:210px" value="数据结构" placeholder="考试科目"><input id="pd" style="width:90px" value="7" placeholder="天数"><button class="btn" onclick="genPlan()">生成计划</button></div><div id="planr"></div>'+scenes([['默认态','科目与天数待填'],['忙碌态','按钮禁用','y'],['结果态','逐日安排可 30 秒扫描','g']])+'</div>'}
function genPlan(){var n=parseInt($('pd').value)||7;var s=$('ps').value||'数据结构';var h='';for(var i=1;i<=n;i++)h+='<div class="list"><b>第 '+i+' 天</b>　'+esc(s)+'：复习要点与自测<button class="btn ghost" onclick="planTask(\''+esc(s)+' 第'+i+'天\')">加入任务</button></div>';$('planr').innerHTML=h;toast('已生成 '+n+' 天计划','ok')}
function planTask(n){S.tasks.push({n:n,done:false});toast('已加入复习任务：'+n,'ok');render()}
function vMemory(){var list=S.materials[S.course]||[];var b=budget();
  return head('课程记忆 · '+S.course,'杀手功能 F06 / F33 的数据入口：资料按课程隔离，全文拼入问答上下文。')+
  '<div class="card"><div class="row"><input id="mt" style="width:230px" placeholder="资料标题（可选）"><button class="btn ghost" onclick="fakeFile()">选择文件 .txt/.md/.docx</button><button class="btn" onclick="saveMat()">保存资料</button></div>'+
  '<textarea id="mc" placeholder="粘贴本课程课件、笔记、重点…"></textarea>'+
  '<div class="row"><button class="btn ghost" onclick="mic(\'mc\')">🎤 语音</button><span class="mut">单份 ≤ 4000 字；总量 ≤ 12000 字</span></div>'+
  '<p class="mut">上下文预算：'+b+' / 12000 字</p><div class="bar"><i style="width:'+Math.min(100,b/120)+'%"></i></div>'+
  '<h3>已上传资料（'+list.length+'）</h3><div class="list">'+(list.length?list.map(function(x,i){return '<div class="r"><span><b>'+esc(x.t)+'</b> '+(x.open?'<span class="tag g">全文展开</span>':'')+'</span><span><button class="btn ghost" onclick="toggleMat('+i+')">'+(x.open?'收起':'查看全文')+'</button><button class="btn ghost" onclick="download(\''+esc(x.t)+'.md\',\''+esc(x.s)+'\')">下载 .md</button><button class="btn" onclick="useMat('+i+')">用于问答</button></span></div>'+(x.open?'<div class="msg">'+esc(x.s)+'</div>':'')}).join(''):'暂无资料')+'</div>'+
  scenes([['默认态','显示真实资料'],['上传中态','按钮禁用与进度提示','y'],['展开态','全文安全渲染 / 收起','g'],['校验失败态','类型或大小不合规逐项提示','y'],['隔离态','切课程后资料不跟随']])+'</div>';
}
function fakeFile(){toast('文件选择：已模拟读取 .md 文件（≤2 MB / ≤2 万字校验通过）');var m=$('mc');if(m&&!m.value)m.value='文件正文：本章重点与例题解析。'}
function saveMat(){var t=$('mt').value.trim()||'未命名资料';var s=$('mc').value.trim();if(!s){toast('正文必填，请粘贴内容','warn');return}S.materials[S.course].push({t:t,s:s,open:false});toast('已保存到「'+S.course+'」的课程记忆，问答上下文已更新','ok');render()}
function toggleMat(i){S.materials[S.course][i].open=!S.materials[S.course][i].open;render()}
function useMat(i){toast('已带「'+S.materials[S.course][i].t+'」进入问答上下文');go('chat')}
function download(name,text){var b=new Blob([text],{type:'text/markdown;charset=utf-8'});var a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=name;a.click();URL.revokeObjectURL(a.href);toast('已触发下载：'+name,'ok')}
function vWrong(){var list=S.wrong;
  return head('错题本','录入 → 错因分析 + 变式题 → 标记掌握 → 筛选 → 导出，形成复习闭环。')+
  '<div class="card"><div class="row"><input id="wq" style="width:300px" placeholder="错题题目"><input id="wu" style="width:160px" placeholder="我的答案（可选）"><input id="wc" style="width:160px" placeholder="正确答案（可选）"><button class="btn" onclick="addWrong()">录入</button><button class="btn ghost" onclick="mic(\'wq\')">🎤 语音</button></div>'+
  '<div class="row"><span class="mut">筛选：</span><select id="wf" onchange="S.filter=this.value;render()">'+['全部','未掌握','已掌握'].map(function(f){return '<option'+(S.filter===f?' selected':'')+'>'+f+'</option>'}).join('')+'</select><button class="btn ghost" onclick="download(\'错题归档.md\',\'# 错题归档\')">导出 Markdown</button></div>'+
  '<div class="list">'+(list.length?list.filter(function(x){return S.filter==='全部'||(S.filter==='已掌握')===x.mastered}).map(function(x,i){return '<div class="r"><span>'+esc(x.q)+' <span class="tag '+(x.mastered?'g':'y')+'">'+(x.mastered?'已掌握':'未掌握')+'</span></span><span><button class="btn ghost" onclick="toast(\'错因分析 + 变式题已展开\')">错因/变式</button><button class="btn ok" onclick="master('+i+')">标记掌握</button></span></div>'}).join(''):'暂无错题')+'</div>'+
  scenes([['默认态','错题列表有值'],['忙碌态','分析与导出按钮禁用','y'],['结果态','变式题展开','g'],['空态','筛选无结果不显示 0.0%','y']])+'</div>';
}
function addWrong(){var q=$('wq').value.trim();if(!q){toast('题干必填','warn');return}S.wrong.push({q:q,mine:$('wu').value,right:$('wc').value,mastered:false});toast('错题已录入','ok');render()}
function master(i){S.wrong[i].mastered=true;toast('已标记掌握，掌握率已刷新','ok');render()}
function vHardware(){return head('硬件联动（可选，不列入验收）','ESP32 接口清单与状态看板；未实机联调，不宣称物理效果已验证。')+
  '<div class="card"><div class="row"><input id="hw" style="width:260px" placeholder="复习任务名，如：复习第3章"><button class="btn" onclick="planTask(\'硬件提醒任务\')">创建任务</button><button class="btn warn" onclick="hwTest()">测试提醒</button><button class="btn ghost" onclick="toast(\'专注灯下发状态已返回\')">专注灯</button></div>'+
  '<div class="list">6 点硬件交互清单：到点提醒｜手动提醒｜番茄钟提醒｜专注灯｜状态看板｜通用下发</div><div id="hwres"></div>'+
  '<div class="banner">未配置 ESP32_ENDPOINT：sent=false（未实机联调），主体功能不受影响。</div>'+
  scenes([['默认态','清单表与看板可见'],['未配置态','sent=false 与原因','y'],['边界声明态','不冒充实物验证','y']])+'</div>'}
function hwTest(){$('hwres').innerHTML='<div class="err">测试提醒：sent=false，原因：ESP32_ENDPOINT 未配置。功能流程继续。</div>';toast('已返回 sent=false 与原因','warn')}
function vSettings(){return head('设置','主题三档 + 六类 Provider 运行时配置；无密钥自动回退演示模式。')+
  '<div class="card"><div class="row"><span class="mut">主题：</span><select id="th" onchange="S.theme=this.value;toast(\'主题已切换并本地持久化\')"><option>跟随系统</option><option>浅色</option><option>深色</option></select><span class="tag">6 套预设色</span></div>'+
  '<div class="row"><span class="mut">Provider：</span><select id="pv" onchange="S.provider=this.value;ctx();render()"><option>demo</option><option>OpenAI</option><option>文心一言</option><option>Kimi</option><option>Claude</option><option>自定义</option></select></div>'+
  '<div class="row"><input style="width:230px" type="password" placeholder="agentKey：必填，如 sk-…"><input style="width:180px" placeholder="agentModel（可留空）"><input style="width:200px" placeholder="agentBaseUrl（可选）"></div>'+
  '<div class="row"><button class="btn" onclick="toast(\'配置已保存：运行时即时生效，状态只回掩码\',\'ok\')">保存</button><button class="btn ghost" onclick="toast(\'连通性自检：探针结果已返回\')">连通性自检</button><button class="btn warn" onclick="clearCfg()">清除配置</button></div>'+
  '<div class="list">Provider 状态卡：OpenAI｜文心一言｜Kimi｜Claude｜自定义｜演示模式 '+(S.provider==='demo'?'<span class="tag g">当前激活</span>':'')+'</div>'+
  scenes([['默认态','演示模式激活'],['配置生效态','运行时写入即时生效','g'],['自检态','探针校验并提示结果'],['回退态','清除或异常后回退 demo','y'],['掩码态','只回密钥掩码']])+'</div>'}
function clearCfg(){S.provider='demo';ctx();render();toast('配置已清除，自动回退演示模式','warn')}
function vM01(){return head('后台管理 · 课程与资料管理','只重组真实管理操作：新建课程、资料入库、查看全文与下载；不虚构权限。')+
  '<div class="card"><div class="row"><input id="nc" style="width:200px" placeholder="新课程名"><button class="btn" onclick="addCourse()">新建课程</button></div>'+
  '<div class="list">课程：'+COURSES.map(function(c){return '<span class="tag '+(c===S.course?'g':'')+'">'+esc(c)+'</span>'}).join('')+'</div>'+
  '<p>当前课程资料 '+S.materials[S.course].length+' 份；'+(S.materials[S.course].length?esc(S.materials[S.course][0].t):'暂无')+'</p>'+
  '<div class="row"><button class="btn" onclick="go(\'memory\')">资料入库 / 查看全文</button><button class="btn ghost" onclick="toast(\'已拦截：课程不存在，400\',\'warn\')">模拟孤儿数据写入</button></div>'+
  scenes([['默认态','课程与资料列表有值'],['校验失败态','空课程名 / 不存在课程返回 400','y'],['隔离态','资料按课程落库，不串课','g']])+'</div>'}
function addCourse(){var n=$('nc').value.trim();if(!n){toast('课程名不可为空（400）','warn');return}if(COURSES.indexOf(n)>=0){toast('课程名重复（400）','warn');return}COURSES.push(n);S.materials[n]=[];S.chat[n]=[];toast('课程已创建：'+n,'ok');render()}
function vM02(){return head('后台管理 · 智能体运行配置','6 类 Provider 凭据与激活项；密钥只回掩码，自检不切换失败项。')+
  '<div class="card"><div class="list">当前激活：'+esc(S.provider)+'　｜　状态：'+(S.provider==='demo'?'规则化演示应答（fallback）':'按配置调用')+'</div>'+
  '<div class="row"><button class="btn" onclick="go(\'settings\')">打开配置表单</button><button class="btn ghost" onclick="toast(\'自检探针已返回可用/不可用\')">连通性自检</button></div>'+
  '<div class="banner">配置优先级：运行时 SQLite ＞ .env ＞ demo；本项目无真实厂商密钥。</div>'+
  scenes([['默认态','demo 激活'],['配置生效态','写入即生效','g'],['自检态','探针返回结果'],['回退态','清除后回退 demo','y'],['掩码态','密钥只回掩码']])+'</div>'}
function vM03(){return head('后台管理 · 运行状态与硬件看板','版本指纹来自 version.py；动态接口 no-store，避免页面新、接口旧。')+
  '<div class="card"><div class="stats"><div class="stat"><b>1.5.0</b><span>version</span></div><div class="stat"><b>'+esc(S.provider)+'</b><span>active_provider</span></div><div class="stat"><b>'+S.tasks.filter(function(x){return !x.done}).length+'</b><span>待复习</span></div><div class="stat"><b>'+S.wrong.filter(function(x){return !x.mastered}).length+'</b><span>待掌握</span></div><div class="stat"><b>25 分</b><span>专注</span></div></div>'+
  '<div class="row"><button class="btn warn" onclick="go(\'hardware\')">测试硬件提醒</button><button class="btn ghost" onclick="go(\'dashboard\')">查看学习概览</button></div>'+
  scenes([['默认态','看板与清单可见'],['未配置态','sent=false 与原因','y'],['边界声明态','未实机联调','y']])+'</div>'}
function vM04(){return head('后台管理 · 复习任务与专注管理','待复习任务、到点提醒、逐日计划与专注记录。')+
  '<div class="card"><div class="row"><input id="mtask" style="width:250px" placeholder="任务名"><button class="btn" onclick="addTask2()">添加</button><button class="btn ghost" onclick="go(\'plan\')">生成计划</button></div>'+
  '<div class="list">'+(S.tasks.length?S.tasks.map(function(x,i){return '<div class="r"><span>'+esc(x.n)+' <span class="tag '+(x.done?'g':'y')+'">'+(x.done?'已完成':'待复习')+'</span></span><button class="btn ghost" onclick="doneTask('+i+')">标记完成</button></div>'}).join(''):'暂无任务')+'</div><p class="mut">后台守护线程每 30 秒扫描到期任务；空任务名回落默认名。</p>'+
  scenes([['默认态','任务与计划有值'],['空态','无任务显示「暂无」','y'],['提醒态','到期任务触发提醒'],['降级态','单接口失败逐模块提示','y']])+'</div>'}
function addTask2(){var v=$('mtask').value.trim()||'未命名复习任务';S.tasks.push({n:v,done:false});toast('任务已添加','ok');render()}
function vM05(){return head('后台管理 · 错题与归档管理','错题筛选、掌握状态与 Markdown 归档导出。')+
  '<div class="card"><div class="row"><button class="btn ghost" onclick="go(\'wrong\')">录入 / 分析错题</button><button class="btn" onclick="download(\'错题归档.md\',\'# 错题归档\\n演示内容\')">导出归档</button></div>'+
  '<div class="list">未掌握 '+S.wrong.filter(function(x){return !x.mastered}).length+' 条；已掌握 '+S.wrong.filter(function(x){return x.mastered}).length+' 条</div>'+
  scenes([['默认态','错题列表有值'],['空态','筛选无结果显示空态','y'],['归档态','blob 下载，失败只提示','g']])+'</div>'}
async function flow(i){
  S.step=i;if(S.done.indexOf(i)<0)S.done.push(i);
  if(i===0){go('dashboard');toast('第 1 步：进入应用，确认课程与复习状态')}
  if(i===1){go('memory');toast('第 2 步：在课程记忆保存一份资料（已预填并保存）');setTimeout(function(){var t=$('mt'),c=$('mc');if(t&&c){t.value='走查示例：树的遍历';c.value='先序：根-左-右；中序：左-根-右；后序：左-右-根。';saveMat()}},80)}
  if(i===2){setCourse('高等数学');toast('第 3 步：已切课，高等数学下无该资料，隔离验证通过','ok')}
  if(i===3){setCourse('数据结构');go('chat');toast('第 4 步：回到数据结构，资料已重新拼入上下文','ok')}
  if(i===4){go('chat');toast('第 5 步：点击「发送」观察忙碌态 → 回答卡 → fallback 标记')}
  if(i===5){go('wrong');toast('第 6 步：标记掌握 → 生成计划 → 加入复习任务，闭环完成','ok')}
  render();
}
async function runflow(){
  S=blank();render();for(var i=0;i<FLOW.length;i++){
    await flow(i);await sleep(i===3?1200:800);
    if(i===3&&$('q')){await send();await sleep(900)}
  }
  toast('核心流程走查完成：进入 → 绑定 → 隔离 → 提问 → 反馈 → 闭环','ok');
}
function resetAll(){S=blank();render();toast('演示状态已重置')}
document.addEventListener('DOMContentLoaded',function(){$('runflow').onclick=runflow;$('reset').onclick=resetAll;$('course').onchange=function(){setCourse(this.value)};render()});
</script></body></html>
"""


CSS_MINI = """<style>body{font:13px 'Microsoft YaHei',Arial,sans-serif;margin:0;background:#F4F7FC;color:#1B2430}a{color:#1750A8;text-decoration:none}.hd{background:#173E7E;color:#fff;padding:9px 16px}.bv{background:#fff;color:#173E7E;padding:2px 6px;border-radius:3px}.bar{background:#E7EFFA;padding:6px 16px;font-size:12px}.w{margin:10px 16px;background:#fff;border:1px solid #D5DEEC;border-radius:5px;padding:11px}h2,h3{color:#173E7E;margin:8px 0}h2{font-size:16px}h3{font-size:13px}table{width:100%;border-collapse:collapse;font-size:12px}th,td{border:1px solid #DCE3EE;padding:5px}th{background:#EEF3FB}.screen{border:1px solid #D5DEEC;border-radius:4px;background:#fff;margin:7px 0}.s-top{background:#173E7E;color:#fff;padding:6px 10px;font-size:12px}.s-body{display:flex}.s-side{width:132px;background:#F0F4FB;padding:7px;font-size:11px;line-height:1.7}.s-side span{display:block}.s-side .on{background:#1750A8;color:#fff;padding:0 4px}.s-main{flex:1;padding:8px}.s-h{color:#173E7E;font-weight:bold}.fw-in,.fw-ta,.fw-list{display:block;border:1px solid #C4D3E8;background:#F8FAFD;border-radius:3px;padding:4px 6px;margin:4px 0;font-size:11px;color:#60708C}.fw-in{display:inline-block}.fw-btn{display:inline-block;background:#1750A8;color:#fff;border-radius:3px;padding:4px 8px;margin:0 4px 4px 0;font-size:11px}.fw-btn.gray{background:#8FA2BE}.fw-card{display:inline-block;border:1px solid #DCE3EE;border-left:3px solid #1750A8;padding:4px 7px;margin:0 4px 4px 0;font-size:11px}.fw-tag{background:#E7EFFA;color:#1750A8;padding:2px 5px;font-size:11px}.fw-warn{background:#FFF1D9;color:#8A5A00;padding:4px 6px;font-size:11px}.story{display:flex;flex-wrap:wrap;gap:5px;align-items:center}.scene{border:1px solid #D5DEEC;border-top:3px solid #1750A8;border-radius:4px;background:#fff;padding:6px 8px;min-width:120px;flex:1;font-size:11px}.scene.y{border-top-color:#D18B00;background:#FFFCF5}.scene.g{border-top-color:#1D7A43;background:#F8FCF9}.scene b{display:block;color:#173E7E}.arrow{color:#8FA2BE;font-size:16px}.mut{color:#71809A;font-size:11px}.hint{background:#EFF5FF;border-left:4px solid #1750A8;padding:7px 9px;font-size:11px;margin:7px 0}</style>"""


def compact_page_html(p):
    """墨刀导入载荷：保留界面、状态分镜、交互动作与跳转，字段细节放本地同源页与文档。"""
    jump = "、".join(sorted(set(a[3] for a in ACTS.get(p["no"], [])))) or "本页状态反馈"
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>%s</title>%s</head><body>'
        '<div class="hd"><b>%s</b>　<span class="bv">%s</span>　%s %s · %s</div>'
        '<div class="bar">分组：%s　｜　功能：%s　｜　验收：%s　｜　交互动作：%d 条　｜　可跳转：%s</div>'
        '<div class="w"><h2>%s %s · 应用界面与交互分镜</h2><p class="mut">%s</p>'
        '<h3>① 应用界面（真实字段与文案）</h3>%s'
        '<h3>② 状态切换分镜（左 → 右）</h3>%s'
        '<h3>③ 交互动作 → 状态反馈 → 页面跳转</h3>%s'
        '<div class="hint">点击「跳转页」列可进入目标页；浏览器本地点击演示见同目录「交互走查版.html」。</div>'
        '<h3>④ 业务流程</h3><p class="mut">%s</p></div>'
        '<div class="bar">%s ｜ 单一源：gen_modao_v150.py + gen_modao_interactive.py ｜ 完整字段 / 组件表见本地同源 HTML 与《原型需求核对表.md》</div>'
        '</body></html>' %
        (esc(page_name(p)), CSS_MINI, APP, VERSION, p["no"], esc(p["name"]), VERSION,
         group_of(p), esc(p["fa"]), esc(p["acc"]), len(ACTS.get(p["no"], [])), esc(jump),
         p["no"], esc(p["name"]), esc(p["lead"]),
         screen_html(p), story_html(p), acts_html(p), esc(p["flow"]), VERSION)
    )


def compact_index_html():
    """墨刀导入载荷首页：信息架构 + 六步核心场景 + 页面跳转入口。"""
    def link(no, text=None):
        return '<a href="%s">%s</a>' % (target_href(no), esc(text or no))

    steps = [("1 进入应用", "P01", "学习概览确认课程与状态"),
             ("2 绑定课程资料", "P07", "把课件 / 笔记存入指定课程"),
             ("3 切课验证隔离", "P07", "切课后资料不跟随"),
             ("4 发起课程内提问", "P02", "资料全文拼入上下文"),
             ("5 观察反馈与回退", "P02", "忙碌态、回答卡、fallback"),
             ("6 形成复习闭环", "P08", "错题分析 → 掌握 → 任务")]
    flow = "".join('<div class="scene"><b>%s</b><span>%s</span>%s</div><span class="arrow">→</span>' %
                   (esc(t), esc(d), link(p, "打开")) for t, p, d in steps)
    ia = (
        '<div style="border:1px solid #D5DEEC;border-radius:4px;padding:10px;background:#FBFCFF">'
        '<b style="color:#173E7E">%s（%s）</b>'
        '<p>├─ 前台应用工作区（10 页）：学习入口 %s；AI 陪伴核心 %s %s %s %s %s；'
        '课程知识底座 %s（杀手功能 F06 / F33）；闭环与辅助 %s %s %s。</p>'
        '<p>└─ 后台管理视图（5 页）：数据入口 %s %s；运行配置与看板 %s %s；任务与归档 %s %s。</p>'
        '</div>' %
        (APP, VERSION, link("P01"), link("P02"), link("P03"), link("P04"), link("P05"), link("P06"),
         link("P07"), link("P08"), link("P09"), link("P10"),
         link("M01"), link("M05"), link("M02"), link("M03"), link("M04"), link("M05"))
    )
    plist = "".join('<span class="fw-tag">%s %s</span>' % (p["no"], link(p["no"], esc(p["name"]))) for p in ALL)
    return (
        '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>%s</title>%s</head><body>'
        '<div class="hd"><b>%s</b>　<span class="bv">%s</span>　P00 信息架构与核心使用场景</div>'
        '<div class="bar">本页不是 PPT 目录：按真实使用场景组织页面层级与走查入口；前台 10 页 + 后台 5 页同处一个工程。</div>'
        '<div class="w"><h2>① 信息架构与页面层级</h2>%s'
        '<h2>② 核心使用场景：从进入应用到用上 AI 陪伴</h2><div class="story">%s</div>'
        '<div class="hint">走查要点：先在课程记忆保存资料 → 切到高等数学确认资料不跟随 → 回到数据结构提问，'
        '回答只引用本科程资料；无密钥时出现演示模式与 fallback 标记。</div>'
        '<h2>③ 全部页面（点击直达）</h2><div>%s</div>'
        '<h3>版本边界</h3><p class="mut">演示模式是规则化应答，不是真实大模型推理；课程记忆为全文拼接，不是检索增强；'
        'ESP32 未实机联调（F37 不列入验收）；单机单用户，无登录与权限。功能 F01 – F37，验收 A01 – A39。</p>'
        '<div class="hint">在线工程用状态分镜 + 页面链接表达交互；浏览器点击演示见同目录「交互走查版.html」。</div></div>'
        '<div class="bar">%s ｜ 生成源：gen_modao_v150.py + gen_modao_interactive.py ｜ 完整需求核对见《原型需求核对表.md》</div>'
        '</body></html>' %
        (INDEX_NAME, CSS_MINI, APP, VERSION, ia, flow, plist, VERSION)
    )


def build():
    os.makedirs(OUT, exist_ok=True)
    items = [{"name": INDEX_NAME, "html": index_html()}]
    for p in ALL:
        items.append({"name": page_name(p), "html": page_html(p)})
    for it in items:
        path = os.path.join(OUT, file_name(it["name"]))
        io.open(path, "w", encoding="utf-8").write(it["html"])
        for bad in OLD_TERMS:
            assert bad not in it["html"], "旧版口径污染 %s: %s" % (it["name"], bad)
        assert VERSION in it["html"], "缺版本标识 " + it["name"]
        assert '<a href=' in it["html"], "缺页面互链 " + it["name"]
        assert '交互动作' in it["html"] or it["name"] == INDEX_NAME, "缺交互动作 " + it["name"]
        assert '状态切换分镜' in it["html"] or it["name"] == INDEX_NAME, "缺状态分镜 " + it["name"]
    interactive_path = os.path.join(OUT, "交互走查版.html")
    io.open(interactive_path, "w", encoding="utf-8").write(INTERACTIVE_HTML)
    assert "一键走查核心流程" in INTERACTIVE_HTML
    assert "切课验证隔离" in INTERACTIVE_HTML
    # 墨刀导入载荷用交互精简版：保留信息架构、界面、状态分镜、交互动作与跳转，
    # 字段细节仍由本地同源 HTML 与核对表承载；精简后导入更稳定。
    import_items = [{"name": INDEX_NAME, "html": compact_index_html()}]
    for p in ALL:
        import_items.append({"name": page_name(p), "html": compact_page_html(p)})
    for bad in OLD_TERMS:
        for it in import_items:
            assert bad not in it["html"], "旧版口径污染导入载荷 %s: %s" % (it["name"], bad)
    io.open(os.path.join(OUT, "html_list.json"), "w", encoding="utf-8").write(
        json.dumps(import_items, ensure_ascii=False, separators=(",", ":")))
    io.open(os.path.join(OUT, "html_list_full.json"), "w", encoding="utf-8").write(
        json.dumps(items, ensure_ascii=False, separators=(",", ":")))

    lines = ["# V1.5.0 墨刀原型 · 需求项与交互核对表", "",
             "> 事实源：`docs/软件需求规格说明书.md`、`static/index.html`、`server.py`、`version.py`；"
             "生成源：`gen_modao_v150.py`（数据）+ `gen_modao_interactive.py`（渲染）。", "",
             "> 交互表达：墨刀 HTML 导入不保留脚本，在线工程以「状态分镜 + 可点击页面链接」表达；"
             "`modao_v150/交互走查版.html` 提供浏览器本地真实点击与状态切换演示。", "",
             "## 1 前台应用原型（P01 – P10）", "",
             "| 页号 | 页面名 | 标识 | 功能编号 | 验收编号 | 关键状态 | 交互动作数 |",
             "|---|---|---|---|---|---|---|"]
    for p in PAGES:
        lines.append("| %s | %s | %s | %s | %s | %s | %d |" %
                     (p["no"], p["name"], p["tab"], p["fa"], p["acc"],
                      " / ".join(s[0] for s in p["states"]), len(ACTS.get(p["no"], []))))
    lines += ["", "## 2 后台管理原型（M01 – M05）", "",
              "| 页号 | 页面名 | 标识 | 真实承载位置 | 功能编号 | 验收编号 | 关键状态 | 交互动作数 |",
              "|---|---|---|---|---|---|---|---|"]
    for p in MPAGES:
        lines.append("| %s | %s | %s | %s | %s | %s | %s | %d |" %
                     (p["no"], p["name"], p["tab"], p["src"], p["fa"], p["acc"],
                      " / ".join(s[0] for s in p["states"]), len(ACTS.get(p["no"], []))))
    lines += ["", "## 3 交互动作 → 状态反馈 → 页面跳转", ""]
    for p in ALL:
        lines += ["### %s %s" % (p["no"], p["name"]), "",
                  "| 用户动作 | 触发控件 | 状态反馈 | 跳转页 |", "|---|---|---|---|"]
        lines += ["| %s | %s | %s | %s |" % a for a in ACTS.get(p["no"], [])]
        lines.append("")
    lines += ["## 4 跨页功能 F25 / A28 承载矩阵", "", "| 承载页 | 输入字段（data-mic-target） |", "|---|---|"]
    lines += ["| %s | `%s` |" % (a, b) for a, b in CROSS_F25]
    lines += ["", "## 5 全局验收项 A01 – A04 归属", "",
              "| 验收项 | 定义（SRS 第 6 章） | 原型承载位置 |", "|---|---|---|"]
    lines += ["| %s | %s | %s |" % (a, b, c) for a, b, c in GLOBAL_ACC]
    lines += ["", "## 6 版本与边界", "",
              "- 版本标识统一 `V1.5.0`；页面名 `V1.5.0_页号_页面名(标识)`；组件统一 `v15-` 前缀。",
              "- 页面范围：P00 信息架构 + P01 – P10 前台应用 + M01 – M05 后台管理，共 %d 页，同处一个墨刀工程、共用同一在线预览链接。" % (len(ALL) + 1),
              "- 每页含应用界面、状态切换分镜、交互动作表、字段组件表、业务流程、规则边界、需求核对卡与页面互链。",
              "- `交互走查版.html` 为本地浏览器演示，含 15 个页面视图、全部状态切换与「一键走查核心流程」；不调用后端、不写入真实数据。",
              "- 作业原文要求「前台应用与后台管理原型」，未要求「独立后台站点」；M01 – M05 只重组 V1.5.0 真实管理操作。",
              "- 系统按单机单用户设计，暂无登录与权限；不列入验收：真实厂商密钥、检索增强、ESP32 实机、多用户。", ""]
    io.open("原型需求核对表.md", "w", encoding="utf-8").write("\n".join(lines))
    print("墨刀导入页数:", len(import_items), "载荷字节:", sum(len(i["html"].encode("utf-8")) for i in import_items))
    print("交互动作总数:", sum(len(v) for v in ACTS.values()))
    print("可交互走查版:", interactive_path, os.path.getsize(interactive_path), "B")
    print("信息架构 / 状态分镜 / 交互动作 / 页面互链 / 版本口径校验: 全部通过")


if __name__ == "__main__":
    build()
