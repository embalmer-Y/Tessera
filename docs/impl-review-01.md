# impl-review-01 · impl 阶段评审报告（2026-09-25）

> **范围**：owner 指令"对之前的开发进行一次 review"。对象 = 2026-09-25 会话四个交付单元：
> ① DEC-40/41/42 实现批（486427c）② MA3.1 部署面（760ddcb）③ MA3.2 skills/平台域/高层链（0773731）④ M3b ts-power/ts-periph/集成重放（4abcdf7）。
> **方法**：验证全量复跑 + 代码走查（safety/power/periph/net/agent 主链文件）+ 文档一致性核对。
> **结论**：验证声明全部复现（全绿属实）；无 P1 阻断项；**8 项发现**（F-1…F-8，分级见下），其中 F-1 为规约-实现差距、F-2 为潜伏缺陷（与 M3b 已修复的悬垂同类）。修复批建议见 §4，待 owner 批准后作为下一交付单元执行。

## 1. 验证复现（2026-09-25 实测）

| 验证项 | 声明 | 复现结果 |
|---|---|---|
| twister（native_sim，10 套件） | 10/10、44 用例 | ✅ 10/10 配置、44/44 用例 passed，29.31s，无告警 |
| L5 机械检查 | 6/6 | ✅ 6/6（唯一写路径/三态完备/禁用模式/常量出处/estop 路径/prov 零写） |
| 固件 pytest | 2/2 | ✅ 2 passed |
| Agent pytest | 58 passed + 2 skipped | ✅ 58 passed, 2 skipped（E2E 门控 skip，符合设计） |
| ruff（agent） | 干净 | ✅ All checks passed |
| skills 同步 | 一致 | ✅ 源文档与 SOURCES.lock 一致 |

工作树干净（`git status` 空）；`[dbg]` 调试 printk 无残留（工作树与 HEAD 均为零处——开发期调试输出已在提交前清除）。

## 2. 发现清单（按严重度）

分级：P1 阻断 / P2 应修 / P3 登记择机 / P4 观察。

### F-1（P2 · 规约-实现差距）periph/预算事件未经 net 外发

- **现状**：`LLD-ts-periph.md:38` 承诺 DETACH 语义含"key 下线通告（**事件外发**）"；但 `src/net/pub.c` 的事件订阅表（ESTOP/SAFE_STATE_CHANGED/PERM_DENIED/INPUT_CHANGED 四类）未包含 `TS_EVT_PERIPH_DETACH/ATTACH` 与 `TS_EVT_POWER_BUDGET`——三事件仅上事件总线（测试直订可见），不经 zenoh 外发。
- **根因澄清**：pub.c:110 注释"事件总线容量 4——四类全占"系**误读**——`src/core/events.c` 的订阅表为 `subs[id][CONFIG_TS_CORE_MAX_SUBS]`，容量按**事件类型分桶**（各 4 位），四类订阅各占不同桶各 1 位，容量充足。即外发是可实现而未实现（遗漏），非容量受限。
- **后果**：外部观察者（Agent/运维面）看不到插拔归因（哪路外设被拔）与供电预算拒绝事件；通道进 SAFE_FAULT 的**状态迁移**有外发（SAFE_STATE_CHANGED）但缺"为何迁移"的归因。DEC-42 的 kind=32+evt_id 信封机制已就绪，仅缺订阅接线。
- **处置建议**：下交付单元补三事件订阅（复用 pub.c `push_evt` 通用路径，payload 携 uid/kind）+ 修正 pub.c 容量注释 + net 测试断言外发信封。

### F-2（P2 · 潜伏缺陷）ts_periph_register 的 GPIO/PWM 路径注册调用方内存指针

- **现状**：`src/periph/desc.c:67` 将 `&d->safe`（**调用方**传入的描述符内嵌通道）注册进 ts-safety；`src/safety/channel.c:55` 存的是指针（`slot->desc = ch`）。调用方若栈上组装 `ts_periph_desc_t` 即悬垂——与 M3b 实现批在 `src/power/slots.c` 已修复的悬垂**同类**（slots.c 改为静态 `pwr_slot_rec` 内嵌通道并留注释）。
- **现状下未爆的原因**：当前调用方（板初始化桩/测试）均用静态存储描述符；POWER 路径经 `ts_power_register_slot` 有静态拷贝，安全。
- **后果**：API 契约含隐式生命周期要求且未在头文件声明；板级移植/新测试极易踩中（正是 M3b 调试期实际踩过的坑）。
- **处置建议**：改为先落静态表再注册——`descs[desc_count] = *d` 后以 `&descs[desc_count].safe` 注册（与 slots.c 同型修复，成功才 `desc_count++`）；或在 `include/ts/periph.h` 契约注释显式声明"描述符（含 safe 通道与 uid 字符串）须静态存储"。

