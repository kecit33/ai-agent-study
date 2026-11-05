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
  try {
    return await res.json();
  } catch (e) {
    console.warn("[api] 响应不是 JSON", url, res.status);
    return { error: "响应解析失败（HTTP " + res.status + "）" };
  }
};

let currentCourseId = null;

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
  const cards = [
    { num: d.courses, label: "课程", sub: `${d.materials} 份课程资料`, tab: "memory", hint: "点击管理课程与资料" },
    { num: d.mastery_rate + "%", label: "错题掌握率", sub: `${d.wrong_mastered}/${d.wrong_total} 已掌握 · ${d.wrong_unmastered} 待攻克`, tab: "wrong", hint: "点击进入错题本" },
    { num: d.focus_today_minutes + " 分钟", label: "今日专注", sub: `累计 ${d.focus_total_minutes} 分钟 / ${d.focus_count} 次`, tab: "", hint: "用下方番茄钟记录专注" },
    { num: d.pending_tasks, label: "待复习任务", sub: "到点自动推送 ESP32 提醒", tab: "hardware", hint: "点击查看硬件联动" },
  ];
  $("statCards").innerHTML = cards.map((c) =>
    `<div class="card${c.tab ? " clickable" : ""}" data-tab="${c.tab}" title="${c.hint || c.sub}">
      <div class="num">${c.num}</div><div class="label">${c.label}</div><div class="sub-num">${c.sub}</div>
    </div>`
  ).join("");
  $("statCards").querySelectorAll(".card.clickable").forEach((el) => {
    el.onclick = () => activateTab(el.dataset.tab);
  });

  const ul = $("focusList");
  ul.innerHTML = d.recent_sessions.length ? "" : "<li><div class='meta'>还没有专注记录，用上面的番茄钟开始第一段专注吧。</div></li>";
  d.recent_sessions.forEach((s) => {
    const li = document.createElement("li");
    li.innerHTML = `<h4>🍅 ${s.minutes} 分钟 ${s.course_name ? "· " + s.course_name : ""}</h4>
      <div class="meta">${s.created_at}${s.note ? " · " + s.note : ""}</div>`;
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
      <div class="meta">到点：${t.due_time || "未设置"}</div>
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
    const r = await res.json();
    if (r.error) {
      $("uploadResult").innerHTML = `<span style="color:#d93025">上传失败：${r.error}</span>`;
      return;
    }
    $("uploadResult").innerHTML =
      `<span class="status">✅ 已存入课程记忆：《${r.filename}》提取 ${r.chars} 字` +
      `${r.truncated ? "（超长已截断至 2 万字）" : ""}</span><div class="meta">预览：${r.preview}…</div>`;
    loadMaterials(); loadOverview();
  } catch (e) {
    $("uploadResult").innerHTML = `<span style="color:#d93025">网络异常：${e}</span>`;
  }
}

function initUpload() {
  const zone = $("uploadZone"), input = $("fileInput");
  zone.onclick = () => input.click();
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
  sel.innerHTML = '<option value="">全部章节（全册）</option>' +
    c.chapters.map((ch) => `<option value="${esc(ch.id)}">${esc(ch.title)}（${ch.question_count} 题）</option>`).join("");
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
  $("studyResourcesOut").innerHTML =
    `<h4>资料清单（${d.count} 项）</h4>` +
    d.items.map((r) => `<div class="res-item">
      <div class="r-title">${esc(r.title)} <span class="tag">${esc(r.kind)}</span></div>
      <div class="r-desc">${esc(r.desc)}</div>
      <a href="${esc(r.url)}" target="_blank" rel="noopener noreferrer">${esc(r.url)}</a>
    </div>`).join("");
}

function renderMindmap(d) {
  lastSvg = d.svg || ""; lastOutline = d.outline || "";
  $("studyMindmapOut").innerHTML = lastSvg || "<div class='hint'>未生成思维导图。</div>";
}

