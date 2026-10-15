# AGENTS.md · Tessera 会话入口

> **本文件是什么**：每个开发会话（ZCode）的第一入口。由 K1 依据 `FOUNDING_PROMPT.md` v1.0（2026-09-18）改写生成。
> **权威顺序**：owner 最新裁决（`decisions.md` 中的 DEC）> `FOUNDING_PROMPT.md` > 本文件摘要。若本文件与上述冲突，以裁决/原文为准，并登记 Q 修正本文件。
> **维护规则**："当前状态"节每会话结束前更新；本文件的修改权在主会话。

## 1. 当前状态

- **2026-10-15（一一九） · EC3 交付（安装期权限确认——Q-40③/DEC-60③ 落地，V0.8.0 实现）**。① **无头路（实现）**：安装类 strict 审批（deploy_push_app/app_deploy/ln_deploy 三点）reason **强制携带包权限面**——tsap_tools.manifest_summary（caps/fs_paths/tier/needs.resources/threads/av/尺寸；不含验签——显示面，真授权门 = tsap_verify + 固件验签链）+ install_permission_brief 一行摘要；坏包审批前拦截；brief 无条件入 task_log。② **本地确认路（LLD 定稿——LLD-A02 v0.2.2 §3.2）**：同一 manifest_summary 数据面（单一事实源），确认事件经 arb 本地席位入固件——接线随设备形态批（嵌入式 install-time 确认无公开先例 = 先行者位置，R9 §4 对照在档）。③ 测试 +2（summary 全字段/坏包拒 + brief 双形态格式）。**agent 183+2s/ruff 显式退出码全绿**（固件零改动）。**下一单元 EC4：侧载通道（同验签链无例外——设计面 + 唯一收口点机械实证）**
- **2026-10-15（一一八） · EC2 交付（信任根表实现——Q-43/DEC-60 落地，V0.8.0 实现）**。① **store**：ts_trust.c（确定性 schema 走查/乒乓写+回读/惰性装载/撕裂回退）+ 两后端 + Kconfig；**分区 4KB→8KB 实施修正**（sim-flash 擦除块对齐实证）。② **appmgr**：有效集 = 工厂根〔TEST=测试根/生产=pk0+**pk1 转正**〕∪ 信任表；verify_slot **NULL = 有效集迭代**；COSE RAM 验签 + trust_update 五步编排（严格 N+1 + 现有效集签名 + 乒乓持久化 + 事件）。③ **net**：sys/trust-update（gated+租约）/trust-get + TRUST_UPDATED 订阅十类。④ **顺带根治存量生产缺陷**：rollback NULL 生产恒拒（IR2-07 以来——TEST 不可见）。⑤ **Agent**：trust_get/trust_update + FakeCube 信任语义。⑥ 测试 +3 面（store schema/乒乓/撕裂双变体 + app test_13 十一断言组〔多根安装实证/重放拒/互荐/全撤回〕 + net 裁剪断言）+ 夹具生成器入仓 + agent ×2。**回归：twister 16/16（107）/agent 181+2s/L5/ruff/sync 全绿**。真机信任表面随板级批。**下一单元 EC3：安装期权限确认（Agent 呈报 strict 路实现 + 本地确认路 LLD——Q-40③）**
- **2026-10-15（一一七） · V0.8.0 生态批开工 + EC1 交付（信任链 LLD 设计定稿——Q-43/DEC-60 落地）**。owner 指令「按开发计划继续直至完成全部原定计划 + 完成后自检（文档/代码规范/测试充分）」——V0.8.0 EC1-5 全批推进 + 终局自检。① **Q-43 呈递（门③）→ DEC-60 按建议值登记**（owner 泛指令先例 DEC-59 同型）：五子项 = 信任表 **TUF root 同型全量替换**（`{"ver","keys[]"}` 2 对定序键——无 revoked 列表：定长溢出 = 旧键复活面根除，撤销 = 次版剔除）/ **有效集分层**（工厂根 ∪ 信任表；生产工厂根 = prov pk0+**pk1 转正消费**〔此前死字段〕；TEST = 固定测试根）/ **ts_trust 4KB 双副本乒乓分区**（TS_STORE_TRUST 默认 n——缺分区 = V0.7 行为逐字节等价，存量板零重刷）/ **sys/trust-update·trust-get**（gated+租约+COSE_Sign1 现有效集签名 + ver 严格 N+1；TRUST_UPDATED 事件订阅十类）/ **verify_slot NULL = 有效集迭代**。② **顺带定案存量生产缺陷**：rollback_n 传 NULL 且生产 NULL = 拒 → 生产回滚路径自 IR2-07 以来恒拒（TEST 不可见——测试根覆盖 NULL）；EC2 修复 + 多根用例实证。③ LLD 四份：ts-store v0.5（§4a）/ts-appmgr v0.7（§5b）/ts-net v0.4（§4.3/§5）/A06 v0.3（trust 工具）。**下一单元 EC2：信任根表实现（store ts_trust.c + appmgr 多根验签/trust-update 编排 + net 命令 + Agent 工具 + 测试）**
- **2026-10-14（一一六） · CG5-B 交付（资源推送方案 A——Q-39③ 落地，V0.7.x 补批）**。① **授权模型定案**：随包联动白名单（激活包 needs.resources 前缀——activate 绑 + boot 恢复；无 needs = 全拒）+ 租约 + sha256 读回校验；不引 prov 白名单。② **固件**：appmgr res registry（scan res_csv 三点同源）+ hal 宿主原语三件 + prefix_match 提取 + sys/fs-begin/chunk/commit（gated；commit 失配删残片；TS_EVT_RESOURCE_WRITTEN 订阅九类；CMD_TABLE 20）。③ **Agent**：deploy.push_resources + envelope path/sha256。④ 测试 +5 面（registry 矩阵/命令分层/boot 恢复/构建裁剪/agent 三态——twister 16/16〔104〕agent 179+2s 全绿）。⑤ 真机 net+SD 组合面随板级批（无该组合 bench——如实登记；授权面 sim 全测 + 后端与 D-SD 同一 API）。**下一版本候选：V0.8.0 生态批（EC1-5 多开发者信任链，Q-40 方向已锁）/ 板级批（net+SD 资源推送真机 E2E + large 档板级配置）——随 owner 点向**
- **2026-10-14（一一五） · CG7 交付 + V0.7.0 收口（tag fw-v0.7.0）——合同泛化批 CG0-7 全批完毕**。① 术语清扫：design 五文件 11 处「立方体→设备」（cube 段名 API 兼容注记；登记行/引文保留）。② 全量复验：**twister 16/16（103）/L5/repo 2/agent 178+2s/ruff/sync 全绿**。③ **真机 spot check（新固件全量重刷 @ deploybench）**：v1 prov 兼容实机实证（load=0 缺省路径）+ **存量 AG7 APP 跨固件复用**（持久化槽装载 `[app1/l0] AG7 DONE`）+ DB PASS + **CG7 DEPLOY PASS**（caps 实机自报 tiers=[small]/512KB 线性帽/128KB 槽池 + 预检消费 + 测试根签名 4 分块部署 + 真验签 + 激活暖复位 ACTIVE——证据 docs/evidence/cg7_deploy_console.txt）。④ V0.7.0 终态：部署模式/控制源仲裁/资源档位/能力发现/estop 清除收口/合同 v2 正典全落地。**余项登记**：CG5-B 资源推送（独立设计面下一单元）；本地交互源/本地清除物理通道（设备形态批）；板级 large 档全链（板级批）。**下一版本候选：CG5-B→V0.7.x 补批 / V0.8.0 生态批（EC1-5）——随 owner 点向**
- **2026-10-14（一一四） · CG6 收口（estop 清除通道）**：实质面已随 CG1（§5a 措辞 + prov 字段）/CG2（命令面守卫 + test_15）交付——核对后无剩余实现面；收口 = LLD-ts-safety v0.3.3 **§9a 已知限制节补齐**（CG1 注记声称的「已知限制节」此前不存在——如实补：ISO 13850 有据偏离〔补偿控制〕/本地清除物理通道随设备形态批〔届时偏离撤销〕/仲裁信号源 deferred/stack_kb 不消费）。**下一单元 CG7：术语清扫（LLD 全库 立方体→设备）+ 全 bench 复验 + tag fw-v0.7.0（CG5-B 资源推送独立单元随后——plan 注记）**
- **2026-10-14（一一三） · CG5-A 交付（能力发现——DEC-59/Q-39④ 落地，V0.7.0 实现④a）**。① 固件 caps 块：sys/get-info 增 {tiers, max_linear_memory_kb, slot_pool_kb}（tiers 派生 large ⇔ LOAD_MAX ≥ GATE_LARGE——与安装期矩阵同源；非 WAMR 桩维持 v1 五键形态）。② Agent 装前预检：push_app ①b——caps 消费，档位不支持/线性内存超帽 → TA_E_POLICY 结构化拒（**装前拒——零上传零租约**）；caps 缺失 = 旧固件跳过（安装期矩阵兜底——双保险）。③ 测试 +2（framework.app test_11〔net 桩面入 app 套件〕+ agent caps 预检三态）。**CG5-B（资源推送方案 A）留下一单元**：fs 写命令面为独立设计面（宿主写授权模型需设计定案——质量优先不赶工），真机 SD 面验证同批。**下一单元 CG5-B：资源推送（fs 写通道设计 + 部署会话推送 + sha256 审计）→ CG6 estop 清除通道 → CG7 术语清扫+全 bench 复验 tag fw-v0.7.0**
- **2026-10-14（一一二） · CG4 交付（资源档位——DEC-59/Q-39②⑤ 落地，V0.7.0 实现③，消费 AG7 数值）**。① **固件**：`ts_appmgr_scan_needs` = tier/needs 单一解析源（键分发 + cbor_min 新增 ts_cbor_skip；schema 纪律：needs 仅 large/resources fs_paths 文法/域外 fail-closed）；安装期匹配矩阵（stage_verify 验签后：线性内存 ≤ WAMR_HEAP 帽 → resources 须 TS_HAL_FS → large 须 LOAD_MAX ≥ GATE_LARGE〔设备能力派生〕）；尺寸门双门 Kconfig（small 16384 维持/large 262144）；boot 走查按包 tier 取门；BUILD_ASSERT(LOAD_MAX ≤ SLOT_SIZE)。② **Agent 镜像**：TsapManifest tier/TsapNeeds（成组纪律同固件）；编译链 tier/needs 形参（large 门 256KB——IR2-03 钳制平移 + needs 链接钉死 flags：initial/max-memory 取整 64KiB 页同值 + -z stack-size 分立两参）；Runner 落盘同步 project.json（三方一致）；_CONVENTIONS 档位纪律。③ **测试**：framework.app test_10（扫描矩阵/匹配行/安装拒/boot 直装走查）+ agent 档位族 7 用例；夹具生成脚本 gen_tier_pkgs.py **入仓**（机械生成 + 测试根签名 + pad 差异化——教训 27）。④ 过程拦下：pad 两度被 GC/DCE（health_ping 语义门顺带拦下）；large 门初版缺省钳制错（测试矩阵暴露）。**twister 16/16（102 用例，+1）/ agent 177+2s（+7）全绿**。**下一单元 CG5：能力发现+资源打包（get-info caps 块 + 部署会话资源推送〔方案 A〕）→ CG6 estop 清除通道 → CG7 术语清扫+全 bench 复验 tag fw-v0.7.0**
- **2026-10-14（一一一） · CG3 交付（控制源仲裁机制——DEC-59/Q-41②/合同 11 落地，V0.7.0 实现②）**。① **席位**：`ts_arb_owner` 原子（缺省 REMOTE = 现行为零变化）；`ts_safety_set_arb` 幂等 + **切换零输出**（无通道写/状态迁移，EN 60204-1 §9.2.3 同型）+ `TS_EVT_ARB_CHANGED`（{owner,old}；订阅八类外发 …/sys/event，安全类 QoS）。② **来源标记 + 压制**：`ts_src_t {APP, ZENOH, LOCAL}` + `ts_safety_commit_src` 新入口（既有 commit 族签名不变 = TS_SRC_APP）；本地激活期 ZENOH 来源拒（commit_impl 入口持锁后、状态检查前——身份级拒绝优先 + 审计 src 归因）；APP 路径不经闸（编排意图载体）。③ **审计 src 维度**：`_rsv` 字段转正（旧记录 0=APP 兼容）+ get-audit 末位加 src（加性）。④ **租约联动（视词语义）**：held_by 恒 false + acquire 拒（不改在册状态，TTL 照常走完）；acquire 回执 `local_active=true` 装饰区分两型拒绝。⑤ **本地交互源激活信号接线随后续设备形态批**（LLD §5b 既定——本批立机制）。⑥ 顺带修复：ts_safety_test_reset 补审计环归零（full_scenario 丢弃算术用例序敏感——测试隔离缺陷，新用例先跑即暴露）。用例 +2（safety test_arb_seat_and_suppression / net test_16_arb_lease_view）。**下一单元 CG4：资源档位（manifest tier/needs 走查 + 安装期匹配矩阵 + 尺寸门双门 small 16KB/large 256KB + 槽池 + Agent 侧 TsapManifest 同步——消费 AG7 数值）→ CG5 能力发现+资源打包 → CG6 estop 清除 → CG7 术语清扫+全 bench 复验 tag fw-v0.7.0**
- **2026-10-14（一一〇） · DEC-59（Q-42 裁决：三项按建议值进入实施——owner 泛指令「继续按照计划进行开发」按既定纪律登记〔先例 NV-5/NV-4 同型〕，可逆性保障：全字段向后兼容/门值为常量/未装载兜底 = v1 等义）+ CG2 交付（部署模式实现——V0.7.0 实现①）**。① **prov schema v2**（prov.c）：双形态确定性解码（9 对 v1 / 11 对 v2——键序 = v1 前缀 + 尾部追加 deploy_mode/estop_remote_clear）；v1 缺字段缺省（orchestrated + 远程清除开放）+ 域外值 fail-closed + v/对数错配拒 + 未装载静态兜底同 v1 缺省（ts_prov_t 增 ts_deploy_mode_t 枚举）。② **linkmon 模式守卫**（linkmon.c）：断链/恢复对称仅 orchestrated 调 set_link；standalone 断链仅留观测事件（事件面不变——LLD-ts-safety §3a）。③ **standalone boot 链路声明**（net/init.c）：prov 装载成功且 standalone → ts_net_init 期 set_link(true) 一次（镜像 TS_NET=n glue 的 BOOT_DONE 声明模式）——**CG1 文本未覆盖的 ACTIVE 驱动者缺口本批定案**（「standalone = 本地逻辑照常」的输出使能路径；输出值保持 poweron 安全值直至显式 commit——DR-04 无回写）。④ **estop-clear 命令面守卫**（cmd.c）：`estop_remote_clear=0` → TS_E_STATE + need=local-clear。⑤ **测试**：framework.store test_prov_v2_fields（+flash 变体同跑）+ net test_14（**standalone 断链零迁移断言** + orchestrated 对照迁移）/test_15（estop-clear 守卫矩阵）——**twister 16/16（99 用例，+4）**。⑥ **顺带修复既有缺陷**：agent/tools/flash_prov.py 直写裸 CBOR 缺分区头（u32 len + u16 crc16——装载器必拒，生产 esptool 烧录路径缺陷，代码检视发现）→ 修复 + v2 字段输出（缺省维持 v1 形状——旧固件兼容）；agent 侧 push_prov 文档面 v1/v2 双形态提及。⑦ LLD 同步：ts-store v0.4.1 / ts-net v0.3.9（§6 standalone boot 声明定案）/ ts-safety v0.3.1（§3a/§5a 实现注记）。回归：twister 16/16（99）/ agent pytest / ruff / sync_check 全绿（显式退出码）。提交 1761a37
- **2026-10-14（一〇九） · CG1 交付（合同泛化 LLD 修订批）：四 LLD 修订 + 安全合同 v2 正典落节（AGENTS.md §6 + FOUNDING_PROMPT §5——DEC-58 批准措辞：合同 3 模式化/合同 5 清除附注/新增合同 11 控制源仲裁/合同 8 立方体→设备）+ Q-42 呈递登记停门（门③）**。① LLD-ts-safety v0.3（§3a 部署模式守卫/§5a estop 清除按设备能力〔无交互设备远程令牌 = 有据偏离登记〕/§5b arb_owner 控制源仲裁〔激活压制远程 + 切换零输出 + 审计 src 维度〕）；② LLD-ts-net（linkmon 模式守卫 + estop-clear prov 守卫〔**兼容性修正：v1 缺字段 = enabled 保现网**〕+ 租约本地席位联动）；③ LLD-ts-appmgr v0.6（§5a 档位与安装期匹配：tier/needs + 尺寸门双门〔small 16KB 维持/large 建议 256KB——AG7 数值〕+ 匹配矩阵拒装 + get-info caps）；④ LLD-ts-store v0.4（prov schema v2：deploy_mode/estop_remote_clear）。**Q-42 停门（门③）**：prov v2 字段（缺省兼容）+ manifest v2 tier/needs + 门值建议（256KB）——CG2-CG4 开工前置。**Q-42 已由 DEC-59 登记（按建议值）——CG2 已交付（见上条）**
- **2026-10-14（一〇八） · AG8 收口（Agent 批 V0.6.0 完结，tag fw-v0.6.0）——通用域解放第一版本批交付：Agent 双角色 + 智能内化落地**。回归定格：**twister 16/16（95 用例）/ repo pytest 2 / agent 170+2s / ruff / sync_check 全绿**（显式退出码核验）；plan §11e AG1-AG8 全 ✅（v1.71）；LLD-A02 §3.1 措辞修正（allow = strict 自动放行——owner 批准义，v0.2.1）。**V0.6.0 终态**：创作循环全栈（AG2 工作区+ws_*〔roots 钳制/防盲写/锚定编辑〕/ AG3 域无关循环引擎+验证器插件 / AG4 终端门面〔Frontend 第二实现〕/ AG5 快照 resume+SIGINT / AG6 双路径 app_develop+参数规则+run 子命令 / AG7 真机 PASS〔真 LLM 4 轮多文件工程收敛 + 无线部署 + 判据命中 + large 数值〕）+ 质量优先条款全程生效（AG7 真实拦下 3 缺陷：路径别名/工具异常炸穿/提交纪律第三复发——均已修）。**下一批 CG1（合同泛化 LLD 修订批——CG0 门④措辞已裁 DEC-58）：safety/net/appmgr/store 四 LLD 修订 → CG2 部署模式 → CG3 控制源仲裁 → CG4 资源档位（消费 AG7 数值）→ CG5 能力发现+资源打包 → CG6 estop 清除 → CG7 术语清扫+全 bench 复验 tag fw-v0.7.0**
- **2026-10-14（一〇七） · AG7 交付（复杂 APP 真机实测——**AG7 PASS**：真 LLM 创作循环全链首次真机点亮 + large 档数值采集）——Agent 批实现⑥**。① **全链**：D-AG7 spec（四节模板：温控滞回 + kv 持久化 + **多文件工程**〔main.c/thermo.c/include/thermo.h——引号包含头文件〕）→ **真 LLM（MiniMax-M3）创作循环 4 轮收敛 215s**（r3 manifest 缺 heap_kb 被「上轮小结」通道修复——AG6 反馈机制实战生效）→ wasm 1793B（imports 恰 = ts_adc_read/ts_gpio_write/ts_kv_save/ts_log_write）→ zenoh 无线部署 slot1 激活 → **真机判据精确命中 `[app1/l0] AG7 DONE cycles=200 heat=0`**（证据 docs/evidence/ag7_console.txt；heat=0 = ADC 悬空残压高于滞回开阈——确定性如实）。② **顺带拦下两真缺陷**（真 LLM 实测价值）：ws_* 路径别名（LLM 自然写 project/ 前缀——确定性剥除 + 提示词声明工程根基准）；**工具异常炸穿循环**（TaError 直抛顶层——改 gated_tool 同语义的结构化反馈回喂）。③ **large 档数值采集**（Q-39/CG4 输入）：真实复杂逻辑 APP 1793B；资源型直编译探针（绕交付门仅测量）——wasm = 资源 + 147B 固定开销，8/16/32/64/128/256/512KB 全线性（512KB 表 → 524KB wasm）；32KB 表即撞现 16KB 门（服务端钳制 IR2-03 生效实证）。④ demo 归档 agent/demos/D-AG7/（spec/三源文件/project.json/wasm/tsap）。⑤ 驱动 = ~/project/logs/ag7_demo.py（仓外惯例）。回归：**170+2s / ruff / sync_check 全绿**（别名测试 +1）。**下一单元 AG8：回归定格（twister 16 套件全量 + repo 2）+ 文档同步 + tag fw-v0.6.0**
- **2026-10-14（一〇六） · AG6 余项交付完毕——Agent 批实现⑤收官：app_develop 升级为创作循环后端（双路径）+ PydanticAI runner + `tessera-agent run` 子命令**。① **app_develop 双路径**：wasm_path=None → **创作循环主路径**（spec_check 门 → 工作区〔task_id 工作区 + 仓库白名单只读 roots〕→ CreationLoop〔判据注入/事件日志/repair_feedback 首轮证据〕→ PACKAGED → 独立复验〔asyncio.to_thread〕→ 返回键兼容 + additive〔task_id/workspace/state/rounds〕）；wasm_path 给出 → **单发流原样维持**（AG6 前行为，自带产物/既有剧本）。② **PydanticLoopRunner**：plan/implement 双 Agent（PlanOutcome/ImplementOutcome DTO）；implement 工具面 = ws_* 四动词 + read_skill（渐进披露维持）；**manifest 随轮硬校验**——不过转 declared_done=False 带小结（loop 新增「上轮小结」回喂通道）不抛崩循环；TsapManifest 校验 + 工程清单落盘（exports 同步链接导出面）。③ **提示词拆块**：_CONVENTIONS 约定块单发/循环共用（改一处两流同步）+ _plan/_implement 系统提示（多文件工程纪律：工程内头文件引号包含/≤200 行整文件再生/大文件锚点替换）。④ **loop.py 扩展**：RoundOutcome 增 manifest/app_id/threads（引擎不消费——域无关维持）+ 收敛轮 facts 收集（LoopResult.facts）+ 上轮小结通道。⑤ **TerminalFrontend.resume()** 公共续跑方法（快照判据恢复）+ __main__ `run` 子命令（--resume/--yes/--json/--no-plan-confirm/--deploy/--key-path；退出码 0/1/2；keys 目录探查）。⑥ **test_app_chain 迁移**：source_c 单发剧本 → 两条循环剧本（收敛全链真 clang 真签名 + 证据回喂两轮修复）；单发/wasm_path 与 deploy 六测原样绿。**169+2s / ruff / sync_check 全绿**。**下一单元 AG7：复杂 APP 真机实测（真 LLM 多文件工程 demo + large 档数值采集〔Q-39 补呈输入〕）**
- **2026-10-13（一〇五） · AG6 部分交付（审批参数规则——Q-38⑤ 落地）：PolicyParamRules + 求值序唯一权威（deny→allow→类别；deny 恒优先/AND 精确匹配/str 归一）+ gated_tool 集成（**allow 命中 = strict 自动放行**——owner 已批 Q-38⑤ 原义：白名单参数如目标 cube=开发板免逐次审批；LLD-A02 §3.1 早前"不越过 strict"句与 owner 批准语义相悖，按批准义实现）+ config [policy.param_rules] 装载 + compose 并入（坏条目跳过不静默生效）——测试 +7（求值序矩阵/AND/归一/三路径 gated/compose 并入/config 解析）——168+2s/ruff/sync_check 全绿**。**AG6 余项（下单元续作，如实登记）：PydanticAI runner 适配器（PlanOutcome/ImplementOutcome DTO + ws_* 工具面）+ app_develop 内部升级（循环后端；wasm_path 旧路径维持单发流；repair_feedback 首轮证据注入；返回键兼容+additive task_id/workspace/state/rounds）+ test_app_chain 迁移（旧 DevelopOutcome 剧本 → 循环剧本）+ `tessera-agent run` 子命令**。app_chain.py 已全文核读（手术前置）
- **2026-10-13（一〇四） · AG5 交付（会话快照 + resume + SIGINT 优雅退出）——Agent 批实现④，断点续跑落地**。① `creation/snapshot.py`：take（循环状态 → `.session/snapshot.json` 原子写——文件内容本体留 project/ 只存哈希表〔单一事实源不双写〕+ round_summaries 摘要）/ load（schema + **逐文件哈希校验**——外部改动/缺文件 = TA_E_SNAPSHOT_STALE 如实拒）/ restore（round/plan 重建 + 历史证据摘要注入首轮提示——证据本体不回灌）。② 循环引擎接线：状态迁移与轮末自动快照（`_snapshot()`——失败如实抛）。③ 门面 SIGINT：KeyboardInterrupt → 兜底快照 + INTERRUPTED 终态（终报含 `--resume <task_id>` 续跑指引；中断路径快照失败不掩盖主信号）。④ 测试 +5（往返一致性/STALE 双形态/缺失与损坏/运行中自动快照无 tmp 残留/**中断→快照→restore→续跑收敛端到端**）——**161+2s / ruff / sync_check 全绿**。**下一单元 AG6：app_develop 升级接线（PydanticAI runner + ws_* 工具面 + 循环后端）+ 审批参数规则（PolicyTable param_rules）+ `tessera-agent run` 子命令**
- **2026-10-13（一〇三） · AG4 交付（终端门面——TerminalFrontend = Frontend 第二实现落地）——Agent 批实现③**。① `cli/render.py`：渲染纯函数层（计划 checkbox/轮次行/证据行/终报/事件派发——无 IO 无 curses，--json 同源；final 事件 rounds 键实证修正）。② `cli/facade.py`：TerminalFrontend——驱动 CreationLoop + 事件渲染（行式或 JSONL）；**三交互钩子注入式**（plan_confirm/question/approval——默认终端 input/getpass，测试注入剧本：交互逻辑与 IO 分离）；计划确认拒绝 → ABORTED 门面级终态（不产出，验证器零调用）；**--yes 语义安全默认**（问询取默认项，strict 审批不豁免恒 deny）；终报双形态（--json = 结构化 report 行）；`tessera-agent run` 子命令接线随 AG6（PydanticAI runner 就绪）。③ 测试 +7（渲染矩阵/快乐路径含计划确认/拒绝 ABORTED/--yes 安全默认/JSON 流式 schema/审批注入路）——**156+2s / ruff / sync_check 全绿**。**下一单元 AG5：会话快照（snapshot.py 原子写/哈希校验/resume 重建 + SIGINT 优雅退出）**
- **2026-10-13（一〇二） · AG3 交付（循环引擎 + CreationVerifier 域插件协议 + FirmwareCreationVerifier 真链）——Agent 批实现②，域无关引擎落地**。① `creation/verifier.py`：协议（compile/face_check/simulate/package）+ VerifyOutcome/PackageOutcome（detail 证据原文不美化——R6）。② `creation/loop.py`：状态机（DRAFT→PLANNING→IMPLEMENTING⇄VERIFYING→CONVERGED→PACKAGED/FAILED）+ 轮次预算 12 + 计划项 + **证据自动回喂**（近 3 条证据入下轮 prompt——编译 stderr 原文/判据表/循环纪律内联）+ 事件流（state/plan/round/evidence/final——AG4 终端与 AG6 task_log 同源）+ asyncio.to_thread 调度同步验证器 + 无 key_path 时 CONVERGED 即终态（打包外层显式触发）。③ `domain/firmware_creation.py`：固件域首实现——compile（工程清单驱动多文件聚合）+ face_check（产物复检：白名单/尺寸档/health_ping 必备）+ package（真 ed25519 签名）+ **sim 诚实拒绝**（sim_runner 未注入 = TA_E_NOT_CONFIGURED，不假日通过——接线随 AG6）。④ `wasm_build.py` 扩展：`compile_project_c`（多文件+工程内头文件引号包含〔规范化钳制〕+ 系统 include 全拒 IR2-03 维持 + 双编译一致 + 面门）+ `_run_clang_files`（单/多文件同一实现重构 + 逐符号 -Wl,--export=）；**AG3 实证定案**：缺导出由面检查一票拒（--allow-undefined 为 natives 所需，链接期不可区分——LLD-A08 已同步修正）。⑤ 测试 +10（DummyVerifier 状态机全矩阵：收敛/预算耗尽/面失败回路/打包失败/sim 跳过与诚实拒绝/无 key 收敛 + 真 clang：多文件头文件链/三门/全链真签名/坏源 stderr 回喂）——**149+2s / ruff / sync_check 全绿**。**下一单元 AG4：终端门面（TerminalFrontend——进度渲染/问询/审批 token/resume/--json）**
- **2026-10-13（一〇一） · C-7 owner 确认 + AG2 交付（工作区模型 + ws_* 四动词 + 测试矩阵 13 用例）——Agent 批实现阶段开工**。① `creation/workspace.py`：工作区布局（project/artifacts/.session）+ **project.json 工程清单 v1**（files/exports = 编译与面检查单一事实源；schema/app_id/tier/threads/manifest/resources/needs 字段齐——后两者留 CG4/CG5 消费）+ roots 钳制（**工程根相对路径语义**〔作者视角〕+ artifacts/\.session 保留前缀 + 符号链接 resolve 防逃逸 + 仓库白名单只读）+ 容量三限（512KB/4MB/64 文件）+ 原子写（tmp+replace）。② `creation/tools.py`：ws_read（行号制分页 400 行/上限 2000）/ws_write（**先读后写防盲写**——mtime+size 指纹；外部改动即 STALE）/ws_edit（唯一锚定替换 + replace_all + 失配带最近线索行号）/ws_list（工程树；@plan 留 AG3）。③ 错误族扩 7 码（TA_E_WORKSPACE_* / TA_E_ANCHOR_* / TA_E_LOOP_BUDGET / TA_E_SNAPSHOT_STALE）。④ .gitignore 增 agent/workspace/（永不入仓）。⑤ 测试 13 例：roots 逃逸矩阵（越界/符号链接/artifacts 只读/.session 不可见/白名单只读）+ 锚定失配/多义 + 分页边界 + 防盲写 + 容量 + 清单单一事实源 + 原子性——**139 passed +2s / ruff / sync_check 全绿**。**下一单元 AG3：循环引擎（状态机/预算/计划/证据回喂）+ CreationVerifier 协议 + FirmwareCreationVerifier（多文件聚合编译——wasm_build 扩展）**
- **2026-10-13（一〇〇） · DEC-58（owner 确认 CG0 门④合同措辞 + C-6 双 HLD）+ AG1 交付（LLD-A08/A09 定稿 + LLD-A01/A02 v0.2 修订）——Agent 批设计阶段收口，C-7 呈递门③**。① DEC-58 落册：合同 3 修订/新增合同 11/合同 5 附注三段措辞批准（安全合同泛化定稿，CG1 解锁）；HLD-agent v0.2 + HLD-contract-v2 生效。② **LLD-A08-creation-workspace**（新）：工作区模型（project.json 工程清单 = 多文件单一事实源 + roots 钳制〔符号链接逃逸/容量上限/artifacts 只读〕）+ ws_* 四动词（唯一锚定替换 + 先读后写防盲写）+ **CreationVerifier 域插件协议**（compile/simulate/face_check/package——固件域首实现，平台零 import 域断言扩展）+ 循环状态机（证据驱动迁移/预算 12/证据自动回喂）+ 会话快照（哈希表单一事实源 + 原子写 + resume 哈希校验）。③ **LLD-A09-terminal-facade**（新）：TerminalFrontend = Frontend Protocol 第二实现（与 McpFrontend 共享 compose 根——审批语义一字不差）；`tessera-agent run` 命令面（--yes/--resume/--json/--deploy）；三交互点（问询/审批 getpass/判据确认）；SIGINT 优雅快照；渲染纯函数分离。④ LLD-A02 v0.2：§3.1 审批参数规则（求值序 deny>allow>类别 唯一权威/只可收紧/精确等值）+ §5 编辑工具旧规格作废注（ws_* 继承）+ §5a 创作循环编排触点（app_develop 升级/repair_feedback 兼容）；LLD-A01 v0.2：app_develop 升级注记 + MCP 面不增 ws_*（面窄 = 安全属性）。⑤ 三连绿（126+2s/ruff/sync_check）。**待 owner：C-7 LLD 批确认（门③）——确认后 AG2 起实现单元（AG2 工作区+scoped 工具 → AG3 循环引擎+验证器 → AG4 终端门面 → AG5 快照 → AG6 接线 → AG7 真机实测 → AG8 tag fw-v0.6.0）；CG1（合同泛化 LLD 修订批）可并行开工**
- **2026-10-13（九十九） · DEC-57（Q-38…41 全部按建议 A + 质量优先治理条款）+ 深度设计两份 + 通用域解放开发计划定稿（plan §11e = V0.6.0 Agent 批 AG1-8 / V0.7.0 合同泛化批 CG0-7 / V0.8.0 生态批 EC1-5 全单元排期）**。① **质量优先条款入册**（owner 原文：不允许最简实现、须虑整体架构/可维护性/可扩展性、方案不满足目标停批讨论换方案——plan §12 增补）；技术栈复核结论 = 无需换（WAMR/PydanticAI/FastMCP/zenoh/Zephyr 评估在 DEC-57⑥）。② **HLD-agent v0.2**（深度修订）：A08 创作工作区 = **域无关循环引擎**（状态机/轮次预算/计划跟踪/证据自动回喂）+ CreationVerifier 域插件接口（固件域首实现——DEC-33 结构原则兑现：未来 PCB 域换 Verifier 即复用循环）+ 工作区模型（project.json 工程清单 = 多文件单一事实源）+ 会话快照；A09 终端门面 = **Frontend 抽象第二实现**（DEC-35 缝首次兑现——三门面共享 compose 根，审批语义同源）；§5.2 创作/交付边界（交付门清单一条不撤，工作区唯一出口 = verifier.package）。③ **HLD-contract-v2 v0.1**（新）：部署模式（orchestrated 现行为不变/standalone 断链仅留痕）+ 控制源仲裁（arb_owner + 本地激活压制远程〔EN 60204-1 §9.2.4 同型〕+ 切换零输出）+ estop 清除按能力声明（无头维持远程令牌 = 有据偏离登记；有交互设备本地为主可禁远程）+ 资源档位（manifest tier/needs + 安装期匹配拒装 + 内存链接期钉死）+ 资源打包方案 A（部署会话推送，不动 TSAP 容器）——**门④三段合同措辞随文呈递待 owner（CG0）**。④ plan §11e 三版本批 + §12 质量条款；跨批依赖 = CG4←AG7 实测数值、CG0 可与 AG1 并行。**待 owner：CG0 门④措辞裁决；AG1（LLD-A08/A09 批）随批开工**
- **2026-10-13（九十八） · R 批 research 四篇交付（通用域解放先导批）+ Q-38…Q-41 四呈递登记停门**：**R6** Agent 创作循环（`docs/research/R6-agent-creation-loop.md`——CLI 调研→Tessera 映射：内环改造〔工作区 scoped 文件面 + 计划/进度 + sim 自测迭代〕/独立 CLI 门面/三门面共享 compose 根；交付门清单不撤）· **R7** 复杂 APP 工程链（`R7-complex-app-engineering.md`——clang 单命令多文件+wasm-ld 标准链/WAMR fast interp 2× 预编译码代价/Android largeHeap 与 Wasmtime ResourceLimiter 档位先例/资源外置 ts-fs）· **R8** standalone 与控制源仲裁（`R8-standalone-mode-arbitration.md`——EtherCAT 按通道替代值/ISO 17757 失联≠故障/EN 60204-1 §9.2.4 本地站压制远程/ISO 13850 estop 复位仅本地 = 现行远程 estop-clear 的张力点入呈递）· **R9** 多开发者信任链（`R9-multi-developer-trust.md`——安卓自签哲学/MCUboot 多公钥最近先例/TUF 离线撤销/RFC 9052 多签容器不可互换 = 维持 COSE_Sign1/OpenWrt 无验签反面教材）。**Q-38（Agent 批前置·门③）/ Q-39（资源分级）/ Q-40（信任链方向）/ Q-41（standalone 合同泛化·门④）四呈递全文在 decisions.md 待 owner 裁决**。**待 owner：Q-38 裁决后 Agent 批（V0.6.0 候选）开工；Q-39/41 随合同泛化批；Q-40 随生态批**
- **2026-10-13（九十七） · 需求校准批（DEC-56：owner 四轮校准「全部按照建议」+ DEC-12 双角色明示）+ 需求文档批交付——通用域解放：平台从「专用小域」走向「通用域」**。四项校准：① 设备**形态不限**（立方体 = 比喻；触摸屏等仅为设备外设例子——**不做专项功能批**）② APP 复杂度**不受结构性预设限制**（16KB 门/单文件/内存账/整文件再生全部重开重定——D4 方向）③ 设备**独立运行与远程编排同为一级模式**（standalone 合同泛化：fail-safe 语义声明化 + 控制源仲裁，estop 至高不变——D6 方向，门④随 design 批）④ **Agent 双角色**（DEC-12 v1.1 owner 原文：「Agent 不但要自带一个简单的 AI 客户端，另外也要能够作为 server 通过 MCP A2A 等方式接入其他 AI 应用」）+ 智能内化（创作面放宽、交付确定性门不撤）。落文：FOUNDING_PROMPT **v1.1**（使命重述 + DEC-01/02/12 修订 + §6 同步）+ decisions.md DEC-56 + plan **§11d 三批路线**（R 批四路 research → Agent 批〔独立 CLI + 创作工作区，V0.6.0 候选〕→ 合同泛化批〔+LLD 术语清扫〕→ 生态批〔D5 维持单根至彼时〕）+ HLD 双注记 + plan 修订日志恢复（v1.69；v1.68 后漏登如实注记）。**下一单元：R 批 research 开工（四路：① Agent 创作循环〔复用 agent-cli-research-01〕② 复杂 APP 工程链与资源泛化 ③ standalone 合同泛化 ④ 多开发者信任链）**
- **2026-10-13（九十六） · AI CLI 深度调研批（owner 指令：下一阶段开发重心 = Agent 侧）+ 审批闸委托人假设缺口登记（记录不开发）→ `docs/agent-cli-research-01.md`：九项候选呈递待 owner 排序**。四路并行实抓（Codex CLI 源码级/opencode v1.19.0/Gemini CLI docs 全套/Claude Code 官方文档）+ ZCode 自省 + aider 增量（R1-R8）。核心结论：① 业界约束实现收敛**五层模型**（提示/指令文件〔AGENTS.md 事实标准〕/机械门禁〔hooks 拦截面 2026 四家收敛 + 诊断回喂〕/权限沙箱〔参数级 specifier + OS 沙箱 + 网络默认禁〕/流程结构〔plan/todo/checkpoint/多代理〕）；② Tessera Agent 机械门禁与审计层**强于全部调研对象**（四道确定性门 + sync_check 机械锁），运行时观测反馈回路（diag_classify/simreal_diff）域独有；③ 缺口集中流程结构层：会话持久化（LN 注册表内存态）/计划外显/hooks 拦截面/回放器 + 审批参数级粒度。**候选九项**（§5，建议序）：任务链持久化恢复 > 计划/进度工具 > 部署域诊断自动回喂 > hooks 拦截面 > 审批粒度+上下文自省 > 决策链回放器 > MCP 客户端 > 问询双向化 > 审批双通道〔已裁挂起〕；多代理与通用文件工具面建议不做。安全缺口同步落册 decisions.md（sys_approve 认证「持有 token」≠「主人本人」——AI 客户端/多客户端自批风险，owner 裁记录不开发）。顺带定案 M16 遗留「sync_check 漂移源待查」：**AGENTS.md 本身是 tessera-workflow/-safety 的锁定源文档——每会话「当前状态」更新即必漂移**（非随机现象；提交流 --update 必跑纪律已固化，根因至此明确）。**待 owner：候选排序裁决后开 Agent 侧新批**
- **2026-10-13（九十五） · M19 全交付（V2 纵深批③：真 wasm 多线程全链——DEC-55/Q-37 A 落地，真机 DT PASS）+ M20 收口（tag fw-v0.5.0）——V2 纵深批三单元完毕**。① **M19a runtime**：`TS_APP_THREADS`（默认 n，基线零扰动）门控 WAMR thread-mgr+共享内存；`ts_thread_start/join` natives = **宿主 k_thread 编排**（`spawn_exec_env` 纯对象 + 我方线程/join——绕开 WAMR zephyr 平台层 os_thread 族三缺陷与 lib-pthread×计量上游死结）；每线程 L2 指令预算回调先行；停止先 join 后回收（共享内存序）；xtensa 软 8 字节原子垫片；framework.threads 新套件（3 用例）。② **M19b**：agent 线程档编译链（官方配方 flags + 白名单 + threads 传递）+ 真 LLM 三轮收敛 demo.dthread.count（threads=2）→ thrdemo 最小载体 → **真机 "DT DONE cnt=2000 rc=2000"**（原子共享 + join 回传；证据 docs/evidence/dt_PASS_console.txt）。③ **M19c**：twister **16/16（95 用例）**/L5 6/6/repo 2/ruff/agent **126**+2s 全绿；教训 35 入册（WAMR loader 原地改写 wasm 缓冲——嵌入必须可写段 等）。④ **M20**：V2 纵深批收口 tag **fw-v0.5.0**（M18 D-PDM + M19 真多线程 + D-AV 盘点上游观察）。**下一版本候选：多真机拓扑 LN（第二块 cube）/ 生产语义深化（真验签部署链板级复验）/ 上游 v4.5.0 正式版平移——随 owner 点向**
- **2026-10-13（九十四） · V2 纵深批开工（owner 点向：多真机 LN 挂起〔第二块 cube 未接入〕）+ M18 D-PDM demo 交付（DP PASS 双侧）——pcm16 音频全链闭环（DEC-54② 既定③收口）**。真 LLM 两轮收敛（wasm 2261B/TSAP 4944B，manifest 三方一致）→ pdmdemo 载体（avdemo 克隆−摄像头+TS_DRV_PDM，基础板目标）→ 真机 **"DP DONE frames=10"** + PC 侧 **8 帧完整（分片 crc 全过、span=4222）→ .pcm/.wav 落盘 = DP PASS**（证据 docs/evidence/dp_PASS_console.txt）。顺带双缺陷收口：av.c 惰性 bring-up（驱动 init 无接线恒 E_IO）+ **M11 重建 dav_recv 整帧误校验**（合同 = 分片级 crc——真机链顺延未暴露的重建债，dav_recv/pdm_recv 双修）。回归：twister 15/15（92）/L5/repo 2/ruff/agent 125+2s 全绿。批计划 = plan §11c（M19 真多线程设计批 Q-37 停门 + M20 收口 tag fw-v0.5.0）。**M19 同批完成呈递：Q-37 已登记停门等 owner**（建议 A = TS_APP_THREADS 门控启用 + 重放合同定点豁免〔DEC-31 局部翻案〕——五事实调研在档：Zephyr 平台零补丁/三件套/终止面/计量 per-env/内存账；批准后 M19a-c 实施批开工）
- **2026-10-13（九十三） · M17b 收口：PDM bring-up 完成（PDMB PASS ×2）——「TS_DRV_PDM 时钟链」观察项撤销，V0.4.x 补批终态全部交付**。owner 提供官方参考源（Seeed wiki 麦克风专页 + AskLou-io/Pomodoro_Circuit_Python〔经核未用 PDM——analogio+A0+模拟语音，如实登记〕）；11 轮收网 = IDF i2s_pdm.c/i2s_hal.c 逐函数对照 + 板内分层焊盘镜像诊断（MCLK/BCK/WS 三信号路由空置脚回读）。双缺陷定案：① 时钟计划误推导（bck_div 4 < 官方硬下限 8；DSR_16S 应 fs×128=2.048MHz）② 致命项 = GDMA 整外设按在复位态（boot 后 rst_en1.dma_rst 默认 1）——寄存器全 0 写不落 → I2S FIFO 灌满（i2s_int=0x3 实证 RX 曾收数，**麦克风硬件完好**）→ FSM 背压关 WS/BCK（MCLK 纯分频不受背压 = 「寄存器全对而引脚全平」矛盾根源）。修复 = gdma_ll_reset_register 出复位 + 官方时钟计划/mono 语义对齐。真机：8 帧 × 640B span=[-726,4605] 真实音频（证据 docs/evidence/pdmb_PASS_console.txt）。回归：twister 15/15（92）/L5 6/6/repo 2/ruff/agent 125+2s；教训 34 入册（RCC 三步定式 + 分层镜像诊断法）。**下一版本候选：多真机拓扑 LN 验证（需第二块 cube）/ V2 级纵深（真多线程批 / D-AV·PDM 产品化纵深）——随 owner 点向**
- **2026-10-13（九十二） · V0.4.x 补批收口（DEC-54 双批准全量落地）：M16 LN 逻辑节点编排 + M17 PDM 批（pcm16 全量 + 驱动 bring-up 半程如实）——V0.4.0 两停门项处置完毕**。M16 = Q-35 方案 A 兑现（lno.py 扇出/聚合/组恢复 + MCP 六工具 + 双 FakeCube 测试；固件零改动 + V1 合同不变）；M17 = pcm16 格式面六面全量（顺带拦 boot_av_set 跨 entry 泄漏与 L5 时基两真缺陷）+ TS_DRV_PDM 驱动骨架/pdmbench（bring-up 8 轮：挂死根因定案〔rx_reset 清时钟使能〕+ 寄存器 dump 达成，**时钟链不出——待逻辑分析仪/IDF 差分，观察项**）。回归终态：twister 15/15（92）/agent 125+2s/L5 6/6/repo 2。**下一版本候选：多真机拓扑 LN 验证（需第二块 cube）/ PDM 时钟链仪器差分 / V2 级纵深（真多线程批 / D-AV 纵深）——随 owner 点向**
- **2026-10-13（九十一） · V0.4.0「语义扩展批」收口（tag fw-v0.4.0）：15 单元 = 13 交付 + 2 呈递停门——V1→V2 语义跨越落地（多 APP 并行真机点亮）**。交付：F1 三批（存储 meta v2/槽池 → rt[N] 运行时 → 寻址+**真机双 APP MA PASS**）+ F3 日志面（IR-16）+ M3 定性/health_ping 语义门 + M4 caps 硬校验（IR-17）+ F6 输入中断（DR-02）+ M8 threads 申报制（Q-33）+ M9 kv 状态持久化（DR-15）+ M10 push_prov（Q-34 A+）+ M11 丢失资产重建（tools/board 回归）+ M12 接缝价值裁剪（t_window IR-18 收口 + HTTP 门面；ACP/A2A 预留）。停门（V0.4.x 补批）：M13 逻辑节点（**Q-35**：建议 A = Agent 侧编排——固件零改动+合同不变）/ M14 PDM（**Q-36**：av pcm16 + TS_DRV_PDM 路径在档）。回归终态：twister 15/15（92）/agent 119+2s/L5 6/6/repo 2。**待 owner：Q-35/Q-36 裁决（批准即开补批）；下一版本候选随裁决定**
- **2026-10-12（九十） · V0.4.0 语义扩展批连续开发：M3-M7c 七单元交付（F1 多 APP 并行真机点亮 = V2 核心语义里程碑）**——M3 LLM APP 死亡定案+health_ping 语义门/M4 caps 硬预校验（IR-17）/M5 输入中断驱动（DR-02，ISR 纯净钩子）/M6 存储面（槽池+meta v2+v1 迁移+per-entry 状态机）/M7 运行时并行（rt[N]+模块缓存数组化〔怪癖第四型〕+分账+广播+双实例 sim 测试，内存账 ~150KB/实例）/M7b 寻址（v2 信封 app 字段+apps 全景视图+Agent 同步）/M7c 真机（deploybench 槽池 4+512KB 池，双 APP 部署 slot1/3、双 ACTIVE、双流全判据 = **MA PASS**，证据 docs/evidence/ma_PASS_console.txt）。回归基线：twister 15/15（84）/agent 117+2s/L5 6/6。**余项：M8 threads/M9 状态持久化/M10 push_prov/M11 D-AV 消费端+ota/M12 接缝包/M13 逻辑节点/M14 PDM/M15 收口 tag fw-v0.4.0**
- **2026-10-12（八十九） · V0.4.0「语义扩展批」开工（owner 裁决全量范围 = 调研 F1-F7 + A1-A8 + 质量债，F8 除外）+ M1/M2 双单元交付**：M1 = F1 多 APP 设计批（**Q-32 呈递停门**——六子项含每 APP 双槽乒乓保留/TEST 包延续性/fs_paths 收口，现状五面实测为据）；M2 = F3 日志面真实化（log 权限类 fail-closed + 全局窗口限速 TS_LOG_RATE_PER_S + 唯一日志路径 + TEST 自动授予——历史包零重打包）。twister 15/15（81，+1）/L5/agent 113 全绿。排期 = plan §11（M1-M15）。**待 owner：Q-32 裁决（批准后 M6/M7 实现批开工；M3-M5 小单元可先行）**
- **2026-10-12（八十八） · V3-2 交付 + V0.3.0 收口（tag fw-v0.3.0）：板级全量复验双 PASS（auditbench AB PASS 留存 4+新增 2=6 与存档逐字段一致 / deploybench D8 PASS 三版本生命周期 + 健康回滚 + rollback_count=1）——新环境板级回归基线完整恢复**；首跑 AB FAIL 定性 = 抓取 RTS 复位干扰（观测纪律：自复位 bench 禁外部复位）；D8 三包在仓（agent/demos/D8）丢失脚本零影响。V0.3.0 终态 = V3-1（生产 app flash 面）+ V3-2（板级复验）。**下一版本候选：V2 级语义项预研（多 APP 并行/逻辑节点并联——设计批 + 门③）/ 上游平移批（等 v4.5.0 正式版，未发布实证）/ D-AV 产品化纵深**
- **2026-10-12（八十七） · V0.3.0 批开工 + V3-1 交付（生产 app flash 面接入——V2-2 既定待办收口）**：生产 app 增 ts 六分区 overlay + TS_STORE/FLASH/AUDIT 接入（板级片段承载 flash 面，native_sim RAM 后端可移植）；验证 = 双构建绿 + twister 15/15 全过（零失败）+ **真机 `[audit] flash 环空` 挂载实证**；tools/board 脚本丢失结案（按需重写——本会话已重建 console_smoke/fetch_blobs/nvd_demo 三件）。**迁移状态：全部完成（owner 确认）**。下一单元：V3-2 板级全量复验（auditbench/deploybench 双 bench 新环境跑通）**
- **2026-10-12（八十六） · 新机器全链 NVD PASS（迁移后「需求→真 LLM 生成→zenoh 部署→真机判据」首次完整重现）**：板接入（dialout chmod 绕行 + root 授权在会话记忆）→ deploybench 烧录上线（WiFi 3.8s + zenoh CONNECTED 本机 9955）→ 四节 spec → MiniMax-M3 生成（543B wasm + 1460B TSAP）→ 无线部署激活 → 真机 `NVD DONE ticks=10` 第 22 行精确命中 + DB6 slot=1 运行 = **NVD PASS**（证据 docs/evidence/nvd_PASS_console_native.txt）；顺带安全链真机演示（APP 死亡→健康检测→回滚拒翻→板存活合同 6）；过程四坑入册（zenoh-pico config.h 剥离范围修正/blobs 挂起根治脚本/prov 路由字节级派生/agent config 重建）。观察项新增：LLM APP DONE 后死亡（与 SYWORK wdt 不同型）。**迁移验证清单至此全项达成**
- **2026-10-11（八十五） · 原生 x86 Linux 环境重建批交付（迁移后首个会话，owner 指令）：migration-x86 §2 六步全部完成——west 工作区 v4.5.0-rc1（浅取 narrow 8.3G + requirements + esptool 5.4.0 + blobs）/ SDK 1.0.1（esp32s3 + hosttools，gnu/ 新布局）/ WAMR 2.4.5 + version.h 444 / agent-venv（Python 3.14.4 实证兼容）/ zenohd 1.10.1。验证：agent 113+2s + ruff / repo pytest 2 / 板级构建 xiao_esp32s3 生产 app 全绿；twister 15/15 补验 PASS（owner 装工具链后 43.94s）。无 sudo 全用户态手法入册 dev-environment §9（新事实源：FlClash 7890 + ghfast 镜像 + clang 18.1.8 tarball + deb 解包编译 C 扩展）。**重大发现：tools/board 34 脚本从未实际入仓（b1a31e4 三处登记失实）——owner 迁移包恢复待办**；上游 v4.5.0 正式版未发布实证（平移批挂上游时机）**
- **2026-10-11（八十四） · V2-2 交付（V0.2.x 补批 · DEC-52①）：审计 flash 持久化——store/audit.c 两页乒乓环（8KB；实现修正登记：翻页代单条覆盖/仅异常类落盘）+ commit/estop 异常下沉 + boot 留存报告 + sys/get-audit flash 读取 + auditbench 真机 AB PASS 两轮（seq 1..12 连续、复位留存实证）；twister 15/15（80）/L5/agent 113 全绿；顺带拦下两真缺陷（res u8 截断/4KB 栈数组爆栈）；WAMR version.h 竞态第三次复发已处置；待办 = 生产 app flash 面接入。V0.2.0 四单元全部完成**
- **2026-10-11（八十三） · V2-3 交付 + V0.2.0 收口（tag fw-v0.2.0）：sim APP 装载面（replay test_90_nv1_app_load + embed 真机同包）+ simreal_diff 首基线达成——NV1 判据行 sim↔real 逐行严格全等（7=7，确定性合同双域机械实证）；twister 15/15（78）/agent 113/ruff 全绿。V0.2.0 终态：V2-1（D-AV DA PASS）/V2-3/V2-4 交付 + V2-2（审计持久化）Q-31 停门维持待 owner 裁决（裁决后随 V0.2.x 补批）。下一版本候选：上游 issue（zenoh-pico 大 payload/#121774 回帖）、v4.5.0 正式平移 + workaround 回收、V2 级语义项（多 APP 并行/逻辑节点并联）**
- **2026-10-11（八十二） · V2-4 交付（V0.2.0 单元 4/4 可执行项）：spec 附属证据强化（提示词注入全部判据/附属串 + repair_loop evidence_hits/missing 统计）；CI 漏步教训修正（NV-3 红定性改 sync_check 漏跑——两次同型事故，提交流固定 --update）。V0.2.0 余项：V2-3 sim APP 面（固件面下一会话单元）+ V2-2 停门（Q-31）+ 收口 tag**
- **2026-10-11（八十一） · V2-1 交付（V0.2.0 单元 1/4，超预期）：D-AV 全链打通 DA PASS——采集自愈（#121774 workaround：超时计数→流重启→帧恢复真机实证）+ 发送层根治（我方 zenoh glue use-after-overwrite：static_buf 别名 × pubq/avq 环形槽覆盖 → 拷贝语义修复；64B 档 1843 chunks 零损坏 + 2 帧完整重组）；上游"1KB 损坏"定性修正 = 我方竞争 + 上游大 payload 双缺陷（64B 档定版绕行，256B 档证伪弃用）；twister 15/15（77）/agent 109/repo 2/2 全绿。V2-2 停门维持，V2-3 sim APP 面随续**
- **2026-10-11（八十） · owner 裁决 V0.2.0「视频链解锁批」开工（plan §9）：V2-1 D-AV 宿主采集自愈 workaround（av.c 超时→stop/start 重启——上游 #121774 维护者定性 DMA re-arm 缺陷且确认 stop/start 有效，我方源码核实）+ 256B 发送档验证→DA PASS 尝试 / V2-2 审计持久化〔Q-31 停门维持〕 / V2-3 sim APP 装载面 + 对拍首基线 / V2-4 spec 附属证据强化；目标 tag fw-v0.2.0；上游回帖草稿待 owner 确认**
- **2026-10-11（七十九） · NV-6 交付 + V0.1.0 版本收口（tag fw-v0.1.0）：真实需求（健康哨兵）全流程编程测试 round1 pass——spec 门判据派生 → 真 LLM 生成 → repair_loop 部署 → 真机 "HBS DONE ticks=20" 精确命中 + DB PASS（NV-1/2/3 产物全链真机首消费）；gate 自举两修正（任意位置标记/主判据概念）；sim 首基线如实顺延（sim APP 装载面缺口——后续增强批）；NV-4 Q-31 维持停门待 owner。V0.1.0 六单元终态：NV-1/2/3/5/6 交付 + NV-4 呈递停门**
- **2026-10-11（七十八） · NV-5 交付（V0.1.0 单元 5/6）：根 README 门面（项目一句话/架构图/快速上手三命令/demo 一览/CI 徽章）；Q-31（审计持久化三选项——建议独立 4KB 分区 64 槽定长环）已呈递停门待 owner。NV-6 版本验收（真实需求全流程）随续——NV-4 逾时未裁顺延**
- **2026-10-11（七十七） · NV-3 交付（V0.1.0 单元 3/6）：sim↔real 语义对拍工具（写序列终态↔判据行读数键值 diff；D9 双证据机械化）+ simreal_diff MCP；pytest 108+2s；首基线随 NV-6 验收链产生。NV-4 审计持久化 Q-31 呈递门随续（逾时未裁顺延，NV-5 README 先行）**
- **2026-10-11（七十六） · NV-2 交付（V0.1.0 单元 2/6）：spec 质量门——四节模板 + 【判据】节引号串机读派生（repair_loop pass_patterns 单一事实源，NV-1 手写双份风险收口）+ app_develop 入口分级集成（errors 阻塞/旧式兼容）+ spec_check MCP + workflow skill 模板节；pytest 103+2s/ruff 绿；真机消费面归 NV-6 验收。NV-3 sim↔real 对拍随续**
- **2026-10-11（七十五） · NV-1 交付（V0.1.0 单元 1/6）：部署后诊断闭环——tools_diag 三模块（7 类失败分类器 + 串口抓取 + 修复闭环编排）+ app_develop repair_feedback + diag_classify MCP；真机单迹 round1 pass（真 LLM 生成→部署→NV1 DONE 精确判据）；顺带根治 app_deploy 暖复位竞态（30s 板回轮询）与 manifest 伪影级联解包（MD1.1 族完备化）；agent 92+2s/ruff 绿；观察项 = SYWORK 源 wdt 偶发复位（登记不动手）。NV-2 spec 质量门随续**
- **2026-10-11（七十四） · owner 裁决版本方向：下一版本 V0.1.0 = 编程链路完整性批（plan §9 排期 NV-1 诊断闭环 / NV-2 spec 质量门 / NV-3 sim↔real 对拍 / NV-4 审计持久化〔Q-31 呈递门，逾时顺延〕 / NV-5 README / NV-6 真实需求全流程编程测试〔版本验收〕）；收口 = tag fw-v0.1.0；连续开发启动——规划批已落盘，NV-1 随续**
- **2026-10-11（七十三） · 批 A 收口：owner 换 SD 卡后 dsdbench DS PASS 全链一次过（挂载/安装/APP ACTIVE/回读 n=68/白名单拒绝物理证据/列目录）——批 A 11/11 全绿定格（S3 全 bench @4.5.0-rc1 真机基线完整恢复；impl-review-03 R1 处置完成）；前两提交已定案 boardbench（BB PASS——BB1 = 指令配额 BUSY_ITERS 30000 定参）与 SD 旧卡坏卡（换卡即愈）；教训 33 转正（ts-prov 换烧必擦）；后续候选 = 上游 #121767/#121774 回复 / v4.5.0 正式平移 / 批 C 产品化（owner 未裁）**
- **2026-10-10（七十二） · 批 A 续：otabench 全链 PASS（img-ver 2.0.0 swap——4.5 mcumgr img API 适配定案）+ estop/periph/psram/meta/wdt 五件 PASS——批 A 主体收口（9 绿 + 2 遗留：boardbench BB1 evt 链、dsdbench fatfs/SDMMC 4.5 适配）；safety.h estop 声明存量缺陷修复（真机 estop 面首次被构建覆盖）**
- **2026-10-10（七十一） · 批 A 首批：netbench/linkdemo/deploybench（DB+D8 双证）@4.5 真机 PASS + otabench 半程（SMP 上传链绿，swap 待查）；netbench 池 153600 调档；ts-prov 覆盖第三坑登记；批 A 续 = otabench swap + 小 bench 七件**
- **2026-10-10（七十） · issue #121774（esp32 video 停摆）提交 + impl-review-03 呈 owner：会话 8 提交审查全通过（证据齐全/缺陷自报）；风险 R1（S3 真机回归覆盖不全——deploybench/otabench/netbench 等 @4.5 未复跑）为最高优先；下一步候选批 A（S3 全 bench @4.5 真机回归）建议优先，批 C（产品化新方向）待 owner 裁决**
- **2026-10-10（六十九d） · D-AV 采集执行 + 新缺陷定案：owner 摄像头修复后帧已可采发（prov 覆盖根因亦修复）；主阻塞更新 = 4.5 下 zenoh-pico 板→路由 1KB 发送 100% 损坏（板侧 crc 正确/自环 20 无损/尺寸相关/4.4 曾通——4.5 回归，upstream 域，与 #121767 关联观察）**
- **2026-10-10（六十九c） · D-AV @4.5 复测：S3=sense 版确认（stream started 实证）+ avdemo @4.5 首构建绿（池 94208）+ dav_recv 采集执行——零帧与 DAV1 同象（非 4.5 回归；收口条件维持 = owner 摄像头排线物理动作，方法持续有效）**
- **2026-10-10（六十九b） · Zephyr upstream issue 提交：zephyrproject-rtos/zephyr#121767（esp_hosted 控制面通/数据面挂——P4 无线面缺陷上报，owner 授权 gh 提交）；上游回复后 P4 无线面复测为外部跟踪项**
- **2026-10-10（六十九） · DEC-51（板卡集收缩 S3-only——P4/H7 搁置留档）+ persistbench S3 @4.5 真机复验 PASS（板级遗留项收口）：4.5 帧深致 verify 链 4096 栈挂死——修复 + 全 S3 bench 批量防御 8192；Zephyr esp_hosted 上游 issue 起草并提交（owner 授权）**
  - 两诊断坑登记：esptool 操作尾部 hard-reset 触发首启秒写回（判据编排须 --after no_reset）；WAMR version.h 只读屏障曾被解除→并发竞争复燃（444 已恢复）。
  - 回归 15/15（77）+ pytest 2/2；S3 = 唯一真机目标（7-4 常接）。
