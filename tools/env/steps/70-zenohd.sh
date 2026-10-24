# SPDX-License-Identifier: Apache-2.0
# steps/70-zenohd.sh · zenohd 1.10.1（PC/设备侧路由器——用户档与开发者档共用）。
# 路线 B：eclipse-zenoh GitHub releases 官方 standalone 二进制（x86_64/aarch64 双发布——
# aarch64 实测 ✅ checklist §12）；cargo 路线 A 仅作文档备选（编译慢，不入自动路线）。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

_log "70 · zenohd ${PIN_ZENOHD_VER}（${ARCH}）"
if [ -x "$TOOLS_DIR/zenohd" ]; then
    step_skip "70 zenohd（$TOOLS_DIR/zenohd 在位）"
    exit 0
fi

_asset="zenoh-${PIN_ZENOHD_VER}-${ARCH}-unknown-linux-gnu-standalone.zip"
fetch "https://github.com/eclipse-zenoh/zenoh/releases/download/${PIN_ZENOHD_VER}/$_asset" \
    "$DL_DIR/$_asset"
_d="$(mktemp -d)"
unzip -q -o "$DL_DIR/$_asset" -d "$_d" || _die "unzip 失败（安装 unzip 或手工解包 $_asset）"
_bin="$(find "$_d" -type f -name zenohd | head -1)"
[ -n "$_bin" ] || _die "zip 内未找到 zenohd 二进制"
install -D -m 0755 "$_bin" "$TOOLS_DIR/zenohd"
rm -rf "$_d"
"$TOOLS_DIR/zenohd" --version | head -1 || _die "zenohd 运行失败（glibc 兼容检查）"
_ok "70 zenohd（$TOOLS_DIR/zenohd；启动命令见 tools/board/README.md）"
