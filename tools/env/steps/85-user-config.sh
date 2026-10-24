# SPDX-License-Identifier: Apache-2.0
# steps/85-user-config.sh · 用户配置装配（面向用户安装程序的核心步——DEC-79）。
# 来源（优先级）：--config 文件导入（KEY=VALUE，可带引号/#注释）> 交互逐项询问（密钥隐藏输入，
# 无回显）> 可选项留空跳过。落盘两件（均 600 / 不入仓）：
#   ~/project/logs/env.sh     —— 凭据与运行环境变量（ANTHROPIC_*/TS_WIFI_* + PATH/构建变量）
#   <repo>/agent/config.toml  —— Agent 运行配置（gitignored；分节表纪律——ARM 机实测两坑）
# 绝不覆盖已存在配置（幂等 = 检测在位即只补缺项提示）；凭据绝不回显、绝不出现在日志。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

_log "85 · 用户配置（LLM 端点 / API key / WiFi〔可选〕）"

# ---- 配置键收集 ----
CFG_ANTHROPIC_BASE_URL="${CFG_ANTHROPIC_BASE_URL:-}"
CFG_ANTHROPIC_API_KEY="${CFG_ANTHROPIC_API_KEY:-}"
CFG_LLM_MODEL="${CFG_LLM_MODEL:-}"
CFG_WIFI_SSID="${CFG_WIFI_SSID:-}"
CFG_WIFI_PASSWORD="${CFG_WIFI_PASSWORD:-}"
CFG_ZENOHD_TCP_PORT="${CFG_ZENOHD_TCP_PORT:-9957}"

load_config_file() {  # load_config_file <file>：KEY=VALUE 导入（CFG_* 命名空间）
    local f="$1" k v
    [ -f "$f" ] || _die "配置文件不存在：$f"
    while IFS= read -r line || [ -n "$line" ]; do
        line="${line%$'\r'}"
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ "$line" =~ ^[[:space:]]*$ ]] && continue
        k="${line%%=*}"; v="${line#*=}"
        [[ "$v" =~ ^\".*\"$ ]] && v="${v#\"}" && v="${v%\"}"
        case "$k" in
            ANTHROPIC_BASE_URL) CFG_ANTHROPIC_BASE_URL="$v" ;;
            ANTHROPIC_API_KEY)  CFG_ANTHROPIC_API_KEY="$v" ;;
            TESSERA_LLM_MODEL)  CFG_LLM_MODEL="$v" ;;
            TS_WIFI_SSID)       CFG_WIFI_SSID="$v" ;;
            TS_WIFI_PASSWORD)   CFG_WIFI_PASSWORD="$v" ;;
            ZENOHD_TCP_PORT)    CFG_ZENOHD_TCP_PORT="$v" ;;
            *) _warn "配置文件未知键（忽略）：$k" ;;
        esac
    done < "$f"
    _ok "配置已导入：$f"
}

ask() {  # ask <提示> <变量名> [secret]
    local prompt="$1" var="$2" secret="${3:-}" cur ans
    cur="${!var}"
    if [ -n "$cur" ]; then return 0; fi
    if [ ! -t 0 ]; then
        _warn "非交互会话且 $var 未提供（--config 或环境变量补齐后重跑，或留空继续）"
        return 0
    fi
    if [ "$secret" = "secret" ]; then
        printf '  %s [输入不回显]：' "$prompt" >&2
        read -rs ans; printf '\n' >&2
    else
        printf '  %s：' "$prompt" >&2
        read -r ans
    fi
    printf -v "$var" '%s' "$ans"
}

