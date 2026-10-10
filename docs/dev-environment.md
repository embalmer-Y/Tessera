# 开发环境记录（dev-environment.md）· 2026-09-21 建立

> **决策依据**：DEC-32（Agent 仅 Linux；开发环境整体迁 WSL2；Windows zephyr 环境复原）、DEC-19（Zephyr v4.4.0 钉版，持续跟进最新 stable）、DEC-24（CI = GitHub Actions，待远端）。
> **本文用途**：开发环境的唯一事实源——目录规范、环境清单、构建方法、教训登记。每次环境变更须更新本文（修改走规范变更流程，见 `docs/std/README.md`）。

## 1. WSL 目录规范（唯一权威布局）

```text
~/project/                       # 开发根（owner 指定，2026-09-21）
  tessera/                       # 本项目仓库（git，主库；自 Windows D:\ 迁入）
  zephyrproject/                 # west 工作区（Zephyr 树 + modules，仓库之外——FOUNDING_PROMPT §4）
    .venv/                       # 固件专用 Python 虚拟环境（不可移动！见 §5 教训）
    build-m0-app/  twister-out/  # 构建产物（不入任何 git 库）
  agent-venv/                    # Agent 专用 venv（MA0 起，DR-19；Python 3.12，依赖钉版见 agent/pyproject.toml）
  logs/                          # 本地构建/测试日志（持久路径；/tmp 是 tmpfs 勿用）
```

- **规则**：仓库与工作区分离；构建产物/日志一律不入库（.gitignore 已覆盖）；`~/project` 下不放假名目录。
- **Windows 侧**：`D:\Software\project\Tessera` 为迁移源快照（**非权威**，owner 确认后可删/存档）；`D:\Software\project\zephyrproject` 已复原 owner 原状（§4）。

## 2. WSL 环境清单（Ubuntu 24.04.1 LTS，32 核）

| 组件 | 版本/位置 | 说明 |
|---|---|---|
| gcc / g++ | 13.3.0（+ **multilib**，native_sim 默认 32 位所需） | apt（清华镜像） |
| cmake / ninja | 3.28.3 / 1.11.1 | apt |
| 其他 apt 包 | gperf、ccache、python3-{pip,setuptools,dev,venv}、git、file、xz-utils | |
| clang / lld | 18.1.3（apt） | 样例 APP 构建（`--target=wasm32` 自由固件，无 WASI——DEC-25） |
| **WAMR 源码** | **WAMR-2.4.5 tag 钉版**，浅克隆 `~/project/deps/wamr`（34MB） | DEC-17 选型 / R1 v0.2 核验版本；仓库不含三方源码（zenoh-pico 同纪律），经 `TS_WAMR_DIR` 注入构建 |
| venv | `~/project/zephyrproject/.venv`，Python 3.12.3 | west 1.5.0 + `scripts/requirements.txt` + `west packages pip --install`（含 **esptool 5.4.0**）+ pytest/gcovr/jsonschema |
| Zephyr 工作区 | v4.4.0 **tag 钉版**（2026-09-26 **官方手册重建**：`west init --mr v4.4.0` + `west update` + `west zephyr-export`；不再自 Windows 拷贝） | DEC-19；重建动因 = 教训 15 根因修复 |
| **Zephyr SDK** | **1.0.1** @ `~/zephyr-sdk-1.0.1`：hosttools + `xtensa-espressif_esp32s3_zephyr-elf`（官方 `west sdk install`，版本自 `zephyr/SDK_VERSION`） | arm 等其他工具链日后按需同法补装 |
| 网络 | apt/pip 清华镜像；GitHub 经 TUN 级代理（WSL 重启自动生效，教训 9） | |

## 3. 构建与测试命令（WSL 内，标准入口）

```bash
cd ~/project/zephyrproject
# 构建（native_sim，DEC-13/14 CI 基线）
.venv/bin/west build -b native_sim ~/project/tessera/firmware/app -d build-m0-app \
  -- -DZEPHYR_EXTRA_MODULES=~/project/tessera/firmware/module/tessera
# twister（运行级测试；tests/ 下用例；M2b.2a 起 WAMR 套件需注入源码根）
export TS_WAMR_DIR=~/project/deps/wamr
.venv/bin/west twister -p native_sim -T ~/project/tessera/firmware/tests \
  --extra-args=ZEPHYR_EXTRA_MODULES=~/project/tessera/firmware/module/tessera
# 样例 APP 产物重建（firmware/tests/wamr/app；源变更后重跑并提交 sample.wasm）
~/project/tessera/firmware/tests/wamr/app/build.sh
# pytest 仓库检查（军规 4 编码）
~/project/zephyrproject/.venv/bin/python -m pytest ~/project/tessera/firmware/tests/pytest -v
# 板级（xiao_esp32s3，2026-09-26 打通）——venv/bin 必须在 PATH（configure 期 cmake 于 PATH 找 esptool）
export TS_WAMR_DIR=~/project/deps/wamr PATH=~/project/zephyrproject/.venv/bin:$PATH
.venv/bin/west build -p always -b xiao_esp32s3/esp32s3/procpu ~/project/tessera/firmware/app \
  -d ~/project/logs/build-xiao3 -- -DZEPHYR_EXTRA_MODULES=$HOME/project/tessera/firmware/module/tessera
.venv/bin/west flash -d ~/project/logs/build-xiao3          # esptool @ /dev/ttyACM0（ESPTOOL_PORT 可显式指定）
~/project/zephyrproject/.venv/bin/python ~/project/logs/console_smoke.py /dev/ttyACM0 12   # console 冒烟（RTS 复位重抓启动全程）
```

**WAMR 接入要点（M2b.2a 实测，零上游补丁）**：① `runtime_lib.cmake` 内部为目录级 `include_directories`——消费方须经 `zephyr_include_directories` 取 `wasm_export.h`；② 三方源码独立库 `tessera_wamr` + `-w`（ems_gc.c 的 `GB` 与 Zephyr util.h 单位宏撞名）；③ `WAMR_BUILD_INVOKE_NATIVE_GENERAL=1`（ia32 汇编缺 `.note.GNU-stack`，被 `--fatal-warnings` 升级为链接错误）；④ `__stdout_hook_install` 兼容垫片（WAMR 平台层引用 Zephyr ≥3.x 已移除 API，`src/appmgr/wamr_compat.c` 空实现满足链接）。

- 注：`-DZEPHYR_EXTRA_MODULES` 的路径含 `~` 时须展开（脚本中用 `$HOME`）；后续按 `docs/std/versioning.md` §4 迁入自管 west manifest 后可省。

### §3.5 Agent 开发命令（MA0 起，DR-19）

