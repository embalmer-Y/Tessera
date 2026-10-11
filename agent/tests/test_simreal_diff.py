# SPDX-License-Identifier: Apache-2.0
"""NV-3 sim↔real 语义对拍测试：写序列终态归一 / console 判据提取 / 键值 diff。"""
from __future__ import annotations

from tessera_agent.tools_diag import simreal_diff as sr

SIM_WRITES = [
    {"ch": "dbled", "value_u": 300, "t_ms": 100},
    {"ch": "dbled", "value_u": 0, "t_ms": 5200},   # 断链 fail-safe 终态
    {"ch": "dbpwm", "value_u": 250, "t_ms": 5201},
    {"ch": "noise", "value_u": 99, "t_ms": 99},    # 对拍通道外（过滤）
]

REAL_CONSOLE = """\
DB0 deploybench start
dbled duty read 999 permille @t=100
link down detected
dbled duty read 0 permille @t=5200
dbpwm duty read 250 permille @t=5201
DB alive t=6000
"""


def test_normalize_sim_final_values():
    got = sr.normalize_sim(SIM_WRITES, ["dbled", "dbpwm"])
    assert got == {"dbled": 0, "dbpwm": 250}


def test_normalize_real_last_hit():
    got = sr.normalize_real(REAL_CONSOLE, {
        "dbled": r"dbled duty read (\d+) permille",
        "dbpwm": r"dbpwm duty read (\d+) permille",
    })
    assert got == {"dbled": 0, "dbpwm": 250}   # 终态（最后一次命中）


def test_diff_full_match_with_tolerance():
    sim = sr.normalize_sim(SIM_WRITES, ["dbled", "dbpwm"])
    real = {"dbled": 0, "dbpwm": 252}
    res = sr.diff(sim, real, tolerance=5)
    assert res.pass_
    assert set(res.match) == {"dbled", "dbpwm"}


def test_diff_mismatch_and_missing():
    sim = {"dbled": 0, "dbpwm": 250}
    real = {"dbled": 300, "dbpwm": 250}
    res = sr.diff(sim, real)
    assert not res.pass_
    assert res.mismatch["dbled"] == {"sim": 0, "real": 300}
    assert res.missing == []  # dbpwm 在两侧
    res2 = sr.diff({"dbled": 0, "x": 1}, {"dbled": 0})
    assert res2.missing == ["x"]


def test_diff_non_numeric_requires_equal():
    res = sr.diff({"m": "SAFE_FAULT"}, {"m": "SAFE_FAULT"})
    assert res.pass_
    res2 = sr.diff({"m": "SAFE_FAULT"}, {"m": "SAFE_ON"})
    assert not res2.pass_


# ---- V2-3 判据行级对拍 ----

SIM_LINES = ["[app1/l3] nv1 init", "[app1/l3] nv1 tick cnt=01",
             "[app1/l3] nv1 tick cnt=02", "[app1/l3] NV1 DONE ticks=05"]
REAL_TEXT = "[app1/l3] nv1 init\n[app1/l3] nv1 tick cnt=01\n" \
            "[app1/l3] nv1 tick cnt=02\n[app1/l3] NV1 DONE ticks=05\n"


def test_extract_and_diff_lines_full_match():
    real = sr.extract_verdict_lines(REAL_TEXT, ["nv1", "NV1"])
    assert real == ["nv1 init", "nv1 tick cnt=01", "nv1 tick cnt=02",
                    "NV1 DONE ticks=05"]
    sim = [sr.normalize_verdict_line(x) for x in SIM_LINES]
    out = sr.diff_lines(sim, real)
    assert out["pass"] and out["sim_len"] == 4 and out["real_len"] == 4


def test_diff_lines_mismatch_detected():
    sim = ["nv1 init", "nv1 tick cnt=01", "NV1 DONE ticks=05"]
    real = ["nv1 init", "nv1 tick cnt=09", "NV1 DONE ticks=05"]
    out = sr.diff_lines(sim, real)
    assert not out["pass"]
    assert out["mismatch"][0]["idx"] == 1


def test_diff_lines_tail_align_tolerates_truncation():
    sim = ["nv1 init", "tick 01", "tick 02", "NV1 DONE ticks=05"]
    real = ["tick 02", "NV1 DONE ticks=05"]   # 采集窗口首截断形态
    out = sr.diff_lines(sim, real, tail_align=True)
    assert out["pass"] and out["tail_aligned"]
    out2 = sr.diff_lines(sim, real)
    assert not out2["pass"]                    # 严格模式如实不过
