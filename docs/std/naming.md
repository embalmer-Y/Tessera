# docs/std/naming.md · 文件与目录命名规范

> **状态**：v1.0 · 2026-10-24 新立（DEC-78 全仓整理——owner 指令「规范各种文件的命名，
> 不允许出现类似 l1，l2，l3，review-01，review-02 这类名称」）。
> **适用范围**：仓库内一切新增文件与目录。存量旧名已按本规范清理（新旧映射 =
> `docs/names.md` §6 重命名登记册；例外：firmware/tests 内嵌包机械生成头 d4_pkg.h / d6_pkg.h /
> d9_pkg.h——改名牵固件 C include 链，随固件批缓办，已登记 §6）；evidence 留痕与历史档案不回溯。

## 1. 总则

1. **名称必须自描述**：仅凭文件名即可判断内容主题；**禁用纯序号/会话代号**命名
   （l1/l2/l3、D1/D2、review-01/-02、ak3_*/cg7_* 类）。
2. **注册标识符不在此限**：DEC-xx/Q-xx/R-xx/IR-xx 等登记册代号（`docs/names.md` §1-§2）
   与 HLD 文内结构节号（如 HLD-agent §2/A00）属文档内部引用体系，允许在正文与表格中使用；
   但**不得作为文件名/目录名的主体**（可作辅助后缀，如 `nvd_acceptance.py` 保留注册缩写 NVD）。
3. **中英文**：文件/目录名一律 ASCII（kebab-case 目录 / snake_case Python / 大写前缀分类）；
   中文用于文档标题与正文。

## 2. 分类规范

| 类别 | 形态 | 示例 |
|---|---|---|
| 设计文档 | `HLD-<域>-<主题>.md` / `LLD-<域>-<主题>.md`（域 = ts 固件模块 / agent Agent 域） | `LLD-ts-net.md`、`LLD-agent-board-adaptation.md` |
| 交付报告（一次性） | `docs/<主题>.md`——主题自描述；序号后缀禁用（多次同题报告以主题词或日期区分） | `board-p4.md`、`netbench.md` |
| 调研文档 | `docs/research/R<注册号>-<主题>.md`（R 号 = 登记册任务代号，主题必须自描述） | `R12-board-selection.md` |
| demo 夹具 | `agent/demos/demo-<主题>/` | `demo-led-blink/`、`demo-p4-probe/` |
| 固件测试/联调 | `firmware/tests/<用途>/`（twister 套件框架名除外——framework.\* 为 CI 惯例） | `netbench/`、`netlab/`、`safety_check/` |
| 板级工具脚本 | `tools/board/<动词或用途>.py`；e2e_ 前缀表端到端驱动 | `e2e_trust_chain.py`、`console_holder.py` |
| 证据留痕 | `docs/evidence/`——存量原名不回溯；**新增建议 `<主题>-<yyyymmdd>.txt`** | `fix2-p4-probe-20261022.txt`（建议形态） |
| 历史归档 | `docs/history/<来源>-archive[-<yyyymm>].md` | `plan-archive-2026-10.md` |

## 3. 禁止形态（反面清单）

- 纯序号：`l1` `l2` `l3` `D1` `D2` …（含以序号开头的目录/脚本名）
- 序号后缀轮转：`review-01` `review-02` `*-01.md`（无法判断第二份何时出现、主题何在）
- 会话/单元代号前缀：`ak3_*.py` `cg7_*.py`（代号仅在登记册与历史正文中有意义）
- 无主题词的缩写堆叠：`md12c-pdm-eval.md`（应为 `pdm-audio-eval.md`）