```bash
# 初始化（一次性）：独立 venv + 钉版安装（DEC-38 #1；pip 清华镜像）
python3.12 -m venv ~/project/agent-venv
~/project/agent-venv/bin/pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -e "~/project/tessera/agent[dev]"
# lint + 测试（军规 10：交付即验证）
~/project/agent-venv/bin/ruff check ~/project/tessera/agent
~/project/agent-venv/bin/python -m pytest ~/project/tessera/agent/tests -v
```

- agent venv 与固件 venv **互不混用**（依赖面隔离；工具链调用经子进程，LLD-A03 §3）；CI 侧等价 job 见 `.github/workflows/ci.yml` `agent-checks`。

## 4. Windows 侧复原记录（2026-09-21，DEC-32）

| 项 | 动作 | 验证 |
|---|---|---|
| zephyr 检出 | v4.4.0 钉版 → **恢复 main @ 64437be51c3**（owner 原状） | `describe = v4.4.0-16104-g64437be51c3`，工作区 clean ✓ |
| 模块 | `west update` 回 main 钉定（经代理 127.0.0.1:7897） | 0 ERROR ✓ |
| 构建产物 | 清除 build-hello / build-m0-h7 / twister-out*（本会话产生） | ✓ |
| 未动项 | owner 的 `.venv`（Python 3.12.13）、SDK 1.0.1（`C:/Users/y1985/zephyr-sdk-1.0.1`） | 原样保留 |

## 5. 教训登记（环境类，避免复犯）

