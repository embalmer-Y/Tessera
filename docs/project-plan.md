# docs/project-plan.md · Tessera 统一项目开发计划

> **版本**：v1.155 · 2026-10-24（v1.0 · 2026-09-22 · 依 owner 指令与 **DEC-39** 建立；历史版本行随归档）。
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
| **板级** | ESP32-S3 → ESP32-P4 → STM32H7 | **板级一~九完成（S3）**：一 bring-up/环境重建（二十）→ 二 效率 DoD 六项（board-bench）→ 三 真机 IO 延迟三层对照 5.75µs 安全层（DEC-44 + TS_DRV_GPIO）→ 四 WiFi+zenoh L1 p50≈12ms（netbench）→ 五 prov/APP flash 持久化（board-persist）→ 六 WAMR 堆 256KB 入 PSRAM（board-psram）→ 七 WiFi 双断链自愈 4.2/9.2s（board-reconnect）→ 八 estop 硬件链路 ≤20ms（board-estop）→ 九 PWM/ADC 真后端（board-periph：LEDC duty ±1‰ + 限幅截断 + 断链 fail-safe 落驱动修复 + ADC 轨到轨 0/3122mV）。**板级十完成（2026-10-02）**：Agent→真机完整部署 E2E 双轨首次闭环（board-deploy：发现→打包→租约→分块→事实对拍→激活→暖复位→APP 自 slot 运行→get-app 对拍，双轮复现；附 exports 命名漂移 + get_info 打回装载结果两修复）。**余项（板级十一候选）**：生产 prov 烧录通道（esptool 直写 / Agent push_prov）、注册期 poweron 值落驱动、input monitor 真输入驱动、MCUmgr 固件 OTA（DEC-07/23 已裁未实现）、Zephyr 升级评估（**P4 前置**：v4.4.0 无 esp32p4 支持，4.5 加入——升级走门 ⑤ 呈递）；**P4 适配恢复**（2026-10-02 owner 二次指令，动机 = APP 复杂性余量：双核 RISC-V HP@400MHz + 16MB flash + 8MB PSRAM）；**H7 适配放弃**（2026-10-02 owner 指令；评估报告 docs/h7-memory-assessment.md 存档）。**MD demo 批（功能完成后）**：**MD0 完成（2026-10-04）：真实 LLM 冒烟（G2）+ APP 代码生成链 G1（DEC-45 方案 A + 可靠性调研 R1-R8 落地，SMOKE3 双轮贯通"需求→编程→打包"）——MD1 demo 阶梯解锁**→ MD1 阶梯 D1-D7（**MD1.1 完成 2026-10-05：五 demo 全 PASS（P1 已根治——meta 双副本读共享缓冲 bug，MD1.1b）**；MD1.2 进行中（**a 完成 2026-10-05：SD bring-up 真机 PASS〔DEC-46 硬件即 Sense 板载〕**；**b 完成 2026-10-05：摄像头 bring-up PASS〔QQVGA ×4 帧 + 帧落 SD 闭环；官方池路径为 V1 唯一路径〕**；**d 呈递中 2026-10-06：avbench spike PASS + Q-27 六子项停门待裁**〔实测：chunk ≤1KB〔>2KB 碎片路径死〕/打拍 ≥4ms/分片重试必须/视频池 PSRAM〕；c=音频 PDM 扩展；D4/D6 输入类并入） → MD2 混合 D8/D9（demo 阶梯——原 readiness 档，2026-10-24 仓整理删除） | 板级报告族 docs/board-*.md；每单元 twister 全量+L5+CI 四 job 绿 |

## 3. 轨道 B · AI Agent（MA 系；DoD 详见 `design/HLD-agent.md` §7）

| 里程碑 | 范围 | 状态（2026-09-22） | 退出标准 |
|---|---|---|---|
| **MA0** | agent/ 骨架（包结构/config/CLI 桩/CI 接线）+ DR-18（versioning Python 钉版节）+ DR-19（dev-env agent venv 节） | **本批开工（DEC-39）** | 本地 pytest + ruff 绿；CI yaml 就绪（上线随远端，同 M0 惯例） |
| **MA1** | A00+A01+A02+A03：网关/编排/审批闸/审计 + fw_* 最小集 + sys_*/task_* | **本地全绿（2026-09-22）**——FastMCP 客户端实测（sys/task/审批流）+ fw_pytest 与 fw_build 句柄化实测；CI 随远端 | MCP 客户端实测：build 句柄化跑通 + 审批流实测 ✓ |
| **MA2** | A04 模拟器 + A05 TSAP 签名 | **本地全绿（2026-09-22）**——pytest 33+1(E2E 实证) 全绿：TSAP 往返+双实现互验+篡改矩阵；sim E2E 真实构建+双跑确定性绿 | 签名往返 + 双实现互验 + smoke 确定性比对绿 ✓ |
| **MA3** | A06 zenoh 部署 + A07 skills + 高层链 app_develop/app_deploy | **本地全绿并退出（2026-09-25，MA3.1+MA3.2）**：MA3.1 部署链（固件 sys/app-* gated + deploy_* 工具 + E2E spec→TSAP→部署仿真立方体）+ MA3.2（skills 4 项+loader+同步检查/DomainPack 平台域拆分+导入图测试/高层链 app_develop·app_deploy + A2A/ACP 接缝）；**例外登记**：push_prov 随维护模式语义后批（LLD-agent-deploy-net §6）；CI 上线随远端 | 端到端：spec → TSAP 包 → 部署到仿真立方体 ✓ |

