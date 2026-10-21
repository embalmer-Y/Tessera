# HLD · Tessera Agent（AI 开发 Agent）· v0.2.3

> **状态**：v0.2.3 深度修订（2026-10-21，V0.13.0 收口——V0.12「Agent 协同批」与 V0.13「Agent 自主化批」全部架构面入册：MCI 多渠道交互层 / web 渠道 / 事件总线 / 问询审批双向化 / BV1 板卡验证域 / MP 内存审计 / clarify 双模式 / 硬件定向与硬件事实域）。v0.2 深度修订（2026-10-13，DEC-56/57）为基座；输入：DEC-11/12 v1.1、DEC-56/57、Q-38 全 A、DEC-65/66/67/68/69/70/71/72/73、R6/R7。
> **输入（承继已裁）**：DEC-33（多域北极星）/DEC-34/35/36/37/38（原 v0.1 决策链全部维持）。
> **固件侧合同**（既有约束）：TSAP v2、zenoh 命名空间、prov CBOR、sys 命令面、native_sim、安全与确定性合同（AGENTS.md §6）。

## 0. 任务与范围（v0.2 重述）

Tessera Agent = PC 侧（Linux）**全 Python 单进程程序**，**双角色**（DEC-12 v1.1）：

1. **内嵌 AI 客户端**（独立终端 CLI）：人直接提需求 → Agent **独立完成**"需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署 → 诊断"全链，开发**任意复杂度**的 APP 与硬件配置（DEC-56）。
2. **server 门面**：经 MCP（既有，stdio + HTTP）供其他 AI 工具（ZCode/Claude Code/Cursor 等）消费同一能力链；A2A（DEC-36④）/ACP（DEC-35）预留缝维持。

**北极星（DEC-33）**：平台层与域工具解耦，未来接入 PCB/结构件等域 agent；**v0.2 新增的第三条结构原则**：创作循环引擎域无关（验证器为域插件——§2.2 A08），使"复杂工程创作"能力本身成为可被未来域复用的平台资产。

## 1. 系统上下文（v0.2.3：MCI 三层四渠道同根）

```text
人（终端）──TerminalFrontend(A09)──┐                      ┌── zenoh ──▶ 设备/zenohd
人（浏览器）──web 渠道(A11+W2)────┤                      │             （设备——形态不限）
外部 AI CLI ──MCP 门面(A01)──────┼─▶ compose 根（AppContext：│
外部 harness ──pi 渠道（M1 HOLD）─┘   cfg/budget/audit/    │
                                     tasks/policy/skills/events）┴── 子进程 ──▶ west/clang/twister/pytest
                                     │                                      （只读白名单+审计）
                                     ├── A02 会话编排（PydanticAI 循环；clarify 双模式前置域）
                                     ├── A08 创作工作区（循环引擎+工作区+快照）
                                     ├── A10 MCI 交互层（EventBus 直推 /events v2——快照+Last-Event-ID 续传）
                                     └── 域工具（固件 DomainPack：fw/sim/tsap/deploy/ln/app_*/bv1/mp/hw 面）
```

**MCI 三层（DEC-66 · LLD-A10）**：Transport（stdio/HTTP——FastMCP 既有）/ Interaction（ApprovalBroker/QuestionBroker/Task.progress + **EventBus 直推**）/ Renderer（各渠道呈现——web 呈现层见 LLD-A14）。**四渠道 = 同一 compose 根的四个客户端**；服务端闸 = 管所有渠道的真边界（D4 hooks 拦截面）。

**四条铁律**：①全渠道共享同一 compose 根（同一审计流/任务注册表/审批闸/事件总线——不是多套系统）；②创作面放宽、**交付门不撤**（§5.2 清单）；③工作区永不入仓（gitignore 常设）；④**判据行保真合同**（W2）：普通模式文案层为叠加摘要，日志区逐字原文且开发者模式全显——判据呈现零改写。

## 2. 分层架构与模块清单（v0.2 增 A08/A09）

