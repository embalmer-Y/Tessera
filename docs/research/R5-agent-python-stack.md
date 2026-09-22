# R5 · Agent Python 栈 HLD 级核验（PydanticAI / FastMCP / TSAP 签名栈 / zenoh-python）

> **状态**：v1.0 · 2026-09-22 · research 阶段产出（阶段白名单内）· 结论供 Agent HLD 与 `design/design-review-02-agent-python-ripple.md` 使用。
> **任务来源**：owner 2026-09-22 指令（Q-18 裁定附带）——"有调整的地方需要重新research"；DEC-37 定全 Python（PydanticAI + FastMCP + 自建编码工具集）后，原基于 TS/pi 的设计输入需 Python 侧 HLD 级事实替换。
> **核验方式**：2 个并行调研子代理于 **2026-09-22 实查**（pydantic.dev / gofastmcp.com 官方文档原文、GitHub 仓库与 pyproject.toml、PyPI JSON API、库源码 raw 抓取）；来源见 §8，未能核验项以 ⚠️ 标注。

## 0. 背景（自包含）

DEC-37（2026-09-22）裁定 Agent 实现 = 全 Python：**FastMCP 门面 + PydanticAI agent 循环 + 自建最小编码工具集（read/write/apply_patch/exec）**，单进程，Linux，Python 3.12（WSL venv 现状）。需核验四个设计级问题：① PydanticAI/FastMCP 能否落 DEC-36 定下的交互栈（含"审批闸"= pi beforeToolCall 的等效物、审计导出、长任务句柄）；② Agent 侧 TSAP 打包签名（DEC-21：wasm + CBOR manifest + COSE_Sign1/ed25519）的 Python 库路线；③ Agent 侧 zenoh 客户端（DEC-18 备注⑥）现状；④ 版本钉住建议。

## 1. PydanticAI 事实卡

