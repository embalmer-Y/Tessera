# Agent demo 就绪度评估 · 现有实现 review——单元报告

> **日期**：2026-10-02 · **触发**：owner 指令（"为 AI Agent 创建一系列 demo，从简单到复杂还有混合的各种应用各做一个小 demo；先 review 现有实现并评估；Agent 是否实测过真实 LLM 调用"）+ 计划调整（H7 放弃 → P4 恢复）。
> **性质**：评估报告（零产品代码改动）。全部结论以代码/文件实证为据。

## 1. 直答：真实 LLM 调用从未实测（证据五条）

1. **全部测试 = FunctionModel 剧本**（pydantic-ai 测试替身，4 个测试文件使用）；pytest 58 passed 无一次真实模型调用。
2. **`agent/config.toml` 不存在**（仅 `config.example.toml` 模板；真实配置文件 gitignored，从未创建）。
3. **`agent/audit/` 目录不存在**——审计双流落盘目录（app_develop/app_deploy 生产运行必写）从未产生过任何痕迹。
4. `common/config.py` 启动期硬检查：`providers.default_model` 为空即 `ConfigError`——真实链路从未被启动过。
5. 依赖已具备：`pydantic-ai-slim[openai,anthropic,google,mcp]==2.47.*` 已声明，支持 openai:/anthropic:/ollama: 模型串与 OpenAI-compatible 自定义端点。

**补测所需（owner 依赖二选一）**：① 本地 `ollama` 拉一个 ≥32k 上下文模型（config 模板默认示例 `ollama:qwen3`）；② 提供 OpenAI-compatible 端点 + key（环境变量注入，不入 config.toml）。补测内容建议 = app_develop 真跑一单（spec → LLM 产出 DevelopOutcome → manifest 硬校验 → 打包复验）+ skill 渐进披露的 read_skill 调用观测。

## 2. 现有实现 review（demo 视角）

### 2.1 已就绪（可直接支撑 demo）

- **部署链全绿**：app_deploy（复验→发现→分块→激活→确认）真机闭环（板级十，双轮）；deploy_*/sys_*/task_* MCP 工具面完整。
- **运行时四回调 + mailbox**（DR-14 串行化）：app_init / app_tick（100ms 周期）/ app_evt（mailbox 事件）/ health_ping（1s 探针，3 败自停回滚）——demo 的行为骨架齐全。
- **natives 面（6 个）**：ts_gpio_write/read、ts_pwm_set、ts_adc_read、ts_time_ms、ts_log_write——LED/PWM/ADC/时间/日志类 demo 的 API 面已够。
- **wasm 工具链在位**：clang 18（WSL `/usr/bin/clang`）+ 成熟构建模式（`firmware/tests/app/appw/build.sh`：`--target=wasm32 -nostdlib -Wl,--no-entry --allow-undefined`）。
- **模拟器（A04）**：scenario schema（输入时间线 + 期望集 eq/within/count + seed 确定性）+ sim_run L4 重放——demo 可"先仿真后真机"两段式展示。
- **skills 渐进披露**：4 skill（workflow/build/tsap/safety）+ SOURCES.lock 同步守卫——LLM 系统提示可注入权威规范。

### 2.2 缺口（demo 批前置，按严重度）

