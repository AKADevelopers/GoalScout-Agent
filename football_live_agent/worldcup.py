from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from functools import lru_cache
from html import unescape
from typing import Any, Callable

FOX_SCORES_URL = "https://www.foxsports.com/scores"
WORLD_CUP_LEAGUE = "WORLD CUP"
NUXT_DATA_RE = re.compile(
    r'<script type="application/json" data-nuxt-data="nuxt-app" data-ssr="true" id="__NUXT_DATA__">(.*?)</script>',
    re.DOTALL,
)


@dataclass(frozen=True)
class WorldCupFixture:
    home_team: str
    away_team: str
    group: str
    kickoff_at: str
    headline: str = ""

    @property
    def summary(self) -> str:
        group = f", {self.group}" if self.group else ""
        kickoff = _format_utc_time(self.kickoff_at)
        kickoff_text = f", {kickoff}" if kickoff else ""
        return f"{self.home_team} vs {self.away_team}{group}{kickoff_text}"


def world_cup_today_summary() -> str | None:
    try:
        fixtures = fetch_fox_world_cup_fixtures()
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError):
        return None
    if not fixtures:
        return None
    return "World Cup today: " + "; ".join(fixture.summary for fixture in fixtures[:4])


def fetch_fox_world_cup_fixtures(
    url: str = FOX_SCORES_URL,
    *,
    urlopen: Callable[..., Any] = urllib.request.urlopen,
    timeout: int = 8,
) -> list[WorldCupFixture]:
    request = urllib.request.Request(url, headers={"User-Agent": "goalscout-agent/0.1"})
    with urlopen(request, timeout=timeout) as response:
        html = response.read().decode("utf-8", errors="ignore")
    return parse_fox_world_cup_fixtures(html)


def parse_fox_world_cup_fixtures(html: str) -> list[WorldCupFixture]:
    match = NUXT_DATA_RE.search(html)
    if match is None:
        return []
    data = json.loads(unescape(match.group(1)))
    root = _resolve_scores_root(data)
    if root is None:
        return []

    fixtures: list[WorldCupFixture] = []
    seen: set[str] = set()
    for event in _walk_dicts(root):
        if event.get("league") != WORLD_CUP_LEAGUE:
            continue
        fixture = _fixture_from_event(event)
        if fixture is None:
            continue
        key = f"{fixture.home_team}|{fixture.away_team}|{fixture.kickoff_at}"
        if key in seen:
            continue
        seen.add(key)
        fixtures.append(fixture)
    return sorted(fixtures, key=lambda fixture: fixture.kickoff_at)


def _resolve_scores_root(data: list[Any]) -> Any | None:
    root_index = next(
        (
            index
            for index, value in enumerate(data)
            if isinstance(value, dict) and "parsedScoreboard" in value and "parsedSegmentRes" in value
        ),
        None,
    )
    if root_index is None:
        return None

    @lru_cache(maxsize=None)
    def resolve_ref(index: int) -> Any:
        value = data[index]
        if isinstance(value, dict):
            return {
                key: resolve_ref(item) if isinstance(item, int) and 0 <= item < len(data) else resolve_entry(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [resolve_ref(item) if isinstance(item, int) and 0 <= item < len(data) else resolve_entry(item) for item in value]
        return value

    def resolve_entry(value: Any) -> Any:
        if isinstance(value, dict):
            return {
                key: resolve_ref(item) if isinstance(item, int) and 0 <= item < len(data) else resolve_entry(item)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [resolve_ref(item) if isinstance(item, int) and 0 <= item < len(data) else resolve_entry(item) for item in value]
        return value

    return resolve_ref(root_index)


def _fixture_from_event(event: Mapping[str, Any]) -> WorldCupFixture | None:
    upper = event.get("upperTeam")
    lower = event.get("lowerTeam")
    if not isinstance(upper, Mapping) or not isinstance(lower, Mapping):
        return None
    home_team = str(upper.get("longName") or "").strip()
    away_team = str(lower.get("longName") or "").strip()
    kickoff_at = str(event.get("eventTime") or "").strip()
    if not home_team or not away_team or not kickoff_at:
        return None
    return WorldCupFixture(
        home_team=home_team,
        away_team=away_team,
        group=str(event.get("gameNotes") or "").strip(),
        kickoff_at=kickoff_at,
        headline=str(event.get("eventHeadline") or "").strip(),
    )


def _walk_dicts(value: Any) -> list[Mapping[str, Any]]:
    found: list[Mapping[str, Any]] = []
    if isinstance(value, Mapping):
        found.append(value)
        for child in value.values():
            found.extend(_walk_dicts(child))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for child in value:
            found.extend(_walk_dicts(child))
    return found


def _format_utc_time(value: str) -> str:
    text = value.strip()
    if not text:
        return ""
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        kickoff = datetime.fromisoformat(text)
    except ValueError:
        return value
    return kickoff.strftime("%H:%M UTC")
