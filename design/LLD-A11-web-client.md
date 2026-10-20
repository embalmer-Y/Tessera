# LLD-A11 · Web 客户端（W1 · 案 A 纯 Python 零构建链）· v0.2（W1 已实现 + 人工验收修订）

> **本文件是什么**：Tessera Agent Web 客户端低层设计——V0.12.0 A11/W1 单元（DEC-67② 定案：案 A 静态单页；owner「简约好看 + 纯 Python 零 Node」确认）。依据 = R11 §4 选型两案 + §7.3 设计语言方法论。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.2（2026-10-19 W2 重塑落地注记——四区观测台形态由 LLD-A14 会话流形态接替；SSE 轮询差分由 EventBus 直推送代，本文件的零构建/同源挂载/MCP-over-HTTP 底座契约不变）。v0.1.2（2026-10-19 人工验收同步修订——见修订记录；v0.1.1 实现交付）。
> **下一步**：本形态将被 **W2 web 渠道重塑**（DEC-69 六点 + W1 验收 UX 反馈四条，plan §11h A3）大幅演进——重塑设计批（门③）时本文升版。

## 1. 形态（案 A）

- **载体**：单页 `agent/web/index.html` + 同目录 ES modules（`app.js`/`mcp.js`/`tokens.css`/`app.css`）——浏览器原生运行，**零 npm/零打包器/零 TS 转译**（Q-48② 定案；类型注解 = JSDoc）。
- **服务**：网关 Starlette 应用同源挂载 `/web → StaticFiles`（无 CORS；与 SSE/MCP 端点同端口；127.0.0.1 缺省）。
- **MCP 消费**：手写极简客户端 `mcp.js`（~200 行）——JSON-RPC over HTTP POST（initialize/tools/list/tools/call）+ `EventSource` 消费 `/events` 推送（A10 §2）。不引官方 TS SDK（那才需要 Node 生态）。

## 2. 页面结构（四区）

| 区 | 内容 | 数据源 |
|---|---|---|
| 会话流 | 任务事件流 + **判据行保真呈现**（等宽/高亮样式，逐字不改） | SSE task_log |
| 交互卡 | 问询卡（options 按钮 → sys_answer）+ 审批卡（token 输入 → sys_approve；allow-session 三选） | SSE question/approval |
| 进度 | 计划项/轮次/loop_state/evidence 计数（结构化，非日志流） | task_progress（D2）+ SSE task_state |
| 时间线 | 决策链回放（D5 同源数据；W1 v1 预留 tab，随 D5 点亮） | task_log 全量 |

## 3. 设计语言（先于代码——R11 §7.3 方法论）

- **语义 token 层**（`tokens.css`，gemini-cli semantic-tokens 同型）：六角色 `--c-fg/--c-bg/--c-accent/--c-ok/--c-warn/--c-danger` + 间距/圆角/等宽字体 token；深浅色两主题 = token 重映射。
- **交互语法**（QwenPaw design.md 同型纪律）：交互卡 = 页面唯一强制注意点（置顶 + 强调边）；判据行 = 等宽 + 角色色但**零改写**；会话流自动滚底 + 用户上滚即暂停（回底按钮）。
- 判据行正则着色表：`AK[A-Z0-9]+ .*PASS` → ok 色；`<err>`/FATAL → danger；`[tsi]`/`NVD DONE` → accent。

## 4. 安全

- 绑定 127.0.0.1 缺省（外网暴露 = owner 显式）；strict 审批 = token 手输（token 不存 localStorage——会话域内存态）；问询无 token（便利面）；**D4 hooks = 服务端真边界**（前端呈现的 deny 与 CLI 渠道同源同语义）。
- 无 Cookie/无会话持久化/无第三方资源（全自持静态——供应链面为零）。

## 5. 测试

- pytest HTTP 层：`/web` 挂载可达 + 静态资源 Content-Type + `index.html` 引用的 ES import 路径静态解析（全部相对路径存在性）。
- 行为验收 = 人工（浏览器全链：发起 app_develop（plan_confirm=True）→ 问询卡应答 → 进度 → 会话流判据行可见）；自动化浏览器测试随需后补（playwright——彼时属 dev-only 依赖，不入运行时）。

## 6. 余项登记

- post 观察钩子面（D4 余项）随本客户端审计展示需求评估。
- 时间线 tab 随 D5 点亮。
- 多任务切换（v1 = 单任务视角——v1 实际无 task_id URL 参数读取，SSE 未附着时跟最新任务；A3 多任务视图收口）。
- **W2 重塑需求（DEC-69）**：界面观感/普通用户文案/对话式交互（用户消息入流 + Agent 状态指示）/多端响应式/左侧设置栏/双模式（开发者全细节含 log；普通模式 = LLM 需求澄清阶段——Agent 能力增量）+ W1 验收 UX 反馈四条（计划项打卡/LLM 心跳/时间线过滤尾随/诊断轮询纪律）。

## 修订记录

- v0.1.2 · 2026-10-19：**人工验收同步修订**——(a) composer（发起区）由 sticky header 移至页面底部 footer（sticky bottom 常驻——owner 反馈采纳，聊天应用惯例）；(b) **前端端点根绝对纪律**：/web/ 同源挂载下 `new URL` 相对解析 = /web/mcp（StaticFiles 405）与 /web/events（404）——人工验收实抓，mcp.js/app.js 改 origin 解析 + test_web 根绝对静态守卫（同类缺陷机械拦截，web 6 用例）；(c) 密钥缺省值落测试根实路径 + spec 占位符更正为 spec 门真实四节名；§2 表布局事实以 agent/web/index.html 现形为准（header 只留品牌 + 连接态，composer 居底）。

- v0.1.1 · 2026-10-19：**W1 实现交付**——agent/web/ 五文件（index.html/tokens.css/app.css/mcp.js/app.js）+ gateway/web.py（mount_web：/web StaticFiles 同源 + /events SSE 轮询差分 v1）+ run_server http 分支组装（共享 AppContext——SSE 与 MCP 面同注册表）；真实 uvicorn 冒烟四探全过（/web 200 html / app.js 200 js / events SSE 首帧 / mcp initialize 应答）；pytest HTTP 层 5 用例（挂载/ES import 解析/路由注册/差分帧语义/SSE 流 + MCP 面不受组装影响）；时间线 tab 预留（随 D5）。
- v0.1 · 2026-10-19：DEC-67② 定案首稿——案 A 形态/四区页面/设计语言 token 层/判据行保真着色/安全面/测试口径。
