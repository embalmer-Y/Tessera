# AI CLI 编程流程与约束实现调研 → Agent 下一阶段功能输入——报告

> **日期**：2026-10-13 · **触发**：owner 指令（「调研其他开源 AI CLI（codex/zcode/opencode 等）具体编程流程实现、工具调用、编码约束怎么实现；深度调研后制定 Agent 下一阶段新功能；下一阶段开发重心 = Agent 侧」）。
> **方法**：四路并行实抓官方文档/仓库源码（Codex CLI / opencode v1.19.0 / Gemini CLI / Claude Code，均标来源 URL）+ ZCode 第一人称自省（本会话系统契约，产品未开源）+ aider 增量（既有调研 `agent-codegen-reliability.md` R1-R8 基础）。同批登记：审批闸委托人假设缺口（观察项，owner 裁「记录不开发」，decisions.md 2026-10-13）。
> **结论**：五对象约束实现收敛为**五层模型**（提示/指令文件/机械门禁/权限沙箱/流程结构）。Tessera Agent 在**机械门禁层与审计层强于全部调研对象**（域内四道确定性门 + SOURCES.lock 机械锁 + flash 审计），缺口集中在**流程结构层**（会话持久化/计划工具/拦截面/回放）与**审批粒度**（工具级 vs 业界参数级）。§5 呈递九项候选待 owner 排序。

## 0. 范围与信息源说明

- **Codex CLI**：openai/codex 仓库 HEAD（2026-10）config.schema.json + 源码 handlers + 文档外迁前最后完整版（commit 40de81e7af，2025-12-24）交叉核实；developers.openai.com 本环境 403（如实）。
- **opencode**：opencode.ai/docs 全套 + v1.19.0（2026-10-11，稳定版）源码（src/tool、src/lsp）；仓库已迁 anomalyco/opencode。
- **Gemini CLI**：google-gemini/gemini-cli docs/ 全套（tools/planning/shell/sandbox/session/checkpointing/hooks/extensions/subagents/auto-memory 等 25+ 页）。
- **Claude Code**：code.claude.com/docs 官方文档 20 页（产品非开源，文档完整——作参考项）。
- **ZCode**：本会话第一人称自省（系统契约可观测面）；**aider**：既有 R1-R8 调研（2026-10-04）增量补注。

## 1. 调研对象档案

### 1.1 OpenAI Codex CLI（开源 · Rust）

- **架构**：单一 Rust 二进制；TUI / 无头 `codex exec`（`--json` JSONL 事件流、`--output-schema` 结构化输出）/ IDE / 桌面 / 云。会话持久 `~/.codex`（SQLite 状态库）；`resume <id>|--last` 复续、fork 走 ThreadFork API。
- **循环**：推理摘要→工具调用→回喂→…；计划工具 `update_plan`（step × pending/in_progress/completed，事件流以 todo_list 外显）；独立只读 Plan 模式（`plan_mode_reasoning_effort`）。
- **工具面**（源码 codex-rs/core/src/tools/handlers/）：`shell`（timeout 默认 10000ms，超时返回 session id 续查）、`exec_command`（PTY）+ `write_stdin`（后台上限 300000ms）、`apply_patch`（**Lark 文法定义的 patch 语法**：`*** Begin Patch`/`*** Update File:`/`@@` 上下文/+−行）、`update_plan`、`view_image`、`current_time`、**`get_context_remaining` / `new_context_window`（上下文预算工具化——模型可查询可重开）**、`sleep`、`request_permissions`/`request_user_input`、`tool_search`、MCP 工具+资源。并行调用需 `supports_parallel_tool_calls=true`（默认串行）。
- **审批/沙箱**：`approval_policy` = on-request | never | granular 对象（旧值 untrusted/on-failure 已从 schema 移除）；`sandbox_mode` = read-only | workspace-write | danger-full-access；底层 macOS Seatbelt / Linux **Landlock+seccomp** / Windows AppContainer；**workspace-write 网络默认禁用**（`network_access=true` 显式开），可写根 = `writable_roots`。
- **约束**：AGENTS.md 发现序 = 全局（override 优先）→ 仓库根→cwd 逐级，根→叶拼接，总量 `project_doc_max_bytes`=32768；**hooks（2026 新）**：SessionStart/End、Pre/PostToolUse、Pre/PostCompact、Stop、UserPromptSubmit、SubagentStart/Stop、PermissionRequest、Interrupt（替代已废弃 notify）。lint/test 无专用回路——shell 输出回喂或 hook。
- **上下文**：/compact + 自动双触发（绝对阈值 + 回合末百分比，`compact_prompt` 可自定义）。
- **多代理**：**内建原语最强**——v1 `spawn_agent/wait_agent/close_agent/resume_agent/send_input`；v2 加 `interrupt_agent/list_agents/send_message/followup_task`；collab 协作模板。
- **扩展**：MCP `[mcp_servers.<id>]` 含 **per-tool `approval_mode`**；skills（SKILL.md + `[skills]` 配置 + max_context_tokens）。

