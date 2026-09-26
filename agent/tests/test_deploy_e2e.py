# SPDX-License-Identifier: Apache-2.0
"""deploy E2E（LLD-A06 §5；MA3 退出标准）：spec → TSAP 包 → 部署到仿真立方体。

门控：环境变量 TESSERA_E2E_DEPLOY=1 且 TAP zeth 在位（复跑环境见
docs/dev-environment.md §8：TAP 需 sudo 建立；zenohd 由本测试拉起）。
默认跳过（CI 无 TAP/固件链路）。
"""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import time
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("TESSERA_E2E_DEPLOY") != "1",
    reason="E2E 部署链需显式开启（TESSERA_E2E_DEPLOY=1）+ dev-environment §8 环境",
)

from tessera_agent.tools_net import deploy  # noqa: E402
from tessera_agent.tools_net.zenoh_service import ZenohService  # noqa: E402
from tessera_agent.tools_tsap import tools as tsap_tools  # noqa: E402

REPO = Path("~/project/tessera").expanduser()
WEST_WS = Path("~/project/zephyrproject").expanduser()
ZENOHD = Path("~/project/tools/zenohd").expanduser()
FW_BUILD = REPO / "agent" / "build" / "deploy-e2e" / "build"
NODE, CUBE = "l3n", "l3c"


def _tap_present() -> bool:
    try:
        subprocess.run(["ip", "link", "show", "zeth"], capture_output=True, check=True)
        return True
    except Exception:  # noqa: BLE001
        return False


def _port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


@pytest.fixture(scope="module")
def cube_env(tmp_path_factory):
    if not _tap_present():
        pytest.skip("TAP zeth 不在位（dev-environment §8-1 建立）")
    zenohd = None
    if not _port_open(7447):
        zenohd = subprocess.Popen(
            [str(ZENOHD), "--listen", "tcp/0.0.0.0:7447"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        for _ in range(50):
            if _port_open(7447):
                break
            time.sleep(0.1)
        else:
            zenohd.terminate()
            pytest.fail("zenohd 未就绪")
    exe = FW_BUILD / "zephyr" / "zephyr.exe"
    if not exe.is_file():
        subprocess.run(
            [str(WEST_WS / ".venv/bin/west"), "build", "-b", "native_sim",
             str(REPO / "firmware/l3app"), "-d", str(FW_BUILD), "--",
             f"-DZEPHYR_EXTRA_MODULES={REPO/'firmware/module/tessera'};"
             f"{WEST_WS/'zenoh-pico'}"],
            cwd=str(WEST_WS), check=True, capture_output=True,
        )
    cwd = tmp_path_factory.mktemp("fw-cwd")
    fw = subprocess.Popen(
        [str(exe), "--eth-if=zeth"], cwd=str(cwd),
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        deadline = time.time() + 30
        connected = False
        while time.time() < deadline:
            with ZenohService("tcp/127.0.0.1:7447", query_timeout_s=3.0) as svc:
                if deploy.discover(svc, timeout_s=3.0):
                    connected = True
                    break
        if not connected:
            pytest.fail("固件 30s 内未在 router 侧可发现（检查 l3fw 日志）")
        yield
    finally:
        os.killpg(os.getpgid(fw.pid), signal.SIGTERM)
        if zenohd is not None:
            zenohd.terminate()


def test_e2e_spec_to_deployed_cube(cube_env, tmp_path):
    """MA3 退出标准：manifest spec → TSAP 打包签名 → 部署到仿真立方体。
    M2b.2 收尾：wasm 产物 = 仓库真夹具（framework.app 运行的同一二进制
    firmware/tests/app/appw/native_app.wasm）——E2E 与固件运行时同一工件。"""
    tsap_tools.tsap_keygen("e2e", str(tmp_path), [str(tmp_path)])
    repo_root = Path(__file__).resolve().parents[1]
    while not (repo_root / "AGENTS.md").is_file():
        repo_root = repo_root.parent
    wasm = repo_root / "firmware" / "tests" / "app" / "appw" / "native_app.wasm"
    assert wasm.is_file(), f"夹具 wasm 缺失：{wasm}"
    pkg = tsap_tools.tsap_package(
        str(wasm),
        {"app_id": "com.tessera.e2e", "app_ver": "1.0.0", "min_fw_ver": "0.1.0",
         "caps": ["gpio:write:0-3"], "stack_kb": 4, "heap_kb": 16,
         "exports": ["health_ping", "app_init", "app_evt"]},
        str(tmp_path / "e2e.key"), str(tmp_path), [str(tmp_path)],
    )
    with ZenohService("tcp/127.0.0.1:7447") as svc:
        cubes = deploy.discover(svc)
        assert any(c["node_id"] == NODE and c["cube_id"] == CUBE for c in cubes), cubes
        before = deploy.status(svc, NODE, CUBE)["get-app"]["active_slot"]
        logs: list[str] = []
        out = deploy.push_app(svc, NODE, CUBE, pkg["package_path"],
                              str(tmp_path / "e2e.pub"), log_fn=logs.append)
    assert out["confirmed"] is True, json.dumps(out, ensure_ascii=False, default=str)
    assert out["released"] is True
    assert out["active_slot"] != before, "必须切入 inactive slot"
    assert out["verify"]["cose_off"] == 16 + out["verify"]["manifest_len"] \
        + out["verify"]["wasm_len"], "容器自洽"
