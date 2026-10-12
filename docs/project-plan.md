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

## 12. 执行纪律（不变）

- 规范套件（tag `std-v1`：testing/versioning/progress/coding）+ 军规十条 + 安全与确定性合同（AGENTS.md §6）。
- 里程碑退出 = review 门（呈递 DoD 对照）；工具面/公共 API/安全合同变更 = 各自 review 门。
- 进度记录规则按 `docs/std/progress.md`；本计划的状态列随里程碑更新。

## 修订记录
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