```text
┌─ 门面层（Frontend 实现 ×2，ACP 预留第 3）────────────────┐
│ A01 mcp-gateway：FastMCP 门面（双层工具面/句柄/审批呈现）     │
│ A09 terminal-facade：交互式终端（进度/问询/审批/汇报/resume） │
├─ 会话编排层（平台层，与传输解耦）──────────────────────┤
│ A02 agent-core：会话编排/审批闸/结构化产物/审计导出           │
│ A08 creation-workspace：循环引擎/工作区/域验证器接口/会话快照  │
│ A07 skills+platform：skill loader + DomainPack 接口 + 预留   │
│ A10 mci-channels：EventBus 直推 + /events v2 + 状态灯派生单源  │  ← V0.12 新增
├─ 交互域（Agent 能力增量——创作循环前置/配套）────────────┤
│ clarify 双模式域 / BV1 板卡验证域 / MP 内存审计域 / HW 硬件定向+事实域 │  ← V0.12/13
├─ 域工具层（固件域 = 第一个 DomainPack）────────────────┤
│ A03 fw-tools / A04 sim-harness / A05 tsap-tools / A06 deploy-net │
│ ＋FirmwareCreationVerifier（A08 验证器的固件域实现）          │
├─ 公共 ──────────────────────────────────────────────┐
│ A00 common：错误模型/任务模型/审计/配置/子进程纪律            │
└──────────────────────────────────────────────────────┘
```

| 模块 | 职责 | 规格 |
|---|---|---|
| A00 common | 错误模型、任务模型（Tasks V2 语义）、审计双流、配置、asyncio/子进程纪律 | LLD-A00 |
| A01 mcp-gateway | FastMCP 实例、工具注册表、长任务句柄、中间件、审批呈现工具对、**审批参数规则求值（Q-38⑤）** | LLD-A01（修订） |
| A02 agent-core | SessionOrchestrator、PydanticAI Agent 构造、审批闸、结构化产物校验、提供者配置 | LLD-A02（修订） |
| A03…A06 | 原职责不变（fw/sim/tsap/deploy 工具族） | LLD-A03…06 |
| A07 skills+platform | skill loader、DomainPack 接口、A2A/ACP 接入缝 | LLD-A07 |
| **A10 mci-channels** | **EventBus**（common/events.py——线程安全 publish/每订阅者队列慢消费者 resync/环形缓冲 Last-Event-ID 重放）+ registry/brokers 发布钩子（bus=None = 现行为逐字节等价）+ gateway/web.py（/events v2：快照首帧+直推+续传+15s 心跳+10s 对账兜底；derive_phase 11 态单源）+ gateway/hooks.py（D4 pre deny/observe + post observe——服务端闸管全渠道）+ gateway/mcp_clients.py（A5 外部 MCP server 桥接——strict 双闸） | LLD-A10/A14/A15 |
| **web 渠道（A11+W2）** | 零 Node 纯 Python 前端（agent/web/ 五文件）+ 双模式（clarify 普通模式）+ 历史任务栏 + ZCode 式任务切换 + 判据行保真文案层 | LLD-A11/A14 |
| **交互域（V0.12/13）** | domain/clarify.py（需求澄清五步 + **HW S0 硬件定向槽**）/ domain/board_validation.py（BV1 画像 C1-C6 检查流水线）/ domain/memory_audit.py（MP 三层账本 R0-R7）/ domain/hardware.py（HW 硬件事实域：caps×画像机械门/声明-调用一致性/Zephyr 收录检索/选型预筛） | LLD-A12/A13/A14/A16 |
| **A08 creation-workspace** | **创作循环引擎**（状态机/轮次预算/计划跟踪/证据回喂）、**工作区模型**（roots/工程清单）、**scoped 编辑工具**（ws_read/write/edit/list）、**域验证器接口**（`CreationVerifier` 协议）、**会话快照与 resume** | **LLD-A08（新）** |
| **A09 terminal-facade** | 终端门面：需求输入→循环驱动→进度渲染→问询/审批交互→结果汇报；`--resume/--yes/--json` | **LLD-A09（新）** |

