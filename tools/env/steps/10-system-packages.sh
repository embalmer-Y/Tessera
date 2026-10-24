# SPDX-License-Identifier: Apache-2.0
# steps/10-system-packages.sh · 系统包（Ubuntu/Debian apt；sudo 交互——owner 指令）。
# 两档包集：user（产品用户最小面）/ dev（开发者全链）。sudo 不可用时报错并给出指引
# （--skip-sudo 时打警告跳过——编译器类由 65-llvm 用户态回退兜底）。
# 用法：TIER=user|dev（install.sh 注入；缺省 dev）。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

TIER="${TIER:-dev}"

_base_pkgs=(git curl wget file xz-utils python3 python3-venv python3-pip ca-certificates)
_dev_pkgs=(build-essential gcc g++ gperf pkg-config libncurses-dev device-tree-compiler patch ccache)
[ "$ARCH" = "x86_64" ] && _dev_pkgs+=(gcc-multilib g++-multilib)   # 32 位 native_sim；aarch64 走 /64 口径
# clang：优先 18.1 系（CI 对齐）；发行版无 18 时装默认 clang（65 步 tarball 可钉 18.1.8）
if apt-cache show clang-18 >/dev/null 2>&1; then
    _dev_pkgs+=(clang-18 lld-18)
else
    _warn "发行版无 clang-18——装默认 clang（如需 18.1.8 精确对齐，运行 steps/65-llvm.sh）"
    _dev_pkgs+=(clang)
fi

if [ "$TIER" = "dev" ]; then pkgs=("${_base_pkgs[@]}" "${_dev_pkgs[@]}"); else pkgs=("${_base_pkgs[@]}"); fi

_need_install=0
for p in "${pkgs[@]}"; do
    dpkg -s "$p" >/dev/null 2>&1 || { _need_install=1; break; }
done
if [ "$_need_install" -eq 0 ]; then
    step_skip "10 系统包（$TIER 档全部在位）"
    exit 0
fi

_log "10 · 系统包（$TIER 档 · ${#pkgs[@]} 项 · apt 路线需要 sudo）"
ensure_sudo || {
    if [ "${SKIP_SUDO:-0}" = "1" ]; then
        _warn "SKIP_SUDO=1：跳过系统包（开发者档编译器面由 65-llvm.sh 用户态兜底；cmake/ninja 由 SDK hosttools 供给）"
        exit 0
    fi
    _die "系统包安装需要 root——交互终端重跑将提示输入密码，或以 root 运行本安装程序"
}
# shellcheck disable=SC2086
$SUDO apt-get update -y $(apt_proxy_opts)
# shellcheck disable=SC2086
$SUDO apt-get install -y --no-install-recommends $(apt_proxy_opts) "${pkgs[@]}"
_ok "10 系统包安装完成（apt）"
