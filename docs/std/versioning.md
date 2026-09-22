# 版本与 git 规范（versioning.md）· v0.1 草案

> **状态**：v0.1 草案，随规范套件待 owner review（见 `README.md`）。生效后修改须走规范变更流程。
> **上位文件**：`AGENTS.md` §5 军规 5；`FOUNDING_PROMPT.md` §2.5。

## 1. 分支模型

- **main = 唯一长线**：每个可验证交付单元一提交（军规 5）；main 任何时候都应可构建（配合 CI 门）。
- **短命任务分支**：仅 impl 阶段的长任务（跨多交付单元）使用，命名 `fw/m<里程碑>-<主题>`（如 `fw/m1-safety-statemachine`）；合并前 CI 全绿，合并后即删。
- **禁止**：改写历史（rebase 已推送提交、force push）；在 main 上做半成品多提交长跑（拆单元提交）。

## 2. 提交规范

- 格式：`<type>(<scope>): <一句话主题>`，正文说明动因与影响（自包含三要素：现状/动因/后果）。
- type：`feat`（新功能）/ `fix` / `docs` / `test` / `refactor` / `build`（构建/CI/west）/ `chore`。
- scope：模块名（`ts-safety`…）或区域（`design`、`std`、`research`、`decisions`）。
- 节奏：每交付单元 ≥1 提交；会话结束兜底提交（军规 5）；失败与回退同样提交留痕（`fix:` + 原因），**禁删库重来**。

## 3. tag 策略

| 类别 | 格式 | 示例 | 打点 |
|---|---|---|---|
| 里程碑 | `m<编号>` | `m1` | 里程碑退出 review 通过时 |
| 重大裁决 | `dec-<主题>` | `dec-wamr-zenoh`（已存在） | DEC 登记完成时 |
| 固件版本 | `fw-v<X.Y.Z>` | `fw-v1.0.0` | 固件发布 |
| 规范版本 | `std-v<X>` | `std-v1` | 规范套件生效时 |

- 固件 semver 语义：**X** = 破坏性变更（公共 API / APP 包格式 / 网络协议语义——对应 review 门 ③）；**Y** = 向后兼容的功能；**Z** = 修复。
- APP 包版本：内嵌于包 manifest（DEC-05），比较规则随 Q-05 裁决定稿；固件不内嵌 APP 版本。

## 4. 外部依赖钉住（west manifest）

- WAMR、zenoh-pico 经自管 west manifest 引入，**revision 一律钉具体提交 SHA 或上游 release tag**，禁 `main`/`master` 浮动引用。
- 升级 = 独立 `build(deps):` 提交，说明升级动因（安全修复优先）+ 回归范围；WAMR minor 含 breaking changes（R1 v0.2 核验），升级前查 release notes。
- Zephyr 版本基线 = **4.4**（DEC-19），并按 owner 指令**持续跟进最新 stable**：每个 Zephyr release 评估升级，升级走显式提交 + 全量回归（钉住具体版本，禁浮动引用）；变更走技术栈变更门（§2.4-⑤，须证明阻塞性）。

### §4.1 Python 依赖钉住（agent/；DR-18，MA0 增补）

- agent/ 的 Python 依赖经 `agent/pyproject.toml` 钉版，**出处 = Q-19 #1 / DEC-38**：`pydantic-ai-slim[openai,anthropic,google,mcp]==2.47.*`、`fastmcp==4.0.*`、`cbor2==6.1.4`、`pycose==1.1.0`、`cryptography>=42`、`eclipse-zenoh==1.10.1`（**三方同 minor**：zenohd router / zenoh-python / 固件 zenoh-pico，DR-22）；禁浮动引用。
- 升级 = 独立 `build(deps):` 提交 + agent 测试全量回归；eclipse-zenoh 升级还须三方协同（牵动固件 M3a）；技术栈级变更走 §2.4-⑤ 门。
- 虚拟环境：`~/project/agent-venv`（独立于固件 venv，见 `docs/dev-environment.md` §3.5）。

## 5. 产物命名与版本落地

- 固件版本号 = `git describe` 生成并写入构建（版本字符串可在运行时经 `sys/version` 查询，供 Agent 与日志对齐）。
- CI 产物命名：`tessera-fw-<board>-<fw-vX.Y.Z>-g<sha>.bin`。
- 产物只从 CI 产出（本地构建仅供开发），保证可溯。

## 修订记录

- v0.1 · 2026-09-19：首版草案。
