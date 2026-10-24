健康探针自动回滚演示：app_init 写 GPIO 实例 0 = 1；app_tick 计数，第 20 次 tick 之后 health_ping 返回 1（模拟 APP 自身故障）——框架健康探针（1s 周期、连续 3 次失败）将自动停止并回滚该 APP；caps 仅 ["gpio:write:0"]。
