#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# verify_env.sh · 安装结果分层验证（对应 docs/env-rebuild-checklist.md §11；DEC-79）。
# 开发者档全量 ①-⑤；标准档跑 ③④⑤（twister/板级构建属开发者面——缺依赖自动跳过并注明）。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/env_common.sh"

RESULTS=()
record() { RESULTS+=("$1"); _log "$1"; }
skip()   { RESULTS+=("SKIP：$1"); _warn "跳过：$1"; }

export ZEPHYR_EXTRA_MODULES="$REPO_DIR/firmware/module/tessera;$WEST_WS/zenoh-pico"
export TS_WAMR_DIR="$WAMR_DIR"
[ -f "$ENV_SH" ] && . "$ENV_SH" || true

_log "验证 ① · twister 回归（native_sim 17 套件——开发者面）"
if [ -x "$FW_VENV/bin/west" ] && [ -d "$WEST_WS/zephyr" ] && [ -n "${TS_WAMR_DIR:-}" ] && [ -d "$TS_WAMR_DIR" ]; then
    _plat="native_sim"                                    # x86_64 = 32 位正典口径
    [ "$ARCH" = "aarch64" ] && _plat="native_sim/native/64"  # aarch64 无 ilp32 multilib（checklist §12）
    if "$FW_VENV/bin/python" "$WEST_WS/zephyr/scripts/twister" \
        -p "$_plat" -T "$REPO_DIR/firmware/tests" \
        --outdir /tmp/twister-verify \
        --extra-args="ZEPHYR_EXTRA_MODULES=$ZEPHYR_EXTRA_MODULES" ; then
        record "① twister PASS"
    else
        record "① twister FAIL（详见 /tmp/twister-verify）"
    fi
else
    skip "① twister（开发者档依赖未装）"
fi

_log "验证 ② · 板级构建（atkbench @ dnesp32s3b——需 WiFi 凭据 + xtensa SDK）"
if [ -n "${TS_WIFI_SSID:-}" ] && [ -d "$SDK_HOME/gnu/xtensa-espressif_esp32s3_zephyr-elf" ]; then
    (cd "$WEST_WS" && "$FW_VENV/bin/west" build -p always -b dnesp32s3b/esp32s3/procpu \
        "$REPO_DIR/firmware/tests/atkbench" -d "$PROJ/builds/verify-atk" -- \
        -DATKBENCH_WIFI_SSID="$TS_WIFI_SSID" -DATKBENCH_WIFI_PASSWORD="${TS_WIFI_PASSWORD:-}") \
        && record "② 板级构建 PASS（$PROJ/builds/verify-atk）" \
        || record "② 板级构建 FAIL"
else
    skip "② 板级构建（WiFi 凭据或 xtensa 工具链未就位——见 ~/project/logs/env.sh）"
fi

_log "验证 ③ · Agent 回归（pytest + ruff）"
if [ -x "$AGENT_VENV/bin/python" ]; then
    (cd "$REPO_DIR/agent" && "$AGENT_VENV/bin/python" -m pytest tests/ -q \
        && "$AGENT_VENV/bin/python" -m ruff check .) \
        && record "③ Agent 回归 PASS" \
        || record "③ Agent 回归 FAIL"
else
    skip "③ Agent 回归（agent-venv 未装）"
fi

_log "验证 ④ · repo 检查（编码/无 BOM + 安全合同机械检查）"
"$AGENT_VENV/bin/python" -m pytest "$REPO_DIR/firmware/tests/pytest" -q 2>/dev/null \
    && python3 "$REPO_DIR/firmware/tests/safety_check/check_safety_contract.py" \
    && record "④ repo 检查 PASS" \
    || skip "④ repo 检查（组件缺失或未装——标准档可后补）"

_log "验证 ⑤ · skills 同步一致性"
if [ -x "$AGENT_VENV/bin/python" ]; then
    (cd "$REPO_DIR/agent" && "$AGENT_VENV/bin/python" -m tessera_agent.skills.sync_check) \
        && record "⑤ skills 同步 PASS" \
        || record "⑤ skills 同步 FAIL（源文档变更后需 --update）"
else
    skip "⑤ skills 同步（agent-venv 未装）"
fi

_log "验证 ⑥⑦ · 板级冒烟 / NVD 全链（需真板 + LLM 凭据——tools/board/README.md「典型编排」）"
skip "⑥⑦ 真机面（有板时按 tools/board/README.md 手工执行）"

echo
_log "===== 验证汇总 ====="
printf '  %s\n' "${RESULTS[@]}"
