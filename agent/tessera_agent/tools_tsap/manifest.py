# SPDX-License-Identifier: Apache-2.0
"""TSAP manifest 镜像 schema v1（LLD-A05 §2；与固件 LLD-ts-appmgr §2 同源）。

CBOR 键序定稿（canonical，与固件侧消费对齐）：
  map{ app_id(tstr), app_ver(tstr), min_fw_ver(tstr), caps(array tstr),
       stack_kb(uint), heap_kb(uint), exports(array tstr) }
exports 约定：必含 "health_ping"；init/tick/evt 可选（LLD-ts-appmgr §2）。
"""

from __future__ import annotations

import re

import cbor2
from pydantic import BaseModel, Field, field_validator

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
APP_ID_RE = re.compile(r"^[a-z0-9.-]{3,64}$")  # 反域名串（LLD-ts-appmgr §2）
_EXPORTS_REQUIRED = "health_ping"
_EXPORTS_ALLOWED = {"health_ping", "init", "tick", "evt"}


class TsapManifest(BaseModel):
    """结构化 manifest（序列化一律 cbor2 canonical）。"""

    app_id: str
    app_ver: str
    min_fw_ver: str
    caps: list[str] = Field(default_factory=list)  # ts_perm_v1 能力文法（M2b 消费）
    stack_kb: int = Field(ge=1, le=64)  # 上限 DEC-27：8KB 栈（KB 口径 ≤64）
    heap_kb: int = Field(ge=1, le=4096)  # 每板动态（DEC-27；Agent 侧上限防滥用）
    exports: list[str]

    @field_validator("app_ver", "min_fw_ver")
    @classmethod
    def _semver(cls, v: str) -> str:
        if not SEMVER_RE.match(v):
            msg = f"版本必须为 semver（X.Y.Z）: {v!r}"
            raise ValueError(msg)
        return v

    @field_validator("app_id")
    @classmethod
    def _app_id(cls, v: str) -> str:
        if not APP_ID_RE.match(v):
            msg = f"app_id 须为反域名小写串: {v!r}"
            raise ValueError(msg)
        return v

    @field_validator("exports")
    @classmethod
    def _exports(cls, v: list[str]) -> list[str]:
        if _EXPORTS_REQUIRED not in v:
            msg = "exports 必须包含 health_ping（LLD-ts-appmgr §2）"
            raise ValueError(msg)
        extra = set(v) - _EXPORTS_ALLOWED
        if extra:
            msg = f"未知导出: {extra}"
            raise ValueError(msg)
        return sorted(set(v))

    def to_cbor(self) -> bytes:
        """canonical CBOR（确定性合同 9 的字节可复现基础）。"""
        m = {
            "app_id": self.app_id,
            "app_ver": self.app_ver,
            "min_fw_ver": self.min_fw_ver,
            "caps": self.caps,
            "stack_kb": self.stack_kb,
            "heap_kb": self.heap_kb,
            "exports": self.exports,
        }
        return cbor2.dumps(m, canonical=True)

    @classmethod
    def from_cbor(cls, data: bytes) -> TsapManifest:
        m = cbor2.loads(data)
        if not isinstance(m, dict):
            msg = "manifest CBOR 必须为 map"
            raise ValueError(msg)
        return cls(
            app_id=m["app_id"],
            app_ver=m["app_ver"],
            min_fw_ver=m["min_fw_ver"],
            caps=list(m.get("caps", [])),
            stack_kb=int(m["stack_kb"]),
            heap_kb=int(m["heap_kb"]),
            exports=list(m["exports"]),
        )
