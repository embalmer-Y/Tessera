# docs/std/ · Tessera 开发规范套件

> **定位**：`AGENTS.md` 是流程宪法（阶段门 / review 门 / 军规十条 / 安全合同），本目录是其下可执行细则；两者冲突时以 `AGENTS.md` 与 owner 最新裁决（`decisions.md` DEC）为准。
> **状态**：**v0.1 草案，待 owner review；批准后打 tag `std-v1` 生效**。生效前按 `AGENTS.md` 既有规则执行，本套件仅作预览。
> **修改流程**：生效后的任何修改 = 规范变更，走 review 门（先登记 Q 呈递，不得直接改写生效版）。

## 文件清单

| 文件 | 内容 | 主要服务对象 |
|---|---|---|
| [testing.md](testing.md) | 测试方法规范：测试层级、机械检查、覆盖率门槛、失败处理 | impl 全阶段（twister/pytest） |
| [versioning.md](versioning.md) | 版本与 git 规范：分支/提交/tag/semver/外部依赖钉住 | 全项目 |
| [progress.md](progress.md) | 项目进度记录规则：事实源、会话协议、里程碑登记 | 全项目（AI 会话协作） |
| [coding.md](coding.md) | 编码规范：C/Zephyr、Python、确定性禁令、常量纪律 | impl 阶段 |

## 三条贯穿性原则（各文件细化）

1. **交付即验证**（军规 10）：没有同批测试与 CI 绿，就没有"完成"。
2. **无 Q 不落盘**（军规 2）：规范内的所有默认值（覆盖率门槛、心跳参数、命名模板等）均标注"默认值，出处见 Q-xx 或本套件生效裁决"；改默认值先过默认值三问。
3. **结论落盘**（军规 8）：进度、裁决、失败与回退一律落文件与 git，聊天记录不是项目状态。

## 修订记录

- v0.1 · 2026-09-19：首版草案（testing / versioning / progress / coding），待 owner review。
