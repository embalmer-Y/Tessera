# AGENTS.md · Tessera 会话入口

> **本文件是什么**：每个开发会话（ZCode）的第一入口。由 K1 依据 `FOUNDING_PROMPT.md` v1.0（2026-09-18）改写生成。
> **权威顺序**：owner 最新裁决（`decisions.md` 中的 DEC）> `FOUNDING_PROMPT.md` > 本文件摘要。若本文件与上述冲突，以裁决/原文为准，并登记 Q 修正本文件。
> **维护规则**："当前状态"节每会话结束前更新；本文件的修改权在主会话。

## 1. 当前状态

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

## 6. 安全与确定性合同（硬约束；HLD 可细化，不得削弱）

1. **三安全态**：每个输出通道（含受控供电）显式声明上电态 / 断链态 / 故障态；无声明不予注册。
2. **写入路径唯一**：一切输出必经保护层校验（限幅 / slew-rate / 限流）后才落驱动；绕过保护层的写入 = 缺陷（须可机械检查）。
3. **断链 fail-safe**：宿主/网络失联 → 输出进安全态；输入流不因保护而中断。
4. **看门狗**：超时 → 全输出安全态；每子系统独立喂狗（可定位卡死来源）。
5. **estop 硬件通道**：急停 ISR 直达安全态，**不经协议栈、不经调度排队**；响应时间上界可测；事后补发事件。
6. **初始化顺序固定**：任一步失败 → 全系统 fail-safe，不得半启动。
7. **受控供电**（DEC-03）纳入 1–6 同一合同（它是特殊形式的输出）。
8. **并联安全归属**（DEC-02 遗留题）：estop 与保护必须能在**本地立方体**独立生效，不依赖逻辑节点内部通信——这是逻辑节点拓扑设计的硬约束。
9. **确定性**：同一输入序列必得同一输出序列（重放测试机械验证）；禁依赖未播种随机、墙钟、容器迭代序。
10. **固件核心不学习**：安全参数、权限模型、输出限值不经运行时自适应修改；APP 权限清单是硬边界，越权访问一律拒绝并留痕。

## 7. 仓库地图

```text
AGENTS.md           本文件（会话入口）
FOUNDING_PROMPT.md  创始 prompt 原文（K1 起始输入，存档不删）
decisions.md        DEC/Q 登记册
docs/research/      调研文档（R1/R2 产出于此）
docs/names.md       命名空间登记表
docs/std/           开发规范套件（testing/versioning/progress/coding；v0.1 待 owner review，批准后 tag std-v1 生效）
design/             规格文档（HLD + LLD-00 + 七模块 LLD；均为 v0.1 草案待 owner 确认）
firmware/           Zephyr 工程（app/ module/ tests/；west 工作区在仓库之外初始化，Zephyr 树不进本仓库；M0 启动）
agent/              MCP server + 模拟器 + 构建工具链（PC 侧；DEC-15 第二阶段）
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
