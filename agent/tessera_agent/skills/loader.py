# SPDX-License-Identifier: Apache-2.0
"""Skill loader（LLD-A07 §1，DEC-37 修订：自建，开放标准目录约定）。

渐进披露：会话系统提示只注入 name+description 一览；全文经 skill_read(name)
按需读取。skill 内容从权威文档派生（不双写真相）——同步纪律见 sync_check.py
（Q-19 #13：源文档变更后须重新派生并更新 SOURCES.lock）。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"


@dataclass
class SkillRef:
    """已注册 skill（开放标准 SKILL.md 解析结果）。"""

    name: str
    description: str
    path: Path
    sources: list[str] = field(default_factory=list)
    body: str = ""

    def listing(self) -> dict[str, str]:
        """渐进披露一级内容（系统提示注入面）。"""
        return {"name": self.name, "description": self.description}


def _parse_frontmatter(text: str) -> tuple[dict[str, object], str]:
    """YAML frontmatter（仅 name/description/sources 平面字段——不引 yaml 依赖）。"""
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    head = text[4:end]
    body = text[end + 5:]
    meta: dict[str, object] = {}
    key: str | None = None
    for line in head.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith("  - ") or line.startswith("- "):  # sources 列表项
            if key == "sources":
                item = line.split("- ", 1)[1].strip()
                assert isinstance(meta["sources"], list)
                meta["sources"].append(item)
            continue
        if ": " in line or line.rstrip().endswith(":"):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            meta[key] = [] if not val else val  # 无值键（sources:）= 空列表容器
    return meta, body


def load_skills(skills_dir: Path = SKILLS_DIR) -> list[SkillRef]:
    """扫描 skills/*/SKILL.md 并注册（启动期一次；缺目录 = 空 集）。"""
    refs: list[SkillRef] = []
    if not skills_dir.is_dir():
        return refs
    for md in sorted(skills_dir.glob("*/SKILL.md")):
        meta, body = _parse_frontmatter(md.read_text(encoding="utf-8"))
        name = str(meta.get("name", md.parent.name))
        refs.append(SkillRef(
            name=name,
            description=str(meta.get("description", "")),
            path=md,
            sources=[str(s) for s in (meta.get("sources") or [])],
            body=body.strip(),
        ))
    return refs


def read_skill(name: str, skills_dir: Path = SKILLS_DIR) -> str:
    """按需全文（渐进披露二级内容；未知名 = ValueError）。"""
    for ref in load_skills(skills_dir):
        if ref.name == name:
            return f"# skill: {name}\n\n{ref.body}"
    msg = f"未知 skill: {name}"
    raise ValueError(msg)


def system_prompt_listing(skills_dir: Path = SKILLS_DIR) -> str:
    """注入系统提示的一览（激活快照同时记录——审计确定性，LLD-A07 §1）。"""
    refs = load_skills(skills_dir)
    if not refs:
        return "（无已注册 skill）"
    lines = ["可用 skills（全文经 read_skill/skill_read 按需读取）："]
    lines += [f"- {r.name}: {r.description}" for r in refs]
    return "\n".join(lines)