### 1.2 opencode（开源 · TypeScript/Bun · v1.19.0）

- **架构**：client/server（TUI 起本地 HTTP server；`opencode serve` 无头默认 127.0.0.1:4096 + `OPENCODE_SERVER_PASSWORD` basic auth；OpenAPI 3.1 规范自动生成 SDK）；`/share` 公开链接（manual 默认）。
- **循环**：Tab 在 **Plan/Build 双主 agent** 间切换（plan 默认 edit/bash=ask 只分析不动手）；v1.19 源码含 `todowrite`。
- **工具面**：`bash`（timeout 默认 120000ms per-call 可覆盖；后台命令无超时）、`read`（行范围）、`edit`（**oldString/newString 唯一匹配**，失配重试容忍排版空白）、`write`、`grep`、`glob`（mtime 序）、`apply_patch`（marker 多文件）、`lsp`（实验）、`webfetch`、`websearch`、`skill`、`question`、`task`（spawn 子代理）。
- **权限**：每工具 `permission: allow|ask|deny` + **glob 对象规则**（bash 按命令模式 `{"git *":"allow","rm *":"deny"}`、edit 按路径、webfetch 按 URL，最后匹配胜）；`--auto` 自动批非 deny；**doom_loop 检测**（同工具同参 3 次重复 → ask）；`.env` 读取默认 deny。无 OS 沙箱文档（/docs/sandboxing 404）。
- **约束**：AGENTS.md 一等（`/init` 引导生成；无则回退 CLAUDE.md）；`instructions` 数组引 glob/URL；**插件钩子** `tool.execute.before/after`（before 可 throw 阻断）、`shell.env`、`event`；**LSP 诊断自动回喂（重点）**：`lsp:true` 启用约 37 个内置 server（clangd/pyright/rust-analyzer…），edit 后 `lsp.touchFile` 等诊断，**只取 severity=1（ERROR）、每文件截 20 条**，以「LSP errors detected in this file, please fix:」附加进工具输出——语言服务器报错直接驱动自修复。
- **上下文**：`compaction.auto` 满窗自动压缩 + `/compact`；`prune` 删旧工具输出；`small_model` 承担标题等轻任务；`--continue/--session/--fork` 恢复。
- **多代理**：内置 build/plan/general/explore/scout + 自定义 `.opencode/agents/*.md`（frontmatter：mode primary|subagent|all、model、temperature、steps 上限）；`task` 工具 + `subagent_depth=1` 禁套娃。
- **扩展**：MCP local/remote；自定义命令 `.opencode/command/*.md`（`$ARGUMENTS`、`` !`cmd` `` shell 注入、`@file`）；插件 `.opencode/plugin/*.ts` 可 `tool()`（zod schema）**注册/覆盖内置工具**。

### 1.3 Gemini CLI（开源 · TypeScript）

