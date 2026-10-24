# SPDX-License-Identifier: Apache-2.0
# steps/40-west-workspace.sh · west 工作区（Zephyr 钉版 + blobs + zenoh-pico 接入三步 + TLS 补丁）。
# 依据 docs/env-rebuild-checklist.md §3（唯一权威配方——本步为其机械化）。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

_log "40 · west 工作区（Zephyr ${PIN_ZEPHYR_REF}）"
WEST="$FW_VENV/bin/west"
[ -x "$WEST" ] || _die "固件 venv 未就绪（先跑 30 步）"
cd "$WEST_WS"

# --- ① init（幂等：.west/config 在位即跳过） ---
if [ ! -f .west/config ]; then
    rm -rf .west manifest-repo
    _log "west init（Zephyr ${PIN_ZEPHYR_REF}）"
    $WEST init -m https://github.com/zephyrproject-rtos/zephyr --mr "$PIN_ZEPHYR_REF" . \
        || _die "west init 失败（网络受限时用 --proxy 配置代理后重跑）"
else
    step_skip "40-① west init（.west 在位）"
fi

# --- ② update（失败集合断点续跑——重试环，checklist §12 ARM 机纪律） ---
if [ ! -d "$WEST_WS/zephyr/scripts" ] || ! $WEST list -f json >/dev/null 2>&1 || \
   [ -z "$(ls -A "$WEST_WS/modules" 2>/dev/null)" ]; then
    _log "west update（大下载 ~8GB；失败自动重试）"
    ok=0
    for i in $(seq 1 10); do
        $WEST update && { ok=1; break; }
        _warn "west update 失败（第 $i 次）——断点续跑重试"
        sleep 8
    done
    [ $ok -eq 1 ] || _die "west update 最终失败（网络通道/磁盘检查后重跑本步）"
else
    step_skip "40-② west update（工作区已就位）"
fi

# --- ③ hal_espressif blobs（WiFi 固件包——不随 west update 拉取，教训 30） ---
_n_blobs() { find "$WEST_WS/modules/hal/espressif" \( -name '*.a' -o -name '*.bin' \) 2>/dev/null | wc -l; }
if [ "$(_n_blobs)" -lt 60 ]; then
    _log "blobs fetch hal_espressif（WiFi blobs，~71 件）"
    ok=0
    for i in 1 2 3; do $WEST blobs fetch hal_espressif && { ok=1; break; }; sleep 5; done
    [ $ok -eq 1 ] || _warn "west blobs fetch 失败——回退 tools/board/fetch_blobs.py（ghfast 通道）"
    [ $ok -eq 0 ] && python3 "$REPO_DIR/tools/board/fetch_blobs.py" || true
    [ "$(_n_blobs)" -ge 60 ] || _die "blobs 未齐（$(_n_blobs)/71）——网络通道检查后重跑"
else
    step_skip "40-③ blobs（$(_n_blobs) 件在位）"
fi

# --- ④ zephyr requirements 补跑（树就位后） ---
"$FW_VENV/bin/python" -c "import elftools, yaml" 2>/dev/null || {
    have_cmd uv && uv pip install --python "$FW_VENV/bin/python" -q -r "$WEST_WS/zephyr/scripts/requirements.txt" \
        || "$FW_VENV/bin/pip" install -q -r "$WEST_WS/zephyr/scripts/requirements.txt"
}

# --- ⑤ zenoh-pico 接入三步（不在 mainline manifest——checklist §3 实测更正） ---
ZP="$WEST_WS/zenoh-pico"
if [ ! -d "$ZP/.git" ]; then
    _log "zenoh-pico ${PIN_ZENOH_PICO_REF} 接入 ①/③：clone"
    git clone --depth 1 --branch "$PIN_ZENOH_PICO_REF" https://github.com/eclipse-zenoh/zenoh-pico.git "$ZP"
else
    step_skip "40-⑤a zenoh-pico clone"
fi

# ② config.h 生成 + 剥 Kconfig 管辖宏（剥光触发上游笔误分支编译失败——dev-env §7-2）。
#    剥 13 个 = checklist 12 个 + AUTO_RECONNECT（R5-V 起 Kconfig/补丁管辖——tls.patch
#    config.h hunk 以「AUTO_RECONNECT 行已剥」为基线；2026-10-24 实证回填）。
if [ ! -f "$ZP/include/zenoh-pico/config.h" ]; then
    _log "zenoh-pico 接入 ②：config.h 生成（cmake）+ 剥 Kconfig 管辖宏 ×13"
    _cmake="$FW_VENV/bin/cmake"; have_cmd "$_cmake" || _cmake="cmake"
    _tmp="$(mktemp -d)"
    $_cmake -S "$ZP" -B "$_tmp" >/dev/null 2>&1 || true
    [ -f "$_tmp/include/zenoh-pico/config.h" ] || _die "zenoh-pico config.h 生成失败（cmake: $_cmake）"
    sed -i -E '/^#define Z_FEATURE_(MULTI_THREAD|PUBLICATION|SUBSCRIPTION|QUERYABLE|QUERY|LINK_TCP|LINK_UDP_UNICAST|LINK_SERIAL|LINK_UDP_MULTICAST|LINK_WS|RAWETH_TRANSPORT|SCOUTING|AUTO_RECONNECT)[[:space:]]/d' \
        "$_tmp/include/zenoh-pico/config.h"
    install -D "$_tmp/include/zenoh-pico/config.h" "$ZP/include/zenoh-pico/config.h"
    rm -rf "$_tmp"
else
    step_skip "40-⑤b config.h（已生成）"
fi

# ③ TLS 补丁（板级基线 CONFIG_ZENOH_PICO_LINK_TLS=y 必施——不施则 Kconfig 未定义符号 abort）
_TLS_PATCH="$REPO_DIR/firmware/module/tessera/ext/zenoh-pico-tls.patch"
if patch -p1 -d "$ZP" --dry-run -s < "$_TLS_PATCH" >/dev/null 2>&1; then
    _log "zenoh-pico 接入 ③：TLS 补丁"
    patch -p1 -d "$ZP" -s < "$_TLS_PATCH" \
        || _die "TLS 补丁施用失败（检查 zenoh-pico 版本 = ${PIN_ZENOH_PICO_REF}）"
elif grep -q "Z_FEATURE_LINK_TLS" "$ZP/include/zenoh-pico/config.h" 2>/dev/null; then
    step_skip "40-⑤c TLS 补丁（已施）"
else
    _die "TLS 补丁既不能干净施用也未见已施痕迹（zenoh-pico 树状态异常——重克隆后重跑）"
fi
_ok "40 west 工作区就绪（Zephyr ${PIN_ZEPHYR_REF} + blobs + zenoh-pico+TLS）"
