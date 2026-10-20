# LLD-A15 · 外部 MCP 桥接（A5/D6 客户端）+ post 观察钩子（A4/D4b）· v0.1

> **本文件是什么**：A5（Agent 作为 MCP client 接入外部 server——DEC-12 v1.1 双角色消费侧，九十六候选⑦销项）与 A4（D4b post 观察面——V0.12.0 余项）低层设计。
> **权威顺序**：owner 裁决 > FOUNDING_PROMPT > 本文件。
> **状态**：v0.1（2026-10-19 随批落稿——设计契约 = plan §11h I 表 A5/A4 行〔V0.13.0 立项时点向，无新门③〕）。

## 1. 定性

- **A5 = 消费侧桥接**：本 Agent 已是 MCP server（FastMCP）；A5 补齐 client 半边——外部 MCP server 的工具经桥接面进入本 Agent 面。**不信任面原则**：外部工具默认 strict（逐调用审批不豁免），命名空间前缀防撞（双向），审批 token 闸/D4 hooks/审计全照常作用（渠道=客户端，安全在服务端）。
- **A4 = post 观察面**：pre 拦截（deny/observe）已交付（DEC-67①③）；post 补**调用后结果摘要外发**——observe-only（post deny 语义为空），经 W2 事件总线 `hook.post` 事件外发，诊断自动注入缝（消费侧闭环随诊断批）。

## 2. A5 桥接面

### 2.1 传输与配置（`[mcp_clients]`）

```toml
[mcp_clients.<server_name>]
url = "http://host:port/mcp"        # 形态一：HTTP
# 或
command = ["prog", "arg"]           # 形态二：stdio 子进程
[mcp_clients.<server_name>.env]
KEY = "v"
```

- server 名净化 `[^A-Za-z0-9_] → _`（空名拒）；非法条目 = 启动期结构化错。
- `_inline` 键 = 测试注入面（内存 FastMCP 实例直连）——config 加载器不产生（测试锚定）。

### 2.2 命名空间（防撞——双向）

每 server 两个桥接工具：`x_<server>_list`（工具清单透传：name/description/schema，只读无审批）+ `x_<server>_call(tool, args)`（点名调用）。外部工具原始名仅作参数——永不与本域工具/彼此相撞。**逐工具投影**（把外部工具注册为本面一等工具）= v2 登记不实现。

### 2.3 会话形态与调用语义

- v1 = **每调用连接**（connect→call→close）：外部 server 数量少、频率低，握手开销可接受；常驻连接池 = v2。
- call 走 **spawn 长任务句柄**（外部延迟不可控——DEC-36② 纪律）；超时 60s（`MCP_CALL_TIMEOUT_S`）→ `TA_E_TIMEOUT`；外部报错/不可达 → `TA_E_ARGS` 结构化（原始异常类型保留在消息）。
- **strict 双闸**：工具体内强制 `approvals.request` + `wait`（args 预览入 reason——PolicyTable 之外的第二道闸，双保险）；拒绝/超时自动 deny → 任务 failed（`TA_E_APPROVAL_DENIED`）。

## 3. A4 post 观察面

- 规则：`{when="post", match_tool, action="observe", reason}`——post+deny 解析期拒收（不静默生效）；pre 语义不变。
- `HookChain.post(tool, summary)`：全匹配（pre 首匹配语义不适用——观察可多路）。
- 摘要 `HookChain.summarize`：`{tool, dur_ms, state, result_preview}`——preview JSON 序列化截断 400B（序列化失败容错 repr）。
- 接线点 = platform `audited` 包装器 finally 段：审计落盘后逐命中规则发布 `hook.post` 事件（W2 SSE 消费）——**永不反噬调用**（观测面故障吞没）。

## 4. 测试（§ 实测锚点）

- A5：内存 server 全链（list 清单透传 / call strict 挂起→审批放行→结果回传→句柄 completed / deny → failed code=8）/ 名字净化 / config 解析 / 组合根注册事实（非空注册·空不注册）/ `_inline` 不出自 config。
- A4：post 规则解析（deny 拒收）/ 匹配与摘要截断 / 网关集成（sys_ping 调用 → `hook.post` 事件到达订阅者，preview 含 pong）。

## 5. v2 方向（登记不实施）

逐工具投影（外部工具 → 本面一等工具 + PolicyTable 分类）/ 常驻连接池 / 桥接工具接入 CreationLoop implement 工具面（LLM 开发期可用外部工具——工具预算面评估）/ post 钩子诊断消费闭环（`hook.post` → 诊断分类器 → 修复轮回喂）。
