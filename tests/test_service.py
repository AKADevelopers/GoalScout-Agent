import sys

from football_live_agent.config import Settings
from football_live_agent.service import build_watch_command, pid_status


def test_build_watch_command_uses_module_runner(tmp_path):
    settings = Settings(
        provider="sportscore",
        poll_seconds=60,
        data_dir=tmp_path,
        api_football_key=None,
        webhook_url=None,
        delivery="console",
        channel_command=None,
        channel=None,
        target=None,
        console_enabled=True,
    )

    command = build_watch_command(settings, python_executable=sys.executable)

    assert command == [sys.executable, "-m", "football_live_agent.cli", "watch"]


def test_pid_status_reports_not_running_when_missing(tmp_path):
    assert pid_status(tmp_path / "watcher.pid") == "not running"
