# SPDX-License-Identifier: Apache-2.0
"""CLI 入口（`serve` = MCP 网关〔MA1〕；`run` = 独立终端门面〔AG6 · DEC-12 v1.1〕）。"""

from __future__ import annotations

import argparse
import json
import sys

from tessera_agent import __version__


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tessera-agent", description="Tessera AI Agent（MCP server + 独立终端）"
    )
    parser.add_argument("--version", action="version", version=f"tessera-agent {__version__}")
    sub = parser.add_subparsers(dest="command")
    serve = sub.add_parser("serve", help="启动 MCP 网关（默认 stdio）")
    serve.add_argument("--transport", choices=["stdio", "http"], default="stdio",
                       help="V0.4.0 M12/A7：http = Streamable HTTP 远程门面")
    serve.add_argument("--host", default="127.0.0.1",
                       help="http 传输绑定地址（外网暴露自担）")
    serve.add_argument("--port", type=int, default=9956, help="http 传输端口")

    run = sub.add_parser("run", help="独立终端门面：提需求 → 创作循环 → 交付包")
    run.add_argument("requirement", nargs="*", help="需求文本（省略则交互输入）")
    run.add_argument("--resume", metavar="TASK_ID", default=None,
                     help="续跑既有创作任务（工作区快照）")
    run.add_argument("--key-path", default=None,
                     help="签名私钥路径（PACKAGED 前置；缺省查 agent/keys/ 下 .key）")
    run.add_argument("--yes", action="store_true",
                     help="非交互：问询取默认项（strict 审批仍拦——安全默认）")
    run.add_argument("--json", action="store_true", help="JSONL 流式输出（CI）")
    run.add_argument("--no-plan-confirm", action="store_true",
                     help="跳过计划确认（默认确认）")
    run.add_argument("--serial-port", default=None, metavar="PORT",
                     help="S8 部署判据窗串口（配 --deploy——判据 miss 自动修复轮）")
    run.add_argument("--deploy", action="store_true",
                     help="收敛后自动部署（app_deploy 链；strict 审批仍拦）")

    replay = sub.add_parser("replay", help="决策链时间线回放（D5 · 审计流只读面）")
    replay.add_argument("--day", default=None,
                        help='审计日 YYYYMMDD（缺省 = 今日；"all" = 合并全部）')
    replay.add_argument("--task-id", default=None, help="按任务句柄过滤")
    replay.add_argument("--tool", default=None, help="按工具名过滤")
    replay.add_argument("--limit", type=int, default=500, help="尾部截取（缺省 500）")
    replay.add_argument("--json", action="store_true", help="结构化输出（W1 时间线同源）")

    val = sub.add_parser("validate",
                         help="板卡验证域：画像驱动确定性检查流水线（LLD-agent-board-validation）")
    val.add_argument("board_id", help="画像 id（agent/boards/<id>.toml）")
    val.add_argument("--checks", default=None, metavar="C1,C3",
                     help="检查子集（缺省全序 C1-C6）")
    val.add_argument("--stop-on-fail", action="store_true",
                     help="首个 FAIL 后提前收（余项记派生 SKIP）")
    val.add_argument("--out", default=None, metavar="PATH",
                     help="报告 JSON 落盘路径")
    val.add_argument("--json", action="store_true",
                     help="打印 JSON 报告（缺省人读形态）")

    mem = sub.add_parser("memory-audit",
                         help="构建期内存审计（LLD-agent-memory-planner · DEC-70；本地只读）")
    mem.add_argument("--map", required=True, metavar="PATH",
                     help="GNU ld map（zephyr/zephyr.map；pre0 图亦可）")
    mem.add_argument("--config", required=True, metavar="PATH",
                     help="Kconfig 生效值（zephyr/.config）")
    mem.add_argument("--prj-conf", default=None, metavar="PATH",
                     help="prj.conf 对照（R0 声明≠生效检测）")
    mem.add_argument("--out", default=None, metavar="PATH",
                     help="报告 JSON 落盘路径")
    mem.add_argument("--json", action="store_true",
                     help="打印 JSON 报告（缺省人读形态）")
    llmc = sub.add_parser(
        "llm-check",
        help="LLM 端点探针：URL/连通/协议/模型列表/KEY 有效性/模型可用性（DEC-80）")
    llmc.add_argument("--url", default=None,
                      help="端点 base（缺省 = $ANTHROPIC_BASE_URL）")
    llmc.add_argument("--key-env", default="ANTHROPIC_API_KEY",
                      help="密钥所在环境变量名（缺省 ANTHROPIC_API_KEY）")
    llmc.add_argument("--model", default=None,
                      help="指定冒烟模型（缺省自动从模型表挑 flash/mini 类）")
    llmc.add_argument("--timeout", type=float, default=20.0, help="每请求超时秒")
    llmc.add_argument("--json", action="store_true", help="结构化输出（缺省人读形态）")

    ev = sub.add_parser(
        "agent-eval",
        help="Agent 能力评估基准：任务谱 T1-T5 × headless 评分（AC-1 · DEC-81）")
    ev.add_argument("--tasks", default=None, metavar="T1,T2",
                    help="任务 id 子集（缺省全谱 T1-T5）")
    ev.add_argument("--config", default=None, metavar="PATH",
                    help="agent config.toml 路径（缺省 <repo>/agent/config.toml）")
    ev.add_argument("--key", default=None, metavar="PATH",
                    help="TSAP 签名私钥路径（缺省 fixtures/ts-test-root.key）")
    ev.add_argument("--timeout-per-task", type=float, default=600.0,
                    help="单任务墙钟上限秒（缺省 600）")
    ev.add_argument("--with-sim", action="store_true",
                    help="sim 判据段（v1 = 装载冒烟，场景定义随 AC-3 补全）")
    ev.add_argument("--out-dir", default=None, metavar="PATH",
                    help="报告落盘目录（缺省 docs/evidence/）")
    ev.add_argument("--json", action="store_true",
                    help="打印 JSON 报告（缺省人读形态）")

    args = parser.parse_args(argv)

    if args.command == "serve":
        from tessera_agent.common.config import load_config
        from tessera_agent.gateway.server import run_server

        run_server(load_config(), transport=args.transport,
                   host=args.host, port=args.port)
        return 0
    if args.command == "run":
        return _run_command(args)
    if args.command == "replay":
        return _replay_command(args)
    if args.command == "validate":
        return _validate_command(args)
    if args.command == "memory-audit":
        return _memory_audit_command(args)
    if args.command == "llm-check":
        return _llm_check_command(args)
    if args.command == "agent-eval":
        return _agent_eval_command(args)
    parser.print_help()
    return 0