1. **venv 不可重定位**：venv 内脚本的 shebang 是绝对路径，目录移动后失效——目录定型（§1）后再建 venv；移动目录须重建。
2. **native_sim 默认 32 位**：需 `gcc-multilib`（仅 build-essential 会报 `bits/libc-header-start.h` 缺失）；64 位变体 `native_sim/native/64` 无此需求。
3. **WSL /tmp 是 tmpfs**：VM 重启即清——日志一律写 `~/project/logs`。
4. **west update 网络失败先查代理**：本机 GitHub 需代理 127.0.0.1:7897（owner 提供）；apt/pip 用国内镜像免代理。
5. **bash 不展开 `=` 后的 `~`**：`--extra-args=ZEPHYR_EXTRA_MODULES=~/...` 会把字面 `~` 传给 CMake（报 not a valid zephyr module）——一律用绝对路径或 `$HOME`。
6. **库源码"缺失实现"断言必须穷尽子目录再下结论**：曾以 `grep -rln pthread_attr_setstack zephyr/lib/posix/*.c`（顶层）误断 Zephyr 无实现，打了不必要的补丁——实现在 `lib/posix/options/pthread.c`。结论前用 `git grep`（全树）复核；对第三方库的每个补丁先做撤销实验（revert→重建→复测）确认必要性。
7. **Windows SDK 经 /mnt 互通掩盖工具链变体问题（2026-09-25，CI 三轮排障真因）**：WSL 会把 Windows 的 `ZEPHYR_SDK_INSTALL_DIR` 翻译成 `/mnt/c/...`——`ZEPHYR_TOOLCHAIN_VARIANT` 未设时 Zephyr 探测 SDK"成功"（实际编译器仍是 host gcc），本地全绿；干净环境（CI runner）同路径直接致命。**native_sim 主机工具链构建一律显式 `ZEPHYR_TOOLCHAIN_VARIANT=host`**（CI 已设；本地亦推荐）。
8. **GitHub Actions 日志 API 需 admin 权限，public 仓库注解（annotations）API 免鉴权可读**：CI 内建"失败时把 CMake Error 首块注入 `::error::` 注解"（ci.yml，常设设施）——无 gh CLI/token 时的调试通路。
9. **代理新模式（2026-09-25 起）**：owner 开启 TUN 级代理后，`wsl --shutdown` 重启即自动生效，WSL 内无需任何代理配置（教训 4 的 127.0.0.1:7897 手动配置不再是必需路径）。
10. **native_sim SMP 需显式 USE_SWITCH（2026-09-26，wamrdemo 实证批）**：`CONFIG_SMP=y` 在 posix 架构下因缺 USE_SWITCH **静默失效**（Kconfig 告警被忽略时）——多核实验须同时开 `CONFIG_USE_SWITCH=y` + `CONFIG_MP_MAX_NUM_CPUS`，并以 autoconf.h 实际值为准复核。
11. **native_sim 忙循环冻结模拟时钟**：Zephyr 线程忙等期间 hw timer 模型不推进（模拟时间停摆、宿主墙钟照走）——时序测量必须用宿主墙钟（minimal-libc time.h 不声明 clock_gettime，native_sim 进程链接宿主 libc，显式 extern 声明可用，仅测试代码）；"忙线程 + 定时器并发"类行为在 native_sim 上不可忠实模拟，留板级验证。
12. **WAMR Zephyr 平台模块生命周期怪癖（2026-09-26，接线批排障双复现）**：同进程内 `wasm_runtime_load→unload→再 load`（相同字节流）与 `init→destroy→再 init→load` 均失败（解析错"unexpected end of section"）——规避 = **模块进程级复用**（runtime.c mod_cache：同字节流复用、不 unload、换包需重启）；升级 WAMR 后先撤实验验证。
13. **板卡 USB 进 WSL（xiao_esp32s3，2026-09-26 打通）**：Windows 侧 `usbipd bind --busid 7-4`（管理员，UAC）→ 保持 WSL 存活 → `usbipd attach --wsl --busid 7-4` → `/dev/ttyACM0`（emb 已在 dialout 组，可直接读写）。注意 attach 需 WSL 发行版在运行；Windows 侧 COM 口同时消失（用完 `usbipd detach` 归还）。**`wsl --shutdown` 后 usbipd 状态残留 "Attached" 但内核未绑定**——须先 `detach` 再 `attach`（2026-09-26 环境重建实证）。
14. **ESP32-S3 工具链勘误（2026-09-26 板级批实证）**：早前"ESP32 不需要 Zephyr SDK"**有误**——Zephyr 4.4 的 ESP32 系列交叉工具链 = **Zephyr SDK 的 xtensa-espressif_\* 系列**（`west espressif` 扩展仅有 monitor 子命令，无 install）。~~构建时显式 `ZEPHYR_SDK_INSTALL_DIR` 防 /mnt 污染~~ → 教训 15 已除根，SDK 发现链干净后**无需**显式指定（保持默认自动发现）。
15. **Windows PATH 泄漏劫持 SDK 发现链——根因定论（2026-09-26，owner 指令官方重建时钉死）**：WSL 默认把 Windows PATH 追加进 Linux PATH（interop）；CMake `find_package(Zephyr-sdk)` 把 PATH 条目的父目录当搜索前缀并按 `<前缀>/zephyr-sdk*/cmake/Zephyr-sdkConfig.cmake` 通配匹配，`/mnt/c`（drvfs）**大小写不敏感**，故 `/mnt/c/Users/y1985/bin` → 前缀 `/mnt/c/Users/y1985` → 命中 Windows 侧 SDK。此通道**同时**劫持 cmake 构建与 `west sdk list/install`（后者经 `listsdk.cmake` 走同一 find_package）。**修复 = `/etc/wsl.conf` 追加 `[interop]\nappendWindowsPath=false` + `wsl --shutdown`**；代价 = WSL 内不能再直接调 Windows exe（本项目无此需求）。教训 7 的"ZEPHYR_SDK_INSTALL_DIR 翻译"机制描述不完整，以本条为准。
16. **SDK 官方安装三要点（2026-09-26）**：① `west sdk install -t` 的工具链名用**全名**（`xtensa-espressif_esp32s3_zephyr-elf`，报错时它会列出全部合法名）；② `west sdk` 是 zephyr 侧扩展命令，依赖 `scripts/requirements.txt`——**先 pip 装依赖再跑 sdk install**，否则扩展导入失败且 west 以内部 AttributeError 掩盖真实错误；③ esptool 由 `west packages pip --install` 官方提供——构建与烧录须把 `.venv/bin` 前置 PATH（configure 期 cmake 在 PATH 找 esptool，缺失直接 configure 失败）。
17. **板级 bring-up 三坑（2026-09-26，xiao_esp32s3）**：① RAM slot 替身（store/part.c）默认双 256KB = 512KB，ESP32-S3 的 dram0_0_seg 装不下（溢出 251KB）——板级片段 `firmware/app/boards/xiao_esp32s3_esp32s3_procpu.conf` 按 DEC-23/DEC-27 收紧（slot 32KB、宿主栈 16KB；PSRAM 挂接待板级任务）；② 改 `boards/` 片段后**必须 `-p always`**——`-p auto` 在同板同源 build 目录不触发 pristine，CONF_FILE 沿用缓存、新片段静默不生效（本次多耗两轮构建）；③ esp32s3 默认 **picolibc**，其 stdio.c 自带 `__stdout_hook_install`，与 WAMR 垫片撞多重定义——垫片加 `#if !defined(CONFIG_PICOLIBC)` 守卫（native_sim minimal-libc 路径不变）。
18. **WAMR XTENSA 陷出必须用官方汇编（2026-09-26 板级二）**：`invokeNative_general.c`（C 版）在 xtensa 上传参不可靠（WAMR cmake 注释自认；native_sim/x86 可用是平台假象）——XTENSA 目标用 `invokeNative_xtensa.s` + `-Wa,--noexecstack`（汇编期补 .note.GNU-stack，否则 Zephyr --fatal-warnings 链接失败）。模块 CMakeLists 已按板分派。
19. **esp32s3 计时源与描述符约束（2026-09-26 板级二实证）**：① `k_cycle_get_64` 本板**冻结**（75ms 忙等 delta=0，uptime 正常；根因未深究，上游跟踪项）——板级周期计时用 **CCOUNT**（`rsr.ccount`，240MHz 直接驱动；32 位 ~17.8s 回绕，差值即时计算回绕安全）；② `ts_safety_register_channel` 存描述符**指针**——描述符须 file-scope 持久对象（栈上复用单对象 = 全表别名 → 全 NOTFOUND；native_sim 测试的 static 惯例掩盖该约束）；③ wsl bash 管道输出中文可能显示为 GBK 伪乱码——**判文件编码一律用 Read 工具直读，勿信管道显示**。
20. **Zephyr 4.4 DT 用户节点 API 陷阱（2026-09-27 板级三实证）**：① **`ZEPHYR_USER_NODE` 是 4.5 API，4.4 无此宏**——4.4 用 `DT_PATH(zephyr_user)`；读 /latest/ 文档时注意版本差；② 未定义宏进了 DT 包装宏（DT_PROP/GPIO_DT_SPEC_GET/DT_NODE_HAS_PROP）会被**字面 token 拼接**，产生"宏不可见/守卫恒假/undeclared 后缀符号"连环假象——遇此类怪象先确认节点宏本身存在；③ DT 的 gpios 单元只认 dt-bindings 宏（`GPIO_ACTIVE_HIGH` 等，`#include <zephyr/dt-bindings/gpio/gpio.h>`——注意双层 gpio 目录）；`GPIO_OUTPUT_LOW/HIGH` 是**运行时 API 旗标**，不属于 DT。
21. **板级 WiFi + zenoh 五要点（2026-09-27 板级四实证，docs/netbench-01.md）**：① esp32s3 WiFi 可用但需 `west blobs fetch hal_espressif`（预编译 blob，git 检出默认无）+ overlay 使能 `&wifi`（SoC dtsi 默认 disabled）；驱动选 mbedTLS/PSA、要求非 SMP；② **WiFi 省电必须关**（默认 modem-sleep 对齐信标 → 命令往返 p50 66ms/max≈105ms≈DTIM；`NET_REQUEST_WIFI_PS` + `WIFI_PS_DISABLED` 后 p50 12ms）；③ WSL mirrored 网络 LAN 入站须 Hyper-V 防火墙放行（`Set-NetFirewallHyperVVMSetting -DefaultInboundAction Allow`，owner UAC 一次）——且 Windows 本机测自身 LAN IP 走 loopback 不可作判据，须设备实测；④ zenoh-pico 1.10.1 回调签名非 const（`z_loaned_query_t*` 即 `_z_query_rc_t` 直名）——const 即不兼容指针错误；⑤ WAMR version.cmake 把 version.h 写进共享源码树——**三次咬人后的真除根（2026-10-04 MD0-1 批：预生成 + chmod 444 只读屏障）**：板级八的"串行预生成"不除根（CI 冷树 1/15 卡死第三次复发 + 本地冷树复刻 8/15 报 configure_file No such file or directory；单套件绿、并行炸 = 同内容 configure_file 在共享输出路径仍有临时文件写删，15 并发竞争撕裂）；真除根 = 预生成后 chmod 444（强制全进程走"比较相同→零写"路径；本地冷树 15/15 实证）。再生 version.h 须先 chmod 644。前两次处置（单套件重跑即绿 / 仅串行预生成）均作废。；⑥ **含反引号的文本严禁经 bash heredoc 落盘**（本条即事故：命令替换吃掉代码段——一律 Write/Edit 工具直写）。
22. **板级 flash 持久化六要点（2026-09-28 板级五实证，docs/board-persist-01.md）**：① espressif 板分区表由 `dts/vendor/espressif/partitions_0x0_amp_*.dtsi` 自动注入（boot/sys/slot0/slot1/appcpu/lpcore/storage）——自定义分区用 overlay 顶层 `/delete-node/ &slot1_partition;` 腾空闲区再新增（boot/sys/slot0 不动 = esptool 偏移零变化）；② **`FIXED_PARTITION_*` 宏 v4.4 已弃用**——现行 = `PARTITION_ID/SIZE/OFFSET/EXISTS`（flash_map.h；twister -Werror 拦截而手工构建可能假阴性）；③ `flash_get_write_block_size` 为 syscall 封装、非 userspace 构建链接不可用——写对齐垫片固定 4B 字粒度（4 对齐蕴含更小对齐；esp32s3 DT write-block-size=4）；④ sim-flash `EXPLICIT_ERASE`（默认 y）= **程序一次**语义（比真机严格）：同值重写/部分编程字扩展写在真机合法、sim 拒绝——prov 头+CBOR 分两次写即被其拦（改一体单次连续写）；⑤ `K_THREAD_DEFINE` 的 delay 形参是 int32 毫秒（传 `K_SECONDS()` k_timeout_t 即编译错）；`sys_reboot` 头 = `zephyr/sys/reboot.h`（非 zephyr/reboot.h）；⑥ 观测首启烧录会话：esptool 抹除加 `--after no_reset`，由抓取脚本的 RTS 复位触发——否则 esptool 自带硬复位抢跑、会话在观测窗口外完成（症状：抓到的"首启"其实是第二轮）。
23. **板级 PSRAM 挂接五要点（2026-10-01 板级六实证，docs/board-psram-01.md）**：① esp32s3 PSRAM = `CONFIG_ESP_SPIRAM`（select SHARED_MULTI_HEAP）+ DT `psram0`（common.dtsi 已有，N8R8 模组 dtsi 定 8MB）——**N8R8 八线必须显式 `SPIRAM_MODE_OCT=y`**（默认 QUAD → esp_init_psram 探测失败硬停）；② 分配走官方共享多堆：`shared_multi_heap_alloc(SMH_REG_ATTR_EXTERNAL, n)`（soc.c 自动 init + 注册；`ESP_SPIRAM_HEAP_SIZE`〔默认 1MB〕= SMH 区域上限）；③ WAMR-2.4.5 的 `WASM_ENABLE_GLOBAL_HEAP_POOL` 旗标**无消费者**——`wasm_runtime_init()` 实为系统分配器；真池模式 = `wasm_runtime_full_init(Alloc_With_Pool, pool.heap_buf=注入缓冲)`（零补丁注入面）；④ 池模式下 WAMR 堆须 ≥ 线性内存页（64KB/页）+ 模块实例/执行环境——64KB "基线"结构性不可行（twister 拦截：allocate linear memory failed）；⑤ 地址域即位置证据：PSRAM 映射 0x3c000000 起（内部 SRAM = 0x3fc8xxxx/0x40xxxxxx），console 打印池指针即可判外置与否。
24. **WiFi 断链重连四要点（2026-10-01 板级七实证，docs/board-reconnect-01.md）**：① **net_mgmt 事件回调内禁调 net_mgmt**——PS/DHCP 请求在回调上下文重入自激（connect/ADDR 事件每 ~40ms 风暴）；纪律 = 回调只置标志 + `k_work_submit`，请求一律工作项上下文；② esp32 WiFi 口断线**不清 IPv4 地址/租约**——重连同址无 ADDR_ADD 事件；断线时显式 `net_dhcpv4_restart`（注意 include 顺序：dhcpv4.h 须在 net_if.h 后，参数表内 struct net_if 可见性）；③ 静默掉线 = **僵尸 TCP 半开**：net_if 仍 up、读任务阻塞 recv、zenoh 租期心跳在本地 TCP 缓冲"成功"——is_up 自省分钟级才收敛；承载事件须显式下沉（ts_net_session_media_down）；④ **阻塞传输操作不得上 sysworkq**（zenoh open/close 死链上十余秒，饿死同队列工作真机实证）——ts-net 周期体专用队列（DEC-43 线程序）；WiFi 驱动无自动重连（Zephyr esp32 口），关联维持 = glue 职责（固定周期重试，无抖动）。
25. **estop 绑定与自动注入三要点（2026-10-01 板级八实证，docs/board-estop-01.md）**：① **v4.4 EDT 管道不发射非 zephyr 前缀 chosen 宏**（dtlib 层属性在、edtlib 层被弃——devicetree_generated.h 缺 `DT_CHOSEN_x`；诊断法：dtlib 直读 dts vs edt.pickle 对比）——自定义 chosen 一律改 **aliases**（`DT_ALIAS(name)`；注意 overlay 语法为 `name = &label;` 直接引用，尖括号 phandle 会被 dts 校验拒绝）；② 无人工按键的硬件路径自动注入：io_mux 输入+输出双使能 + 翻转 GPIO 输出寄存器（esp32s3 GPIO0 bank @0x60004000：ENABLE_W1TS/W1TC + OUT_W1TS/W1TC）→ 引脚电平真实变化 → 中断完整链路（bench 测试注入，产品唯一写路径不变）；③ estop 通道观测设计：三态 fault=true（poweron/linkloss 均 false）——readback false→true 的唯一来源即 fault 直写，判据无歧义。

