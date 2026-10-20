// Tessera Agent web 前端 v2（W2 · LLD-A14 §4）：对话流消费 + 状态灯 +
// 心跳 + 任务栏 + 时间线过滤尾随 + 设置/双模式。判据行保真着色沿用
// （LLD-A10 §3 契约——原始证据流零改写，普通模式为叠加摘要层）。
import { callTool, initialize } from "./mcp.js";
import { PHASES, heartbeatText, phaseSummary, plain } from "./copy.js";

const $ = (id) => document.getElementById(id);
let attachedTaskId = null;      // null = 最新任务
let currentPhase = "idle";      // 状态灯去重
let autoScroll = true;
let lastActivityTs = 0;
let railTasks = [];             // 任务列存根（tasks 帧）

// ---- 判据行着色（LLD-A11 §3 正则表——零改写仅样式） ------------------------
const VERDICT_RULES = [
  ["verdict-err", /FATAL|EXCCAUSE|<err>|Stack overflow|FAILED/],
  ["verdict-ok", /\bAK[A-Za-z0-9]*\b.*\bPASS\b|\bPASS\b|NVD DONE|deploy done|CONNECTED/],
  ["verdict-accent", /^\[tsi\]|\[appmgr\]|\[ts-net\]|\[q\]/],
  ["verdict-warn", /<w(arn|arning)>|WARN/],
];
// 诊断/部署高频行（W1 第四条：普通模式不渲染，开发者模式折叠区可见）
const DIAG_RULE = /\[dep\]|post_deploy_check|capture_window/;

function lineElement(text) {
  const span = document.createElement("span");
  if (DIAG_RULE.test(text)) {
    span.className = "diag";
  } else {
    for (const [c, re] of VERDICT_RULES) {
      if (re.test(text)) { span.className = c; break; }
    }
  }
  span.textContent = text + "\n";
  return span;
}

// ---- 会话流（气泡 + 自动滚底） ----------------------------------------------
function stickBottom() {
  const chat = $("chat");
  return autoScroll && chat.scrollHeight - chat.scrollTop - chat.clientHeight < 48;
}

function appendBubble(role, text, tone) {
  const chat = $("chat");
  const stick = stickBottom();
  const div = document.createElement("div");
  div.className = `bubble ${role}` + (tone ? ` ${tone}` : "");
  const who = document.createElement("span");
  who.className = "who";
  who.textContent = role === "user" ? "您" : "Tessera";
  const body = document.createElement("span");
  body.textContent = text;
  div.append(who, body);
  // W2 验收修复②：气泡追加到流末尾（原 insertBefore 栈顶插入 = 会话倒序
  // 实录）——时序 = 文档序，问询卡仍置顶于 #interactions。
  $("stream").appendChild(div);
  if (stick) chat.scrollTop = chat.scrollHeight;
  else $("to-bottom").hidden = false;
}

function appendLines(lines) {
  const log = $("log");
  const stick = autoScroll && log.scrollHeight - log.scrollTop - log.clientHeight < 40;
  for (const ln of lines) log.appendChild(lineElement(ln));
  while (log.childNodes.length > 4000) log.removeChild(log.firstChild);
  if (stick) log.scrollTop = log.scrollHeight;
  else $("to-bottom").hidden = false;
}

function initStreamUi() {
  const chat = $("chat");
  chat.addEventListener("scroll", () => {
    autoScroll = chat.scrollHeight - chat.scrollTop - chat.clientHeight < 48;
    if (autoScroll) $("to-bottom").hidden = true;
  });
  $("to-bottom").addEventListener("click", () => {
    autoScroll = true; chat.scrollTop = chat.scrollHeight; $("to-bottom").hidden = true;
  });
}

// ---- 状态灯 + 心跳（LLD-A14 §4.2——server 派发 phase，前端零推导） ----------
function renderPhase(phase, progress) {
  if (phase && phase !== currentPhase) {
    currentPhase = phase;
    const meta = PHASES[phase] ?? PHASES.idle;
    const el = $("phase");
    el.className = `phase tone-${meta.tone}`;
    $("phase-label").textContent = meta.label;
  }
  if (progress && progress.last_activity_ts) {
    lastActivityTs = progress.last_activity_ts;
  }
  renderHeartbeat();
}