# 交互/导入双通道（install.sh 已解析 --config 到 CONFIG_FILE）
[ -n "${CONFIG_FILE:-}" ] && load_config_file "$CONFIG_FILE"
if [ "${INTERACTIVE:-1}" = "1" ]; then
    _info "Agent 的 LLM 服务配置（Anthropic 兼容端点——例如 MiniMax 等；密钥只入本机 600 文件）"
    ask "LLM API 端点 URL（ANTHROPIC_BASE_URL，直接回车 = 使用环境已有值/跳过）" CFG_ANTHROPIC_BASE_URL
    ask "LLM API Key（ANTHROPIC_API_KEY）" CFG_ANTHROPIC_API_KEY secret
    ask "模型串（TESSERA_LLM_MODEL，回车 = 默认 ${PIN_DEFAULT_MODEL}）" CFG_LLM_MODEL
    _info "板卡 WiFi 凭据（可选——用于固件构建期注入；没有板卡直接回车跳过）"
    ask "WiFi SSID（TS_WIFI_SSID，可选）" CFG_WIFI_SSID
    ask "WiFi 密码（TS_WIFI_PASSWORD，可选）" CFG_WIFI_PASSWORD secret
fi
[ -n "$CFG_LLM_MODEL" ] || CFG_LLM_MODEL="$PIN_DEFAULT_MODEL"

# ---- 落盘 ①：env.sh（600；已存在则不覆盖——只提示补缺） ----
mkdir -p "$(dirname "$ENV_SH")"
if [ -f "$ENV_SH" ]; then
    step_skip "85-① env.sh（$ENV_SH 已存在——不覆盖；如需重置请手工删除后重跑）"
else
    {
        echo "# Tessera 运行环境（安装程序生成 $(date '+%F %T')；600 仓外——凭据红线不入仓）"
        echo "export ZEPHYR_EXTRA_MODULES=\"$REPO_DIR/firmware/module/tessera;$WEST_WS/zenoh-pico\""
        echo "export TS_WAMR_DIR=\"$WAMR_DIR\""
        echo "export PATH=\"$FW_VENV/bin:\$HOME/.local/bin:\$PATH\""
        [ -n "$CFG_ANTHROPIC_BASE_URL" ] && echo "export ANTHROPIC_BASE_URL=\"$CFG_ANTHROPIC_BASE_URL\""
        [ -n "$CFG_ANTHROPIC_API_KEY" ]  && echo "export ANTHROPIC_API_KEY=\"$CFG_ANTHROPIC_API_KEY\""
        [ -n "$CFG_WIFI_SSID" ]          && echo "export TS_WIFI_SSID=\"$CFG_WIFI_SSID\""
        [ -n "$CFG_WIFI_PASSWORD" ]      && echo "export TS_WIFI_PASSWORD=\"$CFG_WIFI_PASSWORD\""
    } > "$ENV_SH"
    chmod 600 "$ENV_SH"
    _ok "85-① env.sh 生成（600）"
fi

# ---- 落盘 ②：agent/config.toml（gitignored；已存在不覆盖） ----
_CFG_TOML="$REPO_DIR/agent/config.toml"
if [ -f "$_CFG_TOML" ]; then
    step_skip "85-② agent/config.toml（已存在——不覆盖）"
else
    cat > "$_CFG_TOML" <<EOF
# tessera-agent 运行配置（安装程序生成——gitignored；分节表纪律，密钥走 env.sh 环境变量）
[agent]
workspace_repo = "$REPO_DIR"
west_workspace = "$WEST_WS"
west_venv_python = "$FW_VENV/bin/python"
audit_dir = "$REPO_DIR/agent/audit"

[providers]
default_model = "$CFG_LLM_MODEL"
context_window = 1000000

[zenoh]
router_locator = "tcp/127.0.0.1:${CFG_ZENOHD_TCP_PORT}"
EOF
    chmod 600 "$_CFG_TOML"
    _ok "85-② agent/config.toml 生成（600）"
fi

# ---- 自检：密钥未泄漏到本步输出（结构性保证：全程无 echo 凭据） ----
if [ -n "$CFG_ANTHROPIC_API_KEY" ]; then
    if grep -rq "$CFG_ANTHROPIC_API_KEY" "$REPO_DIR" --include='*' -l --exclude-dir=.git 2>/dev/null | grep -qv config.toml; then
        _warn "API key 疑似出现在仓内文件——请检查（红线：凭据不入仓）"
    fi
fi
_ok "85 用户配置完成（未配置项可后续手工补 $ENV_SH / agent/config.toml）"
