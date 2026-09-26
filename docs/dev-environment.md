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

## 修订记录

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
