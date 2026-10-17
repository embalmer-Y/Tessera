# 迁移说明：Windows/WSL2 → 原生 x86 Linux（2026-10-11）

> **性质**：开发环境整体迁移的操作文档（owner 裁决：项目后续在原生 x86 Linux 机器开发）。
> **权威源**：GitHub `embalmer-Y/Tessera`（main + 全部 tag）——迁移前已确认本地与远端完全同步；**仓库即全部工程状态**，本说明覆盖仓外资产与重建步骤。
> **环境事实源**：`docs/dev-environment.md`（WSL 版）；本文档记录原生 Linux 的差异点。

## 1. 迁移原则

- **一切以 GitHub 为准**：clone 即得全部代码/文档/工具（本批已把仓外板级工具脚本与关键证据单迹入仓，见 §3）。
- **凭据不入仓**：WiFi 凭据、LLM API key 经环境变量注入（新机器重配，见 §4）。
- **可重建不搬运**：WAMR 源码、zenohd、Zephyr 工作区、venv 均按钉版重建，不拷贝。

## 2. 新机器环境重建（原生 x86 Linux 与 WSL 的差异）

基础步骤与 `docs/dev-environment.md` §1-§3 相同（目录 `~/project/{tessera,zephyrproject,logs}`、west 工作区 v4.5.0-rc1、SDK 1.0.1、两个 venv）。**（2026-10-17 注：完整重建配方以 `docs/env-rebuild-checklist.md` 为权威——本节为 x86 迁移时点差异记录。）** 差异点：

| 项 | WSL（旧） | 原生 Linux（新） |
|---|---|---|
| 板卡接入 | usbipd（Windows 侧 attach） | **USB 直连**（`/dev/ttyACM0` 原生出现，无需 usbipd；用户加 `dialout` 组） |
| 网络 | mirrored 模式 + Hyper-V 防火墙规则 | 原生桥接，无特殊配置 |
| 主机工具链 | apt build-essential（multilib） | 同左（`gcc gcc-multilib g++-multilib`） |
| WSL 特有坑（全部消失） | 空闲关机清 /tmp、usbipd 陈旧 attach、`/mnt/c` PATH 劫持、Windows PATH 泄漏 | 无 |

重建清单（顺序执行）：

```bash
# ① 仓库
git clone git@github.com:embalmer-Y/Tessera.git ~/project/tessera

# ② west 工作区（Zephyr v4.5.0-rc1 钉版 + zenoh-pico 模块 + blobs）
python3 -m venv ~/project/zephyrproject/.venv
source ~/project/zephyrproject/.venv/bin/activate
pip install west
west init -m https://github.com/zephyrproject-rtos/zephyr --mr v4.5.0-rc1 ~/project/zephyrproject
cd ~/project/zephyrproject && west update && west blobs fetch hal_espressif
pip install -r zephyr/scripts/requirements.txt

# ③ Zephyr SDK 1.0.1（含 xtensa-espressif_esp32s3_zephyr-elf + hosttools）
west sdk install -t xtensa-espressif_esp32s3_zephyr-elf -t hosttools

# ④ WAMR 2.4.5（仓外源码，TS_WAMR_DIR）+ version.h 只读屏障（教训 21⑤）
git clone --depth 1 --branch WAMR-2.4.5 https://github.com/bytecodealliance/wasm-micro-runtime.git ~/project/deps/wamr
cmake -DWAMR_ROOT_DIR=$HOME/project/deps/wamr -P ~/project/deps/wamr/build-scripts/version.cmake
chmod 444 ~/project/deps/wamr/core/version.h

# ⑤ zenohd（PC 联调路由器；三方同 minor 纪律 DR-22）
#    按发行版安装 zenoh 1.10.x，或 cargo install zenohd（记录实际版本）

# ⑥ agent venv（钉版见 agent/pyproject.toml）
python3 -m venv ~/project/agent-venv
~/project/agent-venv/bin/pip install -e "~/project/tessera/agent[dev]"
```

## 3. 仓外资产处置（本批已完成的入仓）

原先只存在于 WSL `~/project/logs` 的资产，已按性质入仓：

- ~~`tools/board/`（34 个脚本）入仓~~ **本条登记失实（两次）且从未兑现**：b1a31e4 提交内容实际为零 tools/board 文件——根因 = `.gitignore` 整目录忽略 `/tools/`（`git add -A` 静默跳过）。2026-10-17 fw-v0.9.0 环境审查批修复：gitignore 摘除 + 当前 era 实际使用的 16 个会话驱动脚本 + ota_client/gen_tls_certs.sh 真实入仓（WSL 时代 34 脚本本体随 WSL 销毁不再可考——其功能后继 = 现清单，见 `tools/board/README.md`）。
- **`docs/evidence/`（关键真机单迹，新目录）**：decisions 登记册引用的验证证据物理文件（nv1/nv6 全流程 console、simreal 首基线 JSON、D-AV 双帧图像、#121774 禁自愈 951 超时对照、auditbench AB PASS、dsd 换卡 PASS）。

