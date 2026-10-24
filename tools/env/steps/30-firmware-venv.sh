# SPDX-License-Identifier: Apache-2.0
# steps/30-firmware-venv.sh · 固件 Python venv（west/twister 面；开发者档）。
# 关键钉版：cmake<4 装入 venv（发行版 cmake 4.x 与 Zephyr 4.5 存在兼容风险——CI=3.28 口径）。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

_log "30 · 固件 venv（$FW_VENV）"
mkdir -p "$WEST_WS"
if [ ! -x "$FW_VENV/bin/python" ]; then
    if have_cmd uv; then
        uv venv "$FW_VENV" --python "$PIN_PY_VENV" >/dev/null
    else
        python3 -m venv "$FW_VENV" 2>/dev/null || _die "venv 创建失败——安装 uv 后重跑"
    fi
fi

if have_cmd uv; then
    _fw_install() { uv pip install --python "$FW_VENV/bin/python" -q "$@"; }
else
    _fw_install() { "$FW_VENV/bin/pip" install -q "$@"; }
fi

"$FW_VENV/bin/west" --version >/dev/null 2>&1 || _fw_install west
"$FW_VENV/bin/cmake" --version >/dev/null 2>&1 || _fw_install "cmake==${PIN_CMAKE_VER}"
cmd_version_at_least "$FW_VENV/bin/cmake" 3.20 || _fw_install "cmake==${PIN_CMAKE_VER}"
"$FW_VENV/bin/esptool" version 2>/dev/null | grep -q "$PIN_ESPTOOL_VER" || _fw_install "esptool==${PIN_ESPTOOL_VER}"

# zephyr requirements（west update 后树才在位——40 步末尾再补跑一次本步）
if [ -f "$WEST_WS/zephyr/scripts/requirements.txt" ]; then
    "$FW_VENV/bin/python" -c "import elftools, yaml" 2>/dev/null \
        || _fw_install -r "$WEST_WS/zephyr/scripts/requirements.txt"
else
    _info "zephyr 树尚未就位——requirements 将由 40 步完成后补跑"
fi
step_skip "30 固件 venv（west + cmake $( "$FW_VENV/bin/cmake" --version | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' ) + esptool）"