- **版本/许可/支持面**：v2.47.0（2026-09-22 当日发布）；MIT；`requires-python >=3.10`（classifiers 3.10–3.14，**3.12 ✓**）；20.1k stars 活跃维护。
- **v2 稳定性承诺**（官方 Version Policy）：V2.0 stable = 2026-06-23；minor 不做故意 breaking；deprecated 保留至下一 major；**minor 可能新增消息/流事件的可选字段**——官方要求历史序列化一律用 `ModelMessagesTypeAdapter`（对审计导出直接相关）。
- **Agent 循环**：`run()/run_sync()/run_stream()/iter()`；多轮 = `message_history=result.new_messages()` 显式传递（无隐式会话态）；`UsageLimits`（request/tokens/tool_calls/cost）；工具注册 `@agent.tool`/`tool_plain`/`tools=[...]`/`toolsets=[...]`，**schema 由函数签名自动生成**（docstring 提供描述，可强制 `require_parameter_descriptions`）。
- **工具并行控制**：多 tool call 默认 `asyncio.create_task` 并发；单工具 `sequential=True` 屏障；run 级可全局串行（`parallel_tool_calls=False`）——确定性合同的 Agent 侧落点。
- **工具调用拦截（审批闸）——能力超过原 pi 方案**：官方 Hooks 一等支持 `before_tool_execute` / `after_tool_execute` / `wrap_tool_execute`（可改写参数、`raise SkipToolExecution(result)` 短路、`raise ApprovalRequired` 挂起待批）；另有 `Tool(..., requires_approval=True)` → `DeferredToolRequests` 暴露待批调用，批准后 `ctx.tool_call_approved=True` 重跑校验与执行；可按工具名过滤（`hooks.on.before_tool_execute(tools=['exec'])`）。
- **结构化输出**：`Agent(output_type=PydanticModel)`；三种模式（ToolOutput 默认 / NativeOutput 提供者原生 schema / PromptedOutput 兜底）；校验失败 `raise ModelRetry` 回传重试（默认预算 1，可调）。
- **会话/审计导出**：`ModelMessagesTypeAdapter` = message history ↔ JSON 官方原语；存储键 = `conversation_id`（每条消息另有 `run_id`）；核心不带持久化后端（官方"deliberately unopinionated"），Harness `StepPersistence` 提供 memory/file/SQLite/Mongo 后端（⚠️成熟度未深查，可自建——TypeAdapter + SQLite 约三十行）。**durable execution（Temporal 等 7 引擎）为可选层，V1 不采用**（JSON 历史导出 + 自建审计即够）。
- **提供者矩阵**：OpenAI/Anthropic/Google(Gemini+Vertex)/xAI/Bedrock/Groq/Mistral/OpenRouter/… 原生；**Ollama 专用 `OllamaModel`**（自托管 v0.5+ 以 llama.cpp 语法强制 json_schema → NativeOutput 可用）；**自定义 OpenAI-compatible baseURL**（`OpenAIProvider(base_url=…)` / env / 注入 AsyncOpenAI）——"LLM 用户自选"（DEC-12）达标。
- **MCP client**：`MCPToolset` 内部包装 FastMCP Client；接受 URL/脚本路径/预建 Client/**进程内 FastMCP server 对象（零网络往返）**；`.prefixed()` 命名空间；`load_mcp_toolsets('mcp_config.json')` 标准 config。
- **依赖重量**：装 `pydantic-ai-slim[openai,anthropic,google,mcp]`（slim 核心 8 依赖）；关键耦合事实：`[mcp]` extra 直接依赖 `fastmcp-slim[client]>=3.3.0,<5`——**PydanticAI 官方以 FastMCP 为 MCP 客户端引擎**。

## 2. FastMCP 事实卡

- **版本/许可/支持面**：v4.0.5（2026-09-17；4.0.0 final = 2026-08-31）；Apache-2.0；Python 3.10–3.13（**3.12 ✓**）；已组件化（`fastmcp` meta → `fastmcp-slim[client,server]`、`fastmcp[tasks]`）；引擎 = MCP Python SDK v2，**CI 跑官方 MCP conformance suite**。
- **spec 版本面（对 DEC-36① 直接落点）**：**单部署同时服务全部 spec 版本**——handshake 时代 2024-11-05/2025-03-26/2025-06-18/2025-11-25 + 现代 sessionless **2026-07-28**，按连接协商；SSE 例外（无法承载 sessionless，停在 2025-11-25）。stdio 与 Streamable HTTP 均一等传输。stateless 语义下 `ctx.elicit()` 仅 legacy 连接可用（与 DEC-36 "elicitation 不依赖"一致）。
- **Middleware（server 侧闸）**：`Middleware.on_call_tool(context, call_next)` 可阻断（raise ToolError）可改写（改 `context.message.arguments`）可过滤工具列表；内置 RateLimiting/Logging/Timing/ResponseCaching 等（私有扩展，单进程自用无碍）。
- **Background tasks（长任务）**：`@mcp.tool(task=True)` + `fastmcp[tasks]`（执行层 Prefect Docket，实现官方 `io.modelcontextprotocol/tasks` 扩展）——句柄+轮询模式一等支持，后端 memory://（单进程）或 redis/valkey；⚠️任务上下文快照（含 token）落后端，Redis 需加密密钥。**V1 决策：自建句柄（进程内 task 注册表 + status/log 查询工具）更简单可控，FastMCP tasks 留作多进程阶段选项**（与 DEC-36② 的自定义路线一致）。
- **与 PydanticAI 协同**：双向官方文档——① agent 消费 MCP（FastMCPToolset，in-memory 直传 server 对象）；② **agent 嵌入 MCP server（Tessera 门面模式）官方正名**：`@server.tool()` handler 内 `await agent.run(...)` 返回 `r.output`（pydantic.dev/docs/ai/mcp/server/）。

## 3. 适配判定（架构需求 → 落点）

| 架构需求（DEC-33/36/37） | 落点（已核验） | 判定 |
|---|---|---|
| MCP 门面（stdio 起步 + Streamable HTTP 预留 + stateless-first + 2025-11-25 兼容） | FastMCP 4 单部署覆盖全 spec 版本，按连接协商 | ✅ |
| agent 嵌入 server（单进程） | 官方文档正名模式（@server.tool 内 agent.run） | ✅ |
| 审批闸（pi beforeToolCall 等效） | wrap_tool_execute + ApprovalRequired + requires_approval + FastMCP Middleware 双层 | ✅ **超集** |
| 审计/重放导出 | ModelMessagesTypeAdapter JSON（conversation_id/run_id）+ 自建落盘 | ✅ |
| 结构化产出校验 | output_type + ModelRetry | ✅ |
| LLM 可换（含本地） | 原生矩阵 + OllamaModel + 自定义 baseURL | ✅ |
| 长任务句柄+轮询 | 自建句柄（V1）/ FastMCP tasks（后置选项） | ✅ |
| Python 3.12 | 两库均支持 | ✅ |
| 确定性（并行工具控制） | sequential=True / parallel_tool_calls=False | ✅ |
| asyncio 全链路 | 单进程单事件循环契合；**工具内禁阻塞调用**（exec 必须走 subprocess/线程池——HLD 编码条目） | ✅（纪律） |

## 4. TSAP Python 签名栈（Agent 侧打包/签名/往返验签）

- **cbor2**：6.1.4（2026-08-01），MIT，活跃（月度连发）；**`dumps(..., canonical=True)` 原生支持 RFC 8949 确定性编码**（自 4.1.0，2026 年仍在修 canonical 缺陷）——manifest 序列化一律 canonical，TSAP 容器字节可复现（L4 重放/合同 9 受益）。
- **pycose**：1.1.0（**2023-12-15 后无 release，停滞约 2 年 9 个月**；仓库 2025-10 仅 CI 维修）；BSD-3-Clause；**COSE_Sign1 + Ed25519(OKPKey/EdDSA) 功能完整**（官方 doctest 往返验证）；依赖 cryptography+cbor2。⚠️实现细节：内部 `cbor2.dumps` 未传 canonical——**签名正确性无碍，但多键 protected header 字节复现不保证规范序** → **使用纪律：protected header 只放单键 `{1: -8}`（alg=EdDSA），KID 放 unprotected**。
- **cryptography**：50.0.1（2026-08-25）；**Apache-2.0 OR BSD-3-Clause 双许可**（v42 起，选 Apache-2.0 分支与仓库 LICENSE 同源）；Ed25519 API 完整（含 raw 快捷法）。
- **备选**：`cwt` 3.3.0（2026-07，活跃，MIT，但 CWT 令牌语义需适配层）；cryptography **无** COSE 高层 API；**DIY fallback 完全可行**：COSE_Sign1 结构极小（tag 18 + 4 元数组；Sig_structure = ["Signature1", phdr_bstr, external_aad, payload]），cryptography Ed25519 + cbor2 手工构造约 30–60 行，RFC 9052 §4.2 定义明确、嵌入式先例充分（wolfCOSE 等即手写）。
- **推荐路线**：`cbor2(canonical=True)` + `pycose` + `cryptography`；**对冲 pycose 停滞**：测试中双实现互验（pycose 验 DIY 产物 / DIY 验 pycose 产物），停滞恶化即切 DIY 主力。固件侧 C 验签器（QCBOR/tinycbor 系）只需容忍任意合法 CBOR map 序（decoupled，固件侧课题不变）。

## 5. zenoh-python（Agent 侧客户端）

- **包名/仓库**：`eclipse-zenoh`（PyPI）= eclipse-zenoh/zenoh-python；1.10.1（2026-09-07），**EPL-2.0 OR Apache-2.0 双许可**（选 Apache-2.0）；Rust 主实现的原生绑定（maturin），非纯 Python 协议栈；ZettaScale 驱动的 Eclipse 项目，push 至核验当日。
- **协议兼容**：无官方兼容矩阵页，但有**结构性保证**——zenoh(Rust)/zenoh-python/zenoh-pico 三仓库 **lockstep 同日发版**（1.10.1/1.10.0/…三仓同步）；**实操纪律：router(zenohd) + zenoh-python + zenoh-pico 三方钉同一 1.x minor**；建议 Agent 集成测试加 router 版本断言。
- **API 形态**：**同步 API（asyncio API 已官方移除**，issue #95 open 有重引入意愿）——Agent asyncio 架构需 `asyncio.to_thread`/线程池包裹，注意回调跨线程队列；wheel = cp39-abi3（Py≥3.9 全系，3.12 ✓，manylinux x86_64/aarch64）。
- **TLS**：JSON5 配置（`tls.root_ca_certificate`、`connect_private_key/certificate`、`enable_mtls`、`verify_name_on_connect`）；**router 侧不指定 root_ca 时默认信任 WebPKI 根**——自签场景必须显式配 CA（prov 流程注意点）。
- **对比 TS 路线**：旧 zenoh-js 已弃用消失，zenoh-ts 为 WASM 浏览器方案——**改 Python 绑定零能力损失**（直包完整 Rust 实现，pub/sub/query/TLS 全覆盖）。
- **风险：Zenoh 2.0 计划 2026 H2**（2025-12 Zenoh User Meeting 宣布；架构级改动如 Zenoh-ID routing；roadmap 免责非承诺）——钉 1.10.1；2.0 升级时三方协同 + 全量回归，**牵动固件侧 M3a（zenoh-pico）**，登记为联合升级风险项。

## 6. 推荐组合与钉版清单（HLD 输入）

| 组件 | 包 | 钉版建议 | 许可 |
|---|---|---|---|
| agent 循环 | `pydantic-ai-slim[openai,anthropic,google,mcp]` | 2.x minor 钉版（升级走 changelog compatibility 标记） | MIT |
| MCP 门面 | `fastmcp`（server 栈） | 4.x 钉版 | Apache-2.0 |
| CBOR | `cbor2` | ==6.1.4（canonical 纪律） | MIT |
| COSE | `pycose`（+DIY fallback 双验） | ==1.1.0 | BSD-3 |
| 密码原语 | `cryptography` | >=42（当前 50.0.1） | Apache-2.0 OR BSD-3 |
| zenoh 客户端 | `eclipse-zenoh` | ==1.10.1（**三方同 minor**：router/zenoh-python/zenoh-pico） | EPL-2.0 OR Apache-2.0 |

安装纪律：用 slim 变体，避开 `pydantic-ai` 完整包拉入 evals/web/logfire。

## 7. 风险清单汇总（按严重度）

1. **FastMCP 4 极新**（final 距今 3 周，单一核心维护者 + Prefect）→ V1 只走 stdio + handshake 时代协议（最保守路径），钉版本。
2. **PydanticAI v2 年轻**（stable ~3 个月）但承诺明确 → minor 钉版 + 审计导出强制 ModelMessagesTypeAdapter + 导出格式纳入我们自己的版本管理。
3. **pycose 停滞** → 单键 phdr 纪律 + DIY fallback 双实现互验（§4）。
4. **Zenoh 2.0 在途**（2026 H2 计划）→ 三方同 minor 钉版 + 联合升级回归（牵动 M3a）。
5. **审批闸的 MCP 侧呈现是设计活**：ApprovalRequired 在 agent 进程内闭环，呈现给 MCP 客户端（owner）需选型——`request_approval/approve` 自定义工具对（推荐）或工具级拒绝；HLD 设计项，非库缺口。
6. **asyncio 纪律**：exec/长命令必须 subprocess/线程池，禁阻塞事件循环（HLD 编码条目）。
7. ⚠️未核验：PydanticAI Temporal 集成细节页（V1 不采用）；FastMCP 服务端 transports 专页（URL 变动 404，能力经 FAQ/多源交叉）；PydanticAI Harness（StepPersistence）成熟度。

## 8. 来源清单

- PydanticAI：pypi.org/project/pydantic-ai；github.com/pydantic/pydantic-ai（pyproject 原文）；pydantic.dev/docs/ai/（overview/agent/tools/tools-advanced/hooks/output/storage/models/openai/ollama/mcp-client/**mcp-server**/durable-overview/version-policy）。
- FastMCP：pypi.org/project/fastmcp；github.com/PrefectHQ/fastmcp；gofastmcp.com（whats-new/faq/middleware/tasks/integrations-pydantic-ai）。
- TSAP 栈：pypi.org/project/cbor2 + github.com/agronholm/cbor2（versionhistory raw）；pypi.org/project/pycose + github.com/TimothyClaeys/pycose（examples.rst/sign1message.py/cosebase.py raw）；cryptography.io（changelog/ed25519）；pypi.org/project/cwt + github.com/dajiaji/python-cwt。
- zenoh-python：github.com/eclipse-zenoh/zenoh-python（README/issue #95）；pypi.org/pypi/eclipse-zenoh/json；github.com/eclipse-zenoh/{zenoh,zenoh-pico}（releases lockstep 比对；DEFAULT_CONFIG.json5 raw）；zenoh.io TLS 指南；corsaro.me（Zenoh Report 2026-02，2.0 计划）。

## 修订记录

- v1.0 · 2026-09-22：初版。2 路并行实查（PydanticAI+FastMCP；TSAP 签名栈+zenoh-python）；结论供 Agent HLD 与 design-review-02。