### F-3（P3 · 装配序耦合）sys 命令表 gated 位按数组下标回填

- **现状**：`src/net/cmd.c:951-953` `ts_net_cmd_sys_init` 先逐个 `ts_net_cmd_register`（填首个空位），再 `table[i].gated = sys_cmds[i].gated`——隐式假设注册按序占 0…N。若未来任何框架模块在 sys_init 之前注册命令（表头偏移），gated 位将**错位到别的命令**：最坏情况部署类写命令（app-begin/chunk/verify/activate）未门控 = 绕过租约准入。
- **现状下未触发**：sys_init 是唯一注册方且表为空起步。
- **处置建议**：注册后按 suffix 回查填位（`find_cmd(sys_cmds[i].suffix)->gated = …`，找不到即 BUILD_ASSERT 级装配错误），消除下标耦合。

### F-4（P3 · 语义顺序）idem 回放检查先于 key/op 匹配与租约门控

- **现状**：`src/net/cmd.c:868-885` 幂等命中即回放，先于 886 行 key/op 双重匹配与 898 行租约门控。
- **风险评估**：副作用安全——回放不重执行（DEC-40 本义），缓存回执对应一次**已通过门控**的历史执行，租约过期后重发同 idem 不产生新副作用。残余问题仅语义层面：同 idem 携同 op 可在**别的 key** 上得到回执（如 get-info 的回执出现在 get-budget key 上，调用方自混淆，同信任域内无越权）。
- **处置建议**（可选，低优先）：把 key/op 匹配挪到 idem 检查之前，回放语义更严；不改亦不构成缺陷。

### F-5（P3 · 已知限制）ts_periph_register 注册链无回滚

- **现状**：`src/periph/desc.c:69-83` 末段 `ts_hal_register_dev` 失败时，已注册的 power 槽/safety 通道无注销 API，残留半注册态——同 uid 重试将永远撞名（`TS_E_PARAM`），需重启恢复。
- **影响评估**：板初始化为编译期静态声明、初始化失败即全系统 fail-safe（合同 6），运行期无重试路径，实际影响低。
- **处置建议**：登记为 V1 已知限制（本报告即登记），不为 V1 增加注销面；板级移植若引入动态注册再议。

### F-6（P2 · 流程）里程碑退出未打 tag（军规 5）

- **现状**：现存 tag 全为裁决/规范批次（kickoff、std-v1、dec-19-24…dec-39、dec-wamr-zenoh）；M1/M2a/M2b/M3a/M3b/MA0…MA3 各退出点提交均无 tag。m0 曾有"CI 上线后打"的明确约定（DEC-24 关联），其余里程碑无此约定。
- **后果**：里程碑边界只能靠提交信息考古，违反军规 5"里程碑与重大裁决打 tag"。
- **处置建议**：对历史里程碑退出提交**补打 tag**（`git tag m1 <sha>` 等，不改写历史，安全）；此后每里程碑退出即打（写入各里程碑 DoD 检查单）。具体 sha 清单在修复批中列出呈 owner。

### F-7（P3 · 潜伏，M2b.2 前置检查项）多线程接入前的并发防护复核

- **现状**：`ts_safety_commit` 持 `commit_lock` + 末段 irq_lock；但 `ts_safety_set_link`/`force_channel_fault`/`channel_recover`（`src/safety/channel.c:94-160`）直接遍历/改写通道表**无锁**；`ts_power_request` 的预算检查→提交（`src/power/slots.c:84-106`）存在 TOCTOU 窗口；lease/idem 缓存按"分发串行"假设无锁（有注释）。
- **现状安全的原因**：当前唯一运行期写入方 = net 单线程（zenoh 回调串行分发）+ 测试直调；estop ISR 路径为原子置位设计。
- **后果**：M2b.2 WAMR 多线程 APP 接入后，并发 commit × set_link/recover 可竞态改写 shadow/state；并发 power_request 可瞬时超预算（两笔各过检查后先后提交）。
- **处置建议**：列入 **M2b.2 DoD 前置检查项**——接入前裁定：扩展 commit_lock 覆盖迁移路径 / 或规定 APP 侧写路径全部经 net 命令面单线程化（后者与"APP 直调 hal 能力"的范围裁定耦合，届时登记 Q）。

### F-8（P4 · 观察项）clear_fault 语义复核未闭环

