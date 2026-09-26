# docs/project-plan.md · Tessera 统一项目开发计划

> **版本**：v1.0 · 2026-09-22 · 依 owner 指令与 **DEC-39** 建立（"整个项目统一规划并着手开发"）。
> **权威顺序**：owner 最新裁决（decisions.md DEC）> `FOUNDING_PROMPT.md` > 本计划。计划变更走修订记录；里程碑进出走 review 门（流程 §2.4-②）。
> **结构**：双轨并行——**轨道 A（固件框架，M 系）** 与 **轨道 B（AI Agent，MA 系）**；交叉依赖见 §4；实施节奏（单会话一交付单元，军规/流程 §2.3）建议排序见 §7。

## 1. 总体路线（DEC-15 三阶段，执行节奏并行化）

1. **阶段一 · 固件框架**（native_sim 上可运行）：M0 → M1 → M2a → M2b → M3a → M3b → 板级移植。
2. **阶段二 · AI Agent + 模拟器**：MA0 → MA1 → MA2 → MA3。
3. **阶段三 · 硬件立方体定型**：连接器/结构/电源（依赖软件形态验证）。

双轨并行不改变阶段内容顺序，仅执行节奏并行（DEC-39）；北极星（DEC-33：多域 → 机器人/Galatea 自生产）为方向约束，不进 V1 里程碑。

## 2. 轨道 A · 固件框架（M 系；DoD 详见 `design/HLD-firmware-framework.md` §7）

| 里程碑 | 范围 | 状态（2026-09-22） | 退出标准 |
|---|---|---|---|
| **M0** 环境/骨架/CI/LICENSE | west 工作区 + native_sim 模块构建 + CI 骨架 + LICENSE | **本地全绿**（WSL：构建 + twister 运行级 + pytest）；余 = GitHub 远端推送（owner 待办 §5） | 推送 + CI 绿（tag `m0`） |
| **M1** | ts-core + ts-safety + L5 机械检查脚本 + **L4 重放框架雏形**（MA2 的接口依赖，见 §4） | **本地全绿（2026-09-22，DEC-39 后开工）**——退出 review 门已呈报；CI 上线随远端 | HLD §7 M1 DoD |
| **M2a** | ts-store + TSAP 格式定稿 + slot（A05 manifest 镜像依赖） | **本地全绿（2026-09-22）**——twister 5/5 配置（新增 framework.store）；TSAP v1 定稿（16B 头/大端）；L5 增第 6 项（prov 零写） | HLD §7 |
| **M2b** | ts-hal 权限（ts_perm_v1）+ WAMR 宿主 + 样例 APP | **M2b 本地全绿（2026-09-23）+ 补审查 IR-05…20 处置（同日）**；M2b.2 进行中——环境批 + Q-23 实证批 + DEC-43 锁收口批交付（2026-09-26）；**接线批第二单元交付（同日）：APP 运行时宿主（执行线程/mailbox/停止/健康自停）+ ts_api_v1 natives + framework.app 端到端——twister 14/14（57 用例）全绿**；余 = M2b.2 收尾单元（boot slot 装载 + 默认翻转 + E2E wasm 化） | HLD §7 |
| **M3a** | ts-net（zenoh-pico；发现/key/sys 命令——A06 对齐依赖） | **M3a.1+M3a.2 本地全绿（2026-09-23）**：传输缝 + keyspace/pubq/session/linkmon + sys 命令面（host-only 7 项，最小 CBOR 定体编解码）+ 遥测/事件发布 + boot net_init 接线 + zenoh-pico 1.10.1 真实绑定（含 queryable/订阅）编译链接绿；**L3 端到端 PASS（2026-09-23，dev-environment §8）**；**DEC-40/41/42 增强批落地（2026-09-23，提交 486427c）：命令信封 v2+幂等缓存/控制租约/事件遥测 ver+kind 信封+QoS 映射/is_up 任务自省/TCP-TLS locator 校验——L3 扩展为五验证点全 PASS，twister 8/8（35 用例）** | HLD §7 |
| **M3b** | ts-power + ts-periph（外设桩——A04 深度仿真依赖）+ 集成重放 | **本地全绿并退出（2026-09-25）**：ts-power（供电槽/预算/限流/事件 + get-budget + kind 97 遥测）+ ts-periph（描述符职责链/插拔→单通道 SAFE_FAULT）+ replay 集成场景（预算+插拔 golden）；impl-review-01 修复批（同日）后回归口径 = twister 10/10（46 用例）/L5 6/6 全绿 | HLD §7 |
| **板级** | ESP32-S3 → ESP32-P4 → STM32H7 | **启动中（2026-09-26）**：板卡定为 **xiao_esp32s3**（owner 已接入，DEC-43④ 真机双核终验载体）；espressif 工具链已装；WSL2 USB 串口不可见（烧录策略待定：usbipd-win / Windows 侧 esptool） | 前置就绪；Zephyr SDK 不需要（ESP32 走 espressif 工具链） |

