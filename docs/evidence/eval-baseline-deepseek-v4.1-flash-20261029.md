# Tessera Agent 能力评估报告（AC-1 基准）

- 套件：`tessera-agent-eval/1 (AC-1, DEC-81)`
- 生成：2026-10-29T04:16:20+00:00
- 模型：`anthropic:deepseek/deepseek-v4.1-flash`
- sim 段：skip（AC-3 判据闭环单元补全场景定义）

## 汇总

| 指标 | 值 |
|---|---|
| 任务数 | 5 |
| PASS | 4 |
| PARTIAL | 0 |
| FAIL | 1 |
| 通过率 | 0.8 |
| 平均轮数（非 FAIL） | 2.0 |
| 总耗时 | 1360.5s |

## 任务明细

| 任务 | 判定 | 轮数 | 耗时s | 未过项 |
|---|---|---|---|---|
| T1 单文件 log-only 基线（心跳计数） | PASS | 1 | 155.6 | — |
| T2 多文件工程（滑动平均 + 独立滤波模块） | PASS | 2 | 399.9 | — |
| T3 caps 真写入（输出通道自检） | PASS | 3 | 337.5 | — |
| T4 threads 档（双线程并行累加） | PASS | 2 | 467.4 | — |
| T5 resources 外置（large 档校准查表） | FAIL | None | 0.0 | converged（UnexpectedModelBehavior: Exceeded maximum output retries (3)） |

## 检查矩阵（✓/✗）

| 任务 | converged | rounds | imports | exports | deterministic | size | caps | threads | tier | needs | source_files | package_on_disk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| T2 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| T3 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| T4 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| T5 | ✗ | — | — | — | — | — | — | — | — | — | — | — |

---

## 基线过程观察（三轮实测 · 2026-10-29）

正式基线 = 第三轮（套件修复后全谱同轮）。三轮过程数据（波动性即数据）：

| 轮 | T1 | T2 | T3 | T4 | T5 | 备注 |
|---|---|---|---|---|---|---|
| 1 | PASS 3轮 436s | 崩溃（ws_write 空参数三连败——套件健壮性缺口，已修） | — | — | — | 评分器无兜底裸崩 |
| 2 | PASS 3轮 574s | PASS 2轮 248s | FAIL 0s（ws_write 三连败） | PARTIAL（threads 未申报=1） | FAIL 0s（IsADirectoryError——**创作链工具面真缺陷，已修**：ws_write 目录路径无防御） | 套件/工具面两修复随批 |
| **3（正式）** | **PASS 1轮 155.6s** | **PASS 2轮 399.9s** | **PASS 3轮 337.5s** | **PASS 2轮 467.4s** | **FAIL（PLANNING 结构化输出重试超限 ×3——模型能力边界）** | 通过率 0.8 |

**关键发现**：
1. **T5 = deepseek-v4.1-flash 当前能力边界**：三轮三种死法（工具参数三连败 ×2 / PLANNING 结构化输出重试超限）——resources 外置 + large 档声明面是 AC-2 创作深度扩展的精确攻击点；agent 侧改进方向 = PLANNING 结构化输出容错（回退策略）与 ws_write 参数校验失败的恢复轮强化。
2. **ws_write 空参数退化**（`{}` 双缺 ×3 连败）在该模型上非确定复现（T2 轮1 / T3 轮2 触发，同 spec 换轮即愈）——创作循环的工具重试上限（3）被模型格式退化耗尽即崩（UnexpectedModelBehavior 未被 loop 捕获）。已随批：评分器兜底（任何死法给分套件继续）+ ws_write 目录路径 fail-closed。
3. **波动性**：T1 三轮 155.6/436.3/574.5s（3.7×）——单轮数据不可作能力结论，基线以「通过率 + 轮数带」为准。
4. T4 轮2 PARTIAL（threads 未申报）→ 轮3 PASS——threads 申报面（manifest.threads=2）是模型遵循度的随机薄弱点，AC-2 谱内复验。

驱动：`python -m tessera_agent agent-eval`（AC-1 · DEC-81）；套件 = agent/tessera_agent/eval/；完整串口 = 仓外 ~/project/logs/eval_baseline_deepseek_console.txt
