# Tessera

**立方体智能 I/O 模块** —— 基于 Zephyr RTOS 的模块化末端输入输出系统，业务逻辑以可安装、可迁移的 APP 形态运行（类安卓：APP 与板卡硬件解耦），输入输出外设可插拔，物理输出具备安全限制，配套 MCP 形态 AI Agent 完成「需求分析 → 软件设计 → 编程开发 → 模拟测试 → 部署」的完整编程链路。

> 本项目完全由 AI（ZCode）开发，owner 负责裁决与 review。开发过程、裁决记录与工程纪律全部在库（`decisions.md` / `AGENTS.md` / `docs/`）。

[![CI](https://github.com/embalmer-Y/Tessera/actions/workflows/ci.yml/badge.svg)](https://github.com/embalmer-Y/Tessera/actions/workflows/ci.yml)

## 架构

```text
┌─────────────────────────── PC / 云 ───────────────────────────┐
│  AI Agent（MCP server：FastMCP）                              │
│  app_develop（真 LLM 生成 APP）· app_deploy · 模拟器 · TSAP   │
│  签名工具链 · spec 质量门 · 部署后诊断闭环 · sim↔real 对拍     │
└──────────────────────┬────────────────────────────────────────┘
                       │ zenoh（发现/部署/遥测/命令面）
┌──────────────────────┴────────────────────────────────────────┐
│  固件框架（Zephyr RTOS 模块 tessera）                          │
│  ts-appmgr  WAMR 宿主（wasm APP 沙箱）· TSAP v2 验签(ed25519) │
│             slot 双槽 · 健康链（指令配额）· 单活跃 APP         │
│  ts-safety  三安全态 · 写入路径唯一（限幅/slew/限流）· estop   │
│             硬件通道 · 断链 fail-safe · 分层看门狗             │
│  ts-hal     权限位图(ts_perm_v1) · GPIO/PWM/ADC/fs/av natives │
│  ts-net     zenoh-pico · 命令信封 v2 + 租约 · 部署命令面      │
│  ts-power / ts-periph / ts-store（prov/meta 双副本/持久化）   │
└──────────────────────┬────────────────────────────────────────┘
                       │ 真机目标：ESP32-S3（主力，真机基线 11 bench 全绿）
                          ESP32-P4 / STM32H7（构建级留档）
```

## 仓库地图

| 路径 | 内容 |
|---|---|
| `firmware/module/tessera/` | 固件框架源码（ts-* 七模块） |
| `firmware/tests/` | twister 套件（17 套件 117 用例——aarch64 /64 现行口径：115 过 + 2 skipped）+ 板级 bench（netbench/deploybench/otabench/…） |
| `firmware/app/` | 生产 app（板级片段：S3 PSRAM/WiFi/分区） |
| `agent/` | MCP server + 模拟器 + TSAP 工具链 + skills（pytest 208 用例 + 2 skipped） |
| `design/` | HLD + 七模块 LLD（v0.2 已确认） |
| `tools/board/` | 板级联调工具（E2E 驱动/prov·证书生成/串口持有器/消费端——README 含典型编排） |
| `docs/` | dev-environment（环境事实源）/ **env-rebuild-checklist（全新机器重建总单，含 ARM Linux）** / project-plan / impl-review 族 |
| `decisions.md` | Q/DEC 裁决登记册（全部决策可溯） |

## 依赖与钉版

钉版纪律（`docs/std/versioning.md` §4）：外部依赖一律钉具体版本/提交，禁浮动引用；升级走独立提交 + 回归。环境重建事实源 = `docs/dev-environment.md`。

| 依赖 | 钉版 | 用途 | 引入方式 |
|---|---|---|---|
| Zephyr RTOS | v4.5.0-rc1 | 固件 RTOS 基线 | west 工作区（`west init --mr`） |
| Zephyr SDK | 1.0.1 | 交叉工具链（xtensa-esp32s3 等）+ hosttools | `west sdk install` |
| espressif HAL blobs | 随 Zephyr 版本 | WiFi/BT 预编译库 | `west blobs fetch hal_espressif` |
| WAMR | 2.4.5 | wasm 运行时（APP 沙箱） | 源码 @ `TS_WAMR_DIR`（仓外 deps，构建期变量） |
| zenoh-pico | 1.10.1 | 板侧 zenoh 传输 | west 工作区模块 |
| eclipse-zenoh（Python） | 1.10.1 | Agent 侧 zenoh 会话 | agent pyproject（**三方同 minor**：zenohd / zenoh-python / zenoh-pico） |
| zenohd | 1.10.x | PC 侧路由器（联调用） | 独立二进制 |
| Python（agent 侧） | 见 `agent/pyproject.toml`：pydantic-ai-slim 2.47.\* / fastmcp 4.0.\* / cbor2 6.1.4 / pycose 1.1.0 / cryptography ≥42 / eclipse-zenoh 1.10.1 / pyserial | Agent 运行依赖，全钉版 | pip（editable 安装） |
| ed25519 签名/验签 | tweetnacl 20140427 快照 | 固件 COSE 验签（`crypto/PROVENANCE.md`）；Agent 侧 pycose + cryptography | 固件内置快照 / pip |
| LLM 端点 | Anthropic 兼容 API（生产 = MiniMax-M3） | APP 代码生成（密钥经环境变量，不入库） | 运行时配置 |

板级构建另需：esptool（固件 venv 内 `west packages pip`）与主机 gcc（native_sim，WSL `build-essential`）。

## 快速上手（Linux 环境）

环境事实源见 `docs/dev-environment.md`；**从零重建（多机/含 ARM Linux）按 `docs/env-rebuild-checklist.md` 逐项执行**（Zephyr v4.5.0-rc1 + Zephyr SDK 1.0.1 钉版；目录规范 `~/project/{Tessera,zephyrproject,logs}`）。迁移历史与平台差异记录见 `docs/migration-x86.md`（WSL2 历史口径见 dev-environment §1-8）。

```bash
# 固件构建（native_sim）
cd ~/project/zephyrproject
west build -p auto -b native_sim ~/project/Tessera/firmware/app \
  -- -DZEPHYR_EXTRA_MODULES=~/project/Tessera/firmware/module/tessera

# 固件回归（twister 17 套件；EXTRA_MODULES/TS_WAMR_DIR 必带；aarch64 加 -p native_sim/native/64 + ZEPHYR_TOOLCHAIN_VARIANT=host）
~/project/zephyrproject/.venv/bin/python ~/project/zephyrproject/zephyr/scripts/twister \
  -p native_sim -T ~/project/Tessera/firmware/tests \
  --extra-args=ZEPHYR_EXTRA_MODULES=~/project/Tessera/firmware/module/tessera

# Agent 回归
cd ~/project/Tessera/agent && python -m pytest tests/ -q && python -m ruff check .
```

## Demo 链（真机验证记录）

| Demo | 内容 | 状态 |
|---|---|---|
| D1–D7 | 控制/输入/安全/部署阶梯（blink→estop→限幅→ADC） | 真机 PASS |
| D4/D6 | ADC 变化上报 / 滞回控制环（clamp 限幅实证 + 真实落驱动） | 真机 PASS |
| D-SD | SD 卡文件系统 APP（白名单拒绝物理证据 + 宿主独立复核） | 真机 PASS |
| D8 | 三版本部署链（初装→升级 G4 即停→健康回滚→复活） | 真机 PASS |
| D9 | 断链 fail-safe 时间线（合同 3 双证据：sim + 真机） | 真机 PASS |
| D-AV | 摄像头帧采集发布（采集自愈 + 发送层根治后全链） | 真机 PASS（V0.2.0） |
| OTA | MCUboot 双槽 SMP 全链（上传→swap→confirm） | 真机 PASS |
| NV1 | 修复闭环（LLM 生成→部署→判据 PASS 一枪全链） | 真机 PASS |
| DP / DT | PDM 音频全链 / 真 wasm 多线程（原子共享 + join） | 真机 PASS |
| MA / NVD / AG7 | 多 APP 并行 / 新机全链 NVD / 真 LLM 多文件工程收敛 | 真机 PASS |
| CG7 | V0.7.0 合同泛化 spot check（caps 自报 + 预检消费 + 部署全链） | 真机 PASS |
| AK AUDIO | ES8311 全 codec 音频输入输出（第二板 dnesp32s3b） | 真机 PASS |
| AK3 TRUST | 多开发者信任链 E2E（注册→多根部署→防回滚→撤回，无线） | 真机 PASS |
| AK4 RES | net+SD 资源推送（sha256 读回校验 + APP 消费端字节命中） | 真机 PASS |
| AK5 LARGE | 206KB wasm 大档全链（板上验签 412KB 包 + PSRAM 装载 + 运行） | 真机 PASS |
| AK6 LN | 双板逻辑节点编排（扇出部署 + 聚合状态双 ACTIVE） | 真机 PASS |

## 安全与确定性合同（摘要，全文 `AGENTS.md` §6）

三安全态（每输出通道显式声明上电/断链/故障态）· 写入路径唯一（一切输出经保护层）· 断链 fail-safe · 分层看门狗 · estop 硬件通道（ISR 直达）· 初始化顺序固定 · 确定性（重放机械验证）· 固件核心不学习（权限模型不经运行时自适应）。

## License

Apache-2.0。
