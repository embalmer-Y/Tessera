# SPDX-License-Identifier: Apache-2.0
"""A07 skills 测试（LLD-A07 §1/§2/§7）：loader 渐进披露 / 同步检查（Q-19 #13）。"""

from __future__ import annotations

import pytest

from tessera_agent.skills import loader, sync_check

EXPECTED = ["tessera-build", "tessera-safety", "tessera-tsap", "tessera-workflow"]


def test_loader_registers_four_skills():
    refs = loader.load_skills()
    assert sorted(r.name for r in refs) == EXPECTED
    for r in refs:
        assert r.description, f"{r.name} 缺 description"
        assert r.sources, f"{r.name} 缺 sources（派生纪律）"
        assert len(r.body) > 100, f"{r.name} 正文过短"


def test_progressive_disclosure_two_levels():
    listing = loader.system_prompt_listing()
    for name in EXPECTED:
        assert name in listing
    assert "军规十条" not in listing or listing.count("\n") <= 6, "一览不得泄漏全文"
    full = loader.read_skill("tessera-safety")
    assert "三安全态" in full and "写入路径唯一" in full
    with pytest.raises(ValueError):
        loader.read_skill("nope")


def test_sync_check_clean_on_repo():
    """CI 守卫：源文档与 SOURCES.lock 必须一致（漂移 = 重新派生 + --update）。"""
    assert sync_check.check() == []


def test_sync_check_detects_stale(tmp_path, monkeypatch):
    skills = tmp_path / "skills"
    (skills / "demo").mkdir(parents=True)
    (skills / "demo" / "SKILL.md").write_text(
        "---\nname: demo\ndescription: d\nsources:\n  - docs/x.md\n---\n\n正文\n",
        encoding="utf-8",
    )
    root = tmp_path
    (root / "docs").mkdir()
    (root / "docs" / "x.md").write_text("v1\n", encoding="utf-8")
    assert sync_check.check(update=True, skills_dir=skills, repo_root=root) == []
    (root / "docs" / "x.md").write_text("v2\n", encoding="utf-8")
    stale = sync_check.check(skills_dir=skills, repo_root=root)
    assert len(stale) == 1 and "demo" in stale[0]
