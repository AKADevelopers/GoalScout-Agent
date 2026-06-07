from __future__ import annotations

from typing import Protocol

from football_live_agent.models import Event, Match


class FootballProvider(Protocol):
    def live_matches(self) -> list[Match]:
        ...

    def events_for_fixture(self, fixture_id: str) -> list[Event]:
        ...
