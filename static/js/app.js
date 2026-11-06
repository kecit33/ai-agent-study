const $ = (id) => document.getElementById(id);
const api = async (url, opts) => {
  let res;
  try {
    res = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...opts,
    });
  } catch (e) {
    console.warn("[api] 网络请求失败", url, e);
    return { error: "网络请求失败，请确认服务已启动：" + e };
  }
  let data;
  try {
    data = await res.json();
  } catch (e) {
    console.warn("[api] 响应不是 JSON", url, res.status);
    return { error: "响应解析失败（HTTP " + res.status + "）" };
  }
  // 统一异常响应形状：调用方永远能安全地读 .error，
  // 不会因服务端返回 JSON null / 非 2xx 而拿到 undefined 再 .xxx 崩溃。
  if (data === null || data === undefined) {
    return { error: "服务端返回空响应（HTTP " + res.status + "）" };
  }
  if (!res.ok && !data.error) {
    return { error: "请求失败（HTTP " + res.status + "）" };
  }
  return data;
};

// 统一错误提示：接口返回 {error} 时给用户可见反馈，而不是「点了没反应」
function showApiError(r) {
  if (r && r.error) { alert(r.error); return false; }
  return true;
}

// 带下载语义的导出：用 blob 下载，接口异常时只提示，不用 location.href
// 把整个应用页面导航替换掉（会丢失未保存的展开状态与输入内容）。
function downloadFromUrl(url, filename) {
  fetch(url).then(async (res) => {
    if (!res.ok) throw new Error("HTTP " + res.status);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(a.href), 1500);
  }).catch((e) => alert("导出失败：" + e));
}

let currentCourseId = null;
let courseLoadSeq = 0;  // 切换课程时丢弃过期异步响应，避免旧课程数据覆盖新课程

/* ==================== 主题：深色 / 浅色 / 跟随系统 + 主题色 ==================== */
const ACCENTS = [
  { name: "校园蓝", color: "#2f6fed" },
  { name: "薄荷青", color: "#0d9488" },
  { name: "葡萄紫", color: "#7c3aed" },
  { name: "活力橙", color: "#ea580c" },
  { name: "樱花粉", color: "#db2777" },
  { name: "竹叶绿", color: "#16a34a" },
];
const MODE_LABEL = { light: "☀️ 浅色", dark: "🌙 深色", auto: "🖥 跟随系统" };
const systemDark = window.matchMedia("(prefers-color-scheme: dark)");
let themeMode = localStorage.getItem("cc-theme-mode") || "auto";

function shade(hex, ratio) {
  // 将 #rrggbb 按比例调暗，用于渐变顶栏的深色端
  const n = parseInt(hex.slice(1), 16);
  const f = (v) => Math.max(0, Math.min(255, Math.round(v * (1 + ratio))));
  const r = f((n >> 16) & 255), g = f((n >> 8) & 255), b = f(n & 255);
  return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("");
}

function applyTheme() {
  const dark = themeMode === "dark" || (themeMode === "auto" && systemDark.matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
  $("themeToggle").textContent = MODE_LABEL[themeMode];
  document.querySelectorAll("#themeSeg button").forEach((b) => {
    b.classList.toggle("active", b.dataset.mode === themeMode);
  });
}

function setMode(mode) {
  themeMode = mode;
  localStorage.setItem("cc-theme-mode", mode);
  applyTheme();
}

function setAccent(color) {
  localStorage.setItem("cc-accent", color);
  document.documentElement.style.setProperty("--primary", color);
  document.documentElement.style.setProperty("--primary-dark", shade(color, -0.25));
  document.querySelectorAll(".swatch").forEach((s) => {
    s.classList.toggle("active", s.dataset.color === color);
  });
}

function initTheme() {
  applyTheme();
  setAccent(localStorage.getItem("cc-accent") || ACCENTS[0].color);
  $("themeToggle").onclick = () => {
    const order = ["auto", "light", "dark"];
    setMode(order[(order.indexOf(themeMode) + 1) % 3]);
  };
  document.querySelectorAll("#themeSeg button").forEach((b) => {
    b.onclick = () => setMode(b.dataset.mode);
  });
  systemDark.addEventListener("change", () => { if (themeMode === "auto") applyTheme(); });

  const box = $("swatches");
  ACCENTS.forEach((a) => {
    const b = document.createElement("button");
    b.className = "swatch"; b.dataset.color = a.color; b.title = a.name;
    b.style.background = a.color;
    b.onclick = () => setAccent(a.color);
    box.appendChild(b);
  });
  const picker = document.createElement("input");
  picker.type = "color"; picker.title = "自定义主题色";
  picker.value = localStorage.getItem("cc-accent") || ACCENTS[0].color;
  picker.oninput = () => setAccent(picker.value);
  box.appendChild(picker);
}

/* ==================== 语音输入（Web Speech API） ==================== */
const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognizer = null, recBtn = null, recTarget = null;

function stopRec() {
  if (recognizer) { try { recognizer.stop(); } catch (e) {} }
}

function toggleMic(btn) {
  if (!SR) {
    alert("当前浏览器不支持语音输入。\n请使用 Chrome 或 Edge，并通过 localhost / HTTPS 访问。\n也可直接键盘输入，功能完全一致。");
    return;
  }
  if (recBtn === btn) { stopRec(); return; }
  stopRec();

  const target = $(btn.dataset.micTarget);
  recognizer = new SR();
  recognizer.lang = "zh-CN";
  recognizer.continuous = true;
  recognizer.interimResults = false;
  recBtn = btn; recTarget = target;
  btn.classList.add("recording"); btn.textContent = "⏹";
  target.placeholder = "正在聆听…再次点击 🎤 结束，识别文字将追加到输入框";

  recognizer.onresult = (e) => {
    for (let i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) {
        const text = e.results[i][0].transcript.trim();
        if (text) target.value = (target.value ? target.value.replace(/\s+$/, "") + " " : "") + text;
      }
    }
  };
  recognizer.onerror = (e) => {
    if (e.error === "not-allowed") alert("未获得麦克风权限，请在浏览器地址栏允许使用麦克风。");
  };
  recognizer.onend = () => {
    if (recBtn) { recBtn.classList.remove("recording"); recBtn.textContent = "🎤"; }
    recBtn = null; recognizer = null;
  };
  try { recognizer.start(); } catch (e) { recognizer.onend(); }
}

