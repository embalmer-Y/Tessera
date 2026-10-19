# LLD-A12 · 板卡验证域（Board Validation Domain）· v0.1

> **本文件是什么**：板卡验证域低层设计——V0.13.0 BV1-D 单元（DEC-68① 高优；owner「Agent 端应有能力在面对新板卡时自行进行验证工作」）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.1（2026-10-19 立项同批首稿；BV1-I 实现前如有修订走版本序）。
> **执行注记修订生效**：首任务 = **现役板自验**（atkbench/xiao——先在已知好板上证明验证域本身）；P4 判定批实测 = 第二任务（随 v4.5.0 平移批，DEC-68 注记修订 2026-10-19）。

## 1. 定位与架构定性

**板卡验证域 = 确定性检查流水线**：输入板卡画像 + 串口/网络通道，输出结构化 bring-up 报告。面向两类消费者：

1. **现役板例行自验**——部署前/联调前的板健康判定（Agent 自主执行，替代人工「看一眼串口」）；
2. **新板 bring-up 验证**（P4 判定批形态）——新板卡接入后 Agent 半自主跑最小链（boot→PSRAM→WAMR→wasm→判据行），报告即判定批证据。

**与 CreationLoop 的关系（诚实定性——质量优先条款自查）**：板卡验证**不硬套**创作循环。CreationLoop 是 LLM 驱动的创作状态机（DRAFT→PLANNING→IMPLEMENTING⇄VERIFYING→PACKAGED），其价值在「生成-验证-修复」的生成侧；板卡验证是**确定性检查序列**——每步判据机械、无生成物、关键路径零 LLM。继承的是 DEC-33 的**原则面**而非引擎本体：

| DEC-33 原则 | BV1 落点 |
|---|---|
| 域插件（能力以域为单位扩展，平台零感知） | `domain/board_validation.py` 独立域模块 + DomainPack 接线 |
| 结构化证据（detail 原文不截断不美化——R6 纪律） | CheckResult.evidence 逐字保留（含失败原文——诊断域输入） |
| 事件/审计面同源 | 检查进度经 Task.progress（D2 面）+ 执行留痕经审计流（D5 时间线可回放） |
| VerifyOutcome 同型 | CheckResult 形状对齐（verdict/detail/evidence/facts） |

**LLM 的位置（可选阶段，非关键路径）**：报告 FAIL 时可选诊断阶段——失败检查的 evidence 喂 PydanticAI runner 出修复建议（复用 diag_classify 既有 7 类分类器为主，LLM 为辅）。v1 仅留缝不实现（诊断分类器覆盖面已实测够用——NPC/R2/R5-V 历次破案均机械证据定案）。

## 2. 板卡画像 schema v1（`agent/boards/<board_id>.toml`）

画像 = 板卡期望的**声明式清单**——验证域的可移植单元；新板接入 = 写一份画像（+ 必要时新增检查项），验证器代码零改动。无凭据（WiFi/prov 密钥不入画像——运行时经 env/config）。

```toml
[board]
id = "atk-dnesp32s3b"              # 画像标识（= 文件名 stem）
description = "正点原子 ATK DNESP32-S3B V1.1（es8311+SD+LCD）"

[serial]                            # C1 串口在场 + 全部串口检查的通道
port = "/dev/serial/by-id/usb-1a86-CH343-if00-uart0"   # 稳定路径纪律（一四六教训：观察器走 by-id）
baud = 115200

[flash]                             # C2 flash 身份
adapter = "esptool"                 # v1 仅 esptool（west flash 同族语义）
chip = "esp32s3"                    # flash-id 期望 chip 名
size_kb = 16384                     # 期望容量（真硅口径——教训：声明与实测校准，boya 16MB 案）

[boot]                              # C3 boot/console 判据
reset = true                        # 验证前是否执行复位（诊断像/产出像均 true）
ready_patterns = ["CONNECTED loc="] # 就绪判据行（逐字——判据行保真合同）
timeout_s = 90                      # atkbench boot ~50s 实测口径 × 裕度

[zenoh]                             # C4 连通与命令面（locator 来自运行时 config，不入画像）
expect_discover = true              # discover() 应见本板 node
probe_ops = ["status"]              # 命令面探针（get-info 同族；缺省 ["status"]）

[caps]                              # C5 caps 消费（可选节——缺省跳过并注记 SKIP）
tiers = ["small"]                   # 期望 tiers 包含
min_slot_pool_kb = 512              # 期望槽池下限

[smoke]                             # C6 部署 E2E 冒烟（可选节——缺省跳过）
package_path = "agent/demos/NVD/nvd.tsap"   # 测试根签名探针包（仓相对路径）
pub_path = "agent/demos/NVD/nvd.pub"
criteria = ["NVD DONE"]             # 判据窗 pass_patterns

[build]                             # C0 可选构建/烧录前级（新板 bring-up 形态用；现役板自验缺省关）
enabled = false
app_target = ""                     # west -b <board> <app> 目标串
```