function renderHeartbeat() {
  $("heartbeat").textContent =
    (currentPhase === "idle" || currentPhase === "done" || currentPhase === "failed")
      ? "" : heartbeatText(lastActivityTs);
}
setInterval(renderHeartbeat, 5000);

// 阶段变化 → Agent 摘要气泡（对话流的 Agent 侧话语）
function announcePhase(phase, progress) {
  if (phase === currentPhase) return;
  const prev = currentPhase;
  currentPhase = phase;
  const meta = PHASES[phase] ?? PHASES.idle;
  const el = $("phase");
  el.className = `phase tone-${meta.tone}`;
  $("phase-label").textContent = meta.label;
  if (phase === prev || phase === "idle") return;
  const tone = meta.tone === "danger" ? "err" : meta.tone === "warn" ? "warn" : null;
  appendBubble("agent", phaseSummary(phase, progress), tone);
}

// ---- 交互卡（问询 / 审批——D7/D4 实体；置顶区） -----------------------------
function renderInteractions(questions, approvals) {
  const box = $("interactions");
  box.textContent = "";
  for (const q of questions ?? []) {
    const card = document.createElement("div");
    card.className = "card";
    const title = document.createElement("div");
    title.textContent = plain(q.question);
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = q.context ? plain(q.context) : "";
    const actions = document.createElement("div");
    actions.className = "actions";
    for (const opt of q.options) {
      const btn = document.createElement("button");
      btn.textContent = plain(opt);
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await callTool("sys_answer", { question_id: q.question_id, answer: opt });
          card.remove();
          appendBubble("user", `${plain(q.question)} → ${plain(opt)}`);
        } catch (e) {
          btn.disabled = false;
          appendBubble("agent", `应答失败：${e.message}`, "err");
        }
      });
      actions.appendChild(btn);
    }
    card.append(title, meta, actions);
    box.appendChild(card);
  }
  for (const a of approvals ?? []) {
    const card = document.createElement("div");
    card.className = "card danger";
    const title = document.createElement("div");
    title.textContent = `安全确认：${plain(a.tool)}`;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `${plain(a.reason)} · 剩 ${Math.round(a.expires_in_s)}s`;
    const actions = document.createElement("div");
    actions.className = "actions";
    const token = document.createElement("input");
    token.className = "token";
    token.type = "password";
    token.placeholder = "审批 token（不落存储）";
    actions.appendChild(token);
    for (const decision of ["allow", "allow-session", "deny"]) {
      const btn = document.createElement("button");
      btn.textContent = { allow: "允许", "allow-session": "本次会话允许", deny: "拒绝" }[decision];
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await callTool("sys_approve", {
            approval_id: a.approval_id, decision, token: token.value,
          });
          card.remove();
          appendBubble("user", `安全确认 ${plain(a.tool)} → ${btn.textContent}`);
        } catch (e) {
          btn.disabled = false;
          appendBubble("agent", `审批失败：${e.message}`, "err");
        }
      });
      actions.appendChild(btn);
    }
    card.append(title, meta, actions);
    box.appendChild(card);
  }
}

// ---- 任务栏（tasks 帧 + sys_tasks 刷新——多任务视图） ------------------------
function renderTasks(tasks) {
  railTasks = tasks ?? railTasks;
  const box = $("tasks");
  box.textContent = "";
  if (!railTasks.length) {
    const p = document.createElement("p");
    p.className = "muted"; p.textContent = "暂无任务";
    box.appendChild(p);
    return;
  }
  for (const t of [...railTasks].reverse()) {
    const row = document.createElement("div");
    row.className = "task-row" + (t.task_id === attachedTaskId ? " attached" : "");
    const name = document.createElement("span");
    name.textContent = `${plain(t.tool)} · ${t.task_id.slice(0, 8)}`;
    const st = document.createElement("span");
    st.className = "task-state";
    st.textContent = PHASES[t.phase]?.label ?? t.state ?? "";
    row.append(name, st);
    row.addEventListener("click", () => attachTask(t.task_id));
    box.appendChild(row);
  }
}

