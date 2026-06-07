from __future__ import annotations

from typing import Protocol

from football_live_agent.models import Event, Match


class Notifier(Protocol):
    def send(self, match: Match, event: Event) -> None:
        ...
