const $ = (id) => document.getElementById(id);
const api = async (url, opts) => {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  return res.json();
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
    { num: d.courses, label: "课程", sub: `${d.materials} 份课程资料` },
    { num: d.mastery_rate + "%", label: "错题掌握率", sub: `${d.wrong_mastered}/${d.wrong_total} 已掌握 · ${d.wrong_unmastered} 待攻克` },
    { num: d.focus_today_minutes + " 分钟", label: "今日专注", sub: `累计 ${d.focus_total_minutes} 分钟 / ${d.focus_count} 次` },
    { num: d.pending_tasks, label: "待复习任务", sub: "到点自动推送 ESP32 提醒" },
  ];
  $("statCards").innerHTML = cards.map((c) =>
    `<div class="card"><div class="num">${c.num}</div><div class="label">${c.label}</div><div class="sub-num">${c.sub}</div></div>`
  ).join("");

  const ul = $("focusList");
  ul.innerHTML = d.recent_sessions.length ? "" : "<li><div class='meta'>还没有专注记录，用上面的番茄钟开始第一段专注吧。</div></li>";
  d.recent_sessions.forEach((s) => {
    const li = document.createElement("li");
    li.innerHTML = `<h4>🍅 ${s.minutes} 分钟 ${s.course_name ? "· " + s.course_name : ""}</h4>
      <div class="meta">${s.created_at}${s.note ? " · " + s.note : ""}</div>`;
    ul.appendChild(li);
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

/* ==================== 初始化 ==================== */
async function init() {
  initTheme();
  await loadStatus();
  await loadCourses();
  await loadMaterials();
  await loadWrongQuestions();
  await loadProviders();
  await loadOverview();
  loadHardwareStatus();
  bindEvents();
  initUpload();
  pomoRender();
  document.querySelectorAll(".mic-btn").forEach((b) => { b.onclick = () => toggleMic(b); });
  const hash = location.hash.slice(1);
  if (hash && $("panel-" + hash)) activateTab(hash);
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

  $("sendChat").onclick = sendChat;
  $("chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) sendChat();
  });

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
  const list = await api("/api/providers");
  const ul = $("providerList");
  ul.innerHTML = "";
  list.forEach((p) => {
    const li = document.createElement("li");
    li.innerHTML = `<h4>${p.label} ${p.active ? "· 当前" : ""}</h4>
      <div class="meta">${p.available ? "✅ 已配置密钥，可用真实模型" : "⚠️ 未配置密钥，将使用演示模式"}</div>
      ${p.active ? "" : `<div class="actions"><button data-name="${p.name}">切换为当前</button></div>`}`;
    ul.appendChild(li);
  });
  ul.querySelectorAll("button").forEach((b) => {
    b.onclick = async () => {
      await api("/api/settings/provider", { method: "POST", body: JSON.stringify({ name: b.dataset.name }) });
      loadStatus(); loadProviders();
    };
  });
}

init();