/* ==================== 番茄钟 ==================== */
const pomo = { total: 25 * 60, remain: 25 * 60, endAt: 0, timer: null, running: false, startedAt: "" };

function pomoRender() {
  const m = String(Math.floor(pomo.remain / 60)).padStart(2, "0");
  const s = String(pomo.remain % 60).padStart(2, "0");
  $("pomoTime").textContent = `${m}:${s}`;
  $("pomoTime").classList.toggle("running", pomo.running);
  const done = pomo.total - pomo.remain;
  $("pomoProgress").style.width = (pomo.total ? (done * 100 / pomo.total) : 0) + "%";
}

function pomoSetMinutes(min) {
  if (pomo.running) return;
  pomo.total = pomo.remain = Math.max(1, Math.min(180, min)) * 60;
  pomoRender();
}

function pomoTick() {
  pomo.remain = Math.max(0, Math.round((pomo.endAt - Date.now()) / 1000));
  pomoRender();
  if (pomo.remain <= 0) pomoFinish();
}

async function pomoStart() {
  if (pomo.running) return;
  if (pomo.remain <= 0) pomoSetMinutes(Number($("pomoCustom").value) || 25);
  pomo.running = true;
  if (!pomo.startedAt) pomo.startedAt = new Date().toISOString();
  pomo.endAt = Date.now() + pomo.remain * 1000;
  pomo.timer = setInterval(pomoTick, 1000);
  $("pomoStart").disabled = true; $("pomoPause").disabled = false;
  $("pomoState").textContent = "专注中…保持节奏，远离手机";
  const r = await api("/api/focus/state", {
    method: "POST",
    body: JSON.stringify({ active: true, minutes: Math.round(pomo.total / 60) }),
  });
  if (r.pushed && r.pushed.sent) $("pomoState").textContent += "（ESP32 专注灯已点亮）";
  pomoRender();
}

function pomoPause() {
  if (!pomo.running) return;
  clearInterval(pomo.timer); pomo.running = false;
  pomo.remain = Math.max(0, Math.round((pomo.endAt - Date.now()) / 1000));
  $("pomoStart").disabled = false; $("pomoPause").disabled = true;
  $("pomoState").textContent = "已暂停，点击「开始专注」继续";
  pomoRender();
}

function pomoReset() {
  clearInterval(pomo.timer); pomo.running = false; pomo.startedAt = "";
  $("pomoStart").disabled = false; $("pomoPause").disabled = true;
  $("pomoState").textContent = "准备开始一段专注时光";
  api("/api/focus/state", { method: "POST", body: JSON.stringify({ active: false, minutes: 0 }) });
  pomoSetMinutes(Number($("pomoCustom").value) || 25);
}

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    [0, 0.25, 0.5].forEach((t) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.connect(g); g.connect(ctx.destination);
      o.frequency.value = 880; g.gain.value = 0.08;
      o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.18);
    });
  } catch (e) {}
}

async function pomoFinish() {
  clearInterval(pomo.timer); pomo.running = false;
  beep();
  const minutes = Math.round(pomo.total / 60);
  $("pomoState").textContent = `🎉 完成 ${minutes} 分钟专注！已记录，休息一下吧`;
  $("pomoStart").disabled = false; $("pomoPause").disabled = true;
  await api("/api/focus/sessions", {
    method: "POST",
    body: JSON.stringify({
      minutes, course_id: currentCourseId, note: "番茄钟专注",
      started_at: pomo.startedAt, ended_at: new Date().toISOString(),
    }),
  });
  pomo.startedAt = "";
  pomoSetMinutes(Number($("pomoCustom").value) || 25);
  loadOverview();
}

/* ==================== 学习概览 ==================== */
async function loadOverview() {
  const d = await api("/api/overview");
  if (!d || d.error || !Array.isArray(d.recent_sessions)) {
    $("statCards").innerHTML = "<div class='card'><div class='label'>概览暂不可用</div>" +
      "<div class='sub-num'>接口加载失败，其余功能仍可正常使用</div></div>";
    return;
  }
  const cards = [
    { num: d.courses, label: "课程", sub: `${d.materials} 份课程资料`, tab: "memory", hint: "点击管理课程与资料" },
    { num: d.wrong_total ? d.mastery_rate + "%" : "暂无", label: "错题掌握率",
      sub: d.wrong_total ? `${d.wrong_mastered}/${d.wrong_total} 已掌握 · ${d.wrong_unmastered} 待攻克` : "还没有错题记录",
      tab: "wrong", hint: "点击进入错题本" },
    { num: d.focus_today_minutes + " 分钟", label: "今日专注", sub: `累计 ${d.focus_total_minutes} 分钟 / ${d.focus_count} 次`, tab: "", hint: "用下方番茄钟记录专注" },
    { num: d.pending_tasks, label: "待复习任务", sub: "到点自动推送 ESP32 提醒", tab: "dashboard", focus: "quickTask", hint: "点击此处添加一条待复习任务" },
  ];
  $("statCards").innerHTML = cards.map((c) =>
    `<div class="card${c.tab ? " clickable" : ""}" data-tab="${c.tab || ""}" data-focus="${c.focus || ""}"
      ${c.tab ? 'tabindex="0" role="button"' : ""} title="${esc(c.hint || c.sub)}">
      <div class="num">${esc(c.num)}</div><div class="label">${esc(c.label)}</div><div class="sub-num">${esc(c.sub)}</div>
    </div>`
  ).join("");
  const activateCard = (el) => {
    if (el.dataset.focus) {
      activateTab(el.dataset.tab || "dashboard");
      const t = $(el.dataset.focus);
      if (t) { t.focus(); if (t.scrollIntoView) t.scrollIntoView({ behavior: "smooth", block: "center" }); }
    } else {
      activateTab(el.dataset.tab);
    }
  };
  $("statCards").querySelectorAll(".card.clickable").forEach((el) => {
    el.onclick = () => activateCard(el);
    // 统计卡片是 div，原生不可聚焦；补键盘激活，纯键盘用户也能跳转
    el.onkeydown = (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); activateCard(el); }
    };
  });

  const ul = $("focusList");
  ul.innerHTML = d.recent_sessions.length ? "" : "<li><div class='meta'>还没有专注记录，用上面的番茄钟开始第一段专注吧。</div></li>";
  d.recent_sessions.forEach((s) => {
    const li = document.createElement("li");
    // 课程名与专注备注均为用户可控文本，必须转义（存储型 XSS）
    li.innerHTML = `<h4>🍅 ${esc(s.minutes)} 分钟 ${s.course_name ? "· " + esc(s.course_name) : ""}</h4>
      <div class="meta">${esc(s.created_at)}${s.note ? " · " + esc(s.note) : ""}</div>`;
    ul.appendChild(li);
  });
  loadQuickTasks();
}