function attachTask(taskId) {
  attachedTaskId = taskId;
  $("log").textContent = "";
  renderTasks(railTasks);
  connect();  // 重连即以新 task_id 建流（服务端按连接起算）
}

// ---- SSE v2 消费（LLD-A14 §3.3：快照 + 直推 + id 续传） ---------------------
let es = null;

function connect() {
  if (es) es.close();
  const url = new URL("/events", window.location.origin); // 根绝对（W1 教训）
  if (attachedTaskId) url.searchParams.set("task_id", attachedTaskId);
  es = new EventSource(url.href);
  const conn = $("conn");
  es.onopen = () => { conn.className = "conn live"; conn.title = "推送已连接"; };
  es.onerror = () => {
    conn.className = "conn down"; conn.title = "推送断开——自动重连";
  };
  es.onmessage = (ev) => {
    const frame = JSON.parse(ev.data);
    handleFrame(frame);
  };
}

function handleFrame(frame) {
  switch (frame.kind) {
    case "task_log":
      appendLines(frame.lines);
      break;
    case "state": {
      if (frame.task_id) $("task-label").textContent = `· ${frame.task_id}`;
      // W2 验收修复③：历史回放（刷新/切任务不丢——日志区空时渲染快照 log）
      if (frame.log?.length && $("log").childElementCount === 0) {
        appendLines(frame.log);
        appendBubble("agent",
          `已恢复任务 ${frame.task_id.slice(0, 10)}（${frame.log.length} 条历史日志——开发者模式可查看全文）`);
      }
      renderInteractions(frame.questions, frame.approvals);
      renderPhase(frame.phase, frame.progress);
      announcePhase(frame.phase, frame.progress);
      if (frame.state === "failed") {
        appendBubble("agent", "任务失败——可展开「详细日志」定位原因。", "err");
      }
      break;
    }
    case "tasks":
      renderTasks(frame.tasks);
      break;
    case "questions":
    case "approvals":
      // 增量开关事件 → 拉一次全量 pending（快照面最简——事件频率低）
      refreshPending();
      break;
    case "resync":
      // 慢消费者重对齐：清空本连接日志（服务端快照将重放）
      $("log").textContent = "";
      break;
    default:
      break;  // 未知帧型忽略（前向兼容）
  }
}

async function refreshPending() {
  try {
    const qs = await callTool("sys_pending_questions", {});
    const as = await callTool("sys_pending_approvals", {});
    renderInteractions(qs.pending ?? [], as.pending ?? []);
  } catch { /* 瞬态——下个对账周期兜底 */ }
}

// ---- 发起任务（双模式——LLD-A14 §5.2；clarify 域 W2-3 接入） ------------------
function mode() {
  return localStorage.getItem("tessera.mode") ?? "normal";
}

async function initLaunchForm() {
  const form = $("task-form");
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const err = $("launch-err");
    err.hidden = true;
    const text = $("spec").value;
    try {
      let handle;
      if (mode() === "normal") {
        appendBubble("user", plain(text));
        handle = await callTool("app_clarify", {
          requirement: text,
          key_path: $("key-path").value || null,
        });
        if (handle.task_id) {
          attachedTaskId = handle.task_id;
          appendBubble("agent", "需求澄清已开始——请回答上方问询卡。");
        }
      } else {
        appendBubble("user", text);
        handle = await callTool("app_develop", {
          spec: text,
          key_path: $("key-path").value,
          plan_confirm: $("plan-confirm").checked,
        });
        attachedTaskId = handle.task_id ?? null;
      }
      $("log").textContent = "";
      $("task-label").textContent = attachedTaskId ? `· ${attachedTaskId}` : "";
      $("spec").value = "";
      renderTasks(railTasks);
    } catch (e) {
      err.textContent = e.message;
      err.hidden = false;
    }
  });
}

