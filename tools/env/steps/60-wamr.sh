# SPDX-License-Identifier: Apache-2.0
# steps/60-wamr.sh · WAMR 2.4.5（仓外源码；构建期 TS_WAMR_DIR 注入——开发者档）。
# version.h 预生成 + chmod 444 只读屏障（教训 21⑤——twister 并行 configure_file 竞态根治）。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

_log "60 · WAMR ${PIN_WAMR_REF}"
if [ ! -d "$WAMR_DIR/.git" ]; then
    git clone --depth 1 --branch "$PIN_WAMR_REF" \
        https://github.com/bytecodealliance/wasm-micro-runtime.git "$WAMR_DIR" \
        || _die "WAMR clone 失败（网络受限时用 --proxy 配置代理后重跑）"
else
    step_skip "60-① WAMR clone"
fi

# version.h：仓库自带但屏障必须显式落位（twister 并行 configure_file 竞态根治——教训 21⑤；
# 可写 = 屏障缺失即重生成 + 444）
if [ -w "$WAMR_DIR/core/version.h" ] || [ ! -f "$WAMR_DIR/core/version.h" ]; then
    _cmake="$FW_VENV/bin/cmake"; have_cmd "$_cmake" 2>/dev/null || _cmake="cmake"
    chmod 644 "$WAMR_DIR/core/version.h" 2>/dev/null || true
    $_cmake -DWAMR_ROOT_DIR="$WAMR_DIR" -P "$WAMR_DIR/build-scripts/version.cmake" \
        || _die "WAMR version.h 生成失败"
    chmod 444 "$WAMR_DIR/core/version.h"
    _ok "60-② version.h 生成 + 只读屏障（444）"
else
    step_skip "60-② version.h（444 屏障在位）"
fi
