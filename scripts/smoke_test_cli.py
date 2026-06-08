from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(args: list[str], *, env: dict[str, str] | None = None, expect_code: int = 0) -> str:
    proc = subprocess.run(args, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    if proc.returncode != expect_code:
        raise SystemExit(f"command failed: {' '.join(args)}\nexpected {expect_code}, got {proc.returncode}\n{proc.stdout}")
    return proc.stdout


def main() -> int:
    help_output = run([sys.executable, "-m", "football_live_agent.cli", "--help"])
    for command in ["onboard", "doctor", "repair", "where-to-watch", "once", "watch"]:
        if command not in help_output:
            raise SystemExit(f"CLI help missing command: {command}")

    with tempfile.TemporaryDirectory() as tmp:
        env = os.environ.copy()
        env["FOOTBALL_AGENT_DATA_DIR"] = tmp
        output = run([sys.executable, "-m", "football_live_agent.cli", "where-to-watch"], env=env, expect_code=1)
        # where-to-watch requires preferences, so this should be blocked clearly before onboarding.
        if "No preferences found" not in output:
            raise SystemExit("missing clear onboarding error for empty data dir")

    print("CLI smoke validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
