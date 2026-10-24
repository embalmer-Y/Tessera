# LLD-agent-creation-workspace · 创作工作区与循环引擎（creation-workspace）· v0.1（AG1）

> **上游**：HLD-agent v0.2 §2.2/§5.2；决策 DEC-56/57（Q-38①③④⑤ + Q-39①⑤）、DEC-33（域无关结构原则）、DEC-38 #6（上下文压缩）。
> **模块定位**：平台层新组件——**域无关**创作循环引擎 + 工作区模型 + 会话快照；固件语义零侵入（验证器经 `CreationVerifier` 协议注入）。

## 1. 文件布局

```text
agent/tessera_agent/creation/
  __init__.py
  workspace.py    # 工作区模型 + roots 钳制 + project.json
  tools.py        # ws_read/ws_write/ws_edit/ws_list（PydanticAI 工具面）
  loop.py         # 循环引擎（状态机/预算/计划/证据组装/LLM 上下文构造）
  snapshot.py     # 会话快照（原子写/重建）
  verifier.py     # CreationVerifier Protocol + 结果数据类
agent/tessera_agent/domain/firmware.py（增）  # FirmwareCreationVerifier 装配
```

## 2. 工作区模型（workspace.py）

### 2.1 文件系统布局

```text
agent/workspace/<task_id>/          # task_id = 任务注册表既有 id（t-<hex>）——复用 A00
  project/                          # 多文件工程源（LLM 编辑面）
  artifacts/                        # verifier 产物（wasm/tsap）——LLM 只读
  .session/snapshot.json            # 会话快照（§6）
  project.json                      # 工程清单 = 多文件工程单一事实源
```

### 2.2 project.json schema（v1）

```json
{
  "schema": 1, "app_id": "demo.x", "app_ver": "1.0.0", "tier": "small|large",
  "files": ["main.c", "control.c", "include/state.h"],
  "exports": ["app_init", "app_tick", "app_evt", "health_ping"],
  "compile_flags_extra": [],            // 线程档等（verifier 消费）
  "threads": 1, "manifest": {…草稿…},   // tsap manifest 镜像（校验器同 schema）
  "resources": [],                      // 外置资源声明（CG5 消费；本批只留字段）
  "needs": null                          // large 档资源声明（CG4 消费；本批只留字段）
}
```

**纪律**：文件表与 exports 表 = 编译输入与面检查的**唯一来源**；`-Wl,--export=` 逐符号传递，缺项由**面检查一票拒**（`--allow-undefined` 为 natives 未定义符号所必需——链接期不可区分缺导出与未实现 native，fail-closed 由面门承载，与单文件链同型；AG3 实证定案）。

### 2.3 roots 钳制（HLD §5.2 落地）

- rw_root = `<workspace>/<task_id>/`；ro_roots = DomainPack 声明（固件域：`firmware/module/tessera/include/`、`agent/skills/`、`docs/`，路径解析为绝对后登记）。
- 一切路径经 `_resolve_within(path, roots)`（IR-13 既有纪律平移）：符号链接解析后必须落在 roots 内，否则 `TA_E_WORKSPACE_PATH`。
- **artrfacts/ 对编辑工具只读**（产物不可手改——交付完整性）；`.session/` 对编辑工具不可见（防快照自篡改）。
- 容量上限：单文件 ≤ 512KB、工程总量 ≤ 4MB、文件数 ≤ 64（config `creation.workspace_limits`——防资源耗尽，超限 `TA_E_WORKSPACE_LIMIT`）。

## 3. scoped 编辑工具（tools.py——循环内部 PydanticAI 工具，**非 MCP 面**）

| 工具 | 语义 | 错误 |
|---|---|---|
| `ws_read(path, offset=0, limit=400)` | 行号制读（对齐 ZCode Read 惯例）；path ∈ rw_root 或 ro_roots | 越界 `TA_E_WORKSPACE_PATH`；超限分页（返回含 total_lines/has_more） |
| `ws_write(path, content)` | 新建/整文件覆写；仅 rw_root 的 `project/`；覆写前须已 ws_read（**防盲写**——文件状态跟踪表） | 未读覆写 `TA_E_WORKSPACE_STALE`；越界/超限同上 |
| `ws_edit(path, old_string, new_string, replace_all=false)` | **唯一 old_string 锚定替换**（R7 §5 证据形态）；失配/多义报错带行号上下文 | 失配 `TA_E_ANCHOR_NOT_FOUND`；多义且未 replace_all `TA_E_ANCHOR_AMBIGUOUS` |
| `ws_list(path=".")` | 工程树（文件+行数+mtime）；`ws_list("@plan")` 返回计划项（§5） | — |

- 工具描述内嵌编辑纪律（先读后改/唯一锚/整文件再生适用于 ≤200 行小文件——提示词层降低首错率，机械层兜底不变）。

## 4. CreationVerifier 协议（verifier.py——域插件接口）

```python
class CreationVerifier(Protocol):
    def compile(self, ws: Workspace) -> CompileResult:
        """聚合编译：clang --target=wasm32 <files> -Wl,--export=<每个导出> -o artifacts/app.wasm
        （钉版 flags + project.json compile_flags_extra；超时 60s 进程组击杀——R4 纪律平移）"""
    def simulate(self, ws: Workspace, scenario: dict) -> SimResult:
        """sim 重放（判据 diff：miss 行 + 写轨迹摘要）"""
    def face_check(self, ws: Workspace) -> FaceReport:
        """导入⊆natives 白名单 / exports 齐 / 尺寸门（分档双门 Q-39⑤）"""
    def package(self, ws: Workspace, key_path: str) -> TsapArtifact:
        """双编译字节一致 + tsap_package 签名——工作区到可部署物唯一出口"""
```