### 2.1 MCP 工具面（双层；v0.2 增量 = app_develop 升级，不加新 MCP 工具）

原子层 33 个维持（sys/task/fw/sim/tsap/deploy/ln/diag/spec_check/simreal_diff）；高层 `app_develop` **升级为循环后端**（入参不变，内部走 A08；返回任务句柄，循环过程经 task_log 观测）——外层 AI CLI（ZCode 等）自带文件工具，无需 MCP 暴露 ws_*（**MCP 面维持窄**是安全属性，不是能力缺失；终端门面与循环内部才是创作面）。`app_deploy/tsap_*` 语义不变。

**v0.2.3 工具面增量（V0.12/V0.13 全批）**：`app_clarify`（confirm——普通模式澄清+交棒）/ `task_progress`（D2 结构化进度）/ `sys_pending_questions`+`sys_answer`（D7 问询双向化）/ `sys_approve`（D4 allow/allow-session/deny 三维）/ `sys_timeline`+CLI replay（D5 决策链回放）/ `sys_tasks`（W2 多任务）/ `board_validate`（BV1，strict）/ `memory_audit`（MP，confirm）/ `web_search`（HW-2，confirm——Tavily keyless 出站面）。服务端闸语义全渠道一致；A5 桥接面 `x_<server>_list/_call` 按配置注册（外部工具默认 strict 双闸）。

### 2.2 创作循环（A08 核心——域无关引擎 + 域插件）

**状态机**：`DRAFT → PLANNING → IMPLEMENTING ⇄ VERIFYING → CONVERGED → PACKAGED`（任一步预算耗尽/不可收敛 → `FAILED` 带证据归档）。轮次预算默认 12（config；每轮 = LLM 一次工具循环）。

**每轮证据自动回喂**（Q-38① 核心，opencode LSP 模式）：编译 stderr 全文（-4KB 截断）+ sim 判据 diff（miss 行）+ 真机串口 miss 模式——**自动附在下轮用户侧消息**，不靠模型记得去查。

**工作区模型**：`agent/workspace/<task_id>/{project/, artifacts/, .session/, project.json}`；`project.json` = 工程清单（文件表/导出表〔四回调 fail-closed〕/tier 声明/manifest 草稿/资源清单）——**多文件工程的单一事实源**，编译与打包都从它派生。

**scoped 编辑工具**（循环内部 PydanticAI 工具，非 MCP 面）：`ws_read`（分页/行号）、`ws_write`、`ws_edit`（唯一 old_string 锚定 + replace_all，R7 §5 证据：小文件整文件再生、大文件锚定替换）、`ws_list`。roots：rw = 本任务工作区；ro = DomainPack 声明的仓库白名单（固件域 = `firmware/module/tessera/include/`、`agent/skills/`、`docs/`）；路径逃逸 = `_resolve_within` 既有纪律；IR2-03 读面纪律对仓库只读面全量维持。

**域验证器接口**（`CreationVerifier` 协议——DEC-33 结构原则落点）：
```python
class CreationVerifier(Protocol):
    def compile(self, project) -> CompileResult        # clang 聚合多文件（Q-39①：-Wl,--export= 逐符号）
    def simulate(self, project, scenario) -> SimResult  # sim 重放 + 判据 diff
    def face_check(self, wasm) -> FaceReport           # 导入⊆白名单/导出齐/尺寸档门
    def package(self, project, key) -> TsapArtifact    # 双编译一致 + 签名（唯一出口）
```
固件域实现 = FirmwareCreationVerifier（wasm_build 多文件化 + A04 sim + A05 打包）。**未来 PCB/结构件域 = 换 Verifier 即复用整个循环引擎**——循环引擎不含任何固件语义。

