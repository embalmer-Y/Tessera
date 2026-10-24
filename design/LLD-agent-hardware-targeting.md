# LLD-agent-hardware-targeting · 硬件定向与新板接入域 · v0.3

> **本文件是什么**：clarify 硬件定向流程 + 联网选型调研 + 新板适配路径设计——owner 2026-10-19 指令（DEC-73）+ 三条门③裁决修订（①搜索参考 QwenPaw 实现；②流程重写 = 需求分析先行、问询是否有板、查 Zephyr 收录、未收录请提供原理图、能力不满足则外接或换板；③新板适配 = DEC-68① BV 域延伸）+ **v0.3 = HW-4 五面扩充**（owner 2026-10-21「应该在Agent层面全面进行优化」——W2 验收 LED 缺陷的创作链硬件事实缺口全链根治，plan v1.141）。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.3（2026-10-21 HW-4 五面扩充；v0.2 的 §1-§6 不变，HW-1/2/3 按 §1-§3 实现）。

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

「Agent 适配新硬件」= DEC-68① BV 域从**验证**延伸到**适配（移植）**。P4 适配批（board-p4）已沉淀人工 playbook，BV2 = 该 playbook 的 Agent 化：

1. **Zephyr 收录板**（分支 B-收录）：以 Zephyr 官方板定义（DTS/Kconfig/默认例程）为基——Agent 生成 Tessera 接入件（五分区 overlay/板 conf 内存初值/WAMR 架构映射/thunk 分派/TS_TEST prov 通道），BV1 判据链跑 bring-up（build→flash→boot→deploy 冒烟），PASS → 画像入目录；
2. **未收录板**（分支 B-未收录）：owner 提供原理图/引脚表 → Agent 出移植清单（外设树/引脚冲突/驱动缺口风险点）+ 协作式 DTS 编写——**人工确认闸**（原理图正确性无机械判据，如实登记）；
3. 判据复用：BV1 C1-C6 + board-p4 型 bring-up 判据行模板。

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
| HW-4 | Agent 级硬件事实全面优化（§7 五面——v0.3 扩充） | ~1 |
| BV2-D | 新板适配域设计批（§4 独立门③） | ~0.5（另立） |

HW 合计 ~2.5 单元；BV2 实现另估（依赖 HW-D 定稿）。

## 7. HW-4 · Agent 级硬件事实全面优化（v0.3——owner 2026-10-21 扩令；门③随批呈递）

> **缺口实证**（W2 人工验收 · LED 缺陷）：用户需求「LED 闪烁」→ LLM 生成 caps
> `gpio:write:0` 并在源码注释写「gpio 实例 0 = 板载 LED」——**零事实支撑的假设**；
> atkbench overlay 该通道无物理引脚（板载 LED=IO4 在 PWM 通道）→ 运行期
> `LED WRITE REJECTED` 168 对（fail-safe 回熄灭）；**编译门（语法/导入面）与判据门
> （日志行出现即 pass）双双不拦**——「soft-pass（判据行命中）/hard-invalid（物理动作
> 未发生）」失配缺口。治理 = Agent 层五面，全部机械可判、零 LLM 轮次。

### 7.1 画像引脚级事实节（画像 schema v1 → v1.1 加性）

`[hardware]` 选入节（opt-in，缺省缺 = 全部 HW-4 面按「画像无事实」跳过——旧画像
零重写兼容，不静默改判）：

```toml
[hardware]
zephyr_board = "dnesp32s3b_esp32s3"  # CONFIG_BOARD 自报匹配键（S0 在线辨认辅助）
soc = "esp32s3"
ram_kb = 512
psram_kb = 8192

[[hardware.pin]]
name = "LEDB"            # 板载事实名（需求↔事实的连接词）
domain = "pwm"           # 通道域（gpio|pwm|adc|av——与 caps class 同空间）
instance = 0             # 通道实例
desc = "板载用户 LED（IO4，高有效）"
source = "原理图 LEDB=IO4 + atkbench overlay ledc0 channel0@0 + w2_hb 实测"  # 必填
```

纪律：`pin.source` **必填**（R12「每字段机械可校验来源」延伸——无来源的引脚声明
拒装载）；`domain ∈ {gpio,pwm,adc,av}`（物理域——power/fs/log/kv/msg/sys 逻辑域
不在此列，门不核对）。

### 7.2 创作链硬件事实注入

- clarify 路（HW-1 S0 ④）：定向产物 = spec 增**【目标硬件】段**（spec_gate 认作可选
  节——缺省不阻塞，旧 spec 兼容）；内容 = 绑定画像的事实摘要 / 选型记录（推定态）/
  BV2 工单 / 「未指定」如实注记。
