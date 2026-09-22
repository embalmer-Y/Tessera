# impl-review-m1 · M1 实现自检记录

> **状态**：v1.0 · 2026-09-22 · owner 指令"请你进行review检查然后继续进行开发"触发（M1 退出 review 门内的自检处置留痕）。
> **对象**：提交 `59b0a82`（M1 交付）的 firmware/module/tessera 源码 + 测试 + L5 脚本。
> **方法**：逐文件复查（重点：并发路径、estop 竞争、锁存生命周期、审计一致性、L5 脚本边界）。

## 发现与处置（IR-01…IR-04）

| # | 级别 | 发现 | 处置 |
|---|---|---|---|
| IR-01 | **缺陷（高）** | `ts_safety_clear_fault` 在 `forced≠0` 时直接拒绝，而没有任何路径复位 forced → **estop 一次即永久锁死**（重启前 clear 永远失败）。LLD §5 原意是"复位只经 clear_fault 发生"，非"clear 也被拒" | 已修：clear_fault = 锁存唯一释放路径（复位 forced + estop 补发宣布位 + 条件恢复状态）；测试更新（清除→恢复 ACTIVE→写路径恢复→二次 estop 可再锁存） |
| IR-02 | 缺陷（中） | commit 末段临界区发现 forced 置位时跳过写回，但返回值/审计仍记 TS_OK——审计会记录一次从未落驱动的"成功"提交 | 已修：`written` 标志，未写回 → res=TS_E_STATE 并如实审计 |
| IR-03 | 限制（记录） | `ts_safety_audit_copy` 无锁读取环形（与 commit 并发理论上可撕裂） | V1 已知限制：单读消费（遥测/导出，M3 接入时加锁或经 sysworkq 串行化）；native_sim 单核抢占下实际风险极低 |
| IR-04 | 说明（记录） | estop ISR 的 DT 粘合（driver_dispatch.c `#if DT_NODE_EXISTS` 分支）在 native_sim 无节点 → 未被执行覆盖 | 板级移植阶段（真机 estop 引脚）补 HIL 验证；已列板级前置项 |

## 复验（全绿）

- L5：5/5；app @ native_sim 构建绿；twister **4/4 配置 100%**（含更新后的 estop 释放/再锁存用例）；仓库 pytest 绿；编码检查绿。

## 结论

IR-01/02 修复后，M1 交付满足退出条件（本地全绿 + DoD 对照 + 收敛留痕完整）；IR-03/04 登记为已知限制/后续验证项。M1 退出随本记录 + owner"继续开发"指令生效。

## 修订记录

- v1.0 · 2026-09-22：初版（IR-01…04 全处置）。
