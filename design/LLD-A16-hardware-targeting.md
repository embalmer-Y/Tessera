# LLD-A16 · 硬件定向与新板接入域 · v0.2

> **本文件是什么**：clarify 硬件定向流程 + 联网选型调研 + 新板适配路径设计——owner 2026-10-19 指令（DEC-73）+ 三条门③裁决修订（①搜索参考 QwenPaw 实现；②流程重写 = 需求分析先行、问询是否有板、查 Zephyr 收录、未收录请提供原理图、能力不满足则外接或换板；③新板适配 = DEC-68① BV 域延伸）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.2（2026-10-19 按 owner 三裁决重写；v0.1 的「在线板默认绑定」提案废弃）。

## 1. 硬件定向流程（裁决②重写——需求分析先行，不作任何假设）

```
需求文本
 → ① 需求分析（clarify 既有缺口分析——先做，与本硬件无关）
 → ② 问询卡：「您是否有现成的目标板卡？」三路：
    A.【有——目录内】列 agent/boards 画像目录选（在线设备列表作辅助提示
      ——「检测到在线设备 board=X」仅帮助辨认，不作默认绑定）→ 绑定画像
    B.【有——其他板卡】→ Zephyr 收录检查（本地 zephyr/boards/ 检索 +
      联网核实上游 support 状态）：
       ├─ Zephyr 已收录 → **新板接入路径**（BV2 适配域，§4）：DTS/conf/
       │   分区布局/WAMR 映射移植 + BV1 bring-up 判据链 → 验证过 → 入目录
       └─ 未收录 → **请客户提供原理图**（自定义板移植路径——原理图/DTS
           编写 = 人机协作面；Agent 出移植清单与风险点，owner 供图定案）
    C.【没有——帮我选】→ 联网选型调研（§3）→ 候选问询卡（含 Zephyr
       收录状态列——收录 = 接入代价低）
 → ③ 需求 × 板卡能力核对（缺口分析 × 画像 [hardware] 节/caps）：
    现有板卡不满足需求（外设缺口/内存不足）→ 问询：「外接硬件
    （扩展模块，如 WiFi 模块/传感器）」或「更换板卡（回 B/C）」
 → ④ 定向产物：spec 增【目标硬件】段（画像引用 / 选型记录 / BV2 工单）
```

**纪律**：所有分支都是**问询驱动**（问询卡 = D7 面），无任何静默假设；在线发现仅作辨认辅助（v0.1 的默认绑定提案废弃——owner 裁定）。

## 2. 联网搜索面（裁决①——QwenPaw 同款实现模式）

**QwenPaw 实测结论**（源码级，`agents/tools/websearch/`）：`SearchProvider` ABC（`search(query, max_results) -> [{title,url,snippet,content}]`）+ 工厂按 config 选 provider（缺省 tavily、未知值 raise 不静默路由）+ **Tavily keyless 匿名模式**——`POST api.tavily.com/search` 带 `X-Tavily-Access-Mode: keyless` 头免 key 直调；配置了 key 时 Bearer 优先，HTTP 401/429/432 自动回退 keyless。

**采纳（照抄模式，不引 QwenPaw 本体）**：

```python
class SearchProvider(ABC):          # gateway/websearch.py
    name: str
    async def search(query, max_results=5) -> list[dict]  # {title,url,snippet,content}

class TavilyProvider(SearchProvider):   # keyless 缺省 + env key 升级 + 三态回退
def get_search_provider() -> SearchProvider:  # config [web_search] provider;
    # 缺省 tavily（keyless）；未知值 = ConfigError（不静默路由——QwenPaw 同款）
```

- `web_search` 独立 MCP 工具（confirm 类）+ clarify/HW 域内嵌消费；查询/结果全量审计。
- 凭据：`TAVILY_API_KEY` env 可选（keyless 零配置可用）；**弃 ddgs 抓取提案**（QwenPaw 不用，稳定性劣）。
- A5 桥接维持「自备搜索 MCP server」扩展位（不经此面）。

## 3. 联网选型调研路径（分支 C）

调研 agent（PydanticAI）+ `web_search` 工具：输入 = 需求【资源】要点；检索面 = 板卡型号 + Zephyr 收录状态 + 外设规格；输出 = 结构化候选 ≤5（型号/SoC/RAM/PSRAM/外设/价位带/**Zephyr 收录状态**/来源链接）；**机械预筛**：内存基线口径（候选 RAM < 需求档最低 → 剔除并标注）+ Zephyr 收录列标注（收录 = 接入代价低——呼应分支 B）；问询卡呈现 → 用户选 → 选型记录入 spec（**推定态**——采购 + BV1 验证前不做能力承诺，R12 §5 同款）。

## 4. 新板适配域（裁决③——BV2，独立批设计门③）

「Agent 适配新硬件」= DEC-68① BV 域从**验证**延伸到**适配（移植）**。P4 适配批（board-p4-01）已沉淀人工 playbook，BV2 = 该 playbook 的 Agent 化：

1. **Zephyr 收录板**（分支 B-收录）：以 Zephyr 官方板定义（DTS/Kconfig/默认例程）为基——Agent 生成 Tessera 接入件（五分区 overlay/板 conf 内存初值/WAMR 架构映射/thunk 分派/TS_TEST prov 通道），BV1 判据链跑 bring-up（build→flash→boot→deploy 冒烟），PASS → 画像入目录；
2. **未收录板**（分支 B-未收录）：owner 提供原理图/引脚表 → Agent 出移植清单（外设树/引脚冲突/驱动缺口风险点）+ 协作式 DTS 编写——**人工确认闸**（原理图正确性无机械判据，如实登记）；
3. 判据复用：BV1 C1-C6 + board-p4-01 型 bring-up 判据行模板。

BV2 细设计（含 Zephyr 收录检索面/移植件模板化/判据自动化程度）独立批门③——本域（HW）只负责把用户**引到** BV2 门口并建工单。

## 5. 测试策略

- S0 流程矩阵（剧本化）：需求分析先行顺序断言 / A 目录选绑定 / B 收录→BV2 工单 / B 未收录→原理图协作面 / C 选型→预筛→候选卡 / ③能力缺口→外接或换板问询；
- web_search：keyless 调用形状（头断言）/ key 升级与 401/429/432 回退 / 工厂未知值 raise / 审计事实；
- 能力核对：外设缺口标注矩阵（画像 [hardware].peripherals × 需求资源节）。

## 6. 切分与规模

| 单元 | 内容 | 规模 |
|---|---|---|
| HW-D ✅ | 本设计批（v0.2 重写） | ~0.5 |
| HW-1 | 硬件定向流程（①-④ 全分支 + 问询卡接线 + 画像 [hardware] 节 + 能力核对） | ~1 |
| HW-2 | web_search 面（provider ABC + Tavily keyless + 工厂 + MCP 独立面） | ~0.5 |
| HW-3 | 联网选型调研路径（调研 agent + 机械预筛 + Zephyr 收录列） | ~0.5 |
| BV2-D | 新板适配域设计批（§4 独立门③） | ~0.5（另立） |

HW 合计 ~2 单元；BV2 实现另估（依赖 HW-D 定稿）。