结果类均含 `ok: bool + detail: str（证据原文，-4KB）`。**固件域实现**：`FirmwareCreationVerifier`（wasm_build 多文件化扩展 + A04 sim 驱动 + A05 打包）装配于 domain/firmware.py——平台层零 import 域模块（导入图测试扩一条断言）。

## 5. 循环引擎（loop.py）

### 5.1 状态机

```text
DRAFT → PLANNING → IMPLEMENTING ⇄ VERIFYING → CONVERGED → PACKAGED
                ↘ FAILED（预算耗尽/不可收敛——证据归档不删工作区）
```

- 迁移由**证据驱动**：IMPLEMENTING→VERIFYING = LLM 声明完成（结构化轮产物）；VERIFYING→IMPLEMENTING = 任一验证不过（证据回喂）；VERIFYING→CONVERGED = compile+face+sim 全绿；CONVERGED→PACKAGED = package 成功。
- 轮次预算 `creation.round_budget`（默认 12）；每轮 = 一次 PydanticAI agent.run（多工具调用循环内含）。预算耗尽 → FAILED + 快照保留（可人工续）。

### 5.2 计划跟踪（PlanItem）

`PlanItem {id, desc, status: pending|in_progress|done}`——PLANNING 轮产物（结构化校验）；每轮注入 LLM 上下文（当前项+未竟项）；`ws_list("@plan")` 与前端进度（A09）同源。

### 5.3 证据自动回喂（Q-38① 核心）

每轮用户侧消息 = `spec 摘要 + 计划状态 + 上轮证据块`：证据块 = CompileResult/SimResult/FaceReport 的 detail 原文（编译 stderr 不截断美化——R6 纪律）+ 判据 miss 行。**自动组装**，不依赖模型主动查询。

### 5.4 LLM 上下文管理

- 系统提示 = `_develop_system_prompt()` 既有（文法内联+skills）+ 循环纪律段（状态机语义/编辑纪律/收敛标准「全绿才许声明完成」）。
- message_history 跨轮维持；达预算 70%（DEC-38 #6）触发 maybe_compress——**存活项**：系统提示/计划/最近 2 轮证据/工程清单；压缩事件入审计。
- `parallel_tool_calls=False`（确定性同构既有纪律）。

## 6. 会话快照（snapshot.py——Q-38④）

### 6.1 schema（`.session/snapshot.json`）

```json
{"schema": 1, "task_id": "…", "state": "IMPLEMENTING", "round": 5, "budget_used": 5,
 "plan": […], "spec_digest": "…", "criteria": […],
 "files": {"main.c": {"sha256": "…", "lines": 210}},
 "round_summaries": [{"r": 1, "event": "compile_fail", "digest": "…"}, …],
 "created_at": "…", "updated_at": "…"}
```

文件内容本体在 project/（快照只存哈希表——单一事实源不双写）；轮次摘要 = 上下文重组材料。

### 6.2 原子写与 resume

- 写：tmp 文件 + `os.replace`（原子）；每次状态迁移/轮末触发。
- resume：校验文件哈希一致（不一致 = `TA_E_SNAPSHOT_STALE`，如实报）→ 重建状态机/计划/预算 → LLM 上下文从 round_summaries 重组（非全量对话——审计流保全量）→ 续跑。
- 生命周期：任务注册表 task 释放（completed/failed/cancelled）后工作区保留（config `creation.workspace_retain_days`，默认 30 天清理——异步任务，不影响主流程）。

## 7. 错误模型扩展（A00 TA_E_* 族）

`TA_E_WORKSPACE_PATH` / `TA_E_WORKSPACE_STALE` / `TA_E_WORKSPACE_LIMIT` / `TA_E_ANCHOR_NOT_FOUND` / `TA_E_ANCHOR_AMBIGUOUS` / `TA_E_LOOP_BUDGET` / `TA_E_SNAPSHOT_STALE`——结构化 detail 含路径/行号/预算数（A01 错误呈现链既有）。

## 8. 审计与观测

- 每轮一条审计事件（工具流）：`creation.round {task_id, round, state, evidence_ok, budget_used}`；PLANNING/PACKAGED 各一条里程碑事件。
- task_log 增量 = 轮事件流（A09 终端渲染与 MCP task_log 轮询同源）。

## 9. 测试要点（L7；零 LLM/零网络）

- roots 矩阵：越界路径/符号链接逃逸/artifacts 改写/.session 访问 → 全拒。
- 编辑工具：锚定失配/多义/未读覆写/分页边界/超限。
- 状态机：全转移矩阵（含 FAILED 证据归档）；预算耗尽路径。
- 证据回喂：VERIFYING 失败后下轮用户消息内容断言（detail 原文在）。
- 快照：往返一致性；哈希不一致 STALE；杀进程（SIGKILL 模拟）后续跑。
- FunctionModel 剧本：多文件工程 3 轮收敛（compile fail→edit→pass→package）；域无关性——DummyVerifier 打桩跑通全状态机。
- 导入图：平台层不 import 域模块断言扩展到 creation/。

## 10. 未决依赖

- AG3 消费本规格实现；Q-39 large 档数值（AG7）只影响 verifier.face_check 的门值来源（config），结构不变。
- `resources`/`needs` 字段本批只登记不消费（CG4/CG5）；spec_check 门与判据派生维持 tools_diag 既有单一事实源。

## 修订记录

- v0.1 · 2026-10-13：初版（AG1；HLD-agent v0.2 §2.2/§5.2 展开；C-7 呈递）。
