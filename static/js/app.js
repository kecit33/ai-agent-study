const $ = (id) => document.getElementById(id);
const api = async (url, opts) => {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  return res.json();
};

let currentCourseId = null;

// ---------------- 初始化 ----------------
async function init() {
  await loadStatus();
  await loadCourses();
  await loadMaterials();
  await loadWrongQuestions();
  await loadProviders();
  bindEvents();
}

async function loadStatus() {
  const s = await api("/api/status");
  const active = s.providers.find((p) => p.active);
  $("providerBadge").textContent = "智能体：" + (active ? active.label : "演示模式");
}

async function loadCourses() {
  const list = await api("/api/courses");
  const sel = $("courseSelect");
  sel.innerHTML = "";
  list.forEach((c) => {
    const o = document.createElement("option");
    o.value = c.id; o.textContent = c.name;
    sel.appendChild(o);
  });
  currentCourseId = sel.value ? Number(sel.value) : null;
}

function bindEvents() {
  // tabs
  document.querySelectorAll(".tab").forEach((t) => {
    t.onclick = () => {
      document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
      document.querySelectorAll(".panel").forEach((x) => x.classList.remove("active"));
      t.classList.add("active");
      $("panel-" + t.dataset.tab).classList.add("active");
    };
  });

  $("courseSelect").onchange = () => {
    currentCourseId = Number($("courseSelect").value);
    loadMaterials();
    loadWrongQuestions();
  };
  $("refreshCourses").onclick = loadCourses;
  $("newCourseBtn").onclick = async () => {
    const name = prompt("课程名称：");
    if (!name) return;
    await api("/api/courses", { method: "POST", body: JSON.stringify({ name }) });
    await loadCourses();
  };

  // chat
  $("sendChat").onclick = sendChat;
  $("chatInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) sendChat();
  });

  // summarize / tutor / plan
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

  // materials
  $("addMaterial").onclick = async () => {
    if (!currentCourseId) return alert("请先选择课程");
    await api(`/api/courses/${currentCourseId}/materials`, {
      method: "POST",
      body: JSON.stringify({ title: $("matTitle").value, content: $("matContent").value }),
    });
    $("matContent").value = ""; $("matTitle").value = "";
    loadMaterials();
  };

  // wrong questions
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
    loadWrongQuestions();
  };

  // hardware
  $("addHwTask").onclick = async () => {
    const r = await api("/api/review-tasks", {
      method: "POST",
      body: JSON.stringify({
        course_id: currentCourseId, task_name: $("hwTask").value,
        due_time: $("hwDue").value || undefined, fire_now: !$("hwDue").value,
      }),
    });
    $("hwStatus").textContent = "已创建：" + JSON.stringify(r.fired || {});
  };
  $("hwTest").onclick = async () => {
    const r = await api("/api/hardware/test", { method: "POST", body: JSON.stringify({ task_name: "测试提醒" }) });
    $("hwStatus").textContent = JSON.stringify(r);
  };
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
  const list = await api(`/api/wrong-questions?course_id=${currentCourseId}`);
  const ul = $("wqList");
  ul.innerHTML = "";
  list.forEach((w) => {
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
        loadWrongQuestions();
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
