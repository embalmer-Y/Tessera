# av-transport-01 · 视频帧 zenoh 分片传输真机测量（MD1.2d spike，Q-27 数据底座）

> **本文件是什么**：avbench（`firmware/tests/avbench/`，AV* console 行）真机测量的报告与根因链——为 MD1.2d 的 zenoh 视频帧传输面设计（Q-27 呈递）供实测数据。
> **环境**：xiao_esp32s3/esp32s3/procpu/**sense**（OV2640 DVP）→ WiFi STA（PS 关）→ zenoh-pico 1.10.1 直连 PC zenohd 1.10.1（tcp/0.0.0.0:9955）；PC 侧接收器 `~/project/logs/av_recv.py`（订阅重组校验）。**隔离设计**：不经 ts-net 框架——传输层独立测量。
> **日期**：2026-10-06。

## 1. 结论（设计参数来源）

| 设计参数 | 实测依据 |
|---|---|
| **分片尺寸 ≤1KB（建议 1KB）** | 512B/1024B 档零错误全达；**>2KB 系统性失败**（zenoh-pico `Z_BATCH_UNICAST_SIZE=2048` 静态生成头〔`include/zenoh-pico/config.h:26`，无 #ifndef 守卫不可编译期覆盖〕——超限走碎片路径 `_z_transport_tx_send_fragment`，打拍+重试下仍不完整） |
| **发送间隔 ≥4ms（打拍纪律）** | 背靠背（无间隔）任意尺寸大量失败（-100 errno=0）；2ms 打拍 512B 档 3 错/300；4ms 打拍两支持档 0 错 |
| **分片级应用层重试（≤5 次 × 20ms）必须** | WiFi 降级时段 z_put 返回 -100 而 BLOCK 语义不保数据（TCP 可靠但 zenoh-pico 客户端在 tx 缓冲/背压面直接拒绝——首个失败 errno=0 = 未达系统调用）；应用层重试实测可恢复 |
| **有效吞吐（QQVGA RGB565 38400B/帧）** | 512B 档 87KB/s（≈2.3fps）；**1KB 档 172KB/s（≈4.5fps）**；PC 侧重组对拍一致（88.2/173.7KB/s）。提 fps 须换 JPEG（OV2640 硬件 JPEG，QQVGA ~5-10KB/帧 → 15-30fps 量级可行）——Q-27 子项② |
| **内存形态** | 视频池 256KB 入 **PSRAM**（`VIDEO_BUFFER_USE_SHARED_MULTI_HEAP=y` + 属性 2=SMH_REG_ATTR_EXTERNAL——psrambench 同机制）；**DVP GDMA 接受 PSRAM 池缓冲**（AV3b 地址 0x3c08xxxx，4 帧真实捕获）；内部 DRAM 保留 188416 系统堆给 WiFi+zenoh（deploybench 档位）——三合一（WiFi+zenoh+视频池）共存实证 |

**终态判据（AV PASS）**：支持档（512/1024）0 错误 0 重试完成矩阵 + PC 侧 4/4 帧完整重组（38400B 校验）双绿；2048/4096 登记为预期不支持（碎片路径，仅报告）。

## 2. 分片协议（bench-only，产品协议由 Q-27 裁定）

- key：`tessera/avbench/frame`（bench 专用键空间，不入产品 keyspace 语义）。
- payload = 16B 头 + 数据（大端）：`cfg u32 | frame u32 | chunk u32 | n_chunks u16 | len u16`。
- QoS：`Z_CONGESTION_CONTROL_BLOCK + Z_PRIORITY_DATA`（视频数据档，非安全 REAL_TIME 档）。
- PC 侧按 (cfg, frame) 重组，块集完整性 + 字节总数双重校验。

## 3. 根因链（过程如实）

1. **板级 conf 片段未生效**：sense 板四段名（`xiao_esp32s3_esp32s3_procpu_sense.conf`）——首版按三段命名，`CONFIG_ESP_SPIRAM` 未入 .config → SMH 无外部区域且 `shared_multi_heap_pool_init` 未跑 → `smh_choice` 回调 NULL → **PC=0 崩溃（EXCCAUSE 20 inst fetch prohibited，寄存器实锤 A3=2/A4=0x20/A5=0x9600 = SMH 调用入参）**。改名后消失。
2. **z_put -100（`_Z_ERR_TRANSPORT_TX_FAILED`）三触发面**（errno 语义经清零对照 nailed）：
   - **背靠背**：任意尺寸大量失败，errno=0（失败未达 `send()` 系统调用——zenoh-pico tx 序列化/背压面内部拒绝）；
   - **>2KB 碎片路径**：系统性失败（部分可被重试挽回但不完整）；
   - **WiFi 降级**（环境方差，实测同参数两轮一轮 0 错一轮 193 错/300、吞吐跌 4.5×）：重试可恢复。
3. **lwIP TX 池**：官方 tcpserversink 样例同款方向的调档实验——512×1KB 静态缓冲致 DRAM 溢出 510KB，最终小档（NET_PKT_TX_COUNT=16/NET_BUF_TX_COUNT=48/NET_BUF_DATA_SIZE=512）装入；失败主因不在 lwIP 池（支持档零错误在默认与小档下均达成过）。
4. 周边事实：zenohd 须绑 `0.0.0.0`（127.0.0.1 板不可达）；`~/project/tools/zenohd` 为本机 router 二进制；快速连续复位下 AP 的 DHCP ~50% 不应答（断开重连三轮循环根治）；cmake 字符串变量传 C 须由 `target_compile_definitions` 显式接线（deploybench 的 ROUTER 宏从未在 C 表达式用过——双层引号历史无咬，avbench 首用即现形，改传裸值由 CMake 加引号）。

## 4. Q-27 呈递关联（详见 decisions.md Q-27）

实测直接支撑的建议：① 专用帧分片通道（publish 面）；② 1KB chunk + 发送线程打拍 + 分片级重试；③ JPEG 帧格式（OV2640 硬件压缩）；④ ts-av/ts-fs natives 最小面 + ts_perm_v1 新类（fs 权限的路径语义须扩文法）；⑤ 视频池 PSRAM 形态（DEC-27 PSRAM 分层纪律内）；⑥ agent 侧 NATIVE_WHITELIST/manifest 同步。

## 5. 载体与复现

- `firmware/tests/avbench/`：`src/main.c`（AV* 行）/ `prj.conf`（zenoh+网络+video+SMH 池）/ `boards/xiao_esp32s3_esp32s3_procpu_sense.{conf,overlay}`（PSRAM+WiFi）。
- 仓外工具（凭证不入库纪律）：`~/project/logs/avb_build.sh`（构建，凭证 cmake 注入）/ `avb_flash.sh`（router+接收器+烧录+console 编排）/ `av_recv.py`（PC 侧重组判据）。
- 判据行样例（终态轮）：`AV5 cfg=1024B n_chunks=38 frames=4 total_ms=869 max_frame_ms=218 thru=172KB/s puts=152 retries=0 errs=0` + `AVR cfg=1024 frame=3 chunks=38/38 bytes=38400 OK`。