- **2026-10-10（六十八） · P4 无线面批交付（半程 + 上游缺陷定案）：C6 伴芯固件链落地（esp-hosted-mcu v3.0.9 @ owner Windows EIM/IDF v6.1 + STREAM datapath 定值）+ P4 侧 esp_hosted RPC 全通真机证据（版本握手 v3.0.9/wifi_connect rc=0/associated 3/3 + C6 侧独立证据）；NB 全链判据挂起 = Zephyr 4.5 esp_hosted 驱动数据面缺陷（UDP/TCP 帧不通——DHCP 3/3 挂），上游域**
  - 顺带修两存量缺陷：zenoh-pico version.h 包含域（生成头包含域提模块级）+ 无 WAMR 面 appmgr 符号桩；回归 15/15（77）+ pytest 2/2。
  - 后续：上游 issue 呈递候选（owner 裁决）；P4 真外设绑定待开；H7 真机待 ST-LINK。
- **2026-10-10（六十七） · P4 PSRAM 挂接批交付：p4psram 真机全链 PASS（P4P1 SMH 探针 0x48000060 读写一致 → WAMR 256KB 堆自 PSRAM 分配 → APP 全链 → P4P PASS）——board-p4-01 §7 第二项收口；H7 真机暂停（owner 暂无 ST-LINK，构建级已交付待器件）**
  - P4 SPIRAM = HEX 16 线（P4 专属 Kconfig 默认）；堆 256KB = S3 同值（DEC-27）；回归 twister 15/15（77）+ pytest 2/2。
  - P4 板余项：无线面（C6 伴芯 esp-hosted）/真外设绑定；D-AV 帧证据（待 owner 摄像头动作）。