function renderPack(r) {
  renderQuiz(r.quiz);
  $("studySummaryOut").textContent = r.summary.markdown;
  $("studyArticleOut").textContent = r.article.markdown;
  renderResources(r.resources);
  renderMindmap(r.mindmap);
  $("studyMeta").textContent =
    `《${r.subject}》· ${r.scope} · ${r.chapters.length} 个章节 ｜ 题目 ${r.quiz.count} 道 ｜ 总结 ${r.summary.markdown.length} 字 ｜ 文章 ${r.article.chars} 字 ｜ 资料 ${r.resources.count} 项 ｜ 导图 ${r.mindmap.node_count} 节点 ｜ 智能体：${r.provider} ｜ 来源：${r.quiz.source}` +
    (r.saved && r.saved.ok ? ` ｜ 已存入课程记忆（课程 #${r.saved.course_id}）` : "");
}

async function doStudyPack() {
  $("studyMeta").textContent = "正在生成全套资源（题目 / 总结 / 文章 / 资料 / 导图）…";
  const p = studyParams();
  const r = await api("/api/study/pack", {
    method: "POST",
    body: JSON.stringify({ ...p, save_to_course: $("studySave").checked }),
  });
  if (r.error) { $("studyMeta").textContent = "生成失败：" + r.error; return; }
  renderPack(r);
}