26. **LEDC/ADC 板级驱动四要点（2026-10-02 板级九实证，docs/board-periph-01.md）**：① **LEDC duty 寄存器字段 = duty ticks << 4**（hal `ledc_ll_set_duty_int_part`：`hw->duty = duty_val << 4`；reg 头部位域注释 [18:0] 有误导，有效位 [18:4]）——硬件比值判据 = DUTY_R/(2^duty_res×16)；② **zephyr,user 支持任意属性含 phandle-array**（`pwms`/`io-channels` 均可；`ADC_DT_SPEC_GET_BY_NAME(DT_PATH(zephyr_user), …)` 即官方文档示例模式）——真机后端绑定统一走 zephyr,user（uid 串 + 资源 spec）；③ LEDC 引脚路由经 **pinctrl**（`LEDC_CHx_GPIOy` 宏 = zephyr `include/zephyr/dt-bindings/pinctrl/esp32s3-pinctrl.h`，非 hal 树）+ channel 子节点（reg/timer），pwms 规格 cell 不含引脚；④ **Kconfig 块嵌套漂移**：TS_POWER/TS_PERIPH 曾误嵌 `if TS_NET`（TS_NET=n 时符号不可见）——新增"某模块默认 y 却消失"症状时先查块结构（Kconfig 无缩进语义，endif 位置即作用域）。