// ---- 时间线（过滤 + 尾随——W1 反馈③） ----------------------------------------
async function initTimeline() {
  const box = $("timeline");
  const filterSel = $("tl-filter");
  const follow = $("tl-follow");
  let entries = [];

  function render() {
    const f = filterSel.value;
    const shown = entries.filter((e) => !f || e.tool === f);
    const lines = [`${shown.length}${shown.length !== entries.length ? "/" + entries.length : ""} 条`];
    for (const e of shown) {
      const glyph = e.state === "ok" ? "✓" : e.state === "failed" ? "✗"
        : e.state === "hook_denied" ? "⛔" : "·";
      lines.push(`[${e.time}] ${glyph} ${e.tool} (${e.kind}, ${e.dur_ms}ms)` +
        (e.task_id ? ` ${e.task_id.slice(0, 10)}` : ""));
    }
    box.textContent = lines.join("\n");
    box.scrollTop = box.scrollHeight;  // 尾随：最新在底
  }

  async function load() {
    box.textContent = "加载中…";
    try {
      const tl = await callTool("sys_timeline", { limit: 200 });
      entries = tl.entries ?? [];
      const tools = [...new Set(entries.map((e) => e.tool))].sort();
      for (const t of tools) {
        if (!filterSel.querySelector(`option[value="${t}"]`)) {
          const o = document.createElement("option");
          o.value = t; o.textContent = t;
          filterSel.appendChild(o);
        }
      }
      render();
      box.classList.remove("muted");
    } catch (e) {
      box.textContent = `加载失败：${e.message}`;
    }
  }

  $("tl-load").addEventListener("click", load);
  filterSel.addEventListener("change", render);
  follow.addEventListener("change", () => {
    if (follow.checked) load();
  });
  setInterval(() => { if (follow.checked) load(); }, 10000);
}

// ---- 设置（LLD-A14 §4.4：主题/模式/密钥/计划确认——localStorage） -------------
function initSettings() {
  const apply = () => {
    const theme = localStorage.getItem("tessera.theme") ?? "auto";
    if (theme === "auto") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = theme;
    document.body.classList.toggle("mode-normal", mode() === "normal");
    $("set-theme").value = theme;
    $("set-mode").value = mode();
  };
  $("set-theme").addEventListener("change", (e) => {
    localStorage.setItem("tessera.theme", e.target.value); apply();
  });
  $("set-mode").addEventListener("change", (e) => {
    localStorage.setItem("tessera.mode", e.target.value); apply();
    $("spec").placeholder = mode() === "normal"
      ? "描述你想让设备做什么…（普通模式会逐项与你确认）"
      : "四节需求单：【需求】【资源】【判据】【安全声明】…";
  });
  $("key-path").value = localStorage.getItem("tessera.key")
    ?? $("key-path").value;
  $("key-path").addEventListener("change", (e) =>
    localStorage.setItem("tessera.key", e.target.value));
  $("plan-confirm").checked = localStorage.getItem("tessera.plan_confirm") === "1";
  $("plan-confirm").addEventListener("change", (e) =>
    localStorage.setItem("tessera.plan_confirm", e.target.checked ? "1" : "0"));
  $("menu-settings").addEventListener("click", () => {
    const s = $("settings");
    s.hidden = !s.hidden;
  });
  $("menu-history").addEventListener("click", () => {
    $("history").classList.toggle("open");
  });
  apply();
}

// ---- 启动 -----------------------------------------------------------------
async function main() {
  document.body.classList.add(mode() === "normal" ? "mode-normal" : "mode-dev");
  initStreamUi();
  initSettings();
  initLaunchForm();
  initTimeline();
  try {
    await initialize();
  } catch (e) {
    $("conn").className = "conn down";
    appendBubble("agent", `MCP 握手失败：${e.message}（网关未以 http 形态运行？）`, "err");
    return;
  }
  connect();
}

main();
