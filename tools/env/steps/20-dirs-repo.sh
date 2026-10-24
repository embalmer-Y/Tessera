# SPDX-License-Identifier: Apache-2.0
# steps/20-dirs-repo.sh · 目录骨架 + 仓库 clone（已 clone 跳过；网络经代理环境继承）。
set -euo pipefail
. "$(dirname "$0")/../env_common.sh"

_log "20 · 目录与仓库"
mkdir -p "$PROJ"/{logs,deps,tools,builds} "$DL_DIR" "$WEST_WS"

if [ -d "$REPO_DIR/.git" ]; then
    step_skip "20 仓库（$REPO_DIR 已在位）"
elif [ -n "${ENV_INSTALLER_DIR:-}" ] && [ "${ENV_INSTALLER_DIR}/../../.git" -ef "$REPO_DIR/.git" ] 2>/dev/null; then
    step_skip "20 仓库（安装程序即自仓库内运行）"
else
    if [ -d "$REPO_DIR" ]; then
        _die "$REPO_DIR 存在但非 git 仓库——请手工处理后再跑"
    fi
    _log "clone Tessera → $REPO_DIR（大写 T——路径约定）"
    git clone https://github.com/embalmer-Y/Tessera.git "$REPO_DIR"
fi
