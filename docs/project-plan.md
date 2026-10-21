# docs/project-plan.md · Tessera 统一项目开发计划

> **版本**：v1.37 · 2026-10-09（v1.0 · 2026-09-22 · 依 owner 指令与 **DEC-39** 建立）.
> **权威顺序**：owner 最新裁决（decisions.md DEC）> `FOUNDING_PROMPT.md` > 本计划。计划变更走修订记录；里程碑进出走 review 门（流程 §2.4-②）。
> **结构**：双轨并行——**轨道 A（固件框架，M 系）** 与 **轨道 B（AI Agent，MA 系）**；交叉依赖见 §4；实施节奏（单会话一交付单元，军规/流程 §2.3）建议排序见 §7。

## 1. 总体路线（DEC-15 三阶段，执行节奏并行化）

1. **阶段一 · 固件框架**（native_sim 上可运行）：M0 → M1 → M2a → M2b → M3a → M3b → 板级移植。
2. **阶段二 · AI Agent + 模拟器**：MA0 → MA1 → MA2 → MA3。
3. **阶段三 · 硬件立方体定型**：连接器/结构/电源——**已按 owner 2026-10-07 指令排除出开发范围**（v1.30；板级固件面〔S3 余项/P4 适配〕仍属轨道 A 保留）。

双轨并行不改变阶段内容顺序，仅执行节奏并行（DEC-39）；北极星（DEC-33：多域 → 机器人/Galatea 自生产）为方向约束，不进 V1 里程碑。

## 2. 轨道 A · 固件框架（M 系；DoD 详见 `design/HLD-firmware-framework.md` §7）

| 里程碑 | 范围 | 状态（2026-09-22） | 退出标准 |
|---|---|---|---|
| **M0** 环境/骨架/CI/LICENSE | west 工作区 + native_sim 模块构建 + CI 骨架 + LICENSE | **本地全绿**（WSL：构建 + twister 运行级 + pytest）；余 = GitHub 远端推送（owner 待办 §5） | 推送 + CI 绿（tag `m0`） |
| **M1** | ts-core + ts-safety + L5 机械检查脚本 + **L4 重放框架雏形**（MA2 的接口依赖，见 §4） | **本地全绿（2026-09-22，DEC-39 后开工）**——退出 review 门已呈报；CI 上线随远端 | HLD §7 M1 DoD |
| **M2a** | ts-store + TSAP 格式定稿 + slot（A05 manifest 镜像依赖） | **本地全绿（2026-09-22）**——twister 5/5 配置（新增 framework.store）；TSAP v1 定稿（16B 头/大端）；L5 增第 6 项（prov 零写） | HLD §7 |
| **M2b** | ts-hal 权限（ts_perm_v1）+ WAMR 宿主 + 样例 APP | **M2b 本地全绿（2026-09-23）+ 补审查 IR-05…20 处置（同日）**；M2b.2 进行中——环境批 + Q-23 实证批 + DEC-43 锁收口批交付（2026-09-26）；**接线批第二单元交付（同日）：APP 运行时宿主（执行线程/mailbox/停止/健康自停）+ ts_api_v1 natives + framework.app 端到端——twister 14/14（57 用例）全绿**；**M2b.2 收尾单元交付（同日）：boot 步骤 8 slot 装载（manifest 走查/caps 组合/app_id 提取）+ TS_APP_WAMR 默认 y + E2E 真夹具 wasm——twister 14/14（58 用例），M2b.2 全部完成** | HLD §7 |
| **M3a** | ts-net（zenoh-pico；发现/key/sys 命令——A06 对齐依赖） | **M3a.1+M3a.2 本地全绿（2026-09-23）**：传输缝 + keyspace/pubq/session/linkmon + sys 命令面（host-only 7 项，最小 CBOR 定体编解码）+ 遥测/事件发布 + boot net_init 接线 + zenoh-pico 1.10.1 真实绑定（含 queryable/订阅）编译链接绿；**L3 端到端 PASS（2026-09-23，dev-environment §8）**；**DEC-40/41/42 增强批落地（2026-09-23，提交 486427c）：命令信封 v2+幂等缓存/控制租约/事件遥测 ver+kind 信封+QoS 映射/is_up 任务自省/TCP-TLS locator 校验——L3 扩展为五验证点全 PASS，twister 8/8（35 用例）** | HLD §7 |
| **M3b** | ts-power + ts-periph（外设桩——A04 深度仿真依赖）+ 集成重放 | **本地全绿并退出（2026-09-25）**：ts-power（供电槽/预算/限流/事件 + get-budget + kind 97 遥测）+ ts-periph（描述符职责链/插拔→单通道 SAFE_FAULT）+ replay 集成场景（预算+插拔 golden）；impl-review-01 修复批（同日）后回归口径 = twister 10/10（46 用例）/L5 6/6 全绿 | HLD §7 |
| **板级** | ESP32-S3 → ESP32-P4 → STM32H7 | **板级一~九完成（S3）**：一 bring-up/环境重建（二十）→ 二 效率 DoD 六项（board-bench-01）→ 三 真机 IO 延迟三层对照 5.75µs 安全层（DEC-44 + TS_DRV_GPIO）→ 四 WiFi+zenoh L1 p50≈12ms（netbench-01）→ 五 prov/APP flash 持久化（board-persist-01）→ 六 WAMR 堆 256KB 入 PSRAM（board-psram-01）→ 七 WiFi 双断链自愈 4.2/9.2s（board-reconnect-01）→ 八 estop 硬件链路 ≤20ms（board-estop-01）→ 九 PWM/ADC 真后端（board-periph-01：LEDC duty ±1‰ + 限幅截断 + 断链 fail-safe 落驱动修复 + ADC 轨到轨 0/3122mV）。**板级十完成（2026-10-02）**：Agent→真机完整部署 E2E 双轨首次闭环（board-deploy-01：发现→打包→租约→分块→事实对拍→激活→暖复位→APP 自 slot 运行→get-app 对拍，双轮复现；附 exports 命名漂移 + get_info 打回装载结果两修复）。**余项（板级十一候选）**：生产 prov 烧录通道（esptool 直写 / Agent push_prov）、注册期 poweron 值落驱动、input monitor 真输入驱动、MCUmgr 固件 OTA（DEC-07/23 已裁未实现）、Zephyr 升级评估（**P4 前置**：v4.4.0 无 esp32p4 支持，4.5 加入——升级走门 ⑤ 呈递）；**P4 适配恢复**（2026-10-02 owner 二次指令，动机 = APP 复杂性余量：双核 RISC-V HP@400MHz + 16MB flash + 8MB PSRAM）；**H7 适配放弃**（2026-10-02 owner 指令；评估报告 docs/h7-memory-assessment.md 存档）。**MD demo 批（功能完成后）**：**MD0 完成（2026-10-04）：真实 LLM 冒烟（G2）+ APP 代码生成链 G1（DEC-45 方案 A + 可靠性调研 R1-R8 落地，SMOKE3 双轮贯通"需求→编程→打包"）——MD1 demo 阶梯解锁**→ MD1 阶梯 D1-D7（**MD1.1 完成 2026-10-05：五 demo 全 PASS（P1 已根治——meta 双副本读共享缓冲 bug，MD1.1b）**；MD1.2 进行中（**a 完成 2026-10-05：SD bring-up 真机 PASS〔DEC-46 硬件即 Sense 板载〕**；**b 完成 2026-10-05：摄像头 bring-up PASS〔QQVGA ×4 帧 + 帧落 SD 闭环；官方池路径为 V1 唯一路径〕**；**d 呈递中 2026-10-06：avbench spike PASS + Q-27 六子项停门待裁**〔实测：chunk ≤1KB〔>2KB 碎片路径死〕/打拍 ≥4ms/分片重试必须/视频池 PSRAM〕；c=音频 PDM 扩展；D4/D6 输入类并入） → MD2 混合 D8/D9（docs/agent-demo-readiness-01.md） | 板级报告族 docs/board-*-01.md；每单元 twister 全量+L5+CI 四 job 绿 |

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

（v1.15：历史两项均已落定——GitHub 远端 + CI 四 job 全绿〔2026-09-25 十四〕；Zephyr SDK 1.0.1 已装〔2026-09-26 二十〕。当前**无阻塞项**；板卡使用中注意事项见 dev-environment §5〔usbipd attach 掉线复挂〕。）

## 6. 环境与基础设施事实源

- `docs/dev-environment.md`：WSL 目录规范（`~/project/{tessera,zephyrproject,logs}`）+ 固件 venv；**MA0 起增补 agent venv（`~/project/agent-venv`，DR-19）**。
- CI：`.github/workflows/ci.yml`（repo-checks → 固件构建/twister → **agent lint+pytest（MA0 接入）**）。

## 7. 交付单元排期表（v1.30 · 2026-10-07 owner 指令重构：排除硬件阶段三、按规划连续开发、每单元后汇报总/阶段进度；每会话一单元）

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| A | **MD1.2g** ✅ | ts-av + ts_net_publish 能力面（DEC-47③⑥：ts_av_capture 最小面 + av 权限类 + ts_net_publish〔打拍≥4ms=速率限制、chunk≤1KB、分片重试≤5×20ms——DEC-47② 值直用〕+ kind 注册表/内存表/L5 同步 + agent 白名单/manifest/提示词 + 用例）；**并入**：fs_paths 条目长度对齐（复检发现②：agent≤64 vs 固件≤63） | 已裁（DEC-47） |
| B | **MD1.2h** ◐ | D-AV demo：JPEG 帧格式（OV2640 硬件压缩）+ 真 LLM 生成 + PC 侧帧重组消费端 + 真机判据——**部分交付 2026-10-07**：链路 90% 打通（真 LLM 一轮过 + 真帧捕获 + 分片发布实证）；JPEG = DAV2 上游缺口（esp32 DVP 不支持变长帧）→ RGB565 保底；DA PASS 被 DAV1 缺陷阻塞（APP 线程冻结，看门狗链按设计收口） | — |
| B2 | 查询面停滞 + DAV1 批 ◐ | **查询面停滞已解（2026-10-09）**：根因 = agent 侧双缺陷（zenoh locator 语法 + Reply API 漂移——板/路由无责）+ rollback_count 随载恢复存量缺陷修复（twister 77 绿）；D8 各段双证齐（含 count=1 终态对拍）唯单跑 PASS 行待网络平峰期；**DAV1 未启动——独立会话再开** | — |
| C | **验签呈递批（Q-29）** ⏸ | IR2-02 根治方案：TSAP 头摘要字段（文件格式变更）+ ed25519 真验签 + 生产 prov 烧录通道（板级余项同批）——**已呈递 2026-10-07，门③ 停门待 owner 裁决**（四子项建议：内置 C verify / fmt_ver=2+32B sha256 / esptool 直写 / TEST 真验签） | 门③ 呈递停门 |
| D | 验签实施批 ✅ | Q-29 裁决后实现 + 真机部署链复验；**并入 IR2-07**（回滚闭环：目标槽验证/回滚后重载/meta 双损如实失败） | — |
| E | MD1.2c | PDM 音频驱动扩展评估——**已交付 2026-10-07：结论缓办**（技术路径可行无消费者；docs/md12c-pdm-eval.md；重开触发四条件在档） | ✅ 评估 |
| F | 输入面 G3 批 ✅ | input monitor ADC 真值化 + 事件→mailbox 路由 + D4/D6 demo 真机全链（D4-DONE/D6-DONE/clamp -12/rc=0）；并入 IR2-06 根治 + estop 沿 prov 化 + ts_wdt_deactivate（DEC-48 对称面） | — |
| G | 板级余项批 ✅ | **G1 ✅** poweron 落驱动；**G2 ✅ 2026-10-10 完整收口**：OTA 全链真机 PASS（v1 运行→SMP 上传 v2→perm swap→v2 运行）——原防火墙诊断推翻，真凶 = 客户端双字节缺陷 + 板侧 smp_udp pre-IP 绑定（修复入仓）+ WSL mirrored 入站 UDP 缺陷（Windows 侧客户端绕行） | — |
| H | G4/G5 批 ✅ | **单活跃 APP 语义收口**（activate 即停 DR-14 + 隔离拒载/标记持久化）+ **模拟器深度增强**（LLD-A04 §2 输入文件实装——scenario inputs 驱动重放 + ch 命名空间）——2026-10-09 交付：twister 15/15（77 用例）/agent/E2E/L5/ruff/板级构建全绿；WAMR 二次 boot_start 怪癖登记（dev-env 教训 28，生产无暴露面） | — |
| I | MD2 混合 demo ◐ | **D9 ✅ 全链**（sim 输入文件首批真消费者 + 真机断链时间线全绿 + 合同 3 双证据）+ **D8 ◐ ~90%**（三版本链路全证：部署/升级 G4 即停/健康回滚/v2 复活 + hb 心跳后 rc=0 落驱动；**拦下并修复 deploy.py v1 残留对拍公式** + deploybench 内存重平；余 = clean-pass 单跑受查询面停滞阻塞——新发现登记 B2 邻接） | — |
| J | Zephyr 升级评估 + P4 ✅ | **评估 ✅ + 升级批 ✅（2026-10-10 DEC-50：rc1 已上——twister 15/15 + 三 bench 构建 + inputdemo 真机复验全绿；仓库内适配三处：WAMR autoconf 域/分区 mapped-partition+冲突删/池再平）**；**P4 适配批 ✅（2026-10-10，docs/board-p4-01.md）**：Waveshare ESP32-P4-WIFI6-DEV-KIT bring-up 全链真机 PASS（p4bench：prov→v2 包安装→暖复位→flash 全状态自举→WAMR@RV32 ACTIVE→写链→P4B PASS）；SDK riscv64 工具链补装 + WAMR RISCV32 板映射登记 + 五分区 overlay @0x7E0000；顺带修复存量缺陷两族（六 bench overlay 缺 mapped-partition 兼容串 + persistbench v1 包漏网——DEC-49② 后即坏） | 门⑤ 已裁（DEC-50） |

（原则不变：依赖就绪先行的最小单元；任一单元 DoD 全绿才进下一个；门项到点即停等 owner〔C 门③、J 门⑤、E 视方案〕；观察项——zenoh-pico Zephyr 集成尺寸钩子上游 issue 暂不提〔DEC-47〕、native-build 偶发面、外部静态 video_buffer 根因、watch 同槽重推。复检发现③〔ts_fs 语义边缘〕见 impl-review-02 §8 附记——登记不动手。）

## 8. 版本 V0.1.0 · 编程链路完整性批（2026-10-11 owner 裁决；每会话一单元，连续开发至完成）

> 范围出处：会话盘点建议四域五单元 + owner 新增"真实需求全流程编程测试"为版本验收（decisions 2026-10-11 版本方向批）。收口 = tag `fw-v0.1.0`（无既有 fw-v tag，首固件功能版本从 0.1.0 起，semver 0.x 开发期）。**不入本版**：v4.5.0 正式平移、#121767/#121774 上游跟进、多 APP 并行/逻辑节点并联（V2 级另立项）、PDM。

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| NV-1 | 部署后诊断闭环 ✅ | agent 侧判据回捕工具（串口窗口 + 分类器：PASS/无挂载/无安装/无 ACTIVE/无事件行/WDT 复位/卡死）+ 失败→feedback 注入 app_develop 重生成→重部署闭环（轮上限防失控）+ 分类器单测 + gated 真机验证（坏 spec 首轮必败→闭环救回 PASS）——**2026-10-11 交付**：tools_diag 三模块 + diag_classify MCP + 15 用例（全量 92+2s）；真机单迹 round1 pass（NV1 DONE 精确判据）；顺带根治 app_deploy 暖复位竞态 + manifest 伪影级联解包；观察项 = SYWORK 源 wdt 偶发复位（登记不动手） | — |
| NV-2 | spec 质量门 ✅ | spec 模板（需求/资源/判据/安全声明四节）+ 静态检查器（判据可测性=有唯一判据行/caps 最小化提示/fs_paths 与 out 通道合法性）+ app_develop 入口集成 + 用例——**2026-10-11 交付**：spec_gate.py（判据引号串机读派生 = repair_loop 单一事实源；errors 阻塞/warnings 留痕；旧式 spec 兼容）+ spec_check MCP + workflow skill 模板节；pytest 103+2s（+11）/ruff 绿；真机消费面归 NV-6 验收 | — |
| NV-3 | sim↔real 对拍 ✅ | 同一 scenario 双跑（sim_run + 真机 bench）判据行机械 diff 工具 + 首个对拍基线（gated 真机面）——**2026-10-11 交付（代码面）**：simreal_diff.py（写序列终态 ↔ 判据行读数语义对拍——形态不对等的 V1 诚实口径）+ MCP 工具；pytest 108+2s（+5）；**首基线随 NV-6 验收链产生**（全流程跑 sim→real 时留档） | — |
| NV-4 | 审计 flash 持久化 | DEC-30④「审计 V1 内存环形（掉电丢失）」语义变更：环形记录格式/分区布局/溢出策略 + 固件实施 + 真机掉电留存验证——**Q-31 已呈递 2026-10-11（三选项：独立 4KB 分区 64 槽定长环〔建议〕/noinit/meta 并区），停门待 owner；逾时未裁顺延** | **Q-31 呈递门** |
| NV-5 | README ✅ | 仓库门面：项目一句话/架构分层图/ts-* 模块地图/快速上手（WSL 环境 + 三命令）/demo 一览（D 系列 + D-SD/D4/D6）/CI 徽章——**2026-10-11 交付**：根 README.md（中文 + 架构 ASCII 图 + 安全合同摘要 + License） | — |
| NV-6 | 真实需求全流程编程测试 ✅ | **版本验收**：一个真实需求走完 spec→LLM 编程→编译打包→sim 模拟测试→部署→真机判据 PASS 全链（消费 NV-1/2/3 产物）；需求候选 = 立方体健康哨兵 APP——**2026-10-11 交付**：round1 pass 全链（spec 门判据派生 → LLM 生成 hbs APP → repair_loop 部署 → 真机 "HBS DONE ticks=20" 精确命中 + DB PASS）；sim 环节 + simreal_diff 首基线**如实顺延**（sim replay 固件不装载 wasm APP——APP 级 sim 面 = 后续增强批；V1 模拟面由 twister 77 用例 + 产物校验承担）；LLM 附属行简化如实留档 | 验收判据 owner 可查（logs/nv6_result.json） |

## 9. 版本 V0.2.0 · 视频链解锁批（2026-10-11 owner 裁决开工；每会话一单元）