| # | 缺口 | 现状 | 影响 | 处置 |
|---|---|---|---|---|
| G1 | **APP 代码生成不在链内** | `app_develop` 的 V1 边界 = LLM 只产出 manifest/计划/安全注记，**wasm 由调用方提供**（app_chain.py 头注 + `wasm_path` 参数）——"需求分析→软件设计→**编程开发**"链断在第三环 | 所有"AI 生成 APP"类 demo 无法自动化；现状只能手工写 C→wasm 后交给链 | 新开发单元：LLM 产 C 源 + `app_compile` 工具（clang wasm32 封装 + 导入面白名单/尺寸检查）+ app_develop 语义升级；**工具面变更 = 门 ③ 呈递** |
| G2 | 真实 LLM 未测（§1） | 全 FunctionModel | LLM 侧的不确定面（结构化输出命中率/重试预算 3 是否够/skill 阅读行为）完全未验证 | owner 配模型 → 冒烟批（MD0） |
| G3 | input monitor 真输入未接 | ts_gpio_read 影子桩（板级三登记） | ADC/GPIO 输入类 demo 真机读不到真值 | 板级十三（已排） |
| G4 | V1 单活跃 APP | 单 slot 活跃 + 回滚 | "多 APP 混合"demo 只能做**单 APP 多能力混合**，不能多 APP 并存/互发 msg（ts_msg_send 未编入 natives） | demo 阶梯按单 APP 设计；多 APP = V2 事项 |
| G5 | 模拟深度 | scenario 为通用通道时间线（M3b 后无扩展） | 状态机复杂 demo 的仿真正常可用；PWM/ADC 真值仿真受桩面限制 | 按 demo 需要逐个补场景（观察后定） |

## 3. Demo 阶梯（评估稿——MD 批次的实施底稿）

分级原则：简单=单能力单向；中=输入或反馈单环；复杂=闭环控制/生命周期；混合=多能力 + 链路/安全事件交织。

| 级 | demo | 能力面 | 前置 |
|---|---|---|---|
| D1 | LED 开关/闪烁（tick 驱动） | gpio:write + tick | G1/G2（全自动）或手工 wasm（现在即可） |
| D2 | 健康心跳与远程观测 | health_ping + sys get-info/get-app + 遥测 | 无 |
| D3 | PWM 呼吸灯（斜坡 + 限幅演示） | pwm:set + tick + 保护层 clamp 真实生效 | 无 |
| D4 | ADC 采集与变化上报 | adc:read + evt + 遥测 | G3（真机真值） |
| D5 | 安全演示三联 | 越权 caps 拒绝留痕 / estop 交互 / 断链 fail-safe 恢复 | 无（板级七/八/九能力现成） |
| D6 | 滞回/PID 控制环 | adc→逻辑→pwm 闭环 + 限幅/速率 | G3 |
| D7 | 健康失败自动回滚 | app_evt 置病 → 探针 3 败 → 回滚切 slot | 无（框架已实现，缺演示编排） |
| D8 | 全生命周期混合 | app_develop(LLM) → sim_run 仿真 → app_deploy 真机 → v2 升级 → 回滚 | G1+G2 |
| D9 | 输入-逻辑-输出 + 断链时间线 | D6 + 强制断链 → fail-safe → 自愈恢复全时间线 | G3 + 板级七能力 |

每个 demo 建议双载体：scenario（仿真验收）+ 真机部署（DB 链复用）。

## 4. 计划调整（本批 owner 指令）

1. **H7 适配放弃**（原板级候选；docs/h7-memory-assessment.md 保留为历史评估）。
2. **P4 恢复为第二目标板**（动机 = APP 复杂性余量：esp32p4_function_ev_board = RISC-V 双核 HP@400MHz + 16MB flash + 8MB PSRAM）。**硬前置事实（Q-24 调研钉死）**：Zephyr v4.4.0 **无 esp32p4 SoC 支持**（4.5 加入）→ P4 批 = Zephyr 升级（4.4.0→4.5+，**门 ⑤ 技术栈变更呈递**：迁移面评估 + 全量回归）先行。
3. **MD demo 批**（"全部功能开发完成后"进入）：MD0 = 前置补齐（真实 LLM 冒烟〔owner 模型配置〕+ G1 APP 代码生成链〔门 ③〕）；MD1 = D1-D7 阶梯实现（每 demo = 源码 + scenario + 真机验证 + 文档）；MD2 = D8/D9 混合 + 演示编排收口。

## 5. 建议

- **MD0 的真实 LLM 冒烟建议提前**（不必等 P4）：owner 提供 ollama/端点任一即可，一小时内可完成冒烟批——它暴露的问题（结构化输出、skill 行为）越早知道，G1 的设计越准。
- 排期序（修订）：板级十一~十四（S3 生产化）→ Zephyr 升级 + P4 适配 → MD0-MD2（demo 批）。