- **2026-10-10（六十六） · H7 移植批（构建级）交付：板裁决落地（owner：mini_stm32h743 = WeAct MiniSTM32H743 核心板，树内目标）——h7bench 构建绿（FLASH 158KB/7.6%、sram0 349KB/68% 含 256KB WAMR 堆）+ WAMR THUMBV7EM 映射 + 五分区 128KB 扇区模式 + 回归 15/15（77）；真机判据待 owner 接板（ST-LINK + USART1，board-h7-01 §6 预案含 HSE 晶振疑点）**
  - DEC-28 板卡目标集（S3→P4→H7）第三板开题即构建级绿；WAMR 三 ISA（xtensa/riscv32/thumbv7em）全数过编译。
  - 真机收口后 H7 批完整退出；WAMR 堆迁 D2 SRAM / ETH 网面评估 = 后续批。
- **2026-10-10（六十五） · P4 适配批交付：ESP32-P4-WIFI6-DEV-KIT（Waveshare）框架 bring-up 真机全链 PASS（p4bench：prov→v2 包安装→暖复位→flash 全状态自举→WAMR@RV32 ACTIVE→写链→P4B PASS）——排期表 A–J 全部收口**
  - 板面：目标 = esp32p4_wifi6_dev_kit/esp32p4/hpcore（v4.5 斜杠限定语法）；SDK 补装 riscv64-zephyr-elf（setup.sh -t 单组件）；WAMR 板映射登记 RISCV32；五分区 @0x7E0000（16M 默认布局 slot1 区）；console 重指 uart0（CH343 COM 口 = esptool 同口，单线判据）；MAIN_STACK_SIZE=8192（RV32 帧深，4096 安装链实测溢出）。
  - 顺带修复存量缺陷两族（教训 31）：六 bench overlay 缺 mapped-partition 兼容串（avdemo/dsdbench/linkdemo/metabench/persistbench/wdtbench——升级批漏网）；persistbench 自构造包为 v1 格式（DEC-49② 后即坏）——gen_p4b_pkg.py 机械生成 v2 包（测试根签名），v1 构造器删除。
  - 回归全绿：twister 15/15（77）+ pytest 2/2 + persistbench S3 @rc1 构建绿；报告 docs/board-p4-01.md。
  - 剩余：P4 无线（C6 伴芯 esp-hosted）/PSRAM 挂接/真外设绑定（后续批）；D-AV 帧证据（摄像头硬件动作后一跑即收）；正式 v4.5.0 发布后平移 rc1。
- **2026-10-10（六十四） · DEC-50 升级批交付：Zephyr v4.5.0-rc1 已上——twister 15/15（77）/agent/L5/ruff 全绿 + inputdemo 真机复验核心判据绿（ID1a 寄存器级 duty/WAMR APP 运行/G4 槽切换/输入真值流）**
  - 仓库内适配三处（教训 30）：WAMR autoconf.h 包含域补 / 三 bench overlay 分区 mapped-partition 兼容串 + appcpu 冲突删 / deploybench 池再平 151552。zenoh-pico 1.10.1 + WAMR 2.4.5 钉版不动。
  - **P4 适配批下会话开**（ESP32-P4-WIFI6-DEV-KIT：板目标选取 + 框架 bring-up）。正式 v4.5.0 发布后平移。
  - 剩余：P4 适配批；D-AV 帧证据（摄像头硬件动作后一跑即收）。
- **2026-10-10（六十三） · D-AV 帧证据累计尝试（零帧——摄像头当晚彻底不出帧，硬件动作前不可收）；Q-30 状态：v4.5.0-rc1 已 tag、正式版未发——owner 裁决 A 后即开升级批**
- **2026-10-10（六十二） · DAV1 交付：根因定案 = 上游 esp32 video 驱动内摄像头 SCCB I2C 轮询忙等（APP 自旋于 native 内；avq/zenoh 排除——冻结先于任何发布）；L1 软看门狗防御链实证；诊断探针（WDT_WARN 栈转储）入仓为常设可观测性**
  - 排期表全部专项收口：A–J ✅/◐→**唯 Q-30 裁决在外**；D-AV PASS 判据条件 = 摄像头硬件稳定度（**owner 动作：Sense 板摄像头排线重插/抗扰**；上游 I2C 忙等零补丁纪律内登记）。
- **2026-10-10（六十） · G2 完整收口：MCUmgr OTA 全链真机 PASS（v1→上传 v2→perm swap→v2 运行）——单元 G 全绿；真凶四层定案（客户端双字节 + 板侧 smp_udp pre-IP 绑定修复入仓 + WSL mirrored 入站 UDP 缺陷 Windows 侧绕行；原防火墙诊断推翻）**
  - 剩余：Q-30 裁决（门⑤）→ 升级批 + P4 适配；D8 单跑 PASS 行（网络已平，可补跑）；DAV1 会话。
- **2026-10-09（五十九） · B2 批（查询面半）交付：「查询面停滞」根因定论 = agent 侧双缺陷（板/路由无责）+ rollback_count 随载恢复存量缺陷修复——twister 15/15（77）/agent/L5/ruff 全绿**
  - 根因（受控双向探针剥离）：zenoh locator 语法（tcp:// → tcp/ 归一化修复）+ Reply API 漂移（err_payload → err.payload + get 迭代排空）；环境放大器 = 暖复位后路由器陈旧 queryable 声明（NAT 拖死 TCP——教训 29.5；client 点对点直查兜底）。
  - rollback_count 随载恢复（flash 实测 1 vs 运行时 0 拦下；boot_start 装载路径修复 + test_04 断言）。
  - D8 各段双证齐（v1/v2 升级 G4/健康回滚 v2 复活 + count=1 对拍 ✓）；单跑 D8 PASS 行待网络平峰期（当晚 AP 关联 8→68s 劣化，如实登记）。DAV1 留独立会话。
  - 剩余：Q-30 裁决（门⑤）→ 升级批 + P4；DAV1 会话；G2 OTA（owner 防火墙）；D8 单跑行（网络平峰期一跑即收）。
- **2026-10-09（五十八） · 单元 J（评估半）交付：Zephyr 升级评估 + Q-30 呈递——门⑤停门等 owner**
  - 结论：v4.4.0 = 当前最新 stable（无落后）；**唯一硬驱动 = P4**（4.4.0 espressif HAL 无 esp32p4，不可移植；支持随 v4.5——main 已有 esp32p4/esp32p4x 双板）；zenoh 三方 1.10.1 已是上游最新（升级零联动）；qemu 元数据/DAV2 两缺口 main 未修（升级不解决，如实排除）。
  - Q-30（门⑤）：建议 A = 4.5 正式发布后即升（DEC-19 既定方向；升级批 1-2 会话——最大迁移项 Espressif 板 DT 重构〔PSRAM 声明〕+ native_sim TAP 转 DT）；B = 等 4.6 LTS4（P4 冻结 + EOL 零裕量）；C = 不动（违 DEC-19）。附 P4 采购硅版本裁决点（v3.x 刷新 vs v1.3）。
  - **禁区：Q-30 裁决前不动技术栈。** 评估底稿 = docs/zephyr-upgrade-eval-01.md。
  - 剩余：B2（DAV1 + 查询面停滞）+ G2 OTA 上传（owner 防火墙）+ D8 clean-pass（随 B2）。
- **2026-10-09（五十七） · 单元 I（MD2）：D9 全链 PASS + D8 ~90%（查询面停滞新发现）——twister 15/15（77）/agent/L5/ruff 全绿**
  - D9：sim（输入文件接口首批真消费者）+ 真机断链时间线全绿（armed 349‰→断链 block+硬件 0%→恢复 D9-DONE + evt×26 合同 3 证据）；LEDC 0% 特例/S3 位序 = 教训 29。
  - D8：三版本生命周期链路全证（部署/升级【G4 激活即停真机首证】/健康回滚/v2 复活 + hb 心跳后 rc=0 真落驱动）；**拦下 deploy.py v1 残留对拍公式（修复+测试）** + deploybench 内存重平（LOAD_MAX 4096/池 156672）。
  - 新登记（不动手）：健康回滚 WDT 竞态（verify 超 APPMGR 窗——呈递候选）；**查询面停滞**（长会话后 queryable 停响应——D8 唯一余项 clean-pass 受阻，B2 邻接）。
  - 剩余：J（Zephyr 升级评估 + P4，门⑤呈递）+ B2（DAV1 + 查询面停滞）；G2 OTA 上传仍待 owner 防火墙。
- **2026-10-09（五十六） · 单元 H（G4/G5）交付：单活跃 APP 语义收口 + 模拟器输入文件实装——twister 15/15（77 用例）/agent 77+2s/E2E/L5/ruff/板级构建全绿**
  - G4：activate 即停运行 APP（DR-14——旧撕裂态：meta 翻转后旧包继续运行；deploybench DB4 观测线程 = 该缺陷的板侧 workaround 佐证）；隔离拒载（rollback 第 4 次拒时持久化 meta.rollback_count = LIMIT+1 → boot 拒载 + 观测面 QUARANTINED——旧缺陷 = 每次上电重载已知坏包）。
  - G5：LLD-A04 §2「输入文件进」实装（M1 约定从未落地）——replay 脚本会话（link/estop/input/commit + JSONL 归并流）+ agent script_lines 映射（ch 命名空间：link/estop/in:N/rep_c/rep_d）；scenario schema v1 零变更。
  - WAMR 怪癖第三型（dev-env 教训 28）：进程内二次 boot_start 实例导出查找恒空（直调免疫；生产无暴露面——重载 = 暖复位）。
  - G2 维持 ◐：板活但 SMP UDP 回包仍被 Hyper-V 防火墙挡（owner UAC 一行待办不变）。
  - 剩余单元：I（MD2 混合 demo D8/D9）→ J（Zephyr 升级评估 + P4，门⑤）+ B2（DAV1 专项）。
- **2026-10-09（五十四） · G2 部分交付（MCUmgr OTA）：sysbuild+imgtool 签名+MCUboot 引导+真机 1.0.0 启动全链打通（647KB 签名镜像双 slot）；OTA 上传步骤待 owner 一行 UAC 开 Hyper-V 防火墙（WSL2 mirrored 入站 UDP 阻挡）；串口 SMP 在 S3 USB-JTAG 上不可用（平台限制登记）**
  - **待 owner**：管理员 PowerShell 运行 `New-NetFirewallHyperVRule -Name SMP -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol UDP -LocalPort Any -Action Allow` → 重跑 ota_client.py 即完成 OTA 全链（v1→upload v2→confirm→reset→v2）。
  - **下一单元（H）**：G4/G5——单活跃 APP 语义收口 + 模拟器深度增强。
