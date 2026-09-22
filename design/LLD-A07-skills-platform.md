# LLD-A07 · Skills 与平台层（多域预留）· v0.1 草案

> **上游**：HLD-agent §2/A07、§6（多域/北极星）；决策 DEC-36③（Agent Skills 分发；DEC-37 修订为自建 loader）、DEC-36④（A2A 预留）、DEC-35（ACP 预留）、DEC-33（北极星）。

## 1. Skill loader（自建，DEC-37 修订落点）

- 读取 `agent/skills/*/SKILL.md`（开放标准目录约定：frontmatter name/description + 正文指导 + 可选 scripts/references）；启动期扫描注册。
- **渐进披露**（对齐标准语义）：会话系统提示只注入 name+description 一览；模型经专用工具 `skill_read(name)` 按需取全文（该工具为 A02 编辑工具族一员，auto 类）。
- 注入纪律：skills 内容进入系统提示 = 影响行为 → 提供者快照记录已激活 skill 集（审计确定性）。

## 2. V1 最小 skill 集（4 个提案，随 C-5 确认）

| skill | 内容（来源） | 用途 |
|---|---|---|
| tessera-workflow | 军规十条摘要 + 阶段白名单 + 提交纪律（AGENTS.md 提炼） | agent 行为约束（无豁免的知识面） |
| tessera-build | west/twister/pytest 用法 + 板集 + 钉版纪律（dev-environment.md 提炼） | fw_* 工具正确使用 |
| tessera-tsap | TSAP 格式/manifest 字段/权限文法 ts_perm_v1（LLD-ts-appmgr 提炼） | 打包与 APP 开发 |
| tessera-safety | 安全合同十条 + 三安全态 + 限值语义（AGENTS.md §6 提炼） | APP 代码生成的安全内化 |

- 维护纪律：skill 内容从权威文档**派生提炼**（不双写真相）——每次权威文档变更后同步检查项入 PR 检查单〔Q-19 提案 13：skill 同步检查脚本〕。
- 对外分发：同一目录即开放标准 skill 包（其他 agent 工具可直接消费，DEC-36③ 分发面）。

## 3. DomainPack 接口（多域预留核心，DEC-33）

```text
DomainPack（协议级接口，固件域 = 首个实现）
  ├ tools: [ToolDef]            # 原子工具集（A01 注册）
  ├ skills: [SkillRef]          # 域知识包（§1 loader）
  ├ policy: PolicyTable         # 审批类别默认表（只可收紧）
  ├ validators: [ArtifactValidator]  # 产物校验器（如 TsapManifestV1）
  └ deployer: Deployer | None   # 部署器（固件域 = A06）
```

- 平台层（A00/A01/A02/A07 loader 部分）**不 import 任何域模块**——经注册表装配（`main.py` 显式注册 FirmwareDomainPack）；新域（PCB/结构件）= 新包 + 注册，平台零改动。
- 未来跨域：默认上层编排 + 各域 MCP 面（DEC-36④）；同进程多 DomainPack 装配为可选形态（V1 单域）。

## 4. A2A 接入缝（DEC-36④ 显式记录点之三）

- 预留 `PeerTransport` 接口（旁挂 SessionOrchestrator）：`serve_agent_card()`（生成 Agent Card：能力=工具面清单）+ `delegate_task(peer, payload)`（对等任务委托）。
- V1 仅接口定义 + 数据模型注释（含启用条件：跨主体/长周期对等，如 Galatea 规模）；实现属未来 Q。

## 5. ACP 接入缝（DEC-35）

- 见 A02 §1 Frontend 抽象（本模块登记归属：ACP 适配器属平台层后补模块，实现时新增 `acp_frontend.py` + 子进程入口，不改编排/域层）。

## 6. docs 知识服务（可选后置，HLD §9）

- 预留：文档型知识经独立 docs MCP server 暴露（Espressif 先例，解决模型训练截止）；V1 以 skills 覆盖，触发条件 = 知识量超出 skill 形态（另立 Q）。

## 7. 测试要点（L7）

- loader：目录约定解析/渐进披露两级内容正确性；skill 激活集入审计快照断言。
- DomainPack：注册表装配（平台不 import 域的架构测试——import 图断言）；策略表只收紧断言。
- 接口缝：PeerTransport/Frontend 打桩替换可运行（编译级+冒烟）。

## 8. 未决依赖

- Q-19 提案 13；固件域各 LLD（工具实现方）；skill 内容提炼源（AGENTS.md/LLD 固件侧）随其版本演进。
