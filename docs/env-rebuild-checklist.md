# 全新机器环境重建总检查单（env-rebuild-checklist.md）· 2026-10-17 建立

> **本文用途**：唯一权威的从零重建配方——当前环境（原生 x86 Linux）销毁后，
> 在任意新机器（x86_64 与 **aarch64/ARM Linux**）按序执行即得完整开发/联调环境。
> **事实来源**：本机 2026-10-11 重建实测（dev-environment §9）+ 2026-10-17
> fw-v0.9.0 环境审查批核对；aarch64 列已按官方资产与包生态核对（SDK 资产名
> 实证存在），**标注 ⚠ 的行 = 尚未在 ARM 机实测，首台 ARM 机执行后回填实测注记**。
> **配套**：板级工具用法 = `tools/board/README.md`；历史迁移记录 = `docs/migration-x86.md`。

## 0. 前提与原则

- **钉版纪律**：一切外部依赖钉具体版本（README「依赖与钉版」表）；禁浮动。
- **仓库即工程状态**：clone `git@github.com:embalmer-Y/Tessera.git` 即得全部
  代码/文档/工具；仓外只允许五类资产（可重建源码 / 构建产物 / 凭据 / 证书 /
  日志）。
- **凭据不入仓**：WiFi / LLM key / 私钥 / 证书私钥一律环境变量或 600 仓外文件。
- 路径约定：`~/project/{Tessera,zephyrproject,logs,deps,tools,builds}`、
  `~/zephyr-sdk-1.0.1`、`~/project/agent-venv`、`~/project/zephyrproject/.venv`。

## 1. 系统包（apt；Ubuntu 24.04 基准）

| 包 | x86_64 | aarch64 | 用途 |
|---|---|---|---|
| build-essential / gcc / g++ | ✅ | ✅ | host 编译（twister native_sim） |
| **gcc-multilib** | ✅ 必装（native_sim 32 位） | **不需要**（aarch64 走 64 位口径，见 §11①） | host 工具链 |
| gperf、pkg-config、libncurses-dev | ✅ | ✅ | Zephyr host 工具 |
| device-tree-compiler (dtc) | ✅ | ✅ | twister/构建 |
| python3 + python3-venv + python3-pip | ✅ | ✅ | 3.12 起可 用；3.14 已实证（x86 机 3.14.4） |
| git、file、xz-utils、curl | ✅ | ✅ | 基础 |
| **clang-18 / lld-18**（可选路线 A） | noble 源缺旧版时走 §7 路线 B | **✅ apt 直装（noble universe 有 clang-18）——ARM 机推荐路线 A** ⚠ | wasm APP 交叉编译（18.1 系对齐 CI） |
| libserialport 等板包 | 不需要 | 不需要 | pyserial 自带 |

网络通道（按需）：代理环境下 git 走
`git config --global http.version HTTP/1.1` +
`git config --global url."https://ghfast.top/https://github.com/".insteadOf "https://github.com/"`
（大克隆加速；对象 SHA 校验保证完整性）；pip 走清华镜像
`-i https://pypi.tuna.tsinghua.edu.cn/simple`。无代理环境删除这两条即可。

## 2. 目录与仓库

```bash
mkdir -p ~/project/{logs,deps,tools,builds}
git clone git@github.com:embalmer-Y/Tessera.git ~/project/Tessera   # 大写 T
```

## 3. 固件 Python venv + west 工作区（Zephyr v4.5.0-rc1 钉版）

```bash
python3 -m venv ~/project/zephyrproject/.venv
source ~/project/zephyrproject/.venv/bin/activate
pip install west
cd ~/project
west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.5.0-rc1 zephyrproject
cd zephyrproject
west update                       # 代理慢时：可改 git fetch --depth 1 手法（dev-env §9.3）
west blobs fetch hal_espressif    # WiFi blobs——必做，不随 west update 拉取（教训 30）
pip install -r zephyr/scripts/requirements.txt
pip install esptool==5.4.0        # 直装——`west packages pip --install` 有 3.14 缺口（§9.5②）
```

