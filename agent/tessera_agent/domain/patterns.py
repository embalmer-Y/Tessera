# SPDX-License-Identifier: Apache-2.0
"""domain/patterns — 成功包样例库（AC-4 · DEC-83）。

库 = `agent/workspace/t-*` 目录本身（**扫描即索引**，无持久索引文件——
成功判定 = artifacts/app.wasm + *.tsap 双产物在盘）。检索面 v1 = 词面
机械（token Jaccard + caps/imports 加权），语义代理 = 快照 plan 步骤文本
（spec 原文仅 digest 入库——模型写的实施计划是需求语义最佳载体）。
注入 = PLANNING 阶段参考样例块（top_k=2 × 300B 摘要，明示禁止照抄）。
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

TOP_K = 2
SUMMARY_MAX = 300
_TOKEN_RX = re.compile(r"[a-z0-9_]+|[\u4e00-\u9fff]")


@dataclass
class PatternEntry:
    workspace: str
    app_id: str
    summary: str
    caps: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    tier: str = "small"
    threads: int = 1
    wasm_bytes: int = 0

    def _tokens(self) -> set[str]:
        text = " ".join([self.app_id, self.summary,
                         *self.caps, *self.imports]).lower()
        return set(_TOKEN_RX.findall(text))

    def render(self) -> str:
        head = (f"app_id={self.app_id}（tier={self.tier} "
                f"threads={self.threads} caps={self.caps or '无'} "
                f"imports={self.imports} wasm={self.wasm_bytes}B）")
        return f"- {head}：{self.summary[:SUMMARY_MAX]}"


def _tokenize(text: str) -> set[str]:
    return set(_TOKEN_RX.findall(text.lower()))


def index_workspace(ws_dir: Path) -> PatternEntry | None:
    """单工作区索引：双产物在盘 = 成功样例；manifest/快照 plan 提取摘要。"""
    if not (ws_dir / "artifacts" / "app.wasm").is_file():
        return None
    tsaps = list((ws_dir / "artifacts").glob("*.tsap"))
    if not tsaps:
        return None
    try:
        project = json.loads(
            (ws_dir / "project.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    manifest = project.get("manifest") or {}
    app_id = str(manifest.get("app_id") or project.get("app_id") or "?")
    summary = _plan_summary(ws_dir)
    imports = sorted(_wasm_imports(ws_dir / "artifacts" / "app.wasm"))
    wasm_bytes = (ws_dir / "artifacts" / "app.wasm").stat().st_size
    return PatternEntry(
        workspace=str(ws_dir), app_id=app_id, summary=summary,
        caps=[str(c) for c in (manifest.get("caps") or [])],
        imports=imports, tier=str(manifest.get("tier") or "small"),
        threads=int(manifest.get("threads") or 1), wasm_bytes=wasm_bytes,
    )


def _plan_summary(ws_dir: Path) -> str:
    """需求语义代理：快照 plan 步骤描述拼接（无快照 = 空串）。"""
    snap = ws_dir / ".session" / "snapshot.json"
    if not snap.is_file():
        return ""
    try:
        data = json.loads(snap.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    parts = []
    for item in data.get("plan") or []:
        if isinstance(item, dict) and item.get("desc"):
            parts.append(str(item["desc"]))
        elif isinstance(item, str):
            parts.append(item)
    return "；".join(parts)[:SUMMARY_MAX]


def _wasm_imports(wasm_path: Path) -> list[str]:
    """wasm import 函数名（ts_* 面——零 wasmtime 依赖的轻解析：
    clang 产物保留符号名，可读串直接可提）。"""
    text = wasm_path.read_bytes().decode("latin-1")
    return sorted(set(re.findall(r"ts_[a-z_]+", text)) - {"ts_natives"})


def build_index(workspaces_dir: Path) -> list[PatternEntry]:
    """全库索引（毫秒级/工作区；无目录 = 空库）。"""
    if not workspaces_dir.is_dir():
        return []
    out = []
    for d in sorted(workspaces_dir.glob("t-*")):
        if not d.is_dir():
            continue
        entry = index_workspace(d)
        if entry is not None:
            out.append(entry)
    return out


def search(entries: list[PatternEntry], spec: str,
           top_k: int = TOP_K) -> list[tuple[PatternEntry, float]]:
    """词面检索（DEC-83②）：Jaccard + caps 前缀族 ×0.5 + imports ×0.5。"""
    spec_tokens = _tokenize(spec)
    spec_caps = {c.split(":")[0] for c in re.findall(r"[a-z]+:", spec)}
    out: list[tuple[PatternEntry, float]] = []
    for e in entries:
        et = e._tokens()
        inter = spec_tokens & et
        union = spec_tokens | et
        score = len(inter) / len(union) if union else 0.0
        e_caps = {c.split(":")[0] for c in e.caps}
        if e_caps and (e_caps & spec_caps):
            score += 0.5
        if e.imports and (set(e.imports) & set(
                re.findall(r"ts_[a-z_]+", spec))):
            score += 0.5
        if score > 0:
            out.append((e, round(score, 3)))
    out.sort(key=lambda p: -p[1])
    return out[:top_k]


def render_for_prompt(hits: list[tuple[PatternEntry, float]]) -> str:
    """PLANNING 注入块（明示防照抄；空 = 空串零注入）。"""
    if not hits:
        return ""
    lines = ["", "[参考样例（样例库检索命中——工程结构/manifest 形态可参照；"
             "业务逻辑禁止照抄，须按当前需求原创实现）]"]
    for e, score in hits:
        lines.append(f"{e.render()}（相关度 {score}）")
    lines.append("[参考样例结束]")
    return "\n".join(lines)


def retrieve(workspaces_dir: Path, spec: str) -> tuple[str, list[str]]:
    """一键面：建库 → 检索 → 渲染注入块。返回 (注入块, 命中 app_id 列表)。"""
    hits = search(build_index(workspaces_dir), spec)
    return render_for_prompt(hits), [e.app_id for e, _ in hits]