- 开发者模式直填 spec 路：`app_develop` 入口按配置 `[agent] board_profile` 解析画像，
  自动追加同构【目标硬件】段（内容含「可用通道/实例全列 + 无物理绑定通道禁用」）。
- 消费面：CreationLoop 每轮提示 spec 全文入【需求】槽（截 2000 字）+ 单发路径全文
  传递——注入即达 LLM，**不改循环引擎**。

### 7.3 caps×画像机械核对门（装前拒——soft-pass 缺口的第一道机械补位）

- 位置：`deploy_push_app` / `app_deploy` MCP 面，**审批请求之前**（EC3「坏包审批前
  拦截」同型——不浪费审批轮次）。
- 规则：manifest caps 展开实例集合，对每个物理域实例查画像 pins——**无绑定 →
  TA_E_POLICY 装前拒**（detail 携带违规 cap 与画像可用面）。门生效条件 = 配置
  `board_profile` 非空且画像含 [hardware]；缺一 = 跳过（如实 log，不静默改判——
  旧画像/未配置域零扰动）。
- 判定语义：caps 申请「gpio:write:0」而画像 gpio 域无任何 pin = 拒；申请 pwm:0 而
  画像 pwm 域只绑了实例 0 = 过——**以画像事实为唯一物理真相源**。

### 7.4 caps⇔natives 声明-调用一致性门（v0.3 实现期补——LED 缺陷第一层）

**实证修正**（真包解剖 `tessera.demo.heartbeat-0.1.0.tsap`）：缺陷包 manifest
caps 只有 `log:write:0`——app 源码调 `ts_gpio_write` 却**未申报 gpio cap**；
固件 TEST 语义自动授予仅覆盖 log:write:0（appmgr/runtime.c IR-16 延续性），
gpio 不在授予面 → 权限层运行期拒（TS_E_PERM）。通道无物理引脚（§7.1 实证）
为**第二层**独立缺陷——纵然申报，atkbench 该通道 -ENODEV 仍拒。

机械补位 = `FirmwareCreationVerifier.face_check` 增**导入面 ⇔ caps 声明一致性**
（包装前拦截，修复轮结构化证据）：native→cap 前缀映射表（gpio/pwm/adc/av/fs/
kv/msg/power 全核；log 豁免 = TEST 语义，生产语义批收紧时同步撤；net_publish/
time_ms 豁免 = 数值面外）。

### 7.5 判据硬件感知（soft-pass 缺口的第二道机械补位）

`post_deploy_check` 抓窗后增**硬件回执扫描**：console 文本中 `<TOKEN> WRITE REJECTED`
族（固件 fail-safe 回执正典形态——ts_gpio_write 等被拒时 app 侧行）→
`out["hardware"]["rejections"]`（token 聚类 + 计数 + 画像绑定状态注记）。判据判定
升级：**判据行命中但窗内存在硬件写拒 → criteria_pass = False**（repair_hint =
「硬件写被拒——判据行为日志假象，物理动作未发生」），修复轮自动获得证据（S8 既有
criteria_pass=False → repair 链，零改动消费）。

### 7.6 部署后硬件回执诊断回喂

7.4 的扫描结果即诊断面：`rejections` 列表进 `out["hardware"]`，随 post_check /
判据 miss 证据链回喂修复轮（D3/hook.post 同源）；画像绑定状态入注记（「LEDB 类
token 在画像无 GPIO 绑定——疑似 PWM 通道（[hardware.pin] LEDDB…）」）——修复轮
LLM 拿到的是**事实**而非猜测。

### 7.7 测试策略（HW-4）

- 画像 [hardware] 装载矩阵（全字段/缺 source 拒/未知域拒/缺省节跳过）；
- 门矩阵：gpio 申请×无绑定=拒 / pwm:0×绑定 0=过 / 逻辑域豁免 / 未配置 board_profile
  跳过 / 审批前拦截次序；
- 回执扫描：`LED WRITE REJECTED` 168 对样本形态聚类 / 判据命中+写拒 → False /
  纯判据 miss 不受扰 / 无写拒不降级；
- 注入：app_develop 直填 spec 自动追加【目标硬件】/ clarify 路段落合成 / 旧 spec 兼容。

## 8. v0.3 不改变的红线

- spec 四节门（NV-2）不变——【目标硬件】为可选节，缺省不阻塞；
- 部署链验签/租约/分块/激活全不变——门在审批前，纯 Agent 侧；
- bus/事件/审批语义不变；画像旧节零改动（v1.1 加性——fail-closed 白名单扩一项）。

