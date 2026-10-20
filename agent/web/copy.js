// 文案层（W2 · LLD-A14 §4.3——DEC-69②）：术语映射 + 状态灯文案 + 阶段
// 摘要模板。普通模式走映射（叠加摘要层），开发者模式原文（判据行保真
// 合同不变——原始证据流零改写，日志抽屉即逐字原文）。

// 状态灯 11 态（server 侧 derive_phase 单源派生——前端零推导，仅文案）。
export const PHASES = {
  idle: { label: "空闲", tone: "idle", note: "等待任务" },
  planning: { label: "规划中", tone: "busy", note: "正在把需求拆解为实施计划…" },
  implementing: { label: "实现中", tone: "busy", note: "正在编写与修改代码…" },
  verifying: { label: "验证中", tone: "busy", note: "正在编译与检查产物…" },
  repairing: { label: "修复轮", tone: "warn", note: "发现问题，正在修复…" },
  awaiting_confirm: { label: "等待您确认", tone: "ask", note: "需要您的答复才能继续" },
  awaiting_approval: { label: "等待审批", tone: "danger", note: "安全敏感操作等待审批" },
  packaging: { label: "打包中", tone: "busy", note: "正在签名打包产物…" },
  deploying: { label: "部署/执行中", tone: "busy", note: "正在执行部署或长任务…" },
  done: { label: "已完成", tone: "ok", note: "任务完成" },
  failed: { label: "失败", tone: "danger", note: "任务失败——可查看详细日志" },
};

// 开发者术语 → 普通用户文案（顺序敏感：长词先替）。
const TERMS = [
  [/app_develop/g, "应用生成"],
  [/spec 门|spec_check/g, "需求单检查"],
  [/spec（?!）/g, "需求单"],
  [/strict 审批|strict/g, "安全确认"],
  [/判据/g, "验收检查"],
  [/TSAP|tsap/g, "应用包"],
  [/wasm/g, "应用模块"],
  [/激活|activate/g, "启用"],
  [/槽位|slot/g, "安装位"],
  [/PACKAGED/g, "打包完成"],
  [/loop_state|round_budget|task_id/g, "内部参数"],
  [/zenoh/g, "通信网络"],
];

export function plain(text) {
  let s = String(text);
  for (const [re, to] of TERMS) s = s.replace(re, to);
  return s;
}

// 阶段摘要（Agent 气泡文案——由 progress 关键数字组装；no-JS-模板串）。
export function phaseSummary(phase, progress = {}) {
  const base = PHASES[phase]?.note ?? "";
  const bits = [];
  if (progress.round != null) {
    bits.push(`第 ${progress.round}${progress.round_budget ? "/" + progress.round_budget : ""} 轮`);
  }
  if (progress.repairing) bits.push("修复模式");
  if (progress.evidence_count) bits.push(`已积累 ${progress.evidence_count} 项验证证据`);
  if (progress.overall) bits.push(`结果：${plain(String(progress.overall))}`);
  return bits.length ? `${base}（${bits.join(" · ")}）` : base;
}

export function heartbeatText(lastActivityTs) {
  if (!lastActivityTs) return "";
  const secs = Math.max(0, Math.round(Date.now() / 1000 - lastActivityTs));
  if (secs < 5) return "刚刚有活动";
  if (secs < 90) return `${secs}s 前有活动`;
  return `${Math.round(secs / 60)}min 前有活动`;
}