## 4. 交叉依赖（双轨咬合点）

| Agent 侧 | 依赖固件侧 | 交付物对齐 |
|---|---|---|
| MA2 模拟器 | **M1** L4 重放框架雏形 | 输入注入/输出捕获协议（LLD-agent-sim-harness §2 接口约定，M1 设计时共同定稿） |
| MA2 TSAP | **M2a** TSAP 格式定稿 | manifest 字段镜像（LLD-agent-tsap-tools §2） |
| MA3 部署 | **M3a** ts-net | 发现/liveness key、sys 命令实现、APP 安装入口、维护模式语义（LLD-agent-deploy-net §6） |
| MA3 模拟深度 | **M3b** 外设桩 | 场景 channel_kind 扩展位 |
| 共同 watch | **Zenoh 2.0**（上游计划 2026 H2） | 三方（zenohd/eclipse-zenoh/zenoh-pico）联合升级 + 全量回归——M3a/MA3 前评估 |

## 5. owner 待办（阻塞项）

（当前无技术阻塞项；review/push 待办与候选池见 §7「待 owner / 候选池」——2026-10-24 v1.155 重构收敛于此；板卡使用注意事项见 dev-environment §5。）

## 6. 环境与基础设施事实源

- `docs/dev-environment.md`：WSL 目录规范（`~/project/{tessera,zephyrproject,logs}`）+ 固件 venv；**MA0 起增补 agent venv（`~/project/agent-venv`，DR-19）**。
- CI：`.github/workflows/ci.yml`（repo-checks → 固件构建/twister → **agent lint+pytest（MA0 接入）**）。

## 7. L 表 · V0.17.0 累积池「Agent 能力版」（2026-10-29 v1.161 重构；DEC-75 纪律）

> 定位 = DEC-75 后的 feature 累积面：逐单元交付、攒够 5-8 个 feature 收口 tag fw-v0.17.0；fix 类随修随发走 patch（fw-v0.16.x）。
> **版本主题（owner 2026-10-29 指令「下一版本的重心是提升 Agent 能力」）**：创作深度 × 判据闭环 × 经验复用 × 能力标尺——四维合力把 Agent 从「能走通全链」（V0.16.0 实证：真模型创作 → 双真板部署判据 PASS）推进到「自主交付质量可度量、可复用、可闭环」。
> 前序：V0.16.0 五单元（BV2 实战/仓整理/环境安装程序/LLM 探针/v4.5.0 平移）已逐字归档 `docs/history/plan-archive-2026-10.md`（收口待 tag fw-v0.16.0 随 owner 令）。

