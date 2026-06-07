from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from football_live_agent.models import Event, Match

MAX_RECENT_ITEMS = 50


class FootballMemory:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data = self._load()

    def record_match(self, match: Match) -> None:
        self._data["last_checked_at"] = _now()
        matches = self._data.setdefault("matches", {})
        matches[match.fixture_id] = _match_data(match)
        self._data["last_match_id"] = match.fixture_id
        self._save()

    def record_event(self, match: Match, event: Event, notified: bool) -> None:
        self.record_match(match)
        item = {
            "recorded_at": _now(),
            "notified": notified,
            "match": _match_data(match),
            "event": _event_data(event),
        }
        self._append_recent("events", item)
        if notified:
            self._append_recent("notifications", item)
        self._save()

    def summary(self) -> str:
        notifications = self._data.get("notifications", [])
        if notifications:
            item = notifications[-1]
            match = item["match"]
            event = item["event"]
            player = f" - {event['player']}" if event.get("player") else ""
            return (
                f"Last football alert: {event['minute_display']} {event['event_type'].upper()} "
                f"{match['scoreline']} ({event['team']}{player})."
            )

        last_match_id = self._data.get("last_match_id")
        matches = self._data.get("matches", {})
        if last_match_id and last_match_id in matches:
            match = matches[last_match_id]
            elapsed = "unknown minute" if match["elapsed"] is None else f"{match['elapsed']}'"
            return f"Last checked match: {match['scoreline']} at {elapsed}."

        return "No football memory yet."

    def to_dict(self) -> dict[str, Any]:
        return self._data

    def _append_recent(self, key: str, item: dict[str, Any]) -> None:
        items = list(self._data.setdefault(key, []))
        items.append(item)
        self._data[key] = items[-MAX_RECENT_ITEMS:]

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"matches": {}, "events": [], "notifications": []}
        with self.path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2, sort_keys=True)
            handle.write("\n")


def _match_data(match: Match) -> dict[str, Any]:
    return {
        "fixture_id": match.fixture_id,
        "home_team": match.home_team,
        "away_team": match.away_team,
        "league": match.league,
        "status": match.status,
        "elapsed": match.elapsed,
        "home_goals": match.home_goals,
        "away_goals": match.away_goals,
        "scoreline": match.scoreline,
    }


def _event_data(event: Event) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "fixture_id": event.fixture_id,
        "event_type": event.event_type,
        "minute": event.minute,
        "minute_display": event.display_minute,
        "team": event.team,
        "player": event.player,
        "detail": event.detail,
    }


def _now() -> str:
    return datetime.now(UTC).isoformat()