> 范围出处：V0.1.0 收口后的遗留清单 + owner 裁决（2026-10-11：D-AV 宿主自愈 workaround 合入——上游 #121774 维护者已定性 DMA re-arm 缺陷且确认 stop/start 恢复有效，我方源码逐环核实，decisions 在档）。版本号：fw-v0.1.0 已 tag，功能批 minor +1 → 目标 tag `fw-v0.2.0`。**不入本版**：多 APP 并行/逻辑节点并联（V2 级另立项）、PDM、v4.5.0 正式平移（上游发布时机）。

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| V2-1 | **D-AV 采集自愈 workaround** ✅ | 固件 `src/hal/av.c`：capture 超时计数（现有 400ms 档）连续 N 次 → `video_stream_stop()+start()` + buffer 重 enqueue → 采集恢复；自愈事件 printk 留痕（不触安全合同——纯读面）；**真机 D-AV 全链解锁**：停摆触发→自愈→后续帧到达实证 + **256B 发送档验证**（TS_NET_PUBLISH_MAX_BYTES=256 绕行既有 1KB 损坏缺陷）→ PC 侧 dav_recv 重组 ≥1 完整帧 = **DA PASS**；**回收条件登记**：上游修复随正式版平移后回收 workaround 与 256B 档（R3 同族）——**2026-10-11 交付（超预期）**：采集自愈实证 + **发送层根治**（我方 zenoh glue use-after-overwrite——static_buf 别名 × 环形槽覆盖；拷贝语义修复）+ 64B 档 1843 chunks 零损坏 + 2 帧完整重组 = **DA PASS**（256B 档证伪弃用；上游定性修正：1KB 损坏 = 我方竞争 + 上游大 payload 双缺陷叠加） | — |
| V2-2 | 审计 flash 持久化（NV-4 实施）✅ | Q-31 裁决后按裁决方案实施——**2026-10-11 交付（DEC-52①）**：store/audit.c 两页乒乓环（8KB；物理约束实现修正登记：翻页代单条覆盖/仅异常类落盘）+ commit/estop 下沉 + boot 留存报告 + sys/get-audit flash 读取 + auditbench 真机 AB PASS 两轮（注入→复位→留存→seq 连续）；twister 15/15（80）/L5 6/6/agent 113 全绿；顺带拦下两真缺陷（res u8 截断/4KB 栈数组）；**待办**：生产 app flash 面接入（独立批） | 已裁（DEC-52） |
| V2-3 | sim APP 装载面 + 对拍首基线 ✅ | sim_run 的 replay 固件增加 wasm APP 装载能力（或等价 APP 级 sim 面）→ NV-3 simreal_diff 首基线兑现（同一 APP/场景双跑对拍留档）——**2026-10-11 交付**：replay 加 test_90_nv1_app_load（embed 真机同包 NV1；WAMR 配置）+ sim_run verdict_patterns + diff_lines（尾部对齐）；**首基线 = 判据行逐行严格全等**（7=7，logs/nv1_simreal_baseline.json——确定性合同双域机械实证）；twister 15/15（78，+1）/agent 113 | — |
| V2-4 | spec 附属证据约束强化 ✅ | LLM 周期行简化对策（NV-6 留档）：spec 附属证据行的生成约束强化（提示词/判据节文法）+ 附属行缺失的 gate 提示级检查——**2026-10-11 交付**：app_develop 首轮提示注入全部判据/附属串（实现面写死）+ repair_loop pass 轮 evidence_hits/missing 统计（缺失如实非阻塞）；pytest 110+2s；LLM 行为改善实证随下次真机全流程顺带观测 | — |
| 观察 | SYWORK wdt 偶发复位 | reason=0x00020000 间歇复位观察项（NV-1 留档）——不排期，随真机批次顺带取证 | — |

## 10. 版本 V0.3.0 · 生产语义收口批（2026-10-12 完成，简记）

> V3-1 生产 app flash 面（ts 六分区 + TS_STORE/FLASH/AUDIT + 真机挂载实证）+ V3-2 板级全量复验（auditbench AB PASS + deploybench D8 PASS）；迁移环境后首版本，全部验证于新机器完成。tag `fw-v0.3.0`（提交 1d8074e）。

## 11. 版本 V0.4.0 · 语义扩展批（2026-10-12 owner 裁决开工；每会话一单元）

> **范围裁决（owner）**：调研清单 F1-F7 + Agent 侧 A1-A8 + 质量债 C 全部入版（**F8 P4 无线面除外**——上游 #121767 外部依赖，维持搁置）。版本性质 = V1→V2 语义跨越（多 APP 并行主线）+ Agent 能力面铺开；体量大（约 12-15 单元），F1 设计门后连续开发。

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| M1 | **F1 多 APP 设计批** ✅ | Q-32 六子项呈递 → DEC-53 全按建议裁决 | 已裁（DEC-53） |
| M2 | F3 ts_log 权限裁决 + 日志真实化 ✅ | log 权限类 fail-closed + 全局窗口限速 + TEST 自动授予 | — |
| M3 | C-1 稳定性定性单元 ✅ | LLM APP 死亡定案（health_ping 非零返回误解）+ 语义门；SYWORK wdt 维持观察 | — |
| M4 | A2 caps 硬预校验 ✅ | caps/fs_paths 提示级→错误级（IR-17 收口） | — |
| M5 | F6 输入中断驱动 ✅ | GPIO_IN 纳入监测 + 边沿回调 ISR 纯净钩子（DR-02 收口） | — |
| M6 | F1 实现Ⅰ（框架面） ✅ | 槽池可配 + meta v2 + v1 迁移 + per-entry 状态机 | — |
| M7 | F1 实现Ⅱ（运行时面） ✅ | rt[N] + 分账 + 广播 + deploybench 真机 MA PASS（M7b/M7c 含寻址面） | — |
| M8 | F4 manifest threads 字段 ✅ | Q-33 申报制（1-4）+ 运行时恒单线程（启用留 V0.5+） | 已裁（Q-33 批内） |
| M9 | F2 APP 状态持久化 ✅ | ts-store kv 两页乒乓 + app_id 哈希归属 + kv natives/权限类（DR-15 收口） | — |
| M10 | A1 push_prov ✅ | Q-34 A+：confirm 令牌+写前校验+per-boot 窗+prov_maint 独立通道（LLD-A06 §6 收口） | 已裁（Q-34 批内） |
| M11 | A3 D-AV 消费端 + ota_client 重建 ✅ | tools/board 回归：dav_recv + ota_client（假 SMP 对练烟测 PASS）；真机链随板级批 | — |
| M12 | 接缝落地打包 ✅（价值裁剪） | t_window 评估语义（IR-18 收口）+ HTTP 门面（A7）；ACP/A2A 维持接口级预留（裁剪登记） | — |
| M13 | F7 逻辑节点设计批 ✅（呈递） | **Q-35 呈递停门**（建议 A：Agent 侧编排——固件零改动+合同不变）；实现Ⅰ随裁决（V0.4.x 补批） | 门③（Q-35 停门） |
| M14 | F5 PDM 音频（呈递） | **Q-36 呈递停门**（av 类 pcm16 变体 + TS_DRV_PDM 路径在档）；实施随裁决（V0.4.x 补批——寄存器级驱动独立会话） | 门③（Q-36，md12c 既定点） |
| M15 | 收口 ✅ | twister 15/15（92）/agent 119+2s/L5 6/6/repo 2 全绿 + tag fw-v0.4.0；M13/M14 停门项随 V0.4.x 补批（V2-2 先例） | — |

- **质量债随批清偿**（不单开）：C-4 低风险打包债（impl-review-02 §4 族）随 M2-M7 各批顺带；WAMR version.h 屏障源头取证随 M3；CI 间歇红观察维持。
- **每单元后**：twister 15/15 + agent pytest + L5 回归（军规 10）。

## 11b. V0.4.x 补批（2026-10-13 owner 双批准 DEC-54：Q-35→A / Q-36→av pcm16）

| 序 | 单元 | 内容 | 状态 |
|---|------|------|------|
| M16 | Q-35 实现Ⅰ · LN 逻辑节点编排 ✅ | lno.py（注册表/扇出/聚合/组恢复）+ MCP 六工具 + 双 FakeCube 测试（+5）——固件零改动 + V1 合同不变 | 交付（agent 124→125） |
| M17 | Q-36 · PDM 批 ✅ | M17a pcm16 格式面六面全量（+2 测试）；M17b TS_DRV_PDM 驱动 + pdmbench——**bring-up 收口（2026-10-13 补批后）**：双缺陷定案（GDMA 复位态 dma_rst=1 + bck_div/fs×128 时钟计划误推导），官方对照 + 分层焊盘镜像诊断，**PDMB PASS ×2**（docs/evidence/pdmb_PASS_console.txt） | 交付（完整） |

- 回归基线：twister 15/15（92）/agent 125+2s/L5 6/6/repo 2。

## 11c. V2 纵深批（2026-10-13 owner 点向开工：多真机 LN 挂起〔第二块 cube 未接入，随硬件到位重启〕，先启 V2 纵深）

> **范围**：V2 级纵深两主线——M18 PDM 产品化（**DEC-54② 既定第③项执行，无需新裁决**：demo.d.pdm 真 LLM 生成 → 真机采集→分片发布→PC 落盘）+ M19 真 wasm 多线程（**设计批 + Q-37 呈递停门〔门③〕**——DEC-31 局部翻案 + 安全合同影响面，批准后实施）。D-AV 纵深盘点维持上游观察（1KB 档/JPEG 变长帧均上游缺陷域，无批内可执行项）。

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| M18 | D-PDM demo ✅ | 真 LLM 生成 demo.dpm（wasm 2261B/TSAP 4944B，两轮收敛）→ pdmdemo 载体（avdemo 克隆−摄像头+TS_DRV_PDM）→ 真机 DP DONE frames=10 + PC 侧 8 帧完整（crc 全过/span 4222/.pcm+.wav 落盘）= **DP PASS 双侧**（证据 docs/evidence/dp_PASS_console.txt）；顺带修 av.c 惰性 bring-up（缺此恒 E_IO）与 dav_recv/pdm_recv 重建件整帧误校验（合同 = 分片级 crc——M11 真机债收口） | — |
| M19 | 真多线程实施批 ✅（DEC-55 落地） | **M19a runtime**：TS_APP_THREADS（默认 n）+ ts_thread_start/join natives（宿主 k_thread 编排——绕开 WAMR os_thread 族三缺陷与 lib-pthread 计量死结）+ 每线程 L2 预算 + xtensa 软 8 字节原子垫片 + framework.threads 套件（3 用例）；**M19b demo**：agent 线程档编译链 + 真 LLM demo.dthread.count（threads=2）→ thrdemo 载体 → 真机 **"DT DONE cnt=2000 rc=2000"**（docs/evidence/dt_PASS_console.txt）；**M19c**：twister 16/16（95）/L5/repo 2/ruff/agent 126 全绿；教训 35 入册 | — |
| M20 | 收口 ✅ | 登记 + 回归定格 + tag fw-v0.5.0 | — |

- 每单元后：twister 15/15 + agent pytest + L5 回归（军规 10）。

## 11d. 通用域解放批（2026-10-13 owner 需求校准裁决 DEC-56：三批路线）

> **背景**：owner 四轮校准定案（DEC-56）——平台从「专用小域」解放为「通用域」：① 设备形态不限（立方体 = 比喻；本地交互外设 = 设备事实，非专项功能批）；② APP 复杂度不受结构性预设限制；③ 设备独立运行（standalone）与远程编排同为一级模式；④ Agent 双角色（DEC-12 v1.1：自带简单 AI 客户端 + MCP/A2A 等 server 门面）+ 智能内化（创作面放宽、交付面确定性门不撤）。需求文档同批落文（FOUNDING_PROMPT v1.1 + DEC-01/02/12 修订）。

| 批次 | 内容 | 前置 |
|------|------|------|
| **R 批 research（先导）** | 四路：① Agent 创作循环架构（会话/工作区/审批/持久化——输入 = `docs/agent-cli-research-01.md`）② 复杂 APP 工程链与资源泛化（多文件→wasm、尺寸/内存/编辑模型重定——D4 方向已裁）③ standalone 运行模式合同泛化（fail-safe 语义声明化/控制源仲裁——D6 方向已裁，门④随 design 批）④ 多开发者信任链（生态批输入——D5 分期已裁） | — |
| **Agent 批（V0.6.0 候选）** | 独立终端 CLI（DEC-12 v1.1 内嵌 AI 客户端形态）+ 创作工作区（scoped 文件工具/多文件工程/sim 自测循环）+ 复杂 APP 工程链接入 + 会话持久化 | R①② |
| **合同泛化批** | standalone 模式/控制源仲裁（安全合同修订，门④）+ 尺寸内存资源分级 + 设备能力发现与安装匹配 + LLD 全库「立方体→设备」术语清扫 | R③ + Agent 批实测数据 |
| **生态批** | 多开发者信任链（注册/撤销/侧载）+ 分发面 | R④ + 合同泛化批 |

## 11e. 通用域解放开发计划（2026-10-13 DEC-57 全裁 + 深度设计定稿：三版本批全单元排期）

> **设计输入**：HLD-agent v0.2（创作循环/终端门面/工作区——AG 批）+ HLD-contract-v2（部署模式/仲裁/档位——CG 批，**门④措辞已随文呈递**）+ R6-R9 调研。**质量优先条款**（DEC-57）全批生效（§12）。每会话一单元（军规）；依赖注记跨批。

### 版本 V0.6.0 · Agent 批（创作循环 + 独立 CLI——DEC-12 v1.1 双角色兑现）

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| AG1 ✅ | LLD-A08/A09 定稿 + LLD-A01/A02 修订 | 同左（C-7 owner 确认 2026-10-13）| 门③ 已过 |
| AG2 ✅ | 工作区 + scoped 工具 | 同左 + 13 例测试矩阵 | — |
| AG3 ✅ | 循环引擎 + 固件验证器 | 同左（sim 诚实拒绝；实证：缺导出由面门承载）| — |
| AG4 ✅ | 终端门面 | 同左（run 子命令接线随 AG6）| — |
| AG5 ✅ | 会话快照 + resume | 同左（SIGINT 优雅退出 + 端到端测试）| — |
| AG6 ✅ | app_develop 升级 + 审批参数规则 | 双路径（循环主路径 + wasm_path 单发维持）+ runner + run 子命令 | — |
| AG7 ✅ | 复杂 APP 真机实测 | **AG7 PASS**（4 轮收敛/判据命中/ag7_console.txt）+ large 数值（wasm = 资源+147B 线性）| — |
| AG8 ✅ | 收口 | twister 16/16（95）/repo 2/agent 170+2s + tag fw-v0.6.0 | review |

### 版本 V0.7.0 · 合同泛化批（standalone/仲裁/档位——HLD-contract-v2 落地）

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| CG0 | 门④措辞裁决 | HLD-contract-v2 §2.4/§3.4/§4.2 三段合同措辞 owner 批准 | **门④**（呈递在档）✅ DEC-58 |
| CG1 | LLD 修订批 | safety/net/appmgr/store 四 LLD 按 HLD-contract-v2 §7 修订 | 门③（schema v2 呈递）✅ Q-42→DEC-59 |
| CG2 | 部署模式 | prov deploy_mode + linkmon 模式守卫 + standalone boot 声明 + 事件面 + estop-clear 守卫 | — ✅ |
| CG3 | 控制源仲裁 | arb_owner/压制门控/租约联动/审计 src 维度（sim 用例 + 板级判据）| — ✅（本地交互源信号接线随后续设备形态批）|
| CG4 | 资源档位 | manifest tier/needs + 安装期匹配矩阵 + 尺寸门分档 + 槽池结构（**AG7 数值消费**）| — |
| CG5 | 能力发现 + 资源打包 | get-info caps 块 + 部署会话资源推送（方案 A）| — ✅（A @fw-v0.7.0；B @V0.7.x 补批——真机 net+SD E2E 随板级批）|
| CG6 | estop 清除通道 | 按能力声明 + prov estop_remote_clear | — ✅（实质随 CG1/CG2 交付；收口 = LLD §9a 已知限制节）|
| CG7 | 术语清扫 + 回归 | LLD 全库「立方体→设备」+ 板级全 bench 复验 + tag fw-v0.7.0 | review ✅（真机 spot check DEPLOY PASS + 全量复验 16/16〔103〕）|

### 版本 V0.8.0 · 生态批（多开发者信任链——Q-40 方向落地）

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| EC1 ✅ | 信任链 LLD | 信任根表/注册撤销/单调版本号 设计定稿 | 门③ ✅ Q-43→DEC-60 |
| EC2 ✅ | 信任根表实现 | prov 扩展 + 验签链多根 + 防回滚 | — ✅（ts_trust 8KB 分区/有效集迭代/trust-update 命令/Agent 工具；生产回滚 NULL 恒拒缺陷顺带根治）|
| EC3 ✅ | 安装期权限确认 | 本地确认路（有交互设备）+ Agent 呈报 strict 路（无头）| — ✅（无头路实现：三点 strict 审批强制携 manifest 权限面；本地路 LLD 定稿随设备形态批——LLD-A02 §3.2）|
| EC4 ✅ | 侧载通道 | 按设备形态按需（同验签链无例外）| — ✅（侧载纪律定稿 + L5 检查 7 机械实证 slot 收口白名单；SD/USB 本体按形态按需——Q-40②）|
| EC5 ✅ | 收口 | 回归 + tag fw-v0.8.0 | review ✅（twister 16/16〔107〕/L5 7/7/repo 2/agent 183+2s/ruff/sync 全绿）|

**跨批依赖**：CG4 ← AG7（large 数值）；CG0 可与 Agent 批并行（措辞已呈递待批）；EC1 ← CG2（prov schema v2 基座）。**未决观察项**（不占批）：上游 v4.5.0 正式版平移、SYWORK wdt 间歇、CI native-build 间歇、多真机 LN 拓扑（第二块 cube 到位重启）。

## 11f. 剩余开发项目批（2026-10-15 owner 接入第二块板卡 dnesp32s3b——正点原子 ATK DNESP32-S3B V1.1 解锁）

> **硬件事实**（owner 提供原理图/引脚表 + Zephyr 树内板文件核实）：ESP32-S3 N16R8、16MB flash（与 xiao 同 16M AMP 布局）、**ES8311 codec**（I2C0 @0x18 与触摸/XL9555 共线；I2S BCK=IO21/WS=IO13/播放=IO14/录音=IO47，无独立 MCLK）+ NS4168 功放（SPK_EN 在扩展器）+ 并行 PDM 麦克风（MSM261S4030，共享 21/13/47）；**SD = SPI2**（SCK=7/MISO=15/MOSI=16/CS=17）；**LCD 320×240 DBI + 触摸**（引脚与树内 DTS 一致）；**按键 BOOT + 扩展器 KEY1/KEY2**（本地交互硬件齐）。解锁：多真机 LN（第二 cube）、设备形态批（本地交互面）、音频输入输出（ES8311——Zephyr 无 in-tree 驱动，域内自研）、net+SD 组合 bench（板自带 SD+WiFi）。

