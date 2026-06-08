from __future__ import annotations

import time
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from football_live_agent.memory import FootballMemory
from football_live_agent.models import Event, Match, Preferences
from football_live_agent.notifiers.base import Notifier
from football_live_agent.providers.base import FootballProvider
from football_live_agent.state import JsonState

KICKOFF_REMINDER_WINDOW_MINUTES = 30
FAST_POLL_SECONDS = 15
MID_POLL_SECONDS = 30
SLOW_POLL_SECONDS = 45
FAILURE_BACKOFF_MULTIPLIER = 2
FAILURE_BACKOFF_CAP = 300


def run_once(
    provider: FootballProvider,
    preferences: Preferences,
    state: JsonState,
    notifiers: Sequence[Notifier],
    memory: FootballMemory | None = None,
    live_matches: Sequence[Match] | None = None,
    upcoming_matches: Sequence[Match] | None = None,
) -> int:
    sent = 0
    current_live_matches = list(live_matches) if live_matches is not None else list(provider.live_matches())
    current_upcoming_matches = list(upcoming_matches) if upcoming_matches is not None else _all_matches(provider)

    for match in current_live_matches:
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

    for reminder in _kickoff_reminders(preferences, current_upcoming_matches):
        match, event = reminder
        if not state.mark_seen(event):
            continue
        if memory is not None:
            memory.record_event(match, event, notified=True)
        for notifier in notifiers:
            notifier.send(match, event)
        sent += 1

    return sent


def calculate_poll_delay(
    base_seconds: int,
    preferences: Preferences,
    live_matches: Sequence[Match],
    upcoming_matches: Sequence[Match],
) -> int:
    base = max(10, int(base_seconds))
    if _has_relevant_live_match(preferences, live_matches):
        return min(base, FAST_POLL_SECONDS)
    if live_matches:
        return min(base, MID_POLL_SECONDS)
    if _has_due_kickoff_reminder(preferences, upcoming_matches):
        return min(base, MID_POLL_SECONDS)
    if upcoming_matches:
        return min(base, SLOW_POLL_SECONDS)
    return base


def watch_forever(
    provider: FootballProvider,
    preferences: Preferences,
    state: JsonState,
    notifiers: Sequence[Notifier],
    poll_seconds: int,
    memory: FootballMemory | None = None,
) -> None:
    delay = max(10, int(poll_seconds))
    while True:
        try:
            live_matches = list(provider.live_matches())
            upcoming_matches = _all_matches(provider)
            run_once(
                provider,
                preferences,
                state,
                notifiers,
                memory=memory,
                live_matches=live_matches,
                upcoming_matches=upcoming_matches,
            )
            delay = calculate_poll_delay(delay, preferences, live_matches, upcoming_matches)
        except Exception as exc:
            print(f"Watcher cycle failed: {exc}")
            delay = min(max(delay * FAILURE_BACKOFF_MULTIPLIER, delay), FAILURE_BACKOFF_CAP)
        time.sleep(delay)


def _all_matches(provider: FootballProvider) -> list[Match]:
    all_matches = getattr(provider, "all_matches", None)
    if callable(all_matches):
        return list(all_matches())
    return list(provider.live_matches())


def _kickoff_reminders(preferences: Preferences, upcoming_matches: Sequence[Match]) -> list[tuple[Match, Event]]:
    if "kickoff" not in preferences._alert_types:
        return []
    reminders: list[tuple[Match, Event]] = []
    now = datetime.now(UTC)
    for match in upcoming_matches:
        kickoff = _parse_datetime(match.kickoff_at)
        if kickoff is None:
            continue
        delta = kickoff - now
        minutes = delta.total_seconds() / 60
        if minutes < 0 or minutes > KICKOFF_REMINDER_WINDOW_MINUTES:
            continue
        event = Event(
            event_id=f"{match.fixture_id}-kickoff-reminder",
            fixture_id=match.fixture_id,
            event_type="kickoff",
            minute=None,
            team=match.home_team,
            player="",
            detail="Kickoff reminder",
        )
        if preferences.should_notify(match, event):
            reminders.append((match, event))
    return reminders


def _has_relevant_live_match(preferences: Preferences, live_matches: Sequence[Match]) -> bool:
    if not live_matches:
        return False
    if not preferences.favorite_teams and not preferences.favorite_players and not preferences.competitions and not preferences.favorite_country.strip():
        return True
    return any(preferences.should_notify(match, Event("live", match.fixture_id, "goal", None, match.home_team, "", "")) for match in live_matches)


def _has_due_kickoff_reminder(preferences: Preferences, upcoming_matches: Sequence[Match]) -> bool:
    return bool(_kickoff_reminders(preferences, upcoming_matches))


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