| 序 | 单元 | 内容 | 规模 | 备注 |
|---|------|------|------|------|
| AC-1 ✅ | **能力评估基准**（eval bench）——先立标尺 | `agent/eval/`：spec 任务谱（T1 单文件 log-only → T2 多文件工程 → T3 caps 真写入 → T4 threads 档〔ts_thread_*，M19 已裁已实施〕 → T5 needs.resources 资源外置〔AK4 协议面已实证〕）× headless 评分器（PACKAGED 与否/收敛轮数/compile_facts 合规/sim 判据过/包规范对拍）× CLI `agent-eval` 报告；模型可插拔（config.toml 模型串）。**deepseek-v4.1-flash 首基线报告随单元交付** | ~1.5 | 无标尺无「提升」可言——确定性合同（合同 9）的度量面；任务谱设计呈递 Q 随单元；真机判据段可选（板在网时） |
| AC-2 ✅ | **创作深度扩展**（richer APP shapes 真链创作） | creation loop（domain/app_chain.py + creation/）对 R7 重开上限的**创作侧消费**：resources 外置声明（ts-fs）/threads 档（CLANG_FLAGS_THREADS + ts_thread_* 白名单——固件面 M19 全就绪，创作循环从未真 LLM 产出过）/caps 真写入（gpio/pwm——HW-4 事实面注入）。三轨道各出真链 PACKAGED + eval 谱 T3/T4/T5 对位 | ~1.5 | R7 §1 四上限的协议/固件面全通（AK4/AK5/DT PASS），缺口只在创作侧；Q-39/DEC-57 已裁方向自然延伸，无新裁决面 |
| AC-3 ✅ | **判据自评价闭环**（criteria loop） | 把判据窗方法学（CONNECTED 切段/单调样本窗——ds41 驱动实证）从 tools/board 仓外驱动**升格为 Agent 工具面**：MCP `app_criteria_run`（判据定义 → 串口/zenoh 采集 → 机械判定）+ app_develop VERIFYING 阶段 sim 判据接线 + diag_classify 失败分类联动（NV-1 域延伸）——创作→部署→判据→修复全自动闭环 | ~1 | 「部署成功」的产品化定义；strict/confirm 审批类随单元呈递 Q；板不在网时 sim 段降级可用 |
| AC-4 | **经验复用**（pattern library） | 成功包样例库：PACKAGED 工作区索引（manifest/compile_facts/判据行摘要）+ 检索面（spec 相似度 × caps × 外设面）+ app_develop PLANNING 阶段参考样例注入——同类 APP 不再从零写；对接 LLD-agent-memory-planner §8 v2 方向 | ~1 | 记忆域从「分析」（memory_audit 只读）扩到「复用」；索引格式/注入预算呈递 Q 随单元 |
| AC-5 | **硬件事实感知深化**（HW-4 收口 + C0 评估到期） | ① P4 画像 [hardware] 引脚采集（板在 USB——机会窗口；S3 已入谱）② 创作链 pin 冲突检查（部署门前置——spec 引用引脚 × 画像事实对拍）③ **C0 全局化评估落结论**（DEC-74②「随 v4.5.0 平移批评估」——平移已完成，本单元给采纳/落选结论呈递） | ~1 | HW-4 source 纪律（R12）延伸；C0 结论为呈递件非默认实施 |

**债务随批（patch 类，不占 feature 计数）**：p4bench activate 暖复位语义（V0.14.0 RTS 助手场景固件侧根治）；zenoh 全通配查询单回执 quirk 调研（一五五观察项）；双板网络画像 cube 空值歧义收尾（p4-wifi6.toml zenoh.cube 回填核对）；aarch64 安装器首台 ARM 机实测回填（条件件——设备到位即行）；P4B app_evt 自检失配定性（固件 bench 面）。

**执行序建议**：AC-1（标尺）→ AC-2（深度）→ AC-3（闭环）→ AC-4（复用）→ AC-5（硬件）；债务随批穿插。

**版本验收建议（对齐 V0.1.0「真实需求全流程编程测试」先例）**：一个真实需求的**端到端 Agent 自主交付**（需求 → 澄清 → 创作〔含硬件引用〕→ sim 判据 → 部署 → 真机判据 PASS，全程 Agent 工具面驱动、owner 只做审批确认）+ **eval 基线对比**（AC-1 首基线 vs 收口基线：任务谱通过率/收敛轮数提升，机械可查）。

### 待 owner（当前）

- V0.16.0 收口：5 feature 全验证闭环（CI #207 绿 + 平移批 CI 绿），**建议收口 tag fw-v0.16.0**——随令打 tag。
- 本规划（v1.161）review：单元集/执行序/版本验收口径随点向（逐单元开工前仍有呈递 Q 门）。

### 候选池（随 owner 点向）

- R12 板卡选型 / R13 结构件（调研已交付 docs/research/，实施面随点向）。
- Q-37 threads 创作面已在 AC-2 消费（无新裁决）；C-4/C-5 仍待 owner（decisions.md 在案，不阻塞本版）。

### E. 长期方向（既有登记维持）

- 多域 DomainPack（PCB/结构件域 agent——CreationVerifier 第二实现；DEC-33 北极星）
- A2A/ACP 协议接入（缝保留，真实消费者出现再启）
- 生产化批（安全认证路径/量产烧录流水线——owner 点向后规划）
- LLM 多模型并行比对（eval bench 成熟后自然延伸——AC-1 面已留模型可插拔）


## 8. 执行纪律（原 §12；v1.70 增补质量优先条款）

- **质量优先（DEC-57，owner 2026-10-13 指令原文精神）**：**不允许最简实现**——各交付单元的设计与实现须考虑整体架构、后续可维护性与架构可扩展性；现方案不能很好满足目标时，**停批与 owner 确认讨论重新选择方案或技术**，不得静默绕行或降级实现。
- 版本节奏纪律（DEC-75，owner 2026-10-23）：**minor 版（0.X.0）须累积 ~5-8 个 feature 方可收口**；issue fix / 板级专项类只走 **patch（0.0.X）** 随修随发；存量版本号不回溯。
- 其余纪律不变：每单元后 twister + agent pytest + L5 回归（军规 10）；阶段门/军规十条（FOUNDING_PROMPT §2/§3）。

- 规范套件（tag `std-v1`：testing/versioning/progress/coding）+ 军规十条 + 安全与确定性合同（AGENTS.md §6）。
- 里程碑退出 = review 门（呈递 DoD 对照）；工具面/公共 API/安全合同变更 = 各自 review 门。
- 进度记录规则按 `docs/std/progress.md`；本计划的状态列随里程碑更新。


