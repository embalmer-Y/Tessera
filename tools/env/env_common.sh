# SPDX-License-Identifier: Apache-2.0
# env_common.sh · Tessera 安装程序公共库（tools/env/ · DEC-79——由 install.sh 与 steps/* source）。
#
# 定位：面向用户的自动化安装程序（用户下载即用）+ 开发者档（--dev 全链）。
# 设计要点：
#   - 钉版纪律（docs/std/versioning.md §4）：外部依赖钉具体版本，常量集中在 PINS。
#   - 架构：x86_64 / aarch64 双支持（SDK/LLVM/zenohd 资产名按架构分派）。
#   - 网络：不做绕行工程——代理经 --proxy URL 或 HTTPS_PROXY 环境配置（git/wget/curl/pip 全继承）。
#   - sudo（owner 指令 2026-10-24）：系统包安装需要 root——交互终端向用户索要 sudo 密码
#     （sudo -v 缓存凭证）；管道/自动化场景支持 sudo -S 从 stdin 读密码；两者皆不可用时
#     转用户态回退（65-llvm 等）或明确报错。
#   - 凭据红线（AGENTS §6/军规）：API key / WiFi 密码只经交互输入或 --config 文件导入，
#     落盘仅 600 仓外文件；绝不入仓、绝不回显。
#   - 幂等：每步以真实状态探测判定已完成即跳过（无 marker 文件——状态漂移免疫）。

# ---------- 钉版常量（与 README「依赖与钉版」表一致；测试面守恒） ----------
readonly PIN_ZEPHYR_REF="v4.5.0-rc1"
readonly PIN_SDK_VER="1.0.1"
readonly PIN_WAMR_REF="WAMR-2.4.5"
readonly PIN_ZENOH_PICO_REF="1.10.1"
readonly PIN_ESPTOOL_VER="5.4.0"
readonly PIN_ZENOHD_VER="1.10.1"
readonly PIN_LLVM_VER="18.1.8"
readonly PIN_CMAKE_VER="3.31.6"        # venv 内钉 <4（发行版 cmake 4.x 与 Zephyr 4.5 兼容风险）
readonly PIN_PY_VENV="3.12"           # venv 保守口径（agent/zephyr 依赖全 wheel）
readonly PIN_DEFAULT_MODEL="anthropic:MiniMax-M3"   # 出厂默认模型串（用户可覆盖）

# ---------- 路径约定（docs/env-rebuild-checklist.md §0） ----------
PROJ="${TESSERA_HOME:-$HOME/project}"
REPO_DIR="$PROJ/Tessera"
WEST_WS="$PROJ/zephyrproject"
FW_VENV="$WEST_WS/.venv"
AGENT_VENV="$PROJ/agent-venv"
SDK_HOME="$HOME/zephyr-sdk-${PIN_SDK_VER}"
WAMR_DIR="$PROJ/deps/wamr"
DL_DIR="$PROJ/deps/dl"
TOOLS_DIR="$PROJ/tools"
ENV_SH="$PROJ/logs/env.sh"
LLVM_ROOT="$PROJ/tools/llvm-${PIN_LLVM_VER}"
ENV_INSTALLER_DIR=""   # install.sh 运行时定位（setup_env.sh 注入；用于步骤定位仓库）

# ---------- 日志 ----------
_log() { printf '\033[1;34m[tessera-installer]\033[0m %s\n' "$*"; }
_info() { printf '            %s\n' "$*"; }
_ok()  { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
_warn() { printf '\033[1;33m  ⚠\033[0m %s\n' "$*" >&2; }
_die() { printf '\033[1;31m  ✗ FAIL:\033[0m %s\n' "$*" >&2; exit 1; }

# ---------- 架构 ----------
detect_arch() {
    local m
    m="$(uname -m)"
    case "$m" in
        x86_64|amd64) echo "x86_64" ;;
        aarch64|arm64) echo "aarch64" ;;
        *) _die "不支持的平台：$m（本安装程序仅支持 Linux x86_64 / aarch64）" ;;
    esac
}
ARCH="$(detect_arch)"

# ---------- 代理 ----------
# 入口脚本解析 --proxy URL 后调 apply_proxy；未指定时继承用户既有 http(s)_proxy 环境。
PROXY_URL="${TESSERA_PROXY:-${https_proxy:-${http_proxy:-}}}"
apply_proxy() {
    [ -n "$PROXY_URL" ] || return 0
    export http_proxy="$PROXY_URL" https_proxy="$PROXY_URL" all_proxy="$PROXY_URL"
    export NO_PROXY="${NO_PROXY:-localhost,127.0.0.1,::1}"
    _info "网络代理：$PROXY_URL"
}
apt_proxy_opts() {  # apt 经 sudo 时不继承环境——需要显式代理选项（无代理输出空）
    [ -n "$PROXY_URL" ] || return 0
    printf ' -o Acquire::http::Proxy=%s -o Acquire::https::Proxy=%s' "$PROXY_URL" "$PROXY_URL"
}

# ---------- 下载 ----------
fetch() {  # fetch <url> <dest>：断点续传 + 重试（wget 优先，curl 回退；代理经环境继承）
    local url="$1" dest="$2" i
    mkdir -p "$(dirname "$dest")"
    for i in 1 2 3 4 5; do
        if command -v wget >/dev/null 2>&1; then
            wget -q -c --timeout=90 --tries=3 "$url" -O "$dest" && return 0
        elif command -v curl >/dev/null 2>&1; then
            curl -sfL --retry 3 -C - "$url" -o "$dest" && return 0
        else
            _die "wget 与 curl 均不可用（请先安装其一）"
        fi
        _warn "下载失败（第 $i 次），10s 后重试：$url"
        sleep 10
    done
    _die "下载最终失败：$url（网络受限时可用 --proxy http://127.0.0.1:7890 配置代理）"
}

# ---------- sudo（owner 指令：执行时向用户索要 root 密码） ----------
# 返回 0 = root 可用（SUDO 置空=已是 root，或 "sudo"）；返回 1 = 不可用（调用方走回退/报错）。
SUDO=""
ensure_sudo() {
    if [ "$(id -u)" -eq 0 ]; then SUDO=""; return 0; fi
    sudo -n true 2>/dev/null && { SUDO="sudo"; return 0; }
    if [ -t 0 ]; then
        _log "部分组件需要 root 权限安装系统包——请在下方提示处输入 sudo（root）密码："
        sudo -v && { SUDO="sudo"; return 0; }
    else
        # 管道/自动化场景（如 echo <密码> | ./install.sh）：sudo -S 从 stdin 读
        _log "非交互会话：将从 stdin 读取 sudo 密码（sudo -S）"
        if sudo -S -v </dev/stdin 2>/dev/null; then SUDO="sudo"; return 0; fi
    fi
    _warn "sudo 凭证不可用"
    return 1
}

# ---------- 幂等探测 ----------
have_cmd() { command -v "$1" >/dev/null 2>&1; }
cmd_version_at_least() {  # <bin> <主.次> 粗粒度比较
    local bin="$1" need="$2" have
    have_cmd "$bin" || return 1
    have="$("$bin" --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+' | head -1)"
    [ -n "$have" ] || return 1
    awk -v h="$have" -v n="$need" 'BEGIN{split(h,a,".");split(n,b,".");exit !(a[1]>b[1] || (a[1]==b[1] && a[2]>=b[2]))}'
}
step_skip() { _ok "$*"; }
