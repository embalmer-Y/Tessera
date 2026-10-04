# MD0-1 · Agent 真实 LLM 冒烟——单元报告

> **日期**：2026-10-04 · **状态**：SMOKE1 + SMOKE2 双 PASS（app_develop 真实 LLM 全链首次贯通）
> **触发**：owner 提供 AI API（minimax Anthropic 兼容端点，模型 MiniMax-M3，上下文 1M——owner 指令）。
> **密钥纪律**：密钥仅存仓外 `~/project/logs/.minimax_key`（600），经 env（ANTHROPIC_API_KEY/ANTHROPIC_BASE_URL）注入；`agent/config.toml`（gitignored）只含模型串与窗口数，无密钥；提交前 git grep 验证零泄漏。

## 1. 结果

| 冒烟 | 内容 | 结果 |
|---|---|---|
| SMOKE1 | pydantic-ai Agent → minimax(anthropic 兼容) → pydantic 结构化输出 | **PASS**（一次命中零重试；usage 计量正常） |
| SMOKE2 | **app_develop 全链**：spec → 真实 LLM（skills 渐进披露 + read_skill 工具）→ DevelopOutcome → manifest 硬校验（反馈回路）→ tsap_package 签名 → tsap_verify 复验 | **PASS ×2 轮复跑**（56.3s / 29.6s，第 3 轮通过 / 首轮或早轮通过） |

**SMOKE2 观测**（spec = LED 呼吸灯：tick 100ms 斜坡 0→1000‰ +10‰/tick、caps 最小权限、限幅 700‰）：
- LLM 产出 manifest 完全合法：`app_id=com.example.led.breath`、`caps=["pwm:set:0","gpio:write:0"]`（最小权限+文法精确）、`exports=[health_ping, app_tick]`、stack 4KB/heap 1KB；
- **DevelopOutcome 质量超预期**：safety_notes 内化合同 10（不学习/越权留痕）；test_plan 8 条自带项目军规风格（确定性重放逐拍断言/限幅 mock/越权留痕/断链 fail-safe/边界回绕/双实现验签）；steps 7 步含 Q-登记→设计→同批测试→twister→打包→review 门——**skills 注入生效**；
- 反馈回路实证必要：第一轮复跑中 LLM 两次 manifest 瑕疵（caps 自造格式 → app_id 下划线）均被硬校验拦下（fail-closed ✓）并经回路修正，第 3 轮通过。

## 2. 冒烟拦下并修复的三项产品缺陷（impl 期同批授权修复，均有实证）

1. **app_develop 输出上限缺失**（app_chain.py）：思考型模型推理段先耗尽 anthropic SDK provider 缺省上限 → `UnexpectedModelBehavior`（链路对真实端点开箱不可用）——补 `model_settings={'max_tokens': 16384}`（OUTPUT_MAX_TOKENS，出处注释）。
2. **config 加载路径错误**（config.py）：文档/gitignore/config.example 均约定 `agent/config.toml`，代码却找包内 `tessera_agent/config.toml`——**配置从未能从文档位置加载**（真实使用首次暴露）。修正 `parents[2]`。
3. **manifest 硬校验无反馈回路**（app_chain.py）：校验在 LLM 运行之后，pydantic 重试管不到——一次一个错、失败即整链报废。补回路：校验错误文本 + message_history 续跑，预算 3（同 OUTPUT_RETRIES）；另将 ts_perm_v1 caps 文法内联系统提示（LLM 仅口头引用文法名时会自造格式）。

## 3. 环境事实（dev-env v2.11 登记）

- 端点：`ANTHROPIC_BASE_URL=https://api.minimax.cn/anthropic`，模型 `MiniMax-M3`（anthropic 兼容面 /v1/messages；x-api-key 与 Bearer 均可——anthropic SDK 默认 x-api-key ✓）；上下文 1M（config.toml `context_window=1048576`，owner 指令）。
- pydantic-ai 2.47.0：模型串 `anthropic:MiniMax-M3` + `AnthropicProvider` 尊重 `ANTHROPIC_BASE_URL`/`ANTHROPIC_API_KEY` env（零代码注入面）。

## 4. 复跑

```bash
# WSL（密钥文件仓外 ~/project/logs/.minimax_key）：
bash ~/project/logs/run_smoke1.sh   # SMOKE1：结构化输出管道
bash ~/project/logs/run_smoke2.sh   # SMOKE2：app_develop 全链（输出 ~/project/logs/llm-smoke-out/）
```

## 5. 对 MD 批的结论

- **G2（真实 LLM 未测）关闭**：链路、skills、结构化输出、反馈回路全实证；
- G1（APP 代码生成）依旧为 MD0 最大前置——本轮 LLM 展现的规格理解力（test_plan/steps 质量）是 G1 的正面信号；
- 后续 demo 全链（app_develop→sim→deploy 真机）的模型侧已就绪。
