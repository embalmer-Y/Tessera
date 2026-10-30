# docs/evidence/README.md · 真机证据留痕索引

> **本文件是什么**：2026-10-24 仓整理（DEC-78）为 52 件真机验证留痕建立的索引——
> 文件名沿用历史会话单元代号**不回溯**（历史登记不回溯 + 引用链稳定；代号释义见
> `docs/names.md` 与 AGENTS 历史归档 `docs/history/agents-status-archive.md`）。
> **新增证据建议命名**：`<主题>-<yyyymmdd>.txt`（docs/std/naming.md §2）。

## 索引（按单元批次）

| 文件 | 内容 | 会话/登记 |
|---|---|---|
| ab_PASS_console_native_rerun.txt / auditbench_AB_PASS.txt | 审计 A/B 对拍（native 重跑）PASS | 审计批 |
| af12_boot_console.txt / af12_console.txt | F1/F2 BOOT 手势三动作真机判据（席位切换/本地 estop） | 一三〇 |
| af31_lcd_console.txt | F3-1 LCD bring-up（LVGL + AKU1） | 一三二 |
| af3_gate_console.txt / _confirm_ / _reject_ | F3 安装闸三路（timeout 60s fail-closed / 短按确认 / 长按拒绝） | 一三三/一三八/一三九 |
| af4_console.txt | F4 peripherals 自报真机实证 | 一二七 |
| af6_console.txt | F6 分块流 WDT 优先级饥饿根治（1ms 让步单轮全绿） | 一二八 |
| ag7_console.txt | AG7 真 LLM 多文件工程创作循环 | AG 批 |
| ak1_console.txt | K1 第二板（atk DNESP32-S3B）bring-up | 一二四 |
| ak3_trust_console.txt / ak3_trust_driver.txt | K3 信任链 E2E T0-T7 + 驱动 | 一二六 |
| ak45_console.txt | K4 资源推送 + K5 large 档全链 | 一二七 |
| ak6_console.txt | K6 多真机 LN 双 ACTIVE | 一二七 |
| ak_audio_console.txt | K2 ES8311 音频（录音/放音/SPK_EN） | 一二四 |
| arm64_rebuild_20261017.txt | ARM 重建机全链（§8 随机重启破案 + §9a NVD PASS） | 一四五 |
| bv1_atk_console.txt / bv1_c6_crash_console.txt | BV1 板卡验证首战（C1-C5 PASS；C6 rx_q 栈溢出崩机实抓） | 一四八·续十 |
| bv2_first_board_console.txt | BV2 适配流水线真板首实战全链 | 一五五 |
| bvfix_c6_console.txt | FIX-1 板级部署崩机专项 C1-C6 六项 PASS | 一四八·续十三 |
| cg7_deploy_console.txt | CG7 合同泛化部署链 spot check | 合同泛化批 |
| d8_PASS_native_rerun.txt | D8 lifecycle demo native 重跑 PASS | V2 批 |
| dav_norecover_console2.txt | AV demo 不可恢复故障路径 | MD1.2 |
| dp_PASS_console.txt | D-PDM 音频真机 PASS | MD1.2 |
| dsd_PASS_newcard.txt | D-SD（重格新卡后）真机 PASS | 一四三 |
| dt_PASS_console.txt | D-THR 真 wasm 多线程 PASS | V2 批 |
| fix2_p4_probe_console.txt | FIX-2 P4 探针根治（ALIVE t=11s 首印/C1-C6 全绿） | 一五四 |
| frame_2.rgb565 / frame_3.rgb565 | AV 视频帧样本（二进制图像） | 视频批 |
| ma_PASS_console.txt | 多 APP 并行部署 PASS | M 批 |
| mp_atk_enomem_console.txt | MP 内存重平后 ENOMEM 观察窗（接受态登记） | 一四八·续十二 |
| nv1_PASS_console.txt / nv1_loop_result.json / nv1_simreal_baseline.json | NVD v1 判定（console + 循环结果 + sim/real 基线） | NV 批 |
| nv6_PASS_console.txt / nv6_result.json | NVD v6 全链 PASS（判据精确命中） | NV 批 |
| nvd_PASS_console_native.txt | NVD native 口径 PASS | NV 批 |
| nvd_app_source.c | NVD heartbeat app 源留档 | NV 批 |
| p1_tls_blocker_console.txt / p1_tls_e2e_console.txt | P1-2 TLS 阻断定位（PSA ECDSA）与 E2E 收口 | 一四〇/一四二 |
| p4w1_console.txt / p4w2_console.txt | P4 WiFi 数据面复活 / P4 入 LN 网 | 一五二/一五三 |
| p4c5_audio_acoustic_loop_20261030.txt | P4C5 音频声学回环 PASS（引脚定案 + 根因链） | 一七三 |
| pdmb_PASS_console.txt | PDM bench（8 帧活信号） | M17 |
| periph_restore_console.txt | 外设三路失败破案（I2C0 锁死）+ 板复原 | 一四三 |
| r2_tls_oneway_root_cause.txt | R2 TLS 单向黑洞根因 + ≤15s 自愈判据 | 一四六 |
| r5_interact_console.txt | R5 单 UART 三合一首战（DRAM 净缺回退如实） | 一四七 |
| r5v_verdicts_console.txt / r5v_zombie_heal_console.txt | R5-V 僵尸自愈 + 终端确认/拒绝四判据 | 一四七 |
| w2_hb_boot_console.txt / w2_hb_live_console.txt | W2 web 验收心跳部署（LED 缺陷 168 对实录在 live） | 一四九 |
