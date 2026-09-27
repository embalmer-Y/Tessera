# WiFi + zenoh 命令往返时延报告 netbench-01 · 2026-09-27（板级四单元，owner 指令）

> **问题**：esp32s3 采用 WiFi + zenoh 网络通信，从命令下发到数据回传需要多久？
> **链路**：xiao_esp32s3（WiFi 2.4G_STA → AP "cemetery" → 有线 LAN）→ PC（192.168.2.90，WSL mirrored 里的 zenohd v1.10.1 @tcp/0.0.0.0:9955）← PC 侧客户端（eclipse-zenoh，本机接入）。
> **载体**：`firmware/tests/netbench/`（板固件：WiFi 连接 + DHCP + prov 烧入 + ts-net/zenoh-pico 完整命令面）+ `netbench_client.py`（三层探针）。
> **口径**：N=100/层（预热 5 弃置），perf_counter 计时；两轮复现（p50 差 <4%）。

## 1. 数据（WiFi 省电关闭后；2026-09-27 两轮一致）

| 探针 | min | p50 | p95 | max | 失败 |
|---|---|---|---|---|---|
| L0 路由本机回环（客户端→zenohd→客户端，纯 PC 跳） | 0.06 | **0.10 ms** | 0.26 | 0.40 | 0 |
| **L1 sys 查询全路径**（WiFi→zenoh→CBOR→命令面→框架状态→回包） | 8.3 | **12.0 ms** | 28.6 | 55.1 | 0 |
| **L2 重命令路径**（estop-clear：租约/安全层交互） | 9.8 | **13.5 ms** | 27.2 | 62.2 | 0 |
| 净（L1−L0 p50，即无线+设备侧净耗时） | — | ≈11.9 ms | — | — | — |

**WiFi 省电是第一敏感项（本单元最重要发现）**：默认 modem-sleep（对齐信标唤醒）下 L1 p50=66ms / max≈105ms（≈DTIM 102ms 特征）——连接后经 `NET_REQUEST_WIFI_PS` 关闭（`esp_wifi_set_ps(WIFI_PS_NONE)`）后 **p50 66→12ms（5.5×）**。板固件已默认关闭（netbench main.c，注释留证）。

## 2. 判读

- **命令/查询场景（人机、Agent、API 级）**：12-14ms p50 优秀（无感级）；p95 ~28ms / max ~62ms（WiFi 重传/竞争尾部，正常量级）。
- **心跳/断链判据**：hb 周期 1s、断链窗 6s（DEC-22）→ 往返占断链窗 0.2%，余量充足。
- **闭环控制场景**：若把 WiFi 命令路径用于 ≤100ms 控制环——p50 可用但 p95/max 不可承诺（无线链路本质）；此类需求应走本地 APP 循环（板内 5.75µs 写路径），网络层只做下发/遥测——与架构定位一致。
- **耗时构成**：本地框架命令处理为 µs 级（board-bench-01 §1.5），~12ms 大头 = WiFi 空口 RTT + lwIP/驱动栈 + zenoh 两端协议处理；框架本身占比 <0.1%。

## 3. 环境事实与教训（详见 dev-environment 教训 21）

- 上游 Zephyr v4.4 的 esp32s3 WiFi 可用（`west blobs fetch hal_espressif` 拉预编译 blob；`&wifi` 节点默认 disabled 需 overlay 使能；驱动依赖 mbedTLS/PSA、要求非 SMP）。
- WSL mirrored 网络：WSL 监听只对 Windows loopback 互通；**LAN 设备入站需 Hyper-V 防火墙放行**（`Set-NetFirewallHyperVVMSetting -DefaultInboundAction Allow`，owner UAC 一次）——注意 Windows 本机测自身 LAN IP 走 loopback 不可作判据，须用设备实测。
- zenoh-pico 1.10.1 回调签名 = **非 const** `z_loaned_query_t*`（= `_z_query_rc_t` 直名）；新工作区首编译即拦（此前 twister 走假传输从未编过 zenoh 面）——修复后 **L3 五验证点复跑 PASS**（环境重建后首次，待办就此清账）。
- prov 板上注入：TS_TEST 通道每次启动烧入（RAM 后端；持久化 = 板级后续任务）。凭证经 cmake 变量注入，仓库零泄漏（git grep 验证）。

## 4. 复跑方法

```bash
# 路由（WSL）：~/project/tools/zenohd --listen tcp/0.0.0.0:9955
# 固件：bash ~/project/logs/nb_flash.sh pristine   # 凭证在该脚本（仓库外）
# 客户端：~/project/agent-venv/bin/python firmware/tests/netbench/netbench_client.py 100
# console：~/project/zephyrproject/.venv/bin/python ~/project/logs/console_smoke.py /dev/ttyACM0 75
```

原始记录：`~/project/logs/netbench-console.log`（NB* 行）+ 两轮客户端 JSON（本文 §1）。
