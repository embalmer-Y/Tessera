# G1 · Agent CLI 代码生成可靠性工程调研 → Tessera 实现映射——报告

> **日期**：2026-10-04 · **触发**：owner 指令（Q-25 → DEC-45 方案 A + "研究其他 Agent CLI 的工程方法保证 coding 可靠性"）。
> **结论**：调研八条实践（R1-R8）全部映射进 G1 实装；真 LLM 全链（SMOKE3）双轮贯通。

## 1. 调研发现（Claude Code / OpenAI Codex CLI / aider / agentic-patterns 文献）

| # | 业界实践 | 来源要点 |
|---|---|---|
| R1 | **可运行验证优先**：给 agent 测试/构建/linter 作判据，要证据不要宣称——"watched session 与 walk-away session 之分"；Stop hooks/条件门做确定性闸 | Claude Code best practices（code.claude.com/docs/en/best-practices）；agentic-patterns.com CI 反馈环 |
| R2 | **工具契约 + 错误反馈回路**：linter 契约 = 文件名入参、错误进 stdout/stderr、非零退出；编译器输出喂回 agent 自修（有界尝试） | aider lint-test 文档；agentic-patterns |
| R3 | **编辑格式按模型能力分级**：whole / search-replace / udiff 多格式；**弱模型用 whole-file 最可靠**（部分编辑易错位/elision）；hash 锚定与 AST 改写降低坏补丁率 | aider edit-formats 文档；arxiv 编码代理解剖（13 种注册编辑格式） |
| R4 | **沙箱与最小权限**：full-auto 的安全性来自 OS 级隔离（Landlock/Seatbelt/网络禁用容器/目录受限）——自动化程度越高，隔离越硬 | Codex CLI 分析（Simon Willison 等）；open-codex |
| R5 | **确定性验证门 + 显式停止条件**：验证步独立于生成步；两次纠正失败即停止换策略（防无限循环）；长跑工作须有监督契约 | Claude Code practices；Wink 故障分类研究（arxiv 2026-02） |
| R6 | **根因优先**："address the root cause, don't suppress the error"——错误信息完整给模型而非摘要美化 | Claude Code best practices |
| R7 | **writer/reviewer 分离与上下文隔离**：实现者与复审者分会话/subagent，复审只报影响正确性的缺口 | Claude Code subagent 模式 |
| R8 | **留痕可回溯**：每改动配 git 提交/测试结果记录，产物带证据链 | aider git 集成；Codex 审计 |

## 2. 映射到 Tessera G1 的工程决策（`tools_tsap/wasm_build.py` + `app_chain.py`）

| 研究 | 落点 |
|---|---|
| R1 | **验证阶梯四道确定性门**：clang 编译（固定 flags）→ 面检查（导入 ⊆ natives 六白名单、必需导出齐、尺寸 ≤ 16KB）→ **双编译字节一致**（确定性自证——合同 9 精神延伸到工具链）→ tsap_verify 验签；全部机器判定，产物即证据（面报告/摘要进结果与审计） |
| R2/R6 | 编译器 **stderr 完整保留**进错误 detail（-4000B）喂回 LLM 反馈回路（预算 3，MD0-1 已验模式）；不截断不美化 |
| R3 | **source_c = 整文件再生**（单文件小 APP 域 whole 最可靠；不做 diff/搜索替换块）——G1 spike + SMOKE3 四轮 LLM 产出零编辑错位佐证 |
| R4 | 编译子进程**固定参数、零网络诉求、时限 kill（60s）、产物不执行**（wasm 只产不跑）；输出目录 roots 白名单（IR-13 既有） |
| R5 | 面检查 fail-closed（白名单外导入/缺导出/超尺寸/非确定性 = 一票拒绝）；3 轮反馈不收敛 = 如实失败上抛（军规 7 同源） |
| R7 | 复审者 = 确定性检查器（本轮）+ MD1 的 scenario 重放期望（独立验收者，LLM 不判自己） |
| R8 | 产物摘要含 source_sha256/imports/exports/size/deterministic → audit 流 + task 日志 |

## 3. 实装清单（本批）

- `tools_tsap/wasm_build.py`：零依赖 wasm 面解析器（llvm-objdump-18 解析不了 strip 后 wasm——G1 spike 实证，仓库夹具对照校准）+ `compile_app_c()` 全检查链。
- MCP 工具 **`app_compile`**（auto 类：本地确定性构建，无网络无部署）。
- **`app_develop` 契约扩展**（DEC-45）：DevelopOutcome 增可选 `source_c`；wasm_path 变可选；链内编译并入反馈回路；输出增 compiled/compile_facts/source_sha256；系统提示内联 C 侧约定（导出名/六 natives 签名/自由固件约束）+ app_id 禁下划线（SMOKE 实证）。
- 测试 +11（pytest 69 passed）：解析器夹具锚定/同源不变量（native_app.c 编译面 == 随仓 .wasm 面）/编译错误反馈/白名单拒/缺导出拒/尺寸拒/越界拒/空源拒/链内编译打包用编译产物。**无静默 skip**（板级十教训）——clang 为硬依赖（CI agent-checks 显式保障）。

## 4. 真 LLM 全链验证（SMOKE3 ×2 轮，MiniMax-M3）

spec（按键翻转 LED + 变化时报日志）→ LLM 产 manifest+source_c →（第 1 轮 heap_kb=0 瑕疵 → 反馈回路修正）→ 第 2 轮通过 → 链内编译 PASS → 打包验签 PASS。两轮产物 646B/456B（实现不同均合规），imports [ts_gpio_write, ts_log_write] 白名单内，四回调导出，双编译一致。**"需求→设计→编程→打包"AI 全链首次贯通**——MD0 前置全部完成。

## 5. 来源

- Claude Code best practices（code.claude.com/docs/en/best-practices）
- aider edit-formats / lint-test 文档（aider.chat）
- Codex CLI 沙箱分析（simonwillison.net 2025-11；openai 安全文档）
- agentic-patterns.com（CI 反馈环模式）；Wink: Recovering from Misbehaviors in Coding Agents（arxiv 2026-02）