| 序 | 单元 | 内容 | 门 |
|---|------|------|----|
| K1 | atkbench bring-up | dnesp32s3b 目标 + 五分区/trust 分区 + WiFi/zenoh + WAMR XTENSA 映射 + 部署链 PASS（第二 cube 就位） | — |
| K2 ✅ | ES8311 音频 | 域内驱动（I2C 控制 + I2S 数据）：输入对齐 av pcm16 + **音频输出新面**（ts_av_write native + av:write 权限类 + manifest av_srk 采样率声明） | 门③ ✅ Q-44→DEC-61（av_srk 实施简化：V1 固定 16k——字段留需求实证后加；真机 AK AUDIO PASS）|
| K3 ✅ | 信任链真机 E2E | ts_trust 分区上板 + 无线注册/撤销/防回滚时间线 + 多根实机安装（**AK3 TRUST PASS**：T0 基线/T1 未注册拒/T2 注册/T3 多根部署装载/T4 防回滚/T5 全撤回/T6 复拒/T7 终态全绿——证据 ak3_trust_driver/console.txt；F1 审计下沉双修正 + F5 回执编码双缺陷根治随批） | — |
| K4 ✅ | net+SD 资源推送 E2E | atkbench 直兼（板自带 SD SPI2 + WiFi）——fs 分区挂载 + push_resources 真机（**AK4 RES PASS**：large 包 needs.resources 白名单 + fs-commit sha256 verified + APP 消费端字节命中；证据 ak45_console.txt） | — |
| K5 ✅ | large 档板级配置 | LOAD_MAX/SLOT_SIZE 抬升 + 内存账重平 + large 全链（**206KB wasm→412KB 包全链**：512KB 槽×4 + 装载/验签缓冲 PSRAM 化〔TS_APP_PSRAM_LOAD_BUF/VERIFY_BUF 新面〕+ 512KB WAMR 池 + COSE 4B 长度头族修复〔read_head/Sig_structure〕+ put_bool RFC 修正；F6 分块流楔死登记——日志面 printk×flash 争用） | — |
| K6 ✅ | 多真机 LN | deploybench + atkbench 双 cube：LN 组部署/断链策略/跨板判据（**AK6 LN PASS**：ln_create 双成员 → ln_deploy 扇出双板 confirmed → ln_status 聚合双 ACTIVE 无降级；xiao 以当前模块重刷〔F1/F5 修复平移〕；atk SMH 1MB→4MB；证据 ak6_console.txt） | — |
| F1 ✅ | 本地交互源 | 按键（BOOT/扩展器 KEY）→ arb LOCAL 席位 + 压制 + 事件（CG3 机制接线）——**真机手势判据收口**（owner BOOT 短按 ×2：`AKL →LOCAL`/`→REMOTE` rc=0 双向切换；证据 af12_boot_console.txt） | — |
| F2 ✅ | 本地 estop 清除 | KEY → clear_fault + prov estop_remote_clear 出厂缺省翻 disabled（ISO 13850 偏离撤销）——**远程门真机实证**（need=local-clear）+ **本地路真机判据收口**（owner BOOT 长按 ≥2s：`AKF1`→`AKF2 force rc=0`→`AKC 清除 rc=0` 链三行；证据 af12_boot_console.txt） | — |
| F3 ✅ | 本地确认路 | LCD 呈现 manifest_summary + 按键确认 → 安装闸（EC3 本地路接线——嵌入式先行者面）——**DEC-62 已裁开工**（①固件侧挂起态/③手势模态/④bring-up/⑤2.5 单元按建议 + **②呈现面 owner 修订 = LVGL**〔弃自绘字体——芯片/尺寸适配性优先，R10 §6 注记：呈现属设备形态面非安全面〕）；执行 = **F3-1 ✅**（AKU1 真机 PASS——教训 36，证据 af31_lcd_console.txt）→ **F3-2/F3-3 ✅**（安装闸：lconf prov + activate/install 同闸 pending 态 + confirm/reject 仅固件本地路 + 60s fail-closed + 事件四态 + -13 回执 + 手势模态 + LCD 呈现；twister 16/16〔109，+1〕agent 196+2s〔+1〕L5/ruff/repo 全绿；**timeout 路真机 PASS**〔deploy → AKP1 → 60s → AKP4 撤销——证据 af3_gate_console.txt〕；**确认路真机 PASS**〔2026-10-16 owner 短按：AKP1 LCD 挂起 → AKPC → AKP2 meta 切换 → AK5 暖复位 → 自 flash 装载 `[app1/l0] AK4 DONE` 判据命中 → AK6 ACTIVE + 远程 get-app state=3 复核——证据 af3_gate_confirm_console.txt〕；**拒绝路真机 PASS**〔owner 长按 ≥2s：AKP1 slot=1 挂起 → AKPR → AKP3 撤销（槽保留可重推）——无复位无 meta 切换、既有 ACTIVE 不受影响 + get-app pending 已清——证据 af3_gate_reject_console.txt〕）——**三路（timeout/确认/拒绝）全真机收口** | — ✅ DEC-62 |
| F4 ✅ | peripherals 自报 | get-info peripherals 块（hal 注册表自报 + Agent 装前消费）——真机实证 akled:gpio/akpwm:pwm/akcodec:adc + periph 责任链单源注册 | — |
| G1 ✅ | Agent 任务链持久化 | LN 注册表落盘 + 跨重启 resume（D1）——LnRegistry(persist_path) 原子写/损坏条目降级跳过/IO 失败告警不抛 + env 重定向（TESSERA_LNO_REGISTRY）+ conftest memory 模式防 CI 副作用；测试 +6 | — |
| G2 ✅ | 诊断自动回喂 | 部署后自动抓串口 → diag_classify → repair 再入队（D3）——post_deploy_check（健康短路/被动抓取+分类/抓取失败不掩蔽）+ capture_window（被动窗——失败路径专用，开埠脉动 F3 在案）+ deploy_push_app post_check_s/serial_port 直参；测试 +5 | — |
| G3 ◐ | 测试债 | L5 工具单测 ✅（check_1/2 合成夹具 + 仓级烟测，repo pytest 5）；gcov 基线 → 顺延登记：native_sim 宿主构建 + CONFIG_COVERAGE 联动属 CI 基建决策（非仓内代码），随 CI 强化批单独评估 | — |
| G4 | 终局 | 全量回归 + 文档同步 + tag + 自检 | review |

**事实修正登记**：树内板文档称 NS4168 codec——实为 ES8311 codec + NS4168 功放（owner 原理图核实）；两音频输入源（ES8311 ADC / PDM 麦克风）共享数据引脚 IO47（分时互斥——K2 设计输入选型依据）。

## 11g. 后续开发计划（2026-10-16 定稿——owner 指令「按目前实现更新文档/检查代码/明确列出后续计划」）

> 基线：§11f 全批收口（K3-K6 + F1/F2/F4 + G1-G3 + F6 根治，回归全绿，c8a7ee8）。本节为**当前唯一有效的待办权威清单**——按优先级/依赖分组；凡涉设计取舍的门③项均标明。

### A. 清欠批 P1（HLD 设计内未实现项——**2026-10-16 owner 点向全批开工，DEC-62④**；执行序 P1-1 → P1-5 → P1-2 → P1-3 → P1-4）

| 序 | 单元 | 内容 | 规模 | 备注 |
|---|------|------|------|------|
| P1-1 ✅ | `ts_msg_send` APP 间消息 | **已交付**（框架路由〔app_id 串身份寻址 + 权限先于目标解析——不泄露存在性〕+ msg:send 名单权限类〔IR-11 收口〕+ FIFO 满槽背压 + TS_APP_EVT_MSG 取件通知 + natives/Agent 镜像；twister 16/16〔111，+2〕agent 197+2s〔+1〕L5/ruff/repo 全绿；真机双 APP 互发 demo 可复用 multiappbench〔随下一板级轮〕） | ~1 单元 | HLD §3.4 原设计项；多 APP 业务的最后一环 |
| P1-2 ✅ | zenoh TLS 链路 | **Q-47 已呈递停门（门③）**：五子项 = pico 使能路径（仓携带补丁）/ 自建 CA + mTLS 双向 / prov v2 bstr 三元组（tls_ca/cert/key，缺省无键 = TLS off 零重刷）/ zenohd TLS 并存口 / 内存重平与工作量 ~1 单元。设计事实在档（zenohd TLS+mTLS 全支持；pico Zephyr 集成缺件 = 需补丁；EC P-256 ~1.5KB 入 4KB prov） | ~1 单元 | owner 裁后开工 |
| P1-3 ✅ | `power_set`/`power_get` native | **已交付**：ts_power_set/get natives（power 层全链已存——perm+预算+唯一写路径+readback；纯暴露面）+ Agent 白名单/约定/面镜像测试 | ~0.5 单元 | twister 111 / agent 204+2s 全绿 |
| P1-4 ✂️ | `counter` 外设类 | **裁剪清账**：零消费者实证（demo/manifest/natives 全库无 counter 面；GPIO 沿计数由 input monitor 近似覆盖）；HLD §9 对照表已更新（R10 §4 日落纪律第一例——需求实据出现再重开） | 裁剪 | 评估完成 2026-10-16 |
| P1-5 ✅ | Agent S8 补全（部署失败自动再入修复轮） | **已交付**：post_deploy_check 判据面（pass_patterns + criteria_pass 三态）+ CreationLoop.repair（证据经上轮小结回喂，S8_REPAIR_MAX=2 计入预算）+ CLI --deploy --serial-port 端到端闭环；agent 203+2s（+6） | ~0.5 单元 | HLD-agent §4 S8（v0.2.2 收口） |

### B. 待 owner 裁决/动作项（当前）

> **收口回归定格 @ 6e54dee（2026-10-16）**：twister 16/16（111）/agent 204+2s/ruff/L5 7/7/repo 5/sync 全绿、工作树干净——**tag-ready**（fw-v0.9.0 候选：形态批 F3 + 清欠批 P1 合版；owner 点头即 tag+push）。**P1-2 ✅ 全链收口（2026-10-17——CONNECTED loc=tls + 经 TLS 部署判据；根因 = 双重内存耗尽已修，前架构域诊断推翻）。外设三路失败已破案（2026-10-17 板态域——I2C0 总线锁死 + SD 旧介质态，同族配置全绿证伪配置回归/接触不良两假说；证据 periph_restore_console.txt，板已复原 TLS E2E 态 + 三外设全绿）。待 owner：① USJ 线缆重插（宿主枚举闩死——顺手项不阻塞，CH343 三功能替补）；② 版本 tag review（fw-v0.9.0 点头即 tag+push）。**

（DEC-62 项已裁毕：
：Q-46 → 开工/F3〔② LVGL 修订〕；版本 tag → 并入下版〔F3+P1 收口时一并 review+tag〕；gcov → 缓办维持〔随 CI 强化批评估〕——F1/F2 物理判据已先行收口 v1.91）

### C. 环境挂起项（外部依赖，不占批）

| 项 | 挂起原因 |
|---|---------|
| 上游 Zephyr v4.5.0 正式版平移 | 正式版未发布（rc1 在用；**owner 2026-10-19 裁定顺延——发布约 2026-10-26，期间 V0.13.0 Agent 重点批先行**；发布后 1-2 会话平移 + workaround 回收 + P4 判定批〔BV1 第二任务〕） |
| P4 板无线面 | Zephyr esp_hosted 上游数据面缺陷（issue #121767 在案）——上游回复后复测 |

### D. Agent 侧候选（CLI 调研批九候选余项——随 owner 点向，建议序 = 调研排序）

| 候选 | 内容 | 现状 |
|------|------|------|
| D2 计划/进度工具 ✅ | **已实现（2026-10-18 · DEC-65⑤ 并入 V0.11.0 批）**：Task.progress 结构化进度面 + task_progress MCP 工具（{task_id, state, progress}——app_develop 创作循环事件经 note_loop_progress 单一映射源实时落位：plan 项/轮次/loop_state/evidence 计数；task_status.snapshot 同源携带）+ 用例 4（映射矩阵/未知事件/浅拷贝/MCP 面）——agent 208+2s | — |
| D4 hooks 拦截面 | **V0.12.0 并入（DEC-66①）**——MCP 工具调用前/后钩子（诊断自动注入等）；拦截/放行语义门③子呈递 | V0.12.0 |
| D5 决策链回放器 | **V0.12.0 并入（DEC-66①）**——审计流 → 时间线回放（web 客户端时间线面同源消费） | V0.12.0 |
| D6 MCP 客户端 | Agent 作为 MCP client 消费外部工具服务器 | **V0.13.0 并入（§11h I 表 A5——owner「重点放在 Agent」点向）** |
| D7 问询双向化 | **V0.12.0 并入（DEC-66①，web 客户端硬前置）**——终端门面问询 → MCP 客户端问询透传 | V0.12.0 |
| ~~多代理/通用文件工具面~~ | — | 调研建议不做（维持） |

### E. 长期方向（既有登记维持）

- 多域 DomainPack（PCB/结构件域 agent——CreationVerifier 第二实现；DEC-33 北极星）
- A2A/ACP 协议接入（缝保留，真实消费者出现再启）
- 生产化批（安全认证路径/量产烧录流水线——owner 点向后规划）
- SMP 多核 APP 并行（维持裁剪：rt[N] 单核已满足语义——需求实据出现再评估）

### G. Agent 协同批 V0.12.0（§11h，2026-10-19 owner 点向「Agent 确实需要升级」+ 多渠道交互新需求——DEC-66；执行序 R11 调研 → D7/D4 → 门③ Q-48 → W1 web 客户端 → D5 → 收口）

> 双轨：① Agent 流程结构收尾（D4/D5/D7——九十六调研缺口清单收口）；② **多渠道交互架构（MCI）**——DEC-35 Frontend 缝演进为显式三层渠道模型（Transport × Renderer × Interaction），Web 客户端为第一新渠道（传输复用 MCP Streamable HTTP；消费 D2 进度面/D5 时间线/D7 问询）。R11 调研批随批执行（克隆 opencode/codex/gemini-cli/aider 代码级学习）。

| 序 | 单元 | 内容 | 规模 | 备注 |
|---|------|------|------|------|
| R11 ✅ | 开源 Agent 代码调研批 | **已交付（d6a4378 + 续二/续三）**：六项目代码级研读（opencode 协议优先单服务器+SSE 总线+permission/form 协议一等公民〔形态主角〕/ codex protocol crate + EventMsg 版本化 wire + ReviewDecision 三维审批 / gemini-cli semantic-tokens / aider UI 包 CLI 反模式）+ **pi 深评（owner 问 make-vs-buy 触发）**——整体替代否决（域网关/安全哲学/关键路径耦合三理由）/ **pi 第二渠道采纳**（MCP Streamable HTTP 精确匹配） / W1 照旧（pi 无 web）+ Q-48 门③呈递四子项 | ~1 单元 | DEC-66③⑤ |
| M1 ⏸ | pi 渠道接入 | **HOLD（DEC-66⑥——owner 裁 pi 吸收待定；双运行时代价顾虑）**：ARM 机装 Node + pi（钉版）→ `pi mcp add tessera --url` 直连 FastMCP 网关 → toolExposure 分级 → 严格审批双通道演练 → 验收 = 经 pi 完成 app_develop→deploy 全链。候选替代 = QwenPaw（Python 单运行时——但 350k LOC 助手框架更重，R11 §7.4）——**harness 引入决策推迟至 W1 真实体验后** | ~0.5 | DEC-66⑤⑥ |
| D7 ✅ | 问询双向化 | **已交付（b8aa6a7）**：QuestionBroker（单次应答契约/枚举域 fail-closed/超时取 default）+ sys_pending_questions/sys_answer（无 token 便利面）+ CreationLoop._emit 异步感知（13 调用点，同步回调行为不变）+ app_develop plan_confirm 桥（缺省 False 行为不变；abort = TA_E_POLICY 结构化终止）——用例 7 | ~0.5 | DEC-67① |
| D4 ✅ | hooks 拦截面 | **已交付（b5c6d84）**：HookChain pre 裁决（config [hooks] 首匹配；prefix* 前缀；deny = TA_E_POLICY 归因 + 审计 hook_denied / observe = _hook 留观标；坏条目跳过；缺省空链行为不变）+ allow-session 审批三维（会话域记住不落盘/deny 不污染/token 先行）——服务端闸 = 管所有渠道真边界；post 观察面余项随 A10 | ~1 | DEC-67①③ |
| A10/A11 ✅ | MCI 架构 + web 客户端设计批 | **已落稿**：LLD-A10 v0.1（三层模型/归位表/SSE v1 轮询差分策略〔诚实注记〕/Renderer 契约判据行保真/安全边界两派对照/出站寻址预留不实现）+ LLD-A11 v0.1（案 A 形态/四区页面/语义 token 设计语言/判据行着色正则/零供应链面/测试口径） | ~0.5 | DEC-67 |
| W1 ✅ | web 客户端 v1 | **已交付（真实 uvicorn 冒烟四探全过）**：agent/web/ 五文件零构建前端（语义 token 深浅色/交互卡置顶/判据行着色零改写/自动滚底暂停）+ gateway/web.py（/web 同源挂载 + /events SSE 轮询差分）+ run_server http 组装（共享 AppContext）+ mcp.js 手写 MCP-over-HTTP 客户端（session 头维持/SSE 帧兼容）——消费 task_progress + D7 问询 + D4 审批（token 内存态）；时间线 tab 随 D5 点亮；pytest 5（挂载/ES 解析/路由/差分帧/SSE 流）+ 人工浏览器验收随 owner | ~1.5 | DEC-67② |
| D5 ✅ | 决策链回放器 | **已交付**：audit_replay.py（load_timeline——持久审计 JSONL 过滤/排序/截尾 + 条目语义派生〔sys_approve=审批/sys_answer=问询/其余=命令；hook_denied 状态〕+ render_timeline 文本形态）+ `tessera-agent replay` CLI 子命令（--day/--task-id/--tool/--json）+ sys_timeline MCP 工具 + W1 时间线 tab 点亮（同源数据）；坏行跳过回放不崩——用例 4（过滤/渲染/CLI 端到端 env 配置/MCP 面） | ~0.5 | DEC-67① |
| 收口 | V0.12.0 收口 | 回归定格 + tag fw-v0.12.0 | ~0.5 | |

### H. 通用化三需求（DEC-68，2026-10-19 owner 登记：① 自主板卡验证〔高优〕；② 需求驱动板卡选择/硬件设计〔调研〕；③ 结构件 3D 打印设计〔调研〕）

> 定位 = 「通用域」主张的硬件侧兑现：Agent 不止编排既有板，而是能验证新板（①）、按需求选板/设计硬件（②）、设计结构件（③）。① = DEC-33 域无关循环引擎 + Verifier 插件设计的第二域应用；② ③ = 多域 DomainPack 北极星的具体化前哨。执行窗口：v4.5.0 平移批之后（① 的首任务 = P4 判定批实测）。

| 序 | 单元 | 内容 | 规模 | 备注 |
|---|------|------|------|------|
| BV1 | 板卡验证域（① 高优） | Board Validation Verifier（build/flash/console 判据/迭代修复 → bring-up 报告）+ 板卡画像面（toolchain/WAMR 映射/thunk/PSRAM/启动链声明式清单）；**首任务 = P4 判定批实测**（Agent 半自主跑最小链）——与 P4 适配汇流 | ~1.5-2 | DEC-68① |
| R12 | 板卡选择/硬件设计调研（②） | 能力目录 schema/选型判定链/硬件设计建议边界（原理图级 vs 模块级）——依赖 BV1 沉淀的能力画像 | ~0.5 | DEC-68② 调研 |
| R13 | 结构件设计调研（③） | 参数化 CAD 路线〔OpenSCAD/CadQuery〕/可打印性约束面〔壁厚/公差/悬垂/方向/材料〕/与功能需求耦合〔开孔/散热/装配〕/Verifier 形态（可打印性机械检查） | ~0.5 | DEC-68③ 调研 |

> **2026-10-19 owner 修订（DEC-68 执行注记修订）**：v4.5.0 正式版仍需约一周——owner 指令「继续其他部分功能开发，重点放在 Agent」。BV1 **提前至 §11h I 表（V0.13.0）**，首任务改**现役板自验**（atkbench/xiao——先在已知好板上证明验证域本身）；P4 判定批实测降为 BV1 第二任务（随 v4.5.0 平移批，上游/硬件就绪后）。R12/R13 并入 V0.13.0 调研单元。

### I. Agent 自主化批 V0.13.0（§11h，2026-10-19 owner 点向：「v4.5.0 还需等待一周——继续其他部分功能开发，重点放在 Agent，规划下一版本」；DEC-68 执行注记修订生效）

> 定位 = **Agent 自主化**（v4.5.0 平移批顺延至上游正式版发布〔~2026-10-26〕后另立 V0.14.0 候选）：① **BV1 板卡验证域**（DEC-68① 高优——Agent 面对新板自行验证；首任务 = 现役板自验，P4 判定降第二任务）；② **D6 MCP 客户端**（DEC-12 v1.1 双角色另一半——九十六候选⑦ 销项）；③ V0.12.0 批内余项（SSE 直推/多任务视图/D4b post 钩子）；④ **R12/R13 调研**（DEC-68②③）。执行序 BV1-D → BV1-I → BV1-R → A3 → A5 → A4 → R12 → R13 → 收口。