27. **手抄二进制数组禁令 + 板 bench 分区残留态（2026-10-02 板级十实证，docs/board-deploy-01.md）**：① **常量字节数组（prov blob 等）禁手抄改写**——丢字节后写通道"成功"返回但确定性解析 fail-closed（症状 = 烧入 OK + 永远 load 失败）；正确做法 = 脚本机械派生（源数组改字节）+ **生成期按消费方 schema 走查验证**（~/project/logs/gen_db_prov.py 模式）；定位法 = esptool read_flash 分区 dump + 独立解析器走查；② **换 bench 后 flash ts 分区残留上一 bench 的 prov/meta**（load=0 旧身份即沿旧身份上线）——板级流程须先 esptool erase_region 0x170000 0x14000（ts 五分区；fw_b 预留不动）；③ env 门控测试（默认 skip）掩盖跨轨漂移（exports 命名案例）——gated 测试须周期性真跑。

28. **WAMR 进程内二次 boot_start 怪癖（2026-10-09 单元 H test_08 排障实证，隔离复现 + 控制变量五组）**：同一进程内 `ts_appmgr_boot_start` 第二次调用产出的实例**导出查找恒空**（`wasm_runtime_lookup_function` 对 health_ping/app_init 全 NULL → E_PARAM），与字节内容/指针/缓存命中无关（wasm 逐字节相同、mod_cache 命中、模块对象不变）；stop 后**直调** `ts_appmgr_app_start`（同模块重启）**不受影响**——判别律 =「进程内第二个 boot_start 必坏，直调免疫」。**怪癖面 = native_sim（X86_32）实证；ESP32-S3（XTENSA）反证在先**——inputdemo（单元 F，2026-10-08）D4 经 ts_core_boot 装载后、D6 阶段同进程第二次 `ts_appmgr_boot_start` 真机装载运行成功（D6-DONE 实证）——怪癖按平台/条件未定，native_sim 侧规避如旧。生产无暴露面（boot_start 每进程恰一次；重载 = 暖复位，persistbench PB4/PB5 链）；测试规避 = activate 语义经直调启动考察（tests/app test_08 注记）。教训 12 怪癖家族第三型；升级 WAMR 后撤实验验证。

29. **ESP32-S3 LEDC 判据三要点（2026-10-09 单元 I / D9 板上实证）**：① **duty 0%（与 100%）走 STOP 特例路径**——Zephyr `pwm_led_esp32`（pwm_led_esp32.c L339）不更新 DUTY 寄存器而是 SIG_OUT_EN=0 + IDLE_LV 直接输出（0% = 恒低）——**DUTY_R 读回判据仅在运行态有效**，0% 判据 = CONF0.SIG_OUT_EN==0 且 IDLE_LV==0（硬件确在 0%，寄存器视角不同）；② **S3 位序/偏移与初代 ESP32 不同**：LSCH0_CONF0@0x0000（HPOINT@0x4 / CONF1@0xC / DUTY_R@0x10），SIG_OUT_EN=BIT(2)、IDLE_LV=BIT(3)——**位定义一律查 `components/soc/esp32s3/register/soc/ledc_reg.h`，勿凭初代记忆**；③ 数值日志含 0 的 APP 代码生成（LLM）约束须显式「0 输出字符 '0'」+「单次 log 完整行」——两轮实证缺省生成的手写转换丢 0 值/只写前缀。

### 2.x 工具链增补（2026-10-02，H7 内存评估批）

- SDK 1.0.1 增装 **arm-zephyr-eabi**（命令 west sdk install -b ~/zephyr-sdk-1.0.1 -t arm-zephyr-eabi，需网络/VPN）——nucleo_h743zi 网面实构建已验证（docs/h7-memory-assessment.md）。

### 2.y Agent LLM 端点（2026-10-04，MD0-1 冒烟批）

- 端点 = minimax Anthropic 兼容面：环境变量 ANTHROPIC_BASE_URL=https://api.minimax.cn/anthropic 与 ANTHROPIC_API_KEY（密钥文件 = 仓外 ~/project/logs/.minimax_key，600 权限，运行器脚本注入）；模型 MiniMax-M3（思考型——pydantic-ai 侧必须显式 max_tokens，SDK 缺省会被思考段耗尽）；上下文 1M（agent/config.toml 的 context_window=1048576）。
- 复跑：bash ~/project/logs/run_smoke1.sh（结构化输出管道）/ run_smoke2.sh（app_develop 全链，产物在 ~/project/logs/llm-smoke-out/）。

### 2.z Agent 测试 clang 硬依赖（2026-10-04，G1/DEC-45 批）

- agent/tests 的 wasm_build 面测试硬依赖宿主 clang（M2b.2a 起在位，/usr/bin/clang 18）；**无静默 skip**（板级十教训）——缺 clang = 响亮失败。CI agent-checks 显式保障步骤已加。app_compile 编译 flags 与 firmware/tests/app/appw/build.sh 同款（自由固件惯例）。

## 6. 会话规范（此后所有开发会话）

- 开发在 **WSL Ubuntu** 内进行；仓库 = `~/project/tessera`（bootstrap 流程不变，见 AGENTS.md §2）。
- Windows 端仅保留浏览器/编辑/交流；不在 Windows 侧跑构建。

## 7. zenoh-pico 工作区接入（M3a.1 起，钉版 1.10.1——DR-22 三方同 minor）

1. 拉取：`git clone --depth 1 --branch 1.10.1 https://github.com/eclipse-zenoh/zenoh-pico.git ~/project/zephyrproject/zenoh-pico`（需代理 127.0.0.1:7897）。
2. 生成 config.h（**上游 Zephyr 模块缺口**：其 zephyr/CMakeLists.txt 不执行 configure_file，直接编译报 `zenoh-pico/config.h` 缺失）：
   - `cmake -S ~/project/zephyrproject/zenoh-pico -B <tmpdir>` 生成 `<tmpdir>/include/zenoh-pico/config.h`
   - 剥离 feature 宏区后落位（feature 宏由 Kconfig→zephyr_compile_definitions 供给，避免重定义）：`sed '/^#define Z_FEATURE_/d; /^#cmakedefine Z_FEATURE_/d' <tmpdir>/include/zenoh-pico/config.h > ~/project/zephyrproject/zenoh-pico/include/zenoh-pico/config.h`
