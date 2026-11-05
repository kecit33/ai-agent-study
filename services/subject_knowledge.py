"""内置学科知识库：为「无密钥演示模式」提供真实、可讲授的学科内容。

设计说明
--------
1. 知识库不是占位文本：题目带标准答案与解析，公式、易错点、章节脉络均按
   同济《高等数学》（第七版）上册的通用教学大纲整理，可直接用于课堂自测。
2. 配置真实大模型（文心一言 / Kimi / GPT / Claude / 自定义兼容接口）后，
   本知识库同时作为「接地上下文」送入模型，避免模型超纲或答非所问；
   模型不可用或返回格式异常时自动回退到本知识库，保证功能永远可用。
3. 未收录的科目走通用模板，并结合「课程记忆」中已上传的资料标题生成内容。
"""
from db import get_conn

DISCIPLINE = "数学"
TEXTBOOK = "高等数学上册"

ALIASES = {
    "数学": TEXTBOOK, "高数": TEXTBOOK, "高等数学": TEXTBOOK,
    "高数上册": TEXTBOOK, "高等数学上册": TEXTBOOK,
    "高等数学（上册）": TEXTBOOK, "高等数学(上册)": TEXTBOOK,
    "advanced mathematics i": TEXTBOOK,
}

# ---------------------------------------------------------------- 公共资料
COMMON_RESOURCES = [
    {"title": "同济大学《高等数学》第七版·上册（教材）", "kind": "教材",
     "desc": "本系统的章节顺序与知识点命名依据；建议按节精读定义与定理证明。",
     "url": "https://www.hep.com.cn/"},
    {"title": "国家高等教育智慧教育平台·高等数学", "kind": "公开课",
     "desc": "国家级课程资源，可按「函数与极限」「一元函数微分学」等专题检索视频。",
     "url": "https://higher.smartedu.cn/"},
    {"title": "中国大学 MOOC·高等数学（一）", "kind": "慕课",
     "desc": "配套测验与讨论区，适合第一轮系统学习与课后自测。",
     "url": "https://www.icourse163.org/"},
    {"title": "MIT 18.01SC Single Variable Calculus", "kind": "公开课",
     "desc": "英文原版单变量微积分，含讲义、习题与解答，可用于拓展理解。",
     "url": "https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/"},
    {"title": "3Blue1Brown《微积分的本质》", "kind": "可视化",
     "desc": "用动画建立导数、积分、泰勒展开的几何直觉，适合概念卡壳时观看。",
     "url": "https://www.3blue1brown.com/topics/calculus"},
    {"title": "Wolfram Alpha", "kind": "工具",
     "desc": "校验极限、导数、积分计算结果，并可查看分步推导。",
     "url": "https://www.wolframalpha.com/"},
    {"title": "Desmos 图形计算器", "kind": "工具",
     "desc": "绘制函数图像，直观验证连续性、极值、凹凸性与旋转体截面。",
     "url": "https://www.desmos.com/calculator"},
    {"title": "Khan Academy · Calculus 1", "kind": "练习",
     "desc": "分知识点即时练习，适合作业之外的补充题量。",
     "url": "https://www.khanacademy.org/math/calculus-1"},
]