## 3. 轨道 B · AI Agent（MA 系；DoD 详见 `design/HLD-agent.md` §7）

| 里程碑 | 范围 | 状态（2026-09-22） | 退出标准 |
|---|---|---|---|
| **MA0** | agent/ 骨架（包结构/config/CLI 桩/CI 接线）+ DR-18（versioning Python 钉版节）+ DR-19（dev-env agent venv 节） | **本批开工（DEC-39）** | 本地 pytest + ruff 绿；CI yaml 就绪（上线随远端，同 M0 惯例） |
| **MA1** | A00+A01+A02+A03：网关/编排/审批闸/审计 + fw_* 最小集 + sys_*/task_* | **本地全绿（2026-09-22）**——FastMCP 客户端实测（sys/task/审批流）+ fw_pytest 与 fw_build 句柄化实测；CI 随远端 | MCP 客户端实测：build 句柄化跑通 + 审批流实测 ✓ |
| **MA2** | A04 模拟器 + A05 TSAP 签名 | **本地全绿（2026-09-22）**——pytest 33+1(E2E 实证) 全绿：TSAP 往返+双实现互验+篡改矩阵；sim E2E 真实构建+双跑确定性绿 | 签名往返 + 双实现互验 + smoke 确定性比对绿 ✓ |
| **MA3** | A06 zenoh 部署 + A07 skills + 高层链 app_develop/app_deploy | **本地全绿并退出（2026-09-25，MA3.1+MA3.2）**：MA3.1 部署链（固件 sys/app-* gated + deploy_* 工具 + E2E spec→TSAP→部署仿真立方体）+ MA3.2（skills 4 项+loader+同步检查/DomainPack 平台域拆分+导入图测试/高层链 app_develop·app_deploy + A2A/ACP 接缝）；**例外登记**：push_prov 随维护模式语义后批（LLD-A06 §6）；CI 上线随远端 | 端到端：spec → TSAP 包 → 部署到仿真立方体 ✓ |

## 4. 交叉依赖（双轨咬合点）

| Agent 侧 | 依赖固件侧 | 交付物对齐 |
|---|---|---|
| MA2 模拟器 | **M1** L4 重放框架雏形 | 输入注入/输出捕获协议（LLD-A04 §2 接口约定，M1 设计时共同定稿） |
| MA2 TSAP | **M2a** TSAP 格式定稿 | manifest 字段镜像（LLD-A05 §2） |
| MA3 部署 | **M3a** ts-net | 发现/liveness key、sys 命令实现、APP 安装入口、维护模式语义（LLD-A06 §6） |
| MA3 模拟深度 | **M3b** 外设桩 | 场景 channel_kind 扩展位 |
| 共同 watch | **Zenoh 2.0**（上游计划 2026 H2） | 三方（zenohd/eclipse-zenoh/zenoh-pico）联合升级 + 全量回归——M3a/MA3 前评估 |