3. 构建接线：`-DZEPHYR_EXTRA_MODULES="<tessera module>;<zenoh-pico>"` + `firmware/tests/net/overlay-zenoh.conf`（EXTRA_CONF_FILE）。**关键项 `CONFIG_POSIX_API=y`**——zenoh-pico Zephyr 平台层直引 `<netdb.h>/<sys/socket.h>`，host libc 下与 Zephyr net_ip.h 结构冲突，必须经 POSIX API 解析。
4. **源码补丁：无（2026-09-23 复核定稿）**。checkout 对上游保持零修改，唯一非上游文件 = `include/zenoh-pico/config.h`（**生成件**，§7-2 产物；其 Zephyr 模块集成缺口只是"不执行生成步骤"，非源码缺陷）。此前登记过的两处补丁（primitives.c 笔误 / system.c setstacksize）经撤销实验证明均非必要——当时的 EINVAL 真因是 §8 的配置链（DNS_RESOLVER/pthread 动态栈/POSIX 池），setstacksize 补丁属误诊（教训见 §5-6）。已知无害上游笔误备忘：`_z_undeclare_queryable` 的 `#else` 分支 `sub->_zn` 应为 `qle->_zn`（仅 Z_FEATURE_SESSION_CHECK=0 时编译到；cmake 缺省=1 不触发——升级换配置时留意）。
5. 升级纪律：三方（zenohd router / eclipse-zenoh Python / zenoh-pico）联合升级 + 全量回归（DR-22；Zenoh 2.0 watch）。

## 8. L3 端到端联调（已达成 2026-09-23；复跑方法）

**结果：PASS（2026-09-23 复跑，DEC-40/41/42 批扩展为五验证点）**：① 发现〔hb+telemetry 到达，遥测信封 ver=1/kind=96〕/ ② 命令-回执〔v1 共存 + v2 rid 回带 kind=16；estop-clear 错令牌=TS_E_PARAM〕/ ③ 幂等〔同 idem 回放原回执不重执行；to=6000 拒绝〕/ ④ 租约全生命周期〔续期同 id；他人获取/代还=TS_E_STATE(-4) 归因回填；本人归还 OK〕/ ⑤ 心跳保持与断链判定〔hb-host 持续→link_up+通道 ACTIVE；停发 10s>6 周期→link_up=0+通道 SAFE_LINKLOSS；迁移事件信封 kind=37〕。

复跑步骤：
1. TAP（每次 WSL 重启后，需 sudo）：`sudo ip tuntap add dev zeth mode tap user emb && sudo ip link set zeth up && sudo ip addr add 192.0.2.2/24 dev zeth`
2. router：`(setsid nohup ~/project/tools/zenohd --listen tcp/0.0.0.0:7447 > ~/project/logs/zenohd.log 2>&1 < /dev/null &)`（zenohd v1.10.1 已装 `~/project/tools/`）
3. 固件：`west build -p -b native_sim firmware/l3app -d <build> -- -DZEPHYR_EXTRA_MODULES="<tessera module>;<zenoh-pico>"` 后运行 `<build>/zephyr/zephyr.exe --eth-if=zeth`
4. 客户端：`~/project/agent-venv/bin/python firmware/l3app/l3_client.py`（输出 JSON，result=PASS；退出码 0）

**Zephyr 4.4 + zenoh-pico 联调要点（踩坑留痕，均已在 l3app/prj.conf 注释）**：
- 以太驱动 `ETH_NATIVE_POSIX` 已更名 `ETH_NATIVE_TAP`；native_sim 运行参数为 `--eth-if=zeth`（非 `--tap`）。
- `CONFIG_DNS_RESOLVER=y`——zenoh-pico Zephyr 平台 TCP 解析走 getaddrinfo（数字地址亦经解析器，缺则连接前即败）。
- **pthread 动态栈依赖链**：`THREAD_STACK_INFO` → `DYNAMIC_THREAD` → `DYNAMIC_THREAD_ALLOC`（缺 THREAD_STACK_INFO 则 DYNAMIC_THREAD 被静默丢弃 → pthread_create 恒 EINVAL）；默认动态栈 1024 过小 → `DYNAMIC_THREAD_STACK_SIZE=8192`。
- **POSIX 对象静态池**：`MAX_PTHREAD_MUTEX_COUNT`/`MAX_PTHREAD_COND_COUNT` 默认 5——zenoh 会话互斥量即超限（ENOMEM→连锁 EINVAL）；提至 16；`POSIX_THREAD_THREADS_MAX` 5→8。
- zenoh 会话堆：官方例程档位以上（实测 192K）。
- **TAP 重建失效教训（2026-09-25）**：zeth 删除重建后为**新设备**——已运行固件的附着 fd 指向旧设备，连接恒 -102；重建 TAP 后须重启固件进程。WSL 网络栈刷新可能静默删除 zeth（含 IP），复跑前先 `ip addr show zeth` 核验。
- Agent 部署 E2E 入口：`TESSERA_E2E_DEPLOY=1 ~/project/agent-venv/bin/python -m pytest agent/tests/test_deploy_e2e.py`（自建固件至 agent/build/deploy-e2e；需 TAP 在位 + zenohd 端口可拉起）。

30. **Zephyr 4.4→4.5 升级批三教训（2026-10-10，DEC-50）**：① west update 后**必须 west blobs fetch hal_espressif**——4.5 起 espressif HAL 二进制库（bt/wifi blob）以 west blobs 管理，不随 update 拉取；缺失 = CMake「Blob isn't valid」且网络经代理较慢（开代理后重启 WSL 生效）；② **esp32 分区节点必须显式 compatible = "zephyr,mapped-partition"**（4.5 新绑定——无此串则 PARTITION_ID 宏不生成 = flash_map 取不到分区）；默认分区布局新增 appcpu/lpcore 分区（0x2C0000 起）与 ts 五分区重叠——overlay 须 /delete-node/ 清冲突；③ **WAMR 平台头裸 include autoconf.h**（4.5 移除 legacy 生成头路径）——模块 CMake 以 ZEPHYR_BINARY_DIR/include/generated/zephyr 补包含域（仓库内修复，CI 可复现，零上游补丁）。