**画像即能力目录的种子（R12 前哨）**：R12 调研的「板卡能力目录 schema」以本画像为消费起点——目录 = 画像 ∪ 外设/资源扩展面，避免两套事实。

## 3. 检查项目录 v1

| # | 检查 | 判据 | FAIL 处置 | SKIP 条件 |
|---|------|------|----------|----------|
| C0 | 构建/烧录前级 | fw_build rc=0 + 烧录完成 | 报告终止（后续检查无意义） | 画像 `[build] enabled=false`（缺省） |
| C1 | 串口在场 | port 存在且可打开（by-id 解析） | 终止（物理域——提示接线） | — |
| C2 | flash 身份 | esptool flash-id：chip == 期望 ∧ size == 期望 | 记 FAIL 继续（身份错 = 镜像/prov 风险，值得看全貌） | — |
| C3 | boot/console | reset+capture 窗内命中全部 ready_patterns | 记 FAIL 继续（C4 起大概率连败——stop_on_fail 可提前收） | — |
| C4 | zenoh 连通 | discover 见 node ∧ probe_ops 全回执 | 记 FAIL 继续 | C3 FAIL 时自动 SKIP（链路前置） |
| C5 | caps 消费 | get-info caps ⊇ 画像期望（tiers 包含 ∧ 槽池 ≥ 下限） | 记 FAIL（能力不达 = 部署预期落空） | 画像无 `[caps]` 节 → SKIP（注记：旧固件/未声明） |
| C6 | 部署 E2E 冒烟 | deploy 全链 + 判据窗命中 criteria（复用 post_deploy_check 三态） | 记 FAIL | 画像无 `[smoke]` 节 → SKIP；C4 FAIL → SKIP |

**SKIP 语义**（periph 三路失败破案纪律——物理失联 ≠ 验证失败）：SKIP 不计入 FAIL，但计入 DEGRADED 判定（见 §4）。C3→C4 的链路 SKIP 是**派生 SKIP**（detail 注明「前置检查未过」），与画像声明的 SKIP（节缺失）区分。

## 4. 流水线与报告

### 4.1 执行模型

```text
BoardValidator.validate(profile, *, checks=None, stop_on_fail=False,
                        transport, progress_cb) -> BoardReport
```

- **串口独占纪律**（三读抢数教训——NVD 案）：验证全程独占串口；esptool（C2）与 capture（C3）串行分相执行，不并发持口。文档级约定：验证期间 console 持有器须暂停（与 bench 判据编排同纪律）。
- 检查顺序固定 C1→C2→C3→C4→C5→C6（C0 可选在最前）；`checks` 参数可裁剪子集（裁剪含依赖时派生 SKIP 同规则）。
- 每检查完成即经 `progress_cb` 落 Task.progress（D2 面：`{stage: "board_validate", check: "C3", done: 3, total: 6, verdicts: {...}}`）——web 渠道（W2）直读。

### 4.2 数据形态（对齐 VerifyOutcome 同型）