**会话快照**（Q-38④）：`.session/snapshot.json`（工程文件内容哈希表 + 计划状态 + 轮次摘要 + 预算计数 + 判据表），原子写（tmp+rename）；resume = 快照重建循环状态 + LLM 上下文由轮次摘要重组（非全量对话回放——审计流仍有全量）。

### 2.3 终端门面（A09 = Frontend 第二实现，DEC-35 缝的第一次兑现）

- **交互契约**：需求（argv 或交互输入）→ 计划呈现〔config 可开确认门〕→ 逐轮进度（计划项状态 + 轮次事件流）→ **交互点三处**：spec 歧义问询（选项呈现）/ strict 审批（token 终端输入——人在场语义成立）/ 判据确认 → 终报（判据命中行 + 产物路径 + 审计 ID + 部署状态）。
- 模式：默认交互；`--yes`（预批问询、审批仍拦 strict——安全默认）/ `--resume <task_id>` / `--json`（CI 流式输出）。
- 与 A01 共享 PolicyTable/broker——**审批语义两门面一字不差**（免维护双轨）。

## 3. 决策映射（v0.2 增量）

| DEC | 落点 |
|---|---|
| DEC-56/DEC-12 v1.1 | 双角色：A09 终端门面（内嵌客户端）+ A01 MCP 门面（server）——§1 三门面同根 |
| DEC-57 Q-38 | A08 循环引擎/工作区/快照 + A09 终端门面 + A01 审批参数规则 |
| DEC-57 Q-39① | Verifier.compile = clang 聚合多文件（工程清单驱动）；face_check 档位门（Q-39⑤） |
| DEC-33（结构原则③）| 循环引擎域无关 + CreationVerifier 域插件（§2.2） |
| DEC-38 #6 | 循环上下文 = 动态预算 + 70% 自动压缩（maybe_compress 上移一层，证据摘要保留） |
| 原有 DEC-33…38 落点 | 全部维持（§3 v0.1 表并入：A00…A07 职责与预留缝不变） |

## 4. 关键场景时序（v0.2）

- **S1/S3/S4/S5 维持**（原子直调/审批/长任务/部署——v0.1 语义不变）。
- **S2' 循环开发（替换 S2）**：`app_develop(spec)`〔MCP 或终端〕→ spec_check 门 → A08 建工作区 → PLANNING（计划呈现/确认）→ IMPLEMENTING（ws_* 编辑）⇄ VERIFYING（verifier.compile/simulate，证据自动回喂）→ CONVERGED → face_check + package（双编译一致+签名）→ 句柄返回，产物路径+审计 ID。
- **S6 终端独立会话**：`tessera-agent run "需求"` → A09 全程交互（§2.3）→ 终报。
- **S7 断点续跑**：进程重启 → `--resume` → 快照重建（计划/文件/预算）→ 从最近未完轮次继续。
- **S8 部署后诊断自动再入**（循环闭环延伸）：S5 部署判据 miss → diag_classify 证据 → 作为修复轮次回注 A08（预算内）——R6 §2「repair 从外环手动转为内环自动」。**v0.2.3 增量**：判据硬件感知（HW-4）——抓窗 `<TOKEN> WRITE REJECTED` 聚类 → 判据行命中而硬件写拒 = criteria_pass False（soft-pass/hard-invalid 机械降级）+ 回执证据入修复轮。
- **S9 普通模式澄清（W2-3）**：粗糙需求 → app_clarify → 缺口分析 → **S0 硬件定向槽（HW-1：mention 绑定/Zephyr 收录检查〔收录=BV2 工单/未收录=原理图协作〕/联网选型〔HW-3 机械预筛〕/暂不指定）** → 澄清轮 ≤3 → spec 合成（【目标硬件】段=定向产物）→ spec 门 → confirm 交棒 app_develop 同任务句柄；restart = 结构化中止。
- **S10 板卡验证（BV1）**：board_validate 画像 → C1-C6 流水线（SKIP 双型/overall 三态）→ 结构化报告；C6 阻断 = 板级专项候选（FIX-1 先例：如实 FAIL 不掩蔽）。
- **S11 硬件事实门链（HW-4）**：包装（face_check 声明-调用一致性——调 native 未申报 cap 拦）→ 部署（caps×画像机械门——物理通道无绑定装前拒，审批前拦截）→ 运行（判据硬件感知 + 回执诊断回喂）——三层全机械、LLM 拿事实不拿猜测。
- **S12 事件直推（W2-1）**：compose 根 EventBus ← registry/brokers 发布钩子 → /events v2（快照+直推+Last-Event-ID 续传+resync）→ web 状态灯 11 态/问询审批卡增量直加/活动心跳。