| 序 | 单元 | 内容 | 规模 | 备注 |
|---|------|------|------|------|
| BV1-D ✅ | 板卡验证域·设计批 | **已落稿（LLD-A12 v0.1）**：确定性检查流水线定性（板卡验证非 LLM 创作任务——不硬套 CreationLoop；DEC-33 原则面继承：结构化证据/事件审计同源/CheckResult 对齐 VerifyOutcome 同型，如实注记）+ 板卡画像 schema v1（agent/boards/*.toml 七节声明式：serial/flash/boot/zenoh/caps/smoke/build——零凭据；R12 能力目录种子）+ 检查项目录 v1（C0 构建烧录前级〔画像门控缺省关〕→ C1 串口在场 → C2 flash 身份 → C3 boot/console → C4 zenoh 连通 → C5 caps 消费 → C6 部署 E2E 冒烟）+ SKIP 双型（派生 vs 声明）+ overall 三态判定（PASS/FAIL/DEGRADED）+ 板态变更披露合同（C6 探针驻留不自动还原——smoke 节即显式授权；C1-C5 只读或可逆）+ MCP board_validate（strict+spawn+D2 progress）/ CLI validate 双面 + FakeBoard 测试口径 + v2 方向登记（自动修复轮=P4 判定批形态/LLM 诊断留缝） | ~0.5 | DEC-68①；全部组合既有面（tools_diag capture/classify + tools_net deploy/ZenohService + tools_fw） |
| BV1-I ✅ | 板卡验证域·实现批 | **已交付**：domain/board_validation.py（画像 fail-closed 装载〔未知节/键拒——防拼写静默失效〕+ 检查项 C1-C6 全实现 + SKIP 双型/派生链 + overall 三态 + BoardReport JSON/人读双形态）+ 板卡画像两份入仓（agent/boards/ atk〔serial by-id/boya 16MB/C5 实测 2048KB 校准〕+ xiao〔板未接线占位——port 空 = C1 如实 FAIL〕）+ LiveTransport（esptool 5 双形态 chip 解析/仓相对路径解析/C6 部署链 ctx 装配）+ MCP board_validate（strict+spawn+D2 progress）/ CLI validate（退出码三态）——用例 33（FakeTransport 全矩阵：三态 × 派生链 × stop_on_fail × 报告双形态 × LiveTransport 无硬件分支）；agent **262+2s** | ~1.5 | 过程三修：esptool `Chip type:` 形态解析/CLI ctx 漏装配（首跑即暴露）/画像路径 CWD 无关化 |
| BV1-R ✅ | 板卡验证域·真机自验 | **C1-C5 全 PASS 稳定复现**（串口/boya 16MB 身份/CONNECTED 判据/akn-akc 命令面/caps 2048KB——板健康判定成立）+ xiao 第二画像复验 = 板不在场形态按设计工作（C1 FAIL → 派生 SKIP 链）。**C6 = 真机缺陷阻断——验证域首战抓获**：部署分块突发 → `esp32_wifi_adapter: memory allocation failed`（R5-I 同象）→ **`rx_q[0]` 栈溢出 FATAL 崩机**（板侧串口全文实抓——bv1_c6_crash_console.txt）；确定性复现（新鲜板态同崩，步点 lease/begin/chunk 随机）；**处置纪律 = 如实 FAIL 不掩蔽**（降级分块/跳过冒烟均不做） | ~0.5 | 缺陷入板级专项候选：R5-I「DRAM 系统性重平」残余 + rx_q 栈面新形态——root cause 随板级批（map 驱动重平续作）；证据 bv1_atk_console.txt |
| FIX-1 ✅ | 板级部署崩机专项（BV1-R C6 破案——owner「请先进行该问题的修复」） | **根因 = rx_q[0] 栈 NET_RX_STACK_SIZE 缺省 1500B 被部署突发压穿 → FATAL 崩机**；修复 = **4096**（atkbench prj.conf；dram0 +2.1KB）。两轮否定实验（教训 41）：STATIC_TX+SPIRAM heap=关联活数据面死（wifi RX DMA 入 PSRAM→DHCP 不可达）；STATIC_TX 单用=关联失败 rc=-134（4.5-rc1 驱动/hal 双层 TX buffer Kconfig 映射存疑——撤回登记上游核实）。prov 安装闸 lconf 1→0 复原（F3 残留挡 activate）+ **agent 租约瞬断自愈**（deploy.py chunk 路径「lease required」→ force renew 同 idem 重发——板侧执行器停顿 >TTL 懒过期自愈）。**判决：全链 C1-C6 六项 PASS（196.6s）+ C4+C6 两轮连 PASS；twister 17/17（115）+ agent 263+2s 回归无损**；残余 = wifi ENOMEM 日志噪声（map 重平专项存续）+ D9 探针驻留（披露合同） | ~0.5 | 教训 41/42 入册 dev-env v2.30；证据 bvfix_c6_console.txt；prov 姿态变更注记（lconf 0——可要求重挂） |
| MP ✅ | 通用内存规划专项（DEC-70）——**设计批+实现批+首应用+基线随批完成（DEC-71 泛指令按建议序）** | **① memory_audit 工具**（LLD-A13 v0.1 门③随批）：构建期确定性审计——GNU ld map + .config 两芯片无关接口（xtensa/host 同构实测）；三层账本（region 占用/保留/余量 + 具名对象符号归并 + config 内存意图账）+ 规则目录 v1（R0 声明≠生效/R1 rx 栈/R2 sysworkq/R3 shell 栈/R4 wifi TX 堆压/R5 TLS 堆下限/R6 区域余量/R7 STATIC TX 观察——每条挂教训出处）；MCP memory_audit（confirm 本地只读）+ CLI `memory-audit`（退出码三态）；用例 26（合成夹具矩阵 + atk 真图摘录锚定）。**首战抓获两潜伏缺陷**：WAMR=n+APPMGR=y 自 M7 起链接断链（pkg.c stage_commit 未门控——netbench 类最小档 4.5-rc1 构建不过，随批修复）+ netbench/deploybench 双 bench 缺 FIX-1/R5-V③ 同型防御（rx 1500/sysworkq 1024——R1/R2 双 fail，随批双 4096）。**② 首应用 atk 重平**：TX 上限 32→16（R4——峰值堆压减半）+ prj.conf 死值清理（R0）；真机判决 **C1-C6 六项 PASS（206.6s）+ 手工部署链零重试**；ENOMEM 噪声降频未根除（3 次/窗——R5 接受态登记，根除路径随 MP v2/板级专项）。**③ 最低内存基线**（docs/memory-baseline.md v0.1）：三档实测总账（最小 net 档 PASS heap 139K/标准档 PASS heap 131K/全外设档 WARN heap 58K+TLS31K+LVGL16K）+ 过程陷阱三条。回归 twister 17/17 + agent **289+2s**（+26） | ~2（原估设计批） | DEC-70/71；LLD-A13；教训 43 |
| A3 ✅ | **W2 web 渠道重塑**（DEC-69）——**全批 ✅（W2-D 门③过〔DEC-72〕+ W2-1..4 实现批）** | **批内切分（规模重估 ~5 单元——原 ~1 估不再适用）**：W2-1 基建（EventBus 发布钩子〔registry/brokers 缺省零变化〕+ /events v2 快照/Last-Event-ID 续传/resync/心跳 + sys_tasks 工具）→ W2-2 呈现层（会话流气泡/Agent 状态灯/活动心跳/计划打卡 + tokens v2 双主题 + 设置栏 + 响应式三档 + 文案层〔判据行保真合同不变——普通模式为叠加摘要层〕+ 时间线过滤尾随 + 诊断帧纪律）→ W2-3 双模式（clarify 需求澄清域：缺口分析→澄清轮≤3→spec 合成→**spec 门不变**→确认交棒 app_develop——Agent 能力增量 + app_clarify MCP 面 + 前端模式切换）→ W2-4 收口（多任务视图 + 回归定格 + LLD 修订）。服务端闸/审批 token/审计同源全不动；pi（M1）维持 HOLD 待 W2 体验 | W2-1 ~1 / W2-2 ~1.5 / W2-3 ~1.5 / W2-4 ~0.5 | DEC-69 + W1 验收反馈；LLD-A14 |
| A5 ✅ | D6 MCP 客户端——**已交付（LLD-A15 §2）** | gateway/mcp_clients.py `MCPClientDomainPack`：config `[mcp_clients]`（url=HTTP/command=stdio；名字净化防撞）→ 每 server 桥接面 `x_<server>_list`（清单透传只读）+ `x_<server>_call`（点名调用——**strict 双闸**〔工具体审批 + PolicyTable〕+ spawn 长任务句柄 + 60s 超时 + 外部故障结构化）；v1 每调用连接（连接池 v2）；组合根按配置注册（非空才挂）；用例 6（内存 server 全链 list/call/deny/净化/config/注册事实——`_inline` 测试注入面 config 加载器不产生） | ~1（实测合批） | DEC-12 v1.1；九十六候选⑦销项 |
| A4 ✅ | D4b post 观察钩子——**已交付（LLD-A15 §3）** | hooks.py post 面（`when="post"` 仅 observe——post deny 解析期拒收；`HookChain.post` 全匹配 + `summarize` 结果摘要 400B 截断）+ platform `audited` finally 段接线（审计后逐命中发布 `hook.post` 事件——W2 SSE 消费面，永不反噬调用）；诊断消费闭环随诊断批；用例 3（解析/匹配截断/网关集成事件到达） | ~0.5（实测合批） | D4 余项收口 |
| R12 ✅ | 板卡选择/硬件设计调研——**已交付（docs/research/R12-board-selection.md v0.1）** | 资产盘点（BV1 画像=目录种子/memory_audit=选型硬门/caps 实测面）+ 目录 schema v0（BV1 超集 `[hardware]` 节——每字段须机械可校验来源）+ 判定链五步（需求抽取〔clarify 同型〕→目录匹配→**内存基线硬门**〔MP 消费〕→策略排序→BV1 实测闭环；①-③ 确定性流水线，LLM 仅语义理解处）+ 硬件设计边界（模块级建议=可交付/原理图级=边界外）+ 缺口路线（目录随接入增长/跨芯片行待 P4 回填） | ~0.5（实测合批） | DEC-68② 调研 |
| R13 ✅ | 结构件设计调研——**已交付（docs/research/R13-structural-design.md v0.1）** | 域定性（LLM 生成 + 机械 Verifier——DEC-33 插件第三域形态，CreationLoop 主体零改动）+ CAD 路线对比（**CadQuery 倾向**——Python 生态同构/ws_* 工具面复用；OpenSCAD 留参照）+ 可打印性检查目录 v0 七条（壁厚/悬垂/桥接/公差/流形/行程/薄壁——网格级机械检查零 LLM）+ 功能耦合（`[physical]` 画像节 fail-closed/散热规则化/实物判据=唯一人工环节如实登记）+ Verifier 形态（compile/check/package 三步同构）+ 缺口路线（OCP 沙箱策略随立项） | ~0.5（实测合批） | DEC-68③ 调研 |
| 收口 ✅ | V0.13.0 收口——**已完成** | 回归定格 + 文档对齐（「外部计数文档对齐」checklist 项首跑 + **HLD-agent v0.2.3 深度修订**——v0.2.2 停在 V0.6.0 时代，V0.12〔D2/D4/D5/D7/W1/MCI〕与 V0.13〔BV1 域〕面未入 HLD）+ tag fw-v0.13.0 | ~0.5 | 批合计原估 ~6.5 单元——A3 扩为 W2 重塑后待设计批重估 |

### I2. 硬件定向批 HW + 新板适配 BV2（§11h，2026-10-19 DEC-73 立案 + HW-D 设计批过门③；2026-10-21 owner 扩令「应该在Agent层面全面进行优化」——HW-4 新登记；**全批 ✅ 收敛 2026-10-21**）

> 定位 = Agent 硬件事实能力：定向（哪块板）→ 选型（联网调研）→ 适配（新板接入）→ **事实（创作链引脚级硬件事实全面优化——W2 验收 LED 缺陷实证的创作链软肋）**。设计底稿 = LLD-A16 v0.2（门③已过）；HW-4 扩充随开工时 LLD-A16 v0.3 补呈门③。

| 序 | 单元 | 内容 | 规模 | 备注 |
|---|------|------|------|------|
| HW-D ✅ | 硬件定向·设计批 | **已落稿（LLD-A16 v0.2，DEC-73 三裁决门③过）**：硬件定向流程（需求分析先行〔不预设硬件〕→ 问询「是否有现成板卡」三路〔目录内选——在线发现仅辨认辅助 / 其他板卡→Zephyr 收录检查——收录=BV2 适配接入、未收录=请客户提供原理图人机协作移植 / 没有→联网选型调研〕→ 需求×能力核对不满足→外接硬件或更换板卡问询）；web_search 工具面（QwenPaw 同款 Tavily keyless 匿名模式——`X-Tavily-Access-Mode: keyless` 免 key + env key 升级 + 401/429/432 自动回退；SearchProvider ABC + 工厂未知值 raise 不静默路由；弃 ddgs）+ 查询词凭据过滤 + 审计全量；选型调研路径（LLM 结构化候选 ≤5 + 内存基线机械预筛 + 推定态标注——采购+BV1 前为推定态诚实边界） | ~0.5 | DEC-73；W2 验收实证缺口触发（板卡事实不在创作提示） |
| HW-1 ✅ | 硬件定向流程实现——**已交付** | clarify 前置 S0 槽四分支落码（画像 `[hardware].board_target` 映射 + get-info board=CONFIG_BOARD 自报消费 + 问询卡接线）+ 未提硬件默认提醒 | ~0.5 | LLD-A16 v0.2 §S0 |
| HW-2 ✅ | web_search 工具面实现——**已交付** | gateway/websearch.py：SearchProvider ABC + TavilyProvider keyless/Bearer 双模 + 401/429/432 三态回退 + 工厂 raise + scrub_query 凭据打码 + MCP `web_search`（confirm 出站面）；用例 6 | ~0.5 | LLD-A16 v0.2 §web |
| HW-3 ✅ | 联网选型调研路径实现——**已交付** | ResearchOut 候选 ≤5（search_web 工具内嵌同 provider）+ 内存机械预筛（总内存 <512KB 剔除——memory-baseline 口径）+ 推定态标注 + 候选问询卡；用例并入 clarify HW 族 | ~0.5 | LLD-A16 v0.2 §S0c |
| HW-4 ✅ | **Agent 级硬件事实全面优化——已交付（五面+一）**（owner 2026-10-21 扩令） | LED 缺陷（串口 168 对 LED BLINK ON/LED WRITE REJECTED——LLM 假设 gpio0=板载 LED 零事实支撑；编译门/判据门双盲区）全链根治于 Agent 层：① 板卡画像**引脚级事实节**（板载 LED/按键/外设→通道域×实例映射，每字段机械可校验来源〔DTS/原理图/实测判据行〕——R12 纪律延伸；atk 补 LEDB=IO4∈akpwm 实证）；② 创作链硬件事实注入（app_develop 提示携带目标板可用通道/实例/约束面）；③ **caps×画像机械核对门**（manifest 申请通道实例画像无物理绑定→装前拒——soft-pass/hard-invalid 缺口机械补位）；④ 判据生成硬件感知（S8 判据行引用通道须过物理存在性核对）；⑤ 部署后硬件回执诊断（WRITE REJECTED 族聚类→自动诊断回喂修复轮——D3/hook.post 同源消费）。LLD-A16 v0.3 门③随批（实现含设计期实证修正：缺陷包解剖 = caps 仅 log 而源码调 ts_gpio_write——第一层为声明缺失〔TEST 自动授予仅覆盖 log，IR-16〕，物理缺绑定第二层）| ~1 | owner 扩令；快改方案废弃——治理根因；**真像回归锚：缺陷包 caps × atk 画像门 REJECT + 声明-调用一致性 face_check 拦截 + pwm:set:0 PASS** |
| BV2-D ✅ | 新板卡适配域·设计批——**已落稿（LLD-A17 v0.1，门③三决策点呈递）** | DEC-68① BV 域从验证延伸到移植（P4 playbook Agent 化）：收录板生成接入件〔分区 overlay/conf/WAMR 映射〕+ BV1 判据链 bring-up + 画像入目录；未收录板原理图人机协作出移植清单 | ~0.5 | 门③另呈（独立批） |

### F. 健壮性收口批 V0.10.0（§11h，2026-10-17 owner 泛指令点向「按照推荐开发顺序进行开发」——DEC-64；执行序 R1 → R2 → R4 → R3）

> 来源：ARM 重建会话（一四五）三项登记固件健壮性缺陷 + TLS 会话陈旧观察项；owner 按建议序点向开工。定位 = 无路由器/长失联场景 fail-safe 常驻（降级而非复位循环）与 ARM 机新暴露域收口。

| 序 | 单元 | 内容 | 规模 | 备注 |
|---|------|------|------|------|
| R1 ✅ | 断链重连健壮化 | **已交付**（根因 = 退避表只护调用间隔、tick 顶喂狗只护间隙，**护不住 open 调用体**——死路由 TCP connect+TLS 握手阻塞 > NET 喂狗窗 2s → 巡检中途判逾 → system_fail 复位环〔arm64_rebuild §8 真机实证〕。修复 = **声明式 WDT 豁免窗**：core 增 `ts_wdt_grace(src, budget)`（窗内巡检不判逾/超窗恢复判逾 fail-safe 保持/feed 清除/60s 钳制/不激活源）+ session_poll open 前后接线（grace → open → feed 成败同路）+ CONFIG_TS_NET_OPEN_BUDGET_MS 15000（观测单次失败 2-5s ×~3 裕度）；握手段 BIO 心跳钩（DEC-63①）保留为独立防线。用例 core grace 数学六断言组 + net test_17 接线双路；LLD-ts-core v0.2.3/LLD-ts-net v0.4.5） | ~0.5 单元 | DEC-64① |
| R2 ✅ | TLS 会话陈旧根因 | **已交付**（根因 = zenoh-pico 单 executor 线程协作模型 + Zephyr 默认 RCVTIMEO=n 使 SO_RCVTIMEO 静默无效 → recv 永久阻塞钉死 executor → lease 任务饿死 → 入向断流判死与自动重连永不执行；router 侧被我方 z_put 心跳喂活 = 双侧互盲。修复 = TS_NET_ZENOH select NET_CONTEXT_RCVTIMEO + atkbench NET_MAX_CONTEXTS 12→4；真机黑洞判定 ≤15s 自愈（端口切换零复位）vs 修复前 25min+ 僵尸。一四二④/NVD v5/x86 同象全归因。证据 r2_tls_oneway_root_cause.txt；LLD-ts-net v0.4.6） | ~1 单元 | DEC-64② |
| R4 ✅ | 健壮性小项 | **已交付**（nvd_demo.py 板型感知参数化——--window/--node/--cube/--port + 路径仓库根派生去 /home/emb 硬编码〔atk 口径 --window 90 实测入 checklist ⑦〕；zenohd-tls.service systemd 用户单元入仓并实机启用——linger 常驻 + 失败自启，`\"` 转义保留 zenohd JSON 引号实测过；路由器进程切换时板自动重连再证 R1+R2 链） | ~0.5 单元 | DEC-64③ |
| R5-U ◐ | UART 交互终端·设计批 | V0.11.0 开工（owner「按照建议开工，完成这一阶段的开发任务」2026-10-18——DEC-65 按建议值）：LLD-ts-interact v0.1（单 UART 三合一形态/ts 命令集七条/信任级=物理在场代理/判据行兼容策略/TS_INTERACT 门控缺省 n） | ~0.5 | DEC-65 |
| R5-I ◐ | UART 交互终端·实现批 | **框架面已交付**（src/interact 薄命令层 + framework.interact 用例 3/3 + Kconfig/CMake 门控缺省 n；单 UART 三合一形态真机点亮 + 终端命令面真机 HIT〔info/pending/log〕——证据 r5_interact_console.txt）；**atkbench 接线回退待重平**：shell/log 静态 ~3.9KB 挤占后 WiFi TX 突发 ENOMEM（部署高压掉线）——净缺 ~8KB 静态 DRAM，map 驱动重平随 R5-V 续批首项。**顺带根治存量缺陷**：build_prov12 实产 204B > 调用方 pb[192]（cap 参数被 ARG_UNUSED 忽略）= 12B 栈越界写——app 套件帧布局侥幸未爆、interact 套件引爆（SIGBUS），两侧同修（cap 检查 + pb 256） | ~1 | DEC-65 |
| R5-V ✅ | UART 交互终端·真机批 | **僵尸自愈收口 ✅（2026-10-18）**：稳定像部署突发击链 → 板 zenoh 全哑 30min+ 零自愈（AUTO_RECONNECT=0 后 glue 判死信号失效）——根因 = **1.10.1 执行器模型 zp_*_task_is_running 语义漂移**（两 API 均退化为「执行器线程存活」，租期 fut 判死退出后 is_up 恒真 = 永久僵尸）；修复 = is_up 三判据 + pico 补丁新访问器 `zp_transport_is_open`（传输态本体；全部死法汇入 _state=CLOSED，半开由租期一租期内兜底）+ NET_CONTEXT_SNDTIMEO select + tcp_zephyr.c SO_SNDTIMEO 对称补丁 + 部署工具超时跨自愈窗重试（8s×2）；**真机判决 = 路由器重启注入 → 判死→一次 -102 退避→CONNECTED 零复位（app 跨断链不受扰）+ 部署全链 PASS + NVD 复验 NVD DONE ticks=10 + 诊断像 6/6 部署过**（证据 r5v_zombie_heal_console.txt；LLD-ts-net v0.4.7）；console=uart0 诊断形态单变量实测（app 日志经 CH343 可观测——板 IP 确证 192.168.2.67）；**R5-V①②③ 全收口（同日续）**：DRAM 重平一击命中（pico pthread 栈池 4→2 = map 实证 system.c 32KB→16KB，释放 16KB 静态——执行器单线程设计）+ R5 接线全上（`uart:~$` 1.9s 点亮 + 日志同 tty，部署 3/3 过——昨日阻断位清零）+ **F3 终端确认/拒绝四判据 ALL PASS**（deploy→PENDING→`ts confirm`→暖复位→NVD DONE 全链 + `ts reject` 槽保留零复位；prov 重烧 lconf=1 同身份）+ **NVD 复验 PASS** + 双栈真机定案（SHELL_STACK 4096 = confirm 链 EXCCAUSE 0 野跳根因；SYSWORKQ 4096 + STACK_SENTINEL = 板缺省 1024 建链窗溢出 SENTINEL 点名——历史静默腐蚀族同象嫌疑）+ stage_commit 包身份提取（verdict 行保真，键判别错位被真机判据当场拦下）+ flash_prov esptool5 二进制名/写前擦除 + offset 陷阱登记（证据 r5v_verdicts_console.txt）| ~0.5 | DEC-65 |
| R5-history | （历史登记——原 R5 ◐ 行）UART 交互终端（owner 需求 2026-10-18 登记 + 同日扩意） | **需求已登记未排期**（owner：板子要像安卓机器——屏幕/音频/按键非必然存在，**板卡最常见的是 UART**；为板卡添加类 linux 终端的交互 UART 终端。消费点 = 无外设形态板的**本地交互源**：F3 安装闸 confirm/reject（现预设 BOOT 手势+LCD）、CG3 arb 席位本地切换、F2 estop 本地清除——同一 pending/arb 挂点换终端载体。**同日扩意（owner）**：console 观测恢复不单独做，**并入本单元**——日志与应用输出与交互终端同走 UART 一路（类 Linux 串口终端形态：printk/getty 同 tty；Zephyr 侧 = shell + log backend 复用，`CONFIG_SHELL_LOG_BACKEND` 原生支持 prompt 保持重绘）；USJ 面保留可选。**设计批门③随排期呈递**（安全语义：终端=物理在场代理，与 BOOT 键同信任级；与 bench 判据行消费的兼容策略） | 1.5-2 单元 | owner 点向排期后开工 |
| R3 ✅ | WAMR /64 仿真缺陷 | **已交付**（root cause = GENERAL C thunk 契约错配：我方为 ia32 汇编 GNU-stack 设 `INVOKE_NATIVE_GENERAL=1`，其契约「argc 个连续 u32 字」仅匹配 32 位 branch A 线性布局；64 位目标编译寄存器分类路径〔fps/ints/stacks 三桶，exec_env 64 位进 ints[0]，小签名 n_stacks=0〕→ GENERAL 收 argc=0 零参数调用 native → exec_env 形参 = 寄存器残留 → user_data 常数垃圾 0xaa0803f0a9467bfd → SIGSEGV；X86_32 目标 ARM 机「静默不落地」同闭合〔branch A 单字 exec_env 零扩展丢高位〕；「AARCH64 目标亦崩」系同携带 GENERAL 所致非目标本身。修复 = /64 按宿主处理器映射 AARCH64/X86_64 + 真实架构汇编 thunk + GENERAL=0 + `--noexecstack`；32 位 x86 CI 口径不变。**twister /64 = 16/16 套件 114/114 用例首次全绿**） | ~0.5 单元 | DEC-64④ |

## 12. 执行纪律（v1.70 增补质量优先条款）

- **质量优先（DEC-57，owner 2026-10-13 指令原文精神）**：**不允许最简实现**——各交付单元的设计与实现须考虑整体架构、后续可维护性与架构可扩展性；现方案不能很好满足目标时，**停批与 owner 确认讨论重新选择方案或技术**，不得静默绕行或降级实现。
- 其余纪律不变：每单元后 twister + agent pytest + L5 回归（军规 10）；阶段门/军规十条（FOUNDING_PROMPT §2/§3）。

- 规范套件（tag `std-v1`：testing/versioning/progress/coding）+ 军规十条 + 安全与确定性合同（AGENTS.md §6）。
- 里程碑退出 = review 门（呈递 DoD 对照）；工具面/公共 API/安全合同变更 = 各自 review 门。
- 进度记录规则按 `docs/std/progress.md`；本计划的状态列随里程碑更新。

## 修订记录
- v1.142 · 2026-10-21：**V0.13.0 版本收口 ✅（owner「请你先完成V0.13剩余部分的开发，完成V0.13.0版本」）——HW-1..4 实现批 + BV2-D 设计批 + 收口单元全批交付**。① **HW-1..4 实现批**（LLD-A16 v0.3 门③随批）：HW-1 S0 硬件定向槽四分支（mention 绑定/Zephyr 收录→BV2 工单/原理图协作/未提及主问询+联网选型+暂不指定）+ 能力核对；HW-2 web_search（Tavily keyless + 凭据打码 + confirm 面）；HW-3 选型调研（候选 ≤5 + 内存机械预筛 + 推定态）；**HW-4 硬件事实五面+一**（画像 [hardware] 引脚级节 v1.1 加性〔atk 补 LEDB=pwm:0 实证〕+ caps⇔natives 声明-调用一致性门〔face_check——LED 缺陷第一层：缺陷包解剖 caps 仅 log 而源码调 ts_gpio_write，TEST 自动授予仅覆盖 log〕+ caps×画像机械门〔审批前装前拒——gpio:write:0×atk 真画像 REJECT 真锚〕+【目标硬件】段创作链注入〔spec_gate 可选节兼容〕+ 判据硬件感知〔WRITE REJECTED 扫描→criteria_pass 降级〕+ 硬件回执诊断回喂）。② **BV2-D**：LLD-A17 v0.1（两路径〔收录板接入件五件套+BV1 bring-up/未收录板原理图人机协作〕+ 门③三决策点呈递——实现随裁决）。③ **收口**：HLD-agent **v0.2.3 深度修订**（MCI 三层四渠道/A10 行/交互域行/工具面九增/S9-S12/§5.4 安全面六增——v0.2.2 V0.6.0 时代之债清偿）+ README 计数对齐 + 回归定格（agent **343+2s** +28/ruff/repo 5/L5/sync + twister 17/17〔115+2s〕）+ **tag fw-v0.13.0**（附注式，push 待 owner）。V0.13.0 全批 = BV1×3 + FIX-1 + MP + W2 + A5 + A4 + R12 + R13 + HW-D + HW-1..4 + BV2-D + 收口 = **16 单元全 ✅**。
- v1.141 · 2026-10-21：**HW-4「Agent 级硬件事实全面优化」登记（owner 扩令：「应该在Agent层面全面进行优化」——LED 缺陷记为待开发项）**——§11h 新立 I2 表收拢 HW 批（HW-D ✅ LLD-A16 v0.2 门③过 + HW-1 定向流程/HW-2 web_search 面/HW-3 选型路径各 ~0.5 待实现 + BV2-D ~0.5 门③另呈）。**HW-4 = LED 缺陷（168 对 LED BLINK ON/LED WRITE REJECTED——LLM 假设 gpio0=板载 LED 零事实支撑，编译门/判据门双盲区）全链根治于 Agent 层五面**：画像引脚级事实节〔R12 来源纪律延伸，atk 补 LEDB=IO4∈akpwm 实证〕/ 创作链硬件事实注入 / caps×画像机械核对门〔装前拒——soft-pass/hard-invalid 缺口补位〕/ 判据生成硬件感知 / 部署后硬件回执诊断回喂；~1 单元，LLD-A16 v0.3 门③补呈随开工；**快改方案（重生成 app 加 pwm cap 演示向）废弃——治理根因不做单点演示修补**。
- v1.140 · 2026-10-19：**DEC-73 三裁决 + LLD-A16 v0.2 重写 ✅（门③修订过——HW 实现解锁）**——① 搜索改 QwenPaw 同款（Tavily keyless 匿名模式源码级核实——X-Tavily-Access-Mode: keyless 免 key + env key 升级 + 三态回退；弃 ddgs）；② 流程重写（需求分析先行 → 问询是否有板 → Zephyr 收录检查〔收录=BV2 接入/未收录=请客户提供原理图〕→ 能力不满足外接或换板；在线板默认绑定提案废弃——仅作辨认辅助）；③ 新板适配 = BV2 域独立批（P4 playbook Agent 化，门③另呈）。HW ~2 单元实现解锁（HW-1 流程/HW-2 web_search/HW-3 选型路径）+ BV2-D ~0.5。
- v1.139 · 2026-10-19：**DEC-73 硬件定向需求登记 + HW-D 设计批 ✅（LLD-A16 v0.1 门③呈递；W2 验收进行中）**——W2 验收实证缺口（板卡事实不在创作提示）触发：① 调研批（板卡身份链协议层已在——get-info board=CONFIG_BOARD + caps.peripherals 无人消费；联网搜索三路径——ddgs 零凭据/Tavily key/A5 桥接；R12 判定链 = 落地消费）；② 设计（clarify 前置硬件定向槽 S0 四分支：需求提及→目录绑定 / 目录外如实 / 未提及→在线发现确认〔get-info board 自报〕/ 不清楚→联网选型调研〔web_search 工具 + LLM 结构化候选 + 内存基线机械预筛 + 推定态标注〕）；③ 规模 ~2 单元（HW-1 硬件槽/HW-2 web_search 面/HW-3 调研路径）——门③三决策点呈递（provider 缺省/在线默认绑定/目录外通用面合成）。
- v1.138 · 2026-10-19：**R12/R13 调研单元交付 ✅（DEC-68②③——V0.13.0 批内最后两单元实现面收口，余 = 收口 tag）**——R12 板卡选型调研（BV1 画像=目录种子 + `[hardware]` schema v0 + 判定链五步〔内存基线=MP 硬门消费；确定性流水线定性〕+ 模块级建议边界）；R13 结构件调研（CadQuery 倾向 + 可打印性检查目录 v0 七条机械可判 + StructuralVerifier=DEC-33 插件第三域形态 + `[physical]` fail-closed）。均调研产出不实施（DEC-68 原文）。plan v1.138/names/AGENTS 续十五补登。
- v1.137 · 2026-10-19：**A5（D6 MCP 客户端）+ A4（D4b post 观察钩子）交付 ✅（owner「暂时没办法实测，进继续推进后续待开发项」）**——① A5：外部 MCP server 桥接（LLD-A15 §2——config `[mcp_clients]` url/command 双传输 + `x_<server>_list/_call` 前缀命名空间防撞 + strict 双闸不信任面 + spawn 句柄 + 60s 超时 + 结构化故障；`_inline` 测试注入面）；② A4：post 观察面（observe-only + 摘要 400B 截断 + `hook.post` 事件经 W2 总线外发——诊断自动注入缝）；③ 回归 agent **312+2s**（+10）/ruff 全绿。plan v1.137/names/LLD-A15/AGENTS 续十五。
- v1.136 · 2026-10-19：**W2 web 渠道重塑实现批 ✅ 全单元（DEC-72 门③过裁）**——① W2-1 基建：EventBus（common/events.py——线程安全 publish/订阅队列 queue_max 慢消费者 resync/环形缓冲 Last-Event-ID 重放）+ 发布钩子（TaskRegistry task.created/state/log + QuestionBroker opened/closed + ApprovalBroker requested/decided；bus=None 对照组零变化）+ note_progress 单一进度入口（last_activity_ts 活动触碰）+ /events v2（快照+直推+续传+15s 心跳+10s 慢速对账兜底+phase 派发表 11 态单源）+ sys_tasks 工具；② W2-2 呈现层：前端五文件重构（对话气泡流/状态灯呼吸/活动心跳/任务栏/时间线过滤尾随/设置抽屉 localStorage/双主题 tokens v2/响应式三档/copy.js 文案层——判据行保真合同不变：普通模式 diag 行与日志区隐藏）；③ W2-3 双模式：clarify 域（domain/clarify.py——缺口分析→澄清轮≤3/问≤8→spec 合成→spec_check 门一次修复→proceed 交棒 app_develop 同任务句柄/restart 结构化中止；LLM 失败结构化提示切开发者模式）+ MCP app_clarify（confirm）+ 前端普通模式接线；④ 回归 agent **302+2s**（+13）/ruff/L5/sync 全绿。plan v1.136/names/AGENTS 续十四/LLD-A14 v0.2/LLD-A11 v0.2。
- v1.135 · 2026-10-19：**W2-D web 渠道重塑设计批 ✅（LLD-A14 v0.1，owner「review完成，请你开始进行W2 web重塑设计」点向；MP 批 b2e7954 同令推送）**——① SSE 直推（EventBus 零依赖层 + registry/brokers 发布钩子〔bus=None 零行为变化〕+ /events v2 快照/Last-Event-ID 续传/resync 慢消费者策略/15s 心跳——消除重连清空）；② DEC-69 六点设计响应（会话流气泡/状态灯+活动心跳/设置栏/响应式三档/tokens v2/文案层——判据行保真合同不变，普通模式为叠加摘要层）；③ **双模式需求澄清域**（domain/clarify.py：缺口分析→澄清轮≤3→spec 合成→spec_check 门不变→确认交棒 app_develop——DEC-69⑥ Agent 能力增量）；④ W1 UX 四条 + 多任务视图落位；⑤ **规模重估 ~5 单元**（W2-1 基建 ~1 / W2-2 呈现层 ~1.5 / W2-3 双模式 ~1.5 / W2-4 收口 ~0.5）——门③呈递待裁，裁后开工。
- v1.134 · 2026-10-19：**MP 通用内存规划专项 ✅ 全批（DEC-71 owner 泛指令按建议序开工）**——① memory_audit 工具（LLD-A13 v0.1：三层账本 + 规则目录 R0-R7 + MCP/CLI 双面 + 26 用例真图锚定）；② 首战双缺陷（WAMR=n 链接断链 M7 遗留/pkg.c 门控修复 + netbench/deploybench R1/R2 双 fail 板级防御）；③ atk 首应用（TX 32→16 + R0 清理；真机 C1-C6 六项 PASS 206.6s；ENOMEM 降频未根除 R5 接受态）；④ 最低内存基线 docs/memory-baseline.md（三档实测：最小 net PASS/标准 PASS/全外设 WARN）——plan v1.134/dev-env v2.31（教训 43）/names/AGENTS 一四八；agent **289+2s**（+26）。
- v1.133 · 2026-10-19：**DEC-70 通用内存规划需求登记（owner：「为各种芯片设计通用内存规划程序，确保配置内存分配合理避免溢出；记录系统最低内存需求」）**——§11h I 表 MP 专项新立（① 跨芯片构建期内存审计/规划程序〔机械化拦截 rx 栈 1500/UI 栈 91%/堆 -80/wifi ENOMEM 实测案例〕② 按配置档最低内存基线文档）；atk map 重平合流为首个应用；设计批门③待呈递。
- v1.132 · 2026-10-19：**FIX-1 板级部署崩机专项 ✅ + BV1-R 转 ✅（owner「请先进行该问题的修复」）**——根因 = rx_q[0] 栈缺省 1500B 被部署突发压穿；修复 = NET_RX_STACK_SIZE 4096（dram0 +2.1KB）+ prov lconf=0 复原（F3 残留）+ agent 租约瞬断自愈（force renew 同 idem 重发）；两轮否定实验入册（STATIC TX/SPIRAM heap——教训 41）；**全链 C1-C6 六项 PASS + twister 17/17 + agent 263+2s 回归无损**；BV1 单元至此全部 ✅；残余 = wifi ENOMEM 噪声（map 重平专项存续）。
- v1.131 · 2026-10-19：**对账 review 批（owner「进行一轮 review——未完成项目 + 文档准确性」）**——实测：工作树干净 / 4 笔待 push / agent 263+2s + ruff + sync 全绿；修复三处文档失准：README agent 计数 208→263（+web 渠道行）、LLD-A11 v0.1.2（验收修订回填：composer 底部化/端点根绝对纪律/守卫测试 + W2 演进注记）、收口行补 HLD-agent v0.2.3 深度修订债（v0.2.2 停在 V0.6.0 时代——V0.12/V0.13 面未入 HLD）。
- v1.130 · 2026-10-19：**DEC-69 web 渠道产品反馈六点登记（owner：「先记录，后续可能还有补充」）**——①界面观感 ②普通用户文案与受众 ③对话式交互（用户消息入流 + Agent 状态指示）④多端适配 ⑤左侧设置栏 ⑥双模式（开发者全细节/普通模式 LLM 需求澄清——Agent 能力增量）；A3 单元范围扩为 **W2 web 渠道重塑**（连同 W1 验收 UX 反馈四条），规模重估待设计批（门③）。
- v1.129 · 2026-10-19：**W1 人工验收执行闭环（owner 浏览器实测）+ W1 验收反馈批（65a78bf）**——owner 全链实测：刷新修复后前端 → 发起心跳计数器 spec → 问询卡 proceed（sys_answer 落审计）→ 两轮收敛（第 1 轮编译拦截 stdint.h 系统包含 → 证据回喂修复）→ **PACKAGED 产物落盘**（tessera.demo.wbt-0.1.0.tsap 测试根签名）→ 时间线决策链核验；验收中实抓前端相对 URL 405/404 双缺陷（根因修复 + 静态守卫）+ composer 移底部 + 密钥缺省值；四条 UX 反馈归 A3（v1.128 行扩充）；验收服务（9960）按嘱停。W1 单元 ✅ 完整收口。
- v1.128 · 2026-10-19：**BV1-I 实现 ✅ + BV1-R 真机自验 ◐（V0.13.0 BV1 主体收口）**——board_validation.py 全链（33 用例/agent 262+2s）+ 两画像入仓 + MCP/CLI 双面；真机 C1-C5 全 PASS 稳定 + xiao 板不在场形态按设计工作；**C6 = 验证域首战抓获真机缺陷**——部署突发 wifi adapter ENOMEM → rx_q[0] 栈溢出崩机（板侧铁证；确定性复现；如实 FAIL 不掩蔽），板级专项候选登记（R5-I 重平残余族）。
- v1.127 · 2026-10-19：**BV1-D 板卡验证域设计批 ✅（DEC-68①，V0.13.0 首单元）**——LLD-A12 v0.1 落稿：确定性检查流水线定性（不硬套 CreationLoop，DEC-33 原则面继承如实注记）+ 板卡画像 schema v1（agent/boards/*.toml 七节）+ 检查项目录 C0-C6 + SKIP 双型/DEGRADED 判定 + 板态变更披露合同 + board_validate（strict）/validate CLI 双面 + FakeBoard 测试口径。BV1-I 实现随续。
- v1.126 · 2026-10-19：**V0.13.0「Agent 自主化批」立项（owner：「v4.5.0 还需等待一周——继续其他部分功能开发，重点放在 Agent」）**——§11h I 表新立：BV1 板卡验证域提前〔DEC-68① 执行注记修订：首任务改现役板自验，P4 判定降第二任务〕+ D6 MCP 客户端（A5）+ V0.12.0 余项（A3 SSE 直推/A4 post 钩子）+ R12/R13 调研并入；执行序 BV1-D → BV1-I → BV1-R → A3 → A5 → A4 → R12 → R13 → 收口（~6.5 单元）；v4.5.0 平移批顺延为 V0.14.0 候选（C 表同步）。
- v1.125 · 2026-10-19：**DEC-68 通用化三需求登记**——① 自主板卡验证（高优，BV1 板卡验证域；首任务 P4 判定批实测）② 需求驱动板卡选择/硬件设计（R12 调研）③ 结构件 3D 打印设计（R13 调研）；§11h H 表新立。
- v1.124 · 2026-10-19：**D5 决策链回放器交付 ✅（V0.12.0 批内全部单元 ✅）**——审计流时间线（CLI replay + sys_timeline + W1 tab 同源）；收口随 owner review（回归定格 229+2s）。
- v1.123 · 2026-10-19：**W1 web 客户端 v1 交付 ✅**——纯 Python 零 Node 全链成立（真实 uvicorn 四探冒烟）；web 渠道 = 第三个 MCI 渠道（Terminal/MCP-stdio/MCP-HTTP+web）。
- v1.122 · 2026-10-19：**DEC-67（Q-48 按建议值裁决）+ D7/D4 交付 + A10/A11 落稿**——问询实体/钩子链/allow-session 进主干（agent 220+2s）；MCI 与 web 客户端设计定稿；W1 实现随续。
- v1.121 · 2026-10-19：**DEC-66⑥（QwenPaw 重点参照 + pi 待定）**——R11 §7 QwenPaw 源码评审（渠道契约/Renderer/逐工具策略/governance/设计语言四件吸收进 A10/A11）；M1 挂 HOLD；执行序修订 = W1/D7/D4 先行（消解双运行时），harness 决策推迟至 W1 后。
- v1.120 · 2026-10-19：**DEC-66⑤ 修订（pi make-vs-buy 深评）**——三维判定（替代否决/第二渠道采纳/W1 照旧）+ M1 单元入批；R11 §6 pi 深评（MCP Streamable HTTP 匹配/无 web/OS 边界安全哲学/会话树）。
- v1.119 · 2026-10-19：**V0.12.0「Agent 协同批」立项 + 多渠道交互架构需求登记（DEC-66）**——owner 双指令：Agent 升级（D4/D5/D7 并入）+ 交互架构重设计（DEC-35 Frontend 缝 → 三层渠道模型；web 客户端第一新渠道，MCP HTTP 复用）；R11 开源代码调研批随批。
- v1.118 · 2026-10-19：**文档-实现一致性审查批（owner 指令「code review 对比文档检查不匹配」）**——11 处勘误：checklist/README/HLD §9 过时计数与通过线（14/16→17/17 等）、HLD §9 三行滞后（power/msg_send/TLS 实为 P1 批已交付）、LLD-ts-net「上游零源码补丁」陈旧声明（实为仓携带 9 文件补丁）、LLD-ts-interact Kconfig 依赖表与实现不符、deploy.py 自愈注释事实性修正（pico 自动重连已钉死——glue 重连 ≤26s）、Kconfig 重复 help 行、flash_prov offset 陷阱入 docstring。
- v1.117 · 2026-10-18：**D2 计划/进度 MCP 外显 ✅（DEC-65⑤，V0.11.0 批收官单元）**——task_progress 工具 + Task.progress 面 + note_loop_progress 映射；agent 208+2s。
- v1.116 · 2026-10-18：**R5-V①②③ 全收口 ✅**——DRAM 重平（pico 栈池 16KB 释放）+ R5 接线全上 + F3 终端四判据 ALL PASS + NVD 复验 + 双栈（SHELL/SYSWORKQ）真机定案 + stage_commit 身份提取 + flash_prov 补齐。
- v1.115 · 2026-10-18：**R5-V 僵尸自愈收口（AUTO_RECONNECT=0 域破案）**——is_up 三判据（zp_transport_is_open pico 访问器）+ SNDTIMEO 对称 + 部署重试；真机四判决（自愈/部署/NVD/6×6 稳定性）入证据；console=uart0 诊断形态定版（app 日志 CH343 可观测）。
- v1.114 · 2026-10-18：**R5-I 框架面交付 + atkbench 接线回退（DRAM 重平登记批内余项）**——ts-interact 组件/用例全绿（twister 17/17 套件 117 用例零失败）+ 三合一形态真机点亮；WiFi ENOMEM 发现与池三档实验入证据；prov12 栈越界存量缺陷两侧同修。
- v1.113 · 2026-10-18：**V0.11.0「无外设交互批」立项开工（DEC-65 按建议值）**——R5 展开为 U 设计/I 实现/V 真机三单元（R5-U LLD-ts-interact v0.1 落稿）+ D2 并行小项；§11h 批次表更名延续。
- v1.112 · 2026-10-18：**R5 范围扩意登记（owner）**——console 观测恢复不单独做，日志/输出/交互终端同走 UART 一路（类 Linux 串口终端形态，shell+log backend 复用）并入 R5；估 1.5-2 单元。
- v1.111 · 2026-10-18：**R3 WAMR /64 仿真缺陷根治 ✅（DEC-64④）**——GENERAL C thunk × 64 位寄存器分类路径契约错配定案；/64 按宿主映射 AARCH64/X86_64 + 架构汇编 thunk；twister /64 首次 16/16（114/114）全绿；§11h V0.10.0 批 R1-R4 全收口（R5 UART 终端已登记待排期）。
- v1.110 · 2026-10-18：**R5 需求登记（owner 指令）**——UART 交互终端（无外设板本地交互源：F3 安装闸/CG3 席位/F2 本地清除挂点，类 linux 终端形态）；未排期，设计批门③随点向呈递。
- v1.109 · 2026-10-17：**R4 健壮性小项 ✅（DEC-64③）**——nvd_demo 板型感知参数化（checklist ⑦ 对齐）+ zenohd-tls systemd 用户单元（入仓 + 实机启用 + linger）；§11h R4 收口。
- v1.108 · 2026-10-17：**R2 TLS 会话单向化根因定案 + 修复 ✅（DEC-64②）**——RCVTIMEO 静默无效 → pico 单 executor 被读任务钉死 → lease 饿死；select 修复 + 真机黑洞判定 ≤15s 自愈；§11h R2 收口。
- v1.107 · 2026-10-17：**V0.10.0「健壮性收口批」立项 + R1 交付（DEC-64——owner 泛指令「按照你的推荐开发顺序进行开发」按建议序 R1→R2→R4→R3）**。R1 断链重连健壮化 ✅：根因 = 死路由 open 调用体阻塞（TCP connect+TLS 握手）超 NET 喂狗窗、退避表与 tick 顶喂狗均护不住调用体（arm64_rebuild §8 复位环实证）；修复 = core 声明式 WDT 豁免窗 ts_wdt_grace（窗内不判逾/超窗恢复 fail-safe/feed 清除/60s 钳制）+ session_poll open 接线 + TS_NET_OPEN_BUDGET_MS 15000；LLD-ts-core v0.2.3/LLD-ts-net v0.4.5；§11h 新立（R2 TLS 会话陈旧/R4 小项/R3 WAMR /64）。
- v1.106 · 2026-10-17：**fw-v0.9.0 tag 打点推送（基线 5a8b9f3，附注式）——形态批 F3 + 清欠批 P1 + P1-2 TLS 合版正式收口**。同批环境审查（owner：环境将销毁、多机含 ARM 重建）：**tools/board 登记失实链结案**（.gitignore `/tools/` 整目录忽略 = b1a31e4/5cc02d4 两处「入仓」机械性失实根因；16 会话驱动 + gen_tls_certs.sh/ota_client.py 真实入仓 + tools/board/README.md）；**新立 docs/env-rebuild-checklist.md**（重建唯一总单：x86_64 实测 + aarch64 推定⚠待回填 + 分层验证七步）；migration-x86 §3/§5 更正；README 计数对齐（twister 113/agent 204）。回归：py_compile 19/bash -n/sync_check/pristine 构建（前批）全绿。
- v1.105 · 2026-10-17：**外设三路失败破案 + 板态复原（owner 复核反馈触发：SD 已重格/板载焊接连接无虞）**。判别过程：F3-1 worktree 全新构建不可判别（16M 布局 + console 不可见）→ 真值探针路线（console 临时切 uart0 经 CH343——ROM 下载协议已证数据路可用）→ **同族配置 boot 三外设全绿**（es8311 rc=0 / SD mounted / LCD rc=0，两 boot 复现）——配置回归与接触不良两假说均证伪，根因 = 板态域（I2C0 总线锁死 + SD 旧卡态）。**四项事实纠偏**：① flash 真硅 = boya 16MB（bootloader+JEDEC 双证——89cee3e「gd 8MB」二次翻案，8MB 布局保守兼容续用）；② 教训 38 修正（uart0 打印路可用——CH343 三功能〔console+esptool+复位〕解耦成立）；③ 新教训 39：prov-write-test 兜底静默覆盖已烧 TLS prov（复烧即愈；真 prov 烧录改编排末步纪律）；④ USJ 宿主枚举闩死（hub 1-7.2，ROM 下载态亦不枚举——线缆域待 owner 重插）。板复原：prov 重烧 15 对 TLS（tls/…:9956）→ mTLS 注入 + CONNECTED loc=tls + 命令面回执全环通。证据 docs/evidence/periph_restore_console.txt；dev-env v2.28。 · 2026-10-17：**P1-2 TLS 全链真机点亮——CONNECTED loc=tls/192.168.2.91:9956 + 经 TLS 部署全判据（upload 2926B/真验签/安装闸 PENDING→timeout fail-closed/终态 STAGED+pending 清）**。根因修正：89cee3e「架构域 ECDSA」诊断**推翻**——板上独立判别机同证书同配置 x509 verify rc=0 全过；真因 = **双重内存耗尽**（mbedtls 堆 16384 握手不足 + 系统池不足 z_malloc -80——ECDSA 症状为其下游表象）。修正值：堆 31744/池 58368/VDB 1。console 路由固化 overlay（uart0 物理不通假停滞破案——dev-env 教训 38）。会话陈旧单向化登记（E2E 前重置纪律）。补丁重生成 329 行六文件可重放。回归：twister 16/16（113）/agent 204+2s/L5 7/7/ruff。**P1-2 单元 ✅ 收口**。外设物理域（es8311/SD/LCD 失联）待 owner 复查接触。
- v1.103 · 2026-10-17：**P1-2 续批（阻断修复实验）——宿主判别机完成 + 板启动事故阻断**：① 宿主判别机（native_sim + PSA_CRYPTO 显式 + 双模块，同证书同配置）**x509 链校验全过 rc=0** → 板侧 mbedtls PSA ECDSA 验签失败定性为架构/构建特定域（xtensa 编译或板全配置差异——非纯 Kconfig），「窄化 PSA 配置」单一路径预期不足，需板恢复后按判别机对照二分；② **/tmp 系统清洗事故**：ak_build 增量构建目录（板可引导的未知仓外配置态）丢失——全新构建的任何镜像（含 F3-1 源）PSRAM 后停滞（排除 probe/频率/镜像头/分区表/源回退五假说）；真硅 8MB 事实入仓（board conf/overlay）；③ 板双口全哑需 owner 物理断电重启；④ TLS 阻断修复路径裁决升级为**板恢复 + 判别机对照**双前置。
- v1.102 · 2026-10-16：**P1-2 TLS 实施批（DEC-63 五子项按建议）——大半交付 + 真机阻断登记**。交付：zenoh-pico-tls.patch 六文件（含五项上游缺口修复：socket union 别名覆写 _fd/DER+1 尾 NUL 解析/mbedtls 4.x API 迁移/MSG_NOSIGNAL/握手脚本 BIO 心跳）、prov 15 对 + glue mTLS 注入 + TS_NET_TLS 门控、工具入仓（flash_prov 三元组 + gen_tls_certs.sh）、zenohd TLS 9956 mTLS 实例（openssl 链验证 ✓）、回归全绿（twister 16/16〔113，+2〕/agent 204+2s/L5 7/7/ruff）。设计事实：zenohd 1.10.1（rustls）TLS1.3-only、x25519 key_share 必需（PSA_WANT_ECC_MONTGOMERY_255）、PKCS8 私钥形态。阻断（真机定位）：mbedtls 4.1.1 PSA ECDSA DER 验签拒收服务端签名（x509 链 0x08 + CertificateVerify -0x8D；openssl 同链全绿 = 板侧 PSA 层域；全链已点亮至 TLS1.3 EncryptedExtensions——证据 p1_tls_blocker_console.txt）。事故与复原：west flash 双板自动选口误刷（atk 镜像落 xiao）——双板复原 AK PASS/DB PASS（教训 37）；池重平 98304→69632。
- v1.101 · 2026-10-16：**F3 拒绝路真机判据收口——安装闸三路（timeout/确认/拒绝）全真机全绿，F3 ◐→✅**。BOOT 长按 ≥2s：AKP1 slot=1 挂起 → AKPR → AKP3 撤销（槽保留可重推）；无复位无 meta 切换，既有 ACTIVE（AK4 slot=0）不受影响 + get-app pending 已清复核。证据 af3_gate_reject_console.txt；驱动 /tmp/ak_f3_gate_e2e.py reject（F3G REJECT PASS）。待 owner 收窄为 Q-47 + tag review。
- v1.100 · 2026-10-16：**F3 确认路真机判据收口（owner 到场按键）**——BOOT 短按全链：deploy → activate -13 → AKP1（LCD 挂起呈现）→ AKPC 确认 → AKP2 meta 切换 → AK5 暖复位 → 自 flash 装载判据 `AK4 DONE` 命中 → AK6 ACTIVE；远程 get-app cbor2 解码 state=3 复核。证据 af3_gate_confirm_console.txt；驱动 /tmp/ak_f3_gate_e2e.py confirm（F3G CONFIRM PASS）。§11f F3 拒绝路仍待 owner 长按。
- v1.99 · 2026-10-16：**P1-3 交付（供电槽 natives）+ P1-4 裁剪清账（counter）**。① ts_power_set/get（ts-power 层全链——perm/预算/唯一写路径/readback——的 wasm 暴露；Agent 白名单/约定/面镜像）；② counter 零消费者实证裁剪（HLD §9 对照表 ✂️——R10 日落纪律首例）。twister 111 / agent 204+2s / ruff / repo 全绿。**清欠批终态：P1-1 ✅ P1-5 ✅ P1-3 ✅ P1-4 ✂️ P1-2 停门（Q-47 待裁）——批实质完成，TLS 随 Q-47 裁决开实施。**
- v1.98 · 2026-10-16：**P1-2 设计事实调研 + Q-47 呈递停门（门③）**——zenohd 1.10.1 TLS/mTLS 全支持（listen tls + enable_mtls）；zenoh-pico Zephyr 集成缺 TLS 特性行（需仓携带补丁——钉版 1.10.1 基）；EC P-256 证书全套 ~1.5KB 入 4KB prov 可容；五子项呈递（补丁路径/CA+mTLS/prov bstr 三元组/并存口/内存重平）待 owner 裁决。
- v1.97 · 2026-10-16：**P1-5 交付（S8 部署判据 miss 自动修复轮——HLD-agent §4 S8 收口，v0.2.2）**。post_deploy_check 判据面（健康也抓窗对拍；criteria_pass 三态区分未验证/未命中）+ CreationLoop.repair（上轮小结通道回喂真机证据；修复窗 2、计入循环预算）+ CLI --serial-port 部署闭环。agent 203+2s（+6）/ruff 绿。
- v1.96 · 2026-10-16：**P1-1 交付（ts_msg_send APP 间消息——HLD §3.4 原设计项收口）**。① 权限面：msg:send:<目标app_id> 名单形态（perm 层 msg_targets ≤4 + TS_PERM_OP_SEND——IR-11 fail-closed 登记的实现收口；LLD-ts-hal v0.2.5）；② 路由面：ts_appmgr_msg_send/recv（app_id 串身份寻址〔DEC-04 禁直接互访的唯一例外通道〕+ 权限先于目标解析〔不泄露运行面存在性〕+ FIFO 4×96B 满槽发送方背压 + TS_APP_EVT_MSG 取件通知；LLD-ts-appmgr v0.9 §5d）；③ natives ts_msg_send/recv + Agent 镜像（白名单 + 约定块 + 面镜像测试）。回归：twister 16/16〔111，+2〕/agent 197+2s〔+1〕/L5 7/7/ruff/repo 5 全绿。
- v1.95 · 2026-10-16：**F3-2/F3-3 交付（安装闸本地确认——DEC-62①③ 落地）**。① prov v2 lconf（12 对——store v0.5.2）；② appmgr 挂起态（activate/install 同闸〔EC4 无例外〕+ confirm/reject 仅固件本地路 + 60s fail-closed + pending_summary 单一事实源——appmgr v0.8 §5c）；③ net -13 回执 + 事件四态（net v0.4.3）；④ atkbench 手势模态 + LCD 呈现 + AKP 判据行族；⑤ Agent deploy pending 收尾 + FakeCube 语义。**timeout 路真机全链 PASS**；确认/拒绝 = owner 按键。回归：twister 16/16〔109，+1〕/agent 196+2s〔+1〕/L5 7/7/ruff/repo 5 全绿。
- v1.94 · 2026-10-16：**F3-1 交付（LCD bring-up——LVGL @ atkbench，AKU1 真机 PASS）**。① 呈现面：ui_lcd.c（LVGL 9.5 Zephyr glue——消息队列编排单线程纪律 + UI 线程 prio 12〔F6 教训〕+ 状态行 1Hz）+ 背光 = XL9555 P0-7 裸 I2C（pca9555 驱动维持禁用——K2 同源）。② 树内事实：ST7789V 走 esp32 lcd_cam 并口（MIPI-DBI 8080，板 DTS chosen 全挂——Kconfig 使能即可）；lcd_bl regulator 节点因引用禁用扩展器随禁。③ **四坑定案（教训 36）**：空 WiFi 凭据烤入 = net_mgmt -22（归因连环误判后 `strings` 一步定案——env.sh 变量名 TS_WIFI_*；守卫 = CMakeLists 空 SSID FATAL_ERROR）；LVGL glue 内存（LV_MEM 死配置 / LV_Z_MEM_POOL 16384 文本面下限 / HEAP_LIB_C 崩——上游域）；USJ×esptool×holder 定式（韧性 holder + 烧录前停 holder）；pkill 自匹配第三复发。④ 内存重平：系统池 122880→102400 + LVGL 专池 16KB + VDB 3%。全链真机：WiFi 关联 + AKU1 + zenoh CONNECTED + AK PASS + 存活稳定（证据 af31_lcd_console.txt）。
- v1.93 · 2026-10-16：**DEC-62 裁决批登记**——Q-46/F3 开工（①③④⑤按建议 + ②呈现面 owner 修订 = **LVGL**）；版本 tag 并入下版；gcov 缓办维持；P1 清欠批全批点向（执行序 P1-1→P1-5→P1-2→P1-3→P1-4）；**R10 HAL 扩展性与安全边界留档**（docs/research/R10-hal-scalability.md——Zephyr 暴露八问题否决/安全边界 O(1)/长尾解法 A 特权驱动组件 + B 策略数据；HAL 扩展门③在案依据）。§11f F3 →呈递 改 ◐ 开工；§11g B 表裁毕清空。
- v1.92 · 2026-10-16：**§11g C 表陈旧项清理**——「P4 摄像头帧证据」行删除：该行派生自 board-p4-01.md §7（2026-10-10 时点），次日 V2-1 即 DA PASS 收口（owner 排线修复已生效 + #121774 workaround + 发送层根治），v1.90 派生时误带入，如实更正。
- v1.91 · 2026-10-16：**F1/F2 物理判据收口（owner 到家按键）**——BOOT 手势三动作真机判据全命中：短按 ×2 = `AKL →LOCAL`/`→REMOTE` rc=0（CG3 席位切换真机闭环）+ 长按 ≥2s = `AKF1`→`AKF2 force rc=0`→`AKC 本地清除 rc=0`（estop 本地路闭环——远程门 need=local-clear 先期已实证）；全程 net=1 板存活；证据 docs/evidence/af12_boot_console.txt。§11f F1/F2 ◐→✅（全批仅 F3 呈递/G3 gcov 顺延两项非 ✅）；§11g B 表删「F1/F2 物理判据」行。
- v1.90 · 2026-10-16：**文档对齐实现批（owner 指令：更新文档/检查代码/列后续计划）**——HLD-firmware v0.3（§3.3/§3.4/§3.5/§7 现状注记 + **§9 设计-实现对照表**〔设计项逐项 ✅/◐/❌ + 登记出处〕）；HLD-agent v0.2.1（AG1-8 完成态 + D1/D3 + S8 半步注记）；README demo 表补 §11f 六项真机判据；names.md 补 Q-44/Q-46/DEC-61 索引 + 本批标识符登记（TS_APP_PSRAM_LOAD_BUF/VERIFY_BUF、post_deploy_check、capture_window、TESSERA_LNO_REGISTRY、D-AK4、AK7-AK9/AKF/AKC/AKL）；**§11g 后续开发计划定稿**（A 清欠批 P1-1…P1-5 / B 待 owner 四项 / C 环境挂起三项 / D Agent 候选五项随点向 / E 长期方向）。代码核查：twister 16/16（108）/agent 195+2s/repo 5/L5 7/7/ruff/sync 全绿 + 模块零 TODO + [q] 观测面注释按 F5 定案收口。
- v1.89 · 2026-10-16：**K6 交付（多真机 LN E2E AK6 LN PASS）**——双 cube（dbn/dbc @ xiao + akn/akc @ atk）LN 组全链：ln_create → ln_deploy 扇出（同包双板 confirmed）→ ln_status 聚合（双 ACTIVE + degraded_members 空）；xiao deploybench 以当前模块重刷（F1/F5 修复平移 + 凭据 cmake 重注入——prov 随重刷重建教训）；atk 侧 ESP_SPIRAM_HEAP_SIZE 1MB→4MB（SMH 外部区三笔分配 512K+256K+420K 超 1MB 实证）。
- v1.88 · 2026-10-16：**K4+K5 交付（net+SD 资源推送 E2E + large 档板级全链）**——① SD 上板一次通（SPI2 引脚表权威 + sdhc-spi-slot + AK7 挂载行）；② K4 AK4 RES PASS（CG5-B 资源推送真机闭环：needs.resources 白名单 + fs-commit sha256 读回 + APP 消费端字节命中）；③ K5 large 全链（206KB wasm/412KB 包编译-验签-安装-激活-PSRAM 装载-512KB 池实例化-运行-消费；caps 自报 [small,large]/1024KB 槽池）；④ 三处大包边界缺陷根治（cbor put_bool 0xE1→0xF5 + read_head 4B 长度 + Sig_structure 0x5A 4B 头——F5 同族）；⑤ 新面 TS_APP_PSRAM_LOAD_BUF/VERIFY_BUF（HLD §4.6 沙箱域纪律）；⑥ **F6 根治**：200 分块流 APPMGR WDT 楔死（APP 线程卡 printk——日志面×flash 争用，F1 家族变体待专项）。D-AK4 demo 入仓。
- v1.87 · 2026-10-16：**K3 交付（信任链真机 E2E AK3 TRUST PASS）+ 四发现定案**——F2 平反（无 zenoh-python 竞态：昨晚空回执 = 板掉线〔DHCP 间歇 F4 + F1 楔死〕+ 夜间探针 key 缺 tessera/ 前缀自坑）；F1 根因定案（失败提交循环 → 异常审计 flash 下沉风暴反噬 net_wq 喂狗 → NET WDT 循环——擦 APP 对照实证）双修正（锁外持久化 + 1Hz 节流）；F5 回执编码双缺陷（trust-get 漏 "keys" 键 + wrap_reply 空 data 零字节值）根治；F4 DHCP 间歇（atkbench 静态回退）；ZenohService scouting/gossip 关断加固 + zenohd 隔离模式（--no-multicast-scouting）环境纪律。回归 twister/agent/ruff 随批复验。
- v1.86 · 2026-10-16：**K2 补丁 + K3 夜间收兵**——SPK_EN 极性修正（NL 低有效）+ 板默认静音（ATKBENCH_AUDIO_PLAY 门控）；K3 驱动被 F1（zenoh-pico 查询高压死锁→WDT——K6 风险项）/F2（工具链空回执竞态）阻塞，三发现登记；deploy._cmd 空载荷重试加固入册。
- v1.85 · 2026-10-16：**K1+K2 交付（新板 bring-up + ES8311 音频）**——K1 atkbench（16M AMP 布局分区 carve + WAMR XTENSA 映射 + 部署链 AK PASS——第二 cube 就位）；K2 ES8311 全 codec（输入输出双面 + ts_av_write 新 native + 六坑定案 + 真机 AK AUDIO PASS）；§11f 批计划 + Q-44/DEC-61 登记。回归 twister 16/16（108）/agent 184+2s/L5 7/7 全绿。下一单元：K3 信任链真机 E2E。
- v1.84 · 2026-10-15：**全项目自检交付（owner 指令）**——SC-05…SC-19 十五项发现全部处置（文档一致性 25/25/README 滞后/names.md 登记册回填/本批一处静默 no-op 补落）；规范电池全过；回归定格全绿 + 间歇观察与既有缺口如实登记。报告 design/final-selfcheck-v0.8.0.md。**原定开发计划（§11e 三版本批 25/25 单元）全部完成。**
- v1.83 · 2026-10-15：**V0.8.0 收口（EC5 + tag fw-v0.8.0）——生态批 EC1-5 全批完毕；§11e 三版本批 25/25 单元全部完成**（R 4 + AG 8 + CG 8 + EC 5）。回归定格：twister 16/16（107）/L5 7/7/repo 2/agent 183+2s/ruff/sync 显式退出码全绿。真机信任表面随板级批（存量板零重刷 = V0.7 逐字节等价）。
- v1.82 · 2026-10-15：**EC4 收口（侧载通道）**——侧载纪律定稿（唯一写路径 = stage 链）+ L5 检查 7（slot 收口白名单机械实证 + 负样本自证；testing.md §3 补全 7 项——顺带修 M10 漏登漂移）；SD/USB 本体按设备形态按需。下一单元：EC5 收口 tag fw-v0.8.0。
- v1.81 · 2026-10-15：**EC3 交付（安装期权限确认）**——无头路实现（manifest_summary + install_permission_brief 注入 deploy_push_app/app_deploy/ln_deploy 三点 strict 审批 reason；坏包审批前拦截）；本地确认路 LLD 定稿（同一数据面，接线随设备形态批）；agent 183+2s/ruff 全绿。下一单元：EC4 侧载通道。
- v1.80 · 2026-10-15：**EC2 交付（信任根表实现）**——ts_trust.c 持久化（8KB 双副本乒乓〔4KB→8KB 擦除块对齐实施修正〕）+ verify_slot NULL=有效集迭代（pk1 转正；生产回滚 NULL 恒拒存量缺陷根治）+ sys/trust-update·trust-get + TS_EVT_TRUST_UPDATED + Agent trust_get/trust_update；夹具 gen_trust_fixtures.py 入仓；twister 16/16（107，+3）/agent 181+2s/L5/ruff 全绿。下一单元：EC3 安装期权限确认。
- v1.79 · 2026-10-15：**V0.8.0 生态批开工 + EC1 交付（信任链 LLD 设计定稿）**——owner 指令「按开发计划继续直至完成全部原定计划 + 完成后自检」；Q-43 五子项呈递（门③）→ DEC-60 按建议值登记（owner 泛指令先例 DEC-59 同型）：信任表 TUF root 同型全量替换（无 revoked 列表）/有效集 = 工厂根〔pk0+pk1，pk1 转正〕∪ 信任表/ts_trust 4KB 双副本乒乓分区（TS_STORE_TRUST 默认 n）/sys/trust-update·trust-get + TS_EVT_TRUST_UPDATED/verify_slot NULL = 有效集迭代（生产回滚 NULL 恒拒存量缺陷定案）。LLD-ts-store v0.5/LLD-ts-appmgr v0.7/LLD-ts-net v0.4/LLD-A06 v0.3。下一单元：EC2 实现。
- v1.78 · 2026-10-14：**CG5-B 交付（V0.7.x 补批）**——随包资源白名单授权模型定案 + sys/fs-begin/chunk/commit（sha256 读回 fail-closed）+ Agent push_resources；twister 16/16（104）/agent 179+2s；真机 net+SD E2E 随板级批。
- v1.77 · 2026-10-14：**V0.7.0 收口（CG7 + tag fw-v0.7.0）**——术语清扫 11 处 + 全量复验（twister 16/16〔103〕）+ 真机 spot check（DEPLOY PASS：caps 自报/预检消费/测试根部署全链 + 存量 APP 跨固件复用 + v1 prov 兼容实证）。CG0-7 全批 ✅；余项：CG5-B（独立单元）/本地交互面（设备形态批）/板级 large 档（板级批）。
- v1.76 · 2026-10-14：**CG6 收口**——estop 清除实质面 CG1/CG2 已交付（核对无剩余）；LLD-ts-safety v0.3.3 §9a 已知限制节补齐（ISO 13850 偏离/本地通道硬件 deferred/仲裁信号源/stack_kb）。下一单元：CG7 术语清扫+复验+tag。
- v1.75 · 2026-10-14：**CG5-A 交付（能力发现）**——get-info caps 块 + push_app 装前预检（装前拒零上传）；CG5-B 资源推送留独立单元（fs 写授权模型设计面）。下一单元：CG5-B。
- v1.74 · 2026-10-14：**CG4 交付（资源档位——AG7 数值消费）**——固件 scan/match/双门/槽池断言 + Agent tier/needs 镜像（门+链接钉死 flags+三方一致同步）；夹具生成脚本入仓；twister 16/16（102）/agent 177+2s。下一单元：CG5 能力发现+资源打包。
- v1.73 · 2026-10-14：**CG3 交付（控制源仲裁机制——合同 11 落地）**——席位 ts_arb_owner + set_arb 零输出/TS_EVT_ARB_CHANGED + ts_src_t 来源标记与压制门控（commit_src 入口，APP 路径不经闸）+ 审计 src 维度 + 租约本地席位视词语义（held_by/acquire + local_active 装饰）+ 顺带修 ts_safety_test_reset 审计环归零（用例序敏感缺陷）。用例 +2。下一单元：CG4 资源档位。
- v1.72 · 2026-10-14：**V0.7.0 合同泛化批开工推进（CG0 ✅ DEC-58 / CG1 ✅ Q-42→DEC-59 / CG2 ✅）**——CG1 四 LLD 修订 + 合同 v2 正典落节 + Q-42 呈递（门③）；DEC-59 三项按建议值（prov v2/manifest v2 档位字段/门值 256KB）；CG2 部署模式实现（prov 双形态解码 + linkmon 模式守卫 + standalone boot 声明〔ACTIVE 驱动者缺口定案〕+ estop-clear 守卫 + flash_prov.py 分区头缺陷顺带修复）。回归：twister 16/16（99 用例，+4）。下一单元：CG3 控制源仲裁。
- v1.71 · 2026-10-14：**V0.6.0 Agent 批收口（AG1-AG8 全 ✅，tag fw-v0.6.0）**——创作循环全栈（工作区/ws_* 循环/域验证器/终端门面/快照/双路径 app_develop/参数规则/run 子命令）+ D-AG7 真机 PASS（真 LLM 4 轮多文件工程收敛 + 无线部署 + 判据命中）+ large 档数值（CG4 输入）。回归定格：twister 16/16（95）/repo 2/agent 170+2s/ruff/sync。下一批：CG0 已裁（DEC-58）→ CG1 LLD 修订批开工。
- v1.70 · 2026-10-13：**通用域解放开发计划定稿（§11e 三版本批全单元）+ §12 质量优先条款入册**——DEC-57（Q-38…41 全 A + 质量指令）；深度设计两份随批：HLD-agent v0.2（A08 创作工作区域无关循环引擎 + A09 终端门面 = Frontend 第二实现 + AG1-8）、HLD-contract-v2（部署模式/控制源仲裁/资源档位/能力匹配 + 门④三段措辞呈递 + CG0-7）；生态批 EC1-5 方向锁定。下一步：CG0 门④措辞裁决（可与 AG1 并行）→ AG1 LLD 批开工。
- v1.69 · 2026-10-13：**§11d 通用域解放批登记（DEC-56 需求校准裁决）**——三批路线（R 批四路 research → Agent 批〔独立 CLI + 创作工作区，V0.6.0 候选〕→ 合同泛化批 → 生态批）+ FOUNDING_PROMPT v1.1 同批落文（使命重述 + DEC-01/02/12 修订，D1-D6 全部按建议裁定）。注：v1.68 后 §10/§11/§11b/§11c 各批补登未走修订日志，本条起恢复日志纪律。
- v1.68 · 2026-10-11：**V2-2 交付（V0.2.x 补批，DEC-52①）**——审计 flash 持久化全链（两页乒乓环 + 异常下沉 + boot 报告 + flash 读取 + auditbench 真机 AB PASS）；V0.2.0 四单元至此全部完成；待办 = 生产 app flash 面接入。
- v1.67 · 2026-10-11：**V2-3 交付 + V0.2.0 收口（tag fw-v0.2.0）**——sim APP 装载面（replay test_90 + embed 真机同包）+ simreal_diff 首基线（NV1 判据行 sim↔real 严格全等 7=7）；twister 15/15（78）/agent 113 全绿。版本终态：V2-1/V2-3/V2-4 交付 + V2-2 Q-31 停门维持（裁决后随 V0.2.x 补批）。
- v1.66 · 2026-10-11：V2-4 交付（spec 附属证据强化：提示词注入全部 patterns + repair_loop evidence 统计）；CI 漏步教训修正（NV-3 红定性改 sync_check 漏跑，两次同型事故附注留档）。V0.2.0 单元 3/4（余 V2-2 停门 + V2-3）。
- v1.65 · 2026-10-11：V2-1 交付（超预期）——**D-AV 全链打通 DA PASS**：采集自愈（#121774 workaround 真机实证）+ **发送层根治**（我方 zenoh glue use-after-overwrite——z_bytes 别名语义 × 环形槽覆盖；拷贝修复；上游"1KB 损坏"定性修正为双缺陷叠加）+ 64B 档零损坏完整帧重组；twister 15/15（77）/agent 109 全绿。V0.2.0 单元 1/4。
- v1.64 · 2026-10-11：owner 裁决——**V0.2.0 视频链解锁批开工**（§9 新排期：V2-1 D-AV 采集自愈 workaround + 256B 档验证→DA PASS 尝试 / V2-2 审计持久化〔Q-31 停门〕 / V2-3 sim APP 装载面 + 对拍首基线 / V2-4 spec 附属证据强化；目标 tag fw-v0.2.0）。
- v1.63 · 2026-10-11：**NV-6 交付 + V0.1.0 版本收口（tag fw-v0.1.0）**——健康哨兵全流程 round1 pass（spec 门→LLM→repair_loop→真机 HBS DONE 精确命中；NV-1/2/3 产物全链真机首消费）；gate 自举两修正（任意位置标记 + 主判据概念）；sim 首基线如实顺延（sim APP 装载面缺口登记）；NV-4 停门维持。六单元终态：5 交付 + 1 呈递停门。
- v1.62 · 2026-10-11：NV-3 交付（simreal_diff 语义对拍工具，首基线随 NV-6）；**Q-31 呈递**（审计持久化三选项停门待 owner）；NV-5 交付（根 README 门面）；V0.1.0 单元 3/5/6 落定，余 NV-4（停门）+ NV-6（验收）。
- v1.61 · 2026-10-11：NV-2 交付（spec 质量门：四节模板 + 判据机读派生 + app_develop 分级集成 + repair_loop 单一事实源联动 + skill 模板节）；V0.1.0 单元 2/6。
- v1.60 · 2026-10-11：NV-1 交付（tools_diag 诊断闭环 + 真机单迹 round1 pass + app_deploy 暖复位竞态根治 + manifest 伪影级联解包）；V0.1.0 单元 1/6 完成。
- v1.59 · 2026-10-11：owner 裁决版本方向——**V0.1.0 编程链路完整性批**（§9 新排期表 NV-1…NV-6：诊断闭环/spec 质量门/sim↔real 对拍/审计持久化〔Q-31 呈递门〕/README/真实需求全流程编程测试〔版本验收〕）；连续开发启动；收口目标 tag fw-v0.1.0。
- v1.58 · 2026-10-11：批 A 收口——owner 换 SD 卡后 dsdbench D-SD 全链一次过（DS PASS：挂载/安装/APP ACTIVE/回读 n=68/白名单拒绝物理证据/列目录）——**批 A 11/11 全绿定格**（S3 全 bench @4.5.0-rc1 真机基线完整恢复）；impl-review-03 R1 处置完成；dev-env 教训 33 转正（ts-prov 换烧必擦）。
- v1.57 · 2026-10-10：批 A 收尾专项——boardbench 全链 PASS（BB1 根因 = 9M 指令超 DEC-48③ 配额被健康链终止〔诊断探针实证〕；BUSY_ITERS 定 30000 + 注释定案；吞吐无 4.5 回归）；dsdbench 构建面通（/sense qualifier 正解——前判「4.5 迁移缺口」修正）+ SD 物理链路通——挂载写失败 = 介质层待 owner 查卡。
- v1.56 · 2026-10-10：批 A 续——otabench 全链 PASS（4.5 mcumgr img API 适配定案：test 键移除/confirm 变 bool/同版镜像设计缺陷）+ estopbench/periphbench/psrambench/metabench/wdtbench 五件 PASS（safety.h estop 声明存量缺陷修复；boardbench 堆迁 PSRAM）；遗留：boardbench BB1 evt 链待查 + dsdbench fatfs/SDMMC 4.5 适配；批 A 主体收口（9 绿/2 遗留）。
- v1.55 · 2026-10-10：批 A 首批（owner 裁决开工）：netbench（池 153600 调档）/linkdemo/deploybench（DB+D8 双证——B2 遗留单跑 PASS 补齐）三件 @4.5 真机 PASS + otabench 半程（上传链绿，swap 待查）；ts-prov 覆盖第三次（教训 33 候选）。
- v1.54 · 2026-10-10：issue #121774（esp32 video 停摆）提交登记；impl-review-03（会话 8 提交审查 + 风险清单 R1-R6 + 下一步候选批 A-D）呈 owner 讨论。
- v1.53 · 2026-10-10：D-AV 采集执行（帧已可采发——prov 覆盖根因修复）+ 新缺陷定案：4.5 下 zenoh-pico 板→路由 1KB 发送 100% 损坏（板侧 crc 正确/自环无损/尺寸相关——4.4 曾通 = 4.5 回归，upstream 域，与 #121767 关联观察）；256B 绕行档未获验证（dequeue 风暴 + 网络间歇）。
- v1.52 · 2026-10-10：D-AV @4.5 复测（sense 板确认 + avdemo @4.5 首构建绿〔池 94208〕+ 采集执行）——零帧定论与 DAV1 一致（硬件动作前不可收，非 4.5 回归）；网络间歇（DHCP 超时轮）观察登记。
- v1.51 · 2026-10-10：DEC-51（板卡集收缩 S3-only，P4/H7 搁置留档）+ persistbench S3 @4.5 真机复验 PASS（4.5 帧深致 verify 链 4096 栈挂死——修复 + 全 S3 bench 批量防御 8192；esptool 写回假象/WAMR 屏障两坑登记）；Zephyr esp_hosted 上游 issue 起草（提交中）。
- v1.50 · 2026-10-10：P4 无线面批——链路半程达成（C6 固件链 + esp_hosted RPC 全通真机证据：版本握手/wifi connect/associated 3/3）；NB 全链判据挂起 = Zephyr esp_hosted 驱动数据面上游缺陷（DHCP/TCP 不通，定案登记）；顺带修两构建面存量缺陷；回归 15/15（77）。
- v1.49 · 2026-10-10：P4 PSRAM 挂接批交付——p4psram 真机全链 PASS（SMH 0x48 域 + WAMR 256KB 堆入 PSRAM + APP 全链）；H7 真机暂停（owner 无 ST-LINK，已登记）；board-p4-01 §7 第二项收口。
- v1.48 · 2026-10-10：H7 移植批（构建级）交付（board-h7-01 v0.1）——owner 板裁决 mini_stm32h743（WeAct 核心板）即树内目标；h7bench 构建绿（FLASH 158KB/7.6%、sram0 68%）+ WAMR THUMBV7EM 映射（ARM 汇编 -mthumb 拒，教训入 §3）+ 五分区 128KB 扇区模式；回归 15/15（77）。真机判据待 owner 接板（ST-LINK + USART1）。
- v1.47 · 2026-10-10：P4 适配批交付（board-p4-01）——ESP32-P4-WIFI6-DEV-KIT 框架 bring-up 真机全链 PASS（p4bench：五分区 @0x7E0000/console=uart0/main 栈 8192/WAMR RISCV32）；SDK riscv64 单工具链补装；存量缺陷两族修复（六 bench 兼容串 + persistbench v1 包）；回归全绿（twister 15/15〔77〕+ pytest + persistbench S3 构建）。J 单元收口。
- v1.46 · 2026-10-10：DEC-50 裁决（rc1 直接采用 + P4=WIFI6-DEV-KIT）→ 升级批交付：v4.5.0-rc1 全回归绿 + inputdemo 真机复验核心判据绿；P4 适配批下会话开。
- v1.45 · 2026-10-10：D-AV 帧证据跨复位累计尝试——零帧交付（摄像头当晚彻底不出帧；方法〔generation 键累计〕已备）；Q-30 状态：v4.5.0-rc1 已 tag、正式版未发，建议 A 时点临近。
- v1.44 · 2026-10-10：DAV1 交付——根因 = 上游 esp32 video 驱动内 SCCB I2C 轮询忙等（APP 自旋于 native；avq/zenoh 全链排除〔冻结先于任何发布〕）；防御链实证；诊断探针入仓；D-AV PASS 判据条件 = 摄像头硬件稳定度（owner 排线/抗扰）。
- v1.42 · 2026-10-10：G2 完整收口（owner 开防火墙后触发）——四层排障（防火墙否定/WSL UDP 中继/客户端双字节/smp_udp pre-IP）+ OTA 全链 PASS；单元 G 全绿；Q-30 仍门⑤停门。
- v1.41 · 2026-10-09：B2 批（查询面半）——停滞根因 = agent 侧（locator/Reply API）双缺陷修复 + rollback_count 随载恢复 + d8_client 加固；D8 差单跑 PASS 行（环境窗口）；DAV1 留独立会话。
- v1.40 · 2026-10-09：单元 J（评估半）——升级评估交付 + Q-30 呈递停门（门⑤）：建议 4.5 发布后即升（P4 解锁）；P4 适配与硅版本裁决点附呈。
- v1.39 · 2026-10-09：单元 I（MD2）——D9 全链 PASS（sim+真机+合同 3）；D8 部分交付（链路全证 + deploy.py v2 对拍修复 + 内存重平；查询面停滞 = 新观察项 B2 邻接）；教训 29（LEDC 0%/S3 位序）。
- v1.38 · 2026-10-09：单元 H（G4/G5）交付——G4 单活跃语义收口（激活即停 + 隔离拒载 + 标记持久化）；G5 模拟深度（输入文件实装 + 脚本会话 + ch 命名空间，scenario schema 零变更）；twister 77 用例全绿；WAMR 怪癖第三型登记（教训 28）。顺带登记：boardbench 板级构建 dram0 溢出 88KB @HEAD（先于本单元，栈增长族累积——复用需先内存再平）。
- v1.37 · 2026-10-09：G2 部分交付——MCUmgr OTA 构建链与 MCUboot 引导全链打通（sysbuild + imgtool + 双 slot + SMP UDP 服务器 + 真机 1.0.0 自报）；OTA 上传待 owner 开 Hyper-V 防火墙（WSL2 mirrored 入站 UDP 阻挡）；串口 SMP 在 S3 USB-JTAG 上不可用（平台限制登记）。
- v1.36 · 2026-10-08：G1 交付——poweron_init 直写驱动（板级九遗留收口；sim 用例 + inputdemo 真机寄存器证据 299‰@300‰）；单元 G 拆分：G2 = MCUmgr OTA 独立单元（mcuboot/SMP UDP/imgtool 签名/真机全链）。
- v1.35 · 2026-10-08：输入面 G3 批（单元 F）交付——input monitor ADC 真值轮询（传输级变化语义，阈值归 APP）+ INPUT_CHANGED→mailbox 路由 + estop 沿 prov 化 + IR2-06 根治（弃管升级替代 abort）+ ts_wdt_deactivate；D4/D6 demo 真机全链（真 LLM 一轮过 + 悬空拾噪真值 + clamp/落驱动实证）；twister 15/15（73 用例）。**impl-review-02 高 3 + 中 8 全部清零**。
- v1.34 · 2026-10-07：MD1.2c（单元 E）评估交付——PDM 缓办结论（上游面/实施路径/重开触发留档 docs/md12c-pdm-eval.md；D 阶梯无音频消费者）；**MD1.2 全子项收口**（唯 h 的 DA PASS 待 B2）。
- v1.33 · 2026-10-07：验签实施批（单元 D）交付——TSAP v2（flags+32B sha256 摘要）+ 固件真 ed25519（tweetnacl 内置，PSA 首查无 ed25519）+ TEST 语义收口（固定测试根）+ IR2-07 回滚闭环（目标槽验签/暖复位/meta 双损如实）；板级"生产 prov 通道"消账（flash_prov.py esptool 直写）；三过程教训（m 别名/bstr 头/栈深 8192）；twister 15/15（70 用例）；真机 DS PASS 复验。**IR2-02 消账——impl-review-02 高风险三项全部清零**。
- v1.32 · 2026-10-07：MD1.2h（单元 B）**部分交付**——真机链路 90%（真 LLM/真帧捕获/分片发布）；**DAV1**（APP 线程冻结缺陷，3/3 复现——看门狗链按设计收口）与 **DAV2**（上游 esp32 DVP 无 JPEG 变长帧支持——demo 走 RGB565 保底）登记；新增 **B2 专项批**（DAV1 调试 + D-AV 全链判据补全）；avdemo 载体与 agent/demos/D-AV/ 入仓。
- v1.31 · 2026-10-07：MD1.2g（单元 A）交付——ts-av + ts_net_publish 能力面（DEC-47③⑥：av.c 采集/发布读类面 + avq 分片通道〔DEC-47② 值经 Kconfig〕+ av:read 权限类 + manifest av_* 三方同步 + test_06/test_12）；并入复检发现②（fs_paths 对齐）与④（回归脚本 WAMR 加固）；LLD-ts-hal v0.2.3 / LLD-ts-net v0.3.8 / LLD-ts-appmgr v0.5.3 / HLD §4.6 av 面增补；twister 15/15（68 用例）。

