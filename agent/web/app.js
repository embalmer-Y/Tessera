// Tessera Agent web 前端（W1 · LLD-A11）：SSE 推送消费 + 交互卡 + 进度 +
// 判据行保真着色（逐字不改——LLD-A10 §3 契约）。
import { callTool, initialize } from "./mcp.js";

const $ = (id) => document.getElementById(id);
let attachedTaskId = null; // null = 最新任务
let logCursor = 0;         // 重连时清空（服务端游标按连接起算）
let autoScroll = true;

// ---- 判据行着色（正则表——LLD-A11 §3；零改写仅样式） ----------------------
const VERDICT_RULES = [
  ["verdict-err", /FATAL|EXCCAUSE|<err>|Stack overflow|FAILED/],
  ["verdict-ok", /\bAK[A-Za-z0-9]*\b.*\bPASS\b|\bPASS\b|NVD DONE|deploy done|CONNECTED/],
  ["verdict-accent", /^\[tsi\]|\[appmgr\]|\[ts-net\]|\[q\]/],
  ["verdict-warn", /<w(arn|arning)>|WARN/],
];

function lineElement(text) {
  const span = document.createElement("span");
  let cls = null;
  for (const [c, re] of VERDICT_RULES) {
    if (re.test(text)) { cls = c; break; }
  }
  span.textContent = text + "\n";
  if (cls) span.className = cls;
  return span;
}

// ---- 会话流（自动滚底 + 用户上滚暂停） ------------------------------------
function appendLines(lines) {
  const log = $("log");
  const stick = autoScroll && log.scrollHeight - log.scrollTop - log.clientHeight < 40;
  for (const ln of lines) log.appendChild(lineElement(ln));
  while (log.childNodes.length > 4000) log.removeChild(log.firstChild);
  if (stick) log.scrollTop = log.scrollHeight;
  else $("to-bottom").hidden = false;
}

function initStreamUi() {
  const log = $("log");
  log.addEventListener("scroll", () => {
    autoScroll = log.scrollHeight - log.scrollTop - log.clientHeight < 40;
    if (autoScroll) $("to-bottom").hidden = true;
  });
  $("to-bottom").addEventListener("click", () => {
    autoScroll = true; log.scrollTop = log.scrollHeight; $("to-bottom").hidden = true;
  });
}

// ---- 交互卡（问询 / 审批——D7/D4 实体的 web 呈现） ------------------------
function renderQuestions(container, questions) {
  for (const q of questions) {
    const card = document.createElement("div");
    card.className = "card";
    const title = document.createElement("div");
    title.textContent = q.question;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `${q.question_id}${q.context ? " · " + q.context : ""}` +
      (q.default ? ` · 缺省 ${q.default}` : "");
    const actions = document.createElement("div");
    actions.className = "actions";
    for (const opt of q.options) {
      const btn = document.createElement("button");
      btn.textContent = opt;
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await callTool("sys_answer", { question_id: q.question_id, answer: opt });
          card.remove();
        } catch (e) {
          btn.disabled = false;
          alert(`应答失败：${e.message}`);
        }
      });
      actions.appendChild(btn);
    }
    card.append(title, meta, actions);
    container.appendChild(card);
  }
}

function renderApprovals(container, approvals) {
  for (const a of approvals) {
    const card = document.createElement("div");
    card.className = "card danger";
    const title = document.createElement("div");
    title.textContent = `strict 审批：${a.tool}`;
    const meta = document.createElement("div");
    meta.className = "meta";
    meta.textContent = `${a.approval_id} · ${a.reason} · 剩 ${Math.round(a.expires_in_s)}s`;
    const actions = document.createElement("div");
    actions.className = "actions";
    const token = document.createElement("input");
    token.className = "token";
    token.type = "password";
    token.placeholder = "审批 token（TESSERA_AGENT_APPROVAL_TOKEN，不落存储）";
    actions.appendChild(token);
    for (const decision of ["allow", "allow-session", "deny"]) {
      const btn = document.createElement("button");
      btn.textContent = decision;
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          await callTool("sys_approve", {
            approval_id: a.approval_id, decision, token: token.value,
          });
          card.remove();
        } catch (e) {
          btn.disabled = false;
          alert(`审批失败：${e.message}`);
        }
      });
      actions.appendChild(btn);
    }
    card.append(title, meta, actions);
    container.appendChild(card);
  }
}

