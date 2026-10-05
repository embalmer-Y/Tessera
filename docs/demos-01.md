# MD1.1 · demo 阶梯第一批（D1/D2/D3/D5/D7）——单元报告

> **日期**：2026-10-05 · **状态**：**部分交付**——五 demo LLM 生成全过（产物入仓）+ 验证基础设施全通 + D1/D2/D5 判据 PASS（D1 含 res=0 全链）；**D3/D7 被 P1 缺陷阻塞**（连续激活的 copy0 写入模式装载错位，见 §4）。
> **上位**：plan v1.19 MD1；docs/agent-demo-readiness-01.md 阶梯。

## 1. 交付内容

1. **五 demo 真实 LLM 生成全过**（MiniMax-M3，`agent/demos/D{1,2,3,5,7}/`：spec.md / app.c（LLM 源码）/ app.wasm / manifest.json / *.tsap 签名包 / md1.pub——复现基线固化入仓；私钥仓外）。产物 199-283B wasm，导入面全部 ⊆ 白名单，四回调导出齐。
2. **deploybench 扩 PWM 通道**（板级九绑定并入：LEDC_CH0→GPIO21 + `dbpwm` 通道 limits max=5000Hz|700‰）——D3 限幅判据载体；dram 99.39%（通道容量 8→4 再裁）。
3. **deploybench 连续部署修复**：DB6 alive 循环持续检测后续激活（板级十单次部署设计在连续部署暴露——第 2 个起 demo 永远 STAGED）。
4. **验证基础设施（md1_run3 模式）**：① **host 心跳线程**（`…/sys/hb-host` 1s 周期 publish——linkmon 判活源是 **publish 心跳而非 query**，此前所有 client 都没发过 → 通道永远 SAFE 态，写全 -4 被拒〔合同 3 正确行为，判据盲区〕）；② 确定性装载等待（app_id+state 轮询，替代固定 sleep）；③ audit 行为判据（16 条快照：res/kind/value_u）。
5. **app_develop 健壮性两补**（MD1.1 实证）：MiniMax-M3 结构化输出的**数组字段偶发 `{"item": X}` 包装**（传输层伪影）——DevelopOutcome 列表字段 BeforeValidator 确定性解包 + 系统提示禁包装 + manifest 层链内解包（三处，留痕）；链外回路预算 3→4（CHAIN_RETRIES，两类缺陷叠加实测）。

## 2. 真机验证结果（三轮 + 单推实验）

| demo | 判据 | 结果 |
|---|---|---|
| D1 LED 慢闪烁 | get-app ACTIVE + audit **res=0** 成功写值含 0/1 | **PASS**（res=0 全链：心跳→链路 ACTIVE→写落硬件；一轮实证，另两轮受 16 条快照窗口/§4 影响） |
| D2 健康心跳 | ACTIVE + init 写 value_u=1 经框架（冷启 SAFE 窗 -4 属时序必然，判据接受 res 任意） | **PASS** |
| D5 越权拦截 | ACTIVE + 合法 gpio 写经框架 + **audit 无 PWM 条目**（越权调用被 perm 层拒绝于 commit 之前） | **PASS** |
| D3 PWM 限幅 | audit 含 -12 + 700‰ 编码限幅条目 | **被 P1 阻塞**（装载错位；单推装载后 PWM 条目全 -4 = 心跳链路未 ACTIVE 时拍的，限幅档数据未采到） |
| D7 健康回滚 | get-app ROLLBACK + slot 翻转 | **被 P1 阻塞** |

**过程事实（如实）**：冷启装载的 init 写必然落在心跳恢复前的 SAFE 窗（-4）——系统时序事实，非缺陷；判据已按此语义定稿。D1 的 res=0 判据窗口与 audit 环滚动有交互（1s 周期写 vs 16 条快照），下批把 D1 判据采样改为双拍合集。

## 3. 三项新机制知识（demo 基础设施的事实源）

1. **linkmon 判活 = host 心跳 publish**（`tessera/<n>/<c>/sys/hb-host`，1s 周期；恢复滞回 2 拍）——Agent 侧不发心跳则通道永远 SAFE 态、一切写被 -4 拒。**部署类 client 必须带心跳**（md1_run3 模式已固化为模板）。
2. **冷启装载时序**：装载（step8）先于链路恢复（WiFi+zenoh+心跳滞回 ~10s）——APP 的 app_init 写必然被 SAFE 态拒绝；行为型 demo 的写应放 tick/evt（链路恢复后）而非 init。
3. audit = 64 深环 + 16 条导出快照——高频写 demo 的判据要考虑滚动窗口。

## 4. P1 缺陷登记：连续激活的 copy0 写入模式装载错位（阻塞 D3/D7）

- **现象**：连续 activate 流（≥3 次）中，**写 meta copy0 的激活（seq 较小侧轮转）在暖复位后装载旧 slot**——三轮统计：D3（第 3 次，写 copy0）3/3 复现、D7（第 5 次，写 copy0）3/3；写 copy1 的（第 1/2/4 次）0% 复现；D3 单推（第 6 次，写 copy1）装载成功。
- **已排除**：meta 双副本读写逻辑审计无果（read 选序/写侧选择均复核）；**esptool 物理dump 证明 copy0 写已落盘**（seq/slot 值正确）且 activate 内回读 memcmp 通过——即"写成功落盘、复位后固件读不回/不选它"。
- **定位方向（专项单元 MD1.1b）**：真机 esp32 flash 读路径的复位前后差异（cache/XIP 语义）、erase_off+write 时序窗、或 read_rec(0)（分区相对 offset 0）路径特有行为；复现载体 = persistbench 型三轮激活 + 每步 esptool dump + 板上 meta_read 打点。**修复前 D3/D7 类（依赖第 3+ 次激活的 demo）阻塞**。
- sim 侧（native_sim flash 变体）twister 用例仅覆盖 2 轮 meta 写——加 ≥3 轮轮转用例入 MD1.1b。

## 5. 复跑

```bash
# 生成（真 LLM，产物入仓 agent/demos/）：bash ~/project/logs/run_md1_gen.sh
# 真机五轮（擦分区→刷 deploybench→心跳+判据）：bash ~/project/logs/md1_e2e.sh
#   （内部 md1_run3.py；当前 D3/D7 受 §4 P1 阻塞——期望 D1/D2/D5 PASS）
```