def _agent_eval_command(args) -> int:
    """AC-1 能力评估基准 CLI（DEC-81）——任务谱顺序真跑 + headless 评分。"""
    import asyncio
    import sys as _sys
    from pathlib import Path

    from tessera_agent.common.config import load_config
    from tessera_agent.eval import report as eval_report
    from tessera_agent.eval import scorer as eval_scorer
    from tessera_agent.eval import suite as eval_suite

    repo = Path(__file__).resolve().parents[2]
    try:
        tasks = eval_suite.select(
            args.tasks.split(",") if args.tasks else None)
    except ValueError as exc:
        print(f"✗ {exc}", file=_sys.stderr)
        return 2

    key_path = args.key or str(
        repo / "agent" / "tests" / "fixtures" / "ts-test-root.key")
    if not Path(key_path).is_file():
        print(f"✗ 签名私钥不存在: {key_path}", file=_sys.stderr)
        return 2

    cfg_path = args.config or str(repo / "agent" / "config.toml")
    cfg = load_config(cfg_path)

    print(f"agent-eval：{len(tasks)} 任务 模型={cfg.default_model} "
          f"单任务上限={args.timeout_per_task:.0f}s sim={'on' if args.with_sim else 'skip'}",
          flush=True)

    async def _run():
        scores = []
        for t in tasks:
            print(f"\n===== {t.id} {t.title} =====", flush=True)

            def log(s: str, _t=t) -> None:
                print(f"  [{_t.id}] {s}", flush=True)

            sc = await eval_scorer.run_task(
                cfg, t, key_path, timeout_s=args.timeout_per_task,
                with_sim=args.with_sim, log_fn=log)
            failed = [k for k, v in sc.checks.items() if not v["ok"]]
            print(f"  --> {sc.verdict} 轮数={sc.rounds} 耗时={sc.elapsed_s:.1f}s"
                  f" 未过={failed or '—'}", flush=True)
            scores.append(sc)
        return scores

    scores = asyncio.run(_run())
    rep = eval_report.report_dict(scores, model=str(cfg.default_model),
                                  with_sim=args.with_sim)
    out_dir = args.out_dir or str(repo / "docs" / "evidence")
    from datetime import datetime as _dt
    stem = "eval-" + _dt.now().strftime("%Y%m%d-%H%M%S")
    jp, mp = eval_report.write_reports(rep, out_dir, stem)
    summary = rep["summary"]
    print(f"\n===== 汇总 PASS={summary['pass']} PARTIAL={summary['partial']} "
          f"FAIL={summary['fail']} 通过率={summary['pass_rate']} =====", flush=True)
    print(f"报告：{mp}\n      {jp}", flush=True)
    if args.json:
        import json as _json
        print(_json.dumps(rep, ensure_ascii=False, indent=2))
    return 0 if summary["fail"] == 0 else 1