function bindStudy() {
  $("studyPack").onclick = doStudyPack;
  $("studyQuiz").onclick = async () => {
    const r = await api("/api/study/quiz", { method: "POST", body: JSON.stringify(studyParams()) });
    renderQuiz(r);
    $("studyMeta").textContent = `《${r.subject}》${r.scope}：已生成 ${r.count} 道题（来源 ${r.source}）`;
  };
  $("studySummary").onclick = async () => {
    const r = await api("/api/study/summary", { method: "POST", body: JSON.stringify(studyParams()) });
    $("studySummaryOut").textContent = r.markdown;
    $("studyMeta").textContent = `总结已生成：${r.chapter_count} 章 / ${r.markdown.length} 字（${r.source}）`;
  };
  $("studyArticle").onclick = async () => {
    const p = studyParams();
    const [a, res] = await Promise.all([
      api("/api/study/article", { method: "POST", body: JSON.stringify(p) }),
      api("/api/study/resources", { method: "POST", body: JSON.stringify(p) }),
    ]);
    $("studyArticleOut").textContent = a.markdown;
    renderResources(res);
    $("studyMeta").textContent = `专题文章 ${a.chars} 字 / ${a.sections} 个章节段落，资料 ${res.count} 项已生成`;
  };
  $("studyMindmap").onclick = async () => {
    const r = await api("/api/study/mindmap", { method: "POST", body: JSON.stringify(studyParams()) });
    renderMindmap(r);
    $("studyMeta").textContent = `思维导图：${r.chapter_count} 章 / ${r.node_count} 节点（${r.source}）`;
  };
  $("studyExport").onclick = () => {
    window.location.href = "/api/study/pack/export?" + new URLSearchParams(studyParams()).toString();
  };
  $("studyOutline").onclick = () => {
    $("studyMindmapOut").innerHTML = lastOutline
      ? "<pre class='out' style='white-space:pre-wrap'>" + esc(lastOutline) + "</pre>"
      : "<div class='hint'>请先生成思维导图。</div>";
    if (lastSvg) setTimeout(() => { /* 保留 SVG 供下载 */ }, 0);
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
  await loadStatus();
  await loadCourses();
  await loadMaterials();
  await loadWrongQuestions();
  await loadProviders();
  await loadStudyCatalog();
  await loadOverview();
  loadHardwareStatus();
  bindEvents();
  bindStudy();
  bindAgent();
  initUpload();
  pomoRender();
  document.querySelectorAll(".mic-btn").forEach((b) => { b.onclick = () => toggleMic(b); });
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
  const active = s.providers.find((p) => p.active);
  $("providerBadge").textContent = "智能体：" + (active ? active.label : "演示模式");
}

async function loadCourses() {
  const list = await api("/api/courses");
  const sel = $("courseSelect");
  const prev = currentCourseId;
  sel.innerHTML = "";
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
    loadMaterials(); loadWrongQuestions();
  };
  $("refreshCourses").onclick = loadCourses;
  $("newCourseBtn").onclick = async () => {
    const name = prompt("课程名称：");
    if (!name) return;
    await api("/api/courses", { method: "POST", body: JSON.stringify({ name }) });
    await loadCourses(); await loadOverview();
  };

  $("quickTaskAdd").onclick = async () => {
    const name = $("quickTask").value.trim();
    if (!name) return alert("请先填写任务名");
    const due = $("quickTaskDue").value;
    await api("/api/review-tasks", {
      method: "POST",
      body: JSON.stringify({ course_id: currentCourseId, task_name: name, due_time: due || undefined, fire_now: !due }),
    });
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
    const r = await api("/api/summarize", { method: "POST", body: JSON.stringify({ text: $("sumText").value }) });
    $("sumOut").textContent = r.result || r.error;
  };
  $("doTutor").onclick = async () => {
    const r = await api("/api/tutor", { method: "POST", body: JSON.stringify({ problem: $("tutorText").value }) });
    $("tutorOut").textContent = r.result || r.error;
  };
  $("doPlan").onclick = async () => {
    const r = await api("/api/review-plan", { method: "POST", body: JSON.stringify({ subject: $("planSubject").value, days: $("planDays").value }) });
    $("planOut").textContent = r.result || r.error;
  };

  $("addMaterial").onclick = async () => {
    if (!currentCourseId) return alert("请先选择课程");
    await api(`/api/courses/${currentCourseId}/materials`, {
      method: "POST",
      body: JSON.stringify({ title: $("matTitle").value, content: $("matContent").value }),
    });
    $("matContent").value = ""; $("matTitle").value = "";
    loadMaterials(); loadOverview();
  };

  $("addWq").onclick = async () => {
    if (!currentCourseId) return alert("请先选择课程");
    await api("/api/wrong-questions", {
      method: "POST",
      body: JSON.stringify({
        course_id: currentCourseId, question: $("wqQuestion").value,
        user_answer: $("wqUser").value, correct_answer: $("wqCorrect").value,
      }),
    });
    $("wqQuestion").value = ""; $("wqUser").value = ""; $("wqCorrect").value = "";
    loadWrongQuestions(); loadOverview();
  };
  $("wqFilter").onchange = loadWrongQuestions;
  $("exportWq").onclick = () => {
    const qs = currentCourseId ? `?course_id=${currentCourseId}` : "";
    window.location.href = `/api/wrong-questions/export${qs}`;
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
    const r = await api("/api/review-tasks", {
      method: "POST",
      body: JSON.stringify({
        course_id: currentCourseId, task_name: $("hwTask").value,
        due_time: $("hwDue").value || undefined, fire_now: !$("hwDue").value,
      }),
    });
    $("hwStatus").textContent = "已创建：" + JSON.stringify(r.fired || {});
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
  addMsg("user", msg);
  $("chatInput").value = "";
  const r = await api("/api/chat", { method: "POST", body: JSON.stringify({ course_id: currentCourseId, message: msg }) });
  addMsg("assistant", r.reply || r.error);
}

function addMsg(role, text) {
  const box = $("chatBox");
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.innerHTML = `<div class="who">${role === "user" ? "我" : "智能体"}</div><div class="bubble"></div>`;
  div.querySelector(".bubble").textContent = text;
  box.appendChild(div);
  box.scrollTop = box.scrollHeight;
}

async function loadMaterials() {
  if (!currentCourseId) { $("matList").innerHTML = ""; return; }
  const list = await api(`/api/courses/${currentCourseId}/materials`);
  const ul = $("matList");
  ul.innerHTML = "";
  list.forEach((m) => {
    const li = document.createElement("li");
    li.innerHTML = `<h4>${m.title || "未命名资料"}</h4><div class="meta">${m.created_at}</div>
      <div class="meta">${String(m.content).slice(0, 120)}…</div>`;
    ul.appendChild(li);
  });
}

async function loadWrongQuestions() {
  if (!currentCourseId) { $("wqList").innerHTML = ""; return; }
  const filter = $("wqFilter").value;
  const list = await api(`/api/wrong-questions?course_id=${currentCourseId}${filter === "unmastered" ? "&unmastered=1" : ""}`);
  const shown = filter === "mastered" ? list.filter((w) => w.mastered) : list;
  const ul = $("wqList");
  ul.innerHTML = shown.length ? "" : "<li><div class='meta'>该筛选下暂无错题。</div></li>";
  shown.forEach((w) => {
    const li = document.createElement("li");
    li.innerHTML = `<h4>错题 #${w.id}${w.mastered ? " ✅已掌握" : ""}</h4>
      <div class="meta">${w.created_at}</div>
      <div class="meta">${String(w.question).slice(0, 160)}</div>
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
