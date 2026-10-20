// 极简 MCP-over-HTTP 客户端（LLD-A11 §1——手写，零依赖零 Node）。
// Streamable HTTP：POST JSON-RPC 至 /mcp；会话经 mcp-session-id 头维持；
// 响应可能为纯 JSON 或 SSE 帧（event/data），两者兼容解析。
let nextId = 1;
let sessionId = null;

function mcpUrl() {
  // 绝对路径——/web/ 同源挂载下相对解析会得到 /web/mcp（StaticFiles 405）
  return new URL("/mcp", window.location.origin).href;
}

async function rpc(method, params) {
  const headers = {
    "content-type": "application/json",
    accept: "application/json, text/event-stream",
  };
  if (sessionId) headers["mcp-session-id"] = sessionId;
  const res = await fetch(mcpUrl(), {
    method: "POST",
    headers,
    body: JSON.stringify({ jsonrpc: "2.0", id: nextId++, method, params }),
  });
  const sid = res.headers.get("mcp-session-id");
  if (sid) sessionId = sid;
  const text = await res.text();
  let payload = text;
  if (text.startsWith("event:") || text.includes("\ndata:")) {
    const line = text.split("\n").find((l) => l.startsWith("data:"));
    payload = line ? line.slice(5).trim() : "{}";
  }
  let msg;
  try {
    msg = JSON.parse(payload);
  } catch (e) {
    throw new Error(`MCP 响应非 JSON（HTTP ${res.status}）: ${text.slice(0, 120)}`);
  }
  if (msg.error) throw new Error(msg.error.message || JSON.stringify(msg.error));
  return msg.result;
}

export async function initialize() {
  await rpc("initialize", {
    protocolVersion: "2025-06-18",
    capabilities: {},
    clientInfo: { name: "tessera-web", version: "0.1" },
  });
  // initialized 通知（无响应——失败静默，会话已建立）
  try {
    await rpc("notifications/initialized", {});
  } catch (e) { /* 通知类：部分实现返回错——忽略 */ }
}

export async function callTool(name, args) {
  let r;
  try {
    r = await rpc("tools/call", { name, arguments: args ?? {} });
  } catch (e) {
    // W2 验收修复④：会话失效（服务重启等）→ 重握手一次重试一次——
    // 不再让整页交互静默失效（问题①实抓的同族根因）
    await initialize();
    r = await rpc("tools/call", { name, arguments: args ?? {} });
  }
  if (r.isError) {
    const text = (r.content ?? []).map((c) => c.text ?? "").join("\n");
    throw new Error(text || `工具 ${name} 失败`);
  }
  const text = (r.content ?? []).map((c) => c.text ?? "").join("");
  try {
    return JSON.parse(text);
  } catch (e) {
    return { raw: text };
  }
}
