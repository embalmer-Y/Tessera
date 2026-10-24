PWM 呼吸灯 demo：app_tick（100ms）驱动 PWM 实例 1（hz=1000）占空比斜坡循环：每 tick +25‰，到 1000‰ 后归零循环往复（部分请求会超出通道 700‰ 限幅——由框架保护层拦截，属预期演示）；caps 仅 ["pwm:set:1"]；health_ping 返回 0。
