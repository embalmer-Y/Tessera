# impl-review-m2a-ma2 · MA0/MA1/MA2 + M2a/M2b 实现审查记录

> **状态**：v1.0 · 2026-09-22 · owner 指令"review 之前几次未进行 review 的代码，确认没问题后继续开发"触发。
> **对象**：MA0（814a6ce）/ MA1（9183bf3）/ M2a（cc65dc9）/ MA2（4b07964）/ M2b（04bed8c）五笔交付的 agent 侧（tessera_agent 全包）与固件侧（ts-store/TSAP/ts-hal/ts-appmgr）代码 + 测试。
> **方法**：逐文件复查（重点：安装链安全语义、边界/整数回绕、错误传播、fail-open/fail-closed 方向、设计符合性对照 HLD/LLD、密钥纪律）。编号接续 impl-review-m1（IR-01…04）。

## 一、已修复缺陷（IR-05…IR-14，随本批交付）

| # | 级别 | 位置 | 发现 | 处置 |
|---|---|---|---|---|
| IR-05 | **缺陷（高）** | `src/appmgr/pkg.c` | `verify_cose_minimal` 为 **fail-open 桩**：只查 COSE 结构前缀（0xd2/0x84）即返回 TS_OK——真实验签（M2b.2）接入前，任何带伪 COSE 头的包都可安装 | 改 **fail-closed**：非 `CONFIG_TS_TEST` 构建一律 TS_E_INVALID_SIG；测试构建（全部 twister 套件）仍走结构级通过以驱动 slot/meta 链路测试 |
| IR-06 | **缺陷（高）** | `include/ts/tsap.h` | 边界检查 `v->cose_off + 1 > len` 在 cose_off==UINT32_MAX 时 u32 回绕为 0 → 越界检查失效，pkg.c 后续以回绕长度做 OOB 读 | u64 域比较（`total + 1 > (uint64_t)len`）；新增用例：总长恰为 UINT32_MAX 的构造头必须拒绝 |
| IR-07 | 加固（中） | `src/store/part.c`、`src/store/slot.c` | `off + len > size` 在 u32 域可回绕（内部调用方当前均为小值，防御性） | 统一改减法形式 `off > size \|\| len > size - off` |
| IR-08 | 缺陷（中） | `src/hal/api.c` | `ts_pwm_set` 的 hz 打包进 u16（值/100）无域检查：hz>6,553,500 静默截断；permille>1000 无检查 | 超域 → TS_E_PARAM；新增用例（pwm 范围 + 打包值经安全层往返一致） |
| IR-09 | 缺陷（中） | `src/appmgr/slot.c` | 回滚路径 `ts_appmgr_meta_write` 返回值被忽略——写失败时运行态已切 slot 而持久 meta 未切（分叉） | 传播错误 + 运行态全量回退（slot/计数/状态，状态取 prev_state 而非硬编码 ACTIVE） |
| IR-10 | 缺陷（低） | `src/store/prov.c` | prov 的 estop 标志 u32→u8 静默截断 | >0xFF → TS_E_IO（拒绝整条 prov） |
| IR-11 | 文字（低） | `src/hal/perm.c` | 注释声称支持 `"*"` 与 "msg name V1 按 0 处理"，代码实态是数值文法、其余 fail-closed 拒绝 | 注释改为实态（不允许声明未实现的能力形态） |
| IR-12 | 文字/接口（低） | `src/store/noinit.c`、`tools_sim/runner.py`、`gateway/server.py` | ① noinit 注释残留"文件路径"字样（RAM 后端前史）；② runner docstring 仍称"west twister 运行"（实态=west build + 直接二进制）；③ `sim_run(rebuild=…)` 参数从未生效（静默死参数） | ①② 注释修正；③ 移除参数（对齐 HLD 工具面，非语义变更） |
| IR-13 | 缺陷（中） | `tools_tsap/tools.py` | `tsap_package` 产物目录无白名单（keygen 有）——可向白名单外写 .tsap 产物 | 提炼 `_resolve_within` 共用助手，keygen/package 同纪律；新增越界拒绝用例；server 侧白名单根 = workspace（`AppContext.write_roots`，默认 workspace、测试注入 tmp 根） |
| IR-14 | **缺陷（高，设计符合性）** | `gateway/server.py` | HLD §5.1 将 `tsap_keygen` 列为 **strict 类**（必须宿主显式批准，超时拒绝），但 MCP 网关面直行执行——审批闸基础设施（ApprovalBroker/sys_approve）在位却无工具过闸（core 层 `gated_tool` 存在但服务 agent 内循环，MA3 才有消费者） | tsap_keygen 改 **句柄化 + input_required**：任务挂起 → `sys_pending_approvals` 呈现 → `sys_approve`（token）→ 放行执行 / deny·超时 → 任务 failed(TA_E_APPROVAL_DENIED)、无密钥产出；E2E 双路径测试（MCP 客户端实测） |

## 二、登记不修（后续单元处置）

| # | 级别 | 发现 | 去向 |
|---|---|---|---|
| IR-15 | 限制（记录） | `pkg.c` 安装链计算整槽 hash 但未持久化/未与 manifest 比对——启动期无 slot 完整性校验 | M2b.2（manifest CBOR 解码 + wasm hash 比对 + 启动期校验一并落地） |
| IR-16 | 限制（记录） | `ts_log_write` 未过权限裁决（V1 空桩） | M3 日志面真实化时接入 sys 类裁决 |
| IR-17 | 限制（记录） | Agent 侧 manifest `caps` 未做 ts_perm_v1 文法预校验（固件装时拒绝，fail-closed，仅反馈偏晚） | MA3 app_develop 链（早期反馈） |
| IR-18 | 限制（记录） | scenario `t_window_ms` 字段未参与期望评估（runner 只取末值） | M3/MA3 输入注入联动 |
| IR-19 | 限制（记录） | `ts_appmgr_install` 无 app_id 唯一性检查（当前无运行时加载方，重复安装=覆盖语义未定义）；`ts_hal_bind_context` 无重复 app_id 查重 | M2b.2 WAMR 生命周期时定 |
| IR-20 | 限制（记录） | `ts_store_noinit_put` 返回 void（写失败不可观测；留痕 best-effort 语义，丢失=下轮 fresh） | 留观（低风险诊断面） |

## 三、复验（全绿）

- twister @ native_sim：**7/7 配置 26/26 用例 100%**（含 IR-06/IR-08 新用例）
- L5 机械检查：**6/6**（prov 零写不受 IR-10 影响）
- 生产构建：app @ native_sim（无 CONFIG_TS_TEST，含 IR-05 fail-closed 分支）编译链接绿
- 固件 pytest 2/2；agent pytest **34 passed + 1 skipped**（E2E 仿真按设计 env 门控）+ ruff 全绿
- 编码检查：UTF-8 无 BOM 违规 0

## 四、结论

五笔交付中登记的已知限制（WAMR=M2b.2、msg 类文法、deploy_* 未实现）与文档一致；本次发现的实质缺陷集中在**安全边界的方向性**（fail-open 桩、审批闸未接线、边界回绕）与**错误传播**（回滚 meta、参数截断），全部随本批修复并补测试。审查后 M2a/M2b/MA0-MA2 达到"本地全绿 + DoD 对照"退出条件；M2b.2（WAMR）仍为登记的未完成依赖（IR-05/15/19 与其关联）。

## 修订记录

- v1.0 · 2026-09-22：初版（IR-05…20 全处置：修复 10 项 + 登记 6 项）。
