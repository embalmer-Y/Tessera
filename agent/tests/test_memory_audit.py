# SPDX-License-Identifier: Apache-2.0
"""memory_audit（LLD-agent-memory-planner · V0.13.0 MP）测试：解析器三行式/符号归并/
Discarded 截断/元数据排除/保留窗 + 规则目录 R0-R7 正负样本 + overall
三态 + 真图摘录锚定（fixtures/map_atk_excerpt.map——atk FIX-1 真行）。
"""
from __future__ import annotations

from pathlib import Path

import pytest

from tessera_agent.domain import firmware
from tessera_agent.domain import memory_audit as ma

FIXTURES = Path(__file__).parent / "fixtures"
EXCERPT = FIXTURES / "map_atk_excerpt.map"

REGIONS_TXT = """
Memory Configuration

Name             Origin             Length             Attributes
FLASH            0x00000000         0x007fff00         r
dram0_0_seg      0x3fc88000         0x00061704         rw
irom0_0_seg      0x42000000         0x02000000         xr
ext_dram_seg     0x3c000000         0x02000000         rw
IDT_LIST         0x3ebfe010         0x00002000         ew
"""


def _region_names(txt: str) -> list[str]:
    return [r.name for r in ma._parse_regions(txt)]


# ---- region 表 ----

def test_region_table_parses_both_forms() -> None:
    names = _region_names(REGIONS_TXT)
    assert names == ["FLASH", "dram0_0_seg", "irom0_0_seg",
                     "ext_dram_seg", "IDT_LIST"]


def test_region_table_ignores_header_row() -> None:
    assert "Name" not in _region_names(REGIONS_TXT)


# ---- input 三行式 + 符号归并 ----

def _objects_of(map_txt: str) -> list[ma.MemObject]:
    regions, objects, fills, _ = ma._parse_map(map_txt)
    return objects


TWO_LINE_MAP = REGIONS_TXT + """
Linker script and memory map

.dram0.bss      0x3fc88000    0x1000 load address 0x0001a3b4
 .bss.long_name_here
                0x3fc88000      0x200 zephyr/libzephyr.a(x.c.obj)
                0x3fc88000                _k_thread_stack_ui_tid
 .bss.short     0x3fc88200       0x40 zephyr/libzephyr.a(y.c.obj)
 *fill*         0x3fc88240        0xc
 .noinit.pico.system.c.0
                0x3fc88300      0x100 modules/zenoh-pico.a(system.c.obj)
                0x3fc88300                thread_stack_area
"""


def test_two_line_entry_with_symbol_attribution() -> None:
    objs = _objects_of(TWO_LINE_MAP)
    ui = [o for o in objs if o.kind == "stack" and o.name == "ui_tid"]
    assert len(ui) == 1 and ui[0].size == 0x200
    assert ui[0].region == "dram0_0_seg"


def test_inline_entry_parsed() -> None:
    objs = _objects_of(TWO_LINE_MAP)
    short = [o for o in objs if o.section == ".bss.short"]
    assert len(short) == 1 and short[0].size == 0x40


def test_fill_counted_but_not_object() -> None:
    regions, objects, fills, _ = ma._parse_map(TWO_LINE_MAP)
    assert fills == 0xC
    assert all(o.section != "*fill*" for o in objects)


def test_pico_pool_attributed_as_stack() -> None:
    objs = _objects_of(TWO_LINE_MAP)
    pico = [o for o in objs if o.kind == "stack"
            and o.name == "thread_stack_area"]
    assert len(pico) == 1 and pico[0].size == 0x100


# ---- Discarded 截断 + 元数据排除 + 保留窗 ----

DISCARDED_MAP = REGIONS_TXT + """
Linker script and memory map

.debug_info     0x00000000    0x1000
 .debug_info    0x00000100     0x800 zephyr/libzephyr.a(init.c.obj)

.dram0.bss      0x3fc88000     0x100 load address 0x0001a3b4
 .bss.real_thing 0x3fc88000      0x100 app/libapp.a(main.c.obj)

Discarded input sections

 .bss.video_buffer_pool
                0x00000000   0x200000 zephyr/libzephyr.a(buffer.c.obj)
"""


def test_discarded_sections_truncated() -> None:
    objs = _objects_of(DISCARDED_MAP)
    assert not any("video_buffer_pool" in o.section for o in objs)
    real = [o for o in objs if o.section == ".bss.real_thing"]
    assert len(real) == 1


def test_debug_input_sections_excluded() -> None:
    objs = _objects_of(DISCARDED_MAP)
    assert not any(o.section.startswith(".debug") for o in objs)


def test_reserved_window_not_used_and_slack_excludes_it() -> None:
    txt = REGIONS_TXT + """
Linker script and memory map

.dram0.dummy    0x3fc88000     0xf600
 *fill*         0x3fc88000     0xf5f4

.dram0.bss      0x3fc97600     0x100 load address 0x0001a3b4
 .bss.thing     0x3fc97600      0x100 app/libapp.a(main.c.obj)
"""
    regions, objects, _, _ = ma._parse_map(txt)
    dram = next(r for r in regions if r.name == "dram0_0_seg")
    assert dram.reserved == 0xF600
    assert dram.used == 0x100
    assert dram.slack == 0x61704 - 0xF600 - 0x100