## 5. 安全与豁免链（Agent 无豁免；v0.2 重划创作/交付边界）

### 5.1 原五链维持
审批闸（三类策略 + **参数规则**）/工具内强制/审计双流/确定性同构/不学习同构——v0.1 §5 全部不变。

### 5.2 创作/交付边界（v0.2 核心安全属性）

**创作面（LLM 可达）**：本任务工作区文件 + 仓库白名单只读 + 循环内部 ws_* 四动词 + verifier 的 compile/simulate 结果。**爆炸半径 = 一个目录的文件 + 编译/重放计算**。

**交付门（一条不撤）**：clang 钉版 flags 编译 → natives 白名单面检查（聚合产物）→ 尺寸门（Q-39⑤ 分档双门）→ 双编译字节一致 → tsap_package 签名 → tsap_verify 复验 → 部署 → 判据行匹配。**工作区到可部署物的唯一出口 = verifier.package**——LLM 无论在循环里多自由，绕不过这道门上板。

**工作区纪律**：`agent/workspace/` 常设 gitignore；无凭据无密钥（密钥仅在 tsap_keygen 通道）；快照含源码不含对话全量。

### 5.3 审批参数规则（Q-38⑤）
PolicyTable 条目可选 `allow`/`deny` 参数规则（如 `deploy_push_app: {cube: [xiao-1]}`），求值序 = deny 规则 → allow 规则 → 类别策略 → broker；规则只可收紧（DEC-38 语义平移）；配置 = config（人工维护，不学习）。

### 5.4 v0.2.3 安全面增量（V0.12/V0.13）
- **服务端闸**（D4）：hooks 拦截面在 compose 根——pre deny = TA_E_POLICY 归因 + 审计 hook_denied；post 仅 observe（拒收解析期）。**全渠道同闸**（web/pi/CLI 无例外）；allow-session = 会话域记住集（进程生命周期不落盘）。
- **问询双向化**（D7）：QuestionBroker 单次应答契约 + 枚举域 fail-closed（answer 不在 options 拒）+ 超时取 default（无 default 超时异常）。
- **外部工具不信任面**（A5）：x_<server>_call 默认 strict 双闸（工具体审批 args 预览 + PolicyTable）；server 名净化防撞。
- **硬件事实三层门**（HW-4）：face_check 声明-调用一致性（包装前）→ caps×画像机械门（审批前装前拒）→ 判据硬件感知（运行期降级）——机械判定零 LLM，豁免面如实注记（log=TEST 语义 IR-16；net=数值面外）。
- **出站联网面**（HW-2）：web_search confirm 类 + 查询词凭据打码（sk-/Bearer/password=/长 hex → REDACTED）+ 查询/结果全量审计。
- **web 渠道红线**（W2）：服务端闸/审批 token（内存态不落存储）/审计同源/判据行保真——四红线不因渠道新增而松动。

## 6. 多域预留与北极星（维持 + v0.2 兑现）

§6.1 DomainPack、§6.2 A2A 预留、§6.3 ACP 预留——**v0.2 兑现一处**：A09 终端门面 = Frontend 抽象的第一个新增实现（证明门面层与传输解耦不是纸上缝——ACP 适配器将是第三个实现）。新增：CreationVerifier = 域插件的第二个扩展点（第一个是 DomainPack 工具注册）。

