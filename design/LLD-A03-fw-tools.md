# LLD-A03 · 固件域工具集（fw_*）· v0.1 草案

> **上游**：HLD-agent §2/A03；事实基线 docs/dev-environment.md（WSL 工作区/venv/命令）。首个 DomainPack 的工具实现（注册经 A07）。

## 1. 工作区模型

- V1 **单工作区**：直接使用宿主既有 `~/project/tessera` + `~/project/zephyrproject`（HLD §1，不复制）；任务级隔离后置（多工作区 = 另立 Q）。
- 只读探测：fw_workspace_status 用 `git -C <repo> status/rev-parse` + 扫描 `firmware/tests` 清单；dirty 状态如实上报（不自动 stash——不代 owner 决策）。

## 2. 工具规格

### fw_workspace_status（auto）
- 返回：{repo_branch, repo_commit, repo_dirty, west_workspace: {zephyr_version, modules[]}, boards_available[], test_suites[]}。
- boards 来自 `west boards`（缓存 1 次会话内）；zephyr_version 从 `west top`+manifest 读。

### fw_build（confirm，句柄）
- 执行体：`{venv}/bin/west build -b {board} {source_dir} -d {build_dir}`（build_dir = `agent/build/{task_id}`，任务结束保留产物、失败也保留日志）。
- target：app（firmware/app）| tests 场景由 twister 承担；extra_args 白名单前缀校验（-DEXTRA_*/-DCONFIG_*，防任意注入——`--`/shell 元字符拒绝）。
- 终态 result：{exit_code, build_dir, artifacts[], warnings_count}；日志全量入任务 RingBuffer。
- 超时〔Q-19 提案 4：30 min〕；增量构建：同 build_dir 复用（-d 固定于任务，任务间不复用 V1）。

### fw_twister（confirm，句柄）
- 执行体：`{venv}/bin/west twister -p {platform} -T {tests_root} --outdir {agent/build/{task_id}}` + 过滤参数；结果解析 twister JSON（passed/failed/-skipped 计数 + 失败用例摘要进 result）。
- 超时同上；平台名校验（fw_workspace_status.boards 求交集）。

### fw_pytest（confirm，句柄）
- 执行体：`{venv}/bin/python -m pytest {scope} -q --json-report`（json-report 插件入钉版清单〔Q-19 提案 1〕）；解析汇总进 result。

## 3. 子进程纪律

全走 A00 run_proc（禁 shell、超时必填、进程组杀、流式日志）；venv 路径来自 config `[agent]`，启动校验存在性（缺 = sys_get_info 报 not_configured）。

## 4. 测试要点（L7）

- 三工具的参数矩阵（非法板/非法参数前缀/超时/非零退出）；twister JSON 解析（含损坏 JSON 容错）；产物路径断言；与真实工作区集成冒烟（MA1）。

## 5. 未决依赖

- Q-19 提案 1/4；固件仓库结构（firmware/ 现状即基线）；twister 平台元数据缺口（qemu 板，docs/dev-environment 教训）不影响本层（透传 west 生态行为）。