def test_alias_window_regions_annotated() -> None:
    report = ma.MemoryReport(map_path="m", config_path="c", pre_build=False,
                             regions=ma._parse_regions(REGIONS_TXT))
    assert "irom0_0_seg" in report.render()


# ---- config 解析 ----

def test_parse_config_forms() -> None:
    cfg = ma.parse_config(
        "CONFIG_FOO=y\n"
        "CONFIG_BAR=4096\n"
        'CONFIG_BAZ="hello"\n'
        "# CONFIG_QUX is not set\n"
        "# 注释行\n"
        "CONFIG_HEX=0x100\n")
    assert cfg == {"FOO": "y", "BAR": "4096", "BAZ": "hello", "QUX": "n",
                   "HEX": "0x100"}


# ---- 真图摘录锚定（atk FIX-1 实图关键行）----

@pytest.fixture(scope="module")
def excerpt_report() -> ma.MemoryReport:
    cfg_txt = (
        "CONFIG_WIFI=y\n"
        "CONFIG_NET_RX_STACK_SIZE=4096\n"
        "CONFIG_TS_NET_ZENOH=y\n"
        "CONFIG_SYSTEM_WORKQUEUE_STACK_SIZE=4096\n"
        "CONFIG_SHELL=y\n"
        "CONFIG_SHELL_STACK_SIZE=4096\n"
        "CONFIG_HEAP_MEM_POOL_SIZE=58368\n"
        "CONFIG_TS_NET_TLS=y\n"
        "CONFIG_ESP32_WIFI_DYNAMIC_TX_BUFFER_NUM=32\n")
    cfg_path = FIXTURES / "map_excerpt.config"
    cfg_path.write_text(cfg_txt, encoding="utf-8")
    return ma.audit(EXCERPT, cfg_path)


def test_excerpt_region_numbers(excerpt_report: ma.MemoryReport) -> None:
    dram = next(r for r in excerpt_report.regions
                if r.name == "dram0_0_seg")
    assert dram.length == 399108
    assert dram.reserved == 62976          # .dram0.dummy（IRAM 镜像窗）
    # data 0x619c + noinit 0x27680 + bss 0x23b98
    assert dram.used == 24988 + 161408 + 146328
    assert dram.slack == 399108 - dram.reserved - dram.used


def test_excerpt_named_objects(excerpt_report: ma.MemoryReport) -> None:
    def find(name: str) -> ma.MemObject:
        hits = [o for o in excerpt_report.objects if o.name == name]
        assert len(hits) == 1, name
        return hits[0]

    assert find("_mbedtls_heap").size == 31744
    assert find("lvgl_heap_mem").size == 16384
    assert find("kheap__system_heap").size == 0xE454
    assert find("rx_stack").size == 4096
    assert find("deploy_watch_tid").size == 4096
    assert find("_mbedtls_heap").region == "dram0_0_seg"


def test_excerpt_flash_text_accounted(excerpt_report: ma.MemoryReport) -> None:
    irom = next(r for r in excerpt_report.regions if r.name == "irom0_0_seg")
    assert irom.used == 0xE01B0
    drom = next(r for r in excerpt_report.regions if r.name == "drom0_0_seg")
    assert drom.used == 0x1C9B8


# ---- 规则目录 ----

def _report_with(cfg: dict[str, str],
                 regions: list[ma.Region] | None = None,
                 diffs: list[dict[str, str]] | None = None) -> ma.MemoryReport:
    return ma.MemoryReport(
        map_path="m", config_path="c", pre_build=False,
        regions=regions or [], config=cfg,
        config_diffs=diffs or [])


def test_r0_override_and_missing_key() -> None:
    diffs = [{"key": "HEAP_MEM_POOL_SIZE", "declared": "196608",
              "effective": "58368"},
             {"key": "CONFIG_TYPO_KEY", "declared": "y",
              "effective": "<未生效>"}]
    f = ma.run_rules({}, _report_with({}, diffs=diffs), diffs)
    r0 = [x for x in f if x.rule_id == "R0"]
    assert len(r0) == 2 and all(x.severity == "warn" for x in r0)


def test_r1_rx_stack_floor() -> None:
    bad = _report_with({"WIFI": "y", "NET_RX_STACK_SIZE": "1500"})
    assert any(x.rule_id == "R1" and x.severity == "fail"
               for x in ma.run_rules(bad.config, bad, []))
    ok = _report_with({"WIFI": "y", "NET_RX_STACK_SIZE": "4096"})
    assert not any(x.rule_id == "R1" for x in ma.run_rules(ok.config, ok, []))
    off = _report_with({"WIFI": "n", "NET_RX_STACK_SIZE": "1500"})
    assert not any(x.rule_id == "R1" for x in ma.run_rules(off.config, off, []))