- **2026-10-08（五十三） · G1 交付（单元 G 拆分·前半）：注册期 poweron 值落驱动——poweron_init 直写驱动（板级九遗留收口）；真机 ID1a 寄存器证据 299‰@want 300 OK + D4/D6 不回归；twister 15/15（74 用例）/agent/L5/ruff 全绿**
  - **下一单元（G2）**：MCUmgr 固件 OTA（DEC-23：mcuboot + 双 slot + SMP UDP + imgtool 签名 + PC 客户端 + 真机 OTA 全链——工作区 mcuboot 在位且 esp32s3 有板级支持；体量 1-2 会话）。
- **2026-10-08（五十二） · 输入面 G3 批交付（排期表单元 F）：input monitor ADC 真值化 + 事件→APP mailbox 路由 + IR2-06 根治（弃管升级替代 abort）+ estop 沿 prov 化 + ts_wdt_deactivate（DEC-48① 对称面，真机拦下）；D4/D6 demo 真机全链（真 LLM 一轮过：D4-DONE reports=8 / D6-DONE changes=6 / clamp rc=-12 限幅实证 / 滞回输出 rc=0 落驱动）；twister 15/15（73 用例）/agent/L5/ruff 全绿——**impl-review-02 高 3 + 中 8 全部清零**
  - **下一单元（G）**：板级余项批——注册期 poweron 值落驱动 + MCUmgr 固件 OTA（DEC-07/23 已裁未实现）。
- **2026-10-07（五十一） · MD1.2c 交付（排期表单元 E）：PDM 音频驱动扩展评估 = 缓办（docs/md12c-pdm-eval.md——技术路径可行〔esp32s3 i2s_ll PDM 寄存器层齐全 + 模块内驱动方案留档〕但 D 阶梯无音频消费者；重开触发四条件在档）——MD1.2 全子项收口（唯 h 的 DA PASS 待 B2）**
  - **下一单元（F）**：输入面 G3 批——input monitor→APP mailbox 路由 + D4/D6 输入 demo；并入 IR2-06（app_stop 持锁死锁面）+ estop 触发沿 prov 化。
- **2026-10-07（五十） · 验签实施批交付（排期表单元 D，DEC-49 落地 + IR2-07 并入）：TSAP v2 + 固件真 ed25519 验签（tweetnacl 809 行公版内置）+ TEST 语义收口（固定测试根）+ 回滚闭环（目标槽验签/暖复位重载/meta 双损如实）——**IR2-02 消账（最后高风险项）+ 生产部署链语义首次点亮**；twister 15/15（70 用例）/agent 76+2s/L5/ruff 全绿；真机 dsdbench DS PASS 全链复验（xtensa 首跑真验签）**
  - **过程三教训**（真机拦下留档）：tweetnacl m 出参不可与 sm 别名（验证前暂存写）；Sig_structure bstr 头按 payload 实长选；**net_wq/主栈 4096 被验签深度压穿**（EXCCAUSE 28 迟爆——net_wq→8192 + benches/生产 app 主栈 8192）。
  - **下一单元（E）**：MD1.2c——PDM 音频驱动扩展评估（hal_espressif i2s_pdm 组件接入，视方案定门）。
- **2026-10-07（四十九） · Q-29 呈递停门（排期表单元 C，门③）：IR2-02 根治方案四子项呈 owner——①固件真验签（建议内置极简 C ed25519 verify；PSA 作实施首查）②TSAP v2 头摘要字段（fmt_ver=2 + 32B sha256）③生产 prov 烧录通道（esptool 直写脚本）④TEST 语义收口（真验签 + 测试根）**；批准后单元 D 实施（并入 IR2-07 回滚闭环）**
  - **待 owner**：Q-29 裁决（decisions.md Q-29 全文：背景/选项/建议/影响——按建议或逐项例外）。
- **2026-10-07（四十八） · MD1.2h 部分交付（排期表单元 B，如实）：D-AV demo 链路 90%——真 LLM 一轮生成 PASS（demo.d.av rgb565 7046B）+ avdemo 载体入库 + 真机实证：安装/ACTIVE ✓、真帧捕获 ✓（cap r=0 len=38400）、分片发布 ✓（c=0..4 r=0）；**DA PASS 被 DAV1 阻塞（APP 线程无声冻结，3/3 复现——看门狗安全链按设计收口：APPMGR 逾期→system_fail→noinit 留痕 0x20001→task_wdt 复位）；DAV2 = 上游 esp32 DVP 无 JPEG 变长帧支持（pitch=0→零长 DMA），demo 走 DEC-47② RGB565 保底**；新增 B2 专项批（DAV1 调试）；CI/回归全绿（twister 15/15〔68〕/L5/pytest/ruff）**
  - **下一单元（C）**：Q-29 验签呈递批（门③ 停门）——TSAP 头摘要字段（文件格式变更）+ ed25519 真验签 + 生产 prov 烧录通道方案。
- **2026-10-07（四十七） · MD1.2g 交付（排期表单元 A，DEC-47③⑥）：ts-av + ts_net_publish 能力面——ts_av_capture 阻塞取帧 + ts_net_publish 分片发布（avq：chunk≤1KB/打拍 4ms/重试≤5×20ms 全 DEC-47② 值）+ av:read 权限类 + manifest av_fmt/av_w/av_h 三方同步（与 caps av: 互为充要）；并入复检发现②（fs_paths 长度对齐 pfx[68]+总长前置校验）与④（回归脚本 WAMR chmod 444 加固——并行全量 15/15 无竞态实证）；twister 15/15（68 用例，+2）/agent 76+2s/L5 6/6/ruff 全绿**
  - **架构落点**：hal/av.c（权限+配置绑定+官方池路径捕获；无摄像头板 TS_E_IO 如实）+ net/avq.c（APP 线程入队 / net_wq 单线程冲刷 = zenoh-pico 并发规避；信封 {fid,cid,n,crc32,d}；满队 BUSY 背压 + DOWN 自弃）；key = `…/av/<app_id>/frame`（数值 stream 防注入）。
  - **下一单元（B）**：MD1.2h——D-AV demo（OV2640 JPEG 硬件压缩 + 真 LLM 生成 APP + PC 侧帧重组消费端 + 真机判据）。
- **2026-10-07（四十六） · 规划批交付（owner 指令）：范围调整 + 计划 v1.30——硬件阶段三排除出开发范围；剩余全量单元重排 A…J 连续开发，每单元后汇报总/阶段进度；复检发现落点登记（IR2-07→D、IR2-06→F、fs_paths 对齐→A、ts_fs 边缘→impl-review-02 §8 附记）**
  - **排期表（plan §7 v1.30）**：A MD1.2g（ts-av+publish 面）→ B MD1.2h（D-AV demo）→ C 验签呈递（Q-29，门③停门）→ D 验签实施（并 IR2-07）→ E PDM 评估 → F 输入面 G3（并 IR2-06/estop 沿）→ G 板级余项（poweron/MCUmgr OTA）→ H G4/G5 → I MD2 → J Zephyr 升级+P4（门⑤停门）。
  - **下一单元（A）**：MD1.2g——ts_av_capture 最小面 + av 权限类 + ts_net_publish（打拍≥4ms=速率限制/chunk≤1KB/分片重试≤5×20ms——DEC-47② 值直用，无新 Q）+ kind/内存表/L5 同步 + agent 白名单/manifest/提示词 + 用例；并入 fs_paths 长度对齐。
- **2026-10-07（四十五） · MD1.2f 交付（排期表单元 5）：D-SD demo 真机全链 PASS——真 LLM 生成 ts-fs APP → Sense 板 SD 五步状态机 + 宿主独立复核双证据（n=68 内容验证 + deny 文件物理不存在）；真机首验抓出 fs_paths 绑定形态缺陷并根治；twister 15/15（66 用例）/agent 74+2s/L5 全绿**
  - **下一单元（排期表 6）**：MD1.2g——ts-av + ts_net_publish 能力面（DEC-47③⑥：ts_av_capture 最小面 + av 权限类 + publish native + 速率限制 + agent 同步 + 用例）。
- **2026-10-07（四十四） · MD1.2e 交付（排期表单元 4，DEC-47④⑤）：ts-fs 能力面——四 natives（无句柄）+ fs 权限类（list/read/write/delete op）+ fs_paths 前缀白名单（manifest/校验器/固件三方同步 + 前缀边界防绕过）；twister 15/15（66 用例）/agent 74+2s/L5 全绿**
  - **双层裁决 fail-closed**：class/op 位图 + fs_paths 白名单（未绑定=全拒；"/SD:/apps" 不授权 "/SD:/apps-secret"）；越权 PERM_DENIED 留痕；`TS_HAL_FS` 门控（默认 n；未使能构建拒收含 fs_paths 的 manifest）。
  - 真机 FAT 读写验证随 **MD1.2f（D-SD demo，下一单元）**：真 LLM 生成 + Sense 板真机判据。
- **2026-10-06（四十三） · PC 读面加固批交付（排期表单元 3，纯工程无 Q）：IR2-03 根治 + IR2-04/09/10/11 并入——agent pytest 74+2s/ruff/L5 6/6 全绿**
  - **五道门**：①`_gate_source` 拒绝一切 #include/__has_include（预处理读面封死——外泄链根除；放宽走门③）②`_read_within` 读面白名单（wasm/包路径须在 roots；密钥豁免=仓外密钥纪律）③max_bytes 服务端钳制 16384 ④zenoh key 段白名单 `[A-Za-z0-9._-]` ⑤clang Popen 进程组击杀 + 取消路径杀组 + 同 out_dir 互斥锁；L5 正则补裸 pwm_set（负样本无误报）。
  - **下一单元（排期表 4）**：MD1.2e——ts-fs 能力面（DEC-47④⑤：ts_fs 四 natives + fs 类 + fs_paths 白名单三方同步 + agent 白名单/manifest 同步 + 用例）。
- **2026-10-06（四十二） · 看门狗实施批交付（DEC-48 落地，排期表单元 2）：IR2-01 根治——四层防线全接线 + 真机三整循环自证；twister 15/15/L5/pytest 全绿**
  - **四层防线**：L1 三源喂狗接线（静态预注册+动态激活；SYWORK/NET/APPMGR 喂狗点）｜L2 WAMR 指令配额（metering 上游开关零补丁；超限异常走既有回滚）｜L3 task_wdt 通道（5s，NULL 回调→自动 sys_reboot）+ 硬件回退（esp32s3 wdt0，MWDT ≈10s）｜L4 noinit 留痕强实现 + system_fail→通道过期→复位闭环。
  - **真机（wdtbench，WB* 行）**：死循环 APP state=3→配额终止→state=4 回滚 rb=1 + 系统存活（WB PASS）；sysworkq 自旋→5s 复位（WB0 重现铁证）——75s 三整循环。限制如实：task_wdt 直通复位无 noinit 留痕（ISR 不可写 flash）。
  - **并入小项**：IR2-05（set_link/recover irq_lock 复查平移）+ IR2-08（commit_a actor 归因，hal 传 app_id）。
  - **下一单元（排期表 3）**：PC 读面加固批（IR2-03 根治 + L5 正则 IR2-04 并入；纯工程无 Q）。
- **2026-10-06（四十一） · Q-28 呈递停门（排期表单元 1）：看门狗接线批方案（IR2-01 根治）——四层防线 + 6 项新默认值，门 ① 等 owner 裁决**
  - **四层防线**：L1 ts_wdt 三源软看门狗（静态预注册+动态激活修复注册窗口冲突）→ L2 APP 执行边界 = WAMR 指令配额（`WAMR_BUILD_INSTRUCTION_METERING=1` 上游开关零补丁；超限异常走既有健康失败→回滚，无 abort 无死锁面）→ L3 Zephyr task_wdt + 硬件回退（esp32 MWDT，软巡检卡死兜底）→ L4 system_fail noinit 故障留痕（IR2-R6 同批）+ 停喂硬 WDT 真复位。
  - **建议默认值**：喂狗周期 SYWORK/NET/APPMGR = 1000/2000/1000ms；指令预算 init/tick/evt = 1M/200k/200k；TASK_WDT_MIN_TIMEOUT=5000 + FALLBACK_DELAY=5000（硬 WDT ≈10s，与 TS_HARD_WDT_CAP_MS 对齐）。
  - **待 owner**：Q-28 六子项裁决（①静态预注册 ②喂狗点 ③指令配额〔核心选型 A/B/C〕 ④task_wdt+回退 ⑤回归面 ⑥并入 IR2-05/08）。批准后单元 2 = 看门狗实施批。
- **2026-10-06（四十） · DEC-47（Q-27 裁决：六子项全部按建议值；上游 issue 暂不提）+ 计划修订批（v1.25 排期表建立）——MD1.2 实现批解锁**
  - **裁定**：①专用帧分片通道 ②1KB chunk/≥4ms 打拍/重试≤5×20ms/JPEG 优先 ③ts_av_capture 最小面 ④ts_fs 四函数 ⑤ts_perm_v1 新类 av/fs + fs_paths 白名单 ⑥同步面含 ts_net_publish 新 native。排期指令 = 审查债按推荐序 + MD1.2 实现批按 v1.25 §7 表。
  - **排期表（plan §7）**：1 看门狗呈递（Q-28，门①）→ 2 看门狗实施（并 IR2-05/08）→ 3 PC 读面加固（并 IR2-04）→ 4 MD1.2e ts-fs 面 → 5 MD1.2f D-SD demo → 6 MD1.2g ts-av+publish 面 → 7 MD1.2h D-AV demo → 8 验签呈递（Q-29，门③）→ 9 验签实施 → 10 MD1.2c PDM → 11 后续候选（MD2/G3 输入面/P4 门⑤/板级余项）。
  - **下一会话**：单元 1 = 看门狗接线批 Q-28 呈递（IR2-01 根治方案：三源喂狗/启动序/真机 task WDT 复位闭环/APP 执行边界选型——停门等裁）。
- **2026-10-06（三十九） · MD1.2d 呈递批交付：avbench 传输 spike 真机 PASS（AV PASS + PC 侧支持档 4/4 帧完整重组双绿）+ Q-27 呈递停门——六子项设计决策待 owner 裁决（门 ③：权限模型/公共 API/协议面）**
  - **实测四设计事实**（docs/av-transport-01.md）：①chunk ≤1KB 钉死（>2KB 走 zenoh-pico 碎片路径系统性失败——Z_BATCH_UNICAST_SIZE=2048 静态头不可覆盖）；②发送打拍 ≥4ms 必须（背靠背崩，z_put -100 errno=0）；③BLOCK 语义在 Zephyr 端背压下不保数据——分片级应用层重试（≤5×20ms）必须；④视频池 256KB 入 PSRAM + DVP DMA 接受 PSRAM 缓冲 + WiFi/zenoh/视频池三合一 DRAM 共存（系统堆 188416 档）。吞吐：1KB 档 172KB/s（QQVGA RGB565 ≈4.5fps；JPEG 提频在 Q-27②）。
  - **Q-27 六子项**（decisions.md，建议值齐）：①专用帧分片通道（A）②1KB/4ms/重试≤5×20ms/JPEG 优先 ③ts_av_capture 最小面（A）④ts_fs 四函数无句柄面（A）⑤ts_perm_v1 新类 av/fs + **fs_paths 路径前缀白名单字段**（A）⑥同步面（NATIVE_WHITELIST/manifest/L5/kind 注册表/内存表 + ts_net_publish 新 native）。
  - **待 owner**：Q-27 裁决（批准 → MD1.2 实现批：natives/权限类/分片通道 + D-AV/D-SD demo）；impl-review-02 处置排期仍待拍板（看门狗接线批→PC 读面加固→验签实装〔含 TSAP 头摘要=文件格式门③〕）。
  - 回归：repo pytest 2/L5 6/6/agent pytest 69+2s/ruff 全绿；avbench 为真机载体（无 twister 面）。
- **2026-10-06（三十八） · impl-review-02 交付：全库风险审查（owner 指令）——3 高/8 中/N 低登记（docs/impl-review-02.md，IR2-xx 编号族）；未裁决 Q = 零实证；零代码改动，处置建议呈 owner**
  - **高 3 项**：IR2-01 看门狗合同（合同 4）整体空转——WAMR 无执行边界/健康探针同线程/wdt 生产零注册零喂狗/注册窗口被 boot 序阻断/全库无硬件 WDT（system_fail 后永久挂死）；IR2-02 固件 COSE 验签结构桩——生产恒拒安装、TEST 放行任意未签名 wasm+自声明 caps（**当前全部真机验证均 TEST 语义，生产语义从未点亮**）；IR2-03 Agent PC 读面外泄链——#include 探读+stderr 回喂 LLM、wasm_path/key_path 读入路径不受 roots 白名单（白名单只管写出不管读入）。
  - **中 8 项**：L5 裸 pwm_set 正则盲区（IR2-04）/estop ISR 覆盖窗口（IR2-05）/app_stop 强杀持锁死锁（IR2-06）/回滚链不闭环+meta 双损静默（IR2-07）/审计 actor 恒 0（IR2-08）/任务取消不杀子进程组（IR2-09）/并发 out_dir 交叉污染（IR2-10）/zenoh key 注入（IR2-11）。
  - **正面实证**：写入路径唯一、六 native 权限 fail-closed 无绕过、**DEC-40/41/42 全部已实现**（此前疑未实现，审查澄清）、meta P1 修复在位、断链物理落值、密钥零泄漏复核；CI 四 job 绿（6a6e38c）。
  - **待 owner**：处置排期拍板（建议序：看门狗接线批〔含设计决策，门①呈递〕→ PC 读面加固批〔纯工程〕→ 验签实装批〔门③，TSAP 头摘要=文件格式〕→ 小项打包）；MD1.2d 呈递仍为既定下一单元，与上述的并行/调序由 owner 定。
- **2026-10-05（三十七） · MD1.2b 交付：OV2640 摄像头 bring-up 真机全链 PASS（CB PASS：QQVGA RGB565 ×4 帧真实捕获 + 首帧 38400B 落 SD 校验——与 MD1.2a 能力闭环）**
  - **路径事实**：外部静态 video_buffer 路径当前不可用（gdma "DMA capable: 0" 报错，根因未钉死留观察项）；**官方 video_buffer_aligned_alloc 池路径一次通**——V1 一律走池路径。Kconfig 门槛实测：DMA_ESP32_MAX_DESCRIPTOR_NUM 48 / VIDEO_BUFFER_POOL_HEAP_SIZE 256KB / NUM_MAX 6。
  - **MD1.2 余项**：MD1.2d（zenoh 视频帧分片传输 + ts-fs/ts-av natives/权限类扩展——门 ③ 呈递）；MD1.2c（PDM 音频驱动扩展评估）；D-SD/D-AV demo 随能力面。
- **2026-10-05（三十六） · DEC-46（Q-26 裁决：硬件即板载 Sense 版）+ MD1.2a 交付：SD 卡 bring-up 真机全链 PASS（7.5GB 卡 + FatFS + 32KB 写读校验）**；Zephyr 支持面钉死：摄像头 ✓（官方 Sense 板变体 + video_esp32_dvp + ov2640 全在树）、SD ✓（本批实证）、音频 PDM ✗（i2s_esp32 无 PDM，驱动扩展批）
  - **关键事实**：v4.4 树内官方 `xiao_esp32s3/esp32s3/procpu/sense` 板变体——摄像头+SD 的 DT 全就绪（OV2640 I2C@0x30 / lcd_cam DVP / spi2 CS21 SD 槽），换板名即点亮；sdbench 载体入库（教训：大缓冲禁上主栈）。
  - **MD1.2 切分**：b=cambench（OV2640 DVP 帧捕获 + JPEG）→ c=音频（PDM 驱动扩展评估呈递）→ d=zenoh 传输面（视频帧分片策略 + ts-fs/ts-av natives/权限类扩展走门 ③）。
  - **排期建议**：MD1.2b（cambench）→ MD1.2d-SD（ts-fs 能力面 + D-SD demo）→ MD1.2c/b-video（传输 + demo）。
- **2026-10-05（三十五） · MD1.1b 交付：P1 根治（meta 双副本读共享缓冲 bug，一行修复）+ metabench 受控复现载体入库 + 真机五 demo 全 PASS（MD1.1 完整收口）；twister 15/15/L5/pytest 全绿。**Q-26 已呈递：音视频传输 + SD 卡 demo（owner 指令）——xiao_esp32s3 无摄像头/麦克风/SD 座，需 owner 硬件（Sense 版/microSD SPI 模块）+ natives 权限类扩展（门 ③）**
  - **根因**：ts_store_meta_read 两次 read_rec 共用一个 data 缓冲——copy0 body 被 copy1 覆盖；选 copy0（s0>=s1）时返回旧内容。触发面 = 双副本皆有效且 copy0 较新（第 3/5/7… 次写后启动）= D3/D7 铁律的机制解释；板级五以来存在，2 轮测试从未覆盖。修复 = 分缓冲；sim 用例 2→6 轮堵口。
  - **过程修正**：appmgr staged 用例此前骑 bug（依赖陈旧读值）——补 store reset 显式基线；D3 判据两修（通道上限 1000Hz|700‰——打包域 hz 高位语义；audit 聚合采样）；D7 谓词放宽 state∈{3,4}。
  - **真机终态**：D1/D2/D3/D5/D7 全 PASS（D3 限幅 23 条 -12+700‰ 实证；D7 state=4 回滚确认）。
  - **待 owner**：Q-26 裁决（AV=A/B/C、SD=A/B——硬件确认 + 权限类扩展批准）；观察项 = watch 同槽重推不复位（五连部署序不受影响）。
- **2026-10-05（三十四） · MD1.1 部分交付（如实）：五 demo 真 LLM 生成全过（产物入仓）+ D1/D2/D5 真机判据 PASS（D1 含 res=0 全链首证：心跳→链路 ACTIVE→写落硬件）；**D3/D7 被 P1 缺陷阻塞**——连续激活写 meta copy0 的暖复位装载错位（3/3 复现铁律，物理 dump 证写落盘，逻辑审计无果，专项 MD1.1b）**
  - **基础设施三知识**：linkmon 判活 = host 心跳 publish（非 query——此前全盲区，md1_run3 心跳模板）；冷启装载 init 写必然落 SAFE 窗（行为写放 tick/evt）；audit 64 环/16 快照窗口。
  - **载体**：deploybench 并 PWM 通道（D3 限幅判据）+ 连续部署修复；app_develop 数组伪影三处解包 + 回路预算 4。
  - **下一步（建议序）**：**MD1.1b（P1 专项定位：copy0 模式受控复现 + ≥3 轮 meta sim 用例）** → 补 D3/D7 → MD1.2（D4/D6：ADC 通道入部署链 + D5 深化事件订阅面）。
- **2026-10-04（三十三） · G1 实现批交付（DEC-45 方案 A）：APP 代码生成链落地——SMOKE3 真 LLM 全链双轮贯通（"需求→设计→编程→打包"AI 全链首次打通）；pytest 69+2s/ruff 全绿；MD0 关闭、MD1 解锁**
  - **可靠性调研落地（owner 指令）**：Claude Code/Codex CLI/aider/Wink 调研 → 八条工程决策 R1-R8（docs/agent-codegen-reliability-01.md）——四道确定性门（编译→白名单面检查→尺寸→**双编译字节一致**）+ stderr 完整反馈回路 + 整文件再生 + 子进程时限/零执行/roots 白名单 + sha256/面报告入审计。
  - **实装**：wasm_build 模块（零依赖 wasm 面解析器 + compile_app_c）+ `app_compile` 工具（auto）+ app_develop source_c 扩展（链内编译并入反馈回路）+ CI agent-checks clang 保障；测试 +11（无静默 skip）。
  - **SMOKE3 ×2**：反馈回路 2 轮收敛；646B/456B 产物均合规；caps 精确最小权限。
  - **余项**：MD1 demo 阶梯 D1-D7（模型侧+代码生成侧已就绪）→ 板级十一~十四（S3 生产化）→ Zephyr 升级 + P4 → MD2 混合。
