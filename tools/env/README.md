# tools/env · Tessera 自动化安装程序（面向用户）

> **定位**（DEC-79 · V0.16.0）：用户下载 Tessera 后的**一键自动化安装程序**——在
> Linux（x86_64 / aarch64）上装出可用的 Tessera 运行/开发环境。手工配方权威 =
> `docs/env-rebuild-checklist.md`（本套件 = 该配方的机械化）。
>
> **凭据红线**：LLM API key / WiFi 密码只经交互输入或 `--config` 文件进入；落盘仅
> 600 仓外文件（`~/project/logs/env.sh`），绝不入仓、绝不回显。

## 快速开始

```bash
git clone https://github.com/embalmer-Y/Tessera.git ~/project/Tessera
cd ~/project/Tessera

./tools/env/install.sh            # 标准档（产品使用：Agent + zenohd + esptool + 配置引导）
./tools/env/install.sh --dev      # 开发者档（追加固件全链：west 工作区/SDK/WAMR/回归面）
bash tools/env/verify_env.sh      # 分层验证（checklist §11 ①-⑤）
```

网络受限环境：`./tools/env/install.sh --proxy http://127.0.0.1:7890`（git/wget/curl/pip/apt 全走代理）。
无 root 环境：`--skip-sudo`（编译器转用户态回退——LLVM tarball；功能面受限，推荐有 sudo）。

## 两档安装面

| | 标准档（默认） | 开发者档（--dev） |
|---|---|---|
| Agent 运行环境（venv + 全依赖 + CLI） | ✅ | ✅ |
| zenohd 1.10.1 本机路由（standalone 二进制） | ✅ | ✅ |
| esptool 5.4.0（板卡烧录） | ✅ | ✅ |
| 用户配置引导（LLM 端点/API key/WiFi） | ✅ | ✅ |
| west 工作区（Zephyr v4.5.0-rc1 + blobs + zenoh-pico+TLS 补丁） | — | ✅ |
| Zephyr SDK 1.0.1（xtensa-esp32s3；`TESSERA_SDK_RISCV=1` 加 riscv64） | — | ✅ |
| WAMR 2.4.5（version.h 444 只读屏障） | — | ✅ |
| twister/构建回归面 | — | ✅ |

系统包（sudo 交互——执行时提示输入密码）：标准档最小面（git/curl/python3-venv 等）；
开发者档加构建工具链（build-essential/multilib[x86_64]/gperf/dtc/clang-18…）。
cmake 钉 3.31.6 于固件 venv 内（发行版 cmake 4.x 与 Zephyr 4.5 兼容风险——对用户机漂移免疫）。

## 用户配置（LLM 端点与密钥）

两条通道（二选一）：

1. **交互式（默认）**：安装过程逐项询问——API Key 隐藏输入不回显；
2. **配置文件**：`./tools/env/install.sh --config my.env`，`KEY=VALUE` 行式（`#` 注释、值可带引号）：

```bash
ANTHROPIC_BASE_URL=https://your-anthropic-compatible-endpoint/v4   # Agent LLM 端点
ANTHROPIC_API_KEY=sk-...                        # 密钥（文件建议 600）
TESSERA_LLM_MODEL=anthropic:MiniMax-M3          # 模型串（缺省 = 此默认）
TS_WIFI_SSID=...                                # 可选——板卡固件构建期注入
TS_WIFI_PASSWORD=...                            # 可选
ZENOHD_TCP_PORT=9957                            # 可选——本机 zenohd TCP 口（缺省 9957）
```

落盘：`~/project/logs/env.sh`（凭据 + 环境变量，600）+ `<repo>/agent/config.toml`（Agent
运行配置，gitignored，600）。**已存在的配置绝不覆盖**（改配置直接编辑或删除后重跑）。

## 步骤化与幂等

每步真实状态探测、已就绪即跳过——**任意一步失败修复后重跑 `install.sh` 即断点续装**：

| 步骤 | 内容 |
|---|---|
| `10-system-packages` | apt 系统包（sudo；档位分派 user/dev） |
| `20-dirs-repo` | 目录骨架 + 仓库 clone |
| `25-agent-venv` | Agent venv（uv 优先）+ editable 安装 |
| `30-firmware-venv` | 固件 venv（west + cmake 3.31.6 + esptool 5.4.0） |
| `40-west-workspace` | west init/update（断点重试）+ blobs 71 件 + zenoh-pico 接入三步 + TLS 补丁 |
| `50-zephyr-sdk` | SDK minimal + xtensa（+riscv64 可选）解 `gnu/` + setup.sh -c |
| `60-wamr` | WAMR clone + version.h 生成 + 444 屏障 |
| `65-llvm` | clang 18 用户态回退（tarball——无 sudo/无 clang-18 时） |
| `70-zenohd` | zenohd standalone 二进制 → `~/project/tools/zenohd` |
| `85-user-config` | 用户配置装配（env.sh 600 + agent/config.toml 600） |

单步补装：`./tools/env/install.sh --step 40-west-workspace`。

## 已实测平台

| 平台 | 实测 | 备注 |
|---|---|---|
| x86_64 · Ubuntu 26.04 | ✅ 2026-10-24（本套件首发验收机） | apt clang-18 = 18.1.8 精确对齐 CI；ghfast 之外代理通道实测 |
| aarch64 · Debian 13 | 手工配方实测（checklist §12） | 脚本路线待首台机回填（SDK/LLVM 资产名已核对） |

## 维护纪律

- 钉版常量在 `env_common.sh` 的 `PIN_*`（与 README「依赖与钉版」表、
  `firmware/tests/pytest/test_env_installer.py` 守恒测试三方一致——改版本三处同步）；
- zenoh-pico TLS 补丁 = `firmware/module/tessera/ext/zenoh-pico-tls.patch`（git apply
  严格校验通过——2026-10-24 修复计数/头行两处潜伏格式缺陷）；
- 剥宏清单 13 个（checklist §3 ② 的 12 个 + AUTO_RECONNECT——R5-V 起补丁基线，2026-10-24 实证回填）。