def _llm_check_command(args) -> int:
    """LLM 端点探针 CLI（DEC-80）——key 经环境变量（--key-env 指名，值不入 argv）。"""
    import os
    import sys as _sys

    from tessera_agent.domain import llm_probe

    url = args.url or os.environ.get("ANTHROPIC_BASE_URL", "")
    if not url:
        print("✗ 缺少 URL：--url 或环境 ANTHROPIC_BASE_URL", file=_sys.stderr)
        return 2
    key = os.environ.get(args.key_env, "")
    if not key:
        print(f"✗ 环境变量 {args.key_env} 未设置（key 不经命令行参数传递）", file=_sys.stderr)
        return 2
    rep = llm_probe.probe(url, key, model=args.model, timeout_s=args.timeout)
    if args.json:
        import json as _json
        print(_json.dumps(rep.to_dict(), ensure_ascii=False, indent=1))
    else:
        print(llm_probe.render_report(rep))
    return 0 if rep.overall_ok else 1


def _validate_command(args) -> int:
    """板卡验证 CLI（LLD-agent-board-validation §5）。退出码：0 = PASS；1 = FAIL/DEGRADED；
    2 = 配置/画像/参数错误。同步阻塞面（检查含串口抓取与部署链）。"""
    from pathlib import Path

    from tessera_agent.common.config import load_config
    from tessera_agent.domain import board_validation as bv

    try:
        cfg = load_config()
    except Exception as exc:  # noqa: BLE001 —— 启动期配置错误如实报
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    path = Path(cfg.workspace_repo) / "agent" / "boards" / f"{args.board_id}.toml"
    try:
        profile = bv.load_profile(path)
        checks = ([c.strip() for c in args.checks.split(",")]
                  if args.checks else None)
    except bv.ProfileError as exc:
        print(f"画像错误：{exc}", file=sys.stderr)
        return 2

    def progress_cb(p: dict) -> None:
        print(f"[bv] {p['check']} {p.get('verdict', '…')}"
              f" ({p['done']}/{p['total']})", file=sys.stderr)

    # C6 部署链须 AppContext（复验/发现/租约）——与 run 门面同款最小装配
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    ctx = AppContext(cfg=cfg, budget=ContextBudget(cfg.context_window))
    transport = bv.LiveTransport(cfg, ctx=ctx)
    try:
        report = bv.validate(profile, transport, checks=checks,
                             stop_on_fail=args.stop_on_fail,
                             progress_cb=progress_cb)
    except bv.ProfileError as exc:
        print(f"参数错误：{exc}", file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(
            json.dumps(report.to_json(), ensure_ascii=False, indent=2),
            encoding="utf-8")
    if args.json:
        print(json.dumps(report.to_json(), ensure_ascii=False, indent=2))
    else:
        print(report.render())
    return 0 if report.overall == "PASS" else 1


def _memory_audit_command(args) -> int:
    """内存审计 CLI（LLD-agent-memory-planner §5）。退出码：0 = PASS；1 = WARN/FAIL；
    2 = 参数/输入错误。本地只读面（无 LLM 无网络）。"""
    from pathlib import Path

    from tessera_agent.domain import memory_audit as ma

    try:
        report = ma.audit(args.map, args.config, args.prj_conf)
    except ma.AuditError as exc:
        print(f"审计输入错误：{exc}", file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(
            json.dumps(report.to_json(), ensure_ascii=False, indent=2),
            encoding="utf-8")
    if args.json:
        print(json.dumps(report.to_json(), ensure_ascii=False, indent=2))
    else:
        print(report.render())
    return 0 if report.overall == "PASS" else 1


def _replay_command(args) -> int:
    """D5（DEC-67①）：审计流时间线回放（只读；无 LLM 无网络）。"""
    from pathlib import Path

    from tessera_agent.audit_replay import load_timeline, render_timeline
    from tessera_agent.common.config import load_config

    try:
        cfg = load_config()
    except Exception as exc:  # noqa: BLE001 —— 启动期配置错误如实报
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2
    tl = load_timeline(Path(cfg.audit_dir), day=args.day,
                       task_id=args.task_id, tool=args.tool,
                       limit=args.limit)
    if args.json:
        print(json.dumps(tl, ensure_ascii=False, indent=2))
    else:
        print(render_timeline(tl))
    return 0


def _spec_patterns(spec: str) -> list[str]:
    """S8 判据源 = spec【判据】节（NV-2 单一事实源；缺节 = 空 = 无判据窗）。"""
    from tessera_agent.tools_diag import spec_gate as _sg

    return list(_sg.check_spec(spec).pass_patterns)


def _post_check(ctx, node: str, cube: str, port: str,
                patterns: list[str]) -> dict:
    from tessera_agent.tools_net import deploy as net_deploy
    from tessera_agent.tools_net.zenoh_service import ZenohService

    with ZenohService(ctx.cfg.router_locator) as svc:
        return net_deploy.post_deploy_check(
            svc, node, cube, serial_port=port, window_s=8.0,
            pass_patterns=patterns)


def _fmt_s8_evidence(diag: dict) -> str:
    d = diag.get("diag") or {}
    return (f"category={d.get('category')} summary={d.get('summary')}\n"
            f"repair_hint={d.get('repair_hint')}\n"
            f"evidence={d.get('evidence')}")


def _run_command(args) -> int:
    """终端门面驱动（LLD-agent-terminal-facade §3）。退出码：0 = PACKAGED（--deploy 含判据）；
    1 = FAILED/ABORTED/INTERRUPTED；2 = 参数/环境错误。"""
    import asyncio
    from pathlib import Path

    from tessera_agent.cli.facade import TerminalFrontend, TerminalOptions
    from tessera_agent.common.config import load_config
    from tessera_agent.common.errors import TaError
    from tessera_agent.creation.loop import PACKAGED
    from tessera_agent.creation.snapshot import load as snap_load
    from tessera_agent.creation.workspace import Workspace
    from tessera_agent.domain.app_chain import PydanticLoopRunner
    from tessera_agent.domain.firmware_creation import FirmwareCreationVerifier
    from tessera_agent.tools_diag import spec_gate

    try:
        cfg = load_config()
    except Exception as exc:  # noqa: BLE001 —— 启动期配置错误如实报
        print(f"配置错误：{exc}", file=sys.stderr)
        return 2

    spec = " ".join(args.requirement).strip()
    if not spec and not args.resume:
        try:
            spec = input("需求：").strip()
        except EOFError:
            spec = ""
    if not spec and not args.resume:
        print("未提供需求（且非 --resume）", file=sys.stderr)
        return 2

    key_path = args.key_path
    if key_path is None:
        keys_dir = Path(cfg.workspace_repo) / "agent" / "keys"
        cands = sorted(keys_dir.glob("*.key")) if keys_dir.is_dir() else []
        if cands:
            key_path = str(cands[0])
        else:
            print("未找到签名私钥（--key-path 或 agent/keys/*.key）", file=sys.stderr)
            return 2

    repo = Path(cfg.workspace_repo)
    base = repo / "agent" / "workspace"
    ro_roots = [p for p in (
        repo / "firmware" / "module" / "tessera" / "include",
        repo / "agent" / "skills",
        repo / "docs",
    ) if p.is_dir()]

    snap = None
    if args.resume:
        try:
            ws = Workspace.open(base, args.resume, ro_roots=ro_roots)
            snap = snap_load(ws)
        except TaError as exc:
            print(f"resume 失败：{exc.message}", file=sys.stderr)
            return 2
        task_id = args.resume
    else:
        import secrets

        task_id = f"t-{secrets.token_hex(4)}"
        ws = Workspace.create(base, task_id, ro_roots=ro_roots)

    ctx = _cli_ctx(cfg)
    fe = TerminalFrontend()
    runner = PydanticLoopRunner(ctx, ws)
    verifier = FirmwareCreationVerifier()
    options = TerminalOptions(yes=args.yes, json_mode=args.json,
                              plan_confirm=not args.no_plan_confirm)

    async def _drive():
        if snap is not None:
            return await fe.resume(spec or "(resume)", ws, verifier, runner,
                                   snap, options=options, key_path=key_path)
        gate = spec_gate.check_spec(spec)
        if gate.errors:
            for e in gate.errors:
                print(f"spec-gate: {e}", file=sys.stderr)
            return None
        return await fe.run(spec, ws, verifier, runner, options=options,
                            criteria=list(gate.pass_patterns),
                            key_path=key_path)

    try:
        result = asyncio.run(_drive())
    except KeyboardInterrupt:
        print(f"\n中断（快照随轮末落盘；--resume {task_id} 续跑）", file=sys.stderr)
        return 1
    except TaError as exc:
        print(f"错误：{exc.message}", file=sys.stderr)
        return 1
    if result is None:
        return 2
    if result.state != PACKAGED:
        return 1

    if args.deploy:
        from tessera_agent.domain.app_chain import app_deploy

        pub = str(Path(key_path).expanduser().with_suffix(".pub"))
        # S8（P1-5 · HLD-agent §4）：部署 → 判据窗检查（--serial-port）→
        # miss = 诊断证据回注创作循环修复轮 → 再打包再部署（≤S8_REPAIR_MAX，
        # repair 轮计入循环预算）。无串口 = 仅部署确认（S5 原语义）。
        patterns = list(_spec_patterns(spec))
        for attempt in range(3):  # 首部署 + 2 修复窗
            try:
                out = asyncio.run(app_deploy(ctx, result.artifact.package_path, pub))
            except TaError as exc:
                print(f"部署失败：{exc.message}", file=sys.stderr)
                return 1
            print(f"部署确认：{out['node']}/{out['cube']}")
            if not args.serial_port or not patterns:
                return 0
            diag = asyncio.run(_post_check(ctx, out["node"], out["cube"],
                                           args.serial_port, patterns))
            if diag.get("criteria_pass") is True:
                print(f"S8 判据命中：{diag.get('pass_patterns')}")
                return 0
            if diag.get("criteria_pass") is None:
                print(f"S8 判据未验证（抓取失败/无窗）：{diag.get('diag_error', '—')}",
                      file=sys.stderr)
                return 0
            print(f"S8 判据 miss（第 {attempt + 1} 窗）：{diag.get('diag')}",
                  file=sys.stderr)
            if attempt == 2:
                print("S8 修复窗耗尽——证据在工作区/审计流", file=sys.stderr)
                return 1
            result = asyncio.run(
                fe.repair(_fmt_s8_evidence(diag), reason="deploy-criteria"))
            if result.state != PACKAGED or result.artifact is None:
                print("S8 修复轮未再收敛——证据归档", file=sys.stderr)
                return 1
    return 0


def _cli_ctx(cfg):
    """终端门面用最小 AppContext（与 MCP 门面同构的轻量装配）。"""
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    return AppContext(cfg=cfg, budget=ContextBudget(cfg.context_window))


if __name__ == "__main__":
    sys.exit(main())
