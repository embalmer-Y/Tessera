# SPDX-License-Identifier: Apache-2.0
# steps/65-llvm.sh · clang 18.1.8 用户态回退（无 sudo/发行版无 clang-18 时——checklist §7 路线 B）。
# 优先级：系统 clang ≥18（apt 路线已装）> LLVM 官方 tarball 解包 ~/project/tools/llvm-18.1.8。
# tarball 兼容性：依赖 libtinfo.so.5（新发行版缺）——同场解包 libtinfo5 deb 并落位 llvm lib/。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

if cmd_version_at_least clang 18 && have_cmd wasm-ld; then
    step_skip "65 clang（系统已装 ≥18）"
    exit 0
fi

if [ -x "$LLVM_ROOT/bin/clang" ]; then
    step_skip "65 clang（$LLVM_ROOT 已在位）"
    exit 0
fi

_log "65 · clang ${PIN_LLVM_VER} 用户态 tarball（无 sudo 回退）"
case "$ARCH" in
    x86_64)  _llvm_asset="clang+llvm-${PIN_LLVM_VER}-x86_64-linux-gnu-ubuntu-18.04.tar.xz" ;;
    aarch64) _llvm_asset="clang+llvm-${PIN_LLVM_VER}-aarch64-linux-gnu.tar.xz" ;;  # ⚠ aarch64 资产名未实测（checklist §7）
esac
fetch "https://github.com/llvm/llvm-project/releases/download/llvmorg-${PIN_LLVM_VER}/$_llvm_asset" \
    "$DL_DIR/$_llvm_asset"
mkdir -p "$TOOLS_DIR"
tar -xJf "$DL_DIR/$_llvm_asset" -C "$TOOLS_DIR"
mv "$TOOLS_DIR/clang+llvm-${PIN_LLVM_VER}-"* "$LLVM_ROOT"

# libtinfo5 兼容（Ubuntu ≥20 缺 libtinfo5）：deb 解包落位 llvm lib/（免 patchelf——tarball rpath=$ORIGIN/../lib）
if ! ldconfig -p 2>/dev/null | grep -q libtinfo.so.5 && ! ls "$LLVM_ROOT/lib/"libtinfo.so.5* >/dev/null 2>&1; then
    _log "补 libtinfo5（deb 用户态解包）"
    _d="$(mktemp -d)"; cd "$_d"
    apt-get download libtinfo5 >/dev/null 2>&1 \
        || apt-get download libtinfo6 >/dev/null 2>&1 \
        || _warn "libtinfo 下载失败——若 clang 运行报 libtinfo.so.5 缺失，手工处理"
    for deb in ./*.deb; do dpkg -x "$deb" "$_d/x"; done
    find "$_d/x" -name 'libtinfo.so.5*' -exec cp {} "$LLVM_ROOT/lib/" \; 2>/dev/null || true
    cd - >/dev/null; rm -rf "$_d"
fi

mkdir -p "$HOME/.local/bin"
for b in clang clang++ wasm-ld clang-format; do
    [ -e "$LLVM_ROOT/bin/$b" ] && ln -sf "$LLVM_ROOT/bin/$b" "$HOME/.local/bin/$b"
done
PATH="$HOME/.local/bin:$PATH" clang --version | head -1 || _die "clang tarball 运行失败"
_ok "65 clang ${PIN_LLVM_VER}（$LLVM_ROOT；软链 ~/.local/bin）"