**未入仓、由迁移包带走的**（见 §5 迁移包）：

| 资产 | 原因 |
|---|---|
| `~/project/logs/md1-keys/`（md1/dav 测试密钥对） | 私钥不入公开仓；当前 TEST bench 全部使用仓内 `ts-test-root`（fixtures），此二对仅历史留档 |
| `~/project/logs/` 其余证据与探针（约 160 个文本、未入仓脚本） | 历史诊断中间产物；关键结论已在 decisions.md，物理单迹留迁移包备查 |
| LLM 凭据（ANTHROPIC_BASE_URL / ANTHROPIC_API_KEY） | 密钥；新机器重配（见 §4） |

**不需要带走**（按钉版重建）：`~/project/deps/wamr`（2.4.5 tag）、`~/project/tools/`（zenohd 二进制）、`~/project/agent-venv`、`~/project/zephyrproject`（11G 工作区全部可重建）、`~/project/builds/`（构建产物）。

## 4. 新机器凭据与配置重配

```bash
# WiFi（板级构建注入；凭据自备）
export TS_WIFI_SSID=... TS_WIFI_PASSWORD=...

# LLM（Agent app_develop；Anthropic 兼容端点）
export ANTHROPIC_BASE_URL=... ANTHROPIC_API_KEY=...

# agent config（~/project/tessera/agent/config.toml，gitignored——从迁移包恢复或按
#   agent/tessera_agent/common/config.py 默认值重建：default_model/context_window/router_locator）
```

GitHub 推送：新机器配置 SSH key（`embalmer-Y` 身份，`embalmer-Y <y19858120112@163.com>`）。

## 5. 迁移验证清单（新机器逐项打勾）

**本节验证清单已升级为独立权威文档 `docs/env-rebuild-checklist.md`（fw-v0.9.0 起环境重建唯一总单；本节以下为 2026-10-11 历史口径存档）。** 历史口径：① HEAD 与 tag 集（当前应含 fw-v0.1.0…fw-v0.9.0）；② twister（现口径 16/16 套件 113 用例）；③ agent pytest（现口径 204+2s）+ ruff；④ repo pytest 2；⑤ 板级冒烟（tools/board/README.md 典型编排）；⑥ zenoh 联调 + TLS E2E（TLS 态 zenohd 双监听）。

## 6. Windows 机器清除指引

**已由 AI 会话执行（本批）**：

- `D:\Software\project\Tessera`（Windows 快照，非权威——GitHub 已全量确认后删除）
- `D:\Software\project\Tessera-fresh`（旧 clone，HEAD 5a73c46 已过时）
- `D:\Software\project\esp_hosted`（C6 固件工作副本，上游可重 clone；P4 已搁置 DEC-51）

**迁移包（owner 带走后Windows 侧删除）**：`D:\tessera_migration_bundle\`（本批生成：仓外证据 + 历史密钥 + config.toml）。

**owner 手动/决定项**（AI 不代删）：

| 项 | 位置 | 建议 |
|---|---|---|
| WSL Ubuntu 发行版 | `wsl --shutdown` 后 `wsl --unregister Ubuntu`（最彻底，含 `~/project` 全部仓外资产——**确认迁移包已带走后执行**） | 删 |
| Windows 共用 zephyrproject | `D:\Software\project\zephyrproject`（含 owner 其它项目 proj/blinky 等——**非 Tessera 专属**） | owner 定（若其它项目仍用则留） |
| Espressif EIM 工具区 | `C:\Espressif`（dist + tools；C6/IDF 批用，DEC-51 后项目不再需要） | 删（建议经 EIM 卸载流程） |
| IDF 多版本框架 | `D:\App\ESP`（eim + idf） | owner 定（个人 IDF 环境可能另用） |
| usbipd | Windows 程序 | 卸载可选（原生 Linux 不需要） |
| ZCode 项目记忆 | `C:\Users\<u>\.zcode\cli\memories\projects\tessera-*` | owner 定（删除则 Windows 侧 ZCode 会话失忆；对迁移无影响） |
| ZCode 会话执行日志 | `C:\Users\<u>\.zcode\cli\exec\sess_29941d7a*` | 删 |

## 7. 迁移后纪律延续

- 开发流程/军规/裁决门不变（AGENTS.md 为会话入口）；
- dev-environment.md 由"WSL 事实源"角色转为**历史环境记录**——新机器首会话应新增原生 Linux 环境节并以之为事实源；
- `tools/board/` 脚本在新机器的路径差异（`~` 展开、venv 路径）首次使用时校正。
