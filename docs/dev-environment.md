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
| venv | `~/project/zephyrproject/.venv`，Python 3.12.3 | west 1.5.0 + zephyr `scripts/requirements.txt` 全量 + pytest/gcovr/jsonschema（pip 清华镜像） |
| Zephyr 工作区 | v4.4.0 **tag 钉版**（自 Windows 拷贝，8.8G，模块与钉版一致） | DEC-19 |
| 网络 | apt/pip 走清华镜像（免代理）；GitHub 访问如需 → 经 Windows 代理 127.0.0.1:7897（WSL→Windows 需用主机 IP，暂未配——当前工作区完整拷贝，无网络需求） | |
| **缺项** | Zephyr SDK（Linux 版）未装 | native_sim 开发**不需要**；真机板交叉构建需时下载 SDK 1.0.1 Linux 包（~1GB，建议经 Windows 代理下载后从 /mnt 拷入）——登记为待办，板级移植前完成 |

## 3. 构建与测试命令（WSL 内，标准入口）

```bash
cd ~/project/zephyrproject
# 构建（native_sim，DEC-13/14 CI 基线）
.venv/bin/west build -b native_sim ~/project/tessera/firmware/app -d build-m0-app \
  -- -DZEPHYR_EXTRA_MODULES=~/project/tessera/firmware/module/tessera
# twister（运行级测试；tests/ 下用例）
.venv/bin/west twister -p native_sim -T ~/project/tessera/firmware/tests \
  --extra-args=ZEPHYR_EXTRA_MODULES=~/project/tessera/firmware/module/tessera
# pytest 仓库检查（军规 4 编码）
~/project/zephyrproject/.venv/bin/python -m pytest ~/project/tessera/firmware/tests/pytest -v
```

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

## 6. 会话规范（此后所有开发会话）

- 开发在 **WSL Ubuntu** 内进行；仓库 = `~/project/tessera`（bootstrap 流程不变，见 AGENTS.md §2）。
- Windows 端仅保留浏览器/编辑/交流；不在 Windows 侧跑构建。

## 7. zenoh-pico 工作区接入（M3a.1 起，钉版 1.10.1——DR-22 三方同 minor）

1. 拉取：`git clone --depth 1 --branch 1.10.1 https://github.com/eclipse-zenoh/zenoh-pico.git ~/project/zephyrproject/zenoh-pico`（需代理 127.0.0.1:7897）。
2. 生成 config.h（**上游 Zephyr 模块缺口**：其 zephyr/CMakeLists.txt 不执行 configure_file，直接编译报 `zenoh-pico/config.h` 缺失）：
   - `cmake -S ~/project/zephyrproject/zenoh-pico -B <tmpdir>` 生成 `<tmpdir>/include/zenoh-pico/config.h`
   - 剥离 feature 宏区后落位（feature 宏由 Kconfig→zephyr_compile_definitions 供给，避免重定义）：`sed '/^#define Z_FEATURE_/d; /^#cmakedefine Z_FEATURE_/d' <tmpdir>/include/zenoh-pico/config.h > ~/project/zephyrproject/zenoh-pico/include/zenoh-pico/config.h`
3. 构建接线：`-DZEPHYR_EXTRA_MODULES="<tessera module>;<zenoh-pico>"` + `firmware/tests/net/overlay-zenoh.conf`（EXTRA_CONF_FILE）。**关键项 `CONFIG_POSIX_API=y`**——zenoh-pico Zephyr 平台层直引 `<netdb.h>/<sys/socket.h>`，host libc 下与 Zephyr net_ip.h 结构冲突，必须经 POSIX API 解析。
4. 升级纪律：三方（zenohd router / eclipse-zenoh Python / zenoh-pico）联合升级 + 全量回归（DR-22；Zenoh 2.0 watch）。

## 8. L3 端到端前置（native_sim ↔ zenohd router；M3a.2 登记，待 owner）

L3（LLD-ts-net §8）= native_sim 固件经真实 zenoh 会话对 PC 侧 router 完成发现/命令/回执/心跳。前置两件，均超出当前用户权限，**待 owner 一并处置**：

1. **TAP 网卡（需 sudo，密码交互）**：native_sim 网络出 host 的唯一路径 = `ETH_NATIVE_POSIX` + TAP。Zephyr 自带脚本 `zephyr/scripts/net-setup.sh -i zeth`（创建 tap0 + NAT 规则）。当前 WSL sudo 需密码 → 无法无人值守执行。
2. **zenohd router 安装（用户态可行）**：GitHub eclipse-zenoh/zenoh release 下载 1.10.x zenohd 二进制（与 DR-22 三方同 minor 对齐）至 `~/project/tools/`；或 `cargo install`（重）。可在 L3 会话内自行完成，无需 owner。

## 修订记录

- v1.2 · 2026-09-23：§8 L3 端到端前置登记（TAP 需 owner sudo；zenohd 用户态安装）。
- v1.1 · 2026-09-23：§5-5 教训（`=` 后 `~` 不展开）+ §7 zenoh-pico 接入（1.10.1 钉版 / config.h 生成缺口 / POSIX_API 关键项）。
- v1.0 · 2026-09-21：建立（WSL 迁移完成 + Windows 复原 + 验证结果：native_sim 构建 ✓、twister 运行级 1/1 passed ✓、pytest ✓）。