31. **P4 适配批六教训（2026-10-10，board-p4-01）**：① **v4.5 板目标斜杠限定语法**——AMP/多变体板（如 esp32p4_wifi6_dev_kit）的有效 target = `板/soc/变体`（`esp32p4_wifi6_dev_kit/esp32p4/hpcore`）；`板_变体` 连写名报 No board named，`板@变体` 报 Invalid revision，错误信息会直接列出全部有效 target；② **SDK 单工具链补装**——`~/zephyr-sdk-1.0.1/setup.sh -t riscv64-zephyr-elf`（经代理，~148MB tarball），不必重下全量 SDK；③ **Waveshare P4 板 console 默认走原生 USB-Serial-JTAG**（需另接 USB 口）——单线判据用 overlay 把 chosen console/shell-uart 重指 uart0（CH343 COM 口实测 = UART0，与 esptool 下载模式同口）；④ **WSL 空闲关机清 /tmp**——跨 wsl.exe 调用的临时文件须放持久位置（~/project/logs）；首启串口观测有竞速窗口：esptool erase 尾部硬复位即启动首启流程，抓取脚本须"擦除（子进程）→立即重开串口"编排（p4_firstboot.py 模式）；⑤ **RV32 调用帧比 Xtensa 深**——S3 过关的 4096 main 栈在 P4 安装链溢出（sp 越栈底 0x230，Illegal instruction @ bss 数据表内——mepc 落数据区 = 栈溢出回跳的典型指纹），P4 板 conf 定 8192；⑥ **twister 两条老坑新咬**：必须带 `--extra-args=ZEPHYR_EXTRA_MODULES=...`（否则 tessera Kconfig 全部 undefined symbol → 8 套件构建失败）；且 bash 管道 `twister | tail` 吃掉退出码（PIPESTATUS 才是真码）——tail 退出 0 = 假绿。

32. **P4 无线面批五教训（2026-10-10，P4+C6 esp-hosted bring-up）**：① **owner Windows EIM 环境**——IDF 多版本框架在 D 盘（D:/App/ESP/idf/.espressif/ 下 v5.2.7/v5.4.4/v6.1），但**工具区与 python venv 在 C:/Espressif/tools**（EIM 布局：IDF_TOOLS_PATH=C:/Espressif/tools、IDF_PYTHON_ENV_PATH=C:/Espressif/tools/python/v6.1/venv——出处 = C:/Espressif/tools/Microsoft.v6.1.PowerShell_profile.ps1）；EIM core 特性缺 dfu-util/esp-rom-elfs/esp-clangd 时以 idf_tools.py install 从 C:/Espressif/dist 离线缓存补齐；bat 调 export.bat 须先 set MSYSTEM= 置空（Git Bash 继承的 MSYSTEM 触发其 shell 检测拒绝）。② **esp-hosted-mcu 仓库目录名必须为 esp_hosted**（IDF 组件名解析按目录名，README 有注）——cp 工程构建产物在 examples/wifi/sta/cp/build；C6 实测 = ESP32-C6FH8 内嵌 8MB flash（烧录 4MB 参数兼容）。③ **C6 SDIO datapath 三态**：SW_AGGR（rel-3 默认，须 host 发 buf-config TLV 协商——Zephyr 驱动不发）/ STREAM（IDF 硬件批流 = 传统每帧带头字节流——恰为 Zephyr esp_hosted 驱动的语义）/ PACKET（v3.0.9 源码内 #error 死代码不可构建）——**cp 侧定值 STREAM**（sdkconfig.defaults.esp32c6 追加 CONFIG_EH_TRANSPORT_CP_SDIO_MODE_STREAM=y）。④ **C6 烧录顺序铁律**：C6 下载模式是持续等待态——先 IO9 接 GND + 按 RST（owner 操作），后跑 esptool（CH340 @ COM9 三线 TX/RX/GND 即可）；无 DTR/RTS 线时 esptool default-reset 不会无限等目标。⑤ **Zephyr esp_hosted 数据面缺陷定案**：STREAM 下 RPC 控制帧全通（版本握手 coprocessor firmware v3.0.9 ✓、wifi_connect rc=0 ✓、associated 3/3 复现；C6 侧日志确认收到 host RPC 并执行 WiFi 连接成功、事件回传到 host）但 **UDP/TCP 数据帧基本不通**（DHCP 3/3 挂、唯一过 DHCP 一例 zenoh TCP 亦挂）——Zephyr 4.5 esp_hosted 驱动（Arduino 贡献的新驱动）RX 数据帧/大帧路径成熟度问题，上游缺陷域（呈递候选：Zephyr upstream issue）。


29.5（并入 29 同族补充）**zenoh 长会话网络面三教训（2026-10-09 B2 批实证）**：① **zenoh 1.10.1 locator 正式语法 = tcp/host:port**——旧式 tcp://host:port 在 zenoh-py 解析为协议 "tcp:" → 会话开失败（"Unicast not supported"）且表现为间歇（ZenohService 已中心归一化）；② **Reply API = ok/err/replier_id**（无 err_payload——旧代码错误回执路径一踩即 AttributeError，且异常中断 get 迭代后会话残留未消费状态，后续调用挂起 =「查询面停滞」假象）；③ **暖复位后路由器残留陈旧 queryable 声明**（板侧 TCP 经 WSL mirrored NAT，复位后 RST 不达路由器→死 peer 声明滞留）——通配发现查询被每个死 peer 拖 3s 超时可致整体超时；已知 node/cube 时用点对点直查绕过，或重启 zenohd 清台。

## 修订记录
- v2.18 · 2026-10-10：P4 无线面批——§5 增教训 32（owner EIM 环境布局/esp_hosted 目录名/SDIO datapath 三态定值 STREAM/C6 烧录顺序铁律/Zephyr esp_hosted 数据面缺陷定案——RPC 通而数据帧挂，上游域）。
- v2.17 · 2026-10-10：P4 适配批——§5 增教训 31（板目标斜杠语法/SDK 单工具链补装/console 重指 uart0//tmp 竞速/RV32 main 栈 8192/twister EXTRA_MODULES 与管道假绿）；docs/board-p4-01.md（P4 bring-up 报告：p4bench 真机全链 PASS）。
- v2.16 · 2026-10-10：**DEC-50 升级批——工作区钉版 Zephyr v4.4.0 → v4.5.0-rc1**（owner 裁决直接采用 rc1）。§5 增教训 30（升级批三件事：west blobs fetch hal_espressif 必做〔blob 不随 west update 拉取〕/分区节点须 compatible="zephyr,mapped-partition" + 默认布局 appcpu/lpcore 分区冲突删除/WAMR 裸 include <autoconf.h> 经新路径补包含域）。
- v2.15 · 2026-10-09：B2 批——§5 增教训 29.5（zenoh locator/Reply API/陈旧声明三教训）；「查询面停滞」根因定论 = agent 侧双缺陷（板与路由器无责）。