- **2026-10-04（三十二） · G1 仓外 spike 双 PASS + Q-25 已呈递（工具面门 ③，停门待裁）**：真 LLM（MiniMax-M3）写 APP C 源 → clang wasm32 **一轮编译通过**×2 轮（7.9s/12.6s，wasm 239/250B），导入面 ⊆ natives 白名单、导出面四回调齐；编译错误反馈回路模式与 MD0-1 同型。制成零依赖 wasm 面检查器（llvm-objdump-18 解析不了 strip 后 wasm——夹具对照校准）。**Q-25（decisions.md）**：新增 app_compile（auto 审批）+ app_develop 产物契约扩展（可选 source_c 字段，链内自动编译）——建议方案 A；B = 仅加工具不动高层链；C = LLM 直出 wasm（已排除）。**待 owner 裁决后进实现批。** 同批 CI 处置：native-build 间歇挂（#29；#28/#30 绿）——chmod 444 本地两种语义均 15/15 但 CI 偶发面未除尽（如实纠错），ffd50be 已补失败诊断转储，下次复发即可见真因。
- **2026-10-04（三十一） · MD0-1 交付：Agent 真实 LLM 冒烟双 PASS——app_develop 真实 LLM 全链首次贯通（MiniMax-M3 @ minimax anthropic 兼容端点，owner 提供 API + 1M 上下文指令）；G2 关闭；冒烟拦下三产品缺陷同批修复；pytest/ruff 全绿**
  - **冒烟**（docs/agent-llm-smoke-01.md）：SMOKE1 = pydantic-ai→minimax 结构化输出管道 PASS；SMOKE2 = spec→真实 LLM（skills 渐进披露 + read_skill）→DevelopOutcome→manifest 硬校验→签名打包→复验 **全链 PASS ×2 轮复现**（56.3s/29.6s）。LLM 产出质量超预期：caps 精确最小权限、test_plan 八条自带军规风格（重放/限幅/越权/断链/review 门）——skills 注入生效。
  - **三缺陷修复（均实证）**：① app_develop 缺输出上限（思考型模型耗尽 SDK 缺省——链路对真实端点开箱不可用；OUTPUT_MAX_TOKENS=16384）；② config 加载路径错（文档约定 agent/config.toml，代码找包内路径——配置从未能从文档位置加载）；③ manifest 硬校验无反馈回路（一次一个错整链报废——补错误反馈 + message_history 续跑回路〔预算 3〕+ caps 文法内联提示）。
  - **密钥纪律**：密钥仓外文件 600 权限 + env 注入；config.toml（gitignored）仅模型串；提交前 git grep 零泄漏验证。
  - **MD 批状态**：G2 关闭；G1（APP 代码生成链）= MD0 余项（门 ③）；demo 全链的模型侧就绪。
- **2026-10-02（三十） · owner 计划调整 + Agent demo 就绪度评估交付：H7 放弃 / P4 恢复（前置 Zephyr 升级 4.5+，门 ⑤）/ MD demo 批入计划（MD0-2，D1-D9 阶梯）——真实 LLM 调用从未实测（实证），app_develop 的 wasm 边界 = demo 最大缺口**
  - **计划调整（owner 指令，decisions 登记）**：H7 适配放弃（评估报告存档）；P4 适配恢复（动机 = APP 复杂性余量；v4.4.0 无 esp32p4 支持 → Zephyr 升级为硬前置）；新增 MD demo 批（功能完成后：MD0 前置补齐 → MD1 阶梯 D1-D7 → MD2 混合 D8/D9）。
  - **评估（docs/agent-demo-readiness-01.md，零代码改动）**：① **真实 LLM 调用从未实测**（全测试 FunctionModel / config.toml 未创建 / audit 零痕迹）——补测需 owner 提供模型（ollama 或 OpenAI-compatible 端点）；② 已就绪 = 部署链真机闭环 / 四回调+mailbox / natives×6 / clang wasm32 / 模拟器 L4 / skills 渐进披露；③ 缺口 = **G1 APP 代码生成不在 app_develop 链内**（LLM 只产 manifest，wasm 调用方提供——门 ③）/ G2 真实 LLM / G3 input monitor / G4 单活跃 APP / G5 模拟深度；④ 建议 MD0 的 LLM 冒烟提前（不等 P4）。
  - **排期序（修订）**：板级十一~十四（S3 生产化）→ Zephyr 升级 + P4 适配 → MD0-MD2。**待 owner**：① MD0 模型配置（ollama/端点）；② P4 实板（esp32p4_function_ev_board 等，升级评估后采购亦可）。
- **2026-10-02（二十九） · 板级十交付：Agent→真机完整部署 E2E 双轨首次闭环（DEPLOY PASS + DB PASS 双轮复现）——twister 15/15（65 用例）/L5 6/6/Agent pytest 58+2s 全绿；同批 owner 指令：P4 移植暂缓**
  - **链路**（deploybench DB* + client.py DEPLOY*，docs/board-deploy-01.md）：Agent 侧**复用 MA3.1 deploy 链本体**对真板：发现（get-info 自报 dbn/dbc）→ tsap_keygen/package（tsap_verify 真 ed25519）→ 租约闭环（DEC-41）→ **4×256B 分块上传**（idem + high_water）→ 容器事实对拍 → 激活（整槽 hash + meta 原子切换）→ 板自动暖复位 → **步骤 8 自 flash 装载 APP 运行（WAMR@PSRAM）** → 复位后 get-app 对拍 state=ACTIVE + app_id + slot 一致。
  - **两项存量缺陷修复（E2E 拦下）**：① 跨轨命名漂移——Agent `TsapManifest._EXPORTS_ALLOWED` = init/tick/evt（LLD §2 笔误漂移）而固件 runtime/夹具/LLD §4 三方均 `app_init/app_tick/app_evt`，白名单照漂移面 = 拒绝一切真包（env 门控 sim E2E 默认跳过掩盖）；白名单+三测试+LLD §2 对齐（LLD-ts-appmgr v0.5.1）。② get_info 惰性初始化打回装载结果——boot_start 成功不置 `initialized` → 首次观测读取把 ACTIVE 盲写回 STAGED + active_slot 不回填（槽位对拍必败）；成功路径补 initialized + active_slot=meta（v0.5.2）。
  - **过程留痕**：prov 手抄数组丢 6 字节（fail-closed 拦下，esptool 分区 dump 定位，改脚本机械生成+走查验证——教训 27：手抄二进制数组禁令）；换 bench 分区残留态 → 流程增 esptool erase_region；zenohd 后起会话自愈实证。
  - **板侧载体**：deploybench = WiFi glue（板级七定稿）+ prov flash 持久（板级五语义）+ 三合一内存（DEC-29 每板裁剪 TS_APP_LOAD_MAX 2048 / TS_SAFETY_MAX_CHANNELS 8，池 188416 不动，WAMR 堆 256KB@PSRAM，dram 99.81%）。
  - **余项（板级十一候选）**：生产 prov 烧录通道（esptool 直写 / Agent push_prov〔MA3〕）、注册期 poweron 落驱动、input monitor 真输入、MCUmgr 固件 OTA、Zephyr 升级评估、H7 移植；**P4 暂缓（owner 指令随批登记）**。观察项：固件侧 COSE 验签 = V1 结构级（真验签在 Agent 侧）；"激活即热装载"留待加载周期批次；gated 测试周期复跑（testing.md 维护项登记）。
- **2026-10-02（二十八） · 板级九交付：PWM/ADC 真驱动（ts-periph dispatch 板级后端）真机全链 PASS——twister 15/15（65 用例）/L5 6/6/Agent pytest 58+2s 全绿**
  - **后端**：`CONFIG_TS_DRV_PWM`（driver_dispatch.c = L5 白名单内；zephyr,user 绑定 pwm-uid+pwms 三元胞，LEDC 引脚路由经 pinctrl；失败进 `ts_drv_pwm_err_count` 观测计数〔真机全程 0〕）+ `CONFIG_TS_DRV_ADC`（hal/api.c 输入面——合同 3 输入直读不经保护层；zephyr,user adc-uid+io-channels = 官方文档示例模式；12bit/内部基准/12dB 衰减，mV = 通用换算 1100mV 口径〔esp32 驱动 raw 预补偿：eFuse 校准+衰减反归一〕，读失败如实 TS_E_IO）。
  - **安全层存量欠账修复（bench 拦下）**：① `set_link(false)` 断链迁移此前**仅改 shadow** = 物理输出滞留断链前值（HLD §4.5-S2 原文"声明值落驱动"欠账；fault 路径本就落驱动故 estop 真机未暴露）——修复 = 声明值经 ts_drivers 落驱动，DR-04 恢复不回写不变（真机 PP5 首证）；② Kconfig 结构缺陷：TS_POWER/TS_PERIPH 误嵌 `if TS_NET` 块（TS_NET=n 不可见）——endif 上移回归 depends TS_HAL 本位；③ `ts_pwm_set` hz 下界 100Hz（打包粒度，V1 桩曾静默接受）。
  - **真机**（periphbench，PP* 行，docs/board-periph-01.md）：LEDC duty 寄存器六点 **±1‰**（含跨 hz 1000↔5000 重配 res 14↔13）/ 保护层限幅 900‰→700‰ **落硬件** + TS_E_RANGE / 端点 0%·100% 停止态 / **断链 fail-safe linkloss 0% 落驱动真机首证** + 恢复显式重写 / ADC 轨到轨注入 **0mV·3122mV**（3.3V 饱和；io_mux 注入 = estopbench 同型）。板级事实：LEDC duty 寄存器字段 = **ticks<<4**（hal ledc_ll 直证；reg 头部位域注释误导）。
  - **观察项登记**（报告 §5）：注册期 poweron 值落驱动未接线（V1 各板 poweron 与硬件缺省一致未暴露）；ADC 悬空保持残压（真部署需外部网络）；input monitor 真输入驱动未接（板级三既有登记）；LEDC 同 timer 多通道须同频。
  - **计划补账**：project-plan **v1.15**（板级行收口板级一~九 + §5 owner 待办清空——历史两项已落定）；文档：LLD-ts-safety v0.2.6 / LLD-ts-hal v0.2.2 / LLD-ts-periph v0.5 / dev-env v2.8 教训 26 / names 军规 6 撞名自查（periphbench PB*→PP*，persistbench 不受影响）。
  - **余项（板级十候选）**：生产 prov 烧录通道（esptool 直写 / Agent push_prov〔MA3〕）、**Agent→真机完整部署 E2E**（经 WiFi/zenoh 分块安装真机 APP——固件能力齐备）、注册期 poweron 落驱动；P4/H7 移植未启动。
- **2026-10-01（二十七） · 板级八交付：estop 绑定真机验证 PASS（硬件链路 ×3，合同 5 真机首证）——twister 15/15（65 用例）/L5/pytest 全绿**
  - **绑定机制修订**（上游事实）：v4.4 EDT 管道不发射非 zephyr 前缀 chosen 宏（dtlib 属性在、edtlib 弃）——改走 **aliases**（`DT_ALIAS(ts_estop_gpio)`），模块同步切换，DR-11 语义不变（LLD-ts-safety v0.2.5 + dev-env 教训 25）。
  - **真机**（estopbench，docs/board-estop-01.md）：引脚沿（io_mux 双使能注入 = 完整硬件路径）→ ISR 直达 → fault 落通道 **≤20ms** → 锁存 → clear+显式 commit 恢复，×3 轮；观测判据 = 通道三态 fault=true。如实记录：TS_EVT_ESTOP 补发属周期驱动接线（直启面未接，framework 测试已覆盖）；沿配置仍为上升沿占位（DR-11 prov 化待办）。
  - **回归**：twister 15/15（65）/L5 6/6（estop 调用图零违规）/pytest 2/2。
  - **余项（板级九候选）**：PWM/ADC 真驱动（ts-periph dispatch 板级后端）、生产 prov 烧录通道（esptool 直写 / Agent push_prov〔MA3〕）。
- **2026-10-01（二十六） · 板级七交付（owner 指令"其次 WiFi 重连"）：双断链全链自愈 4.2/9.2s（真机）——twister 15/15（65 用例）/L5/pytest 全绿**
  - **分层定稿**（board-reconnect-01 §1）：WiFi 关联 = glue（驱动无自动重连；固定 2s 无抖动 + 断线 DHCP 重启〔esp32 陈旧租约〕）；zenoh 会话 = ts-net 自带退避；检测加速 = **`ts_net_session_media_down()`**（僵尸 TCP 半开显式下沉——静默掉线时 is_up 分钟级才收敛）。
  - **两项框架修复**（三轮真机迭代实证）：① ts-net 周期体迁**专用工作队列**（sysworkq 被 zenoh 阻塞操作饿死，重试迟 18s；DEC-43 线程序 net=8>APP=10）；② netbench net_mgmt 回调重入自禁（回调内 net_mgmt = 事件 ~40ms 风暴）。
  - **真机**：NB-R 双断链自愈 9.2s/4.2s（快关联缓存生效）；zenoh 同进程 close→re-open 首次实证；恢复后 L1×30 零失败 p50 13.4ms。局限：真实 AP 断电未测（无 AP 控制）。
  - **回归**：twister 15/15（65）/L5 6/6/pytest 2/2。文档：board-reconnect-01 + LLD-ts-net v0.3.7 + dev-env 教训 24。
  - **余项（板级八候选）**：estop chosen overlay、PWM/ADC 真驱动、生产 prov 烧录通道（esptool 直写/Agent push_prov）。
- **2026-10-01（二十五） · 板级六交付（owner 指令"优先 PSRAM"）：WAMR 实例堆 256KB 入 PSRAM（DEC-27/HLD §4.6 兑现）——真机全链 PASS；twister 15/15（65 用例）/L5/pytest 全绿**
  - **两条事实修正**：①"Zephyr 4.4 无 psram 节点"评估有误（psram0@common.dtsi + N8R8 8MB；**八线须显式 SPIRAM_MODE_OCT**，默认 QUAD 即 esp_init_psram 硬停）；② WAMR-2.4.5 的 GLOBAL_HEAP_POOL 旗标无消费者——wasm_runtime_init() 实为系统分配器，"64KB 池基线"从未生效（板级二足迹数据与此一致）。
  - **实现**：runtime.c 统一显式池（wasm_runtime_full_init 注入堆缓冲；PSRAM = SMH_REG_ATTR_EXTERNAL 官方分配面 / 其余 = 内部静态池；零上游补丁）；Kconfig TS_APP_PSRAM_HEAP（默认 n）；**TS_APP_WAMR_HEAP 默认 65536→262144**（池模式下 64KB 结构性不可行——线性内存一页即 64KB，twister 实证拦截；HLD §4.6 注记 + LLD-ts-appmgr v0.5）。
  - **真机**（psrambench，docs/board-psram-01.md）：8MB 八线识别 + memtest OK；SMH 探针 0x3c030060 读写一致；WAMR 池 buf=0x3c030060@256KB；APP 全链 PASS。**量化对照**：PSRAM 开 = 内部 dram 38.8%；关 + 256KB = 溢出 14548B（目标内部装不下的硬证据）。生产 app 板 conf 升每板默认。
  - **回归**：twister 15/15（65）/L5 6/6/pytest 2/2 + 真机重刷复验 PASS。分层纪律结构面成立（仅 APP 沙箱入 SMH）。
  - **下一单元（板级七，owner 指令次优先）**：WiFi 重连策略；余项：estop chosen overlay、PWM/ADC 真驱动、生产 prov 烧录通道。
- **2026-09-28（二十四） · 板级五交付：prov/APP flash 持久化（真机全链 PASS）+ ts-store flash 后端入库——twister 15/15（65 用例）/L5/pytest 全绿**
  - **后端**：`CONFIG_TS_STORE_FLASH` + DT 五分区（ts_prov/meta/slot_a/slot_b/noinit，carved 自 espressif AMP 布局空闲 slot1 区——boot/sys/slot0 与 esptool 偏移零变化；fw_b 预留 = DEC-23 固件双 slot）；ops 增 erase_off、逐 4B 字"读-比-写"垫片（同值跳过幂等/位子集校验/仅抹除态编程）；分区缺失/尺寸错配 = 构建期失败。上层适配：meta 副本步距动态化 + 写前范围擦除；noinit one-shot 读清；`ts_store_slot_erase` API + stage_begin 安装前擦除；prov 注入一体单写（sim 程序一次语义拦下双写缺陷）；cbor_min 无条件编译（TS_NET=n 暴露的真实依赖）。LLD-ts-store v0.3 同步。
  - **真机验证**（persistbench 载体，docs/board-persist-01.md）：完整单迹 = PB1 首启烧录会话（prov 注入 + 440B TSAP 分步安装链 + activate + 暖复位）→ 复位后 prov/meta/slot 全出自 flash、APP 自 slot 装载运行 + evt 写路径全链 PASS。附带证据：跨固件重刷持久（west flash 不动分区）+ 中断会话一致性（半途复位 → step8 r=-7 不阻塞启动）。
  - **语义观察留痕**：冷启动 poweron_init 后通道处 SAFE_POWERON，APP app_init 期写被拒（TS_E_STATE）= 合同 1/3 预期（ACTIVE 迁移 = set_link，正常部署由 linkmon 驱动；TS_NET=y 无传输压 linkloss 亦真机观测正确生效）；无网面部署（TS_NET=n）由 glue 在 BOOT_DONE 后声明链路。
  - **回归**：framework.store.flash 新 CI 变体（native_sim sim-flash，EXPLICIT_ERASE 程序一次语义**比真机严格**）7/7；twister **15/15（65 用例）**/L5 6/6/pytest 2/2 全绿。API 口径：PARTITION_ID/SIZE 现行宏（FIXED_PARTITION_* v4.4 弃用，教训 22）。
  - **余项（板级六候选）**：estop chosen overlay、PSRAM 挂接（HLD §4.6，解锁 256KB WAMR 堆目标）、PWM/ADC 真驱动、WiFi 重连策略、生产 prov 烧录通道（esptool 直写 / Agent push_prov〔MA3〕）。
- **2026-09-27（二十三） · 板级四交付：WiFi+zenoh 命令往返实测（owner 指令）——上游 esp32s3 WiFi 打通；L1 全路径 p50≈12ms（省电关 5.5×）；L3 五验证点环境重建后复跑 PASS——twister 14/14（58 用例）/L5/pytest 全绿**
  - **链路**：xiao_esp32s3（WiFi "cemetery"）→ LAN → PC(192.168.2.90) → WSL mirrored zenohd@9955；客户端三层探针（L0 路由本机 0.10ms / **L1 sys 查询全路径 p50 12.0ms p95 28.6ms max 55ms 零失败** / L2 estop-clear p50 13.5ms），N=100×2 轮复现 <4%。
  - **关键发现**：① WiFi 省电是第一敏感项（默认 modem-sleep p50=66ms/max≈105ms≈DTIM；固件已默认关，5.5×改善）；② 判读：命令/Agent/API 级无感、断链窗占比 0.2%；闭环控制走板内路径（网络层 = 下发/遥测定位）；本地框架处理占比 <0.1%。
  - **载体入库**：firmware/tests/netbench/（板固件 + netbench_client.py）；**凭证零泄漏**（cmake 变量注入，git grep 验证）；prov 板上注入走 TS_TEST（RAM 后端，持久化 = 板级后续）。
  - **过程修复**：zenoh-pico 1.10.1 回调非 const（新工作区首编译即拦）→ **L3 五验证点复跑 PASS**（环境重建后首次，待办清账）；WSL mirrored LAN 入站 = Hyper-V 防火墙（owner UAC 放行一次）；WAMR version.cmake 并行竞态判明（非回归，单套件重跑绿）。
  - **余项（板级五）**：prov/APP 持久化（flash 分区）、estop chosen overlay、PSRAM 挂接、PWM/ADC 真驱动、WiFi 重连策略。
- **2026-09-27（二十二） · DEC-44（Q-24 → A）+ 板级三交付：真机 IO 延迟实测完成——判定"不过高"（两数量级裕量）；最小真 GPIO 后端入库（CONFIG_TS_DRV_GPIO）**
  - **DEC-44**：V1 双核终验以 native_sim 多核为准（不采购经典款；S3 SMP 降观察项）；同批 owner 指令 = 真机 IO 延迟确认。
  - **实测（board-bench-01 §1.5，三层对照，GPIO9 真寄存器）**：裸 `gpio_pin_set_dt` p50=204ns（~4.9MHz）/ 框架安全层 5.75µs（~174kHz；压测竞争下 p50/p95 **零变化**、max +66ns）/ 完整 wasm APP 路径 10.59µs（~94kHz）。**判定：不过高**——100Hz 输出更新占周期 0.058%（全路径 0.106%），两数量级裕量；位带式 >174kHz 协议走硬件外设通道（架构本意）；输入路径真驱动未接（板级待办）。
  - **入库物**：`CONFIG_TS_DRV_GPIO`（默认关；native_sim/CI 零影响）+ zephyr,user DT 绑定（uid 匹配通道）→ driver_dispatch.c（L5 白名单文件）真写 + sim 记录保留；L5 唯一写路径检查增 boardbench 裸基线豁免（对照层）；boardbench BB5 系列。
  - **过程教训（dev-env 20）**：`ZEPHYR_USER_NODE` 为 4.5 API（4.4 用 `DT_PATH(zephyr_user)`）；未定义宏在 DT 包装宏里字面拼接产生连环假象。
  - **回归**：twister 14/14（58 用例）/L5 6/6/pytest/native_sim bench 构建全绿。
  - **余项（板级四）**：RAM slot→flash 后端、estop chosen overlay、PSRAM 挂接（HLD §4.6）、PWM/ADC 真外设驱动。
- **2026-09-26（二十一） · 板级二交付：效率 DoD 真机实测完成（`docs/board-bench-01.md`）+ WAMR xtensa 可用性修复——twister 14/14（58 用例）/L5/pytest 全绿**
  - **六项数据（xiao_esp32s3 @240MHz 单核，fast-interp）**：① 解释器吞吐 1043ns/iter（vs native_sim 1.1ns）② native 往返净 ~3.5µs ③ 写路径端到端 9.7µs/call（安全层净 ~5.2µs）④ mailbox p50=28µs/max=34µs（n=300 零失败）⑤ 足迹 text 82-91KB@flash / bss 92-113KB / libc 堆余 ~218KB ⑥ 单核抢占并发（锁竞争 p95 不变、尾部 +12µs、estop 并发中生效+可恢复）；APP 冷启动 4.8ms。**结论：V1 效率预算充裕（报告 §2）。**
  - **载体**：`firmware/tests/boardbench/`（wasm 夹具 669B + 宿主 CCOUNT 计时 + 影子翻转检测；非 twister 独立应用，复跑 = 报告 §6）。
  - **WAMR xtensa 修复**：invokeNative 切官方汇编（`invokeNative_xtensa.s` + `-Wa,--noexecstack`；GENERAL C 版 xtensa 传参不可靠——模块 CMakeLists 按板分派）；runtime.c app_init 异常路径补 WAMR 异常文本 printk（失败可见性）。
  - **事实与呈递**：**ESP32-S3 在 Zephyr v4.4.0 无 SMP**（`arch_cpu_start` 缺失，构建实证；espressif 双核 = AMP 独立镜像）→ ⑥ 降级单核实测，**Q-24 已登记待 owner 裁决双核终验载体**（建议 A：native_sim 多核为准 + 跟进上游 SMP）。`k_cycle_get_64` 本板冻结 → CCOUNT（教训 19）；诊断插曲如实：三轮误诊（invokeNative/解释器/栈深）后定位为 bench 描述符别名 bug。
  - **下一单元（板级三）**：RAM slot→flash 后端、estop chosen overlay、PSRAM 挂接（HLD §4.6）、真 GPIO/外设驱动。
- **2026-09-26（二十） · 环境官方重建 + 板级 bring-up 达成：SDK 发现链根因钉死除根（Windows PATH interop）；工作区/SDK 按官方手册重建安装；xiao_esp32s3 交叉构建/烧录/console 冒烟全绿；效率 DoD 六项移交下一单元**
  - **根因（owner 指令"彻底解决"时钉死，dev-env 教训 15）**：WSL interop 把 Windows PATH 追加进 Linux PATH → cmake `find_package(Zephyr-sdk)` 前缀通配 + drvfs 大小写不敏感 → `/mnt/c` Windows SDK 劫持构建与 `west sdk` 双通道。**修复 = `/etc/wsl.conf [interop] appendWindowsPath=false` + `wsl --shutdown`**（教训 7/14 机制描述以此为准；显式 ZEPHYR_SDK_INSTALL_DIR 缓解不再需要）。
  - **官方重建（后续操作依托官方工具）**：apt 手册清单 → fresh venv → `west init --mr v4.4.0` + `west update` + `west zephyr-export` + `west packages pip --install`（esptool 5.4.0 官方接入）→ **SDK 1.0.1 = `west sdk install -t xtensa-espressif_esp32s3_zephyr-elf`**（@ `~/zephyr-sdk-1.0.1`，`west sdk list` 验证发现链无污染）；旧工作区（Windows 拷贝版 8.8G）已删。
  - **回归**：native_sim 构建 + twister **14/14（58 用例）×2**（picolibc 守卫前后各一轮）+ pytest + L5 全绿；zenoh-pico 原样回拷（1.10.1+config.h），L3 E2E 复跑待后续单元。
  - **板级（xiao_esp32s3）**：交叉构建绿（板级内存片段 `firmware/app/boards/xiao_esp32s3_esp32s3_procpu.conf`〔DEC-23/27：slot 32KB/宿主栈 16KB，PSRAM 挂接前过渡〕+ WAMR 垫片 picolibc 守卫〔esp32s3 默认 picolibc 自带 `__stdout_hook_install`〕；教训 17 三坑留痕）→ esptool 烧录绿 → **console 冒烟绿**（boot 全程 / step8 无 APP 不阻塞〔r=-7 如实上报〕/ prov 缺失安全回退 n-dev·c-dev）；足迹第一组数据：text 91KB@flash / 静态 bss 113KB / libc 堆余 218KB。
  - **下一单元（板级二）**：效率 DoD 六项（吞吐/陷出往返/写路径时延/mailbox 抖动/足迹对照/framework.conc 双核）+ RAM slot→flash 后端 + estop chosen overlay + PSRAM 挂接（HLD §4.6）。
