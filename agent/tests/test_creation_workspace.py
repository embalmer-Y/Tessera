# SPDX-License-Identifier: Apache-2.0
"""AG2 工作区 + scoped 编辑动词测试矩阵（LLD-agent-creation-workspace §9——零 LLM/零网络）。

覆盖退出标准（HLD-agent v0.2 §7 AG2）：roots 逃逸 / 锚定失配 / 分页边界 / 白名单只读，
外加：防盲写（STALE）/容量上限/工程清单单一事实源/原子性。
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from tessera_agent.common.errors import (
    TA_E_ANCHOR_AMBIGUOUS,
    TA_E_ANCHOR_NOT_FOUND,
    TA_E_ARGS,
    TA_E_NOT_FOUND,
    TA_E_WORKSPACE_LIMIT,
    TA_E_WORKSPACE_PATH,
    TA_E_WORKSPACE_STALE,
    TaError,
)
from tessera_agent.creation.tools import WorkspaceTools
from tessera_agent.creation.workspace import Workspace


@pytest.fixture()
def env(tmp_path: Path):
    """工作区 + 仓库只读白名单环境。"""
    base = tmp_path / "workspace"
    ro = tmp_path / "repo"
    (ro / "include").mkdir(parents=True)
    (ro / "include" / "ts.h").write_text("int ts_gpio_write(int ch, int v);\n", encoding="utf-8")
    ws = Workspace.create(base, "t-001", ro_roots=[ro / "include"], app_id="demo.x")
    return ws, WorkspaceTools(ws), ro


def _err_code(fn, *args, **kwargs) -> int:
    with pytest.raises(TaError) as ei:
        fn(*args, **kwargs)
    return ei.value.code


# ---- roots 矩阵 ---------------------------------------------------------


def test_roots_outside_rejected(env):
    ws, tools, ro = env
    assert _err_code(tools.ws_read, "../../etc/passwd") == TA_E_WORKSPACE_PATH
    assert _err_code(tools.ws_write, "../evil.c", "x") == TA_E_WORKSPACE_PATH
    assert _err_code(tools.ws_read, "/etc/passwd") == TA_E_WORKSPACE_PATH


def test_roots_symlink_escape_rejected(env):
    ws, tools, ro = env
    secret = ro.parent / "secret.txt"
    secret.write_text("s3cret", encoding="utf-8")
    link = ws.project_dir / "leak.c"
    link.symlink_to(secret)
    assert _err_code(tools.ws_read, "leak.c") == TA_E_WORKSPACE_PATH
    assert _err_code(tools.ws_write, "leak.c", "x") == TA_E_WORKSPACE_PATH


def test_artifacts_readonly_and_session_hidden(env):
    ws, tools, ro = env
    art = ws.artifacts_dir / "app.wasm"
    art.write_bytes(b"\x00asm")
    out = tools.ws_read("artifacts/app.wasm")
    assert "asm" in out["content"]  # 只读可达
    assert _err_code(tools.ws_write, "artifacts/app.wasm", "x") == TA_E_WORKSPACE_PATH
    assert _err_code(tools.ws_edit, "artifacts/app.wasm", "a", "b") == TA_E_WORKSPACE_PATH
    assert _err_code(tools.ws_read, ".session/snapshot.json") == TA_E_WORKSPACE_PATH


def test_repo_whitelist_readonly(env):
    ws, tools, ro = env
    out = tools.ws_read(str(ro / "include" / "ts.h"))
    assert "ts_gpio_write" in out["content"]
    assert _err_code(tools.ws_write, str(ro / "include" / "ts.h"), "x") == TA_E_WORKSPACE_PATH


# ---- 编辑动词语义 --------------------------------------------------------


def test_write_requires_read_for_overwrite(env):
    ws, tools, ro = env
    tools.ws_write("main.c", "int app_init(void) { return 0; }\n")
    # 覆写未再读（写后指纹已刷新——新写入者视为已读）→ 直接覆写应被拒？不：
    # ws_write 后 _mark_read 已刷新，模拟"外部修改"后再覆写必须先读。
    (ws.project_dir / "main.c").write_text("extern int changed;\n", encoding="utf-8")
    assert _err_code(tools.ws_write, "main.c", "new") == TA_E_WORKSPACE_STALE
    tools.ws_read("main.c")
    tools.ws_write("main.c", "int v2;\n")
    assert "v2" in (ws.project_dir / "main.c").read_text(encoding="utf-8")


def test_edit_anchor_not_found_and_ambiguous(env):
    ws, tools, ro = env
    src = "int a = 1;\nint b = 2;\nint a = 1;\n"
    tools.ws_write("c.c", src)
    tools.ws_read("c.c")
    code = _err_code(tools.ws_edit, "c.c", "int missing = 9;", "x")
    assert code == TA_E_ANCHOR_NOT_FOUND
    code = _err_code(tools.ws_edit, "c.c", "int a = 1;", "int a = 3;")
    assert code == TA_E_ANCHOR_AMBIGUOUS
    out = tools.ws_edit("c.c", "int a = 1;", "int a = 3;", replace_all=True)
    assert out["replaced"] == 2
    tools.ws_read("c.c")
    out = tools.ws_edit("c.c", "int b = 2;", "int b = 9;")
    assert out["replaced"] == 1


def test_edit_stale_after_external_change(env):
    ws, tools, ro = env
    tools.ws_write("s.c", "int x = 1;\n")
    tools.ws_read("s.c")
    time.sleep(0.02)  # 外部改动须跨文件时间戳粒度 tick（HZ=250 内核粗时钟 4ms）
    (ws.project_dir / "s.c").write_text("int x = 2;\n", encoding="utf-8")
    assert _err_code(tools.ws_edit, "s.c", "int x = 2;", "int x = 3;") == TA_E_WORKSPACE_STALE


def test_read_paging_boundaries(env):
    ws, tools, ro = env
    body = "".join(f"line {i}\n" for i in range(1000))
    tools.ws_write("big.c", body)
    out = tools.ws_read("big.c", offset=0, limit=400)
    assert out["total_lines"] == 1000
    assert out["has_more"] is True
    assert out["content"].splitlines()[0].startswith("1\t")
    out = tools.ws_read("big.c", offset=990, limit=400)
    assert out["has_more"] is False
    assert "1000\tline 999" in out["content"]
    assert _err_code(tools.ws_read, "big.c", offset=-1) == TA_E_ARGS
    assert _err_code(tools.ws_read, "big.c", limit=0) == TA_E_ARGS
    assert _err_code(tools.ws_read, "big.c", limit=5000) == TA_E_ARGS


def test_missing_file_and_dir_listing(env):
    ws, tools, ro = env
    assert _err_code(tools.ws_read, "project/nope.c") == TA_E_NOT_FOUND
    tools.ws_write("a.c", "int a;\n")
    tools.ws_write("sub/b.c", "int b;\n")
    out = tools.ws_list(".")
    names = {e["file"] for e in out["entries"]}
    assert {"a.c", "sub/b.c"} <= names


# ---- 容量与工程清单 ------------------------------------------------------


def test_file_size_and_count_limits(env):
    ws, tools, ro = env
    big = "x" * (512 * 1024 + 1)
    assert _err_code(tools.ws_write, "big.c", big) == TA_E_WORKSPACE_LIMIT
    for i in range(64):
        tools.ws_write(f"f{i:03d}.c", f"int v{i};\n")
    assert _err_code(tools.ws_write, "overflow.c", "int z;\n") == TA_E_WORKSPACE_LIMIT


def test_project_json_single_source_of_truth(env):
    ws, tools, ro = env
    tools.ws_write("main.c", "int main_code;\n")
    tools.ws_write("lib/util.c", "int util;\n")
    project = ws.load_project()
    assert project["files"] == ["lib/util.c", "main.c"]
    assert project["exports"] == ["app_init", "app_tick", "app_evt", "health_ping"]
    assert project["schema"] == 1
    assert project["app_id"] == "demo.x"


def test_create_twice_rejected_and_open_roundtrip(env):
    ws, tools, ro = env
    base = ws.root.parent
    assert _err_code(Workspace.create, base, "t-001") == TA_E_WORKSPACE_PATH
    again = Workspace.open(base, "t-001", ro_roots=[ro / "include"])
    assert again.load_project()["app_id"] == "demo.x"
    assert _err_code(Workspace.open, base, "t-999") == TA_E_WORKSPACE_PATH


def test_atomic_write_leaves_no_tmp(env):
    ws, tools, ro = env
    tools.ws_write("m.c", "int m;\n")
    leftovers = [p.name for p in ws.project_dir.rglob("*.tmp")]
    assert leftovers == []


def test_project_alias_normalization(env):
    """AG7 实证：LLM 自然带 project/ 前缀——确定性剥除（提示词声明 + 兜底）。"""
    ws, tools, ro = env
    tools.ws_write("main.c", "int a;\n")
    out = tools.ws_read("project/main.c")  # 别名读
    assert "int a;" in out["content"]
    out = tools.ws_list("project")  # 别名列目录 = 工程根
    assert any(e["file"] == "main.c" for e in out["entries"])
    tools.ws_write("project/util.c", "int u;\n")  # 别名写
    project = ws.load_project()
    assert "util.c" in project["files"]
    assert _err_code(tools.ws_write, "project/../evil.c", "x") == TA_E_WORKSPACE_PATH