- v2.14 · 2026-10-09：单元 I（MD2-D8/D9）——§5 增教训 29（LEDC 0% 特例路径/S3 位序/LLM 零值约束）。
- v2.13 · 2026-10-09：单元 H（G4/G5）——§5 增教训 28（WAMR 进程内二次 boot_start 怪癖——判别律/规避/生产无暴露面定论）。
- v2.12 · 2026-10-04：G1 批——§2 增 agent 测试 clang 硬依赖注记；agent-codegen-reliability-01 报告。
- v2.11 · 2026-10-04：MD0-1 真实 LLM 冒烟——§2 增 Agent LLM 端点（minimax/anthropic 兼容/M3/1M 窗口 + 密钥纪律 + 复跑入口）；agent-llm-smoke-01 报告。
- v2.10 · 2026-10-02：H7 内存评估批——§2 增 arm-zephyr-eabi 工具链；docs/h7-memory-assessment.md（S3 四配置实测 + H743 实构建 + 移植前置项）。
- v2.9 · 2026-10-02：板级十（Agent→真机部署 E2E）——§5 增教训 27（手抄二进制数组禁令 + 分区残留态 + gated 测试漂移掩盖）；board-deploy-01 报告。
- v2.8 · 2026-10-02：板级九（PWM/ADC 真后端）——§5 增教训 26（LEDC duty<<4 / zephyr,user phandle-array / LEDC pinctrl 宏位置 / Kconfig 嵌套漂移）；board-periph-01 报告。
- v2.7 · 2026-10-01：板级八（estop 真机）——§5 增教训 25（EDT 非 zephyr chosen 丢弃→aliases / io_mux 双使能注入 / fault=true 观测判据）；board-estop-01 报告。
- v2.6 · 2026-10-01：板级七（WiFi 重连）——§5 增教训 24（net_mgmt 回调重入自激 / esp32 陈旧租约 / 僵尸 TCP 半开 / sysworkq 阻塞纪律）；board-reconnect-01 报告与复跑入口。
- v2.5 · 2026-10-01：板级六（PSRAM 挂接）——§5 增教训 23（OCT 显式 / SMH 分配面 / WAMR GLOBAL_HEAP_POOL 无消费者 / 64KB 基线不可行 / 地址域证据）；board-psram-01 报告与复跑入口。
- v2.4 · 2026-09-28：板级五（flash 持久化）——§5 增教训 22（AMP 分区表腾位 / FIXED_PARTITION 弃用 / syscall 封装链接陷阱 / sim 程序一次语义 / K_THREAD_DEFINE delay 形参 / esptool no_reset 观测法）；board-persist-01 报告与复跑入口。
- v2.3 · 2026-09-27：板级四（WiFi+zenoh 命令往返基准）——§5 增教训 21（blobs/省电/mirrored 防火墙/zenoh const/version.cmake 竞态/反引号 heredoc 禁令）；netbench-01 报告与复跑入口（~/project/logs/nb_flash.sh，凭证在仓库外）。
- v2.2 · 2026-09-27：板级三（IO 延迟实测）——§5 增教训 20（ZEPHYR_USER_NODE 4.5 API / 4.4 用 DT_PATH(zephyr_user)；未定义宏字面拼接连环假象；dt-bindings 宏层级）。
- v2.1 · 2026-09-26：板级二（效率基准）——§5 增教训 18（WAMR XTENSA 陷出用官方汇编 + noexecstack）/19（k_cycle_get_64 冻结 → CCOUNT；通道描述符持久约束；管道伪乱码判读法）；板级基准复跑入口 = `docs/board-bench-01.md` §6（`~/project/logs/bflash.sh`）。
- v2.0 · 2026-09-26：**环境官方手册重建（owner 指令）**——§2 工作区改为 `west init --mr v4.4.0` 官方重建 + SDK 1.0.1 官方安装（~/zephyr-sdk-1.0.1）+ esptool 接入；§3 增板级构建/烧录/console 冒烟命令；§5 增教训 15（PATH interop 根因定论 + wsl.conf 修复）/16（SDK 安装三要点）/17（板级 bring-up 三坑），修正教训 13（shutdown 后 detach→reattach）/14（缓解手段除根后作废）；zenoh-pico 自旧工作区原样回拷（1.10.1 + config.h；L3 E2E 复跑待后续单元）。回归：native_sim 构建 + twister 14/14（58 用例）×2 + pytest + L5 全绿；板级：构建/烧录/console 冒烟绿，占用 text 91KB / 静态 bss 113KB / libc 堆余 218KB。
- v1.9 · 2026-09-26：接线批——§5 增教训 12（WAMR 模块生命周期怪癖 + mod_cache 复用规避）/13（usbipd 板卡进 WSL 全流程，xiao_esp32s3 @ /dev/ttyACM0）。
- v1.8 · 2026-09-26：板级前置——espressif 工具链安装（west espressif install，ESP32 系列不需要 Zephyr SDK）；xiao_esp32s3 定为真机板（DEC-43④）；WSL2 下 USB 串口不可见（板级会话需 usbipd-win 附加或 Windows 侧 esptool 烧录）。
- v1.7 · 2026-09-26：Q-23 实证批——§5 增教训 10/11（native_sim SMP 需显式 USE_SWITCH 否则静默失效 / 忙循环冻结模拟时钟——宿主墙钟为唯一可信测量时基）；framework.wamrdemo 套件（SMP/真实时间对齐配置样板）。
- v1.6 · 2026-09-26：M2b.2a 环境批——§2 增 WAMR-2.4.5 钉版（~/project/deps/wamr）与 clang/lld（wasm32 样例 APP）；§3 增 TS_WAMR_DIR 注入 + 样例重建入口 + WAMR 接入四要点（include 传播/独立库 -w/通用 invokeNative/stdout 钩子垫片）。
- v1.5 · 2026-09-25：§5 增教训 7/8/9（Windows SDK /mnt 互通掩盖变体问题〔CI 真因〕/Actions 注解调试通路/TUN 级代理重启即用）；远端 `github.com/embalmer-Y/Tessera` 上线，CI 四 job 全绿。

- v1.2 · 2026-09-23：§7 补丁清单 + §8 L3 端到端达成（PASS）与复跑方法（TAP 需 sudo；zenohd v1.10.1 @ ~/project/tools）。
- v1.4 · 2026-09-25：§8 补 TAP 重建失效教训 + Agent 部署 E2E 入口（MA3.1）。
- v1.3 · 2026-09-23：§8 L3 扩展为五验证点（DEC-40/41/42 实现批次：v2 信封/幂等/to 拒绝/租约/事件信封）复跑 PASS；缺省回退 locator udp→tcp（DEC-40 命令面链路约束——zenohd 缺省监听兼容）。
- v1.1 · 2026-09-23：§5-5 教训（`=` 后 `~` 不展开）+ §7 zenoh-pico 接入（1.10.1 钉版 / config.h 生成缺口 / POSIX_API 关键项）。
- v1.0 · 2026-09-21：建立（WSL 迁移完成 + Windows 复原 + 验证结果：native_sim 构建 ✓、twister 运行级 1/1 passed ✓、pytest ✓）。
