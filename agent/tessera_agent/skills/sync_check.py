# SPDX-License-Identifier: Apache-2.0
"""skill 同步检查（Q-19 #13 / DEC-38 #13；LLD-A07 §2 维护纪律）。

权威文档变更后 skill 须重新派生并更新 SOURCES.lock（sha256 of 源文档）。
本脚本机械校验：源文档摘要与 lock 一致——不一致 = skill 可能过期，退出码 1。
用法：python -m tessera_agent.skills.sync_check [--update]
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from tessera_agent.skills.loader import SKILLS_DIR, load_skills

LOCK_NAME = "SOURCES.lock"


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _find_repo_root(sdir: Path) -> Path:
    """向上找仓库根（AGENTS.md 标记；找不到 = skills 父目录——测试沙盒布局）。"""
    for cand in sdir.parents:
        if (cand / "AGENTS.md").is_file():
            return cand
    return sdir.parent


def check(update: bool = False, *, skills_dir: Path | None = None,
          repo_root: Path | None = None) -> list[str]:
    """返回过期项描述（空 = 同步）；update=True 时重写 lock。

    skills_dir/repo_root 缺省 = 模块属性（调用时解析——测试可注入沙盒）。
    """
    sdir = skills_dir if skills_dir is not None else SKILLS_DIR
    root = repo_root if repo_root is not None else _find_repo_root(sdir)
    lock_path = sdir / LOCK_NAME
    expected: dict[str, list[str]] = {}
    if lock_path.is_file():
        for line in lock_path.read_text(encoding="utf-8").splitlines():
            if ":" in line:
                skill, digests = line.split(":", 1)
                expected[skill.strip()] = [d.strip() for d in digests.split(",") if d.strip()]

    stale: list[str] = []
    current: dict[str, list[str]] = {}
    for ref in load_skills(sdir):
        digests: list[str] = []
        missing: list[str] = []
        for src in ref.sources:
            p = root / src
            if not p.is_file():
                missing.append(src)
                continue
            digests.append(_digest(p))
        current[ref.name] = digests
        if missing:
            stale.append(f"{ref.name}: 源文档缺失 {missing}")
        elif expected.get(ref.name) != digests:
            stale.append(
                f"{ref.name}: 源文档已变更（lock={expected.get(ref.name)} 当前={digests}）"
                "——请重新派生 skill 并 --update"
            )
    extra = set(expected) - set(current)
    if extra:
        stale.append(f"lock 含未注册 skill: {sorted(extra)}")

    if update and not any("缺失" in s for s in stale):
        lines = [f"{name}: {','.join(d)}" for name, d in sorted(current.items())]
        lock_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"SOURCES.lock 已更新（{len(lines)} 项）")
        return []
    return stale


def main() -> int:
    update = "--update" in sys.argv
    stale = check(update=update)
    if stale:
        print("skill 同步检查 FAIL:")
        for s in stale:
            print(f"  - {s}")
        return 1
    print("skill 同步检查 OK（源文档与 SOURCES.lock 一致）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
