# LLD-A04 · 模拟器与重放（sim_*）· v0.1 草案

> **上游**：HLD-agent §2/A04；决策 DEC-13（模拟深度 = native_sim + 外设桩，数字孪生-lite）、DEC-36②（句柄化）。固件侧对接：M1 交付的 L4 重放框架雏形、ts-periph 外设桩（M3b 扩展深度）。

## 1. 场景模型（Scenario）

- 场景文件 = JSON（schema 版本化 `scenario_version: 1`），三段：
  - `inputs[]`：事件序列——{t_ms（虚拟时刻）, channel（输入通道逻辑名）, value}；按 t_ms 升序为不变量（校验拒绝乱序）。
  - `expectations[]`：输出断言——{t_window_ms, channel, op: eq/within/count, value}。
  - `meta`：{firmware_commit?, boards?, seed?（透传固件重放语义）}。
- `sim_validate_scenario` = Pydantic 校验 + 语义校验（通道名在固件测试配置面内、时间窗非负）。
- 场景存放：`agent/scenarios/*.json`（入库，可版本化评审）。

## 2. 运行器（sim_run，confirm，句柄）

- 执行链：确保 native_sim 构建（复用 fw_build 产物或触发重建，rebuild 参数控制）→ 以**重放模式**运行固件测试二进制（对接固件侧 L4 重放入口——输入注入与输出捕获的机制随 M1 定稿，本层只约定接口）→ 收集输出时序 → 断言评估 → 报告。
- 接口约定（供固件 M1 参考）：Agent 侧需要固件测试二进制支持"输入文件进（stdin 或 argv 路径）、结构化输出出（stdout JSONL 或出口文件）、退出码表结果"三件事；具体协议在 M1 L4 设计时共同定稿（登记为未决依赖，MA2 前对齐）。
- **确定性要求**（合同 9 同构）：同场景两次运行输出逐字节一致（时间戳由虚拟钟驱动）；报告含 determinism: bool 字段（两次内部重跑比对，V1 直接内建〔Q-19 提案 12〕）。

## 3. 报告

- result：{scenario, build_info, assertions: {pass, fail, details[]}, timeline_digest（sha256——重放指纹）, determinism}。
- 失败断言带窗口与实际值；timeline 全量入任务日志（超限截断规则同 A00）。

## 4. 外设桩深度演进

- V1（MA2）：框架级重放（M1 L4 钩子）——数字量输入/输出序列。
- 随 M3b：ts-periph 桩描述符驱动的外设级仿真（ADC 波形、通信外设帧）——场景 schema 预留 `channel_kind` 字段扩展位。

## 5. 测试要点（L7）

- 场景校验矩阵（schema 错/乱序/未知通道）；断言评估器单测（eq/within/count/窗口边界）；determinism 检测（人为注入非确定性输出必须被捕获）；与 native_sim smoke 的集成（MA2 退出）。

## 6. 未决依赖

- 固件 M1 L4 重放入口协议（§2 接口约定——MA2 前共同定稿）；固件 M3b 外设桩；Q-19 提案 12。
