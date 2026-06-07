from __future__ import annotations

import time
from collections.abc import Sequence

from football_live_agent.memory import FootballMemory
from football_live_agent.models import Preferences
from football_live_agent.notifiers.base import Notifier
from football_live_agent.providers.base import FootballProvider
from football_live_agent.state import JsonState


def run_once(
    provider: FootballProvider,
    preferences: Preferences,
    state: JsonState,
    notifiers: Sequence[Notifier],
    memory: FootballMemory | None = None,
) -> int:
    sent = 0
    for match in provider.live_matches():
        if memory is not None:
            memory.record_match(match)
        for event in provider.events_for_fixture(match.fixture_id):
            if not preferences.should_notify(match, event):
                if memory is not None:
                    memory.record_event(match, event, notified=False)
                continue
            if not state.mark_seen(event):
                if memory is not None:
                    memory.record_event(match, event, notified=False)
                continue
            for notifier in notifiers:
                notifier.send(match, event)
            if memory is not None:
                memory.record_event(match, event, notified=True)
            sent += 1
    return sent


def watch_forever(
    provider: FootballProvider,
    preferences: Preferences,
    state: JsonState,
    notifiers: Sequence[Notifier],
    poll_seconds: int,
    memory: FootballMemory | None = None,
) -> None:
    while True:
        try:
            run_once(provider, preferences, state, notifiers, memory=memory)
        except Exception as exc:
            print(f"Watcher cycle failed: {exc}")
        time.sleep(poll_seconds)
