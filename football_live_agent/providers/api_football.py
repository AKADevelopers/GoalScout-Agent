from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from football_live_agent.models import Event, Match

BASE_URL = "https://v3.football.api-sports.io"

EVENT_TYPE_MAP = {
    "goal": "goal",
    "card:red card": "red_card",
    "card:yellow card": "yellow_card",
    "subst": "substitution",
    "var:goal cancelled": "var_goal_cancelled",
    "var:penalty confirmed": "var_penalty_confirmed",
}


class ProviderError(RuntimeError):
    pass


class MissingApiKeyError(ProviderError):
    pass


class ApiFootballProvider:
    def __init__(self, api_key: str | None, base_url: str = BASE_URL) -> None:
        if not api_key:
            raise MissingApiKeyError("Set API_FOOTBALL_KEY before using the API-Football provider.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")

    def live_matches(self) -> list[Match]:
        payload = self._get("/fixtures", {"live": "all"})
        return [normalize_match(item) for item in payload.get("response", [])]

    def events_for_fixture(self, fixture_id: str) -> list[Event]:
        payload = self._get("/fixtures/events", {"fixture": fixture_id})
        return [normalize_event(fixture_id, item) for item in payload.get("response", [])]

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"x-apisports-key": self.api_key})
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise ProviderError(f"Provider HTTP error {exc.code}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"Provider network error: {exc.reason}") from exc


def normalize_match(raw: dict[str, Any]) -> Match:
    return Match(
        fixture_id=str(raw["fixture"]["id"]),
        home_team=str(raw["teams"]["home"]["name"]),
        away_team=str(raw["teams"]["away"]["name"]),
        league=str(raw["league"]["name"]),
        status=str(raw["fixture"]["status"].get("short", "")),
        elapsed=raw["fixture"]["status"].get("elapsed"),
        home_goals=raw.get("goals", {}).get("home"),
        away_goals=raw.get("goals", {}).get("away"),
    )


def normalize_event(fixture_id: str, raw: dict[str, Any]) -> Event:
    event_type = _event_type(raw)
    minute = raw.get("time", {}).get("elapsed")
    team = str(raw.get("team", {}).get("name") or "")
    player = str(raw.get("player", {}).get("name") or "")
    detail = str(raw.get("detail") or "")
    event_id = f"{fixture_id}-{event_type}-{minute}-{team}-{player}-{detail}"
    return Event(event_id, fixture_id, event_type, minute, team, player, detail)


def _event_type(raw: dict[str, Any]) -> str:
    raw_type = str(raw.get("type") or "").strip().casefold()
    detail = str(raw.get("detail") or "").strip().casefold()
    mapped = EVENT_TYPE_MAP.get(f"{raw_type}:{detail}") or EVENT_TYPE_MAP.get(raw_type)
    if mapped:
        return mapped
    if raw_type == "goal" and "missed" in detail:
        return "missed_penalty"
    if raw_type == "goal" and "penalty" in detail:
        return "penalty"
    return raw_type.replace(" ", "_") or "unknown"