async function loadQuickTasks() {
  const list = await api("/api/review-tasks");
  const ul = $("quickTaskList");
  ul.innerHTML = "";
  const pending = (Array.isArray(list) ? list : []).filter((t) => !t.notified);
  if (!pending.length) {
    ul.innerHTML = "<li><div class='meta'>暂无待复习任务，用上方输入框添加一条吧。</div></li>";
    return;
  }
  pending.forEach((t) => {
    const li = document.createElement("li");
    li.innerHTML = `<h4>${esc(t.task_name)}${t.course_name ? " · " + esc(t.course_name) : ""}</h4>
      <div class="meta">到点：${esc(t.due_time || "未设置")}</div>
      <div class="actions"><button data-done="${t.id}">✓ 标记完成</button></div>`;
    ul.appendChild(li);
  });
  ul.querySelectorAll("button[data-done]").forEach((b) => {
    b.onclick = async () => {
      await api(`/api/review-tasks/${b.dataset.done}/done`, { method: "POST", body: JSON.stringify({}) });
      loadQuickTasks(); loadOverview();
    };
  });
}

/* ==================== 文件上传 ==================== */
async function uploadMaterial(file) {
  if (!currentCourseId) return alert("请先选择课程");
  const fd = new FormData();
  fd.append("file", file);
  $("uploadResult").innerHTML = "正在解析并入库…";
  try {
    const res = await fetch(`/api/courses/${currentCourseId}/materials/upload`, { method: "POST", body: fd });
    let r;
    try { r = await res.json(); }
    catch (e) { throw new Error("响应不是 JSON（HTTP " + res.status + "）"); }
    if (!r || r.error || !res.ok) {
      $("uploadResult").innerHTML = `<span style="color:#d93025">上传失败：${esc((r && r.error) || ("HTTP " + res.status))}</span>`;
      return;
    }
    // 文件名与预览来自用户上传的文件内容，必须转义（存储/反射型 XSS）
    $("uploadResult").innerHTML =
      `<span class="status">✅ 已存入课程记忆：《${esc(r.filename)}》提取 ${esc(r.chars)} 字` +
      `${r.truncated ? "（超长已截断至 2 万字）" : ""}</span><div class="meta">预览：${esc(r.preview)}…</div>`;
    loadMaterials(); loadOverview();
  } catch (e) {
    $("uploadResult").innerHTML = `<span style="color:#d93025">网络异常：${esc(e)}</span>`;
  }
}

function initUpload() {
  const zone = $("uploadZone"), input = $("fileInput");
  // 上传区是 div，原生不可聚焦；补焦点/role/键盘激活，让纯键盘用户也能选文件
  zone.tabIndex = 0;
  zone.setAttribute("role", "button");
  zone.setAttribute("aria-label", "点击或按回车选择课件文件，也可拖拽到此处");
  zone.onclick = () => input.click();
  zone.onkeydown = (e) => {
    if (e.key === "Enter" || e.key === " ") { e.preventDefault(); input.click(); }
  };
  input.onchange = () => { if (input.files[0]) uploadMaterial(input.files[0]); input.value = ""; };
  ["dragover", "dragenter"].forEach((ev) => zone.addEventListener(ev, (e) => {
    e.preventDefault(); zone.classList.add("dragover");
  }));
  ["dragleave", "drop"].forEach((ev) => zone.addEventListener(ev, (e) => {
    e.preventDefault(); zone.classList.remove("dragover");
  }));
  zone.addEventListener("drop", (e) => {
    const f = e.dataTransfer.files[0];
    if (f) uploadMaterial(f);
  });
}

/* ==================== 学习资源包 ==================== */
let lastSvg = "", lastOutline = "";
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

/* ==================== 轻量 Markdown 渲染（escape-first，杜绝 XSS） ====================
 * 仅支持「演示模式 / 大模型」实际产出的子集：标题、粗体、斜体、行内代码、
 * 代码块、引用、有序/无序列表、分割线、表格、段落。所有文本先转义再格式化，
 * 因此即便模型返回 <script> 等也不会被执行。 */
