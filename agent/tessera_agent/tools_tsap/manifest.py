# SPDX-License-Identifier: Apache-2.0
"""TSAP manifest 镜像 schema v1（LLD-A05 §2；与固件 LLD-ts-appmgr §2 同源）。

CBOR 键序定稿（canonical，与固件侧消费对齐）：
  map{ app_id(tstr), app_ver(tstr), min_fw_ver(tstr), caps(array tstr),
       stack_kb(uint), heap_kb(uint), exports(array tstr) }
exports 约定：必含 "health_ping"；init/tick/evt 可选（LLD-ts-appmgr §2）。
"""

from __future__ import annotations

import re
from typing import Literal

import cbor2
from pydantic import BaseModel, Field, field_validator, model_validator

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
APP_ID_RE = re.compile(r"^[a-z0-9.-]{3,64}$")  # 反域名串（LLD-ts-appmgr §2）
_EXPORTS_REQUIRED = "health_ping"
# 导出名 = 固件运行时 lookup 面（LLD-ts-appmgr §4 调用约定：app_init/
# app_tick/app_evt + health_ping；板级十修复——早前 init/tick/evt 为
# LLD §2 笔误漂移，与 runtime.c/夹具 wasm 均不符）
_EXPORTS_ALLOWED = {"health_ping", "app_init", "app_tick", "app_evt"}


class TsapManifest(BaseModel):
    """结构化 manifest（序列化一律 cbor2 canonical）。"""

    app_id: str
    app_ver: str
    min_fw_ver: str
    caps: list[str] = Field(default_factory=list)  # ts_perm_v1 能力文法（M2b 消费）
    stack_kb: int = Field(ge=1, le=64)  # 上限 DEC-27：8KB 栈（KB 口径 ≤64）
    heap_kb: int = Field(ge=1, le=4096)  # 每板动态（DEC-27；Agent 侧上限防滥用）
    exports: list[str]
    # DEC-47⑤（MD1.2e）：ts-fs 路径前缀白名单（绝对路径、无 ..；缺省 = 无 fs 授权）
    fs_paths: list[str] | None = None
    # DEC-47③（MD1.2g）：ts-av 采集格式/分辨率声明（与 caps 含 "av:" 互为充要）
    av_fmt: Literal["jpeg", "rgb565"] | None = None
    av_w: int | None = Field(default=None, ge=16, le=800)
    av_h: int | None = Field(default=None, ge=16, le=800)

    @model_validator(mode="after")
    def _av_group(self) -> TsapManifest:
        """caps 的 av: 能力与 av_fmt/av_w/av_h 声明须成组出现（DEC-47③：
        固件侧配置绑定要求三者齐备；缺组 = boot 装载拒绝——fail-closed）。"""
        has_av = any(c.startswith("av:") for c in self.caps)
        if has_av and (self.av_fmt is None or self.av_w is None or self.av_h is None):
            msg = "caps 含 av: 但 av_fmt/av_w/av_h 未齐备声明（DEC-47③）"
            raise ValueError(msg)
        if not has_av and self.av_fmt is not None:
            msg = "声明 av_fmt/av_w/av_h 但 caps 无 av: 能力（DEC-47③）"
            raise ValueError(msg)
        return self

    @field_validator("fs_paths")
    @classmethod
    def _fs_paths(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        if not v:
            return None  # 空数组归一为缺省
        for p in v:
            if not re.match(r"^/[A-Za-z0-9._:/-]{0,62}/?$", p) or ".." in p:
                msg = f"非法 fs_paths 条目: {p!r}（须绝对路径，禁 ..）"
                raise ValueError(msg)
        out = sorted(set(v))
        if len(";".join(out)) >= 256:
            # 固件绑定 CSV 容量 = CONFIG_TS_HAL_FS_PATHS_MAX（256B 含 NUL）
            msg = "fs_paths 总长超限（固件 CSV 容量 256B）"
            raise ValueError(msg)
        return out

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
        if self.fs_paths:
            m["fs_paths"] = self.fs_paths  # DEC-47⑤：仅在有授权时携带
        if self.av_fmt is not None:
            m["av_fmt"] = self.av_fmt  # DEC-47③：仅在有声明时携带
            m["av_w"] = self.av_w
            m["av_h"] = self.av_h
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
            fs_paths=list(m["fs_paths"]) if m.get("fs_paths") else None,
            av_fmt=m.get("av_fmt"),
            av_w=int(m["av_w"]) if "av_w" in m else None,
            av_h=int(m["av_h"]) if "av_h" in m else None,
        )
