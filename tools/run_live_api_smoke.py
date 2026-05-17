#!/usr/bin/env python3
"""Start the Live Combat API server, run smoke, and stop it."""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Sequence
from urllib import error, request


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from smoke_live_api import main as smoke_main  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Live Combat API smoke with a managed server process.")
    parser.add_argument("--config", type=Path, default=Path("config/generated"))
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--battle", default="demo_001")
    parser.add_argument("--seed", type=int, default=1001)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    script = TOOLS_DIR / "run_live_api.py"
    process = subprocess.Popen(
        [
            sys.executable,
            str(script),
            "--config",
            str(args.config),
            "--host",
            args.host,
            "--port",
            str(args.port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
    )

    try:
        if not _wait_for_health(args.host, args.port, process):
            stdout, stderr = _stop_process(process)
            print("Live API managed smoke failed: server did not become ready", file=sys.stderr)
            if stdout:
                print(stdout, file=sys.stderr)
            if stderr:
                print(stderr, file=sys.stderr)
            return 1

        return smoke_main(
            [
                "--host",
                args.host,
                "--port",
                str(args.port),
                "--battle",
                args.battle,
                "--seed",
                str(args.seed),
            ]
        )
    finally:
        if process.poll() is None:
            _stop_process(process)


def _wait_for_health(host: str, port: int, process: subprocess.Popen) -> bool:
    url = f"http://{host}:{port}/api/health"
    deadline = time.time() + 10
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        try:
            with request.urlopen(url, timeout=1) as response:
                return response.status == 200
        except error.URLError:
            time.sleep(0.2)
    return False


def _stop_process(process: subprocess.Popen) -> tuple:
    process.terminate()
    try:
        return process.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        return process.communicate(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