function mdEscape(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function mdInline(s) {
  // s 已经过 HTML 转义；再叠加行内标记
  s = s.replace(/`([^`]+)`/g, (_, c) => "<code>" + c + "</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/\*([^*]+)\*/g, "<em>$1</em>");
  return s;
}
function renderMarkdown(src) {
  if (src == null) return "";
  const lines = String(src).replace(/\r\n/g, "\n").split("\n");
  const codes = [];
  const out = [];
  // 先抽离围栏代码块，避免块内内容被当成其它语法
  for (let i = 0; i < lines.length; i++) {
    if (/^```/.test(lines[i])) {
      const buf = [];
      i++;
      while (i < lines.length && !/^```\s*$/.test(lines[i])) { buf.push(lines[i]); i++; }
      codes.push(mdEscape(buf.join("\n")));
      out.push(" CODE" + (codes.length - 1) + " ");
    } else {
      out.push(lines[i]);
    }
  }
  const isRow = (l) => /^\|.*\|\s*$/.test(l);
  const parseCells = (l) => l.split("|").slice(1, -1).map((c) => c.trim());
  const isSep = (cells) => cells.length > 0 && cells.every((c) => /^:?-+:?$/.test(c));

  let html = "", listType = null, para = [], table = null;
  const flushPara = () => { if (para.length) { html += "<p>" + mdInline(mdEscape(para.join(" "))) + "</p>"; para = []; } };
  const flushList = () => { if (listType) { html += "</" + listType + ">"; listType = null; } };
  const flushTable = () => {
    if (table && table.head.length) {
      html += "<table><thead><tr>" + table.head.map((h) => "<th>" + mdInline(mdEscape(h)) + "</th>").join("") +
        "</tr></thead><tbody>" +
        table.rows.map((r) => "<tr>" + r.map((c) => "<td>" + mdInline(mdEscape(c)) + "</td>").join("") + "</tr>").join("") +
        "</tbody></table>";
    }
    table = null;
  };
  const flushAll = () => { flushPara(); flushList(); flushTable(); };

  for (const line of out) {
    if (/^ CODE\d+ $/.test(line)) {
      flushAll();
      const id = parseInt(line.match(/\d+/)[0], 10);
      html += "<pre><code>" + codes[id] + "</code></pre>";
      continue;
    }
    if (!line.trim()) { flushAll(); continue; }
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) { flushAll(); const lv = h[1].length; html += "<h" + lv + ">" + mdInline(mdEscape(h[2])) + "</h" + lv + ">"; continue; }
    if (/^(---|\*\*\*|___)\s*$/.test(line)) { flushAll(); html += "<hr>"; continue; }
    if (/^>\s?/.test(line)) { flushAll(); html += "<blockquote>" + mdInline(mdEscape(line.replace(/^>\s?/, ""))) + "</blockquote>"; continue; }
    if (isRow(line)) {
      const cells = parseCells(line);
      if (isSep(cells)) { if (table && table.pending) { table.head = table.pending; table.pending = null; } continue; }
      if (!table) { table = { pending: cells, head: [], rows: [] }; }
      else if (table.pending && !table.head.length) { table.head = table.pending; table.rows.push(cells); table.pending = null; }
      else { table.rows.push(cells); }
      continue;
    } else { flushTable(); }
    const ul = line.match(/^([•\-*])\s+(.*)$/);
    if (ul) { flushPara(); if (listType !== "ul") { flushList(); html += "<ul>"; listType = "ul"; } html += "<li>" + mdInline(mdEscape(ul[2])) + "</li>"; continue; }
    const ol = line.match(/^\d+\.\s+(.*)$/);
    if (ol) { flushPara(); if (listType !== "ol") { flushList(); html += "<ol>"; listType = "ol"; } html += "<li>" + mdInline(mdEscape(ol[1])) + "</li>"; continue; }
    flushList(); flushTable();
    para.push(line);
  }
  flushAll();
  return html;
}
function setMarkdown(el, md) { if (el) el.innerHTML = renderMarkdown(md); }

function studyParams() {
  return {
    subject: $("studySubject").value.trim() || "高等数学上册",
    chapter: $("studyChapter").value,
    count: Number($("studyCount").value) || 6,
    difficulty: $("studyDifficulty").value,
  };
}

async function loadStudyCatalog() {
  const c = await api("/api/study/catalog");
  const sel = $("studyChapter");
  const chapters = (c && !c.error && Array.isArray(c.chapters)) ? c.chapters : [];
  sel.innerHTML = '<option value="">全部章节（全册）</option>' +
    chapters.map((ch) => `<option value="${esc(ch.id)}">${esc(ch.title)}（${esc(ch.question_count)} 题）</option>`).join("");
}

function renderQuiz(d) {
  const box = $("studyQuizOut");
  if (!d.questions || !d.questions.length) {
    box.innerHTML = "<div class='hint'>该范围暂无题目，试试切换章节或清空难度筛选。</div>";
    return;
  }
  box.innerHTML = d.questions.map((q, i) => `
    <div class="quiz-card">
      <div class="q-head">
        <span class="q-no">#${i + 1}</span>
        <span class="tag">${esc(q.type)}</span>
        <span class="tag down">${esc(q.difficulty)}</span>
        <span class="tag">${q.origin === "llm" ? "模型生成" : "知识库"}</span>
      </div>
      <div class="q-stem">${esc(q.stem)}</div>
      <div class="q-meta">章节：${esc(q.chapter)} ｜ 考点：${esc((q.points || []).join("、")) || "—"}</div>
      <details><summary>查看答案与解析</summary>
        <p><b>答案：</b>${esc(q.answer)}</p>
        <p><b>解析：</b>${esc(q.analysis)}</p>
      </details>
    </div>`).join("");
}

function renderResources(d) {
  // 接口异常时 d 可能是 {error}；链接只放行 http(s)/站内路径，挡掉 javascript: 等协议
  const items = (d && Array.isArray(d.items)) ? d.items : [];
  const count = (d && d.count != null) ? d.count : items.length;
  $("studyResourcesOut").innerHTML =
    `<h4>资料清单（${esc(count)} 项）</h4>` +
    (items.length ? items.map((r) => {
      const raw = String(r.url || "");
      const safe = /^(https?:\/\/|\/)/i.test(raw) ? raw : "";
      const link = safe
        ? `<a href="${esc(safe)}" target="_blank" rel="noopener noreferrer">${esc(raw)}</a>`
        : `<span class="meta">${esc(raw || "无链接")}</span>`;
      return `<div class="res-item">
      <div class="r-title">${esc(r.title)} <span class="tag">${esc(r.kind)}</span></div>
      <div class="r-desc">${esc(r.desc)}</div>
      ${link}
    </div>`;
    }).join("") : "<div class='hint'>资料清单暂不可用，请重试。</div>");
}

function renderMindmap(d) {
  lastSvg = d.svg || ""; lastOutline = d.outline || "";
  $("studyMindmapOut").innerHTML = lastSvg || "<div class='hint'>未生成思维导图。</div>";
}

function renderPack(r) {
  if (!r || r.error || !r.quiz || !r.summary || !r.article || !r.resources || !r.mindmap) {
    $("studyMeta").textContent = "资源包数据不完整，请重试或缩小章节范围";
    return;
  }
  renderQuiz(r.quiz);
  setMarkdown($("studySummaryOut"), r.summary.markdown);
  setMarkdown($("studyArticleOut"), r.article.markdown);
  renderResources(r.resources);
  renderMindmap(r.mindmap);
  let meta =
    `《${r.subject}》· ${r.scope} · ${(r.chapters || []).length} 个章节 ｜ 题目 ${r.quiz.count} 道 ｜ 总结 ${r.summary.markdown.length} 字 ｜ 文章 ${r.article.chars} 字 ｜ 资料 ${r.resources.count} 项 ｜ 导图 ${r.mindmap.node_count} 节点 ｜ 智能体：${r.provider} ｜ 来源：${r.quiz.source}` +
    (r.saved && r.saved.ok ? ` ｜ 已存入课程记忆（课程 #${r.saved.course_id}）` : "");
  if (r.discipline && r.discipline === "自定义科目") {
    meta += " ｜ ⚠️ 未内置《" + r.subject + "》专用知识库，已用通用模板；接入文心一言/Kimi 等真实模型可结合课件深度生成";
  }
  $("studyMeta").textContent = meta;
}

async function doStudyPack() {
  studyBusy(true, "正在生成全套资源（题目 / 总结 / 文章 / 资料 / 导图）…");
  try {
    const p = studyParams();
    const r = await api("/api/study/pack", {
      method: "POST",
      body: JSON.stringify({ ...p, save_to_course: $("studySave").checked }),
    });
    if (r.error) { $("studyMeta").textContent = "生成失败：" + r.error; return; }
    renderPack(r);
  } catch (e) {
    $("studyMeta").textContent = "生成失败：" + e;
  } finally {
    studyBusy(false);
  }
}

function studyBusy(on, msg) {
  ["studyPack", "studyQuiz", "studySummary", "studyArticle", "studyMindmap"].forEach((id) => {
    const b = $(id); if (b) b.disabled = on;
  });
  if (on) $("studyMeta").textContent = msg || "正在生成，请稍候…";
}

function subjectHintText(r) {
  if (r && r.discipline && r.discipline === "自定义科目") {
    return " ｜ ⚠️ 未内置《" + (r.subject || "该科目") + "》专用知识库，已用通用模板；接入真实模型可结合课件生成";
  }
  return "";
}

function bindStudy() {
  $("studyPack").onclick = doStudyPack;
  $("studyQuiz").onclick = async () => {
    studyBusy(true, "正在生成自测题…");
    try {
      const r = await api("/api/study/quiz", { method: "POST", body: JSON.stringify(studyParams()) });
      if (r.error) { $("studyMeta").textContent = "生成失败：" + r.error; return; }
      renderQuiz(r);
      $("studyMeta").textContent = `《${r.subject}》${r.scope}：已生成 ${r.count} 道题（来源 ${r.source}）` + subjectHintText(r);
    } finally { studyBusy(false); }
  };
  $("studySummary").onclick = async () => {
    studyBusy(true, "正在生成复习总结…");
    try {
      const r = await api("/api/study/summary", { method: "POST", body: JSON.stringify(studyParams()) });
      if (r.error) { $("studyMeta").textContent = "生成失败：" + r.error; return; }
      setMarkdown($("studySummaryOut"), r.markdown);
      $("studyMeta").textContent = `总结已生成：${r.chapter_count} 章 / ${r.markdown.length} 字（${r.source}）` + subjectHintText(r);
    } finally { studyBusy(false); }
  };
  $("studyArticle").onclick = async () => {
    studyBusy(true, "正在生成专题文章与资料…");
    try {
      const p = studyParams();
      const [a, res] = await Promise.all([
        api("/api/study/article", { method: "POST", body: JSON.stringify(p) }),
        api("/api/study/resources", { method: "POST", body: JSON.stringify(p) }),
      ]);
      // 两个请求彼此独立：任一失败都应给出明确结果，而不是抛未捕获异常
      // 让 studyMeta 永久停在「正在生成…」
      if (a && !a.error && a.markdown) setMarkdown($("studyArticleOut"), a.markdown);
      renderResources(res);
      const articleOk = !!(a && !a.error && a.markdown);
      const resCount = (res && !res.error && res.count != null) ? res.count : 0;
      $("studyMeta").textContent = articleOk
        ? `专题文章 ${a.chars || a.markdown.length} 字 / ${a.sections || "—"} 个章节段落，资料 ${resCount} 项已生成` + subjectHintText(a)
        : "生成失败：" + ((a && a.error) || "文章接口未返回内容") +
          (res && res.error ? "；资料清单也未生成" : "");
    } catch (e) {
      $("studyMeta").textContent = "生成失败：" + e;
    } finally { studyBusy(false); }
  };
  $("studyMindmap").onclick = async () => {
    studyBusy(true, "正在生成思维导图…");
    try {
      const r = await api("/api/study/mindmap", { method: "POST", body: JSON.stringify(studyParams()) });
      if (r.error) { $("studyMeta").textContent = "生成失败：" + r.error; return; }
      renderMindmap(r);
      $("studyMeta").textContent = `思维导图：${r.chapter_count} 章 / ${r.node_count} 节点（${r.source}）` + subjectHintText(r);
    } finally { studyBusy(false); }
  };
  $("studyExport").onclick = () => {
    downloadFromUrl("/api/study/pack/export?" + new URLSearchParams(studyParams()).toString(),
                    "学习资源包.md");
  };
  $("studyOutline").onclick = () => {
    $("studyMindmapOut").innerHTML = lastOutline
      ? "<pre class='out' style='white-space:pre-wrap'>" + esc(lastOutline) + "</pre>"
      : "<div class='hint'>请先生成思维导图。</div>";
  };
  $("studySvgDownload").onclick = () => {
    if (!lastSvg) return alert("请先生成思维导图");
    const blob = new Blob([lastSvg], { type: "image/svg+xml;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "高等数学上册-思维导图.svg";
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 1500);
  };
}

/* ==================== 模型接入（文心一言 / Kimi / 自定义） ==================== */
function agentPayload() {
  const payload = { provider: $("agentProvider").value };
  [["api_key", "agentKey"], ["secret_key", "agentSecret"], ["model", "agentModel"],
   ["base_url", "agentBaseUrl"], ["token_url", "agentTokenUrl"]].forEach(([k, id]) => {
    const v = $(id).value.trim();
    if (v) payload[k] = v;
  });
  return payload;
}

function agentLog(title, r) {
  $("agentStatus").textContent = title + "\n" + JSON.stringify(r, null, 2);
}

function bindAgent() {
  $("agentProvider").onchange = () => {
    const p = $("agentProvider").value;
    $("agentModel").placeholder = p === "qianfan" ? "默认 ernie-3.5-8k（v2 可填 ernie-4.5-8k）"
      : p === "moonshot" ? "默认 moonshot-v1-8k" : p === "custom" ? "必填，如 qwen-plus / llama3"
      : p === "openai" ? "默认 gpt-3.5-turbo" : "默认 claude-3-5-sonnet-20241022";
    $("agentBaseUrl").placeholder = p === "custom" ? "必填，如 http://localhost:11434/v1/chat/completions"
      : p === "qianfan" ? "可选；填千帆 v2 地址则只需 API Key" : "可选，留空使用官方地址";
  };
  $("agentSave").onclick = async () => {
    const r = await api("/api/agent/credentials", {
      method: "POST", body: JSON.stringify({ ...agentPayload(), activate: true }),
    });
    agentLog("保存结果：", r);
    if (r.ok) {
      $("agentKey").value = ""; $("agentSecret").value = "";
      await loadStatus(); await loadProviders();
    }
  };
  $("agentValidate").onclick = async () => {
    const r = await api("/api/agent/test", {
      method: "POST", body: JSON.stringify({ provider: $("agentProvider").value, mode: "validate" }),
    });
    agentLog("配置校验（不联网）：", r);
  };
  $("agentTest").onclick = async () => {
    $("agentStatus").textContent = "正在连接模型，请稍候…";
    const r = await api("/api/agent/test", {
      method: "POST", body: JSON.stringify({ provider: $("agentProvider").value, mode: "probe" }),
    });
    agentLog("连通性测试结果：", r);
  };
  $("agentClear").onclick = async () => {
    const r = await api("/api/agent/credentials/clear", {
      method: "POST", body: JSON.stringify({ provider: $("agentProvider").value }),
    });
    agentLog("已清除运行时配置：", r);
    ["agentKey", "agentSecret", "agentModel", "agentBaseUrl", "agentTokenUrl"].forEach((id) => { $(id).value = ""; });
    await loadStatus(); await loadProviders();
  };
}

/* ==================== 初始化 ==================== */
async function init() {
  initTheme();
  // 关键顺序：先完成所有交互绑定，再发起任何网络请求。
  // 原实现把 bindEvents 放在一长串 await 之后，任意一个接口异常就会抛出
  // 并中断 init()，导致标签、按钮、上传、番茄钟全部失效（整页变砖）。
  bindEvents();
  bindStudy();
  bindAgent();
  initUpload();
  pomoRender();
  document.querySelectorAll(".mic-btn").forEach((b) => { b.onclick = () => toggleMic(b); });

  // 单个模块加载失败只降级该模块，不影响其余模块与已绑定的交互。
  const safe = async (name, fn) => {
    try { await fn(); }
    catch (e) { console.warn("[init] " + name + " 加载失败，已降级", e); }
  };
  await safe("状态", loadStatus);
  await safe("课程", loadCourses);   // 必须先取课程，后续模块依赖 currentCourseId
  await safe("课程资料", loadMaterials);
  await safe("错题本", loadWrongQuestions);
  await safe("模型接入", loadProviders);
  await safe("资源包目录", loadStudyCatalog);
  await safe("学习概览", loadOverview);
  safe("硬件状态", loadHardwareStatus);

  const autoPack = new URLSearchParams(location.search).get("autopack") === "1";
  const hash = location.hash.slice(1);
  if (hash && $("panel-" + hash)) activateTab(hash);
  // 答辩/验收快捷入口：/?autopack=1 打开即自动生成「高等数学上册」全套资源
  if (autoPack) { activateTab("study"); doStudyPack(); }
}

function activateTab(name) {
  const t = document.querySelector(`.tab[data-tab="${name}"]`);
  if (!t) return;
  stopRec();
  document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
  document.querySelectorAll(".panel").forEach((x) => x.classList.remove("active"));
  t.classList.add("active");
  $("panel-" + name).classList.add("active");
  if (history.replaceState) history.replaceState(null, "", "#" + name);
  if (name === "dashboard") loadOverview();
  if (name === "hardware") loadHardwareStatus();
  if (name === "settings") loadProviders();
}

async function loadStatus() {
  const s = await api("/api/status");
  if (!s || s.error || !Array.isArray(s.providers)) {
    $("providerBadge").textContent = "智能体：状态不可用";
    return;
  }
  const active = s.providers.find((p) => p.active);
  $("providerBadge").textContent = "智能体：" + (active ? active.label : "演示模式");
}

async function loadCourses() {
  const list = await api("/api/courses");
  const sel = $("courseSelect");
  const prev = currentCourseId;
  sel.innerHTML = "";
  if (!Array.isArray(list)) {
    const o = document.createElement("option");
    o.value = ""; o.textContent = "课程加载失败，请点右侧刷新";
    sel.appendChild(o);
    currentCourseId = null;
    return;
  }
  list.forEach((c) => {
    const o = document.createElement("option");
    o.value = c.id; o.textContent = c.name;
    sel.appendChild(o);
  });
  if (prev && list.some((c) => c.id === prev)) sel.value = prev;
  currentCourseId = sel.value ? Number(sel.value) : null;
}

function bindEvents() {
  document.querySelectorAll(".tab").forEach((t) => {
    t.onclick = () => activateTab(t.dataset.tab);
  });

  $("courseSelect").onchange = () => {
    currentCourseId = Number($("courseSelect").value);
    // 对话历史按课程隔离：不清空会让 A 课程的对话留在 B 课程页面下，
    // 用户会误以为智能体把上一门课的资料也带过来了。
    $("chatBox").innerHTML = "";
    courseLoadSeq++;   // 让切课程前发出的请求在返回时被丢弃
    loadMaterials(); loadWrongQuestions();
  };
  $("refreshCourses").onclick = loadCourses;
  $("newCourseBtn").onclick = async () => {
    const name = (prompt("课程名称：") || "").trim();
    if (!name) return;
    const r = await api("/api/courses", { method: "POST", body: JSON.stringify({ name }) });
    if (!showApiError(r)) return;
    await loadCourses(); await loadOverview();
  };

  $("quickTaskAdd").onclick = async () => {
    const name = $("quickTask").value.trim();
    if (!name) return alert("请先填写任务名");
    const due = $("quickTaskDue").value;
    const r = await api("/api/review-tasks", {
      method: "POST",
      body: JSON.stringify({ course_id: currentCourseId, task_name: name, due_time: due || undefined, fire_now: !due }),
    });
    if (!showApiError(r)) return;
    $("quickTask").value = ""; $("quickTaskDue").value = "";
    loadQuickTasks(); loadOverview();
  };

  $("sendChat").onclick = sendChat;
  $("chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) sendChat();
  });
  $("goModelSetup").onclick = (e) => {
    e.preventDefault();
    activateTab("settings");
    setTimeout(() => $("agentProvider").scrollIntoView({ behavior: "smooth", block: "center" }), 120);
  };

  $("doSummarize").onclick = async () => {
    const btn = $("doSummarize"); btn.disabled = true;
    try {
      const r = await api("/api/summarize", { method: "POST", body: JSON.stringify({ text: $("sumText").value }) });
      setMarkdown($("sumOut"), r.result || r.error);
    } finally { btn.disabled = false; }
  };
  $("doTutor").onclick = async () => {
    const btn = $("doTutor"); btn.disabled = true;
    try {
      const r = await api("/api/tutor", { method: "POST", body: JSON.stringify({ problem: $("tutorText").value }) });
      setMarkdown($("tutorOut"), r.result || r.error);
    } finally { btn.disabled = false; }
  };
  $("doPlan").onclick = async () => {
    const btn = $("doPlan"); btn.disabled = true;
    try {
      const r = await api("/api/review-plan", { method: "POST", body: JSON.stringify({ subject: $("planSubject").value, days: $("planDays").value }) });
      setMarkdown($("planOut"), r.result || r.error);
    } finally { btn.disabled = false; }
  };

  $("addMaterial").onclick = async () => {
    if (!currentCourseId) return alert("请先选择课程");
    const content = $("matContent").value.trim();
    if (!content) return alert("请先填写资料内容");
    const r = await api(`/api/courses/${currentCourseId}/materials`, {
      method: "POST",
      body: JSON.stringify({ title: $("matTitle").value, content }),
    });
    if (!showApiError(r)) return;   // 失败时保留输入，避免用户白打一遍
    $("matContent").value = ""; $("matTitle").value = "";
    loadMaterials(); loadOverview();
  };

  $("addWq").onclick = async () => {
    if (!currentCourseId) return alert("请先选择课程");
    const question = $("wqQuestion").value.trim();
    if (!question) return alert("请先填写错题题目");
    const r = await api("/api/wrong-questions", {
      method: "POST",
      body: JSON.stringify({
        course_id: currentCourseId, question,
        user_answer: $("wqUser").value, correct_answer: $("wqCorrect").value,
      }),
    });
    if (!showApiError(r)) return;
    $("wqQuestion").value = ""; $("wqUser").value = ""; $("wqCorrect").value = "";
    loadWrongQuestions(); loadOverview();
  };
  $("wqFilter").onchange = loadWrongQuestions;
  $("exportWq").onclick = () => {
    const qs = currentCourseId ? `?course_id=${currentCourseId}` : "";
    downloadFromUrl(`/api/wrong-questions/export${qs}`, "AI错题本.md");
  };

  // 番茄钟
  document.querySelectorAll(".pomo-presets .mini").forEach((b) => {
    b.onclick = () => { pomoSetMinutes(Number(b.dataset.min)); $("pomoCustom").value = b.dataset.min; };
  });
  $("pomoCustom").onchange = () => pomoSetMinutes(Number($("pomoCustom").value) || 25);
  $("pomoStart").onclick = pomoStart;
  $("pomoPause").onclick = pomoPause;
  $("pomoReset").onclick = pomoReset;

  // 硬件
  $("addHwTask").onclick = async () => {
    const taskName = $("hwTask").value.trim();
    if (!taskName) return alert("请先填写任务名");
    const r = await api("/api/review-tasks", {
      method: "POST",
      body: JSON.stringify({
        course_id: currentCourseId, task_name: taskName,
        due_time: $("hwDue").value || undefined, fire_now: !$("hwDue").value,
      }),
    });
    if (!showApiError(r)) return;
    $("hwStatus").textContent = "已创建：" + (r.task_name || taskName) +
      "（" + JSON.stringify(r.fired || {}) + "）";
    loadHardwareStatus();
  };
  $("hwTest").onclick = async () => {
    const r = await api("/api/hardware/test", { method: "POST", body: JSON.stringify({ task_name: "测试提醒" }) });
    $("hwStatus").textContent = JSON.stringify(r);
  };
  $("hwFocusOn").onclick = () => setFocusHw(true);
  $("hwFocusOff").onclick = () => setFocusHw(false);
  $("hwRefresh").onclick = loadHardwareStatus;
}

async function setFocusHw(active) {
  const r = await api("/api/focus/state", { method: "POST", body: JSON.stringify({ active, minutes: 25 }) });
  $("hwStatus").textContent = (active ? "专注灯开启：" : "专注灯关闭：") + JSON.stringify(r.pushed || {});
  loadHardwareStatus();
}

async function loadHardwareStatus() {
  const r = await api("/api/hardware/status");
  $("hwBoard").textContent = JSON.stringify(r, null, 2);
}

async function sendChat() {
  if (!currentCourseId) return alert("请先选择课程");
  const msg = $("chatInput").value.trim();
  if (!msg) return;
  const btn = $("sendChat"); btn.disabled = true;
  addMsg("user", msg);
  $("chatInput").value = "";
  try {
    const r = await api("/api/chat", { method: "POST", body: JSON.stringify({ course_id: currentCourseId, message: msg }) });
    addMsg("assistant", r.reply || r.error);
  } finally { btn.disabled = false; }
}

function addMsg(role, text) {
  const box = $("chatBox");
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = `<div class="who">${role === "user" ? "我" : "智能体"}</div><div class="bubble"></div>`;
  div.querySelector(".bubble").innerHTML = renderMarkdown(text);
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function loadMaterials() {
  if (!currentCourseId) { $("matList").innerHTML = ""; return; }
  const seq = courseLoadSeq;
  const list = await api(`/api/courses/${currentCourseId}/materials`);
  if (seq !== courseLoadSeq) return;   // 已切到别的课程，丢弃过期响应
  const ul = $("matList");
  ul.innerHTML = "";
  if (!Array.isArray(list)) {
    ul.innerHTML = "<li><div class='meta'>资料加载失败，请点「刷新课程」重试。</div></li>";
    return;
  }
  if (!list.length) {
    ul.innerHTML = "<li><div class='meta'>暂无资料，可在上方粘贴文本或上传文件。</div></li>";
    return;
  }
  list.forEach((m) => {
    const li = document.createElement("li");
    const fullId = `mat-full-${m.id}`;
    const text = String(m.content == null ? "" : m.content);
    li.innerHTML = `<h4>${esc(m.title || "未命名资料")}</h4><div class="meta">${esc(m.created_at)}</div>
      <div class="meta">${esc(text.slice(0, 120))}${text.length > 120 ? "…" : ""}</div>
      <div class="actions">
        <button data-act="view">查看全文</button>
        <button data-act="download" class="ghost">下载 .md</button>
      </div>
      <div id="${fullId}" class="md mat-full" hidden></div>`;
    ul.appendChild(li);
    // 查看全文 / 收起：复用安全 Markdown 渲染器（先转义，防 XSS）
    const viewBtn = li.querySelector('[data-act="view"]');
    const box = li.querySelector(".mat-full");
    viewBtn.onclick = () => {
      if (box.hidden) {
        setMarkdown(box, text);
        box.hidden = false;
        viewBtn.textContent = "收起";
      } else {
        box.hidden = true;
        viewBtn.textContent = "查看全文";
      }
    };
    li.querySelector('[data-act="download"]').onclick = () => downloadMaterial(m);
  });
}

// 将单份资料导出为 Markdown 文件（标题 + 时间 + 全文）
function downloadMaterial(m) {
  const title = String(m.title || `资料-${m.id}`).replace(/[\\/:*?"<>|]/g, "_");
  const body = `# ${m.title || "未命名资料"}\n\n> 导出时间：${m.created_at}\n\n${m.content || ""}`;
  const blob = new Blob([body], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${title}.md`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(a.href);
}

async function loadWrongQuestions() {
  if (!currentCourseId) { $("wqList").innerHTML = ""; return; }
  const seq = courseLoadSeq;
  const filter = $("wqFilter").value;
  const list = await api(`/api/wrong-questions?course_id=${currentCourseId}${filter === "unmastered" ? "&unmastered=1" : ""}`);
  if (seq !== courseLoadSeq) return;   // 丢弃切课程前的过期响应
  const ul = $("wqList");
  if (!Array.isArray(list)) {
    ul.innerHTML = "<li><div class='meta'>错题加载失败，请点「刷新课程」重试。</div></li>";
    return;
  }
  const shown = filter === "mastered" ? list.filter((w) => w.mastered) : list;
  ul.innerHTML = shown.length ? "" : "<li><div class='meta'>该筛选下暂无错题。</div></li>";
  shown.forEach((w) => {
    const li = document.createElement("li");
    // 题目由用户录入并落库，未转义会造成存储型 XSS（已在真实浏览器复现）
    li.innerHTML = `<h4>错题 #${esc(w.id)}${w.mastered ? " ✅已掌握" : ""}</h4>
      <div class="meta">${esc(w.created_at)}</div>
      <div class="meta">${esc(String(w.question == null ? "" : w.question).slice(0, 160))}</div>
      <div class="actions">
        <button data-act="analyze" data-id="${w.id}">分析错因+出变式题</button>
        <button data-act="master" data-id="${w.id}">标记掌握</button>
      </div>`;
    ul.appendChild(li);
  });
  ul.querySelectorAll("button").forEach((b) => {
    b.onclick = async () => {
      const id = b.dataset.id;
      if (b.dataset.act === "analyze") {
        const r = await api(`/api/wrong-questions/${id}/analyze`, { method: "POST", body: JSON.stringify({}) });
        const pre = document.createElement("pre");
        pre.textContent = "错因分析：\n" + (r.error_reason || "") + "\n\n定向变式题：\n" + (r.variant || r.error);
        b.parentElement.parentElement.appendChild(pre);
      } else {
        await api(`/api/wrong-questions/${id}/master`, { method: "POST", body: JSON.stringify({ mastered: true }) });
        loadWrongQuestions(); loadOverview();
      }
    };
  });
}

async function loadProviders() {
  const d = await api("/api/agent/providers");
  const ul = $("providerList");
  ul.innerHTML = "";
  if (!d || d.error || !Array.isArray(d.providers)) {
    ul.innerHTML = "<li><div class='meta'>模型接入状态加载失败，设置页暂不可用。</div></li>";
    return;
  }
  d.providers.forEach((p) => {
    const li = document.createElement("li");
    const masked = (p.masked && p.masked.api_key) ? " ｜ Key " + p.masked.api_key : "";
    li.innerHTML = `<h4>${esc(p.label)} ${p.active ? "· 当前" : ""}</h4>
      <div class="meta">${p.configured ? "✅ 已配置，可用真实模型" : "⚠️ 未配置，使用内置演示模式"}
        ｜ 来源 ${esc(p.source)} ｜ 模型 ${esc(p.model || "—")}${esc(masked)}</div>
      ${p.hint ? `<div class="meta">${esc(p.hint)}</div>` : ""}
      <div class="actions">
        <button data-cfg="${p.name}">配置</button>
        ${p.active ? "" : `<button data-name="${p.name}">切换为当前</button>`}
        ${p.name === "demo" ? "" : `<button data-probe="${p.name}">连通性测试</button>`}
      </div>`;
    ul.appendChild(li);
  });
  ul.querySelectorAll("button").forEach((b) => {
    b.onclick = async () => {
      if (b.dataset.cfg) {
        $("agentProvider").value = b.dataset.cfg;
        $("agentProvider").onchange();
        activateTab("settings");
        $("agentProvider").scrollIntoView({ behavior: "smooth", block: "center" });
      } else if (b.dataset.name) {
        await api("/api/settings/provider", { method: "POST", body: JSON.stringify({ name: b.dataset.name }) });
        loadStatus(); loadProviders();
      } else if (b.dataset.probe) {
        const r = await api("/api/agent/test", {
          method: "POST", body: JSON.stringify({ provider: b.dataset.probe, mode: "probe" }),
        });
        agentLog("连通性测试 · " + b.dataset.probe + "：", r);
      }
    };
  });
}

init();
