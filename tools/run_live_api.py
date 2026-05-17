#!/usr/bin/env python3
"""Run the Ikusa Forge local live combat API server."""

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SIM_DIR = REPO_ROOT / "sim-python"
if str(SIM_DIR) not in sys.path:
    sys.path.insert(0, str(SIM_DIR))

from ikusa_sim.live_api import BattleSessionManager, LiveApiError, create_live_api_server  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Ikusa Forge Live Combat API / 实时战斗 API.")
    parser.add_argument("--config", type=Path, default=Path("config/generated"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        manager = BattleSessionManager(args.config)
        server = create_live_api_server(args.host, args.port, manager)
    except LiveApiError as exc:
        print(f"Live API failed to start: {exc.message}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"Live API failed to bind {args.host}:{args.port}: {exc}", file=sys.stderr)
        return 1

    base_url = f"http://{args.host}:{args.port}"
    print("Ikusa Forge Live Combat API / 实时战斗 API")
    print(f"- URL: {base_url}")
    print(f"- health: GET {base_url}/api/health")
    print(f"- start: POST {base_url}/api/battle/start")
    print("- example body: {\"battle_id\":\"demo_001\",\"seed\":1001}")
    print("- Press Ctrl+C to stop")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nLive API stopping")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