- **2026-09-26（十九） · M2b.2 收尾单元交付——boot 步骤 8 slot 装载 + TS_APP_WAMR 默认 y + E2E 真夹具 wasm：twister 14/14（58 用例）全绿，M2b.2 全部完成；板级运行效率 DoD 六项固化（owner 指令）**
  - ts_appmgr_boot_start：active slot TSAP → manifest canonical 走查（未知键 fail-closed；caps ';' 组合；app_id/app_ver 提取；stack/heap_kb V1 消耗常量〔已知限制〕）→ wasm 装载（TS_APP_LOAD_MAX=16K）→ 运行 → STAGED→ACTIVE；boot 步骤 8 尾部追加（**APP 故障不阻塞启动** = 合同 6 显式例外）；framework.app test_04 全链（构造容器→分步安装→boot 装载→写 gpio→app_id 断言）。
  - E2E wasm 化：test_deploy_e2e 改用固件同源夹具 native_app.wasm（Agent 打包链与固件运行时同一工件）；mod_cache 复用改内容比较（boot 缓冲 vs 夹具两份拷贝）。
  - 过程修复（如实）：caps 分段末段越界（GCC UB 拦截）、manifest 键分支下标笔误（app_id 落 app_ver）、core 步骤守卫测试更新（新增步骤触发）。
  - **板级效率 DoD（plan v1.10）**：① 解释器吞吐（vs native_sim 1.1ns/迭代）② native 陷出往返 ③ 写路径端到端时延 ④ mailbox/tick 抖动 ⑤ 足迹对拍 HLD §4.6 ⑥ conc 双核终验。**下一步 = 板级移植（xiao_esp32s3：/dev/ttyACM0 已通、espressif 工具链就绪）**。
- **2026-09-26（十八） · 接线批第二单元交付（APP 运行时宿主 + natives，M2b.2a 核心）——twister 14/14（57 用例）全绿；板卡通道打通（usbipd → /dev/ttyACM0）**
  - runtime.c：每 APP 一框架线程（DEC-43 A，V1 单活跃）+ mailbox（DR-14 深度 8 满丢最旧）+ 停止语义（join 2s 强杀回收）+ 健康探针（连续 3 败自停 → health_fail 回滚入口）；Kconfig 常量全部 DEC-27 溯源。
  - natives.c：ts_api_v1 V1 子集（gpio/pwm/adc/time/log）；**ctx 经 exec_env user_data 注入防伪造**；权限裁决全经 ts-hal（PERM_DENIED 留痕 = 合同 10）。已知偏差 ①（全局注册→调用期裁决）与 ②（WAMR 模块生命周期怪癖 → mod_cache 进程级复用）登记 LLD-ts-appmgr v0.3 §7 + dev-env §5-12。
  - framework.app 3 用例：生命周期端到端（init 写经唯一写路径落 gpio/mailbox evt 驱动/stop 回收/重复停止拒绝）/ 权限拒绝（-3 + 事件留痕）/ 健康失败自停。夹具 wasm 286B（clang --allow-undefined 导入）。
  - 租约语义澄清（decisions 批次条目）：DEC-41 准入 = net 命令面（部署面已落）；natives 按 LLD-ts-hal §3 = 权限裁决。
  - **板级就绪**：xiao_esp32s3 经 usbipd 附加进 WSL（/dev/ttyACM0，dev-env §5-13 全流程）；espressif 工具链已装。
  - 余项（M2b.2 收尾单元）：boot 步骤 8 slot 装载接线 + TS_APP_WAMR 默认翻转 + Agent E2E wasm 化 → 之后板级移植。
- **2026-09-26（十七） · DEC-43 实现批交付（Q-23 裁定 A 后落地：锁收口 + 并发回归）——twister 13/13（54 用例）/L5 6/6/pytest×2/ruff/skills 全绿；板级前置就绪（xiao_esp32s3 + espressif 工具链）**
  - 裁决登记：Q-23 → **DEC-43**（方案 A + 实验数据版定位：锁收口随接线批顺带；板卡定为 **xiao_esp32s3** 真机双核终验——owner 已接入）。
  - 锁收口：commit.c 重构（write_lock/commit_locked 受控暴露）+ 迁移路径（set_link/force_channel_fault/channel_recover 双检/clear_fault）入互斥 + ts_power_request 检查-提交原子化（203ns TOCTOU 窗口消除）+ pubq 互斥（锁内出队/锁外发送）；**estop ISR 无锁直达不变（合同 5）**；锁序 write_lock→pubq 单向。
  - **framework.conc** 新套件（SMP+USE_SWITCH）：对齐双冲 0 超限（锁后硬保证）/迁移×提交不变量/pubq 会计闭合与序号单调。
  - 板级前置：espressif 工具链已装（west espressif install）；**WSL2 下 USB 串口不可见**（烧录策略随板级会话定：usbipd-win 或 Windows 侧 esptool）；文档 LLD-ts-safety v0.2.4/ts-power v0.2.1/ts-net v0.3.6。
  - 下一单元：**接线批第二单元**（appmgr 执行线程 + ts_* natives 挂接 + 写路径租约挂钩）→ 板级移植（xiao_esp32s3 起）。
- **2026-09-26（十六） · Q-23 实证批交付（owner 指令"先做 demo 实验用真实数据确认"）：framework.wamrdemo 4 用例全绿——B 方案饿死实证（基线 ~1.2ms → 同队 busy(1e8) 后 105-113ms，APP 时长全量转嫁，两轮复现）/ TOCTOU 窗口实测 203ns（4 核栅栏同步 4000 轮未碰撞——锁收口定位由"高危前置"修订为"接线批顺带"，真 SMP 板仍需）/ A 通路可用（专用线程+独立实例 10 轮完整，并发优越性受 native_sim 时间模型限制留板级验证）；时延画像（~1.1ns/wasm 迭代，busy(1e8)≈106-126ms）**
  - 实验环境要点（dev-env v1.7 §5-10/11）：native_sim SMP 需显式 USE_SWITCH（否则静默失效）；忙循环冻结模拟时钟——测量须宿主墙钟（显式声明 clock_gettime）；真实时间对齐 SLOWDOWN_TO_REAL_TIME（twister/TEST 默认关）。
  - 修订后建议呈递 decisions.md（Q-23 实验补充）：**维持方案 A**，锁收口随接线批一并落 + 并发压力回归用例 + S3 双核板级终验。**待 owner 裁定后开工接线批**（appmgr 执行线程 + ts_* natives + 租约挂钩）。
- **2026-09-26（十五） · M2b.2a 环境批交付（owner 指令"按照计划执行：M2b.2a"）：WAMR-2.4.5 钉版接入 + 样例 APP + framework.wamr 冒烟——twister 11/11（47 用例）/L5 6/6/pytest×2/ruff/skills 全绿；**Q-23 已登记待裁（接线批前置）****
  - WAMR 接入：源码钉版 `~/project/deps/wamr`（WAMR-2.4.5 tag，浅克隆 34MB，经 `TS_WAMR_DIR` 注入——仓库不含三方源码，zenoh-pico 同纪律）；模块构建配置按既有裁决落位（DEC-25 fast 解释器+WASI 全关+AOT/JIT 不启用；DEC-31 线程/共享内存编译期关；DEC-27 #10 池模式 + native_sim 堆 64KB=HLD §4.6）；`CONFIG_TS_APP_WAMR` 默认 n（接线批随 Q-23 裁定后翻转）。
  - 零上游补丁四要点（留痕 dev-env v1.6 §3）：① runtime_lib.cmake 目录级 include → `zephyr_include_directories` 传播 wasm_export.h；② WAMR 源码独立库 `tessera_wamr` + `-w`（ems_gc.c `GB` 与 Zephyr 单位宏撞名）；③ `WAMR_BUILD_INVOKE_NATIVE_GENERAL=1`（ia32 汇编缺 .note.GNU-stack）；④ `__stdout_hook_install` 兼容垫片（WAMR 平台层引用 Zephyr 已移除 API，wamr_compat.c 空实现）。
  - 样例 APP：`firmware/tests/wamr/app/`（clang wasm32 自由固件 103B，health_ping/on_input，build.sh 重建产物）；**framework.wamr** 冒烟 = 装载/零导入实例化（WASI 关边界活体证明）/调用/重放一致。
  - CI：native-build 增 WAMR 检出步骤 + TS_WAMR_DIR env；**下一步 = Q-23 裁定后接线批**（appmgr 执行线程 + ts_* natives 挂接 + 写路径租约挂钩 + 并发压力用例）。
- **2026-09-25（十四） · 远端上线 + CI 全绿 = M0 完整退出（DEC-24 落地）：`github.com/embalmer-Y/Tessera`（public）——main + 23 tag 已推；CI 四 job 全绿（repo-checks/l5-checks/agent-checks/native-build〔runner 上 twister 全量 10 套件〕）**
  - 过程：origin 更换（旧 origin 系 M0 迁移期指向 Windows 快照的本地路径）；合并 owner 建仓初始提交（LICENSE 附录占位符风格差异——保留本地 {yyyy} 版，法律文本等价）。
  - CI 首跑 native-build 失败，三轮定位（教训落盘 dev-env §5-7/8）：①bare runner 缺 Zephyr 主机构建依赖（apt 清单补齐）；②真因 = `ZEPHYR_TOOLCHAIN_VARIANT` 未设 → 探测 SDK → runner 无 SDK 致命——本地 WSL 曾被 Windows 侧 SDK 经 /mnt 环境互通掩盖（"Found host-tools: zephyr 1.0.1 (/mnt/c/…)"，编译器实为 host gcc）；修复 = 显式 `ZEPHYR_TOOLCHAIN_VARIANT=host`（本地同口径复验：构建 + twister 10/10〔46 用例〕全绿）。调试通路 = 失败时 CMake Error 首块注入注解（公开注解 API 可读，日志 API 需 admin；已留作常设设施）。
  - 代理新模式：owner TUN 级代理开启，`wsl --shutdown` 重启即自动生效（dev-env §5-9）——**M2b.2 的网络前置已就绪**。
  - 下一步（待 owner 点向）：**M2b.2**（WAMR + wasm 工具链，网络已通，开工即登记 F-7 并发方案 Q）或**板级移植**（前置 Zephyr SDK for Linux ~1GB）。
- **2026-09-25（十三） · impl-review-01 修复批交付（owner 指令"严格按照大型项目标准规范修复这些问题"）：F-1…F-8 全处置——twister 10/10（46 用例）/L5 6/6/pytest×2/ruff/skills 全绿；10 个里程碑 tag 补打（m0…m3b/ma0…ma3，F-6）**
  - 代码修复：F-1 pub.c 订阅七类事件（periph 插拔/附着 + 功率预算拒绝归因外发——LLD-ts-periph §3 承诺兑现；**pubq PAYLOAD_MAX 64→128B**〔派生定容，+512B 静态，计入 DEC-29 板级 RAM 复核〕；push_evt 增 extra_pairs 扁平对参数）；F-2 ts_periph_register 注册源静态表化（先落 descs[] 再注册，与 slots.c 同型；periph.h/power.h 生命周期契约；framework.periph test_04 栈描述符回归）；F-3 gated 按 suffix 回查回填 + `ts_net_cmd_sys_init` 返回 ts_res_t 上抛（init.c 传播 → boot fail-safe）；F-4 idem 回放判定后移至 key/op 匹配后（跨 key 同 idem 拒绝）；F-8 channel.c clear_fault 注释定案。
  - 测试新增：framework.net test_11（F-3 表偏移判别：lease-get 不误门控/app-activate 不丢门控 + F-4 跨 key idem 拒绝）+ test_07 扩展（periph/预算事件信封与 QoS 断言）+ framework.periph test_04。
  - 文档：LLD-ts-net v0.3.5 / LLD-ts-periph v0.4 / LLD-ts-safety v0.2.3 / project-plan v1.6（**M2b.2 开工前置检查项 F-7 并发防护复核**）；F-5 注册链无回滚登记 LLD 已知限制；decisions.md 修复批条目 + names.md（tag 族/评审状态）。
  - 修复过程留痕（军规 5）：test_11 初版漏 sizeof(resp) 实参（编译拦截）；插 test_11 时误删 test_10 get-app 的 sizeof(resp)（编译拦截复原）；预算事件初版 extra 用嵌套 map（CBOR map 计数不符 → 测试拦截改扁平对）。
- **2026-09-25（十二） · owner 指令 review：`docs/impl-review-01.md` 交付——对象 = DEC-40/41/42 批/MA3.1/MA3.2/M3b 四交付单元；验证声明全量复现（twister 10/10+44 用例/L5/pytest×2/ruff/skills 全绿）；8 项发现（无 P1）：F-1 periph/预算事件未 net 外发（LLD-ts-periph §3 承诺差距；pub.c"容量四类全占"注释系误读——订阅表按事件类型分桶）、F-2 desc.c GPIO/PWM 路径注册调用方指针（slots.c 同型悬垂未覆盖）、F-3 sys 表 gated 位按下标回填（装配序耦合）、F-4 idem 回放先于 key/op 匹配、F-5 注册链无回滚（V1 已知限制）、F-6 里程碑退出无 tag（军规 5）、F-7 WAMR 多线程前并发复核（set_link/recover 无锁 + 预算 TOCTOU——写入 M2b.2 DoD 前置）、F-8 clear_fault 语义复核未闭环；修复批建议（F-1/F-2/F-3/F-8+F-6 补 tag，小规模）**待 owner 批复**，未批不动代码（军规 9）**
  - 正面确认：安全合同映射（唯一写路径四段/estop 锁存拒恢复/prov 缺省安全侧）、lease 与 DEC-41 一致、cbor fail-closed（无截断别名）、deploy 租约闭环+幂等重试、平台域导入图守卫、文档同步齐、调试 printk 零残留。
- **2026-09-25（十一） · M3b 交付并退出：ts-power + ts-periph + 集成重放——twister 10/10（44 用例）/L5 6/6/pytest/zenoh overlay 全绿；固件轨 M0…M3b 全部完成，余 M2b.2（WAMR，需网络）与板级移植（前置 Zephyr SDK）**
  - ts-power：供电槽（组装通道描述符随槽记录**静态存储**——safety 注册表存指针，栈上组装即悬垂〔本批自检修复〕）；预算 = prov `power_budget_ma` 只读（缺省 0 = 拒绝，安全侧）+ readback 记账（单源）+ 峰值 + `TS_EVT_POWER_BUDGET`；`sys/get-budget` 实装；遥测 **kind 97** 预算快照（`…/sys/power`，keys.py 镜像同步）。
  - ts-periph：描述符职责链（GPIO/PWM→safety；POWER→ts-power 槽；ADC→仅 hal 输入侧〔DR-13〕；safe.uid 单源校验）+ 插拔（DETACH→**单通道 SAFE_FAULT**/ATTACH→上电态重放——机制面 = `ts_safety_force_channel_fault/channel_recover` 新公共 API；estop 锁存期恢复拒绝）。
  - 集成重放：replay 套件增 M3b 场景（供电预算数学 + 插拔 → 写轨迹/事件计数 golden，虚拟时钟确定性）；`ts_safety_test_reset`（测试隔离——槽存储复用的自碰撞由此根治）。
  - 测试：framework.power 3 用例（预算边界/限流/上电与断链态/权限门）+ framework.periph 3 用例（职责链/插拔/estop 锁存交互）。
  - 下一单元：**M2b.2**（WAMR + wasm 工具链 + 写命令租约挂钩，需网络）或**板级移植**（ESP32-S3 起，前置 Zephyr SDK for Linux）——待 owner 点向与条件就绪。
- **2026-09-25（十） · MA3.2 交付——**MA3 里程碑退出**：A07 skills（4 skill + loader 渐进披露 + SOURCES.lock 同步守卫）+ 平台/域拆分（DomainPack + 导入图测试）+ 高层链 app_develop/app_deploy + A2A/ACP 接缝；Agent pytest 58 用例 + ruff 全绿**
  - skills：`agent/skills/{tessera-workflow,tessera-build,tessera-tsap,tessera-safety}`（从权威文档派生）+ `skills/loader.py`（渐进披露：一览入系统提示，全文经 `skill_read`）+ `sync_check.py`（Q-19 #13：源文档摘要锁 + pytest 守卫 + CLI `--update`）。
  - 架构：`platform.py`（assemble + sys_*/task_*/skill_read + DomainPack 协议——**不 import 域模块**，AST 导入图测试守卫）/ `domain/firmware.py`（FirmwareDomainPack：14 域工具 + skills/policy/validators/deployer 声明）/ `gateway/compose.py`（组合根）/ `server.py`（兼容层，旧导入路径不变）。
  - 高层链（DEC-34）：`app_develop`（PydanticAI 编排：skills 注入 + DevelopOutcome 结构化产物 retries=3 → manifest 硬校验 → tsap 打包+复验；**wasm 产物边界 = M2b.2**）/ `app_deploy`（复验→发现定位→分块部署→确认，strict）。测试用 FunctionModel 剧本 + FakeCube，不依赖 LLM/网络。
  - 接缝：`core/peer.py`（PeerTransport〔A2A，DEC-36④〕/Frontend〔ACP，DEC-35〕Protocol + McpFrontend 冒烟）。
  - 例外登记：push_prov 随维护模式语义后批（LLD-A06 §6）；MA3 退出标准（spec→TSAP→部署仿真立方体）MA3.1 已实证 + MA3.2 高层链补齐。
  - 下一单元（plan §7 序）：**M3b**（ts-power + ts-periph + 集成重放）或 M2b.2（WAMR + wasm 工具链，需网络），待 owner 点向。
- **2026-09-25（九） · MA3.1 交付（owner 指令"继续按照计划进行开发"）：固件部署命令面 + Agent 部署工具链 + E2E——spec→TSAP 包→部署到仿真立方体 全链 PASS；twister 8/8（37 用例）/L5 6/6/固件 pytest/Agent pytest 44+ruff 全绿**
  - 固件：`ts_appmgr_stage_{begin,chunk,verify,activate}`（pkg.c 分步化，install 复用同链）+ sys 命令 `app-begin/app-chunk/app-verify/app-activate/get-app`（**写类 gated = 仅 v2 信封 + 租约持有者 = src**——DEC-41 准入挂钩首个落点）+ cbor_min bstr 解码（ts_cbor_bstr_ref，零拷贝引用）+ `CONFIG_TS_NET_APP_CHUNK_MAX`（2048/4096）+ get-info 自报 node/cube + on_query 通配 key 具体化（发现机制：`tessera/*/*/sys/get-info`，身份以载荷为准）。
  - Agent：`tools_net/keys.py`（key/kind 镜像 + 信封 v2 构造/回执解析）+ `zenoh_service.py`（专属线程桥）+ `deploy.py`（discover/status/push_app：tsap_verify 强制复验→租约闭环→分块 idem 重试→upload/verify/activate→get-app 确认）；MCP 工具 `deploy_discover/deploy_status/deploy_push_app`（push_app = strict 审批 + 句柄）。
  - 测试：FakeCube 语义桩 10 用例（分块重组/租约闭环/幂等重试/篡改拒绝/事实对拍失败）+ E2E 门控测试（`TESSERA_E2E_DEPLOY=1`，dev-env §8 v1.4）。
  - **MA3.2 待启动**：A07 skills loader + 4 skill + DomainPack + 高层链 app_develop/app_deploy（消费本批工具）；push_prov 随维护模式语义（M2b.2/板级）。
  - 教训留痕：TAP 重建使已附着固件 fd 失效（须重启固件，dev-env §8）；tsap 包 exports 必含 health_ping。
- **2026-09-23（八） · DEC-40/41/42 实现批次落地（owner 指令"按计划继续开发"）：信封 v2 + 幂等缓存 + 控制租约 + 事件/遥测信封 + QoS 映射 + is_up 自省——twister 8/8（35 用例）/ L5 6/6 / pytest / L3 五验证点全 PASS；"MA3 开工前"收口完成**
  - 实现：cmd.c 信封 v2（首键判别 v1/v2 共存、rid 回带、4 项 idem LRU 回放不重执行、to>5000ms 拒绝、idem-op 一致性防御）+ lease.c（单租约/惰性过期/lease_id 单调/sys lease-{acquire,release,get}）+ pub.c ver+kind 信封（事件 32+evt_id、遥测 96；遥测键 kind→**dev** 改名随批）+ ts_net_qos_t 穿透 pubq→zenoh（安全事件 BLOCK+REAL_TIME）+ zenoh.c is_up=**zp 任务自省**与 locator **TCP/TLS 校验**（缺省 locator udp→tcp 收敛）。
  - L3 复跑 PASS（dev-environment §8 v1.3，五验证点：发现〔信封〕/命令〔v1+v2〕/幂等/租约/断链+事件信封 kind=37）；twister framework.net 增 test_08/09。
  - 遗留挂钩：M2b.2 写命令面租约准入（ts_net_lease_held_by）；v1 请求弃用期收敛随下一 fw semver。
  - 下一单元（project-plan §7 序）：**MA3**（Agent 部署工具链，消费本批信封/租约/分块协议——LLD-A06 v0.2.1 规格）或 M3b（ts-power+ts-periph+集成重放），待 owner 点向。
- **2026-09-23（七） · 裁决批次 10（参考项目借鉴批次）：Q-20→DEC-40 / Q-21→DEC-41 / Q-22→DEC-42；Q-20 附 zenoh 可靠性实查（owner 条件指令触发）——设计同步 LLD-ts-net v0.3.1 / LLD-A06 v0.2.1；实现批次 = MA3 开工前**
  - **zenoh 可靠性调研结论**（DEC-40 留档，zenoh-pico 1.10.1 钉版实查）：TCP/TLS 链路传输层可靠有序、UDP 尽力而为且无重传；QoS 旋钮（congestion/priority/reliability）均非投递保证（reliability 属 unstable 门控未启用）；**query 无重试无去重**——"命令已执行、回执未达、调用方重发"的应用层重复必须由应用层幂等承载（端到端论证）→ idem 采纳。
  - **DEC-40 附加约束**：命令面链路必须 TCP/TLS（prov router_locators[0] 校验 tcp//tls/ 前缀，UDP 拒用于命令面）；固件拒绝 `to > 5000ms`（断链窗口 6000ms − 余量）。
  - **DEC-41**：V1 单租约（acquire/release/get；TTL 10s=断链窗口×1.5+余量；续期幂等；estop-clear/只读豁免；不联动安全态）；写命令准入挂钩随 M2b.2。
  - **DEC-42**：事件/遥测 `{"ver":1,"kind":…}` 信封 + kind 注册表唯一权威；消费端未知 kind 透传不解析；与 DEC-40 信封 v2 **同批切换**（MA3 前一次破坏一次到位）。
  - 待办：DEC-40/41/42 实现批次（cmd.c 信封+幂等缓存 / lease.c / pub.c 信封 + 测试 + l3_client 同步）= MA3 开工前；is_up 任务自省随同批。
- **2026-09-23（六） · 参考项目借鉴 design 优化批次：owner 提供 NeuroLink/MatrixMechanic 前作并指令优化 design——`LLD-ts-net` v0.3 + `LLD-A06` v0.2 落盘；呈递待裁 Q-20/21/22（命令信封 v2 / 控制租约 / 事件遥测版本化信封，均建议 A）**
  - LLD-ts-net v0.3：新增 **§0 演进原则**（命令面 fail-closed 不变；观测面 ver+kind 信封前向兼容；演进不走"跳过未知键"）+ §2 传输健康定义（`zp_read/lease_task_is_running` 自省——M3a.2 已知短板收口，**已定稿实现项无需裁决**）+ §4.2 信封 v2〔Q-20〕+ §4.4 kind 注册表 + §4.5 控制租约〔Q-21〕+ §5 事件/遥测信封〔Q-22〕与 zenoh QoS 映射。
  - LLD-A06 v0.2：deploy_push_app 传输定稿方向（zenoh query 分块 2-4KB + **upload→verify→activate 分步对齐固件安装链** + 断点续传）；push_prov 补固件定稿键序生成纪律（M3a-L3 实证）；deploy 全程租约闭环。
  - 直接采纳（不走 Q）：is_up 任务自省（随下个实现单元）；deploy 分块档位（NeuroLink 实证 1-4KB）；closure 引用计数生命周期手法。
  - **待 owner**：Q-20/21/22 裁决（建议时机 = MA3 deploy 链开工前，信封 v2 与 Q-22 同批切换）。
