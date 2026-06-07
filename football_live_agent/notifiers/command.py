from __future__ import annotations

import shlex
import subprocess
from collections.abc import Callable, Sequence
from typing import Any

from football_live_agent.models import Event, Match
from football_live_agent.notifiers.console import format_notification

Runner = Callable[..., Any]


class CommandNotifier:
    def __init__(
        self,
        command_template: Sequence[str],
        channel: str | None = None,
        target: str | None = None,
        runner: Runner = subprocess.run,
    ) -> None:
        self.command_template = list(command_template)
        self.channel = channel or ""
        self.target = target or ""
        self.runner = runner

    def send(self, match: Match, event: Event) -> None:
        message = format_notification(match, event)
        args = [
            part.format(message=message, channel=self.channel, target=self.target)
            for part in self.command_template
        ]
        result = self.runner(args, check=False, capture_output=True, text=True, timeout=30)
        if getattr(result, "returncode", 0) != 0:
            stderr = getattr(result, "stderr", "") or "unknown command error"
            raise RuntimeError(f"Channel command failed: {stderr}")


def build_platform_command(platform: str) -> list[str]:
    normalized = platform.strip().casefold()
    if normalized == "openclaw":
        return ["openclaw", "message", "send", "--channel", "{channel}", "--target", "{target}", "--message", "{message}"]
    if normalized == "hermes":
        return ["hermes", "message", "send", "--channel", "{channel}", "--target", "{target}", "--message", "{message}"]
    raise ValueError(f"Unsupported command platform: {platform}")


def split_command_template(template: str) -> list[str]:
    return shlex.split(template)