- zenoh-pico 模块随 `west update` 就位（manifest 内 1.10.1 钉版）；
  **TLS 补丁**：`firmware/module/tessera/ext/zenoh-pico-tls.patch` 应用步骤 =
  dev-environment §7-4（重放纪律：pristine 基线 + strip 12 个 Kconfig 宏）。

## 4. Zephyr SDK 1.0.1（交叉工具链；x86_64 / aarch64 资产均实证存在）

```bash
# x86_64:
#   zephyr-sdk-1.0.1_linux-x86_64_minimal.tar.xz
# aarch64（ARM Linux）⚠:
#   zephyr-sdk-1.0.1_linux-aarch64_minimal.tar.xz
# 解压 ~/zephyr-sdk-1.0.1 后，工具链 tarball 解入 **gnu/ 子目录**（1.0 新布局——
# 顶层放置 = cmake "Unable to find any architecture"；dev-env §9.3）:
#   toolchain_gnu_linux-<arch>_xtensa-espressif_esp32s3_zephyr-elf.tar.xz
# 最后: cd ~/zephyr-sdk-1.0.1 && ./setup.sh -c   （注册 cmake 包 + hosttools）
```

来源：`github.com/zephyrproject-rtos/sdk-ng/releases/tag/v1.0.1`。
注意 minimal 包**不含工具链**，工具链单独下载同 tag assets。

## 5. WAMR 2.4.5（仓外源码；构建期 TS_WAMR_DIR 注入）

```bash
git clone --depth 1 --branch WAMR-2.4.5 \
  https://github.com/bytecodealliance/wasm-micro-runtime.git ~/project/deps/wamr
cmake -DWAMR_ROOT_DIR=$HOME/project/deps/wamr -P \
  ~/project/deps/wamr/build-scripts/version.cmake   # 生成 version.h
chmod 444 ~/project/deps/wamr/core/version.h        # 只读屏障（教训 21⑤——并发竞争）
```

## 6. 标准构建环境变量（每次会话；建议入 ~/project/logs/env.sh 同文件）

```bash
export ZEPHYR_EXTRA_MODULES="/home/<u>/project/Tessera/firmware/module/tessera;/home/<u>/project/zephyrproject/zenoh-pico"
export TS_WAMR_DIR=/home/<u>/project/deps/wamr
export PATH="$HOME/project/zephyrproject/.venv/bin:$PATH"   # esptool/west 直用——
            # 板级 cmake 探测 "esptool>=5.0.2 not found in PATH" 即此缺失
# 凭据（见 §9）
source ~/project/logs/env.sh
```

## 7. clang 18（wasm APP 编译链；CI 对齐 18.1 系）

- **路线 A（推荐）**：`sudo apt install clang-18 lld-18`（noble universe；
  aarch64 同名包存在 ⚠）。若 CI 对齐要求 18.1.x 精确版，看 `clang-18 --version`
  决定是否走路线 B。
- **路线 B（x86_64 实测法，apt 不可用时）**：LLVM 18.1.8 官方 tarball +
  libtinfo5 deb `dpkg -x` + `patchelf --set-rpath`（全步骤 dev-env §9.3；
  aarch64 需换 aarch64 LLVM tarball 与 `aarch64-linux-gnu` 路径 ⚠）。
- 软链 `clang`/`clang++` 入 `~/.local/bin`。

## 8. zenohd 1.10.1（PC 侧路由器；三方同 minor：zenohd/zenoh-python/zenoh-pico）

```bash
# 路线 A：cargo（aarch64 原生支持 ⚠ 实测回填版本号）
cargo install --locked zenohd --version 1.10.1   # 产物入 ~/.cargo/bin，软链 ~/project/tools/zenohd
# 路线 B：eclipse-zenoh GitHub releases 官方二进制（x86_64/aarch64 均有发布 ⚠）
```
启动命令（明文 9955 / TLS mTLS 双监听 9956+9957）= tools/board/README.md。

## 9. 凭据与运行时配置（不入仓资产）