```python
@dataclass
class CheckResult:
    check: str            # "C1"…"C6"/"C0"
    verdict: str          # "PASS" | "FAIL" | "SKIP"
    detail: str           # 一行人读结论
    evidence: list[str]   # 原文行（不截断不美化）
    facts: dict           # 机械字段（chip/size/caps/discover 节点表…）
    dur_ms: int
    derived_skip: bool    # 派生 SKIP（前置未过）vs 声明 SKIP（节缺失）

@dataclass
class BoardReport:
    board_id: str
    started_at: float
    dur_s: float
    overall: str          # "PASS" | "FAIL" | "DEGRADED"
    checks: list[CheckResult]
    def to_json(self) -> dict      # 机读形态（--out 落盘）
    def render(self) -> str        # 人读形态（Renderer 契约——判据行逐字）
```

**overall 判定规则**：任一 FAIL = `FAIL`；零 FAIL 且存在 SKIP = `DEGRADED`；全 PASS = `PASS`。

**板态变更披露（合同级诚实条款）**：C6 冒烟会**变更板态**（探针 APP 驻留 ACTIVE 槽）。报告 facts 记录冒烟前 get-app 状态（state/slot/app_id）；v1 **不自动还原**（还原 = 重部署原包——超出验证域职责，repair_hint 给出处置建议）。画像 `[smoke]` 节的存在即板态变更的显式授权——无节板卡零板态扰动（C1-C5 全只读或可逆）。

## 5. 面接线

| 面 | 形态 | 备注 |
|---|------|------|
| MCP `board_validate` | spawn 后台任务（长时面惯例）→ task_id；strict 类 | 政策表登记 `"board_validate": "strict"`（与 deploy 同族——含板态写入与复位）；审批一次覆盖整轮 |
| CLI `tessera-agent validate` | `<board_id> [--checks C1,C3] [--out report.json] [--json]` | AppContext 最小装配（同 run 子句柄）；退出码 0=PASS / 1=FAIL 或 DEGRADED / 2=参数错 |
| 进度面 | Task.progress（§4.1） | task_progress 工具 + W2 web 直读——零新外显面 |
| 审计/回放 | 既有审计流（D5 同源） | validate 全程 = 时间线可回放条目 |

**DomainPack 归位**：`board_validation` 作为 firmware 域 extras 挂入 sys_get_info（`domains[].board_validation = {profiles: [...], checks: [...]}`）——不新开域包（域间无独立状态，画像装载共享 config 面）。

## 6. 安全与纪律

1. **strict 类缺省**：board_validate 含复位/烧录探针/板态写入——与 deploy 族同严格度；allow-session（D4）可供连续自验会话放行，token 纪律不变。
2. **串口独占**：§4.1；观察者/持有器冲突 = C1 即 FAIL（fail-fast，不与持有器抢数）。
3. **零凭据面**：画像无密钥无 WiFi；探针包 = 测试根签名（生产根不入验证域）。
4. **只读优先**：C1-C5 均只读或可逆（复位除外——画像 `reset=false` 可关，用于「不扰动在跑业务」的巡检形态）；C6 变更须显式画像授权（§4.2）。

## 7. 测试口径（BV1-I）

- **FakeBoard 传输注入**：检查项依赖 `BoardTransport` 协议（port 存在性/打开/复位抓取/flash-id 查询/zenoh 服务）——sim 级全矩阵：每检查 PASS/FAIL/SKIP 三态 × 派生 SKIP 链 × stop_on_fail × overall 三态判定。
- **画像装载**：好画像/缺节画像/坏字段画像（fail-closed——未知字段拒绝装载，防拼写静默失效）。
- **面测试**：MCP spawn+strict、CLI 退出码三态、progress_cb 序列、报告 JSON/文本双形态字段完备。
- **真机判据（BV1-R）**：atkbench 全链 PASS 报告入仓证据 + xiao 第二画像复验——① 的验收即实战。

## 8. v2 方向（不进本批，登记防丢）

- **自动修复轮**（DEC-68①「迭代修复」完整形态）：FAIL → 修复动作表（重烧/复烧 prov/换口重试）→ 重验——P4 判定批（build+flash 自动化）为首个真实需求，届时按实据立项。
- **LLM 诊断阶段**：evidence → PydanticAI runner 修复建议（§1 留缝）。
- **R12 消费**：画像 → 能力目录扩展面（外设/资源/算力画像）。
- **连续巡检形态**：`reset=false` + 定时自验 → 健康时序（与 zenohd 常驻化同族——路由器级持久化决策随 owner）。
