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
| J | Zephyr 升级评估 + P4 ◐ | **评估已交付（2026-10-09，docs/zephyr-upgrade-eval-01.md）：4.4.0=当前 stable；唯一硬驱动 = P4（4.4 HAL 无 esp32p4，支持随 4.5）；zenoh 1.10.1 已最新零联动**——Q-30 呈递**停门中**（建议 A：4.5 发布后即升；附 P4 硅版本裁决点）；批准后 = 升级批（1-2 会话）+ P4 适配批（另 1-2 会话 + owner P4 实板） | 门⑤ **停门等 owner** |

（原则不变：依赖就绪先行的最小单元；任一单元 DoD 全绿才进下一个；门项到点即停等 owner〔C 门③、J 门⑤、E 视方案〕；观察项——zenoh-pico Zephyr 集成尺寸钩子上游 issue 暂不提〔DEC-47〕、native-build 偶发面、外部静态 video_buffer 根因、watch 同槽重推。复检发现③〔ts_fs 语义边缘〕见 impl-review-02 §8 附记——登记不动手。）

## 8. 执行纪律（不变）

- 规范套件（tag `std-v1`：testing/versioning/progress/coding）+ 军规十条 + 安全与确定性合同（AGENTS.md §6）。
- 里程碑退出 = review 门（呈递 DoD 对照）；工具面/公共 API/安全合同变更 = 各自 review 门。
- 进度记录规则按 `docs/std/progress.md`；本计划的状态列随里程碑更新。

## 修订记录
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
