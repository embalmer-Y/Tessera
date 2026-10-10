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
| `firmware/tests/` | twister 套件（15 套件 77+ 用例）+ 板级 bench（netbench/deploybench/otabench/…） |
| `firmware/app/` | 生产 app（板级片段：S3 PSRAM/WiFi/分区） |
| `agent/` | MCP server + 模拟器 + TSAP 工具链 + skills（pytest 100+ 用例） |
| `design/` | HLD + 七模块 LLD（v0.2 已确认） |
| `docs/` | dev-environment（环境事实源）/ project-plan / impl-review 族 |
| `decisions.md` | Q/DEC 裁决登记册（全部决策可溯） |

## 快速上手（WSL2 Ubuntu 环境）

环境事实源见 `docs/dev-environment.md`（目录规范 `~/project/{tessera,zephyrproject,logs}`；Zephyr v4.5.0-rc1 + Zephyr SDK 1.0.1 钉版）。

```bash
# 固件构建（native_sim）
cd ~/project/zephyrproject
west build -p auto -b native_sim ~/project/tessera/firmware/app \
  -- -DZEPHYR_EXTRA_MODULES=~/project/tessera/firmware/module/tessera

# 固件回归（twister 15 套件；EXTRA_MODULES 必带）
~/project/zephyrproject/.venv/bin/python ~/project/zephyrproject/zephyr/scripts/twister \
  -p native_sim -T ~/project/tessera/firmware/tests \
  --extra-args=ZEPHYR_EXTRA_MODULES=~/project/tessera/firmware/module/tessera

# Agent 回归
cd ~/project/tessera/agent && python -m pytest tests/ -q && python -m ruff check .
```

## Demo 链（真机验证记录）

| Demo | 内容 | 状态 |
|---|---|---|
| D1–D7 | 控制/输入/安全/部署阶梯（blink→estop→限幅→ADC） | 真机 PASS |
| D4/D6 | ADC 变化上报 / 滞回控制环（clamp 限幅实证 + 真实落驱动） | 真机 PASS |
| D-SD | SD 卡文件系统 APP（白名单拒绝物理证据 + 宿主独立复核） | 真机 PASS |
| D8 | 三版本部署链（初装→升级 G4 即停→健康回滚→复活） | 真机 PASS |
| D9 | 断链 fail-safe 时间线（合同 3 双证据：sim + 真机） | 真机 PASS |
| D-AV | 摄像头帧采集发布 | ◐（上游 #121774 + zenoh-pico 发送缺陷阻塞） |
| OTA | MCUboot 双槽 SMP 全链（上传→swap→confirm） | 真机 PASS |
| NV1 | 修复闭环（LLM 生成→部署→判据 PASS 一枪全链） | 真机 PASS |

## 安全与确定性合同（摘要，全文 `AGENTS.md` §6）

三安全态（每输出通道显式声明上电/断链/故障态）· 写入路径唯一（一切输出经保护层）· 断链 fail-safe · 分层看门狗 · estop 硬件通道（ISR 直达）· 初始化顺序固定 · 确定性（重放机械验证）· 固件核心不学习（权限模型不经运行时自适应）。

## License

Apache-2.0。