def test_r2_r3_stack_floors() -> None:
    bad = _report_with({"TS_NET_ZENOH": "y",
                        "SYSTEM_WORKQUEUE_STACK_SIZE": "1024",
                        "SHELL": "y", "SHELL_STACK_SIZE": "2048"})
    ids = {x.rule_id for x in ma.run_rules(bad.config, bad, [])}
    assert {"R2", "R3"} <= ids


def test_r4_wifi_tx_heap_pressure() -> None:
    bad = _report_with({"WIFI": "y",
                        "ESP32_WIFI_DYNAMIC_TX_BUFFER_NUM": "32",
                        "HEAP_MEM_POOL_SIZE": "58368"})
    assert any(x.rule_id == "R4" for x in ma.run_rules(bad.config, bad, []))
    ok = _report_with({"WIFI": "y",
                       "ESP32_WIFI_DYNAMIC_TX_BUFFER_NUM": "8",
                       "HEAP_MEM_POOL_SIZE": "58368"})
    assert not any(x.rule_id == "R4"
                   for x in ma.run_rules(ok.config, ok, []))


def test_r5_tls_heap_floor() -> None:
    bad = _report_with({"TS_NET_TLS": "y", "HEAP_MEM_POOL_SIZE": "58368"})
    assert any(x.rule_id == "R5" for x in ma.run_rules(bad.config, bad, []))
    ok = _report_with({"TS_NET_TLS": "y", "HEAP_MEM_POOL_SIZE": "65536"})
    assert not any(x.rule_id == "R5"
                   for x in ma.run_rules(ok.config, ok, []))


def test_r6_region_slack_guard() -> None:
    tight = [ma.Region(name="d", origin=0, length=4096, used=3000,
                       reserved=1000)]  # slack 96 < 2048
    f = ma.run_rules({}, _report_with({}, regions=tight), [])
    assert any(x.rule_id == "R6" for x in f)
    roomy = [ma.Region(name="d", origin=0, length=8192, used=3000)]
    assert not any(x.rule_id == "R6"
                   for x in ma.run_rules({}, _report_with({}, regions=roomy), []))


def test_r7_static_tx_observation() -> None:
    f = ma.run_rules({"ESP32_WIFI_STATIC_TX_BUFFER": "y"},
                     _report_with({"ESP32_WIFI_STATIC_TX_BUFFER": "y"}), [])
    r7 = [x for x in f if x.rule_id == "R7"]
    assert len(r7) == 1 and r7[0].severity == "warn"
    assert "教训 41" in r7[0].evidence


def test_overall_tri_state() -> None:
    warn = ma.MemoryReport(map_path="m", config_path="c", pre_build=False,
                           findings=[ma.Finding("R0", "warn", "x")])
    assert warn.overall == "WARN"
    fail = ma.MemoryReport(map_path="m", config_path="c", pre_build=False,
                           findings=[ma.Finding("R0", "warn", "x"),
                                     ma.Finding("R1", "fail", "y")])
    assert fail.overall == "FAIL"
    clean = ma.MemoryReport(map_path="m", config_path="c", pre_build=False)
    assert clean.overall == "PASS"


# ---- audit() 面 ----

def test_audit_fail_closed_missing_files(tmp_path: Path) -> None:
    with pytest.raises(ma.AuditError, match="map 不存在"):
        ma.audit(tmp_path / "no.map", tmp_path / "no.config")
    (tmp_path / "m.map").write_text(REGIONS_TXT, encoding="utf-8")
    with pytest.raises(ma.AuditError, match="config 不存在"):
        ma.audit(tmp_path / "m.map", tmp_path / "no.config")
    (tmp_path / "c.config").write_text("# 空\n", encoding="utf-8")
    with pytest.raises(ma.AuditError, match="未解析出任何键"):
        ma.audit(tmp_path / "m.map", tmp_path / "c.config")


def test_audit_pre_build_flag(tmp_path: Path) -> None:
    (tmp_path / "zephyr_pre0.map").write_text(EXCERPT.read_text("utf-8"),
                                              encoding="utf-8")
    (tmp_path / "c.config").write_text("CONFIG_FOO=y\n", encoding="utf-8")
    rep = ma.audit(tmp_path / "zephyr_pre0.map", tmp_path / "c.config")
    assert rep.pre_build is True


def test_intent_ledger_lists_memory_keys() -> None:
    rep = _report_with({"MAIN_STACK_SIZE": "8192",
                        "HEAP_MEM_POOL_SIZE": "58368",
                        "LV_Z_MEM_POOL_SIZE": "16384",
                        "SOME_UNRELATED": "y",
                        "NOT_A_NUM": "abc"})
    keys = dict(rep._intent_ledger())
    assert keys["MAIN_STACK_SIZE"] == 8192
    assert keys["HEAP_MEM_POOL_SIZE"] == 58368
    assert "SOME_UNRELATED" not in keys and "NOT_A_NUM" not in keys


# ---- 域注册事实 ----

def test_mcp_tool_registered() -> None:
    pack = firmware.FirmwareDomainPack()
    assert "memory_audit" in pack.tools
    assert pack.policy.entries.get("memory_audit") == "confirm"
