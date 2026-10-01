# board-psram-01 · 板级六：PSRAM 挂接（WAMR 实例堆外置，xiao_esp32s3）

> **状态**：v1.0 · 2026-10-01 · 板级六交付单元报告（owner 指令"优先解决 PSRAM 挂接"）。
> **DoD**：DEC-27/HLD §4.6 的 esp32s3 WAMR 实例堆 256KB 目标落地；PSRAM 分层纪律（仅 APP 沙箱内存入外部 RAM）经代码结构强制；真机全链验证。**判定：达成。**
> 关联：DEC-27 #10（池模式/每板堆尺寸）、HLD §4.6（分层纪律与每板表）、LLD-ts-appmgr v0.4。

## 1. 两条事实修正（本批钉死，均有构建/源码证据）

1. **早期"Zephyr 4.4 板级 DTS 无 psram 节点 → PSRAM 暂不可用"评估有误**：`psram0` 节点在 `esp32s3_common.dtsi`（`compatible = "espressif,esp32-psram"`，默认 okay），N8R8 模组 dtsi 定 `size = <8MB>`；`CONFIG_ESP_SPIRAM`（select SHARED_MULTI_HEAP）+ `SPIRAM_MODE_OCT`（八线必须显式——默认 QUAD 探测失败 = esp_init_psram 硬停）即启用。生产 app 板 conf 的旧注释一并修正。
2. **"WAMR 池模式 64KB"从未真正生效**：WAMR-2.4.5 中 `WASM_ENABLE_GLOBAL_HEAP_POOL` 旗标已无消费者（`global_heap_buf` 全树不存在）；`wasm_runtime_init()` 实走 **Alloc_With_System_Allocator**（内部 SRAM 系统堆）。板级二足迹数据（"libc 堆余 ~218KB"）与此一致。真池模式须经 `wasm_runtime_full_init(Alloc_With_Pool, 注入堆缓冲)` 显式建立——本批落地，零上游补丁。
   - 连带修正：**64KB 池基线结构性不可行**（线性内存一页即 64KB，池内还要装模块实例/执行环境；twister 实证 framework.app 4 用例 "allocate linear memory failed"）——`TS_APP_WAMR_HEAP` 默认 65536 → **262144**（与 DEC-27 板级目标一致；native_sim 宿主内存充裕）。HLD §4.6 表已加修正注记。

## 2. 实现

- **runtime.c 统一池初始化**：`CONFIG_TS_APP_PSRAM_HEAP=y` → 堆缓冲 = `shared_multi_heap_alloc(SMH_REG_ATTR_EXTERNAL, 256KB)`（esp32s3 PSRAM 官方注册面，soc.c 自动 `esp_init_psram + esp_psram_smh_init`）；否则 = 内部 SRAM 静态池（native_sim/CI）。init 失败 fail-closed（TS_E_NOMEM/TS_E_IO）；console 打印池地址 = 位置证据。
- **Kconfig**：`TS_APP_PSRAM_HEAP`（depends TS_APP_WAMR && ESP_SPIRAM && SHARED_MULTI_HEAP，默认 n——native_sim/CI 零影响）。
- **板 conf**：psrambench 与生产 app（firmware/app）均 `ESP_SPIRAM=y + SPIRAM_MODE_OCT=y + MEMTEST=y + PSRAM_HEAP=y + WAMR_HEAP=262144`（DEC-27 esp32s3 每板默认兑现）。
- **分层纪律结构面**：仅 WAMR 实例堆（模块实例/线性内存/APP 堆）外置；框架安全数据（ts-safety 表/审计）、ts-core、zenoh、WAMR 运行时控制面全部留在内部 SRAM（不入 SMH 分配面）。

## 3. 真机验证（psrambench，docs/board-psram-01 单迹）

```text
I (octal_psram): vendor id 0x0d (AP) … density 64Mbit   ← 8MB 八线 PSRAM 识别
I (esp_psram): Found 8MB PSRAM device / memory test OK
PS1 smh probe: buf=0x3c030060 读写一致（PSRAM 存活）       ← 外部 RAM 地址域（0x3c..）
[appmgr] wamr pool heap: buf=0x3c030060 size=262144 (psram/smh)
PS3 app_init -> gpio=1（WAMR 池=PSRAM，全链）
PS3 app_evt(0) -> gpio=0
PS PASS init_res=0 evt_seen=1 heap=256KB@PSRAM
```

- 直启面（无 core_boot）init_res=0：app_init 写入即达——与 persistbench 冷启 SAFE_POWERON 拒写（-4）互为对照，两个场景语义各自正确。
- **量化对照**：PSRAM 开 = 内部 dram0_0_seg **154928/399108 = 38.8%**（psrambench）；PSRAM 关 + 256KB 堆 = **溢出 14548B**（DEC-27 目标在 512KB 内部 SRAM 装不下的硬证据——旧"64KB 过渡值"的真实代价）；生产 app（net 全开）= 44.7%。

## 4. 回归与余项

- twister **15/15（65 用例）** / L5 6/6 / pytest 2/2 / 真机重刷复验 PASS。
- 余项（板级七起）：WiFi 重连策略（owner 次优先）、estop chosen overlay、PWM/ADC 真驱动、生产 prov 烧录通道。
- 观察项：PSRAM 速度当前默认 40MHz（`SPIRAM_SPEED` 可升 80M——性能余量留待效率基准需要时）；`ESP_SPIRAM_HEAP_SIZE`（默认 1MB）= SMH 区域上限，256KB 堆远在其内。

## 5. 复跑入口

`west build -p always -b xiao_esp32s3/esp32s3/procpu firmware/tests/psrambench -d <build> -- -DZEPHYR_EXTRA_MODULES=<module>` → `west flash` → `console_smoke.py /dev/ttyACM0 12`（关注 `wamr pool heap` 与 `PS PASS` 行）。
