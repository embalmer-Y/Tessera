# SPDX-License-Identifier: Apache-2.0
"""CLI 入口（`serve` = MCP 网关〔MA1〕；`run` = 独立终端门面〔AG6 · DEC-12 v1.1〕）。"""

from __future__ import annotations

import argparse
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
    run.add_argument("--deploy", action="store_true",
                     help="收敛后自动部署（app_deploy 链；strict 审批仍拦）")
    args = parser.parse_args(argv)

    if args.command == "serve":
        from tessera_agent.common.config import load_config
        from tessera_agent.gateway.server import run_server

        run_server(load_config(), transport=args.transport,
                   host=args.host, port=args.port)
        return 0
    if args.command == "run":
        return _run_command(args)
    parser.print_help()
    return 0


def _run_command(args) -> int:
    """终端门面驱动（LLD-A09 §3）。退出码：0 = PACKAGED（--deploy 含判据）；
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
    except Exception as exc:  # noqa: BLE001——启动期配置错误如实报
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
        try:
            out = asyncio.run(app_deploy(ctx, result.artifact.package_path, pub))
        except TaError as exc:
            print(f"部署失败：{exc.message}", file=sys.stderr)
            return 1
        print(f"部署确认：{out['node']}/{out['cube']}")
    return 0


def _cli_ctx(cfg):
    """终端门面用最小 AppContext（与 MCP 门面同构的轻量装配）。"""
    from tessera_agent.common.limits import ContextBudget
    from tessera_agent.platform import AppContext

    return AppContext(cfg=cfg, budget=ContextBudget(cfg.context_window))


if __name__ == "__main__":
    sys.exit(main())