- v1.30 · 2026-10-07：**owner 指令重构排期**——硬件阶段三排除出开发范围（板级固件面保留）；剩余全量单元重排 A…J（A MD1.2g → B MD1.2h → C Q-29 呈递〔门③〕→ D 验签实施〔并入 IR2-07〕→ E PDM 评估 → F 输入面 G3〔并入 IR2-06/estop 沿〕→ G 板级余项〔poweron/MCUmgr OTA〕→ H G4/G5 → I MD2 → J Zephyr 升级+P4〔门⑤〕）；连续开发授权 + 每单元后汇报总/阶段进度。复检发现落点：②fs_paths 长度对齐→单元 A；①IR2-06/07 排期缺口→D/F；③ts_fs 语义边缘→impl-review-02 §8 附记；④本地回归脚本 WAMR 预处理→仓外工具。

- v1.29 · 2026-10-07：MD1.2f——D-SD demo 真机全链 PASS（真 LLM ts-fs APP；宿主独立复核双证据；真机首验根治 fs_paths 绑定形态缺陷；提示词/校验器/解包三处 fs 面同步）。

- v1.28 · 2026-10-07：MD1.2e——ts-fs 能力面交付（DEC-47④⑤：四 natives + fs 类 + fs_paths 白名单三方同步；twister 15/15〔66 用例〕）。
- v1.27 · 2026-10-06：PC 读面加固批（排期表单元 3：IR2-03 根治——include 禁令/读面白名单/max_bytes 钳制/key 段白名单/进程组击杀与取消杀组/out_dir 互斥；并入 IR2-04 L5 裸 pwm_set 正则；agent pytest 74+2s）。
- v1.26 · 2026-10-06：DEC-48（Q-28 裁决全按建议值）+ **看门狗实施批交付**（排期表单元 1+2 完成：四层防线全接线——三源喂狗/WAMR 指令配额/task_wdt 通道+硬件回退/noinit 留痕+复位闭环；真机 wdtbench 三整循环自证；并入 IR2-05/08；twister 15/15 全绿）——**IR2-01 高风险根治**。
- v1.25 · 2026-10-06：**DEC-47（Q-27 裁决：六子项全部按建议值——专用帧分片通道/1KB+4ms+重试+JPEG/ts_av_capture/ts_fs×4/fs_paths 白名单/含 ts_net_publish 新 native；上游 issue 暂不提）** + 排期表建立（§7：看门狗呈递 Q-28 → 实施 → PC 加固 → MD1.2e-h → 验签呈递 Q-29 → 实施 → MD1.2c → 后续候选）。
- v1.24 · 2026-10-06：impl-review-02（全库风险审查 3 高/8 中/IR2-xx 登记，处置排期待 owner）+ MD1.2d 呈递批（avbench 传输 spike 真机 PASS：≤1KB chunk + 4ms 打拍 + 分片重试零错误、1KB 档 172KB/s、PSRAM 视频池实证；**Q-27 六子项呈递停门**——natives/权限类/分片通道设计待裁）。
- v1.23 · 2026-10-05：MD1.2b——摄像头 bring-up PASS（CB PASS：官方池路径 + Kconfig 门槛实测；外部静态缓冲路径不可用留观察项）。
- v1.22 · 2026-10-05：DEC-46（Q-26 裁决：硬件即板载 Sense 版）+ MD1.2a（SD bring-up PASS：官方 Sense 板变体 DT 全就绪 + sdbench 载体；支持面结论：摄像头 ✓/SD ✓/PDM ✗）。
- v1.21 · 2026-10-05：MD1.1b——P1 根治（meta 读共享缓冲）+ 五 demo 全 PASS（MD1.1 完成）；Q-26 呈递（音视频/SD demo：硬件 + natives 权限类扩展）。
- v1.20 · 2026-10-05：MD1.1 部分交付（D1/D2/D5 PASS + 基础设施三知识 + P1 缺陷登记→MD1.1b 专项；docs/demos-01.md）。
- v1.19 · 2026-10-04：G1 交付（DEC-45 方案 A：app_compile + source_c 链内编译；Agent CLI 可靠性调研 R1-R8 落地 docs/agent-codegen-reliability-01.md；SMOKE3 双轮贯通）——**MD0 关闭，MD1 解锁**。
- v1.18 · 2026-10-04：MD0-1 真实 LLM 冒烟交付（owner 提供 minimax API；SMOKE1/2 双 PASS；G2 关闭；app_develop 三缺陷修复：max_tokens/config 路径/manifest 反馈回路）。
- v1.17 · 2026-10-02：owner 计划调整——H7 放弃 / P4 恢复（前置 Zephyr 升级，4.5+ 才有 esp32p4）/ 新增 MD demo 批（MD0-2，阶梯 D1-D9 见 docs/agent-demo-readiness-01.md；review 结论 = 真实 LLM 从未实测 + app_develop 的 wasm 边界为 demo 最大缺口 G1）。
- v1.16 · 2026-10-02：板级十交付（Agent→真机部署 E2E 闭环）；P4 移植暂缓登记（owner 指令）；板级十一候选清单更新。
- v1.15 · 2026-10-02：板级五~九收口补账（板级行停更于板级二态；五~八此前仅在 AGENTS/decisions 登记现并入计划）——五 flash 持久化 / 六 PSRAM 256KB / 七 WiFi 重连自愈 / 八 estop 硬件链路 / 九 PWM/ADC 真后端（本批交付）；§5 owner 待办清空（历史两项已落定）；板级十候选 = prov 烧录通道、Agent→真机 E2E、poweron 落驱动。
- v1.14 · 2026-09-27：板级四交付——WiFi+zenoh 命令往返实测（docs/netbench-01.md：L1 全路径 p50≈12ms/p95≈29ms，省电关闭 5.5×；L3 五验证点环境重建后复跑 PASS）；上游 esp32s3 WiFi 打通（blobs+overlay+省电关）。