## 7. 里程碑（v0.2：Agent 批 AG 单元；MA0…3 已完成）

> **v0.2.1 现状注记（2026-10-16）**：AG1-AG8 全部完成（fw-v0.6.0 已 tag；AG7 真 LLM 四轮收敛多文件工程真机点亮）。此后续批：CG（合同泛化消费）/EC（生态）按 HLD-contract-v2 落地；§11f Agent 批追加 **D1 任务链持久化**（LnRegistry JSON 落盘/恢复/降级 + env 重定向——本文 M16 内存态注册表的"持久化再议"兑现）与 **D3 诊断自动回喂**（post_deploy_check：部署后健康检查 → 被动抓取 + 分类 → category/repair_hint/evidence 入部署回执；deploy_push_app 增 post_check_s/serial_port 直参）。**S8 已串联（P1-5 · 2026-10-16 交付）**：post_deploy_check 增判据面（pass_patterns——健康也抓窗对拍判据行；criteria_pass 三态：True/False/None〔未验证〕）+ CreationLoop.repair()（PACKAGED → 修复轮，证据经「上轮小结」通道回喂，S8_REPAIR_MAX=2、计入循环预算）+ CLI `--deploy --serial-port` 端到端闭环（部署 → 判据窗 → miss 自动修复轮 → 再打包再部署）。

| # | 单元 | 内容 | 依赖 | 退出标准 |
|---|---|---|---|---|
| AG1 | LLD-A08/A09 定稿 + A01/A02 修订 | 循环引擎/工作区/快照/终端门面规格 + 审批参数规则规格 | 本 HLD（owner 确认） | LLD 批确认（门③） |
| AG2 | 工作区 + scoped 工具 | 工作区模型/project.json/ws_* 四动词（roots 钳制/分页/锚定编辑）+ 单测矩阵 | AG1 | pytest：roots 逃逸/锚定失配/分页边界/白名单只读 |
| AG3 | 循环引擎 + 固件验证器 | 状态机/预算/计划跟踪/证据回喂 + FirmwareCreationVerifier（多文件编译聚合/sim 接线/判据表）| AG2 | FunctionModel 剧本：多文件工程 3 轮收敛/预算耗尽 FAILED 证据归档 |
| AG4 | 终端门面 | A09 交互循环（进度/问询/审批 token/resume/--json）| AG3 | 终端冒烟：需求→循环→终报；审批/断点续跑实测 |
| AG5 | 会话快照 + resume | 快照原子写/重建/上下文重组 | AG3（与 AG4 可并） | 杀进程重启续跑实测 |
| AG6 | app_develop 升级接线 + 审批参数规则 | MCP 面单向升级（无新工具）；PolicyTable 参数规则 + 求值链测试 | AG3 | MCP 面回归 + 规则矩阵测试 |
| AG7 | 复杂 APP 实测（真 LLM） | 多文件工程真 LLM 收敛 demo（≥3 文件/含状态机/kv）+ **large 档数值数据采集**（Q-39 数值补呈输入）| AG4/5/6 | 真机判据命中 + 数值报告 |
| AG8 | 收口 | 回归定格 + 文档同步 + tag fw-v0.6.0 | AG7 | 三连全绿 + 板级回归 |

**v0.2.3 现状注记（2026-10-21 · V0.12.0/V0.13.0 全部交付）**：V0.12.0（R11 调研 → D7 问询双向化 → D4 hooks → A10/A11 设计 → W1 web 客户端 → D5 回放器 → tag fw-v0.12.0）；V0.13.0（BV1 板卡验证域 D/I/R + FIX-1 板级崩机专项 + MP 内存规划〔LLD-A13：memory_audit R0-R7 + 最低内存基线〕+ W2 web 渠道重塑〔LLD-A14：EventBus/呈现层/双模式/收口 + 五缺陷验收修复 + 真机部署验证 + LED 缺陷如实记录〕+ A5 MCP 客户端 + A4 post 钩子 + R12/R13 调研 + HW 域〔LLD-A16：HW-1 定向槽/HW-2 web_search/HW-3 选型/HW-4 硬件事实五面+一〕+ BV2-D 设计〔LLD-A17 门③呈递〕→ tag fw-v0.13.0）。后续候选：BV2 实现（LLD-A17 门③三决策点待裁）/ pi 渠道（M1 HOLD——待 web 真实体验后决策）。

