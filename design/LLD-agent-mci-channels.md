# LLD-agent-mci-channels · 多渠道交互架构（MCI 渠道三层模型）· v0.1

> **本文件是什么**：Tessera Agent 多渠道交互（MCI）低层设计——V0.12.0 A10 单元（DEC-67① 定案；需求源 DEC-66②「未来多渠道交互架构，方便扩展其他交互方式」）。依据 = R11-multichannel-interaction.md（六项目代码级调研）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.1（2026-10-19 DEC-67① 按建议值定案后首稿）。

## 1. 三层渠道模型

**Channel ≡ Transport × Renderer × Interaction**——新增渠道 = 实现三面即接入，Agent 核心/域工具/固件零改动。

| 层 | 职责 | 现状 | 本批动作 |
|---|---|---|---|
| Transport | 字节流与请求语义（stdio / HTTP+Streamable / SSE 推送） | FastMCP stdio+HTTP 已在（HLD §9） | SSE 推送端点（§3） |
| Renderer | 事件流 → 渠道可呈现部件（按渠道能力裁剪） | TerminalFrontend（cli/render.py）归位 | WebFrontend（A11/W1） |
| Interaction | 问询/审批/进度三类一等实体 | D7 QuestionBroker / ApprovalBroker / TaskRegistry.progress 已在 | —（协议面已闭合） |

**归位纪律**：既有 TerminalFrontend 与 MCP 面不重写——按本模型标注归属（第三例独立验证：opencode/QwenPaw/我方三方同构，「服务端优先、渠道=客户端」）。

## 2. Transport 面

- **stdio**（缺省，DEC-38 #2）与 **HTTP+Streamable**（`run_server(transport="http")`，HLD §9 解锁项）维持。
- **SSE 推送面（新增）**：`GET /events`（与 MCP 同源同端口）——v1 实现策略 = Starlette SSE 路由 + 0.5s 轮询差分源（task_log 尾随 + questions/approvals pending 变化 + task state），事件形态 `{"kind": "task_log"|"question"|"approval"|"task_state", ...}`。**诚实注记**：轮询差分非最佳（长期 = 内核事件总线直推），但 v1 零重构且语义完备；A10 修订时按实测升级。
- 绑定默认 127.0.0.1（外网暴露 = owner 显式 + 自担——既有约束维持）。

## 3. Renderer 契约

```text
render(event: Envelope, caps: ChannelCaps) -> Parts
  ChannelCaps = {markdown, code_highlight, tables, max_len, interactive}
  Parts = [Text|CodeBlock|VerdictLine|QuestionCard|ApprovalCard|Progress|TimelineEntry]
```

- **Terminal**：现有 cli/render.py 即该契约的终端实现（归位注记，不改名不迁移）。
- **Web**：A11/W1——caps 全能（markdown/代码高亮/表格 + DOM 交互）。
- **判据行保真**（合同级）：`[tsi]`/`NVD DONE`/`AK*` 等机械判据行在任意渠道逐字呈现——Renderer 不得改写，只做样式区分（R5 终端同纪律）。

## 4. Interaction 面（协议实体，全部已实现）

| 实体 | 列举 | 应答/决定 | 防护 |
|---|---|---|---|
| 问询（D7） | sys_pending_questions | sys_answer（枚举域 fail-closed） | 无 token（便利面）；审计归因 |
| 审批（DEC-38 #7） | sys_pending_approvals | sys_approve（token；D4 增 allow-session） | **token = 安全边界** |
| 进度（D2） | task_progress / task_status | —（只读） | — |
| 钩子裁决（D4） | —（拦截面） | —（config 声明） | deny 恒优先 + 审计 |

## 5. 出站寻址（预留）

单渠道 v1 不需要 ChannelAddress；多出站渠道（钉钉/飞书类）接入时引入 `kind:id → to_handle` 统一路由（QwenPaw schema.py 参照，R11 §7.1）。**预留不实现**（真实渠道出现再启——D6 同判据）。

## 6. 安全边界（显式对照）

- 渠道安全哲学两派：pi「OS 边界、默认不审批」vs 我方「制造门禁」。**分层共存**：渠道侧自由（未来 harness 客户端自带体验），**服务端闸（D4 hooks + strict 审批 token）为真边界**——对所有渠道一视同仁。
- 问询面为便利交互面（无 token）；strict 动作恒经 token 审批（DEC-38 #7；「持有 token ≠ 主人本人」缺口维持记录不开发）。

## 7. 测试要点

- SSE 端点：事件差分（task_log 新行/pending 变化可见）；断连重连语义。
- Renderer 契约：判据行逐字保真（终端/web 双实现对拍——simreal_diff 思想延伸）。
- Interaction：三实体经 web 渠道全链（W1 验收承担）。

## 修订记录

- v0.1 · 2026-10-19：DEC-67① 定案首稿——三层模型/归位表/SSE v1 策略/Renderer 契约（判据行保真）/安全边界对照；出站寻址预留不实现。