- v1.13 · 2026-09-27：DEC-44（Q-24 → A：native_sim 多核为准，不采购；S3 SMP 观察）+ 板级三交付——真机 IO 延迟实测（board-bench-01 §1.5：裸 204ns / 框架 5.75µs / wasm 全路径 10.6µs；判定不过高）+ 最小真 GPIO 后端（CONFIG_TS_DRV_GPIO + zephyr,user 绑定）。

- v1.0 · 2026-09-22：初版（DEC-39 授权；双轨统一；MA0 同批开工）。
- v1.1 · 2026-09-22：M1 状态更新（本地全绿：twister 4/4 配置 12 用例 + L5 5/5 + pytest；L4 雏形接口随 M1 定稿 = 编译期内嵌场景 + stdout JSONL + 退出码）。
- v1.3 · 2026-09-25：MA3 行更新（MA3.1 部署链 E2E 全绿；MA3.2 余项 = A07 skills/DomainPack/app_develop/app_deploy）。
- v1.10 · 2026-09-26：M2b.2 收尾单元交付（boot 步骤 8 slot 装载 + 默认翻转 + E2E 真夹具 wasm；twister 14/14〔58 用例〕）；板级行固化运行效率 DoD 六项（owner 指令多检查架构运行效率）。
- v1.11 · 2026-09-26：板级 bring-up 达成（环境官方重建〔根因：Windows PATH interop 劫持 SDK 发现链，已 wsl.conf 除根〕+ SDK 1.0.1 官方安装 + 交叉构建/烧录/console 冒烟绿 + 足迹第一组数据）；板级待办与效率 DoD 六项顺延下一单元；ESP32 工具链勘误（需 Zephyr SDK，dev-env 教训 14）。
- v1.12 · 2026-09-26：板级二交付——效率 DoD 真机实测完成（docs/board-bench-01.md：吞吐 1043ns/iter、往返 ~3.5µs、写路径 9.7µs、mailbox p50 28µs、足迹对照、⑥单核降级〔ESP32-S3 无 SMP，Q-24 呈递〕）；WAMR xtensa 陷出修复；板级三待办固化（flash 后端/estop overlay/PSRAM/真驱动）。
- v1.9 · 2026-09-26：接线批第二单元（APP 运行时宿主 + natives + framework.app，twister 14/14〔57 用例〕）；M2b.2 余 = 收尾单元（boot slot 装载/默认翻转/E2E wasm 化）。
- v1.8 · 2026-09-26：DEC-43 实现批（锁收口 + framework.conc，twister 13/13〔54 用例〕）；板级行更新（xiao_esp32s3 定板 + espressif 工具链就绪——ESP32 不需要 Zephyr SDK）。
- v1.7 · 2026-09-26：M2b 行更新——M2b.2a 环境批交付（WAMR-2.4.5 接入 + framework.wamr 冒烟，twister 11/11〔47 用例〕）；接线批前置 = Q-23（宿主线程模型/并发收口，F-7 落点）。
- v1.6 · 2026-09-25：M2b 行补开工前置检查项（impl-review-01 F-7 并发防护复核——WAMR 多线程接入前裁定）；M3b 行回归口径更新为 46 用例（impl-review-01 修复批：twister 10/10〔46 用例〕）。
- v1.5 · 2026-09-25：M3b 行更新（里程碑退出；固件轨 M0…M3b 全绿，余 = M2b.2〔WAMR，需网络〕与板级移植〔前置 Zephyr SDK〕）。
- v1.4 · 2026-09-25：MA3 里程碑退出（MA3.2 交付：skills/DomainPack/高层链；58 用例 + ruff 全绿；push_prov 例外登记）。
- v1.2 · 2026-09-23：M3a 行补 DEC-40/41/42 实现批次（信封 v2/租约/事件遥测信封/QoS/is_up；L3 五验证点；twister 35 用例全绿，提交 486427c）。