// ---- 进度（task_progress 结构化面——D2） ----------------------------------
function renderProgress(el, progress, state) {
  el.classList.remove("muted");
  el.textContent = "";
  const kv = document.createElement("div");
  kv.className = "kv";
  const fields = {
    loop_state: `状态 ${progress.loop_state ?? "-"}`,
    round: progress.round != null ? `轮次 ${progress.round}/${progress.round_budget ?? "?"}` : null,
    rounds_used: progress.rounds_used != null ? `累计 ${progress.rounds_used} 轮` : null,
    evidence_count: `证据 ${progress.evidence_count ?? 0}`,
    repairing: progress.repairing ? "修复轮" : null,
  };
  for (const v of Object.values(fields)) {
    if (v) { const s = document.createElement("span"); s.textContent = v; kv.appendChild(s); }
  }
  const st = document.createElement("div");
  st.className = "kv";
  st.textContent = `task ${state ?? "-"}`;
  el.append(st, kv);
  const plan = progress.plan ?? [];
  for (const item of plan) {
    const row = document.createElement("div");
    row.className = "plan-item";
    const stSpan = document.createElement("span");
    stSpan.className = item.status === "done" ? "st-done" : "st-pending";
    stSpan.textContent = item.status === "done" ? "✓" : "○";
    const desc = document.createElement("span");
    desc.textContent = `${item.id} ${item.desc}`;
    row.append(stSpan, desc);
    el.appendChild(row);
  }
  if (!plan.length && !Object.keys(progress).length) {
    el.textContent = "未附着任务";
    el.classList.add("muted");
  }
}

// ---- SSE 消费 -------------------------------------------------------------
function connect() {
  const url = new URL("events", window.location.href);
  if (attachedTaskId) url.searchParams.set("task_id", attachedTaskId);
  const es = new EventSource(url.href);
  const conn = $("conn");
  es.onopen = () => { conn.className = "conn live"; conn.title = "推送已连接"; };
  es.onerror = () => {
    conn.className = "conn down"; conn.title = "推送断开——自动重连";
    // 服务端游标按连接起算：重连 = 清空重放（本帧起）
    $("log").textContent = "";
  };
  es.onmessage = (ev) => {
    const frame = JSON.parse(ev.data);
    if (frame.kind === "task_log") { appendLines(frame.lines); return; }
    if (frame.kind === "state") {
      $("task-label").textContent = frame.task_id ? `· ${frame.task_id}` : "";
      const box = $("interactions");
      box.textContent = "";
      const has = (frame.questions?.length ?? 0) + (frame.approvals?.length ?? 0);
      if (!has) {
        const p = document.createElement("p");
        p.className = "muted"; p.id = "no-interactions";
        p.textContent = "暂无待应答问询 / 审批";
        box.appendChild(p);
      } else {
        renderQuestions(box, frame.questions ?? []);
        renderApprovals(box, frame.approvals ?? []);
      }
      renderProgress($("progress"), frame.progress ?? {}, frame.state);
    }
  };
  return es;
}

// ---- 发起任务 -------------------------------------------------------------
function initLaunchForm() {
  $("task-form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const err = $("launch-err");
    err.hidden = true;
    try {
      const handle = await callTool("app_develop", {
        spec: $("spec").value,
        key_path: $("key-path").value,
        plan_confirm: $("plan-confirm").checked,
      });
      attachedTaskId = handle.task_id ?? null;
      $("log").textContent = "";
      $("task-label").textContent = attachedTaskId ? `· ${attachedTaskId}` : "";
    } catch (e) {
      err.textContent = e.message;
      err.hidden = false;
    }
  });
}

// ---- 时间线（D5 决策链回放——sys_timeline 同源） ---------------------------
function initTimeline() {
  $("tl-load").addEventListener("click", async () => {
    const box = $("timeline");
    box.textContent = "加载中…";
    try {
      const tl = await callTool("sys_timeline", { limit: 200 });
      const lines = [`${tl.total} 条${tl.truncated ? "（已截尾）" : ""} · ${tl.span[0] ?? "—"} → ${tl.span[1] ?? "—"}`];
      for (const e of tl.entries) {
        const glyph = e.state === "ok" ? "✓" : e.state === "failed" ? "✗"
          : e.state === "hook_denied" ? "⛔" : "·";
        lines.push(`[${e.time}] ${glyph} ${e.tool} (${e.kind}, ${e.dur_ms}ms)` +
          (e.task_id ? ` task=${e.task_id}` : ""));
      }
      box.textContent = lines.join("\n");
      box.classList.remove("muted");
    } catch (e) {
      box.textContent = `加载失败：${e.message}`;
    }
  });
}

// ---- 启动 -----------------------------------------------------------------
async function main() {
  initStreamUi();
  initLaunchForm();
  initTimeline();
  try {
    await initialize();
  } catch (e) {
    $("conn").className = "conn down";
    appendLines([`[web] MCP 握手失败：${e.message}（网关未以 http 形态运行？）`]);
    return;
  }
  connect();
}

main();
