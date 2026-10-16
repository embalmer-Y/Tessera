# D-AK4 · K4 net+SD 资源推送真机 demo（CG5-B 方案 A 消费端）

> 2026-10-16 K4（plan §11f）。atkbench @ akn/akc（dnesp32s3b 板载 TF 槽
> SPI2：SCK=IO7/MISO=IO15/MOSI=IO16/CS=IO17——引脚分配表权威）。

## 链路

1. 宿主编译 app.c（clang wasm32，caps fs:read + fs_paths ["/SD:/res"]）
   → 测试根签名打包（needs.resources = ["/SD:/res"]）。
2. `deploy.push_app` → activate（needs.resources 前缀白名单随包激活绑定）
   → 暖复位装载。
3. `deploy.push_resources`（sys/fs-begin/chunk/commit + sha256 读回校验）
   推送 `/SD:/res/ak4.txt`（36B = "AK4-RES-" + 28 数字）。
4. APP 逐 tick 轮询 `ts_fs_read`：字节级命中 → console `[appN/l0] ak4
   match=1` + `AK4 DONE`；40 tick 未命中 → `AK4 FAIL`。

## 判据

- 驱动侧：push_resources 每文件 `verified` 回执（固件全量读回 sha256 一致）。
- 板侧：console `ak4 match=1` + `AK4 DONE`（推送内容经 APP 消费端字节级复核）。
- 驱动 = ~/project/logs/ak4_res_e2e.py（仓外惯例）。

## 与 D-SD 的分工

D-SD（MD1.2f）= APP 自写自读（本地写入面）；D-AK4 = **宿主推送 → APP 消费**
（CG5-B 部署会话资源推送面——fs 写命令通道的真机消费闭环）。
