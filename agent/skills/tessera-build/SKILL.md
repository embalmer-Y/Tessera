---
name: tessera-build
description: 固件构建/测试命令事实源——west/twister/pytest 用法、钉版纪律与环境要点
sources:
  - docs/dev-environment.md
  - docs/std/versioning.md
---

# 固件构建与测试（fw_* 工具用法）

> 派生自 docs/dev-environment.md（WSL 环境事实源）。命令均经 fw_build/fw_twister/fw_pytest
> 工具（子进程 venv west），勿裸跑。

## 环境与目录（WSL Ubuntu 24.04）

- 仓库 `~/project/tessera`；west 工作区 `~/project/zephyrproject`（Zephyr **v4.4.0 钉版**）；
  固件 venv `~/project/zephyrproject/.venv`；Agent venv `~/project/agent-venv`。
- Tessera 模块经 `ZEPHYR_EXTRA_MODULES` 注入（路径含 `~` 不展开——一律 `$HOME` 绝对路径）。

## 常用命令

- 构建：`west build -b native_sim <app> -d <build> -- -DZEPHYR_EXTRA_MODULES="<tessera>;<zenoh-pico>"`
- twister：`west twister -p native_sim -T ~/project/tessera/firmware/tests --extra-args=ZEPHYR_EXTRA_MODULES=$HOME/project/tessera/firmware/module/tessera`
- pytest（军规 4 编码）：`~/project/zephyrproject/.venv/bin/python -m pytest firmware/tests/pytest`
- L5 机械检查：`python3 firmware/tests/l5/check_l5.py`

## 钉版纪律（versioning.md）

Zephyr v4.4.0；zenoh 三方同 minor（zenohd / eclipse-zenoh / zenoh-pico = 1.10.1，DR-22）；
Python 依赖见 agent/pyproject.toml（升级 = 显式提交 + 全量回归）。

## zenoh-pico 接入要点（dev-env §7）

上游零源码补丁；唯一非上游文件 = 生成的 `include/zenoh-pico/config.h`；
`CONFIG_POSIX_API=y` 关键（netdb 冲突）；pthread 链与 POSIX 池参数见 l3app/prj.conf 注释。