## 修订记录
- v1.164 · 2026-10-29：**AC-3 判据自评价闭环 ✅（owner「请你开启AC-3的开发」→ DEC-82）**：① **判据窗引擎** `domain/criteria.py`（纯函数：CONNECTED 切段取末段〔CH343 开埠复位脉动去伪——ds41 方法学升格〕+ present/monotonic 两规则 + render_evidence 修复链直喂文本）。② **创作 wasm PC 侧执行器** `domain/wasm_sim.py`（SimFn 预留缝的 AG6 时代实现落地——wasmtime==50.* 钉版；natives stub 按 module.imports 反射生成〔签名自适应〕；tick 循环带签名适配调用〔eval T1 实证模型产物 app_tick 无参——FIX-2 教训反向：宿主 argc 须匹配 param cells〕；**sim 适用门** threads>1/needs.resources = skip 注记不跑假 sim）。③ **接线三处 additive**：_app_develop_loop 恒注入 sim_runner / app_develop 增 sim_scenario 可选参（VERIFYING sim 判据——scenario=None 零变化）/ MCP `app_criteria_run`（confirm 类：串口被动采集 → 切段 → 机械判定；真机判据窗方法学正式升格工具面）。④ **eval --with-sim 实装**（AC-1 v1 占位补全）：T1/T2/T3 sim 定义（ticks+verdict_patterns+monotonic）；T4/T5 = None 真机域如实登记；sim 段失败 = PARTIAL 不否决整轮。⑤ **验证**：测试 +9（引擎/执行器现场编译 wasm 全链/skip 注记/MCP 面）——agent 387+2s 全绿 + ruff；**T1+sim 端到端 PASS**（真链 2 轮 PACKAGED + sim 判据段实跑 ticks=300 全过）。真机判据窗验收顺延（板已下线——板回位一条命令可验）。⑥ 过程随批修：执行器签名适配（无参 app_tick 崩→反射调用）+ sim 异常不否决整轮。V0.17.0 累积 3/5-8。
- v1.163 · 2026-10-29：**AC-2 创作深度扩展 ✅（owner「继续下一单元的开发」；AC-1 批 66d23e5 推送 + CI 绿同日）**：① **创作循环容错面三处**（模型侧退化不再崩链——终态语义/预算语义不变）：PLANNING 结构化输出重试超限 → 降级线性计划继续创作（证据留痕 plan_fallback）；implement 侧工具参数/输出重试耗尽 → 计失败轮转反馈下轮重试（implement_retry_exhausted，上轮失败摘要回喂）；容错面拓 OSError（DSML 泄漏族）。② **ws_write 路径入参校验**（MAX_PATH_LEN=256 + 拒换行——eval AC-2 轮 T2 实证 deepseek DSML 模板记号泄漏进 path（File name too long 打穿 OS 层）fail-closed 化）。③ **验证**：测试 +3（plan 降级/implement 失败轮/退化 path 拒绝）——agent 378+2s 全绿 + ruff；eval 实证：容错后死法从「崩整轮套件」（基线轮2 T2）缩为「单任务 FAIL」，T5 进入 IMPLEMENTING 且 manifest 校验反馈轮正常运转（容错设计预期行为）。④ **T5 定性（四轮四死法实证）**：resources 外置 = deepseek-v4.1-flash 稳定能力边界（ws_write 三连败 / PLANNING 输出超限 / 600s·900s 超时——轮内 manifest 校验反馈面 agent 侧已全部就位，收敛未达属模型能力域）；**换强模型复验 = agent-eval 即插即用面**（基准价值直接兑现）；T3 caps/T4 threads 创作侧真链收敛已由基线轮3 PASS 实证（三轨道缺口闭合 2/3，T5 残留 = 模型域观察项）。V0.17.0 累积 2/5-8。
- v1.162 · 2026-10-29：**AC-1 能力评估基准 ✅（V0.17.0 首单元；owner「同意Agent优化规划。请你开始实施」→ DEC-81；fw-v0.16.0 tag 同日随令打推）**：① `agent/eval/` 包（suite.py 任务谱 T1-T5 = 真实需求措辞 spec × 期望轮廓 / scorer.py headless 评分器〔converged/轮数/imports-exports-deterministic-size/caps-threads-tier-needs 对拍/package_on_disk，九维机械〕/ report.py JSON+markdown 双形态）+ CLI `agent-eval`（--tasks 子集/--timeout-per-task 600s/--with-sim v1 占位〔场景定义随 AC-3〕）；评分器 develop_fn 注入点 = 测试零网络；测试 +8 + ws_write 目录防御回归 +1。② **deepseek-v4.1-flash 首基线：PASS 4/5 通过率 0.8**（T1 1轮155.6s / T2 2轮 / T3 caps 3轮 / T4 threads 2轮 全过；T5 resources 外置 = **模型能力边界**：PLANNING 结构化输出重试超限——三轮三死法，AC-2 精确攻击点）；波动性数据入册（T1 三轮 3.7× 耗时差/同 spec 换轮即愈的 ws_write 空参数退化）；报告 docs/evidence/eval-baseline-deepseek-v4.1-flash-20261029.{md,json}。③ **eval 首跑即抓两缺陷随批修复**：创作链 ws_write 目录路径无防御（原子替换裸抛 IsADirectoryError 崩链→fail-closed 化）+ 评分器无兜底（UnexpectedModelBehavior 裸崩→任何死法给分套件继续）。④ 回归：agent 375+2s 全绿 + ruff。V0.17.0 累积 1/5-8。
- v1.161 · 2026-10-29：**V0.16.0 收口 review + V0.17.0「Agent 能力版」立项（owner「请你进行review，并规划下一版本的开发，下一版本的重心是提升Agent能力」）**。① **V0.16.0 review**：五单元 DoD 全对照（详见会话 review 报告）+ 回归面全绿（agent 366+2s / twister 17/17 / repo 11 / ruff / sync / CI 双绿）+ 债务清单五项带出处（真机重烧待凭据 / aarch64 安装器待首台 ARM 机 / p4bench 激活语义 / P4B app_evt 自检失配 / zenoh 全通配 quirk）——**建议收口 tag fw-v0.16.0**；L 表五行逐字归档 docs/history/plan-archive-2026-10.md。② **V0.17.0 累积池新立（AC-* 代号，names 查碰零碰撞）**：主题 = 创作深度 × 判据闭环 × 经验复用 × 能力标尺；单元 AC-1 能力评估基准（先立标尺，deepseek 首基线随单元）/ AC-2 创作深度扩展（R7 上限创作侧消费——resources/threads/caps 三轨道，固件面 M19+AK4/AK5 全就绪）/ AC-3 判据自评价闭环（判据窗方法学升格 Agent 工具面）/ AC-4 经验复用（pattern library——memory 域分析扩复用）/ AC-5 硬件事实感知深化（HW-4 P4 引脚 + C0 评估到期落结论）；债务随批五项 patch 类；执行序 AC-1→5；版本验收 = 真实需求端到端 Agent 自主交付 + eval 基线对比（对齐 V0.1.0 先例）。 grounded 素材：R6/R7 调研 + DEC-57 质量优先条款 + M19/Q-37 threads 已实施 + LLD-agent-memory-planner §8 / skills-platform DomainPack 预留。
- v1.160 · 2026-10-29：**Zephyr v4.5.0 正式版平移 ✅（owner「检查 v4.5.0 状态……已发布则切换」→ L 表第五单元；DEC-50 修订记录「正式 v4.5.0 发布后平移」兑现）**：① 上游 2026-10-28 发布（prerelease=False 实测核实）→ 工作区切换（zephyr checkout v4.5.0 @41d10b59730 + west update 模块对齐 + blobs 73 件 + requirements 刷新）；② **回归三绿**：twister 17/17 套件（115+2s）零回归 + **deploybench（BV2 EXTRA 形态 = 现行真机镜像形态）构建绿零调平**（787812B）+ atkbench **dram0 溢出 6716B 调平绿**（1299604B——rc1→final 全库静态面累积，bss 大头 mbedtls 31KB/tessera 18.8KB/lvgl 16.6KB 无单域暴涨）；③ 调平面：atkbench 板级 heap 58368→61440 + prj.conf 四键（mbedtls 专用堆 31744→24576〔现行 prov 明文形态对位释放，TLS 复验回抬〕/ PSA key slot 16→4 / net pkt 14→12 / net buf 36→24）——**heap 下限新知入册**：CONFIG_HEAP_MEM_POOL_ADD_SIZE_ESP_WIFI=51200 等 Σ=56384，heap 低于该和被 kernel/CMakeLists final_heap_size 顶住无效（三轮实证 4732B 恒定不动）；④ 钉版面六处同步（env_common.sh PIN / 守恒测试 / ci.yml ×3 / checklist §3 / README×2 / tools/env README）+ checklist v1.5 平移注记（**rc1 工作区不可反向 checkout**——模块已 final 锚定 SHA，混树 Kconfig abort）；⑤ 守恒测试 6/6 + rc1 基线对照构建因模块混树不可行（工作区一致性约束，如实登记）。V0.16.0 累积 5 feature（DEC-75 线 5-8 收口窗内）。证据：本会话 twister/构建输出；板级 conf 注记谱系。
- v1.159 · 2026-10-24：**deepseek-v4.1-flash 模型测试部署段补全 ✅ 双板全链 PASS（owner「两块板卡我已经接入该机器的USB，请你检查并继续刚刚的测试」；v1.158 挂起段收口）**：① 板态迁移——双板 prov 均为 ARM 时代陈旧路由（.101:9956|9957；ARM 机仍在线 ping 0.29ms = prov 指向即归属观察），zenohd 本机 9955+9957 起 + flash_prov 重烧（P4 @0x7e0000 p4-dev/cube-p4 / S3=atk 同板 dbn/dbc @0x7e0000 workorder 位——误烧 0x5f0000 一轮 = atk 残留布局假设，0x5f0000/0x170000 历史残留位解剖实录）→ 双板 CONNECTED .91:9957。② 签名面纪律实证：deploybench TEST 语义板验签 = fixtures/ts-test-root（临时钥必拒）→ ds41 包测试根重签 2758B（IR2-03 白名单：输入/输出均须在允许根）。③ S3 双跑全 PASS（11 分块/verify facts 对拍/activate/暖复位 10s ACTIVE/slot 0→1 乒乓/HB 57 样本单调 ×2）+ P4 三段式 PASS（push 全链 PASS → p4bench 无激活即暖复位语义 state 停 STAGED → 外部复位完成转正〔RTS 助手场景再现〕→ 判据窗 v2 58 样本 10..580 单调）。④ wasm 架构中立实证：同包跨 xtensa/RV32 双板运行。⑤ 观察项五条：ARM 机 .101 仍在线 / CH343 开埠复位脉动双板实证 + 复位窗 SHA-256 瞬态两例（后续 boot 全净）/ p4bench activate 不暖复位 / P4B FAIL app_evt = bench 自检对第三方 app 固有失配（health_fails=0）/ deploybench caps=null quirk 再现。证据 agent-test-ds41-flash-20261024.txt（部署段全文）。
- v1.158 · 2026-10-24：**五笔随令推送（CI #207 全绿）+ deepseek-v4.1-flash 模型真实链路测试（fix 类补笔）**：app_develop 双运行均 PACKAGED（单轮 126.4s + 四轮含修复链）；随批修复 anthropic 传递依赖钉版（==1.3.*——最新版 Beta 类型崩/＜1.3 导入面缺，新装 venv 即踩）+ llm_probe 建议面增 sdk_base_url（anthropic SDK 自拼 /v1/messages——base 含 /v1 须剥尾，实测 /api/v1→404、/api→200）；板上部署段待板上线（双路由地址发现为空）。证据 agent-test-ds41-flash-20261024.txt。
- v1.157 · 2026-10-24：**LLM 端点探针 ✅（owner 指令 → DEC-80；L 表第四单元）**：domain/llm_probe.py 五面检测（URL 合法性/连通性分类/协议检测/模型列表/KEY 有效性+模型可用性——鉴权面合一判定）+ 配置建议；MCP llm_check（confirm 类；key 只经 key_env 环境变量名——值不入参/审计）+ CLI llm-check；实测回填三事实（/models 可不鉴权、max_tokens≥16、reasoning 小预算文本空≠不可用）；tools/env 85 步联动自动校验；测试 +10（MockTransport 注入）——agent 366+2s 全绿。V0.16.0 累积：BV2 + 仓整理 + 安装程序 + 探针 = 4 feature（DEC-75 线 ~5-8 渐近）。
- v1.156 · 2026-10-24：**环境自动部署脚本 ✅（owner 指令 → DEC-79；L 表第三单元）**：tools/env/ 面向用户安装套件（install.sh/--dev/steps×10/verify_env.sh/README——sudo 交互索密 + --proxy 代理支持 + 凭据交互或 --config 导入 600 仓外）；本机（x86_64/Ubuntu 26.04）开发环境全链恢复实测：twister 17/17 套件 115+2s（framework.net 并行 configure_file 竞态单跑 17/17 过——v1.148 同型环境域）+ agent 356+2s 全绿（clang-18 apt 路线 = 18.1.8 精确对齐 CI；23 环境域失败全转正）+ repo 6+5 + sync 全绿。顺带修复仓内潜伏缺陷：zenoh-pico-tls.patch hunk 计数头（19→12）与 primitives.h 段缺 --- 头行（新机必踩——git apply 全拒）+ zenoh-pico 剥宏清单 12→13（AUTO_RECONNECT，R5-V 起补丁基线——checklist §3 勘误 v1.4）；固件 venv 钉 cmake 3.31.6（发行版 cmake 4.x 与 Zephyr 4.5 兼容风险免疫）；守恒测试 firmware/tests/pytest/test_env_installer.py +6。
- v1.155 · 2026-10-24：**全仓整理与命名规范化（owner 指令 → DEC-78；L 表第二单元 ✅）**：① 删除 14 件（9 一次性评审/自检档合并 docs/history/review-archive.md——IR/IR2/DR/SC 发现编号溯源链保留；migration-x86〔checklist 为唯一重建总单〕/agent-llm-smoke-01/agent-demo-readiness-01〔结论已消费〕/agent/decisions.md 孤儿/legacy+hardware 空目录）；② 命名规范化（LLD-A00…A17+LLD-00→LLD-agent-\*/LLD-ts-common；docs \*-01 16 件去号；demos D 系/P4W→demo-\*；l3app→firmware/tests/netlab；tests/l5→tests/safety_check〔check_l5→check_safety_contract，CI/SKILL 同步〕；tools/board 16 脚本描述化；scenarios 2 件——新旧映射登记 names.md §6）；③ 瘦身（AGENTS §1 留近三会话〔658→102 行〕、plan 现行化、names 旧修订归档）；④ 新立 docs/std/naming.md + docs/evidence/README.md 索引；⑤ agent 死模块扫描零命中、固件 C 逻辑不动（注释引用同步；无工具链——交付即验证）；⑥ 验证 = 引用扫零 + 子智能体复核修补轮（d8_client→lifecycle_client / plan §7 重复块与 §2 旧引用 / evidence 索引勘误 / d4/d6/d9_pkg.h 缓办登记——复核发现全闭合） + agent 333+2s+23 env-fail（环境域）+ ruff + repo pytest + sync --update + 子智能体复核。evidence 文件名历史不回溯（索引化），decisions.md 不瘦身（权威记录）。
- v1.154 · 2026-10-24：**板卡画像同板去重合并（owner 指令「atk-dnesp32s3b / dnesp32s3b 这两个应该是一块板子」——fix 类卫生笔，DEC-75：随修随发不占 feature 计数）**：agent/boards/ 双画像实为同板（正点原子 ATK DNESP32-S3B = Zephyr 收录板 alientek/dnesp32s3b；串口 by-id 全同 + boya 16MB 同源 + zephyr_board 键即收录名；重复根源 = BV2 实战为同板新开流水线画像）——合并为 **dnesp32s3b.toml（流水线规范名，install_profile 生成键——防 BV2 再生成重现重复）**：吸收 atk 物理事实（[hardware] 引脚节/boya 出处/持有器与 C0 注记）+ 现行镜像态取 BV2 值（cube=dbc 显式回填〔一五五观察项④就此板闭合〕/slot 32KB 注记产线镜像 2048/P4W 探针）；atk-dnesp32s3b.toml 删除。**附带修复**：HW-1 全名提及「ATK DNESP32-S3B」此前双命中拒绝绑定（恰一门恢复）；test_hardware/test_clarify×2/clarify 文档串/LLD-agent-board-validation 示例 id（v0.1.2）随改。验证：受影响套件 71 绿 + ruff + 目录匹配 sanity 恰一命中；agent 全量 333+2s+23 env-fail（**本会话机 = 全新环境**：仓库 10-24 全新 clone、zephyr/SDK/clang 未建——stash 基线对照同败非本笔引入；agent venv 已按 checklist §10 重建〔uv + py3.12 全 wheel〕）。
- v1.153 · 2026-10-23：**BV2 实战 ✅（§11h L 表新立——V0.16.0 累积池首单元，DEC-75 纪律）**：适配流水线真板首应用全链闭环（双板接入+供电双证 / atk flash-id / 五件套生成=板级面唯一来源 / deploybench 构建烧录 prov / 第二板入网 / BV1 C1-C6 全 PASS / 画像入目录 owner 委托记 / 双板 LN 双 ACTIVE PASS）。实战回填生成器三缺口（&wifi 分派/PWM 事实面/网络内存家族）+ BV1 C4 probe_cube 直查兜底 + deploybench prov 陈旧路由修复；观察项登记（通配单回执 quirk/双板命名 cube 语义）。
- v1.152 · 2026-10-23：**DEC-77 硬件域两项登记（owner 指令）**：① C6 stock 重烧任务剔除（owner 实机确认无问题——与我方 V0.14.0 buf-config TLV × STREAM 原生兼容实测双证闭合；IO9+RST 法降纯档案）；② **轮烧工作流**（硬件域事实）：主机单 USB 口不能双板同接——第二块板可通电驻网，烧录/串口检查走 USB 轮流窗口、测试/部署全程走 WiFi（zenoh 与串口解耦）；**BV2 真板实战 + 多真机 LN 复验由挂起转可执行**（板身份首烧窗口 flash-id 实测定）；BV1 判据面适配注记（C1-C3 串口面限 USB 窗口、C4-C6 网络面随时）。
- v1.151 · 2026-10-23：**DEC-76 渠道裁撤登记（owner 指令）**：pi 渠道（M1）正式取消（非 HOLD，终态裁撤——DEC-66⑤ 第二渠道采纳废止）；**Node.js 永不引入 = 项目硬边界**（web 案 A 零 Node 升格永久约束）；渠道定格四渠道（Terminal/stdio/MCP-HTTP/web），harness 槽位保留为架构预留。G 表 M1 ✂️、HLD-agent §1/§7/§9 同步。
- v1.150 · 2026-10-23：**DEC-75 版本节奏纪律登记（owner 指令）+ V0.15.0 推送**：minor 版（0.X.0）= 功能版本，须累积 ~5-8 个 feature 方可收口；issue fix 只走 patch（0.0.X）随修随发；存量版本号不回溯重编（0.13.0/0.14.0/0.15.0 维持原号）。V0.15.0 三笔 + 登记笔随 owner review 完成令推送（main + tag fw-v0.15.0）。后续批规划按 feature 计数排批；v4.5.0 平移批归属（捆绑 feature 或 patch）随批呈递认定。
- v1.149 · 2026-10-22：**SOURCES.lock 漂移复发登记（dc62682 CI agent-checks 红——4f83586 同类第二复发）+ 提交消息勘误**：dc62682（V0.14.0 收口笔）触碰 AGENTS/plan 等 skill 源文档但 SOURCES.lock 未随更新（tessera-safety/workflow 源哈希漂移）——本地全绿通过是因为 sync 在最终文档编辑**之前**执行，且 docs-only 尾改未复跑 skills 用例；该笔消息「sync 全绿」与事实不符（如实勘误）。**远端实况**：dc62682 的 ci 双 workflow = native-build/l5/repo 三绿 + agent-checks 唯一红（test_sync_check_clean_on_repo）；修复已随本地 V0.15.0 线（HEAD sync 绿）——push 后 HEAD 复绿，dc62682 历史红为常态不可变。**教训升级（4f83586 教训第 2 复发）**：sync 校验必须在**提交前最后一刻**执行（任何后续 touch 文档的编辑——包括提交消息撰写期的 AGENTS 追加——都令前次 sync 失效）；收口检查单将 sync 从「批内一项」升级为「commit 前最后一步」。
- v1.148 · 2026-10-22：**V0.15.0 收口 ✅（FIX-2 + BV2-I + 收口 = 3 单元全交付）**：回归定格 twister 17/17（115/115——wamr 套件并行 configure_file 竞态 error 单跑 PASS 环境域）/ agent **346+2s**（+11 BV2 + +1 抓取面）/ ruff / repo 5 / sync；HLD-agent **v0.2.4**（工具面 +board_adapt + 现状注记）；README 计数对齐；**tag fw-v0.15.0**（附注式本地，push 待 owner review）。后续候选：v4.5.0 正式版平移（V0.16.0，上游 ~10-26）/ BV2 真板实战 / pi 渠道（M1 HOLD）。
- v1.147 · 2026-10-22：**BV2-I ✅（V0.15.0 主单元——DEC-74 三裁决落地）**：domain/board_adapt.py 收录板路全链（定位/布局模板族〔P4 playbook 真锚——与在树 overlay 逐偏移对拍测试〕/五件套/C0 预检/agent/adapt 工作区）+ install_profile owner 闸（BV1 loader 可装载 = 工单两端闭环）+ MCP board_adapt（strict）+ 未收录清单待确认态（go_build 恒 False）；测试 +11。§11h K 表 BV2-I ✅ v1.147。
- v1.146 · 2026-10-22：**V0.15.0「新板适配批」立项 + FIX-2 ✅ 根治（owner「我已经完成review，请你继续开发」泛指令——DEC-74 BV2 门③三裁决按建议值过裁〔先例 DEC-59/64/65/67 同型〕；V0.14.0 四提交 + tag fw-v0.14.0 已随令推送）**。① **§11h K 表新立**（执行序 FIX-2 → BV2-I → 收口；v4.5.0 平移顺延 V0.16.0 候选）；② **FIX-2 ✅**（详见 J 表 ✅ 行）：板载插桩破案——call0() argc=0 × WAMR「argc ≥ param_cell_num」契约（带参 app_tick 必陷）+ 实例异常位跨调用毒化 + health 配额缺省三连根因；修复（tick 经 call1 带 ctx / 失败清异常 / health 显式配额带参，23+/15-）+ agent 抓取面（post_deploy_check reset_before_capture 单端口会话——CH343 两段式竞态 no_verdict 假 FAIL 根治）+1 用例；**板上闭环 = 探针 ALIVE 首印 + 零复位 + BV1 C4+C6 PASS（P4 C1-C6 全链首次全绿 93.3s）**；P4 烧录布局（ROM 0x2000 简单引导）与 meta 双副本快照纪律入册；③ DEC-74：LLD-agent-board-adaptation §5 三决策点按建议值——接入件产出 `agent/adapt/<board>/` 工作区（适配件是产物非源码）/ C0 流水线内临时解锁 / v1 = 收录板全链 + 未收录清单生成。

> 更早修订记录（v1.0…v1.145）与历史批次计划已归档 `docs/history/plan-archive-2026-10.md`（2026-10-24 仓整理）。

