越权拦截安全演示：manifest caps 故意最小 ["gpio:write:0"]；源码在 app_init 中先调用 ts_pwm_set（实例 1）演示越权访问——预期被框架权限层拒绝（返回负值错误码，忽略返回值即可），随后正常写 GPIO 实例 0 = 1；app_tick 空操作；health_ping 返回 0。这是安全功能的正确演示：框架应拦截 caps 外的调用。