CHAPTERS = [
    {
        "id": "ch1", "title": "第一章 函数与极限",
        "overview": "极限是整门高等数学的语言基础：先用 ε-N / ε-δ 把「无限接近」严格化，"
                    "再用无穷小比较、两个重要极限与夹逼准则建立一套可计算的工具集，"
                    "最后由极限定义连续性，并给出闭区间上连续函数的三大性质。",
        "method": "先按「定义 → 性质 → 计算方法」三层过一遍；计算题优先判断是否属于 0/0、∞/∞、"
                  "1^∞、0·∞、∞-∞ 等未定式，再选等价无穷小、洛必达（第三章）或恒等变形。"
                  "分段函数分界点必须分别算左右极限，这是历年最容易被忽略的失分点。",
        "exam": "求极限（含数列极限）、无穷小阶的比较、间断点类型判定、由连续性求参数、零点定理证明题。",
        "topics": [
            {"name": "函数与初等函数", "detail": "定义域、奇偶性、单调性、周期性、反函数与复合函数；基本初等函数图像。"},
            {"name": "数列与函数极限定义", "detail": "ε-N、ε-X、ε-δ 语言；左极限、右极限与极限存在的充要条件。"},
            {"name": "无穷小与无穷大", "detail": "阶的比较（高阶、同阶、等价、k 阶）；等价无穷小替换定理。"},
            {"name": "极限运算法则与两个重要极限", "detail": "四则运算、复合函数极限；lim sin x / x = 1，lim (1+1/x)^x = e。"},
            {"name": "连续性与间断点", "detail": "第一类（可去、跳跃）与第二类（无穷、振荡）间断点；闭区间连续函数的最值、有界、介值与零点定理。"},
        ],
        "formulas": [
            "lim(x→0) sin x / x = 1；lim(x→∞) (1 + 1/x)^x = e；lim(x→0) (1 + x)^(1/x) = e",
            "x→0 等价无穷小：sin x ~ x ~ tan x ~ arcsin x ~ arctan x ~ ln(1+x) ~ e^x − 1",
            "x→0：1 − cos x ~ x²/2；(1+x)^α − 1 ~ αx；x − sin x ~ x³/6",
            "1^∞ 型：lim u^v = exp(lim v·ln u) = exp(lim v(u−1))（当 u→1）",
            "夹逼准则：g(x) ≤ f(x) ≤ h(x) 且 lim g = lim h = A ⇒ lim f = A",
        ],
        "pitfalls": [
            "等价无穷小只能在「乘除因子」整体替换，加减项中随意替换会丢高阶项导致错误。",
            "1^∞、0·∞、∞−∞ 是未定式，不能对两部分分别取极限再相乘/相减。",
            "分段函数在分界点的连续性必须用左右极限与函数值三者相等判断，不能只看表达式。",
            "零点定理要求闭区间连续且端点异号，缺一不可。",
        ],
        "questions": [
            {"type": "计算题", "difficulty": "基础",
             "stem": "求极限 lim(x→0) sin(3x) / tan(2x)。",
             "answer": "3/2",
             "analysis": "x→0 时 sin(3x) ~ 3x，tan(2x) ~ 2x，原式 = lim 3x/(2x) = 3/2。",
             "points": ["等价无穷小", "两个重要极限"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "求极限 lim(x→∞) (1 − 2/x)^(3x)。",
             "answer": "e^(−6)",
             "analysis": "属 1^∞ 型。取对数：3x·ln(1 − 2/x) ~ 3x·(−2/x) = −6，故原式 = e^(−6)。",
             "points": ["1^∞ 未定式", "等价无穷小"]},
            {"type": "证明/讨论题", "difficulty": "中等",
             "stem": "设 f(x) = sin x / x (x ≠ 0)，f(0) = 0。判断 x = 0 的间断点类型，并说明如何修改定义使其连续。",
             "answer": "x = 0 为可去间断点；改定义 f(0) = 1 即在 x = 0 连续。",
             "analysis": "lim(x→0) sin x / x = 1 极限存在但不等于 f(0) = 0，属第一类可去间断点；补充定义 f(0) = 1 后连续。",
             "points": ["间断点分类", "重要极限"]},
            {"type": "证明题", "difficulty": "较难",
             "stem": "用夹逼准则求 lim(n→∞) [1/√(n²+1) + 1/√(n²+2) + … + 1/√(n²+n)]。",
             "answer": "1",
             "analysis": "记 S_n 为和式，则 n/√(n²+n) ≤ S_n ≤ n/√(n²+1)，两端极限均为 1，由夹逼准则得 lim S_n = 1。",
             "points": ["夹逼准则", "数列极限"]},
        ],
        "resources": [0, 1, 2, 5, 6],
    },
    {
        "id": "ch2", "title": "第二章 导数与微分",
        "overview": "导数刻画函数的变化率，微分刻画局部线性近似。本章从导数定义出发，建立四则、复合、"
                    "反函数、隐函数与参数方程的完整求导体系，并讨论高阶导数与可导性的边界情形。",
        "method": "把求导拆成「识别结构 → 分层拆解 → 逐层求导 → 合并化简」四步。"
                  "复合函数用链式法则画层级图避免漏层；分段点、绝对值点、含参点一律回到定义求左右导数。",
        "exam": "用定义求导与讨论可导性、复合/隐函数/参数方程求导、高阶导数与莱布尼茨公式、微分近似计算。",
        "topics": [
            {"name": "导数定义与几何意义", "detail": "f'(x₀) = lim Δy/Δx；切线与法线方程；左导数、右导数与可导判定。"},
            {"name": "求导法则", "detail": "四则运算、反函数求导、复合函数链式法则、基本初等函数导数表。"},
            {"name": "隐函数与参数方程求导", "detail": "F(x,y)=0 两边对 x 求导；dy/dx = y'(t)/x'(t)；对数求导法。"},
            {"name": "高阶导数", "detail": "二阶导的物理意义；莱布尼茨公式；常见函数的 n 阶导数。"},
            {"name": "微分与线性近似", "detail": "dy = f'(x)dx；Δy ≈ dy 用于近似计算与误差估计。"},
        ],
        "formulas": [
            "(uv)' = u'v + uv'；(u/v)' = (u'v − uv')/v²；链式法则 dy/dx = (dy/du)(du/dx)",
            "(x^α)' = αx^(α−1)；(ln x)' = 1/x；(e^x)' = e^x；(a^x)' = a^x ln a",
            "(sin x)' = cos x；(cos x)' = −sin x；(tan x)' = sec²x；(arctan x)' = 1/(1+x²)",
            "隐函数：dy/dx = −F_x / F_y；参数方程：dy/dx = y'(t)/x'(t)",
            "d²y/dx² = [d(dy/dx)/dt] / x'(t)；(uv)^(n) = Σ C(n,k) u^(k) v^(n−k)",
        ],
        "pitfalls": [
            "连续不一定可导：y = |x| 在 x = 0 连续但左右导数分别为 −1 与 1。",
            "复合函数求导易漏中间层，例如 ln(1+e^(x²)) 需要连乘 e^(x²) 与 2x。",
            "参数方程二阶导必须再对 t 求导后除以 x'(t)，不能直接对 x 求导。",
            "微分 dy = f'(x)dx 与增量 Δy 只在 Δx→0 时近似相等，别把近似当恒等。",
        ],
        "questions": [
            {"type": "计算题", "difficulty": "基础",
             "stem": "设 y = ln(1 + e^(x²))，求 y'。",
             "answer": "y' = 2x·e^(x²) / (1 + e^(x²))",
             "analysis": "三层复合：外层 ln u 导 1/u，中层 1+e^v 导 e^v，内层 x² 导 2x，连乘即可。",
             "points": ["链式法则", "复合函数"]},
            {"type": "证明/讨论题", "difficulty": "较难",
             "stem": "设 f(x) = x² sin(1/x)（x ≠ 0），f(0) = 0。求 f'(0)，并判断 f'(x) 在 x = 0 是否连续。",
             "answer": "f'(0) = 0；但 f'(x) 在 x = 0 不连续。",
             "analysis": "f'(0) = lim(h→0) h·sin(1/h) = 0（有界量乘无穷小）。x ≠ 0 时 f'(x) = 2x sin(1/x) − cos(1/x)，"
                         "x→0 时 cos(1/x) 振荡无极限，故导函数在 0 处不连续。这是「可导但导函数不连续」的经典反例。",
             "points": ["导数定义", "振荡间断", "可导与连续"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "设 x² + y² = 1（y ≠ 0），求 dy/dx 与 d²y/dx²。",
             "answer": "dy/dx = −x/y；d²y/dx² = −1/y³",
             "analysis": "两边对 x 求导：2x + 2y·y' = 0 ⇒ y' = −x/y。再求导：y'' = −(y − x y')/y² "
                         "= −(y + x²/y)/y² = −(x²+y²)/y³ = −1/y³。",
             "points": ["隐函数求导", "高阶导数"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "设参数方程 x = t − sin t，y = 1 − cos t，求 dy/dx。",
             "answer": "dy/dx = sin t / (1 − cos t) = cot(t/2)",
             "analysis": "x'(t) = 1 − cos t，y'(t) = sin t，故 dy/dx = y'(t)/x'(t)；用半角公式化为 cot(t/2)。",
             "points": ["参数方程求导", "半角公式"]},
        ],
        "resources": [0, 1, 3, 5, 7],
    },
    {
        "id": "ch3", "title": "第三章 微分中值定理与导数的应用",
        "overview": "中值定理把「局部导数」与「整体增量」连接起来，是证明题的核心工具；泰勒公式与洛必达法则"
                    "把极限计算推进到高阶；再用一、二阶导数系统刻画单调性、极值、凹凸性与曲率。",
        "method": "证明题先识别要证的不等式/等式适合哪个定理，再构造辅助函数；"
                  "应用题固定流程为「求 f' 找驻点 → 划分区间判单调 → 求 f'' 判凹凸与拐点 → 比较端点与极值定最值」。",
        "exam": "罗尔/拉格朗日定理证明题、洛必达与泰勒求极限、单调性与极值、最值应用题、凹凸性与拐点、渐近线与曲率。",
        "topics": [
            {"name": "三大中值定理", "detail": "费马引理、罗尔定理、拉格朗日中值定理、柯西中值定理及辅助函数构造。"},
            {"name": "泰勒公式", "detail": "带皮亚诺/拉格朗日余项的泰勒展开；常用函数在 x=0 的麦克劳林公式。"},
            {"name": "洛必达法则", "detail": "0/0 与 ∞/∞ 型；其他未定式的转化；使用前提条件与失效情形。"},
            {"name": "单调性、极值与最值", "detail": "驻点与不可导点；一阶导符号判定；闭区间最值的比较法；实际优化问题。"},
            {"name": "凹凸性、拐点与曲率", "detail": "二阶导符号与拐点；弧微分与曲率 K = |y''|/(1+y'²)^(3/2)。"},
        ],
        "formulas": [
            "拉格朗日：f(b) − f(a) = f'(ξ)(b − a)，ξ ∈ (a, b)；柯西：f(b)−f(a) / g(b)−g(a) = f'(ξ)/g'(ξ)",
            "泰勒：f(x) = Σ(k=0..n) f^(k)(x₀)/k!·(x−x₀)^k + R_n(x)",
            "e^x = 1 + x + x²/2! + x³/3! + o(x³)；sin x = x − x³/3! + o(x³)",
            "ln(1+x) = x − x²/2 + x³/3 + o(x³)；(1+x)^α = 1 + αx + α(α−1)x²/2 + o(x²)",
            "洛必达：lim f/g = lim f'/g'（仅 0/0、∞/∞ 且右端极限存在或为 ∞）",
        ],
        "pitfalls": [
            "洛必达法则只适用于 0/0 与 ∞/∞，且要求导数之比的极限存在；滥用会得出伪结论。",
            "中值定理前提条件（闭区间连续、开区间可导）必须逐条验证。",
            "f'(x₀)=0 只是极值的必要非充分条件，y = x³ 在 x=0 是驻点但不是极值点。",
            "f''(x₀)=0 不一定为拐点（如 y = x⁴），必须看两侧二阶导是否变号。",
        ],
        "questions": [
            {"type": "证明题", "difficulty": "中等",
             "stem": "证明：当 x > 0 时，e^x > 1 + x + x²/2。",
             "answer": "令 g(x) = e^x − 1 − x − x²/2，由 g'''(x) = e^x > 0 逐阶推得 g(x) > 0。",
             "analysis": "g(0)=g'(0)=g''(0)=0 且 g'''(x)=e^x>0 ⇒ g'' 在 (0,∞) 递增且 g''>0 ⇒ g' 递增且 g'>0 "
                         "⇒ g 递增且 g(x)>g(0)=0。亦可用带拉格朗日余项的泰勒公式：余项 e^ξ x³/6 > 0。",
             "points": ["泰勒公式", "单调性证明不等式"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "求 lim(x→0) (x − sin x) / x³。",
             "answer": "1/6",
             "analysis": "泰勒展开 sin x = x − x³/6 + o(x³)，分子 = x³/6 + o(x³)，故极限为 1/6；"
                         "或连续三次洛必达：lim (1−cos x)/(3x²) = lim sin x/(6x) = 1/6。",
             "points": ["泰勒公式", "洛必达法则"]},
            {"type": "计算题", "difficulty": "基础",
             "stem": "求 f(x) = x³ − 3x² − 9x + 5 的单调区间与极值。",
             "answer": "增区间 (−∞,−1)、(3,+∞)，减区间 (−1,3)；极大值 f(−1)=10，极小值 f(3)=−22。",
             "analysis": "f'(x) = 3x² − 6x − 9 = 3(x+1)(x−3)，驻点 x=−1, 3；列表判符号后代入原函数求极值。",
             "points": ["单调性", "极值"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "求曲线 y = x⁴ − 6x² 的凹凸区间与拐点。",
             "answer": "|x|>1 时为凹（下凸），|x|<1 时为凸（上凸）；拐点 (1,−5) 与 (−1,−5)。",
             "analysis": "y'' = 12x² − 12 = 12(x−1)(x+1)；y''=0 得 x=±1，两侧变号，"
                         "代入 y(±1)=1−6=−5，故拐点为 (±1,−5)。",
             "points": ["凹凸性", "拐点"]},
        ],
        "resources": [0, 2, 3, 4, 7],
    },
    {
        "id": "ch4", "title": "第四章 不定积分",
        "overview": "不定积分是求导的逆运算，目标是「找全体原函数」。本章围绕基本积分表，建立第一类/第二类换元法"
                    "与分部积分法两大工具，并给出有理函数与三角有理式的通用处理思路。",
        "method": "拿到积分先看结构：复合函数内层导数是否出现（凑微分）、是否含根式或 √(a²−x²)（三角换元）、"
                  "是否为两类不同函数相乘（分部积分，按「反对幂指三」选 u）。每题算完务必求导验算并补常数 C。",
        "exam": "凑微分、三角换元、分部积分、有理函数分解、综合积分题，以及由原函数反求被积函数的概念题。",
        "topics": [
            {"name": "原函数与不定积分概念", "detail": "原函数存在定理；∫f(x)dx = F(x)+C；积分与求导互逆。"},
            {"name": "基本积分表与凑微分", "detail": "13 个基本公式；第一类换元法 ∫f(φ(x))φ'(x)dx。"},
            {"name": "第二类换元法", "detail": "三角代换消去 √(a²−x²)、√(a²+x²)、√(x²−a²)；倒代换。"},
            {"name": "分部积分法", "detail": "∫u dv = uv − ∫v du；u 的选取优先级；循环型与递推型积分。"},
            {"name": "有理函数与三角有理式", "detail": "部分分式分解；万能代换 t = tan(x/2)。"},
        ],
        "formulas": [
            "∫x^α dx = x^(α+1)/(α+1) + C (α ≠ −1)；∫1/x dx = ln|x| + C",
            "∫e^x dx = e^x + C；∫a^x dx = a^x/ln a + C；∫sec²x dx = tan x + C",
            "∫dx/(1+x²) = arctan x + C；∫dx/√(1−x²) = arcsin x + C",
            "∫u dv = uv − ∫v du；∫f(φ(x))φ'(x)dx = ∫f(u)du（u = φ(x)）",
            "∫√(a²−x²)dx = (x/2)√(a²−x²) + (a²/2)arcsin(x/a) + C",
        ],
        "pitfalls": [
            "不定积分结果必须带任意常数 C，漏写是最高频的形式错误。",
            "∫1/x dx = ln|x| + C，绝对值不能省略；在跨过 x=0 的区间上要分段讨论。",
            "第二类换元求出关于 t 的原函数后必须回代为 x，并注意反三角函数的取值范围。",
            "分部积分的 u 应按「反、对、幂、指、三」优先级选取，选反会使积分更复杂。",
        ],
        "questions": [
            {"type": "计算题", "difficulty": "基础",
             "stem": "计算 ∫ x·e^(2x) dx。",
             "answer": "(x/2 − 1/4)e^(2x) + C",
             "analysis": "取 u = x，dv = e^(2x)dx，则 v = e^(2x)/2；原式 = x e^(2x)/2 − ∫e^(2x)/2 dx "
                         "= (x/2 − 1/4)e^(2x) + C。求导可验算回 x e^(2x)。",
             "points": ["分部积分法"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "计算 ∫ dx / (x² + 2x + 5)。",
             "answer": "(1/2)·arctan((x+1)/2) + C",
             "analysis": "配方 x²+2x+5 = (x+1)² + 4，令 u = x+1，则 ∫du/(u²+2²) = (1/2)arctan(u/2) + C。",
             "points": ["配方", "基本积分表"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "计算 ∫ √(1 − x²) dx（|x| < 1）。",
             "answer": "(x/2)√(1−x²) + (1/2)arcsin x + C",
             "analysis": "令 x = sin t，dx = cos t dt，原式 = ∫cos²t dt = (t/2)+(sin 2t)/4 + C "
                         "= (1/2)arcsin x + (x/2)√(1−x²) + C，注意回代。",
             "points": ["三角换元", "回代"]},
            {"type": "计算题", "difficulty": "基础",
             "stem": "计算 ∫ sin²x·cos x dx。",
             "answer": "sin³x / 3 + C",
             "analysis": "凑微分：cos x dx = d(sin x)，令 u = sin x 得 ∫u²du = u³/3 + C。",
             "points": ["第一类换元法", "凑微分"]},
        ],
        "resources": [0, 2, 5, 7],
    },
    {
        "id": "ch5", "title": "第五章 定积分",
        "overview": "定积分由「分割、近似、求和、取极限」定义，是一个数；牛顿—莱布尼茨公式把它与不定积分连成一体，"
                    "变限积分则把积分上限变成函数，直接催生了微积分基本定理的完整形式，最后延伸到反常积分。",
        "method": "计算题先检查积分区间内有无瑕点或无穷区间（有则按反常积分处理），"
                  "再利用奇偶性、周期性、区间可加性化简，最后选牛顿—莱布尼茨、换元（务必换限）或分部积分。",
        "exam": "定义求极限、积分中值定理、变限积分求导、定积分计算、奇偶对称化简、反常积分敛散性判别。",
        "topics": [
            {"name": "定积分定义与性质", "detail": "黎曼和；线性性、区间可加性、比较定理、估值定理与积分中值定理。"},
            {"name": "微积分基本公式", "detail": "变限积分函数 Φ(x)=∫ₐˣf(t)dt；牛顿—莱布尼茨公式。"},
            {"name": "定积分计算法", "detail": "换元法（同步换限）、分部积分法、华里士（点火）公式、奇偶与周期化简。"},
            {"name": "反常积分", "detail": "无穷区间反常积分、无界函数瑕积分；收敛判别与 Γ 函数简介。"},
        ],
        "formulas": [
            "∫ₐᵇ f(x)dx = F(b) − F(a)（f 在 [a,b] 连续且 F' = f）",
            "d/dx ∫ₐ^φ(x) f(t)dt = f(φ(x))·φ'(x)",
            "∫₋ₐᵃ f dx = 2∫₀ᵃ f dx（f 偶）；= 0（f 奇）",
            "华里士公式：∫₀^(π/2) sinⁿx dx = (n−1)/n·(n−3)/(n−2)·…·(π/2)（n 为偶数时末项）",
            "∫ₐᵇ u dv = [uv]ₐᵇ − ∫ₐᵇ v du；∫₁^(+∞) dx/x^p 当 p>1 收敛",
        ],
        "pitfalls": [
            "定积分换元必须同步更换积分上下限，只换被积函数不换限是典型错误。",
            "被积函数在区间内有瑕点时不能直接用牛顿—莱布尼茨公式，例如 ∫₋₁¹ dx/x² 实际发散。",
            "变限积分上限是 φ(x) 时要乘 φ'(x)，漏掉链式因子是常见失分点。",
            "∫|f| ≠ |∫f|，去绝对值必须按零点分段。",
        ],
        "questions": [
            {"type": "计算题", "difficulty": "基础",
             "stem": "计算 ∫₀^(π/2) sin²x dx。",
             "answer": "π/4",
             "analysis": "用降幂 sin²x = (1 − cos 2x)/2，积分得 [x/2 − sin 2x/4]₀^(π/2) = π/4；"
                         "亦可用华里士公式 I₂ = (1/2)(π/2) = π/4。",
             "points": ["华里士公式", "降幂"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "设 F(x) = ∫₀^(x²) e^(−t²) dt，求 F'(x)。",
             "answer": "F'(x) = 2x·e^(−x⁴)",
             "analysis": "变限积分求导公式：F'(x) = e^(−(x²)²)·(x²)' = 2x e^(−x⁴)。",
             "points": ["变限积分", "链式法则"]},
            {"type": "判断题", "difficulty": "中等",
             "stem": "有人计算 ∫₋₁¹ dx/x² = [−1/x]₋₁¹ = −2。这个结果对吗？请说明原因并给出正确结论。",
             "answer": "错误。x = 0 是瑕点，该反常积分发散（趋于 +∞）。",
             "analysis": "被积函数在积分区间内无界，必须拆成 ∫₋₁⁰ + ∫₀¹ 两个瑕积分分别取极限；"
                         "其中 ∫₀¹ dx/x² = lim(ε→0⁺)(1/ε − 1) = +∞，故原积分发散。",
             "points": ["瑕积分", "敛散性判别"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "计算 ∫₀^π x·sin x dx。",
             "answer": "π",
             "analysis": "分部积分：取 u = x，dv = sin x dx ⇒ v = −cos x，"
                         "原式 = [−x cos x]₀^π + ∫₀^π cos x dx = π + 0 = π。",
             "points": ["分部积分", "定积分计算"]},
        ],
        "resources": [0, 1, 3, 5, 7],
    },
    {
        "id": "ch6", "title": "第六章 定积分的应用",
        "overview": "本章把定积分变成「可建模的计算工具」：元素法（微元法）是统一思想，"
                    "先在小区间上写出微元 dA / dV / dW，再积分求和；覆盖面积、体积、弧长与物理应用。",
        "method": "画图 → 选积分变量 → 写微元 → 定限 → 积分，五步固定下来。"
                  "面积与体积题务必先求交点、判断上下（左右）函数，必要时分区间；物理应用先统一单位。",
        "exam": "平面图形面积（直角坐标/极坐标）、旋转体体积、平行截面面积已知的立体体积、弧长、做功与水压力。",
        "topics": [
            {"name": "元素法（微元法）", "detail": "在 [x, x+dx] 上以「匀代变」写出部分量近似 dU = f(x)dx，再积分。"},
            {"name": "平面图形面积", "detail": "直角坐标 A = ∫(上−下)dx；极坐标 A = (1/2)∫ρ²(θ)dθ。"},
            {"name": "体积", "detail": "绕 x 轴圆盘法 V = π∫f²dx；绕 y 轴柱壳法 V = 2π∫x f dx。"},
            {"name": "平面曲线弧长", "detail": "L = ∫√(1+y'²)dx；参数式 L = ∫√(x'²+y'²)dt。"},
            {"name": "物理应用", "detail": "变力做功、液体侧压力、引力；建立坐标系后写微元。"},
        ],
        "formulas": [
            "A = ∫ₐᵇ |f(x) − g(x)| dx；极坐标 A = (1/2)∫ₐᵝ ρ²(θ) dθ",
            "绕 x 轴：V = π∫ₐᵇ f²(x)dx；绕 y 轴（柱壳）：V = 2π∫ₐᵇ x f(x) dx",
            "弧长：L = ∫ₐᵇ √(1 + y'²) dx；参数式 L = ∫ₐᵝ √(x'²(t) + y'²(t)) dt",
            "变力做功：W = ∫ₐᵇ F(x)dx；液体压力：P = ∫ ρ g h(y)·w(y) dy",
        ],
        "pitfalls": [
            "面积必须「上减下」且非负；两曲线在区间内交换上下位置时要分段积分。",
            "绕不同轴旋转公式不同：绕 x 轴常用圆盘法，绕 y 轴用柱壳法更简便，混淆会差一个因子。",
            "极坐标面积公式别漏系数 1/2，且要先由图形确定 θ 的完整范围。",
            "弧长被积函数含平方根，必须保证取非负并正确化简完全平方。",
        ],
        "questions": [
            {"type": "计算题", "difficulty": "基础",
             "stem": "求由 y = x² 与 y = x 围成的平面图形的面积。",
             "answer": "1/6",
             "analysis": "交点 x = 0, 1；在 [0,1] 上 x ≥ x²，A = ∫₀¹ (x − x²)dx = 1/2 − 1/3 = 1/6。",
             "points": ["元素法", "平面图形面积"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "上题图形绕 x 轴旋转一周，求旋转体体积。",
             "answer": "2π/15",
             "analysis": " washer（圆环）法：V = π∫₀¹ (x² − x⁴)dx = π(1/3 − 1/5) = 2π/15，"
                         "外半径为 y = x，内半径为 y = x²。",
             "points": ["旋转体体积", "圆环法"]},
            {"type": "计算题", "difficulty": "较难",
             "stem": "求摆线 x = a(t − sin t)，y = a(1 − cos t)（0 ≤ t ≤ 2π）一拱的弧长。",
             "answer": "8a",
             "analysis": "x' = a(1−cos t)，y' = a sin t，√(x'²+y'²) = a√(2−2cos t) = 2a·sin(t/2)；"
                         "L = ∫₀^(2π) 2a sin(t/2)dt = 8a。",
             "points": ["参数方程弧长", "半角公式"]},
            {"type": "计算题", "difficulty": "中等",
             "stem": "求心形线 ρ = a(1 + cos θ)（a > 0）所围图形的面积。",
             "answer": "(3/2)πa²",
             "analysis": "A = (1/2)∫₀^(2π) a²(1+cos θ)²dθ = (a²/2)(2π + 0 + π) = (3/2)πa²，"
                         "其中 ∫cos²θdθ 在 [0,2π] 上等于 π。",
             "points": ["极坐标面积"]},
        ],
        "resources": [0, 1, 4, 6],
    },
    {
        "id": "ch7", "title": "第七章 微分方程",
        "overview": "微分方程是「含未知函数导数的方程」，本章从一阶方程的可分离变量、齐次、线性三大可解类型出发，"
                    "再到可降阶的高阶方程，最后用特征方程法完整解决二阶常系数线性方程。",
        "method": "先判阶数与类型，再选方法：一阶看能否分离变量、是否为齐次、是否可写成 y'+P(x)y=Q(x)；"
                  "二阶常系数直接写特征方程并按「两相异实根 / 重根 / 共轭复根」套通解，非齐次再叠加特解。",
        "exam": "可分离变量方程、齐次方程、一阶线性方程（含常数变易法）、可降阶方程、二阶常系数线性方程、简单建模题。",
        "topics": [
            {"name": "基本概念", "detail": "阶、解、通解、特解、初值条件与积分曲线。"},
            {"name": "一阶方程可解类型", "detail": "可分离变量、齐次方程 dy/dx = φ(y/x)、一阶线性与伯努利方程。"},
            {"name": "可降阶的高阶方程", "detail": "y^(n)=f(x)、y''=f(x,y')、y''=f(y,y') 三类代换。"},
            {"name": "线性微分方程解的结构", "detail": "齐次通解 + 非齐次特解；线性无关与朗斯基行列式。"},
            {"name": "二阶常系数线性方程", "detail": "特征方程三种情形；非齐次项为 e^(λx)Pₙ(x) 或三角函数时的特解设法。"},
        ],
        "formulas": [
            "可分离变量：dy/g(y) = f(x)dx ⇒ ∫dy/g(y) = ∫f(x)dx + C",
            "一阶线性 y' + P(x)y = Q(x)：y = e^(−∫P dx)[∫Q·e^(∫P dx)dx + C]",
            "特征方程 r² + pr + q = 0；两相异实根：y = C₁e^(r₁x) + C₂e^(r₂x)",
            "重根 r：y = (C₁ + C₂x)e^(rx)；共轭复根 α±iβ：y = e^(αx)(C₁cos βx + C₂sin βx)",
            "伯努利 y' + P(x)y = Q(x)yⁿ：令 z = y^(1−n) 化为一阶线性",
        ],
        "pitfalls": [
            "分离变量时除以 g(y) 会丢失 g(y)=0 对应的常数解，需单独补回。",
            "一阶线性通解公式中 e^(−∫P dx) 与 e^(∫P dx) 符号相反，套错整题皆错。",
            "特征方程出现重根时第二个线性无关解必须乘 x。",
            "非齐次特解与齐次解「共振」时，需额外乘 x 或 x²，不能直接设同型。",
        ],
        "questions": [
            {"type": "初值问题", "difficulty": "基础",
             "stem": "求解初值问题 y' = 2xy，y(0) = 1。",
             "answer": "y = e^(x²)",
             "analysis": "分离变量 dy/y = 2x dx ⇒ ln|y| = x² + C ⇒ y = C₁e^(x²)；代入 y(0)=1 得 C₁=1。",
             "points": ["可分离变量", "初值问题"]},
            {"type": "初值问题", "difficulty": "中等",
             "stem": "求解 y' + 2y = e^(−x)，y(0) = 0。",
             "answer": "y = e^(−x) − e^(−2x)",
             "analysis": "一阶线性，P=2, Q=e^(−x)：y = e^(−2x)[∫e^(2x)e^(−x)dx + C] "
                         "= e^(−2x)(e^x + C) = e^(−x) + C e^(−2x)；y(0)=0 ⇒ C = −1。",
             "points": ["一阶线性方程", "常数变易法"]},
            {"type": "初值问题", "difficulty": "中等",
             "stem": "求解 y'' − 3y' + 2y = 0，y(0) = 1，y'(0) = 0。",
             "answer": "y = 2e^x − e^(2x)",
             "analysis": "特征方程 r² − 3r + 2 = 0 ⇒ r = 1, 2；通解 y = C₁e^x + C₂e^(2x)。"
                         "由 C₁+C₂=1、C₁+2C₂=0 解得 C₁=2, C₂=−1。",
             "points": ["特征方程", "二阶常系数齐次"]},
            {"type": "计算题", "difficulty": "基础",
             "stem": "求微分方程 y'' + y = x 的通解。",
             "answer": "y = C₁cos x + C₂sin x + x",
             "analysis": "齐次通解 y_h = C₁cos x + C₂sin x；右端为一次多项式且 λ=0 非特征根，"
                         "设特解 y* = ax + b，代入得 ax + b = x ⇒ a=1, b=0，故 y* = x。",
             "points": ["非齐次方程", "待定系数法"]},
        ],
        "resources": [0, 1, 3, 5],
    },
]


def resolve(subject: str) -> str:
    """把「数学 / 高数 / 高等数学」等别名统一解析到内置教材名。"""
    key = (subject or "").strip()
    return ALIASES.get(key, key)


def is_builtin(subject: str) -> bool:
    return resolve(subject) == TEXTBOOK


def catalog() -> dict:
    """返回知识库目录：学科 → 教材 → 章节。"""
    return {
        "discipline": DISCIPLINE,
        "textbook": TEXTBOOK,
        "aliases": sorted(ALIASES.keys()),
        "chapters": [{"id": c["id"], "title": c["title"],
                      "topics": [t["name"] for t in c["topics"]],
                      "question_count": len(c["questions"])} for c in CHAPTERS],
        "fallback": "未收录的科目将走通用模板，并结合该课程已上传的课程记忆生成内容",
    }


def _generic_chapter(name: str, materials: list) -> dict:
    """未内置科目：结合课程资料标题生成一份可用的通用章节骨架。"""
    hints = [m["title"] or ("资料%d" % (i + 1)) for i, m in enumerate(materials[:5])]
    base = [
        {"name": "基本概念与定义", "detail": "梳理「%s」的核心术语、符号约定与适用前提。" % name},
        {"name": "原理与推导", "detail": "理解主要结论的来龙去脉，能复述关键推导步骤。"},
        {"name": "典型题型与方法", "detail": "按题型归类解题套路，形成可复用的解题清单。"},
        {"name": "易错点与边界条件", "detail": "记录高频错误、反例与结论成立的限制条件。"},
        {"name": "综合应用", "detail": "把知识点放进完整题目或真实场景中检验掌握程度。"},
    ]
    if hints:
        base.append({"name": "课程记忆联动", "detail": "结合已上传资料：" + "、".join(hints)})
    return {
        "id": "generic", "title": name,
        "overview": "本系统尚未内置《%s》的专用知识库，已按通用学科学习框架生成资源包，"
                    "并把「课程记忆」中已上传的 %d 份资料标题纳入上下文。"
                    "配置文心一言 / Kimi 等真实模型后，可由模型结合上传的课件全文深度生成。" % (name, len(materials)),
        "method": "建议先按「概念 → 原理 → 题型 → 错因 → 应用」五层搭建框架，"
                  "再把课程资料逐份拆成知识点卡片，最后用自测题检验。",
        "exam": "以任课教师给出的考试大纲为准；本资源包提供通用复习骨架与自测题模板。",
        "topics": base,
        "formulas": ["（通用模板）请在「课程记忆」中上传含公式的课件，或接入真实大模型以生成公式速查表。"],
        "pitfalls": ["未结合具体教材时，结论的适用条件与例外情形最容易被忽略。",
                     "只背结论不复述推导，遇到变式题容易失分。"],
        "questions": [
            {"type": "概念题", "difficulty": "基础",
             "stem": "请用自己的话表述《%s》中最核心的一个概念，并说明它成立的前提条件。" % name,
             "answer": "能准确写出定义、符号含义、适用前提，并能举出一个反例说明前提不可省略。",
             "analysis": "概念题的评分点在于「定义 + 条件 + 反例」三要素齐全，缺一即不完整。",
             "points": ["概念理解"]},
            {"type": "方法题", "difficulty": "中等",
             "stem": "针对《%s》的某一类典型题型，写出可复用的解题步骤清单。" % name,
             "answer": "至少包含：识别题型 → 列出已知与所求 → 选择方法 → 执行推导 → 结果校验 五步。",
             "analysis": "把隐性经验显性化为步骤，是稳定得分与查漏补缺的关键。",
             "points": ["方法归纳"]},
            {"type": "辨析题", "difficulty": "中等",
             "stem": "举出一个《%s》中容易混淆的结论对，并说明二者的区别与联系。" % name,
             "answer": "能指出至少一个关键差异，并给出使其中一个成立、另一个失效的具体例子。",
             "analysis": "辨析题考查边界意识，建议配合课程记忆中的课件原文核对表述。",
             "points": ["易错辨析"]},
        ],
        "resources": list(range(len(COMMON_RESOURCES))),
    }


def get_chapters(subject: str, chapter: str = "") -> list:
    """返回待生成的章节列表；chapter 支持章号、章节 id、标题关键字。"""
    name = resolve(subject)
    if not is_builtin(name):
        mats = []
        try:
            conn = get_conn()
            rows = conn.execute(
                "SELECT title FROM course_materials WHERE course_id IN "
                "(SELECT id FROM courses WHERE name=?) ORDER BY id", (name,)
            ).fetchall()
            conn.close()
            mats = [dict(r) for r in rows]
        except Exception:
            pass
        return [_generic_chapter(name, mats)]

    key = (chapter or "").strip()
    if not key or key in ("全部", "all", "全册", "all chapters"):
        return CHAPTERS
    for c in CHAPTERS:
        if key == c["id"] or key == c["title"] or key in c["title"]:
            return [c]
    # 支持「第1章」「1」「ch1」等写法
    num = ''
    for ch in key:
        if ch.isdigit():
            num += ch
    if num and 1 <= int(num) <= len(CHAPTERS):
        return [CHAPTERS[int(num) - 1]]
    # 支持按知识点名称定位
    hit = [c for c in CHAPTERS if any(key in t["name"] for t in c["topics"])]
    if hit:
        return hit
    return CHAPTERS


def get_resources(indices) -> list:
    return [dict(COMMON_RESOURCES[i]) for i in indices if 0 <= i < len(COMMON_RESOURCES)]
