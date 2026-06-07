from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

from football_live_agent.config import Settings


def build_watch_command(settings: Settings, python_executable: str | None = None) -> list[str]:
    executable = python_executable or sys.executable
    return [executable, "-m", "football_live_agent.cli", "watch"]


def start_background(settings: Settings, cwd: Path | None = None) -> int:
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    log_path = settings.data_dir / "watcher.log"
    pid_path = settings.data_dir / "watcher.pid"
    command = build_watch_command(settings)
    env = os.environ.copy()
    env["FOOTBALL_AGENT_DATA_DIR"] = str(settings.data_dir)

    with log_path.open("a", encoding="utf-8") as log:
        kwargs = {
            "cwd": str(cwd or Path.cwd()),
            "env": env,
            "stdout": log,
            "stderr": subprocess.STDOUT,
            "stdin": subprocess.DEVNULL,
        }
        if os.name == "nt":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            kwargs["start_new_session"] = True
        process = subprocess.Popen(command, **kwargs)

    pid_path.write_text(str(process.pid), encoding="utf-8")
    return process.pid


def pid_status(pid_path: Path) -> str:
    if not pid_path.exists():
        return "not running"
    raw = pid_path.read_text(encoding="utf-8").strip()
    if not raw:
        return "not running"
    return f"running with pid {raw}"


def stop_background(pid_path: Path) -> str:
    if not pid_path.exists():
        return "not running"
    raw = pid_path.read_text(encoding="utf-8").strip()
    if not raw:
        pid_path.unlink(missing_ok=True)
        return "not running"
    try:
        os.kill(int(raw), signal.SIGTERM)
    except OSError:
        pid_path.unlink(missing_ok=True)
        return "not running"
    pid_path.unlink(missing_ok=True)
    return f"stopped pid {raw}"