- **架构**：交互 `gemini` / 无头 `-p`（text|json|stream-json）/ ACP（JetBrains/Zed）/ `-e` 扩展。会话按项目哈希存 `~/.gemini/tmp/<hash>/chats/`；`/resume`、`--resume latest|N`；**checkpointing**（默认关）：批准写工具时在影子 git 仓快照文件态+对话+工具调用，`/restore` 回滚。
- **循环**：**Plan Mode** = `enter_plan_mode`（切只读）→ `exit_plan_mode(plan_path)` 交批（计划文件须在 plans/ 目录；YOLO 下不可用）；任务分解 `write_todos` + 实验性 `tracker_*` 六工具（**DAG 依赖**）。
- **工具面**：`read_file`（行范围/图片/PDF）、`read_many_files`、`write_file`、`replace`（唯一匹配默认，allow_multiple 放开）、`run_shell_command`（注入 GEMINI_CLI=1；**链式命令拆分校验**）、`glob`（默认 respect_git_ignore）、`grep_search`（git grep 优先）、`google_web_search`（grounding）、`web_fetch`、`list_directory`；MCP 工具命名 `mcp_{server}_{tool}`；`tools.core` 白名单（`run_shell_command(git)` 前缀限定）。
- **审批/沙箱**：`--approval-mode` 四值 default/auto_edit/**yolo**/plan（yolo 仅命令行，`security.disableYoloMode` 可禁）；确认框「Always allow」入 Policy；沙箱 `tools.sandbox`：docker / **runsc（gVisor，最强）** / lxc / macOS Seatbelt（profile 默认 permissive-open）——默认镜像同路径挂载、SANDBOX_MOUNTS 默认只读。
- **约束**：GEMINI.md 三层（全局→工作区→**JIT：工具触碰目录时向上扫描至信任根**）拼接，`context.fileName` 可改名（可配 `["AGENTS.md","GEMINI.md"]`）；自定义命令 `.gemini/commands/*.toml`（`{{args}}`、`!{}` shell、`@{}` 文件）；**hooks 完备**：BeforeTool/AfterTool/BeforeAgent/AfterAgent/BeforeModel/BeforeToolSelection/AfterModel/SessionStart/SessionEnd/Notification/PreCompress，matcher 正则，**exit 2 = 阻断**，timeout 60s。
- **上下文**：`/compress` 手动 + 剩余 ~20% 窗口自动压缩（v0.11.3+）；记忆三层 + **实验 auto-memory：后台挖 transcript 产 memory 补丁与 SKILL.md 草稿 → `/memory inbox` 人工审阅 → 原子应用**（最激进的记忆自动化，且保留了人审闸）。
- **多代理**：无 Task 工具——**子代理以同名工具暴露 + `@name` 前缀指派**；内置 codebase_investigator/cli_help/generalist；自定义 `.gemini/agents/*.md`（tools 通配/内联 mcpServers/max_turns）；禁止递归。
- **扩展**：extensions 打包命令+MCP+hooks+子代理（`gemini extensions install <git URL>`）；VS Code Companion（共享最近 10 文件/光标/选区 ≤16KB）。

### 1.4 Claude Code（非开源 · 官方文档完整——参考项）