## 5. owner 待办（阻塞项）

1. **GitHub 远端地址**（DEC-24）→ M0 完整退出（tag `m0`）+ CI 上线（固件与 agent 两个 job 同时点亮）。
2. **Zephyr SDK for Linux 下载**（~1GB；板级移植前置；native_sim 开发不需要）。

## 6. 环境与基础设施事实源

- `docs/dev-environment.md`：WSL 目录规范（`~/project/{tessera,zephyrproject,logs}`）+ 固件 venv；**MA0 起增补 agent venv（`~/project/agent-venv`，DR-19）**。
- CI：`.github/workflows/ci.yml`（repo-checks → 固件构建/twister → **agent lint+pytest（MA0 接入）**）。

## 7. 会话交付单元建议排序（单会话一单元，流程 §2.3）

M1 → MA1 → M2a → MA2 → M2b → M3a → MA3 → M3b → 板级（S3）→ …
（原则：依赖就绪先行的最小单元；任一里程碑 DoD 全绿才进下一个；M/MA 交替推进双轨。）

## 8. 执行纪律（不变）

- 规范套件（tag `std-v1`：testing/versioning/progress/coding）+ 军规十条 + 安全与确定性合同（AGENTS.md §6）。
- 里程碑退出 = review 门（呈递 DoD 对照）；工具面/公共 API/安全合同变更 = 各自 review 门。
- 进度记录规则按 `docs/std/progress.md`；本计划的状态列随里程碑更新。

## 修订记录

- v1.0 · 2026-09-22：初版（DEC-39 授权；双轨统一；MA0 同批开工）。
- v1.1 · 2026-09-22：M1 状态更新（本地全绿：twister 4/4 配置 12 用例 + L5 5/5 + pytest；L4 雏形接口随 M1 定稿 = 编译期内嵌场景 + stdout JSONL + 退出码）。
- v1.3 · 2026-09-25：MA3 行更新（MA3.1 部署链 E2E 全绿；MA3.2 余项 = A07 skills/DomainPack/app_develop/app_deploy）。
- v1.9 · 2026-09-26：接线批第二单元（APP 运行时宿主 + natives + framework.app，twister 14/14〔57 用例〕）；M2b.2 余 = 收尾单元（boot slot 装载/默认翻转/E2E wasm 化）。
- v1.8 · 2026-09-26：DEC-43 实现批（锁收口 + framework.conc，twister 13/13〔54 用例〕）；板级行更新（xiao_esp32s3 定板 + espressif 工具链就绪——ESP32 不需要 Zephyr SDK）。
- v1.7 · 2026-09-26：M2b 行更新——M2b.2a 环境批交付（WAMR-2.4.5 接入 + framework.wamr 冒烟，twister 11/11〔47 用例〕）；接线批前置 = Q-23（宿主线程模型/并发收口，F-7 落点）。
- v1.6 · 2026-09-25：M2b 行补开工前置检查项（impl-review-01 F-7 并发防护复核——WAMR 多线程接入前裁定）；M3b 行回归口径更新为 46 用例（impl-review-01 修复批：twister 10/10〔46 用例〕）。
- v1.5 · 2026-09-25：M3b 行更新（里程碑退出；固件轨 M0…M3b 全绿，余 = M2b.2〔WAMR，需网络〕与板级移植〔前置 Zephyr SDK〕）。
- v1.4 · 2026-09-25：MA3 里程碑退出（MA3.2 交付：skills/DomainPack/高层链；58 用例 + ruff 全绿；push_prov 例外登记）。
- v1.2 · 2026-09-23：M3a 行补 DEC-40/41/42 实现批次（信封 v2/租约/事件遥测信封/QoS/is_up；L3 五验证点；twister 35 用例全绿，提交 486427c）。
