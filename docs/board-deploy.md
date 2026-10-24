# 板级十 · Agent→真机完整部署 E2E——单元报告

> **日期**：2026-10-02 · **载体**：`firmware/tests/deploybench/`（板侧 DB* + Agent 侧 client.py）· **状态**：PASS（双轮全绿 + 回归全绿）
> **里程碑意义**：**双轨首次真机闭环**——AI Agent 侧 deploy 链（MA3.1 同一实现）对真板完成 发现 → keygen/打包 → 租约 → 分块上传 → 容器事实对拍 → 激活 → 板自动暖复位 → APP 自 slot 装载运行 → 复位后 get-app 对拍。
> **同批 owner 指令**：ESP32-P4 移植暂缓（decisions 登记随批）。

## 1. 交付内容

1. **deploybench 板侧载体**（`firmware/tests/deploybench/`，xiao_esp32s3）：WiFi glue（netbench 板级七定稿模式：固定 2s 重试 + 断线 DHCP 重启 + media_down 下沉）+ prov flash 持久（首启 TS_TEST 烧入，此后复位直读——板级五语义）+ ts_core_boot（zenoh 命令面 + 步骤 8 slot 装载）+ 部署观测线程（激活检测 → 自动暖复位 → DB6 运行宣告）。板 conf = 三合一内存拼装（WiFi+zenoh+WAMR）：DEC-29 每板预算裁剪 `TS_APP_LOAD_MAX 16384→2048`（夹具 286B）+ `TS_SAFETY_MAX_CHANNELS 32→8`（本载体 1 通道），系统池不动（188416 = 板级七实测档位）；WAMR 堆 256KB 入 PSRAM（板级六）。dram 99.81%（余 748B）。
2. **client.py**（Agent 侧驱动，agent-venv 运行）：**复用 MA3.1 deploy 链本体**（tools_net.deploy + ZenohService + tools_tsap——与 sim E2E / MCP 工具同一实现，非并行探针）；分块 256B（930B 包 → 4 块，证多分块路径）。
3. **跨轨命名漂移修复（被 E2E 拦下的存量缺陷）**：Agent `TsapManifest._EXPORTS_ALLOWED` 白名单 = init/tick/evt（LLD §2 笔误漂移）——固件 runtime lookup/夹具 wasm/LLD §4 调用约定三方均为 `app_init/app_tick/app_evt`，白名单照抄漂移面 = **拒绝一切真包**；env 门控的 sim E2E 默认跳过掩盖此缺陷。修复 = 白名单 + 三个测试 + LLD §2 对齐 app_*（LLD-ts-appmgr v0.5.1）。
4. **get_info 惰性初始化打回装载结果（真机首证修复）**：`ts_appmgr_boot_start` 成功后置 state=ACTIVE 但不置 `initialized` → 首次 `get_info`（观测线程/sys get-app）懒路径盲写 `state=STAGED`，**装载结果被观测面抹掉**；且 boot_start 未回填 `active_slot`（部署确认语义 = activate/get-app 槽位对拍会失败）。修复 = 成功路径置 `initialized=true` + `active_slot=meta.active_slot`（LLD-ts-appmgr v0.5.2）。

## 2. 真机时间线（DB*/DEPLOY*，两轮复现）

| 段 | 判据 | 结果 |
|---|---|---|
| 首启 | 擦分区后 prov 烧入 flash → zenoh 会话 | DB2 load=-8 burn=0 → CONNECTED t≈10s；DB3 ready slot=0 |
| Agent 发现 | 通配 get-info 自报 dbn/dbc | DEPLOY 发现 dbn/dbc fw=dev |
| 打包 | tsap_keygen + tsap_package（native_app.wasm 286B，同源夹具） | 930B TSAP，tsap_verify PASS（真 ed25519） |
| 租约闭环 | lease-acquire/续期/release（DEC-41） | holder=tessera-agent id=1，结束 released ✓ |
| 分块上传 | 4×256B，每块 idem + high_water 进度 | 930/930B → slot 1 |
| 固件验签 | app-verify：头/容器自洽/COSE 结构级（V1）+ 事实对拍 | manifest_len=133 wasm_len=286 cose_off=435 与本地一致 |
| 激活 | 整槽 hash → meta 原子切换 slot 1 → get-app 确认 | activate confirmed slot=1；DB4 activated → DB5 暖复位 |
| 复位后装载 | 步骤 8 自 flash 装载 + WAMR（PSRAM 池）运行 | DB6 app running app_id=com.tessera.e2e slot=1 |
| 复位后对拍 | Agent get-app：state=ACTIVE(3) + app_id + slot 一致 | DEPLOY PASS（断言全过） |

第二轮复跑（脚本每次 esptool erase_region 从零开始）：DEPLOY PASS + DB6 slot=1 t=10661 + DB PASS ✓。

## 3. 过程留痕（如实，三轮迭代）

1. **prov 手抄数组丢 6 字节**：手写 blob（149B vs 应为 158B）→ 固件确定性解析 fail-closed（load=-8 且烧入"成功"——写通道对坏数据不透明）。定位法 = esptool read_flash 分区 dump + 按固件 schema 走查。修复 = 脚本机械生成 + 生成期走查验证（`~/project/logs/gen_db_prov.py`）。附带发现：netbench 源注释"155B"亦不准（实际 158）。
2. **分区残留态**：换 bench 后首启读到上一 bench 的 prov（load=0 旧身份）——板级流程增 esptool `erase_region 0x170000 0x14000`（ts 五分区；fw_b 不动）。
3. **exports 白名单漂移**（§1-3）：client 打包即被拒，暴露 env 门控测试的漂移掩盖面。
4. **get_info 打回 + active_slot 缺填**（§1-4）：第一轮 DB4/DB5 正常但 DB6 不达——step8 实际成功（wamr pool 行在），观测面读数被打回 STAGED；且 slot 读数 0 ≠ meta 1。第二轮修复后全绿。
5. zenohd 未预启动时板侧 z_open rc=-102 重试 ×6 后自愈（会话退避工作正常）——脚本改为预启动，亦证明 router 后起可自愈。

## 4. 回归

twister **15/15（65 用例）**（slot.c 修复零破坏）/ L5 6/6 / Agent pytest **58 passed, 2 skipped** / SOURCES.lock 同步 OK（LLD 变更两次刷新）/ 真机双轮 DEPLOY+DB PASS。

## 5. 观察项（登记不动手，军规 9）

- **固件侧 COSE 验签 = V1 结构级**（tag18+array4；pkg.c verify_cose_minimal 已知限制）——真 ed25519 验签在 Agent 侧 tsap_verify；固件侧真验签随 TSAP v2/密钥管理批次（LLD-ts-appmgr §7 已知限制清单）。
- 部署会话重启依赖 bench 自动暖复位（激活语义 = STAGED 待加载周期）——"激活即热装载"（不重启切换）留待 appmgr 加载周期批次。
- deploybench prov 经 TS_TEST 烧入（生产通道 = esptool 直写 / Agent push_prov，板级十一候选首位）。
- env 门控测试的漂移掩盖（exports 案例）：建议 gated 测试纳入季度复跑清单（std/testing.md 维护项，登记不动手）。

## 6. 复跑

```bash
# WSL 内（凭证经 db_build.sh cmake 变量注入，不入仓库）：
bash ~/project/logs/db_build.sh   # 构建
bash ~/project/logs/db_e2e.sh     # 擦 ts 分区 → zenohd → 烧录 → 150s console → client.py
# 判据 = 输出含 "DEPLOY PASS" 与 console 含 "DB PASS"
```
