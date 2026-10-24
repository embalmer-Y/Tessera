# SPDX-License-Identifier: Apache-2.0
# steps/50-zephyr-sdk.sh · Zephyr SDK 1.0.1（交叉工具链 + hosttools；开发者档）。
# 布局（checklist §4）：minimal 解压 ~/zephyr-sdk-1.0.1；工具链 tarball 解入 gnu/ 子目录
# （1.0 新布局——顶层放置 = cmake 探测失败）；setup.sh -c 注册 cmake 包 + hosttools。
# 工具链面（按架构 + 用途）：xtensa-esp32s3 = ESP32-S3 板级构建必需；riscv64 = P4/C6 可选。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

SDK_REL="https://github.com/zephyrproject-rtos/sdk-ng/releases/download/v${PIN_SDK_VER}"
_minimal_asset="zephyr-sdk-${PIN_SDK_VER}_linux-${ARCH}_minimal.tar.xz"
_xtensa_asset="toolchain_gnu_linux-${ARCH}_xtensa-espressif_esp32s3_zephyr-elf.tar.xz"
_riscv_asset="toolchain_gnu_linux-${ARCH}_riscv64-zephyr-elf.tar.xz"

_log "50 · Zephyr SDK ${PIN_SDK_VER}（${ARCH}）"

if [ ! -d "$SDK_HOME" ] || [ ! -x "$SDK_HOME/setup.sh" ]; then
    fetch "$SDK_REL/$_minimal_asset" "$DL_DIR/$_minimal_asset"
    mkdir -p "$HOME"
    tar -xJf "$DL_DIR/$_minimal_asset" -C "$HOME"
else
    step_skip "50-① SDK minimal（$SDK_HOME 在位）"
fi

# xtensa（ESP32-S3 目标——默认必装）
if [ ! -d "$SDK_HOME/gnu/xtensa-espressif_esp32s3-zephyr-elf" ]; then
    fetch "$SDK_REL/$_xtensa_asset" "$DL_DIR/$_xtensa_asset"
    mkdir -p "$SDK_HOME/gnu"
    tar -xJf "$DL_DIR/$_xtensa_asset" -C "$SDK_HOME/gnu"
else
    step_skip "50-② xtensa-esp32s3 工具链"
fi

# riscv64（P4/C6 目标——TESSERA_SDK_RISCV=1 时装）
if [ "${TESSERA_SDK_RISCV:-0}" = "1" ]; then
    if [ ! -d "$SDK_HOME/gnu/riscv64-zephyr-elf" ]; then
        fetch "$SDK_REL/$_riscv_asset" "$DL_DIR/$_riscv_asset"
        mkdir -p "$SDK_HOME/gnu"
        tar -xJf "$DL_DIR/$_riscv_asset" -C "$SDK_HOME/gnu"
    else
        step_skip "50-③ riscv64 工具链"
    fi
fi

# 注册（幂等：setup.sh -c 可重跑）
if [ ! -f "$SDK_HOME/cmake-user-package-repo/.repo-registry" ]; then
    (cd "$SDK_HOME" && ./setup.sh -c) || _die "SDK setup.sh -c 失败"
else
    step_skip "50-④ setup.sh -c（已注册）"
fi
_ok "50 SDK 就绪（$SDK_HOME；hosttools 含 cmake/ninja/gperf/dtc——PATH 见 env.sh）"