```bash
# ~/project/logs/env.sh（600）:
export TS_WIFI_SSID=... TS_WIFI_PASSWORD=...      # 板级构建注入
export ANTHROPIC_BASE_URL=... ANTHROPIC_API_KEY=...  # Agent 真 LLM（Anthropic 兼容端点）
# agent/config.toml（gitignored，~/project/Tessera/agent/）:
#   按 agent/tessera_agent/common/config.py 默认值重建（default_model/context_window/router_locator）
# TLS 证书（TLS E2E 才需要）: tools/board/gen_tls_certs.sh → ~/project/tls/（600）
```

## 10. Agent venv（钉版见 agent/pyproject.toml）

```bash
python3 -m venv ~/project/agent-venv
~/project/agent-venv/bin/pip install -e "~/project/Tessera/agent[dev]"
```
- Python 3.14 下部分包无 wheel（x86 实测：ruamel.yaml.clib / tree-sitter-cmake）
  → 源码编译手法（libpython3.14-dev 用户态解包 + CC/CFLAGS/LDFLAGS）=
  dev-env §9.3；**aarch64 的 gcc lib 路径换 `/usr/lib/gcc/aarch64-linux-gnu/14`** ⚠。
 保守选择：新机用 Python 3.12 系可全 wheel 免编译（agent 依赖已实证 3.12/3.14 双兼容）。

## 11. 分层验证清单（重建完成判据；顺序执行）

| # | 验证 | 命令 | 通过线 |
|---|---|---|---|
| ① | twister 回归 | `~/project/zephyrproject/.venv/bin/python zephyr/scripts/twister -p native_sim -T ~/project/Tessera/firmware/tests --extra-args=ZEPHYR_EXTRA_MODULES=…`（aarch64：`-p native_sim/native/64` ⚠） | **16/16 套件（113 用例）**；aarch64 首跑后回填实数 |
| ② | 板级构建 | `west build -p always -b dnesp32s3b/esp32s3/procpu ~/project/Tessera/firmware/tests/atkbench -d ~/project/builds/ak -- -DATKBENCH_WIFI_SSID=… -DATKBENCH_WIFI_PASSWORD=…`（§6 环境变量前置） | 零 error 零 DRAM overflow，镜像产出 |
| ③ | agent 回归 | `cd agent && pytest tests/ -q && ruff check .` | **204 passed +2 skipped** / ruff 干净 |
| ④ | repo pytest | `firmware/tests/pytest` 下 pytest | 2 passed |
| ⑤ | sync_check | agent venv `python -m tessera_agent.skills.sync_check` | 与 SOURCES.lock 一致 |
| ⑥ | 板级冒烟（有板时） | tools/board/README.md「典型编排」①-⑥ | CONNECTED loc=tls + AKa0/AK7/AKU1 rc=0 |
| ⑦ | 全链验收（有板+LLM key） | `python3 tools/board/nvd_demo.py` | NVD PASS（真 LLM→部署→真机判据） |

## 12. 平台差异登记（已实测 vs 待实测）

- **x86_64**（本机口径，全项实测）：§9.3 无 sudo 手法、multilib 32 位 native_sim、
  clang tarball 18.1.8、Python 3.14.4。
- **aarch64/ARM Linux** ⚠ 全列推定项（官方资产/包生态已核对，待首台机实测回填）：
  SDK aarch64 minimal + esp32s3 工具链（资产名实证）；apt clang-18；
  native_sim/native/64 twister 口径；agent 依赖 aarch64 wheel 覆盖度；
  zenohd cargo 二进制；gcc 路径差异（§9.3/§10 两处）。
  **首台 ARM 机执行本单后，在此逐行回填「实测 ✅ + 实测值」。**

## 修订记录

- v1.0 · 2026-10-17：fw-v0.9.0 环境审查批建立（x86_64 实测 + aarch64 核对）；
  同批修复 tools/board 登记失实链（.gitignore `/tools/` 整目录忽略根因 +
  16 个会话驱动入仓——tools/board/README.md）。
