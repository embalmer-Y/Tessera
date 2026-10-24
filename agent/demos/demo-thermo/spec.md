温控滞回多文件工程演示（D-AG7，通用域解放 Agent 批 AG7 验收）：用多文件工程（main.c + thermo.c + include/thermo.h，头文件经引号包含 #include "include/thermo.h"）实现确定性温控滞回逻辑，验证创作循环路径全链。

【需求】app_init 仅 log "ag7 init"。app_tick（100ms 周期）经 int ts_adc_read(int ctx, int inst)（ctx 传 0，inst 传 0）读温度毫伏值 mv；滞回控制加热器：加热关断状态下 mv < 2500 → 开加热（经 int ts_gpio_write(int ctx, int inst, int v)（ctx 传 0，inst 传 0，v 传 1），heat_on 计数 +1）；加热开启状态下 mv > 2800 → 关加热（v 传 0）。每 tick cycles 计数 +1；每 20 tick 用 int ts_kv_save(int ctx, const char* buf, int len) 保存一次累计 cycles（十进制手写转换，≤16B 缓冲静态数组）；cycles 达 200 → log "AG7 DONE cycles=200 heat=<heat_on 累计开关次数>"（十进制手写转换）后进入空操作终态。health_ping 恒返回 0。控制决策与计数状态经 include/thermo.h 声明、thermo.c 实现（thermo_step(int mv, int* heat_out) 形态——main 只做 natives 调用与编排）。

【资源】caps=["adc:read:0","gpio:write:0","kv:write:0"]；无 fs/av/net 需求。

【判据】"AG7 DONE cycles=200 heat=<n>"（n = 加热累计开启次数，十进制）

【安全声明】输出仅经 ts_gpio_write（保护层限幅路径）；确定性（无随机/墙钟分支）；越权 natives 不调用；health_ping 恒 0（业务终态经 ts_log 行表达）。