## 8. 测试策略（v0.2 增量）

- A08：状态机全转移矩阵/预算耗尽/证据回喂内容断言/快照往返一致性（杀进程实测）/roots 逃逸矩阵。
- A09：交互脚本化测试（pexpect 或输入注入）；审批/问询路径全覆盖。
- 真实 LLM 仅 AG7 冒烟（历史惯例：FunctionModel 剧本覆盖逻辑，真 LLM 验收收敛力）。
- CI：pytest + ruff 维持；A08/A09 测试零网络零 LLM 依赖。

## 9. V1 范围裁剪清单（v0.2）

不做：ACP/A2A 实现（缝保留；A09/A11 已证明缝有效）/多域 DomainPack 实现（Verifier 接口预留——BV1/MP/HW 已按域内确定性流水线定性落地，非 LLM 创作域不硬套 CreationLoop）/对话级回放（任务级快照 + W2 历史任务栏已覆盖；跨进程持久化 = v2——审计 JSONL 为持久事实源）/多客户端并发创作（单任务单工作区）/MCP 面暴露 ws_*（安全属性）/BV2 适配实现（LLD-A17 设计已落稿，门③三决策点待裁）/pi 渠道（M1 HOLD）。维持：上下文压缩（DEC-38）、HTTP 门面、A5 每调用连接（连接池 = v2）。

## 10. 未决依赖与呈递

- **C-6**：本 HLD v0.2 + LLD-A08/A09（AG1 产出后一并呈递确认，门③）。
- Q-39 large 档数值：AG7 实测后补呈（合同泛化批 CG4 消费）。
- 固件侧：多文件编译的 wasm 导出面检查器扩展（AG3 内联，wasm_build 既有解析器扩展）；判据表与 spec_gate 单一事实源维持。

## 修订记录

- v0.2.2 · 2026-10-16：P1-5——**S8 端到端串联**（post_deploy_check 判据面 + CreationLoop.repair 修复轮 + CLI --serial-port 部署闭环；测试 +6）。
- v0.2.1 · 2026-10-16：实现现状对照批（owner 指令）——§7 增完成态注记（AG1-8 ✅ + D1/D3 交付 + S8 半步登记）。
- v0.2 · 2026-10-13：**DEC-56/57 深度修订**——双角色定稿（A09 终端门面 = Frontend 第二实现）；新增 A08 创作工作区（域无关循环引擎 + CreationVerifier 域插件 + 工作区模型 + 会话快照）；§5.2 创作/交付边界（交付门清单一条不撤）；S2'/S6-S8 场景；AG1-8 里程碑（fw-v0.6.0）。质量优先条款（DEC-57）贯彻：循环引擎域无关/快照原子写/审批两门面同源。
- v0.1.1 · 2026-09-22：Q-19 → DEC-38 同步（§9 裁剪清单）。
- v0.1 · 2026-09-22：初版。
- v0.2.3 · 2026-10-21：**V0.13.0 收口深修**——V0.12（D2/D4/D5/D7/W1/MCI：A10 层 + web 渠道 + 问询审批双向化 + 回放器）与 V0.13（BV1/MP/W2/A5/A4/HW/BV2-D）全部架构面入册：§1 MCI 三层四渠道同根 + 四铁律（+判据行保真）/§2 A10 行 + 交互域行 + 工具面九增/§4 S9-S12 四场景 + S8 硬件感知增量/§5 §5.4 安全面六增/§7 现状注记/§9 裁剪清单更新。v0.2.2 停于 V0.6.0 时代之债清偿。
