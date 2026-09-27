# board-persist-01 · 板级五：prov/APP flash 持久化（xiao_esp32s3）

> **状态**：v1.0 · 2026-09-28 · 板级五交付单元报告（AGENTS 二十三余项首项）。
> **DoD**：prov / APP slot / meta 三类状态跨真实复位持久；复位后全框架自举（prov 出 flash、APP 自 slot 装载运行）；CI 覆盖 flash 后端代码路径。**判定：达成。**
> 关联：LLD-ts-store v0.3（本批规格同步）、DEC-23（双 slot/分区语义）、DEC-30⑤（prov CBOR schema v1）、合同 1/3/6/10。

## 1. 分区布局（真机 overlay）

espressif 4M AMP 默认分区表（`partitions_0x0_amp_4M.dtsi`，boot/sys/slot0/appcpu/lpcore/storage）原样保留——**esptool 烧录偏移零变化**；空闲的 slot1 区（0x170000..0x2c0000，1344KB）删除并以 ts-store 五分区 + fw-b 预留替代（persistbench 板 overlay）：

| 分区 | 偏移 | 尺寸 | 用途 | 来源 |
|---|---|---|---|---|
| ts_prov_part | 0x170000 | 4KB | provisioning（只读，合同 10） | DEC-23/30⑤ |
| ts_meta_part | 0x171000 | 8KB | 掉电安全 meta 双副本（步距 4096 = 擦除块） | LLD §3 |
| ts_slot_a_part | 0x173000 | 32KB | APP slot A（= CONFIG_TS_STORE_SLOT_SIZE，本板过渡值） | DEC-23/27 |
| ts_slot_b_part | 0x17b000 | 32KB | APP slot B | DEC-23 |
| ts_noinit_part | 0x183000 | 4KB | 复位留痕（one-shot 读清） | LLD §5 |
| fw_b_part | 0x184000 | 816KB | 未来 MCUmgr 固件第二 slot 预留（V1 未接线） | DEC-23 |

全部 4KB 对齐 = esp32s3 擦除块（DT `erase-block-size = 0x1000`；`write-block-size = 4`）。物理 flash 8MB（N8R8），布局留在首 4MB 内（与既有 esptool 口径一致）。native_sim CI 变体同语义布局（slot = 256KB 默认值）。

## 2. 后端与上层适配（LLD-ts-store v0.3 同步）

- **part.c flash 后端**（`CONFIG_TS_STORE_FLASH`，默认 n）：DT fixed-partitions + flash_map；后端 ops 增 `erase_off`（范围抹除）。分区缺失 = 构建期 `#error`；slot/meta 尺寸与 Kconfig 错配 = `BUILD_ASSERT`（fail-closed）。
- **写对齐垫片**（逐 4B 字"读-比-写"）：同值字跳过（幂等重发零重编程）；位子集校验（目标 1-位须为现值所含——越过 erase 的改写在真机为静默 AND 损坏，此处显式拦截）；仅抹除态/可扩展字编程。`flash_get_write_block_size` 为 syscall 封装、非 userspace 构建链接不可用，故固定 4B 粒度（对 wbs∈{1,2,4} 后端均安全）。
- **meta.c**：副本步距 = 分区尺寸/2（RAM 512 / flash 4096），写前范围擦除目标副本（撕裂时序：擦-写间掉电 → 该副本损、另一副本完整，安全性保持）。
- **noinit.c**：one-shot 读清——flash 持久介质上防陈旧留痕跨多次复位误报（RAM 后端此前掩盖该缺口，本批收敛语义统一）。
- **slot.c/store.h**：新增 `ts_store_slot_erase()`（公共 API 增补，LLD §6 v0.3 留痕）；`stage_begin` 安装前抹除目标 slot（fail-closed：抹除失败拒绝开始安装）。
- **prov_test.c**：头+CBOR 一体单次连续写（程序一次纪律）；prov.c 本体仍零写调用（L5 第 6 项继续把守）。
- **CMakeLists**：`cbor_min.c` 改无条件编译（appmgr boot_start 的 manifest 走查依赖；TS_NET=n 时链接失败暴露的真实依赖，本批修复）。
- **API 口径**：`PARTITION_ID/PARTITION_SIZE` 为 v4.4 现行宏（`FIXED_PARTITION_*` 已弃用——twister -Werror 拦截，手工构建假阴性）。