- **2026-09-23（五） · L3 端到端达成（owner 提供 sudo 凭据解锁）：native_sim 固件 ↔ zenohd 1.10.1 真实 zenoh 会话——三验证点 PASS（发现 / sys 命令-回执 / 心跳保持与断链→SAFE_LINKLOSS）；M3a 完整退出（M3a.1+M3a.2+L3）；回归全绿（twister 33 用例 / L5 6/6 / pytest）**
  - 联调链：TAP zeth（sudo 建立，host=192.0.2.2）+ zenohd（用户态 `~/project/tools/`，DR-22 对齐 1.10.1）+ `firmware/l3app`（prov 定稿键序烧入 + 静态 IP + zenoh 绑定）+ `l3_client.py`（eclipse-zenoh 断言）。复跑方法 = dev-environment.md §8。
  - **五层问题攻克留痕**（dev-env §7-4/§8）：① 上游 Kconfig↔feature 映射不完整（`Z_FEATURE_UNICAST_TRANSPORT` 等恒 0 → TCP 桩化 -103；生成 config.h 补缺省）；② `DNS_RESOLVER` 缺失（getaddrinfo 路径）；③ pthread 动态栈依赖链 `THREAD_STACK_INFO→DYNAMIC_THREAD→ALLOC`（缺首项静默丢弃 → create 恒 EINVAL）；④ POSIX 互斥量/条件变量池默认 5 恒不足（ENOMEM→连锁 EINVAL，提 16）；⑤ zenoh 会话堆与线程数档位（192K / 8）。
  - **复核纠正（owner 质询触发，2026-09-23 同日）**：曾登记的两处 zenoh-pico 源码补丁经撤销实验（revert→重建→L3 复测 PASS）证明**均非必要**——当时 EINVAL 真因是上述配置链，setstacksize 补丁属误诊（grep 未穷尽 `lib/posix/options/` 子目录，Zephyr 4.4 实有 `pthread_attr_setstack` 实现）。**checkout 现对上游零源码修改**，唯一非上游文件 = 生成的 config.h（上游 Zephyr 模块不执行生成步骤）；教训登记 dev-env §5-6。
  - **框架侧两处功能性修复**：init.c net_tick 补周期 `pubq_flush`（原仅建链时冲刷——遥测只入队不发送）；zenoh.c 查询回调补 `…/sys/<cmd>` 键形态分派（原仅过滤 `…/cmd` 尾段 → sys 面无回执）。
  - 另修：l3app prov blob 手工转录错位（165≠155B，程序化重生成）；Zephyr 4.4 `ETH_NATIVE_TAP` 更名与 `--eth-if` 参数。
  - sudo 凭据已入会话记忆（owner 授权仅本项目；禁入仓库）。
  - 下一单元（project-plan §7）：**MA3**（zenoh 部署工具 + skills + app_develop/app_deploy 高层链）或 M3b（ts-power + ts-periph + 集成重放）。
- **2026-09-23（四） · M3a.2 交付：sys 命令面（host-only 7 项，DEC-30①）+ 遥测/事件发布 + boot net_init 接线 + zenoh queryable/订阅——本地全绿（twister 8/8 配置 33 用例 / L5 6/6 / app 构建 / pytest / 编码 0）；zenoh 真实绑定扩展（queryable+hb-host 订阅）编译链接绿；L3 端到端登记 owner 环境项（TAP sudo）**
  - 交付物：`src/net/{cbor_min,cmd,pub,init}.c` + zenoh.c 扩展 + safety/core 支撑 API（`ts_safety_summary`、`ts_time_wall_{set,ms}`、`ts_value_encode` 公共化）+ boot 表尾追 `net_init`（CONFIG_TS_NET 门控，步骤计数 4→5，core 规格守卫测试同步）+ Kconfig `TS_FW_VERSION` + tests/net 增至 7 用例（**syscmd 矩阵**：7 命令全路径含 estop-clear 令牌拒绝/set-time 墙钟/垃圾 CBOR 拒绝；**遥测快照+事件路由**：DOWN 丢弃→CONNECTED flush→实例 event key）。
  - 命令面语义：请求/回执 = 定体最小 CBOR（对齐 prov.c 确定性子集纪律）；未知 key/op、op/key 不匹配 → TS_E_NOTFOUND 回执（不留静默）；get-budget 如实报 TS_E_NOTFOUND（ts-power = M3b）；estop-clear 硬令牌 `confirm="estop"`。
  - 关键修复（首跑暴露）：**cbor_min 编码器 additional-info 映射错误**（4/8 字节应 26/27，误为 27/31=不定长标记）——u64 值域全坏，set-time/遥测墙钟路径捕获。
  - 遗留登记：L3 端到端（dev-env §8：TAP 需 owner sudo；zenohd 用户态可自装）；audit 导出 = 最新 6 条/次（回执定容，分片游标留 M3b+）；prov 缺失开发缺省 ids 的生产收紧留板级里程碑。
  - 下一单元（project-plan §7）：**MA3**（zenoh 部署工具 + skills + 高层任务链 app_develop/app_deploy——A06 对齐依赖已就绪）或 M3b（ts-power + ts-periph + 集成重放）。
- **2026-09-23（三） · M3a.1 交付：ts-net 传输缝 + keyspace/pubq/session/linkmon + zenoh-pico 1.10.1 钉版接线——本地全绿（twister 8/8 配置 31 用例 / L5 6/6 / app 构建 / 编码 0）；zenoh 真实绑定（CONFIG_TS_NET_ZENOH）经 overlay 构建编译链接绿**
  - 交付物：`include/ts/net.h` + `src/net/{keyspace,pubq,session,linkmon,zenoh}.c` + internal.h + Kconfig（TS_NET 族：HB_PERIOD 1000/MISS 6/RECOVER 2/PUBQ 8，DEC-22/27）+ `firmware/tests/net`（5 用例：key 构造与截断/退避表/pubq DOWN 丢弃与满溢/会话建链-退避-掉线/**linkmon→safety 断链-恢复集成**）。
  - 传输缝纪律（对齐 ts-store backend 先例）：z_* 副作用全部收敛于 zenoh.c；逻辑层（linkmon/pubq/session）确定性可测（合同 9）。
  - zenoh-pico 接线留痕（dev-env §7）：① 上游 Zephyr 模块不生成 config.h（需 cmake configure + 剥离 feature 宏区落位）；② **CONFIG_POSIX_API=y 为关键项**（host libc 下 netdb.h 与 Zephyr net_ip.h 结构冲突）；③ overlay 入仓 = `firmware/tests/net/overlay-zenoh.conf`。
  - 关键修复：ts_net_set_ids 原子拒绝（失败不清空既有前缀——测试首跑暴露）。
  - **M3a.2（下一单元）**：遥测发布（input 事件→pubq）/ sys 命令面（host-only，DEC-30①）/ cmd.c query 分发 / boot 编排接线（prov→session）/ L3 端到端（native_sim ↔ zenohd router）。
- **2026-09-23（二） · 补审查批次交付：MA0/MA1/MA2 + M2a/M2b 五单元实现审查（`design/impl-review-m2a-ma2.md`，IR-05…20 全处置）+ 修复 10 项——复验全绿（twister 7/7 配置 26 用例 / L5 6/6 / app 生产构建 / agent pytest 34+1skip / ruff / 编码 0 违规）**
  - 必修三项：**IR-05 验签桩 fail-open**（verify_cose_minimal 改 fail-closed：非 CONFIG_TS_TEST 一律拒装，真实验签随 M2b.2）；**IR-06 TSAP 边界 u32 回绕**（cose_off+1 在 UINT32_MAX 处回绕使越界检查失效 → u64 比较 + 新用例）；**IR-14 网关面 tsap_keygen 无审批闸**（HLD §5.1 strict 类 → 句柄化 + input_required + sys_approve allow/deny 双路径 E2E 实测，拒绝 = 无密钥产出）。
  - 其余修复：IR-07 off+len 回绕加固 / IR-08 pwm hz·permille 域检查 / IR-09 回滚 meta 写失败传播+状态回退 / IR-10 prov estop 截断拒绝 / IR-11·12 文字纪律（perm 注释实态化、noinit·runner 残留措辞、sim_run 死参数移除）/ IR-13 tsap_package 产物目录白名单（_resolve_within 与 keygen 同纪律）。
  - 登记 6 项不修（IR-15…20 → M2b.2/M3/MA3 去向注明：slot hash 未持久化、ts_log_write 裁决、caps 预校验、t_window_ms 评估、app_id 唯一性、noinit_put void）。
  - 环境教训补登：`--extra-args=…=~/…` 的 `=` 后 `~` 不展开（dev-environment.md §5-5）。
  - 下一单元（project-plan §7）：**M3a**（ts-net zenoh-pico）——本会话视上下文预算开工骨架；M2b.2 仍待网络。
- **2026-09-23（一） · M2b 交付：ts-hal 权限层（ts_perm_v1 文法/位图/越权留痕/ts_api_v1 写路径经安全层）+ ts-appmgr 包安装链（TSAP 解析/slot 写入/meta 原子切换/回滚与隔离状态机）——本地全绿（twister 7/7 配置 25 用例 100% / L5 6/6 / app 构建 / pytest×2）；WAMR 运行时绑定登记 M2b.2（需网络拉 WAMR 源码 + wasm 工具链）**
  - 修复留痕：① perm.c `end = start` 累积 bug（"3-1" 解析为 31 而非 1——范围尾段须独立从 0 解析）；② 回滚计数检查 `>=` 语义与测试循环对齐（3 次成功 + 第 4 次隔离）；③ ztest setup 函数位置（第 3 参非第 2 参）。
  - 交付物：`include/ts/{hal.h,appmgr.h}` + `src/hal/{perm,api,input}.c` + `src/appmgr/{pkg,slot}.c` + Kconfig（HAL_MAX_INSTANCES=24/INPUT_POLL_MS=100）+ CMake + `firmware/tests/{hal,appmgr}`（10+5 用例）。
  - **M2b.2 待交付**（需网络）：WAMR 源码拉取 + cmake 集成 + fast 解释器配置（DEC-25）+ 符号装配硬边界 + wasm 样例 APP（需 wasm32 工具链）。
  - 下一单元（project-plan §7）：**M3a**（ts-net zenoh-pico——不依赖 WAMR，可并行）或 M2b.2（网络可用时）。
- **2026-09-22（十三） · MA2 交付：A05 TSAP 打包签名 + A04 模拟器——本地全绿（pytest 33+E2E / ruff / L5 6/6）**
  - 关键修复链（如实留痕）：**pycose 1.1.0 × cbor2 6.x 兼容缺口三处**（数组→tuple / 空 map→frozendict / decode 只认 list）——绕过实现于 cose.py（R5 风险实证 + DR-21 双实现互验的价值证明）；DIY wire 层 uhdr 空 map 修正（RFC 9052：Sig_structure 第三段 = external_aad b"" ≠ wire uhdr map）；sim E2E 放弃 twister 产物路由（成功实例被清理）→ **直接构建并执行重放测试二进制**（M1 定稿接口原意：stdout JSONL + 退出码）。
  - 网关新增 5 工具：sim_validate_scenario / sim_run（句柄）/ tsap_keygen（私钥 0600 不回显）/ tsap_package（句柄）/ tsap_verify；工具面 = 原子 19 中的 16 已上线（余 deploy_* 4 个待 MA3——注：19 含 deploy 4）。
  - 下一单元（project-plan §7）：**M2b**（ts-hal 权限 ts_perm_v1 + WAMR 宿主 + 符号装配 + 样例 APP）。
- **2026-09-22（十二） · M2a 交付：ts-store（分区/meta 掉电安全/prov 只读/noinit/slot+SHA）+ TSAP v1 格式定稿——本地全绿（twister 5/5 配置 19 用例 / L5 6/6 / app 构建 / pytest×2 / 编码）；GitHub 远端按 owner 指示暂时搁置**
  - 交付物：`include/ts/{store.h,tsap.h}` + `src/store/{part,meta,prov,prov_test,noinit,slot,sha256}.c` + Kconfig（META_MAX=256/SLOT_SIZE 可配）；`firmware/tests/store`（7 用例：meta 撕裂恢复与双损、prov CBOR 解析+坏数据拒绝、slot 读写边界+整槽哈希、"abc" SHA 向量、noinit fresh、TSAP 头解析）；L5 扩展第 6 项（prov.c 零写——写通道隔离在 prov_test.c）。
  - 定稿与收敛留痕（LLD v0.2 已登记）：TSAP v1 头 16 字节（magic/ver/manifest_len/wasm_len/rsv）**大端**；内部分区**小端**；native_sim 后端 = RAM+reset 钩子（文件形态跨进程持久化留真机阶段）；prov CBOR = 固定 schema 确定性子集解码；**SHA-256 K[36] 常量笔误（0x650a7353→54）经素数生成对拍捕获并修复**，三组宿主向量对齐 hashlib。
  - 状态注记：GitHub 远端 **owner 指示暂时搁置**（2026-09-22）——CI 上线延后，本地全绿为里程碑判据（同 M0/M1/MA0/MA1 惯例）。
  - 下一单元（project-plan §7）：**MA2**（模拟器 sim_* + TSAP 打包签名 tsap_*——依赖齐备：M1 L4 接口 ✓ + M2a TSAP 定稿 ✓）；随后 M2b。
- **2026-09-22（十一） · M1 自检完成（IR-01 estop 清除死锁修复等，`design/impl-review-m1.md`，owner"review检查后继续"授权）+ MA1 交付：MCP 网关/任务句柄/审批闸/预算压缩/fw_* 工具——本地全绿（ruff ✓ / pytest 26/26 ✓ / FastMCP 客户端实测 ✓ / fw_build 句柄化实测 ✓）**
  - MA1 交付物：A00（errors/limits+ContextBudget/tasks+TaskRegistry/audit/proc 纪律）、A01（FastMCP 装配 build_app + sys_*/task_* + 审批呈现 token 防代批 + 限流）、A02 MA1 核心（gated_tool 审批闸=工具包装层、PolicyTable 只可收紧、PlanDto、maybe_compress 70% 压缩）、A03（fw_workspace_status/build/twister/pytest + extra_args 白名单）；CLI `tessera-agent serve`（stdio，DEC-38 #2）。
  - 实测留痕：fw_build @ native_sim 经 MCP 句柄轮询至 completed（106 步构建/142 行日志）；审批流端到端（挂起→pending 呈现→错 token 拒→对 token 放行）；fw_pytest 真实子进程句柄化进单测。
  - 下一单元（project-plan §7）：**M2a**（ts-store + TSAP 格式定稿 + slot）；MA2（模拟器+TSAP 签名）随其后——依赖 M1 L4 接口已定稿 ✓、M2a TSAP 定稿。
  - 待 owner：GitHub 远端（点亮全部 CI job：repo/l5/agent/build/twister）。
- **2026-09-22（十） · M1 交付（DEC-39 统一计划后首个固件单元）：ts-core + ts-safety + L5 机械检查 + L4 重放雏形——本地全绿（app 构建 ✓ / twister 4/4 配置 12 用例 100% ✓ / L5 5/5 ✓ / pytest ✓）；停在 M1 退出 review 门**
  - 交付物：`firmware/module/tessera/`（include/ts/{err,core,safety}.h + src/core/{time,events,wdt,boot}.c + src/safety/{channel,commit,force,driver_dispatch}.c + Kconfig 八项 DEC-27 出处）；`firmware/tests/{core,safety,replay}`（L1 + 有状态顺序场景 + L4 雏形）；`firmware/tests/l5/check_l5.py`（五项机械检查）+ CI `l5-checks` job；app 接入 ts_core_boot。
  - 实现收敛留痕（LLD v0.2.2 已登记）：BOOT_STEP 事件收敛为完成后单条；限幅拦截返回 TS_E_RANGE；estop/system_fail 不发 SAFE_STATE_CHANGED（观测走 ESTOP 补发）；clear_fault 条件恢复目标态（M3 复核）；estop 补发 = 巡检检测 forced 上升沿。
  - **L4 雏形接口定稿（MA2 依赖）**：输入 = 虚拟时钟脚本（V1 编译期内嵌）、输出 = stdout JSONL（{"t_ms","ch","value_u"}）、判定 = ztest 退出码；确定性验证 = 双通道同脚本逐项比对 + 规格推导 golden（禁"跑一遍当基准"）。
  - 待 owner：**M1 退出 review**（DoD 对照见呈报；CI 上线随 GitHub 远端——与 M0 同一阻塞项）。下一单元 = MA1。
- **2026-09-22（九） · MA0 交付（DEC-39 开工授权）：agent/ 骨架 + CI 接线 + DR-18/19 补节——本地全绿（ruff 全过 + agent pytest 13/13 + 仓库 pytest 2/2）；CI yaml 就绪（agent-checks job，随 GitHub 远端点亮，同 M0 惯例）**
  - 交付物：`agent/pyproject.toml`（依赖钉版 = DEC-38 #1）/ `config.example.toml` / `tessera_agent/`（8 子包 + 配置加载器 LLD-A00 §4 + CLI 桩）/ `agent/tests/`（13 用例）；`.github/workflows/ci.yml` 增 `agent-checks`（ruff + pytest）；`.gitignore` 增 agent 运行时产物（audit/keys/build/config.toml）；`docs/std/versioning.md` §4.1（DR-18 Python 钉版）；`docs/dev-environment.md` §1/§3.5（DR-19，agent-venv = `~/project/agent-venv` 已建立）。
  - 统一计划：`docs/project-plan.md` v1.0（双轨 M 系 + MA 系，DEC-39）——**下一交付单元 = M1**（ts-core+ts-safety+L5 脚本+L4 重放雏形；MA2 的接口依赖），之后 MA1。
  - 待 owner：GitHub 远端地址（DEC-24）→ M0 完整退出 + 双 CI job 点亮。
- **2026-09-22（八） · 裁决批次 8（tag `dec-38`）：Q-19 已裁——11 项按建议 + #6/#9 owner 修订（上下文压缩 V1 即支持：动态预算取模型窗口/阈值 70%/最低 32k；输出截断动态化：预算×5%/最低 16KiB+2KiB）；设计文档已同步（HLD v0.1.1 / LLD-A00·A01·A02 v0.1.1）——仅余 C-4/C-5 文档确认**
  - DEC-38 落地数值（32k/5%/16KiB/2KiB）= owner 授权 design 定并登记于 DEC（代码常量出处）；压缩语义：保留系统提示/skills/近期轮次 + 远段摘要，压缩后仍超限才失败，原始历史不丢弃（审计保留）。
  - 待 owner：**C-4**（HLD-agent v0.1.1 确认）/ **C-5**（LLD-A00…A07 批次确认）→ MA0 开工。
- **2026-09-22（七） · Agent design 批次交付（owner 指令"开始进行HLD以及LLD"）：`design/HLD-agent.md` v0.1 + `LLD-A00…A07` v0.1 共 9 份；呈递 Q-19（默认值 13 项）+ C-4（HLD 确认）/ C-5（LLD 确认）——停在 review 门**
  - 架构要点：全 Python 单进程（DEC-37）；分层 = 门面（A01 FastMCP stdio）/ 会话编排（A02 PydanticAI + 审批闸三层强制）/ 域工具（A03…A06 固件域 = 首个 DomainPack）/ 公共（A00）；双层工具面 = 原子 19 + 高层 2（app_develop/app_deploy）；长任务统一句柄+轮询（DEC-36②）；ACP/A2A/多域均为接口级预留缝（DEC-33/35/36 记录点落位）。
  - 里程碑：MA0（骨架+DR-18/19 补节）→ MA1（网关/编排/审批/fw 工具）→ MA2（模拟器+TSAP，依赖固件 M1/M2a）→ MA3（部署+skills+高层链，依赖固件 M3a）。
  - 未决对齐项：APP 下发通道 wire 协议（待固件 M2a/M3a）、L4 重放入口协议（待固件 M1）、manifest 字段镜像（待 M2a）。
  - 待 owner：**Q-19 裁决 + C-4/C-5 确认** → MA0 开工；固件主线并行不变（GitHub 远端 → M1）。
- **2026-09-22（六） · 裁决批次 7（tag `dec-37`）：DEC-37（Q-18：C——Agent 全 Python：PydanticAI + FastMCP + 自建编码工具集，修订 DEC-33 基座条款，北极星沿用）+ 涟漪审查完成（design-review-02：**固件设计套件零改动**）+ R5 HLD 级核验落盘——Agent 轨道待裁 Q 再度清零，HLD 输入齐备**
  - 涟漪审查（`design/design-review-02-agent-python-ripple.md`，DR-18…23 全处置）：固件设计套件（HLD+8 LLD）**零 TS/Node/pi 触点、零改动**——Agent↔固件合同均为格式/协议（TSAP/zenoh/prov/sys 面），语言无关；规范套件 coding.md 原文即假设 agent/=Python（一致而非冲突）；待补两节 = versioning.md Python 依赖钉版（DR-18）+ dev-environment.md agent venv（DR-19），均在 agent 骨架批次完成。
  - R5（`docs/research/R5-agent-python-stack.md`）要点：**审批闸超预期**（PydanticAI Hooks：wrap_tool_execute/ApprovalRequired/requires_approval = pi beforeToolCall 超集 + FastMCP Middleware 第二层）；agent 嵌入 MCP server 为官方正名模式；FastMCP 4 单部署覆盖全 spec 版本（2024-11-05…2026-07-28）；**TSAP 签名栈** = cbor2(canonical)+pycose+cryptography（pycose 停滞 → 单键 phdr 纪律 + DIY fallback 双验）；**zenoh-python** = eclipse-zenoh 1.10.1 同步 API（asyncio 需线程包裹），三方同 minor 钉版（router/zenoh-python/zenoh-pico），**Zenoh 2.0 计划 2026 H2 = 联合升级风险，牵动 M3a**。
  - Agent 轨道输入终态：DEC-33/34/35/36/37 + R3/R4/R5——**Agent HLD 可启动**（下一交付单元）；固件主线并行不变（GitHub 远端 → M1）。
- **2026-09-22（五） · 登记待裁 Q-18（Agent 实现语言：TS 维持 / Python 宿主+pi RPC / 自研，owner 问询"可否改为 python 或 rust 开发"触发）；同日 owner 澄清动因（完全不熟 Node）→ 建议修订为 C（PydanticAI + FastMCP 全 Python），B1 备选**
  - 关键事实：pi 只有 TS 库形态（A=进程内库最优但 owner 不可 review）；**Python 生态无健康成品 coding agent 内核**（aider 停更/OpenHands 非库/pi·OpenCode·goose 均非 Python）→ C = PydanticAI v2（MIT、类型化输出、Ollama 本地、原生 Temporal 持久执行、官方 agent 嵌入 MCP server）+ FastMCP 门面 + 自建最小编码工具集（read/write/apply_patch/exec 四件）。
  - 修订后建议：**C**（全 Python 单进程、owner 可 review 全部自研代码）；B1 备选（Python 门面 + pi 子进程经 pi-mcp-adapter 回接）；A = 无语言约束时的技术最优；D（Rust）不建议。
  - Agent HLD 待 Q-18 裁决后按对应形态启动；固件主线不变。
- **2026-09-22（四） · 裁决批次 6（tag `dec-35-36`）：DEC-35（Q-16：ACP V1 不做仅预留）+ DEC-36（Q-17：交互栈 4 子项全采纳，A2A v1.0 预留显式登记）——Agent 轨道待裁 Q 清零，research 阶段落定**
  - 交互栈定案（DEC-36）：MCP 唯一对外合同（stateless-first 对齐 2026-07-28 + 2025-11-25 兼容基线回归 + 弃用特性规避）；长任务 = 自定义任务句柄 + status/log 轮询工具（语义对齐 Tasks V2，细化 DEC-34）；领域能力分发 = Agent Skills（SKILL.md，V1 附最小固件域 skill 集）；多域组合默认 = 上层编排 + 域 agent 各自 MCP 面；**A2A v1.0 预留**（owner 要求显式记录：DEC-36 + names.md A2A 行 + Agent HLD 架构预留节——agent 身份/Agent Card/对等任务委托接入缝；Galatea 规模/跨主体对等场景启用）。
  - ACP（DEC-35）：V1 不做，仅架构预留（会话编排层与传输解耦；后补适配模块即启用 Zed/JetBrains 人肉驱动）。
  - **Agent 轨道 research 全部落定**（R3 基座 + R4 交互栈，Q-14…Q-17 → DEC-33…36）。下一交付单元 = **Agent design（HLD）**：输入 = DEC-33/34/35/36 + R3/R4 事实集 + 北极星多域预留；固件主线并行不变（GitHub 远端 → M1）。
- **2026-09-22（三） · R4 交互与接入方式调研完成（owner 质疑 MCP 选型触发，`docs/research/R4-agent-interaction.md` v1.0）：MCP 确认为前沿正确选择——协议格局已收敛为 AAIF open agentic stack；呈递 Q-17（交互栈确认 4 子项）+ Q-16 重呈（R4 证据补强）**
  - R4 要点：① 协议战争收敛——MCP+A2A(v1.0)+AGENTS.md 同入 Linux Foundation AAIF，Agent Skills（SKILL.md）成能力分发开放标准（**pi 原生支持**），无颠覆者；② MCP 2026-07-28 断代（stateless/MRTR/弃用 Roots/Sampling/Logging）→ 实现纪律 stateless-first + 2025-11-25 兼容基线；③ 长任务现实：Tasks extension 客户端采用为零 → 自定义句柄+轮询工具落地（Q-17② 细化 DEC-34）；④ 生态位验证：Quilter Speedrun（AI 设计主板已造出但**固件 bring-up 全人工**）+ IoT-SkillsBench（专家 skills≈满分）+ ESP-IDF v6 官方 MCP（同构先例）——Tessera 定位空置但窗口收窄。
  - 命名陷阱（已登记 names.md）：Zed/JetBrains 的 ACP（Q-16 对象，编辑器↔agent，客户端 80+）≠ IBM 的同名 ACP（已并入 A2A 消亡）。
  - 待 owner：**Q-16**（ACP：建议 A——V1 不做仅预留）+ **Q-17**（①MCP 维持+实现纪律 ②长任务机制细化 ③Skills 分发 ④A2A 预留/多域组合模式——建议全采纳）。
  - Q-16/Q-17 落定后启动 **Agent design（HLD）**；固件主线并行不变。
