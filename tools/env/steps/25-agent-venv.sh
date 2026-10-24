# SPDX-License-Identifier: Apache-2.0
# steps/25-agent-venv.sh · Agent venv（产品用户档核心——tessera-agent 可执行）。
# venv 创建：优先 uv（无 ensurepip 依赖 + 托管 Python 带编译头）；回退 python3 -m venv。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

_log "25 · Agent venv（$AGENT_VENV）"
[ -d "$REPO_DIR/agent" ] || _die "仓库未就位（先跑 20 步）"

if [ ! -x "$AGENT_VENV/bin/python" ]; then
    if have_cmd uv; then
        uv venv "$AGENT_VENV" --python "$PIN_PY_VENV" >/dev/null
    else
        python3 -m venv "$AGENT_VENV" 2>/dev/null || _die "venv 创建失败（系统 python 无 ensurepip）——安装 uv 后重跑：curl -LsSf https://astral.sh/uv/install.sh | sh"
    fi
fi

if ! "$AGENT_VENV/bin/python" -c "import tessera_agent" >/dev/null 2>&1; then
    if have_cmd uv; then
        TIER="${TIER:-user}"
        if [ "$TIER" = "dev" ]; then
            uv pip install --python "$AGENT_VENV/bin/python" -q -e "$REPO_DIR/agent[dev]"
        else
            uv pip install --python "$AGENT_VENV/bin/python" -q -e "$REPO_DIR/agent"
        fi
    else
        "$AGENT_VENV/bin/pip" install -q -e "$REPO_DIR/agent"
    fi
fi
"$AGENT_VENV/bin/tessera-agent" --help >/dev/null 2>&1 \
    && step_skip "25 Agent venv（tessera-agent 可执行）" \
    || _die "tessera-agent 安装异常（查看上方日志）"
