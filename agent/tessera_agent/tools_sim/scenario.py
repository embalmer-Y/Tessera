# SPDX-License-Identifier: Apache-2.0
"""sim_* 场景模型与校验（LLD-A04 §1）。

scenario_version 1：inputs（虚拟时刻输入序列，t_ms 升序不变量）/
expectations（eq|within|count 断言）/meta。
V1 语义注记：固件侧重放场景为编译期内嵌（M1 定稿接口）——本层场景对象用于
校验与期望评估；输入注入演进（输入文件）随 M3/MA3 联动。
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator, model_validator

_OPS = {"eq", "within", "count"}


class SimInput(BaseModel):
    t_ms: int = Field(ge=0)
    ch: str = Field(min_length=1, max_length=32)
    value: float | int | bool


class SimExpectation(BaseModel):
    ch: str = Field(min_length=1, max_length=32)
    op: str
    value: float | int | bool
    t_window_ms: int = Field(default=0, ge=0)
    tolerance: float = Field(default=0.0, ge=0.0)

    @field_validator("op")
    @classmethod
    def _op(cls, v: str) -> str:
        if v not in _OPS:
            msg = f"op 必须为 {_OPS}: {v!r}"
            raise ValueError(msg)
        return v


class SimMeta(BaseModel):
    firmware_commit: str | None = None
    board: str | None = None
    seed: int | None = None  # 透传固件重放语义（合同 9）


class Scenario(BaseModel):
    scenario_version: int = Field(frozen=True, default=1)
    inputs: list[SimInput] = Field(min_length=1)
    expectations: list[SimExpectation] = Field(default_factory=list)
    meta: SimMeta = Field(default_factory=SimMeta)

    @model_validator(mode="after")
    def _ordered(self) -> Scenario:
        for a, b in zip(self.inputs, self.inputs[1:], strict=False):
            if b.t_ms < a.t_ms:
                msg = f"inputs t_ms 必须升序: {a.t_ms} -> {b.t_ms}"
                raise ValueError(msg)
        return self


def scenario_validate(scenario: dict) -> list[str]:
    """返回错误清单（空 = 合法）。"""
    try:
        Scenario(**scenario)
    except Exception as exc:  # noqa: BLE001
        return [str(exc)]
    return []