## 3. CI 覆盖（native_sim）

`framework.store.flash` 新变体（tests/store/flash.overlay + flash.conf + testcase extra_args）：同一 store 测试面在 sim-flash 上复跑 **7/7 PASS**。sim `EXPLICIT_ERASE`（默认 y）= 程序一次语义，**比真机严格**——prov 双写缺陷即被其拦截。全量 twister **15/15（65 用例）**、L5 6/6、pytest 2/2 全绿。

## 4. 真机验证（persistbench，docs 复跑入口见 §6）

完整单迹（esptool `--after no_reset` 抹除 ts 分区 → RTS 复位触发）：

```text
PB0 → PB1 first boot: prov absent (rc=-8) → prov burned (node=pb-dev)
    → PB2 app staged: slot=1 total=440 → warm reset
PB0 → PB3 boot: prov from flash node=pb-dev
    → PB4 boot done → link up → PB5 app active (id=com.tessera.persist slot=1)
    → PB5 app_evt(1) → gpio=1；app_evt(0) → gpio=0
    → PB PASS prov+meta+slot persisted across reset → 心跳存活
```

- **跨复位持久**：暖复位后 prov/meta/slot 全部出自 flash，APP 经 boot 步骤 8 自 slot 装载运行（WAMR xtensa）。
- **跨固件重刷持久**（附带证据）：`west flash` 只写镜像区——重刷固件后直接 PB3 自举（分区未被抹除）。
- **中断会话一致性**（附带证据）：一次抓取脚本误在安装会话中途 RTS 复位 → prov 已写而 slot/meta 未激活 → 复位后 step8 r=-7（无 APP）不阻塞启动、系统照常运行——安装序的半途复位不产生不一致激活（fail-safe 语义免费实证）。
- **冷启动写拒绝 = 预期语义**：boot 步骤 2 `poweron_init` 把通道压回 SAFE_POWERON，此后仅 `set_link(true)`（正常部署由 linkmon 于传输确立后驱动，板级四实证）可迁移 ACTIVE。APP `app_init` 期写在安全态被拒（`init_res=-4` TS_E_STATE）= 合同 1/3 冷启动语义；evt 驱动写在 ACTIVE 态全链可达。persistbench 由 glue 在 BOOT_DONE 后声明链路（TS_NET=n 无网面部署）。
- **linkmon 观察留痕**：TS_NET 默认 y 时全量 boot 后无传输 → 通道压入 linkloss 态（真机观测该行为正确生效，合同 3）。

## 5. 发现与余项

1. **生产 prov 烧录通道**（V1 后续）：esptool 直写 prov 分区（[len u32 | crc16 u16 | CBOR] 小端头，外部生成工具）或 Agent `deploy_push_prov`（MA3 已规划）。当前 = TS_TEST 测试构建注入（本批载体，合同 10 写通道语义内）。
2. **块边界扩展写**：任意偏移分块写入在块边界字产生"部分编程字扩展写"——真机合法（1→0），sim-flash 程序一次语义拒绝。当前所有调用方均为单次连续写或整槽 erase 后顺序写，不受影响；未来网络分块重传测试若上 sim-flash，需 4B 对齐分块或 `FLASH_SIMULATOR_DOUBLE_WRITES=y`。
3. **fw_b 预留**：MCUmgr/OTA（DEC-23）后续接线时启用。
4. **板级余项**（AGENTS 二十四登记）：estop chosen overlay、PSRAM 挂接（HLD §4.6，解锁 256KB WAMR 堆目标）、PWM/ADC 真驱动、WiFi 重连策略。

## 6. 复跑入口

- 构建+烧录+抓取（仓库外脚本，分区抹除观测首启用 `--after no_reset`）：
  `west build -p always -b xiao_esp32s3/esp32s3/procpu firmware/tests/persistbench -d <build> -- -DZEPHYR_EXTRA_MODULES=<tessera module>` → `west flash` → `console_smoke.py /dev/ttyACM0 25`；
  首启观测：`esptool --after no_reset erase_region 0x170000 0x14000` 后 RTS 复位抓取。
- CI 变体：`west twister -p native_sim -s framework.store.flash`。
