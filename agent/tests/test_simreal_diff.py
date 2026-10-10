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