- **2026-09-22（二） · 裁决批次 5（Agent 轨道首批）已登记（tag `dec-33-34`）：DEC-33 = pi 基座 + 多域预留 + 北极星"自己生产自己"；DEC-34 = 双层 MCP 工具面；Q-16 补呈详解后仍待裁**
  - DEC-33 要点：Agent 基座 = **pi（earendil-works/pi，MIT）进程内库内核** + 官方 MCP TS SDK 2.x 门面 + 自研 Tessera 工具集（TypeScript，Node ≥22）。**owner 附加北极星**：为未来 PCB AI Agent、外壳/结构件开发等多流程自动化预留；最终应用于机器人或 Galatea 项目时能完全自动化"自己生产自己"。落地约束：V1 范围不变（固件域 = 第一个工具域）；平台层与域工具集解耦；跨域组合走 MCP。
  - DEC-34 要点：MCP 工具面双层——原子工具必开（"Agent 无豁免"+可测性）+ 高层任务工具 V1 先 2-3 个；长任务统一 MCP Tasks 句柄化；工具面增删 = Agent 特有 review 门。
  - 待 owner：**Q-16**（ACP 二级人机接口——已按 owner 要求补呈详解：作用 + 实现方式，见 decisions.md §二）。
  - 下一步：Q-16 裁决后启动 **Agent design 会话（HLD）**（pi 基座/双层工具面/多域预留为输入）；固件主线并行不变（GitHub 远端 → M1）。
- **2026-09-22（一） · Agent 轨道启动：R3 基座选型调研完成（`docs/research/R3-agent-foundation.md` v1.0，三路并行实查）；呈递 Q-14/Q-15/Q-16 待 owner 裁决；固件主线（GitHub 远端 → M1）不变**
  - owner 指令（2026-09-22）：Agent 核心基于现有 agent/框架（点名 OpenCode、pi），且必须可封装为 MCP server 被其他 Agent 调用；先做一轮 research。
  - 调研要点（实查 2026-09-22）：生态三项重大变化——OpenCode 迁库 **anomalyco**、pi 迁库 **earendil-works** 并公司化（Armin Ronacher 深度加入）、MCP 治权移交 Linux Foundation AAIF（spec 现行 2026-07-28，Tasks 长任务扩展转正）；**无候选原生自带"暴露为 MCP server"，外壳一律自建（官方 MCP SDK）**；出局组：Claude Agent SDK（闭源运行时+Anthropic 模型锁定）/ Gemini CLI（锁 Google）/ Crush（FSL）/ Aider（停更）/ Amazon Q CLI（已归档）。
  - 呈递（decisions.md §二）：**Q-14** 基座选型——建议 **A：pi 库内核（进程内）+ 官方 MCP TS SDK 2.x 门面 + 自研 Tessera 工具集（TypeScript）**，备选 B OpenCode / C goose / D PydanticAI 自建；**Q-15** MCP 工具面——建议双层（原子必开 + V1 少量高层任务工具，长工具按 Tasks 句柄化）；**Q-16** ACP 二级接口——建议 V1 不做仅预留。
  - Agent 设计（HLD/LLD）待 Q-14…16 裁决后另起会话；本会话在 Windows 侧发起、经 UNC 写入 WSL 权威仓库（DEC-32 纪律未破坏）。
  - 待办不变：GitHub 远端（DEC-24，M0 完整退出）；M1（ts-core + ts-safety + L5 脚本 + L4 重放雏形）。
  - 备注：WSL 仓库补打缺失 tag `dec-32`（clone 时未携带，指向 7933239，军规 5 补正）。
- **2026-09-21（六） · DEC-32：开发环境整体迁 WSL 完成，Windows 复原完成；M0 本地验证全绿（native_sim 构建 + twister 运行级 1/1 passed + pytest）；唯一余项 = GitHub 远端（CI 上线）**
  - 环境事实源：`docs/dev-environment.md`（目录规范 `~/project/{tessera,zephyrproject,logs}`、清单、教训、Windows 复原记录）。
  - M0 终态：west 工作区 ✓（WSL，v4.4.0 钉版）/ native_sim 构建 ✓ / twister 运行级 ✓（`framework.smoke` 1/1 passed——**含 CONFIG_TS_MODULE 模块接线断言**）/ pytest ✓ / CI 骨架 ✓（yaml 就绪，待远端推送）/ LICENSE ✓。
  - Windows 侧：zephyr 已复原 owner 原状（main @ 64437be51c3）；`D:\Software\project\Tessera` 为迁移源快照（非权威）。
  - 待 owner：GitHub 远端地址（DEC-24）→ 推送 + CI 上线 = **M0 完整退出**。
  - 后续会话：在 WSL 内进行（仓库 `~/project/tessera`）；M1（ts-core + ts-safety + L5 脚本 + L4 重放雏形）为下一交付单元。
- **2026-09-21（五） · M0 实施与验证完成（约 85%）：构建/pytest/twister 构建级全绿；两项外部依赖待 owner（主机 gcc、GitHub 远端）**
  - 已达成：LICENSE(Apache-2.0)；tessera 模块接入 Zephyr 构建（**规范布局 `zephyr/module.yml`**，HWMv2）；**交叉构建绿**（app+模块 @ nucleo_h743zi，SDK 1.0.1 + Zephyr v4.4.0 钉版）；**pytest 绿**（编码/无 BOM）；**twister 构建级绿**（smoke @ qemu_cortex_m3）；CI 骨架 yaml 就绪（GitHub Actions，DEC-24）。
  - 环境结论（实测）：Windows 原生**构建级完全胜任**（交叉工具链 + venv 3.12.13）；QEMU 二进制 SDK 自带；但 ① native_sim 需主机 gcc（缺）② Zephyr 4.4.0 的 qemu 板 twister 元数据未迁移（`twister.yaml` 缺失），QEMU 运行级测试当前不执行（与 OS 无关的数据缺口）。**运行级测试策略 = WSL2（Ubuntu 就绪，差 `sudo apt install -y build-essential` 一行）+ GitHub CI(Linux)**；Windows 承担构建级。
  - 工作区已钉 **v4.4.0**（原浮动 main，DEC-19 纪律）；网络经代理 127.0.0.1:7897 同步全绿（mbedtls-3.6 曾失败，代理后解决）。
  - 待 owner：① 主机 gcc（WSL 一行命令或 Windows mingw）→ 补 native_sim 构建/twister 运行级验证；② GitHub 远端地址 → CI 上线（M0 完整退出）。
- **2026-09-21（四） · impl 阶段启动：DEC-31（Q-13 禁自建线程）+ C-1/C-2/C-3 确认，规范套件生效（tag `std-v1`）；M0 进行中**
  - 环境深查结论（owner 指示复检，工作区 `D:\Software\project\zephyrproject`）：专用 venv **Python 3.12.13** + west 1.5.0 + Zephyr python 依赖齐；cmake 4.4.3 + ninja 1.13.2；**Zephyr SDK 1.0.1**（交叉工具链全，含 xtensa-esp32s3/arm；hosttools 仅 qemu/openocd，**无主机 gcc**）；WSL2 Ubuntu（Python 3.12.3+venv，**无 gcc**）。
  - **环境缺口（唯一）**：native_sim 需主机 gcc——owner 二选一：① WSL 内 `sudo apt install -y build-essential`；② Windows 装 MSYS2/mingw。补齐前 M0 构建验证用 SDK 交叉工具链（目标板）先行。
  - **纪律处置**：工作区 zephyr 原为浮动 main（v4.4.0+16104），M0 内钉到 **v4.4.0 tag**（DEC-19）。
  - **开发流程计划**（每会话一交付单元 + 同批测试 + CI 绿 + DoD 对照 + 里程碑 review 门）：M0（本会话：环境/骨架/CI/LICENSE）→ M1（ts-core+ts-safety，L5 机械检查脚本与 L4 重放框架雏形）→ M2a（ts-store+TSAP/slot）→ M2b（ts-hal 权限+WAMR 宿主+样例 APP）→ M3a（ts-net）→ M3b（ts-power+ts-periph+集成重放）→ 板级移植（ESP32-S3→P4→H7）。
  - 待办：① owner 补主机 gcc（一行命令）；② M0 收尾（native_sim 构建 + twister 运行）；③ GitHub 远端（DEC-24，CI 上线）。
- **2026-09-21（三） · 裁决批次 4 已登记（DEC-30，tag `dec-30`）：Q-01…Q-12 全部裁毕（DEC-17…30，共 14 项）；仅余 C-1/C-2/C-3 三项文档确认，确认后 M0 开工**
  - DEC-30（Q-11①-⑤ 按建议）：sys 命令面 host-only（estop-clear 确认令牌）；共享写后写胜出 + 审计含 app_id；APP 状态 V1 不持久化；审计 V1 内存环形（掉电丢失）；prov = CBOR schema v1 运行时只读。
  - 设计文档已全面同步 DEC 语义（HLD/LLD 内全部未决项标注收敛为 DEC 编号；各 LLD 未决依赖多数清零）。
  - **最终自检完成（2026-09-21，`design/final-selfcheck.md`，SC-01…04 全处置）——已交 owner 人工检查**。
  - 待 owner：**Q-13**（APP 线程模型，owner 问询触发已呈递：建议禁止自建线程、编译期禁用）+ **三行确认**——C-1 HLD v0.2 确认 / C-2 LLD v0.2 确认 / C-3 规范套件批准（打 tag `std-v1`）。
  - M0 就绪清单：Q-03/Q-10/Q-12 已裁 ✅；GitHub 远端地址待 owner 提供（DEC-24）；宿主环境验证（Windows/WSL2）与 LICENSE 补齐在 M0 内完成。
  - 禁区：C-1/C-2/C-3 确认前不进 impl。
- **2026-09-21（二） · 裁决批次 3 已登记（DEC-27…29，tag `dec-27-29`）：Q-10 全裁 + 板卡策略转向高性能（RP2350 移出）+ 内存预算每板动态；仅剩 Q-11①-⑤ 与 C-1…C-3**
  - DEC-27（Q-10）：14 项按建议；**WAMR 实例堆每板动态配置**（默认值 = HLD §4.6 每板表）；PSRAM 分层纪律生效。
  - DEC-28（板卡策略，修订 DEC-14）：**框架面向高性能高配置板卡；RP2350 移出目标集**（Zephyr 无 PSRAM 驱动 + 520KB SRAM）；目标 = ESP32-S3 / ESP32-P4 / STM32H7 + native_sim。
  - DEC-29（Q-11⑥）：内存预算**每板动态分配计算**（构建期生成，规则见 HLD §4.6）。
  - 待 owner：① **Q-11①-⑤**（sys 命令面 / 共享写后写胜出 / APP 状态不持久化 / 审计 V1 内存环形 / prov CBOR 模型——详解已呈递，请明示同意或逐项例外）；② C-1 HLD v0.2 / C-2 LLD v0.2 / C-3 规范套件批准。**全部落定即 M0 开工**（GitHub 远端地址届时需 owner 提供，DEC-24）。
  - 禁区：上述确认前不进 impl。
- **2026-09-21 · 裁决批次 2 已登记（DEC-25/26，tag `dec-25-26`）；仅剩待裁：Q-10、Q-11 + C-1…C-3 文档确认，全部落定即启动 M0**
  - 已裁：DEC-25（Q-06：V1 = fast 解释器 + WASI 关 + AOT 留作 Agent 构建选项）、DEC-26（Q-07：逻辑节点 V1 仅预留，node 段预留、单立方体时 node = cube id）。正文（HLD §1/§3.4、LLD-ts-appmgr/ts-net/ts-store 等）已同步 DEC 语义。
  - 待 owner：① **Q-10**（15 组工程默认值）/ **Q-11**（6 项语义）——详细解释已呈递（2026-09-21 会话）；② C-1 HLD v0.2 / C-2 LLD v0.2 / C-3 规范套件批准（tag `std-v1`）。
  - M0 前置补充：GitHub 远端地址待 owner 提供（DEC-24）；宿主环境验证（Windows/WSL2）与 LICENSE 补齐在 M0 内完成。
  - 禁区：C-1/C-2 与 Q-10/Q-11 落定前不进 impl。
- **2026-09-20（三） · 裁决批次 1 已登记（DEC-19…24，tag `dec-19-24`）；仍待裁：Q-06/Q-07（已补通俗解释）、Q-10、Q-11 + HLD/LLD 确认 + 规范套件批准**
  - 已裁：Q-03（4.4 + **持续跟进最新 stable**，DEC-19）、Q-04（client；router 宿主扩至 **ARM64 Linux 工业/机器人主板**，DEC-20）、Q-05（TSAP 容器，DEC-21）、Q-08（断链参数因超长物理链路**延长且 prov 可配**：1000ms×6≈6s、WDT 10s，DEC-22）、Q-09（双 slot + MCUmgr，DEC-23）、Q-12（GitHub Actions，DEC-24）。正文相关参数已同步（HLD/LLD/Q-10 表）。
  - 待 owner：① Q-06/Q-07——已按 owner 要求在 decisions.md 补通俗解释，读后裁决；② Q-10（15 组默认值）/Q-11（6 项语义）；③ C-1 HLD v0.2 / C-2 LLD v0.2 / C-3 规范套件（tag `std-v1`）。
  - 待办：上述裁决完成后即启动 M0（依赖 Q-10 部分 CI 值；GitHub 远端地址待 owner 提供，DEC-24）。
  - 禁区：HLD/LLD 确认与 Q 裁决完成前不进 impl。
- **2026-09-20（二） · design review-01 完成（17 项全处置）+ 设计深化批次交付，待 owner review；新增 Q-11、Q-10 增至 15 组**
  - 交付物：`design/design-review-01.md`（逐条审查报告）；缺陷修复批次（TS_FAIL_*/ts_ctx_t/ts_periph_kind_t/keyspace hb 补全/estop DT 绑定/断链恢复语义/审计消费策略）；深化批次（**HLD v0.2**：ts-store 模块行、§4.5 关键场景时序、§4.6 内存预算、sys 命令面、输入采集、V1 裁剪清单；**新增 LLD-ts-store**；LLD-ts-hal §5 input monitor；LLD-ts-appmgr mailbox/停止语义；LLD-ts-net sys 命令表）。
  - 登记增量：**Q-11**（语义批次 6 项）、Q-10 表 #14/#15、names.md（ts-store/TS_FAIL_*/ts_ctx_t/DR 族）。
  - 待办：① Q-03…Q-12 裁决 + HLD v0.2/LLD v0.2 确认 + 规范套件批准（tag `std-v1`）；② M0（west + native_sim + CI，依赖 Q-03/Q-10/Q-12；含 LICENSE 补齐与宿主环境验证）。
  - 禁区：HLD/LLD 确认与 Q 批次裁决前不进 impl。
- **2026-09-20 · LLD 批次（1+7 份）已交付，待 owner review；新增待裁 Q-10**
  - 交付物：`design/LLD-00-common.md`（错误码/线程模型/目录约定）+ 七模块 LLD（ts-core/ts-safety/ts-hal/ts-appmgr/ts-net/ts-power/ts-periph，各含 API 规格/状态机/并发/Kconfig/测试要点/未决依赖）；**Q-10**（LLD 默认值清单 13 组，`decisions.md`）。
  - 处置说明：owner 指令"编写 LLD"视为 design 阶段继续授权；HLD v0.1 与 Q-03…Q-09 **仍未逐条确认**——LLD 内一切未决项以〔Q-xx 提案〕标注，未落定（军规 2）。
  - 待办：① Q-03…Q-10 裁决 + HLD/LLD 确认 + 规范套件批准（tag `std-v1`）；② M0（west 工作区 + native_sim 空模块 + CI 骨架，依赖 Q-03/Q-10）。
  - 禁区：HLD/LLD 确认与 Q 批次裁决前不进 impl（流程 §2.4-②/③）。
- **2026-09-19 · K1 review 经 owner 推进指令视为通过；research v0.2 + HLD v0.1 + 规范套件 v0.1 已交付，全部待 owner review**
  - K1 门处置：owner 指令"深入 research → design → 规范文档"（2026-09-19）视为 K1 review 通过与阶段推进授权；如有误请 owner 纠正，本行即改。
  - 交付物：① research v0.2（R1/R2 增补 §5/§6 二次核验：WAMR 2.4.5/体积/集成、zenoh-pico 1.9/传输/TLS/足迹）；② `design/HLD-firmware-framework.md` v0.1（架构分层 + ts-* 七模块 + 合同逐条映射 + 里程碑 M1…M3）；③ `docs/std/`（README/testing/versioning/progress/coding）；④ 待裁批次 **Q-03…Q-09**（`decisions.md`）。
  - 待办：① Q-03…Q-09 裁决 + HLD 确认 + 规范套件批准（tag `std-v1`）；② M0（west 工作区 + native_sim 空模块 + CI 骨架，依赖 Q-03）；③ M1…M3 按 HLD 实施。
  - 禁区：HLD 确认与 Q 批次裁决前不进 impl（流程 §2.4-②/③）；规范套件 v0.1 未生效前按本文件既有规则执行。

## 2. 会话 bootstrap（每次会话固定执行）

1. 读本文件，重点是"当前状态"节；
2. 读 `decisions.md`，确认未裁 Q；
3. 读当前阶段文档（`docs/research/` 或 `design/`）；
4. 长会话上下文被压缩后，一律以文件现状为准续写，不以记忆续写。

## 3. 项目一句话（详见 FOUNDING_PROMPT §0）

**Tessera**：立方体智能 I/O 模块——基于 Zephyr RTOS 的模块化末端输入输出系统。业务逻辑以**可安装、可迁移的 APP** 形态运行（类安卓：APP 与板卡硬件解耦）；输入输出外设**可插拔**；多个立方体可经扩展面**并联为一个逻辑节点**；物理输出具备**安全限制**；配套 **MCP 形态 AI Agent** 完成"需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署"的完整编程链路。本项目完全由 AI（ZCode）开发，owner 负责裁决与 review。

## 4. 开发流程（摘要；全文见 FOUNDING_PROMPT §2）

- **主线**：research → owner 裁决 → design（规格）→ owner 确认 → impl（实现+测试）→ 阶段退出 review → 下一阶段。
- **阶段产出白名单**：research 只出 `docs/research/*.md` 与 Q 登记；design 只出 `design/` 规格与修订记录；impl 只出规格清单内代码 + 同批测试。**越权产出 = 立即撤回并留痕**。
- **单会话预算**：一个会话交付一个可验证交付单元；超出部分登记待办另起会话。
- **review 门**（必须停下等 owner，不得自裁）：① 一切选型与默认值（先登记 Q）；② 阶段退出（对照 DoD）；③ 公共 API / 文件格式 / 网络协议 / 权限模型变更；④ 安全合同任何改动；⑤ 技术栈变更（须证明阻塞性，附备选对比与迁移成本）。
- **呈递格式（强制，不自包含直接重写）**：背景（现状 + 为何是问题）→ 选项 → 建议 → 影响。
- **决策登记**：`decisions.md`；生命周期 Q-xx → owner 回复 → DEC-xx（附日期与原文）；编号不复用，REJECTED 留档。
- **默认值三问**（写任何常量前自答）：从哪来（Q/推导）？越界会怎样？改动破坏什么？

## 5. 工程纪律（军规十条，违反即流程缺陷）

1. **流程至上**：阶段白名单不越、review 门不闯。
2. **无 Q 不落盘**：未裁决的默认值/选型不得写成"已决定"，不得进代码常量。
3. **文字纪律**：只记录必要内容；必要内容必须**自包含**（现状 + 动因 + 后果三要素齐全），不带会话上下文也能读懂。
4. **编码纪律**：全库文本 UTF-8 无 BOM；批量文本操作显式指定编码；禁用依赖系统代码页的工具。
5. **git 纪律**：每交付单元一提交 + 会话结束兜底提交；里程碑与重大裁决打 tag；失败与回退留痕，禁改写历史。
6. **命名纪律**：跨文档标识符（DEC/Q/M/REQ/模块名/板名）登记于 `docs/names.md`；新造先查碰撞；禁裸单字母作跨文档标识符。
7. **测试同批**：实现与测试同一交付；失败如实报告，禁美化、禁把失败改写为"选择不行动"。
8. **结论落盘**：聊天与记忆不是项目状态；会话结束前把持久结论写入文档/登记册。
9. **顺手重构禁止**：任务外的发现登记不动手，不混入本批交付。
10. **交付即验证**：DoD 对照 + 构建/测试全绿 + lint 通过，才算完成；有缺口如实列出。

## 6. 安全与确定性合同（硬约束；HLD 可细化，不得削弱；v2 · DEC-58 措辞批准 2026-10-13）

1. **三安全态**：每个输出通道（含受控供电）显式声明上电态 / 断链态 / 故障态；无声明不予注册。
2. **写入路径唯一**：一切输出必经保护层校验（限幅 / slew-rate / 限流）后才落驱动；绕过保护层的写入 = 缺陷（须可机械检查）。
3. **断链 fail-safe（部署模式化）**：**被编排的设备**：宿主/网络失联 → 输出进安全态（断链 fail-safe）；**独立运行的设备**：编排通道失联为留痕事件，不改变输出控制权；输入流不因保护而中断（两种模式相同）。部署模式由 provisioning 显式声明，运行时不推断。
4. **看门狗**：超时 → 全输出安全态；每子系统独立喂狗（可定位卡死来源）。
5. **estop 硬件通道**：急停 ISR 直达安全态，**不经协议栈、不经调度排队**；响应时间上界可测；事后补发事件。**清除**：具备本地交互能力的设备以本地清除为主（远程清除可由 provisioning 禁用）；无本地交互能力的设备允许远程清除但须硬令牌确认。清除不解除锁存条件外任何状态、不引发输出。
6. **初始化顺序固定**：任一步失败 → 全系统 fail-safe，不得半启动。
7. **受控供电**（DEC-03）纳入 1–6 同一合同（它是特殊形式的输出）。
8. **并联安全归属**（DEC-02 遗留题）：estop 与保护必须能在**本地设备**独立生效，不依赖逻辑节点内部通信——这是逻辑节点拓扑设计的硬约束。
9. **确定性**：同一输入序列必得同一输出序列（重放测试机械验证）；禁依赖未播种随机、墙钟、容器迭代序。
10. **固件核心不学习**：安全参数、权限模型、输出限值不经运行时自适应修改；APP 权限清单是硬边界，越权访问一律拒绝并留痕。
11. **控制源仲裁**：设备可接受远程编排与本地交互两类控制源。本地交互源激活期间，远程写命令被拒绝；控制权切换本身不产生输出，且全程留痕。estop 硬件通道高于一切控制源（合同 5 不受本条影响）。

## 7. 仓库地图

```text
AGENTS.md           本文件（会话入口）
FOUNDING_PROMPT.md  创始 prompt 原文（K1 起始输入，存档不删）
decisions.md        DEC/Q 登记册
docs/research/      调研文档（R1/R2 产出于此）
docs/names.md       命名空间登记表
docs/std/           开发规范套件（testing/versioning/progress/coding；v0.1 待 owner review，批准后 tag std-v1 生效）
docs/evidence/      真机验证单迹（decisions 引用的 console/JSON/帧图像物理文件；迁移批入仓）
docs/migration-x86.md  环境迁移说明（2026-10-11 WSL→原生 Linux；仓外资产处置 + 清除指引）
design/             规格文档（HLD + LLD-00 + 七模块 LLD；均为 v0.1 草案待 owner 确认）
firmware/           Zephyr 工程（app/ module/ tests/；west 工作区在仓库之外初始化，Zephyr 树不进本仓库；M0 启动）
agent/              MCP server + 模拟器 + 构建工具链（PC 侧；DEC-15 第二阶段）
tools/board/        板级开发工具脚本（构建/烧录/运行/验证/包生成；WiFi 凭据经 TS_WIFI_* 环境变量注入，不入仓）
hardware/           立方体结构 / 连接器 / 电源资料（DEC-15 第三阶段启动）
legacy/             （可选）历史参考资料，NON-NORMATIVE；源自 Galatea 仓库 tag `physio-handoff`
```

## 8. 子代理纪律

委派子代理时提示词自包含；`AGENTS.md` / `decisions.md` / `design/` 的修改权只在主会话。

## 9. 会话结束检查单

- [ ] 交付单元已提交（git log 可溯）
- [ ] 持久结论已落盘（文档/登记册，而非聊天记录）
- [ ] `docs/names.md` 已登记本会话新标识符
- [ ] 本文件"当前状态"节已更新
- [ ] 如触发 review 门：已停在门内并按呈递格式（背景→选项→建议→影响）呈报 owner
