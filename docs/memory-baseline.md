# Tessera 最低内存基线（Memory Baseline）· v0.1

> **本文件是什么**：Tessera 系统按配置档的 DRAM/PSRAM/FLASH 最低需求——DEC-70②（owner：「记录这一套系统的最低要求下内存的需求是多少」）。数据来源 = **memory_audit（LLD-agent-memory-planner）对三档载体的实测构建账**（2026-10-19，Zephyr 4.5.0-rc1 / SDK 1.0.1 / ARM 重建机）。
> **消费方**：R12 板卡选型 / BV1 画像内存门（v2）/ 新板内存可行性预判。
> **口径**：某档最低需求 = 静态账（map 实测）+ 最低可行堆/栈配置值（本批实测通过组合）。推定项逐条 ⚠ 标注。

## 三档实测总账（ESP32-S3 同系，dram0_0_seg = 399108B ≈ 390KB）

| 账面 | 最小 net 档（netbench） | 标准档（deploybench） | 全外设档（atkbench） |
|---|---|---|---|
| 配置差 | 无 WAMR/无 TLS/无 UI/无音频 | +WAMR（PSRAM 堆）+store | +TLS mTLS+LVGL+音频+SD+shell |
| **审计判定** | **PASS** | **PASS** | **WARN**（R5 接受态，见下） |
| dram0 used | 349688B（341.5K） | 342076B（334.1K） | 333572B（325.8K） |
| dram0 保留（IRAM 镜像窗等） | 42208B | 49712B | 62976B |
| dram0 链接余量 | 7212B（7.0K） | 7320B（7.1K） | 2560B（2.5K） |
| 系统堆定值 | 139356B（139264 配置+头） | 131144B（131072 配置+头） | 58452B（58368 配置+头） |
| irom0（代码） | 491696B（480K） | 572688B（559K） | 984144B（961K） |
| drom0（rodata） | 53888B（53K） | 65368B（64K） | 117240B（115K） |
| PSRAM | 不需要 | WAMR 堆 512KB + 装载/验签缓冲 ⚠账面细化（v2——别名窗归并） | 同左 + SPIRAM 可分配堆 4MB |

## 各档具名大头（决定下限的结构性项）

- **共同底座**（三档共有）：pico pthread 栈池（netbench/deploybench 4 槽 × 8192 = 32K；atk 2 槽 = 16K——R5-V① 重平）、main 栈 8192、rx_q 栈 4096（FIX-1 防御）、sysworkq 4096（R5-V③ 防御）、ISR 2048、net mgmt/wifi 事件栈 2048×2、tcp slab、zenoh 会话静态面。
- **最小 net 档增量**：≈ 无（底座即主体；heap 139KB 承载 zenoh 会话 + lwIP 动态面）。
- **标准档增量**：+WAMR 宿主静态面（PSRAM 堆 512KB 不占 DRAM）、+store 槽池/验签链、+net_wq 8K。
- **全外设档增量**：+mbedtls 静态堆 31744B（TLS 握手有界化——Q-47⑤）+LVGL 专池 16384B（F3-1 运行时下限）+es8311 DMA 缓冲 10K（5K×2）+shell/interact 静态面+prov_tls/idem/audit 等 ts 面。

## 最低需求声明（本批实测通过组合）

| 档 | DRAM（region 总量） | FLASH | PSRAM | 关键栈/堆下限（规则联动） |
|---|---|---|---|---|
| 最小 net 档 | **390KB**（余 7.0K） | ≈545KB | 不需要 | heap ≥139264 / rx ≥4096 / sysworkq ≥4096 |
| 标准档 | **390KB**（余 7.1K） | ≈638KB | ≥1MB（WAMR 512K + 双缓冲装载/验签）⚠ | heap ≥131072 / 同上 |
| 全外设档 | **390KB**（余 2.5K——擦边态） | ≈1.1MB | ≥1MB（同上）+ 建议可分配 4MB | heap 58368（R5 接受态）/ shell ≥4096 |

**同芯片外推**：DRAM 需求由「底座静态 ~200K + 堆」主导——128KB RAM 级 MCU 需先做底座裁剪（无 zenoh 的裸 core/safety 档随 P4 判定批实测回填 ⚠）。
**跨芯片**：本批三载体同为 ESP32-S3；RISC-V/ARM 端实测随 v4.5.0 平移批（P4 判定批）与 BV1 第二任务回填 ⚠。

## 全外设档 R5 接受态（如实登记）

系统堆 58368 < R5 建议 65536：P1-2 实测 50-56K 档 TLS 建链期 z_malloc -80 循环、58368 档全链可用（P1-2/FIX-1/本批三次真机全链 PASS）。+7K 无干净捐主（dram0 链接余量仅 2.5K；栈/池全部为实测下限）。**处置 = WARN 接受 + 残余观察**：wifi TX ENOMEM 噪声降频未根除（TX cap 32→16 后小包部署仍 3 次/窗——证据 mp_atk_enomem_console.txt；部署链可靠 PASS）。根除路径 = zenoh 缓冲 PSRAM 化（风险 = 教训 41 同域）或堆结构性重平——MP v2 / atk 板级专项登记。

## 过程陷阱（本批实录，规则化来源）

1. **声明≠生效（R0）**：三 bench prj.conf 死堆值被板级 conf 覆盖（196608 声明 vs 58368/139264/131072 生效）——堆值权威一律以 `.config` 为准。
2. **构建期间改 conf = 静默中间态**：ninja 后期 kconfig 重跑吃到编辑中间态（deploybench NET_MAX_CONTEXTS 12→6 假象）——构建运行期间禁改 conf 文件。
3. **最小档构建回归**：WAMR=n + APPMGR=y 组合自 M7（Q-32⑤ 激活停旧）起链接断链——pkg.c stage_commit 门控修复随本批；基线档必须实际构建验证（「曾经构建过」≠「现在能构建」）。
