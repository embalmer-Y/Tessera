# LLD-A16 · 硬件定向与选型调研域 · v0.1

> **本文件是什么**：clarify 硬件定向槽 + 联网选型调研路径低层设计——owner 2026-10-19 指令（W2 验收实证缺口：「用户没说硬件 Agent 不知道；用户要新板卡就会出问题」→「用户没说明时提醒指定硬件；用户不清楚时 Agent 联网选型调研」；DEC-73）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.1（2026-10-19 设计批，门③呈递）。

## 1. 问题定性与调研结论

**现状（调研①）**：Agent 的硬件意识是隐式的——LLM 只拿到平台级 native 白名单（ts_* 函数面），板级外设事实（LCD/es8311/SD…）不在任何创作提示里；用户原话是唯一线索（W2 验收实锤：用户说 LVGL 它就信 LVGL）。而**板卡身份链在协议层其实已存在**：

| 事实源 | 内容 | 缺口 |
|---|---|---|
| 固件 `get-info` 自报 | `board = CONFIG_BOARD`（如 `dnesp32s3b/esp32s3/procpu`）+ `caps.peripherals`（uid:kind 全量）+ tiers/slot_pool | Agent 侧无人消费（discover 透传后丢弃）；CONFIG_BOARD 串与画像 id 无映射 |
| 板卡画像 `agent/boards/*.toml` | 七节人工沉淀（BV1 域）；R12 `[hardware]` 节 schema v0 已设计 | 未进 clarify/创作面 |
| 内存基线 `memory-baseline.md` | 三档实测 DRAM/PSRAM/FLASH 最低需求 | R12 判定链硬门，未接任何运行时路径 |

**联网搜索调研（调研②）**：三条可行路径——
1. **ddgs**（原 duckduckgo-search，Python 库）：零凭据即用；抓取型（DDG 无官方 API）→ 稳定性/限流风险，断供风险自担；
2. **Tavily / Brave Search API**：agent 优化、稳定；需注册 key（Tavily 免费 1000 次/月）——凭据纪律同 env.sh；
3. **A5 MCP 桥接**：任意外部搜索 MCP server 可后挂（`x_<server>_call`）——用户自备面。

**R12 接入面（调研③）**：R12 判定链五步（需求抽取→目录匹配→内存硬门→排序→BV1 闭环）已定性「①-③ 确定性流水线、LLM 仅语义理解处」——本域 = 该链的**第一次落地消费**。

## 2. 设计：clarify 硬件定向槽（前置 Step 0）

在澄清五步之前插入**目标硬件定向**，四分支：

```
需求文本
 → S0a 需求抽取：文本是否明确提及板卡型号/硬件？（LLM 结构化——R12 ①同型）
    ├─ 提及且命中本地目录 → 绑定画像，S0 完成（向用户回显一句确认）
    ├─ 提及但目录外（如"P4C6"）→ 目录外态：如实告知该板未接入
    │   （需 BV1 bring-up 才能部署/验证）+ 问询：仍按通用面合成 / 转选型调研
    ├─ 未提及 → S0b 在线发现：deploy_discover（board 自报）
    │   ├─ 恰一在线板 → 问询卡确认：「检测到在线设备 <board 描述>，
    │   │   是否为该设备开发？」（默认 = 是；"其他设备" → 转选型调研）
    │   └─ 多台 → 问询卡列选（board 描述 + node_id）
    └─ 无在线板/用户选"不清楚" → S0c 联网选型调研（§3）
 → S0 产物：spec 增【目标硬件】段（画像引用或选型记录）+ 部署目标预绑定
```

- **S0c 联网选型调研**：PydanticAI agent + `web_search` 工具（§3）——输入 = 需求【资源】要点；输出 = 结构化候选清单（型号/SoC/RAM/PSRAM/外设/价位带/来源链接，≤5 项）；**机械预筛**：内存基线口径过滤（候选 RAM < 需求档最低 → 剔除，标注理由）；呈现问询卡供用户选择；用户选择 = 选型记录入 spec（含「推定态」标注——未经 BV1 实测）。
- **诚实边界**：联网候选在采购+BV1 验证前是**推定态**（R12 §5 同款）——机械门只在本地目录内生效；选型记录不等于能力承诺。
- **目录外新板**：S0 绑定失败不是错误——spec 照常合成（平台级 native 面），但部署阶段会因无画像/无在线节点如实失败；问询卡明确告知「新板需先走 BV1 接入（画像 + bring-up）」。

## 3. `web_search` 工具面

- **Provider 链**（config `[web_search]`）：`provider = "auto"`（缺省）= env 有 TAVILY_API_KEY → Tavily；否则 ddgs 兜底。显式 `"tavily"|"ddgs"|"none"` 可钉死；`"none"` = S0c 直接结构化报错（离线环境如实）。
- **独立 MCP 工具**：`web_search(query, max_results=5)`（confirm 类）——开发者模式/未来消费方同用；查询与结果全量入审计。
- **安全边界**：只读外发（查询词不含凭据/env 值——工具内过滤）；搜索结果**不可信内容不直接执行**（只作选型候选材料 + 用户确认闸）；限流失败 → 结构化重试提示。
- **凭据**：TAVILY_API_KEY 走 env（同 ANTHROPIC_API_KEY 纪律）；ddgs 零凭据为缺省可用态。

## 4. 板卡画像增补（微改）

- 画像 `[hardware]` 节（R12 schema v0 落地首用）：`board_target = "dnesp32s3b"`（= CONFIG_BOARD 首段，映射键）+ `ram_kb/psram_kb/flash_mb/peripherals/price_band`（机械可校验来源纪律不变）；
- discover 侧：回执 `board` 字段透传已有——Agent 侧补 `board_target → profile` 映射查询（无命中 = 目录外态，不报错）。

## 5. 测试策略

- S0 分支矩阵（剧本化）：提及+命中 / 提及+目录外 / 未提及+恰一在线 / 未提及+多台 / 未知+搜索成功 / 未知+搜索失败（结构化，链可继续以"平台级通用面"合成）；
- 机械预筛矩阵：RAM 不足剔除/外设缺口标注/推定态标注；
- provider 链：key 在位→Tavily / 缺→ddgs / none→结构化；web_search 工具注册与审计事实；
- 映射：CONFIG_BOARD → 画像命中/目录外。

## 6. 切分与规模

| 单元 | 内容 | 规模 |
|---|---|---|
| HW-D ✅ 本批 | 本设计批 | ~0.5 |
| HW-1 | 画像 `[hardware]` 节 + discover 消费 + S0a/S0b 分支 + 问询卡接线 | ~0.5 |
| HW-2 | `web_search` 工具面（provider 链 + config + 独立 MCP 面） | ~0.5 |
| HW-3 | S0c 联网选型调研路径（调研 agent + 机械预筛 + 选型记录）+ 测试 | ~0.5 |

合计 ~2 单元。非目标（登记）：自动采购/价格实时抓取/目录自动爬取入库（人工沉淀 + BV1 校准纪律维持）。

## 7. 门③决策点（呈递 owner）

1. **搜索 provider 缺省**：建议 = ddgs 零凭据兜底（开箱可用）+ Tavily key 可选（owner 注册后 env 注入升级稳定性）——是否认可？
2. **S0b 在线设备默认绑定**：恰一在线板时「默认 = 是」的问询语义（一键确认）是否符合预期？
3. 目录外新板的「仍按通用面合成」路径是否保留（vs 硬拒）？
