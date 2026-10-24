#!/usr/bin/env bash
# SPDX-License-Identifier: Apache-2.0
# install.sh · Tessera 自动化安装程序（面向用户 · DEC-79——V0.16.0）
#
# 一键在 Linux（x86_64 / aarch64）上安装 Tessera：
#   标准档（产品使用）＝ Agent 运行环境（venv + 依赖）+ 本机 zenohd 路由 + esptool
#                          + 用户配置（LLM 端点/API key 运行时输入或配置文件导入）
#   开发者档（--dev）    ＝ 标准档 + 固件全链（west 工作区/Zephyr SDK/WAMR/zenoh-pico+TLS/
#                          twister 回归面）
#
# 用法：
#   ./install.sh                      # 交互式标准档（LLM 配置逐项询问——密钥隐藏输入）
#   ./install.sh --dev                # 开发者档（系统包安装时会提示输入 sudo 密码）
#   ./install.sh --config FILE        # 非交互：从 KEY=VALUE 配置文件导入（见 README）
#   ./install.sh --proxy URL          # 网络代理（如 http://127.0.0.1:7890）
#   ./install.sh --skip-sudo          # 无 root 环境（编译器转用户态回退）
#   ./install.sh --step NAME          # 只跑指定步骤（调试/补装；NAME 如 40-west-workspace）
#
# 凭据红线：API key / WiFi 密码只经交互输入或 --config 文件进入；落盘仅 600 仓外文件，绝不入仓。
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/env_common.sh"

TIER=user
CONFIG_FILE=""
STEP_ONLY=""
while [ $# -gt 0 ]; do
    case "$1" in
        --dev)       TIER=dev ;;
        --config)    CONFIG_FILE="${2:?--config 需要文件参数}"; shift ;;
        --proxy)     PROXY_URL="${2:?--proxy 需要 URL 参数}"; TESSERA_PROXY="$PROXY_URL"; shift ;;
        --skip-sudo) SKIP_SUDO=1 ;;
        --step)      STEP_ONLY="${2:?--step 需要步骤名}"; shift ;;
        -h|--help)   sed -n '3,20p' "$0"; exit 0 ;;
        *)           _die "未知参数：$1（--help 查看用法）" ;;
    esac
    shift
done
export TIER CONFIG_FILE SKIP_SUDO
apply_proxy

# 定位仓库：本安装程序即仓库内（tools/env/）→ 直接用；否则先 clone（步骤 20）
if git -C "$HERE/../../" rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_DIR="$(git -C "$HERE/../../" rev-parse --show-toplevel)"
fi
export ENV_INSTALLER_DIR="$HERE"

cat <<'BANNER'
────────────────────────────────────────────────────────────
  Tessera 自动化安装程序（Linux x86_64 / aarch64）
  标准档 = Agent + zenohd 路由 + 烧录工具 + 用户配置
  开发者档（--dev）追加固件全链（Zephyr SDK / WAMR / 回归面）
────────────────────────────────────────────────────────────
BANNER
_log "平台：$(uname -m) · $(. /etc/os-release && echo "$PRETTY_NAME") · 安装档：$TIER"

run_step() {
    _log "▶ 步骤 $1"
    bash "$HERE/steps/$1.sh"
}

# ---- 标准档 ----
if [ -n "$STEP_ONLY" ]; then
    run_step "$STEP_ONLY"
    exit 0
fi
run_step 10-system-packages
run_step 20-dirs-repo
run_step 25-agent-venv
run_step 70-zenohd
run_step 85-user-config

# ---- 开发者档追加 ----
if [ "$TIER" = "dev" ]; then
    run_step 30-firmware-venv
    run_step 40-west-workspace
    run_step 50-zephyr-sdk
    run_step 60-wamr
    # clang 兜底（apt 已装则秒过；无 sudo 发行版走 tarball 用户态）
    run_step 65-llvm
fi

_log "安装完成 ✅（$TIER 档）"
_info "验证：bash $HERE/verify_env.sh（标准档 ①③④⑤ / 开发者档全量）"
[ "$TIER" = "user" ] && _info "启动 Agent：source ~/project/logs/env.sh && ~/project/agent-venv/bin/tessera-agent --help"
exit 0