- **现状**：`src/safety/channel.c:162-179` `ts_safety_clear_fault` 仅迁移状态不回写输出值（clear 后物理输出保持 fault 安全值直至下次显式 commit）。代码注释声明"LLD §3 状态机图未明示复位目标态……语义随 M3 net 联调复核"——M3a/M3b 已退出，该项复核未在文档闭环。
- **评估**：行为与 DR-04（恢复不自动回写、须显式 commit）精神一致，倾向**确认现实现为定案语义**，但需把"待复核"注释转为 LLD 正式条款。
- **处置建议**：修复批中同步 LLD-ts-safety（clear_fault 复位语义定案：状态迁移 + 值不回写）+ 移除代码内"待复核"注。

## 3. 走查通过项（正面确认）

- **安全合同映射**：唯一写路径四段完整（限幅→slew→限流→末段临界区复查 forced，`commit.c`）；供电预算 prov 只读、未加载 = 0 = 全拒（缺省即安全侧）；estop 锁存期 `channel_recover` 拒绝（`TS_E_STATE`）；三安全态齐备 + 安全值自身须落 limits 的注册校验；L5 六项机械检查全过。
- **slots.c 静态存储修复**正确、注释留痕、decisions.md 如实登记该缺陷（军规 7 合规）。
- **lease.c** 与 DEC-41 完全一致（惰性过期、lease_id 单调不复用、同 holder 幂等续期、他人不可代还）。
- **cbor 解析 fail-closed**：`ts_cbor_tstr` 超长即拒（`v >= cap` → false），rid/src/idem 无截断别名风险；v1/v2 首键判别 + 未知键/超集/重复键全拒；v1 携 v2 专属键（idem/to/offset/data）拒绝 → 部署面不可能经 v1 绕过。
- **deploy.py**：租约 finally 闭环（release 失败记录 + TTL 兜底说明）；分块 idem + 仅可重试错误重试；verify 事实对拍 fail-closed（缺键即不等）；闭包默认参绑定避开晚绑定坑；自动发现"恰一在线"策略。
- **平台域纪律**：platform.py 零域 import 有 AST 导入图测试守卫；组合根显式注册；app_develop"无签名不产出"硬点在工具内（链外直调同样强制）。
- **文档同步**：names.md 4 新行 / decisions.md M3b 条目（含缺陷如实记录）/ project-plan v1.5 / LLD-ts-power v0.2、LLD-ts-periph v0.3、LLD-ts-net v0.3.4 均与代码一致。

## 4. 处置建议（修复批 = 建议的下一交付单元，待 owner 批准）

| 项 | 动作 | 规模预估 |
|---|---|---|
| F-1 | pub.c 补订阅 PERIPH_DETACH/ATTACH + POWER_BUDGET（push_evt 通用路径，payload 携 uid/kind/预算三元组）+ 修容量注释 + net 测试断言 | 小（净增 ~40 行 + 测试） |
| F-2 | desc.c 改静态表注册（先 `descs[desc_count]=*d` 再注册 `&descs[desc_count].safe`）或头文件契约注释 | 小 |
| F-3 | sys_init 按 suffix 回查填 gated 位 + 装配断言 | 极小 |
| F-8 | LLD-ts-safety clear_fault 语义定案 + 移除代码"待复核"注 | 极小（纯文档 + 注释） |
| F-6 | 历史里程碑补打 tag（sha 清单呈 owner 核后执行） | 极小 |
| F-4 | （可选）key/op 匹配前移至 idem 检查前 | 极小 |
| F-5/F-7 | 登记（本报告即登记处）；F-7 写入 M2b.2 DoD 前置检查项（project-plan 补一行） | 极小 |

批内验证：twister 全量 + L5 + pytest ×2 + ruff + skills sync（与本报告 §1 同口径）。

## 5. 处置结果（2026-09-25 修复批，owner 批复"严格按照大型项目标准规范修复这些问题"）

F-1/F-2/F-3/F-4/F-8 代码修复 + F-6 十个里程碑 tag 补打（m0…m3b/ma0…ma3）+ F-5/F-7 登记落位（LLD 已知限制 / project-plan M2b.2 开工前置检查项）；新增测试 framework.net test_11 + framework.periph test_04 + test_07 扩展；派生定容一处（pubq PAYLOAD_MAX 64→128B，溯源见 LLD-ts-net §5）。回归全绿：twister 10/10（46 用例）/ L5 6/6 / pytest ×2 / ruff / skills sync。文档同步：LLD-ts-net v0.3.5 / LLD-ts-periph v0.4 / LLD-ts-safety v0.2.3 / project-plan v1.6 / decisions.md 修复批条目 / AGENTS.md（十三）。明细见上述登记处。

---
*登记：docs/names.md（impl-review-01）；AGENTS.md 当前状态已同步。修复批未获批准前不动代码（军规 9）。*