- **架构**：交互 `claude` / `-p` 无头（`--bare` 跳过 hooks/skills/MCP/CLAUDE.md）/ IDE 扩展 / 云 + 手机 remote-control；`--continue/--resume/--fork-session`；**checkpointing**：每轮 prompt 前快照，`/rewind` 可只还原代码/只还原对话/两者（保留 100 个、30 天清理；只追踪文件工具编辑——Bash 改动不还原）。
- **循环**：**plan mode** = Shift+Tab / `--permission-mode plan`，批准前仅只读（计划存 `~/.claude/plans`，Ctrl+G 手改，批准后可切 auto）；任务分解 TodoWrite → **TaskCreate/TaskUpdate 族**（新模型启用，环境变量门控）；验证回路 = 同 prompt 内要求跑测试迭代到绿、`/goal` 每轮复检、**Stop hook 未过检查则 block**、专职验证 subagent。
- **工具面**：`Bash`（默认超时 2min/上限 10min；`run_in_background` 默认 30min/上限 2h；输出 ~30k 字符内联超长转文件）、`Edit`（**唯一 old_string 替换 + replace_all，改前须 Read**）、`Write`/`Read`（~25k token/次）、`Glob`/`Grep`、`Agent`（原 Task，v2.1.63 改名）、`WebFetch`（Markdown 化+抽取 prompt、15min 缓存、**拒 localhost**）、`WebSearch`、`Skill`、`AskUserQuestion`、NotebookEdit、PowerShell、LSP/Monitor。
- **审批/权限**：模式 default/acceptEdits/plan/**auto**（后台分类器）/**dontAsk**（该询问即拒）/bypassPermissions；**规则语法 `Tool(specifier)`**：`Bash(git add:*)` 前缀、`Edit(//绝对/**)` 路径、`WebFetch(domain:example.com)`、`mcp__server__tool`——求值 **deny→ask→allow 首匹配，allow 不能穿透 deny**；`canUseTool` 为六步链终点（hooks→deny→ask→mode→allow→回调）；Bash 沙箱 = OS 级（Seatbelt / bubblewrap+socat+seccomp），写限 cwd/temp，**网络走默认空白名单代理**，`sandbox.enabled` 默认 false。
- **约束**：CLAUDE.md 层级 managed > `~/.claude` > 项目（**AGENTS.md 可替代**）> local > 子目录，`@path` 导入递归 4 跳，compact 后重注入项目根，建议 <200 行；**hooks 事件最全**（PreToolUse/PostToolUse/PostToolUseFailure/PermissionRequest/PostToolBatch/UserPromptSubmit/Stop/SubagentStop/PreCompact/SessionStart/End/Notification/FileChanged），PreToolUse 出参 `permissionDecision` + **`updatedInput` 可改写参数**，exit 2 拦截；skills = SKILL.md 渐进披露三级（description 常驻→调用载全文→附属按需），compact 重注入限额 5k/技能。
- **上下文**：/compact（可带 focus）+ 自动 compact（`/autocompact` 可调阈值）；存活项白名单 = 系统提示+项目根 CLAUDE.md+auto memory+计划+最近 5 文件+技能体；`/context` 实时占比分解；memory = MEMORY.md 索引常驻（200 行/25KB）+ 主题文件按需。
- **多代理**：`.claude/agents/*.md`（frontmatter：tools/disallowedTools/model/permissionMode/maxTurns/**isolation: worktree**）；内置 Explore/Plan/general-purpose；并行上限 20、嵌套 3 层；`/subtask` fork 继承全对话。
- **扩展**：MCP 三 scope（local/project `.mcp.json` 支持 `${VAR:-default}`/user）；**插件市场**（打包 skills/agents/hooks/MCP/mods）；自定义命令已并入 skills；status line 可编程（stdin JSON → stdout 显示）。

### 1.5 ZCode（本会话自省——owner 日常使用面，产品未开源）

以下来自本会话系统契约的第一手观测（非源码）：

- **工具面**：Bash（**沙箱默认开**、`dangerouslyDisableSandbox` 显式豁免、`run_in_background` + 超时 120s 默认/600s 上限、专用文件/搜索工具优先纪律）、Read（行号制；**编辑前必须已读**——文件状态由 harness 跟踪）、Edit（**唯一 old_string 匹配**，replace_all 可选）、Write（覆盖已读文件）、Agent（subagent_type 含 Explore/general-purpose/visual-judge 族，可后台）、TodoWrite/TodoRead、TaskOutput/TaskStop、WebFetch/WebSearch、AskUserQuestion（选项 + **preview 并排对比**）、EnterPlanMode/**ExitPlanMode（计划批准门）**、Skill（渐进披露 + `plugin:skill` 命名空间）、可视化目录（Gen UI）。
- **权限**：「工具运行于用户选定的权限模式；被拒 = 用户否决——调整而非原样重试」；hooks 输出视同用户反馈；破坏性/外向动作先确认。
- **约束分层**：AGENTS.md 工作区指令（**显式声明 OVERRIDE 默认行为**）；系统注入不可信内容标记（untrusted_gen_ui_state 等显式降权）；memory 目录 + MEMORY.md 索引（user/feedback/project/reference 四型 + 链接网）。
- **流程结构**：plan mode 批准门；Todo 任务列表外显；上下文增长自动摘要接续（"summarized context"机制）；Cron/OffPeak 定时与闲时任务；动态 workflow（TypeScript 编排多 subagent + 类型化中间结果 + 运行可修补/可恢复）。
- **多代理**：subagent 类型化（如 visual-judge = 独立视觉验收门——「用一道验收门，不要自己先看再派一道」的防重复审查纪律）。

### 1.6 aider（既有 R1-R8 基础上的增量注记）

R1-R8（agent-codegen-reliability）已覆盖其核心：repo map（tree-sitter 依赖图 token 预算化）、编辑格式分级（whole/diff/u-diff——弱模型 whole 最可靠）、auto-commit 每改动、**lint/test hooks 编辑后自动回喂**。本批补注其定位：五对象中唯一「编辑器外挂」形态（非代理循环原生），但其「lint/test 作确定性判据 + git 全程留痕」两条已被各家吸收为标准件。

## 2. 横向对比

| 维度 | Codex | opencode | Gemini CLI | Claude Code | ZCode | Tessera Agent |
|---|---|---|---|---|---|---|
| 形态 | Rust 单二进制+云 | TS client/server | TS | 闭源 CLI+IDE+云 | 闭源 CLI | Python/FastMCP 服务（stdio+HTTP） |
| 指令文件 | AGENTS.md（32KB 上限） | AGENTS.md/CLAUDE.md 回退 | GEMINI.md 三层+JIT（可改名） | CLAUDE.md（AGENTS.md 可替代） | AGENTS.md（OVERRIDE 声明） | skills 4 件 + SOURCES.lock 机械锁 |
| 编辑机制 | apply_patch（文法） | edit 唯一串替换 + apply_patch | replace 唯一匹配 | Edit 唯一串替换（先读后改） | Edit 唯一串替换（先读后改） | 无通用编辑（source_c 整文件再生——R3 域内最优解） |
| 审批 | policy 三值+granular | per-tool allow/ask/deny+glob | 四模式+Policy Engine | 六模式+specifier 规则+六步链 | 权限模式+批准门 | auto/confirm/strict 三级+token |
| 沙箱 | Seatbelt/Landlock+seccomp（网络默认禁） | 无 | Docker/gVisor/Seatbelt | Seatbelt/bubblewrap（默认关） | Bash 默认沙箱 | 域封闭面（无通用 shell/文件工具；子进程固定参数/产物不执行） |
| 诊断回喂 | shell 输出/hook | **LSP ERROR 自动附工具输出** | shell 输出 | getDiagnostics+Stop hook | —— | clang stderr 完整回喂（R2/R6）+ diag_classify/simreal_diff |
| hooks/拦截 | 11 事件族（2026 新） | 插件 before/after | 11 事件 exit2 阻断 | 12+ 事件 + 参数改写 | hooks=用户反馈 | 无（PolicyTable 静态分级） |
| 计划/分解 | update_plan | plan agent+todowrite | plan mode+write_todos+DAG tracker | plan mode+TaskCreate 族 | plan mode+TodoWrite | 无 |
| 会话/恢复 | resume+SQLite+fork | --continue/--fork | /resume+checkpoint 影子 git | --resume+rewind 快照 | 摘要接续 | 无（server 生存期=会话） |
| 上下文 | compact 双触发+**余量工具化** | auto compact+prune+small_model | 20% 自动+auto-memory（人审闸） | auto compact+microcompact+/context | 自动摘要接续 | maybe_compress 70%（任务内） |
| 多代理 | spawn/wait 原语族（最强） | task+depth1 | 子代理即工具+@指派 | agents 文件+20 并发+worktree 隔离 | subagent 类型化+后台 | 无（ln 扇出=编排非智能体） |
| MCP | 客户端（per-tool 审批档） | 客户端 | 客户端+extensions | 客户端+插件市场 | —— | **服务端**（被消费方）；客户端无 |

## 3. 共性模式提炼

### 3.1 约束实现的五层模型（本批核心结论）

所有调研对象的「编码约束」都可归入五层，越往下越硬：

- **L1 提示层**（软）：系统提示行为准则——可被对抗性输入侵蚀，无一家只靠它。
- **L2 指令文件层**（项目记忆）：**AGENTS.md 已成事实标准**（Codex/ZCode 原生；Claude Code 显式可替代 CLAUDE.md；opencode 一等支持；Gemini context.fileName 可配）。共性发现序 = 全局→项目→子目录（Codex 根→叶拼接 + 32KB 上限；Claude @import 4 跳 + compact 后重注入；Gemini JIT 触碰目录扫描）。
- **L3 机械门禁层**（确定性验证）：两件标准件——①**诊断回喂**（opencode LSP ERROR 自动附工具输出最系统化；aider lint-test 最早期；Claude getDiagnostics+Stop hook 门）；②**hooks/插件拦截**（2026 年四家全员收敛到同一语义：工具调用前后注入代码判定的闸——Claude 最全 12+ 事件且 PreToolUse 可**改写参数**，Gemini exit 2 阻断，Codex 11 事件族新立，opencode before 可 throw）。
- **L4 权限沙箱层**（硬边界）：审批模式 + **参数级规则语法**（Claude `Tool(specifier)` 首匹配链 / opencode glob 对象 / Gemini Policy Engine / Codex granular）+ OS 沙箱（Seatbelt/Landlock+seccomp/bubblewrap/Docker/gVisor）+ **workspace-write 网络默认禁**（Codex/Claude 双确认）。共同原则 = **自动化程度越高，隔离越硬**（R4 重申并全员兑现）。
- **L5 流程结构层**（把约束编进流程）：plan mode（只读约束+批准门——三家独立收敛同型）、任务分解工具（进度外显=观测面）、checkpoint/undo（可回滚=可冒险）、多代理（上下文隔离 + 专职验证者）。

### 3.2 工具面最小核心与长任务

五件套全员齐备：shell（超时默认 Codex 10s / Claude 2min / opencode 120s）、read（行号/范围）、edit（两族：**唯一字符串替换**〔Claude/opencode/ZCode/Gemini——先读后改+唯一锚〕vs **patch 文法**〔Codex Lark〕）、write、search。长任务三态：超时→后台→句柄轮询（Codex session id+write_stdin / Claude run_in_background / Tessera task_* 同型）。特色件：Codex 把上下文余量做成工具（模型可查询可重开）——预算可观测性的最直接形态；问询工具（AskUserQuestion/question/request_user_input）三家标配。

### 3.3 反馈回路三型

①**编译器/诊断型**（opencode LSP、Tessera clang stderr 回喂）②**测试/验证型**（aider test hook、Claude Stop hook 门、Tessera 四道确定性门）③**运行时观测型**（Tessera diag_classify + simreal_diff——**五对象均无此型**：部署后真机行为回喂闭环，域独有优势）。业界证据一致指向：自修复收敛的核心杠杆 = 把诊断**自动**附在工具输出后面（不靠模型记得去查）。

### 3.4 上下文管理

compact 全员（手动+自动阈值化；Claude 有存活项白名单 + microcompact；opencode 有 prune/small_model 分流）；记忆分层全员（Gemini auto-memory 最激进但保留 inbox 人审闸；Claude auto memory MEMORY.md 索引常驻）；repo map 仅 aider（其余靠 glob/grep 即时检索）。

### 3.5 多代理

四家全员、形态三派：文件定义+Agent 工具（Claude，20 并发/worktree 隔离）、内建原语族（Codex spawn/wait/interrupt——可编程编排最强）、子代理即工具+@指派（Gemini，禁递归）/depth=1（opencode）。共性 = 子代理是**上下文隔离**手段而非算力手段。

## 4. Tessera Agent 现状对照（本地核证）

工具面 = **33 个 MCP 工具**（platform 8：sys_ping/sys_get_info/sys_pending_approvals/sys_approve/task_status/task_log/task_cancel/skill_read + firmware 域 25：fw_*×4/sim_*×2/tsap_*×3/deploy_*×4/ln_*×6/app_*×3/diag_classify/spec_check/simreal_diff）；审批三级 auto/confirm/strict（strict = tsap_keygen/deploy_push_prov/deploy_push_app/ln_deploy/app_deploy 五件，token + 只可收紧 PolicyTable）；skills 4 件 + SOURCES.lock sha256 锁。

| 业界共性面 | Tessera Agent 现状 | 判定 |
|---|---|---|
| 指令文件层 | skills 渐进披露 + **SOURCES.lock 机械同步锁**（比调研对象的 md 拼接更强：漂移即测试红） | ✓ 等价且更严 |
| 机械门禁·验证门 | 四道确定性门（编译→面检查→尺寸→双编译一致）+ spec_check 判据派生 + simreal_diff 双域对拍 | ✓ **强于全部调研对象**（域内） |
| 机械门禁·诊断回喂 | clang stderr 完整回喂 + 预算 3（R2/R6）；**部署后 diag_classify 需手动喂串** | ◐ 编译域闭环；部署域半自动 |
| 审批 | 三级 + token + 只可收紧；**粒度 = 工具级**（业界已到参数级 specifier） | ◐ 有面缺粒度 |
| 沙箱 | 域封闭面（无通用 shell/文件工具；读面五道门 IR2-03；子进程固定参数/时限/**产物不执行**） | ✓ 域等价（面窄=面小） |
| hooks/拦截面 | 无（PolicyTable 静态） | ✗ 缺 |
| 计划/任务分解 | 无结构工具（repair_loop 内部步骤不外显） | ✗ 缺 |
| 会话持久化/恢复 | 无（server 生存期=会话；**LN 注册表内存态——重启即失**） | ✗ 缺 |
| checkpoint/回放 | audit 全留痕，无回放器 | ◐ 半 |
| 上下文压缩 | maybe_compress 70% 阈值（任务内）；无会话级自动/无余量自省工具 | ◐ 半 |
| 长任务句柄 | task_status/log/cancel 三件 | ✓ 同型 |
| 问询双向化 | strict 挂起→sys_pending_approvals 呈现（单向等批）；无参数化问询 | ◐ 半 |
| 多代理 | 无（ln_deploy 顺序扇出=编排非智能体） | ✗ 缺（域价值待评估） |
| MCP | **服务端**✓（被 ZCode 等消费——集成呈递在档）；客户端能力无 | ◐ 半 |

## 5. 下一阶段候选方向（呈递 owner 排序，非裁决）

按「价值杠杆 / 体量」建议序：

1. **任务链持久化与恢复（resume）**——对标全员会话持久化（Codex SQLite resume / Claude --resume / Gemini checkpoint）。Tessera 场景：长链 develop→deploy→verify 跨 server 重启续跑（板侧 idem 已备，缺 Agent 侧状态落盘）；**LN 注册表落盘**（现重启即失，M16 已知限制）。体量 1-2 单元。
2. **计划/进度结构工具**——对标 update_plan/write_todos/TaskCreate 族。价值：repair_loop 步骤外显为可观测面 + owner 可中断点 + 任务链状态机化（与候选 1 同基座）。体量小。
3. **部署域诊断自动回喂闭环**——对标 opencode LSP 自动回喂（域等价物）。tools_diag capture 已有，接法：部署后自动抓串口进 task_log → diag_classify 自动分类 → 失败类按需 repair 再入队。**业界证据表明「诊断自动附在输出后」是自修复收敛的第一杠杆**。体量小。
4. **工具拦截面（hooks 等价）**——PreToolUse 策略钩子（审批/门禁可编程化）+ PostToolUse 审计注入。对标四家 2026 收敛语义。体量中。
5. **审批参数级粒度 + 上下文余量自省工具**——specifier 规则语法（如 deploy_push_app(cube:xiao-*) 放行）+ budget 暴露（对标 Codex get_context_remaining）。小步升级包。体量小。
6. **决策链回放器（checkpoint 等价）**——audit 已全留痕，差回放器（按 task/app 维度重演 + diff）。对标 Claude rewind / Gemini /restore。价值：事后归因 + 复盘材料。体量中。
7. **MCP 客户端能力**——消费外部 MCP server（场景候选：外部验证器/观测器）。对标全员 mcpServers 配置。体量中。
8. **问询双向化**——AskUserQuestion 等价（挂起呈现在批 + 参数化选项问询，含 preview）。体量小。
9. **审批双通道加固**——已登记观察项（owner 2026-10-13 裁「记录不开发」）；列此保持清单完整，与 ZCode 集成呈递联动恢复。

**建议的取舍立场**：固件面机器强制安全不动摇；Agent 侧向业界收敛面对齐的最大三个杠杆 = ①流程结构层补齐（候选 1+2：把「单次工具调用面」升级为「可观测、可恢复的任务链」）②反馈回路闭环自动化（候选 3：部署域诊断自动回喂）③门禁可编程化（候选 4）。多代理（域内确定性已高）与通用文件工具面（域封闭面是安全边界）建议维持不做。

## 6. 结论

- 「编码约束」的业界答案已收敛：**五层模型**，且 2026 年的新增量集中在 L3 hooks 拦截面与 L5 流程结构层（plan/checkpoint/multi-agent）。
- Tessera Agent 的差异化优势在**域内机械门禁**（四道确定性门 + 双域对拍 + flash 审计）与**运行时观测反馈型回路**（五对象均无）——这两块是护城河，不追平、领先。
- 缺口集中在**流程结构层**：会话/任务链持久化、计划外显、拦截面、回放——恰好是「下一阶段重心 Agent 侧」最能借力业界成熟模式的位置（§5 候选 1-4）。

## 7. 来源汇总

- Codex：github.com/openai/codex（HEAD config.schema.json、codex-rs/core/src/tools/handlers/*、docs @40de81e7af：sandbox/config/agents_md/exec）
- opencode：opencode.ai/docs（tools/agents/permissions/plugins/lsp/rules/server/commands/config/mcp-servers/share/policies）+ anomalyco/opencode v1.19.0 源码（src/tool、src/lsp）
- Gemini CLI：google-gemini/gemini-cli docs/（tools/planning|shell|file-system|todos|tracker|memory|mcp-server、cli/session-management|checkpointing|sandbox|gemini-md|settings|custom-commands|auto-memory、core/subagents、hooks/reference、extensions、ide-integration）
- Claude Code：code.claude.com/docs/en（tools-reference、permissions、permission-modes、hooks、sub-agents、memory、skills、commands、sandboxing、context-window、checkpointing、mcp、plugins/overview、statusline、best-practices、vs-code、settings、agent-sdk/permissions）
- 本地：agent/tessera_agent/{platform,domain/firmware,gateway/approvals,gateway/server}.py（工具面/分级/token/传输核证）；docs/agent-codegen-reliability.md（R1-R8）
