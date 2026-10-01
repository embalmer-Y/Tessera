# board-reconnect-01 · 板级七：WiFi 断链重连策略（xiao_esp32s3）

> **状态**：v1.0 · 2026-10-01 · 板级七交付单元报告（owner 指令"其次 WiFi 重连策略"）。
> **DoD**：WiFi/zenoh 全链断链自愈真机验证（脚本化双断链）；重连策略各层职责明确；相关框架缺陷修复入库。**判定：达成。**
> 关联：DEC-27（固定退避表/无抖动纪律）、DEC-43（线程模型 net > APP）、合同 3（断链 fail-safe——输出侧 linkmon 已有，本批补传输侧恢复）、LLD-ts-net（本批 v0.3.7 同步）。

## 1. 策略分层（职责定稿）

| 层 | 职责 | 实现 |
|---|---|---|
| WiFi STA | 关联维持 | **app glue**（Zephyr esp32 驱动无自动重连）：断线事件 → 固定 2s 重试 CONNECT（无抖动，与 DEC-27 退避同纪律） |
| IP | 租约刷新 | glue：断线时显式 `net_dhcpv4_restart`（esp32 口断线不清地址/租约——陈旧绑定态下重连同址无 ADDR_ADD 事件，实证） |
| zenoh 会话 | 传输重建 | **ts-net 自带**：session_poll 检测掉线 → close → 固定退避表 250/500/1000/2000 重 open |
| 检测加速 | 僵尸会话 | **新增 `ts_net_session_media_down()`**：承载断线事件显式下沉——静默掉线时 TCP 半开（读任务阻塞 recv、租期心跳在本地缓冲"成功"），is_up 分钟级才收敛；下沉后会话下一 poll 立即判 DOWN |
| 输出安全 | fail-safe | linkmon（已有，合同 3）：hb 丢失 → linkloss 态；恢复滞回后 set_link(true) |

## 2. 过程修复（三轮真机迭代，如实）

1. **ts-net 周期体占 sysworkq**：zenoh open/close 为阻塞 TCP 操作（死链上可达十余秒）——饿死同队列的 WiFi 重试工作（实测迟 18s）。修复：周期体迁**专用工作队列**（栈 4096/优先级 8 = DEC-43 线程序 net > APP〔10〕）。netbench 系统池相应让 8KB。
2. **僵尸 TCP 半开**：断链后会话不检测（123s 无自愈）——新增 `ts_net_session_media_down()`（见 §1）；netbench 断线事件调用。
3. **net_mgmt 回调重入自激**：事件回调上下文内调 net_mgmt（PS/DHCP 请求）→ connect/ADDR 事件每 ~40ms 风暴、WiFi 永不稳定（z_open 连败）。修复纪律：**回调只置标志 + 提交工作项，net_mgmt 一律工作项上下文执行**。

## 3. 真机验证（netbench NB-R 场景：稳态后设备侧强制断链 ×2）

```text
NBR ready t=5734 → 稳态 15s
NBR0 forced drop #1 t=20739 → disconnect → media_down → +2s 重试 → 关联(7.0s)
  → zenoh 重开 CONNECTED → NBR9 recovered #1 全链自愈=9222ms
NBR0 forced drop #2 t=39966 → 同路径 → 关联(2.0s) → zenoh 重开
  → NBR9 recovered #2 全链自愈=4230ms
NBR PASS cycles=2 → 心跳稳定（assoc=1 net=1 持续 90s+）
```

- **双断链全链自愈 4.2s / 9.2s**（WiFi 重关联主导：第二次 2s vs 第一次 7s = 快关联缓存生效）。
- zenoh 同进程 close→re-open 生命周期真机实证可用（此前未验证）。
- **恢复后命令面**：客户端 L1 sys 查询 ×30 零失败、p50 13.4ms（与板级四基线 12.0ms 一致）；L2 estop-clear p50 17.9ms 正常。
- 断链窗口客户端侧证据（第一轮实测）：L1 无应答即中断（对侧观测）。
- 局限如实：设备侧强制断链 = 与 AP 侧掉线在 STA 视角等价（断线事件 + 同一恢复路径代码）；真实 AP 断电场景未测（需控制 AP，板级环境无）。

## 4. 回归

twister **15/15（65 用例）**（session/media_down/专用队列改动全量回归）/ L5 6/6 / pytest 2/2 全绿。

## 5. 复跑入口

`bash ~/project/logs/nb_flash.sh pristine`（凭证仓库外注入）→ `console_smoke.py /dev/ttyACM0 120`（关注 NBR0/NBR9/NBR PASS 行）→ `netbench_client.py 30`（恢复后命令面）。
