from __future__ import annotations

import json
import os
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from football_live_agent.models import Event, Match
from football_live_agent.providers.api_football import ProviderError

BASE_URL = "https://sportscore.com/api/widget"
SOURCE_ID = "goalscout-agent"
LIVE_MATCH_STATUSES = {"live", "inplay", "in_play", "1h", "2h", "ht", "halftime", "extra_time", "penalties"}
FRIENDLY_KEYWORDS = ("friendly", "warmup", "warm-up")


class SportScoreProvider:
    def __init__(
        self,
        base_url: str = BASE_URL,
        limit: int = 50,
        powershell_runner: Callable[..., Any] = subprocess.run,
        cache_dir: Path | None = None,
        retries: int = 1,
        request_timeout: int = 12,
        fallback_timeout: int = 15,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.limit = limit
        self.powershell_runner = powershell_runner
        self.cache_dir = cache_dir
        self.retries = max(1, retries)
        self.request_timeout = max(1, request_timeout)
        self.fallback_timeout = max(1, fallback_timeout)
        self._last_matches_payload: dict[str, Any] | None = None

    def live_matches(self) -> list[Match]:
        payload = self._get_matches()
        self._last_matches_payload = payload
        matches = [normalize_match(item) for item in payload.get("matches", [])]
        return [match for match in matches if _is_watchable_status(match.status)]

    def all_matches(self) -> list[Match]:
        payload = self._last_matches_payload or self._get_matches()
        self._last_matches_payload = payload
        return [normalize_match(item) for item in payload.get("matches", [])]

    def football_update(self) -> str:
        payload = self._last_matches_payload or self._get_matches()
        self._last_matches_payload = None
        matches = [normalize_match(item) for item in payload.get("matches", [])]
        live = [match for match in matches if _is_watchable_status(match.status)]
        recent = sorted(
            [match for match in matches if _is_finished_status(match.status)],
            key=_kickoff_timestamp,
            reverse=True,
        )
        upcoming = sorted(
            [match for match in matches if _is_upcoming_status(match.status)],
            key=_upcoming_sort_key,
        )

        parts = []
        if live:
            parts.append(f"Football is live now: {live[0].scoreline} in {live[0].league}. I will notify you about goals and key events.")
        else:
            parts.append("No live football match is currently returned by the football feed.")
        recent_friendlies = [match for match in recent if _is_friendly_or_warmup(match)]
        upcoming_friendlies = [match for match in upcoming if _is_friendly_or_warmup(match)]
        if recent_friendlies:
            parts.append(f"Recent friendly/warmup result: {_format_result(recent_friendlies[0])}.")
        elif recent:
            parts.append(f"Latest result: {_format_result(recent[0])}.")
        if upcoming_friendlies:
            parts.append(f"Upcoming friendlies/warmups: {_format_fixtures(upcoming_friendlies, limit=3)}.")
        elif upcoming:
            parts.append(f"Next fixture: {_format_fixture(upcoming[0])}.")
        if len(parts) == 1:
            parts.append("No recent result or upcoming fixture was returned by SportScore right now.")
        return " ".join(parts)

    def events_for_fixture(self, fixture_id: str) -> list[Event]:
        payload = self._get("/match/", {"sport": "football", "slug": fixture_id, "src": SOURCE_ID})
        match = normalize_match(payload["match"])
        return [normalize_incident(match, item) for item in payload["match"].get("incidents", [])]

    def _get_matches(self) -> dict[str, Any]:
        return self._get("/matches/", {"sport": "football", "limit": str(self.limit), "src": SOURCE_ID})

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": "goalscout-agent/0.1"})
        last_error: urllib.error.URLError | None = None
        for attempt in range(self.retries):
            try:
                with urllib.request.urlopen(request, timeout=self.request_timeout) as response:
                    payload = json.loads(response.read().decode("utf-8"))
                    self._write_cache(path, params, payload)
                    return payload
            except urllib.error.HTTPError as exc:
                raise ProviderError(f"SportScore HTTP error {exc.code}") from exc
            except urllib.error.URLError as exc:
                last_error = exc
                if attempt < self.retries - 1:
                    time.sleep(1)

        if last_error is None:
            raise ProviderError("SportScore network error: unknown error")

        try:
            if os.name == "nt":
                payload = self._get_with_powershell(url, last_error)
                self._write_cache(path, params, payload)
                return payload
            raise ProviderError(f"SportScore network error: {last_error.reason}") from last_error
        except ProviderError:
            cached = self._read_cache(path, params)
            if cached is not None:
                return cached
            raise

    def _get_with_powershell(self, url: str, original_error: urllib.error.URLError) -> dict[str, Any]:
        script = (
            "$ProgressPreference='SilentlyContinue'; "
            f"Invoke-RestMethod -Uri {json.dumps(url)} -TimeoutSec {self.fallback_timeout} | "
            "ConvertTo-Json -Depth 50"
        )
        result = self.powershell_runner(
            ["powershell", "-NoProfile", "-Command", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=self.fallback_timeout + 5,
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            raise ProviderError(f"SportScore network error: {original_error.reason}; PowerShell fallback failed: {stderr}") from original_error
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ProviderError("SportScore PowerShell fallback returned invalid JSON") from exc

    def _cache_path(self, path: str, params: dict[str, str]) -> Path:
        if self.cache_dir is None:
            raise ValueError("cache_dir is not configured")
        key = f"{path}?{urllib.parse.urlencode(sorted(params.items()))}"
        safe = "".join(char if char.isalnum() else "_" for char in key).strip("_")
        return self.cache_dir / "provider-cache" / f"{safe}.json"

    def _write_cache(self, path: str, params: dict[str, str], payload: dict[str, Any]) -> None:
        if self.cache_dir is None:
            return
        cache_path = self._cache_path(path, params)
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with cache_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def _read_cache(self, path: str, params: dict[str, str]) -> dict[str, Any] | None:
        if self.cache_dir is None:
            return None
        cache_path = self._cache_path(path, params)
        if not cache_path.exists():
            return None
        with cache_path.open("r", encoding="utf-8-sig") as handle:
            return json.load(handle)


def normalize_match(raw: dict[str, Any]) -> Match:
    return Match(
        fixture_id=_slug_from_url(str(raw.get("url") or "")),
        home_team=str(raw.get("home") or ""),
        away_team=str(raw.get("away") or ""),
        league=str(raw.get("competition") or ""),
        status=str(raw.get("status") or raw.get("status_text") or ""),
        elapsed=_as_int(raw.get("live_minute")),
        home_goals=_as_int(raw.get("home_score")),
        away_goals=_as_int(raw.get("away_score")),
        kickoff_at=_optional_str(raw.get("time") or raw.get("start_time") or raw.get("kickoff_at")),
    )


def normalize_incident(match: Match, raw: dict[str, Any]) -> Event:
    event_type = _event_type(raw)
    team = _team_from_side(match, str(raw.get("side") or ""))
    player = _player(raw)
    detail = _detail(raw)
    minute = _as_int(raw.get("time"))
    home_score = raw.get("home_score", match.home_goals)
    away_score = raw.get("away_score", match.away_goals)
    event_id = f"{match.fixture_id}-{event_type}-{minute}-{team}-{player}-{home_score}-{away_score}"
    return Event(event_id, match.fixture_id, event_type, minute, team, player, detail)


def _slug_from_url(url: str) -> str:
    parts = [part for part in url.strip("/").split("/") if part]
    if parts:
        return parts[-1]
    return url.strip("/")


def _event_type(raw: dict[str, Any]) -> str:
    raw_type = str(raw.get("type") or "").strip().casefold()
    if raw.get("is_goal") or raw_type == "goal":
        return "goal"
    if raw.get("is_sub") or raw_type == "substitution":
        return "substitution"
    if raw.get("is_card") or "card" in raw_type:
        if "red" in raw_type:
            return "red_card"
        return "yellow_card"
    return raw_type.replace(" ", "_") or "unknown"


def _team_from_side(match: Match, side: str) -> str:
    side = side.casefold()
    if side == "home":
        return match.home_team
    if side == "away":
        return match.away_team
    return ""


def _player(raw: dict[str, Any]) -> str:
    player = str(raw.get("player") or "").strip()
    if player:
        return player
    return str(raw.get("player_in") or "").strip()


def _detail(raw: dict[str, Any]) -> str:
    player_in = str(raw.get("player_in") or "").strip()
    player_out = str(raw.get("player_out") or "").strip()
    if player_in and player_out:
        return f"{player_in} for {player_out}"
    return str(raw.get("type") or "").strip()


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _is_watchable_status(status: str) -> bool:
    normalized = status.strip().casefold()
    return normalized in LIVE_MATCH_STATUSES


def _is_finished_status(status: str) -> bool:
    return status.strip().casefold() == "finished"


def _is_upcoming_status(status: str) -> bool:
    normalized = status.strip().casefold()
    return normalized in {"upcoming", "not_started", "not started", "delayed"}


def _is_friendly_or_warmup(match: Match) -> bool:
    league = match.league.strip().casefold()
    return any(keyword in league for keyword in FRIENDLY_KEYWORDS)


def _format_result(match: Match) -> str:
    return f"{match.scoreline} in {match.league}"


def _format_fixture(match: Match) -> str:
    return f"{match.home_team} vs {match.away_team} in {match.league}"


def _format_fixtures(matches: list[Match], limit: int) -> str:
    return "; ".join(_format_fixture(match) for match in matches[:limit])


def _kickoff_timestamp(match: Match) -> float:
    if not match.kickoff_at:
        return 0.0
    text = match.kickoff_at.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        kickoff = datetime.fromisoformat(text)
    except ValueError:
        return 0.0
    if kickoff.tzinfo is None:
        kickoff = kickoff.replace(tzinfo=UTC)
    return kickoff.timestamp()


def _upcoming_sort_key(match: Match) -> tuple[int, float]:
    timestamp = _kickoff_timestamp(match)
    if timestamp <= 0:
        return (1, 0.0)
    return (0, timestamp)
