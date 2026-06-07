# Football Live Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable football skill and a Python live watcher that can notify a user about goals and other followed match events.

**Architecture:** A portable Agent Skills folder explains the football workflow to OpenClaw, Hermes, and compatible agents. A small Python package handles onboarding, provider polling, event normalization, duplicate suppression, and console/webhook notifications.

**Tech Stack:** Python 3.11+, standard library HTTP/JSON modules, pytest, Agent Skills `SKILL.md`, local JSON persistence.

---

## File Map

- Create: `E:\Football agent or skill\pyproject.toml` for package metadata and pytest settings.
- Create: `E:\Football agent or skill\football_live_agent\__init__.py` for package version.
- Create: `E:\Football agent or skill\football_live_agent\models.py` for normalized preference, match, event, and notification data classes.
- Create: `E:\Football agent or skill\football_live_agent\config.py` for environment and data-path loading.
- Create: `E:\Football agent or skill\football_live_agent\state.py` for JSON state persistence and event deduplication.
- Create: `E:\Football agent or skill\football_live_agent\onboarding.py` for first-run questions and preference saving.
- Create: `E:\Football agent or skill\football_live_agent\providers\base.py` for provider interface.
- Create: `E:\Football agent or skill\football_live_agent\providers\api_football.py` for API-Football integration.
- Create: `E:\Football agent or skill\football_live_agent\notifiers\base.py` for notifier interface.
- Create: `E:\Football agent or skill\football_live_agent\notifiers\console.py` for local notification output.
- Create: `E:\Football agent or skill\football_live_agent\notifiers\webhook.py` for webhook notifications.
- Create: `E:\Football agent or skill\football_live_agent\watcher.py` for one-shot and continuous watch loops.
- Create: `E:\Football agent or skill\football_live_agent\cli.py` for `onboard`, `once`, `watch`, `preferences`, and `test-notification`.
- Create: `E:\Football agent or skill\tests\test_models.py` for preference matching and formatting tests.
- Create: `E:\Football agent or skill\tests\test_state.py` for deduplication tests.
- Create: `E:\Football agent or skill\tests\test_watcher.py` for mocked provider and notifier flow tests.
- Create: `E:\Football agent or skill\tests\test_api_football.py` for API-Football normalization tests.
- Create: `E:\Football agent or skill\skills\football-live-agent\SKILL.md` for portable agent instructions.
- Create: `E:\Football agent or skill\skills\football-live-agent\agents\openai.yaml` for skill UI metadata.
- Create: `E:\Football agent or skill\skills\football-live-agent\references\provider-notes.md` for provider setup and latency notes.

## Task 1: Package Scaffold

**Files:**
- Create: `E:\Football agent or skill\pyproject.toml`
- Create: `E:\Football agent or skill\football_live_agent\__init__.py`
- Create folders: `E:\Football agent or skill\football_live_agent\providers`, `E:\Football agent or skill\football_live_agent\notifiers`, `E:\Football agent or skill\tests`

- [ ] **Step 1: Create package metadata**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "football-live-agent"
version = "0.1.0"
description = "Portable football live notification watcher for agent skills."
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0"]

[project.scripts]
football-live-agent = "football_live_agent.cli:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
```

- [ ] **Step 2: Add package version**

```python
__version__ = "0.1.0"
```

- [ ] **Step 3: Run import check**

Run: `python -c "import football_live_agent; print(football_live_agent.__version__)"`

Expected: `0.1.0`

## Task 2: Models And Preferences

**Files:**
- Create: `E:\Football agent or skill\football_live_agent\models.py`
- Create: `E:\Football agent or skill\tests\test_models.py`

- [ ] **Step 1: Write model tests**

```python
from football_live_agent.models import Event, Match, Preferences


def test_preferences_match_favorite_team_and_goal_type():
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina", "Inter Miami"],
        favorite_players=["Messi"],
        competitions=["World Cup"],
        alert_types=["goal", "red_card"],
        timezone="Asia/Karachi",
    )
    match = Match(
        fixture_id="10",
        home_team="Argentina",
        away_team="Brazil",
        league="World Cup",
        status="LIVE",
        elapsed=55,
        home_goals=2,
        away_goals=1,
    )
    event = Event(
        event_id="10-goal-55-Messi",
        fixture_id="10",
        event_type="goal",
        minute=55,
        team="Argentina",
        player="Messi",
        detail="Normal Goal",
    )

    assert preferences.should_notify(match, event) is True


def test_preferences_reject_unfollowed_team():
    preferences = Preferences(
        favorite_country="Pakistan",
        favorite_teams=["Pakistan"],
        favorite_players=[],
        competitions=[],
        alert_types=["goal"],
        timezone="Asia/Karachi",
    )
    match = Match(
        fixture_id="11",
        home_team="France",
        away_team="Germany",
        league="Friendly",
        status="LIVE",
        elapsed=20,
        home_goals=0,
        away_goals=1,
    )
    event = Event(
        event_id="11-goal-20",
        fixture_id="11",
        event_type="goal",
        minute=20,
        team="Germany",
        player="",
        detail="Normal Goal",
    )

    assert preferences.should_notify(match, event) is False
```

- [ ] **Step 2: Run tests to verify failure**

Run: `pytest tests/test_models.py -q`

Expected: tests fail because `football_live_agent.models` does not exist.

- [ ] **Step 3: Implement models**

```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


def _norm(value: str | None) -> str:
    return (value or "").strip().casefold()


@dataclass(frozen=True)
class Match:
    fixture_id: str
    home_team: str
    away_team: str
    league: str
    status: str
    elapsed: int | None
    home_goals: int | None
    away_goals: int | None

    @property
    def scoreline(self) -> str:
        home = "-" if self.home_goals is None else str(self.home_goals)
        away = "-" if self.away_goals is None else str(self.away_goals)
        return f"{self.home_team} {home}-{away} {self.away_team}"


@dataclass(frozen=True)
class Event:
    event_id: str
    fixture_id: str
    event_type: str
    minute: int | None
    team: str
    player: str
    detail: str = ""

    @property
    def display_minute(self) -> str:
        return "?" if self.minute is None else f"{self.minute}'"


@dataclass
class Preferences:
    favorite_country: str
    favorite_teams: list[str] = field(default_factory=list)
    favorite_players: list[str] = field(default_factory=list)
    competitions: list[str] = field(default_factory=list)
    alert_types: list[str] = field(default_factory=lambda: ["goal", "red_card", "kickoff", "fulltime"])
    timezone: str = "UTC"
    quiet_hours_start: str | None = None
    quiet_hours_end: str | None = None
    webhook_url: str | None = None

    def should_notify(self, match: Match, event: Event) -> bool:
        if "all" not in self._alert_types and _norm(event.event_type) not in self._alert_types:
            return False

        followed_teams = {_norm(team) for team in self.favorite_teams if team.strip()}
        followed_players = {_norm(player) for player in self.favorite_players if player.strip()}
        competitions = {_norm(name) for name in self.competitions if name.strip()}
        country = _norm(self.favorite_country)

        team_hit = _norm(event.team) in followed_teams or _norm(match.home_team) in followed_teams or _norm(match.away_team) in followed_teams
        country_hit = bool(country) and (country == _norm(match.home_team) or country == _norm(match.away_team) or country == _norm(event.team))
        player_hit = bool(_norm(event.player)) and _norm(event.player) in followed_players
        competition_hit = bool(competitions) and _norm(match.league) in competitions

        if not followed_teams and not followed_players and not competitions and not country:
            return True

        return team_hit or country_hit or player_hit or competition_hit

    @property
    def _alert_types(self) -> set[str]:
        return {_norm(alert) for alert in self.alert_types}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Preferences":
        return cls(
            favorite_country=str(data.get("favorite_country", "")),
            favorite_teams=list(data.get("favorite_teams", [])),
            favorite_players=list(data.get("favorite_players", [])),
            competitions=list(data.get("competitions", [])),
            alert_types=list(data.get("alert_types", ["goal", "red_card", "kickoff", "fulltime"])),
            timezone=str(data.get("timezone", "UTC")),
            quiet_hours_start=data.get("quiet_hours_start"),
            quiet_hours_end=data.get("quiet_hours_end"),
            webhook_url=data.get("webhook_url"),
        )
```

- [ ] **Step 4: Run model tests**

Run: `pytest tests/test_models.py -q`

Expected: both tests pass.

## Task 3: Config, State, And Onboarding

**Files:**
- Create: `E:\Football agent or skill\football_live_agent\config.py`
- Create: `E:\Football agent or skill\football_live_agent\state.py`
- Create: `E:\Football agent or skill\football_live_agent\onboarding.py`
- Create: `E:\Football agent or skill\tests\test_state.py`

- [ ] **Step 1: Write state tests**

```python
from football_live_agent.models import Event
from football_live_agent.state import JsonState


def test_seen_event_is_persisted(tmp_path):
    state = JsonState(tmp_path / "state.json")
    event = Event("fixture-goal-1", "fixture", "goal", 10, "Argentina", "Messi")

    assert state.mark_seen(event) is True
    assert state.mark_seen(event) is False

    reloaded = JsonState(tmp_path / "state.json")
    assert reloaded.mark_seen(event) is False
```

- [ ] **Step 2: Run state tests to verify failure**

Run: `pytest tests/test_state.py -q`

Expected: test fails because `football_live_agent.state` does not exist.

- [ ] **Step 3: Implement config and state**

`config.py`

```python
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    provider: str
    poll_seconds: int
    data_dir: Path
    api_football_key: str | None
    webhook_url: str | None


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("FOOTBALL_AGENT_DATA_DIR", ".football-live-agent"))
    poll_raw = os.environ.get("FOOTBALL_AGENT_POLL_SECONDS", "60")
    try:
        poll_seconds = max(10, int(poll_raw))
    except ValueError:
        poll_seconds = 20

    return Settings(
        provider=os.environ.get("FOOTBALL_AGENT_PROVIDER", "sportscore"),
        poll_seconds=poll_seconds,
        data_dir=data_dir,
        api_football_key=os.environ.get("API_FOOTBALL_KEY"),
        webhook_url=os.environ.get("FOOTBALL_AGENT_WEBHOOK_URL"),
    )
```

`state.py`

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from football_live_agent.models import Event


class JsonState:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._data = self._load()

    def mark_seen(self, event: Event) -> bool:
        seen = set(self._data.setdefault("seen_event_ids", []))
        if event.event_id in seen:
            return False
        seen.add(event.event_id)
        self._data["seen_event_ids"] = sorted(seen)
        self._save()
        return True

    def _load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"seen_event_ids": []}
        with self.path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2, sort_keys=True)
            handle.write("\n")
```

- [ ] **Step 4: Implement onboarding**

```python
from __future__ import annotations

import json
from pathlib import Path

from football_live_agent.models import Preferences


DEFAULT_ALERTS = ["goal", "red_card", "kickoff", "fulltime"]


def ask_csv(prompt: str) -> list[str]:
    value = input(prompt).strip()
    return [item.strip() for item in value.split(",") if item.strip()]


def run_onboarding(path: Path) -> Preferences:
    print("Football live agent setup")
    favorite_country = input("Favorite country: ").strip()
    favorite_teams = ask_csv("Favorite teams or clubs, comma-separated: ")
    favorite_players = ask_csv("Favorite players, comma-separated: ")
    competitions = ask_csv("Competitions to follow, comma-separated: ")
    alerts = ask_csv("Alert types, comma-separated. Leave blank for goals, red cards, kickoff, fulltime: ")
    timezone = input("Timezone, for example Asia/Karachi: ").strip() or "UTC"
    webhook_url = input("Webhook URL, optional: ").strip() or None

    preferences = Preferences(
        favorite_country=favorite_country,
        favorite_teams=favorite_teams,
        favorite_players=favorite_players,
        competitions=competitions,
        alert_types=alerts or DEFAULT_ALERTS,
        timezone=timezone,
        webhook_url=webhook_url,
    )
    save_preferences(path, preferences)
    return preferences


def load_preferences(path: Path) -> Preferences:
    with path.open("r", encoding="utf-8") as handle:
        return Preferences.from_dict(json.load(handle))


def save_preferences(path: Path, preferences: Preferences) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(preferences.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
```

- [ ] **Step 5: Run state tests**

Run: `pytest tests/test_state.py -q`

Expected: test passes.

## Task 4: Provider And API-Football Normalizer

**Files:**
- Create: `E:\Football agent or skill\football_live_agent\providers\__init__.py`
- Create: `E:\Football agent or skill\football_live_agent\providers\base.py`
- Create: `E:\Football agent or skill\football_live_agent\providers\api_football.py`
- Create: `E:\Football agent or skill\tests\test_api_football.py`

- [ ] **Step 1: Write API-Football normalization tests**

```python
from football_live_agent.providers.api_football import normalize_event, normalize_match


def test_normalize_match_from_api_football_fixture():
    raw = {
        "fixture": {"id": 123, "status": {"short": "1H", "elapsed": 44}},
        "teams": {"home": {"name": "Argentina"}, "away": {"name": "Brazil"}},
        "league": {"name": "World Cup"},
        "goals": {"home": 1, "away": 0},
    }

    match = normalize_match(raw)

    assert match.fixture_id == "123"
    assert match.scoreline == "Argentina 1-0 Brazil"


def test_normalize_goal_event_from_api_football_event():
    raw = {
        "time": {"elapsed": 44},
        "team": {"name": "Argentina"},
        "player": {"name": "Messi"},
        "type": "Goal",
        "detail": "Normal Goal",
    }

    event = normalize_event("123", raw)

    assert event.event_type == "goal"
    assert event.event_id == "123-goal-44-Argentina-Messi-Normal Goal"
```

- [ ] **Step 2: Run provider tests to verify failure**

Run: `pytest tests/test_api_football.py -q`

Expected: tests fail because provider modules do not exist.

- [ ] **Step 3: Implement provider interface**

```python
from __future__ import annotations

from typing import Protocol

from football_live_agent.models import Event, Match


class FootballProvider(Protocol):
    def live_matches(self) -> list[Match]:
        ...

    def events_for_fixture(self, fixture_id: str) -> list[Event]:
        ...
```

- [ ] **Step 4: Implement API-Football adapter**

```python
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
    if raw_type == "goal" and "penalty" in detail:
        return "penalty"
    if raw_type == "goal" and "missed" in detail:
        return "missed_penalty"
    return raw_type.replace(" ", "_") or "unknown"
```

- [ ] **Step 5: Run provider tests**

Run: `pytest tests/test_api_football.py -q`

Expected: tests pass.

## Task 5: Notifiers And Watcher

**Files:**
- Create: `E:\Football agent or skill\football_live_agent\notifiers\__init__.py`
- Create: `E:\Football agent or skill\football_live_agent\notifiers\base.py`
- Create: `E:\Football agent or skill\football_live_agent\notifiers\console.py`
- Create: `E:\Football agent or skill\football_live_agent\notifiers\webhook.py`
- Create: `E:\Football agent or skill\football_live_agent\watcher.py`
- Create: `E:\Football agent or skill\tests\test_watcher.py`

- [ ] **Step 1: Write watcher tests**

```python
from football_live_agent.models import Event, Match, Preferences
from football_live_agent.state import JsonState
from football_live_agent.watcher import run_once


class FakeProvider:
    def live_matches(self):
        return [
            Match("1", "Argentina", "Brazil", "World Cup", "LIVE", 44, 1, 0),
        ]

    def events_for_fixture(self, fixture_id):
        return [
            Event("1-goal-44-Argentina-Messi", "1", "goal", 44, "Argentina", "Messi", "Normal Goal"),
        ]


class CollectingNotifier:
    def __init__(self):
        self.messages = []

    def send(self, match, event):
        self.messages.append((match, event))


def test_run_once_sends_new_goal_once(tmp_path):
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=["Messi"],
        competitions=["World Cup"],
        alert_types=["goal"],
        timezone="Asia/Karachi",
    )
    notifier = CollectingNotifier()
    state = JsonState(tmp_path / "state.json")

    assert run_once(FakeProvider(), preferences, state, [notifier]) == 1
    assert run_once(FakeProvider(), preferences, state, [notifier]) == 0
    assert len(notifier.messages) == 1
```

- [ ] **Step 2: Run watcher tests to verify failure**

Run: `pytest tests/test_watcher.py -q`

Expected: test fails because watcher and notifier modules do not exist.

- [ ] **Step 3: Implement notifier interface and console notifier**

`base.py`

```python
from __future__ import annotations

from typing import Protocol

from football_live_agent.models import Event, Match


class Notifier(Protocol):
    def send(self, match: Match, event: Event) -> None:
        ...
```

`console.py`

```python
from __future__ import annotations

from football_live_agent.models import Event, Match


class ConsoleNotifier:
    def send(self, match: Match, event: Event) -> None:
        print(format_notification(match, event))


def format_notification(match: Match, event: Event) -> str:
    player = f" - {event.player}" if event.player else ""
    return f"[{event.display_minute}] {event.event_type.upper()} {match.scoreline} ({event.team}{player})"
```

- [ ] **Step 4: Implement webhook notifier**

```python
from __future__ import annotations

import json
import urllib.error
import urllib.request

from football_live_agent.models import Event, Match


class WebhookNotifier:
    def __init__(self, url: str) -> None:
        self.url = url

    def send(self, match: Match, event: Event) -> None:
        payload = {
            "event_type": event.event_type,
            "minute": event.minute,
            "team": event.team,
            "player": event.player,
            "detail": event.detail,
            "fixture_id": event.fixture_id,
            "match": {
                "home_team": match.home_team,
                "away_team": match.away_team,
                "scoreline": match.scoreline,
                "league": match.league,
                "status": match.status,
            },
            "text": f"{event.event_type.upper()} {match.scoreline}",
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10):
                return
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Webhook notification failed: {exc}") from exc
```

- [ ] **Step 5: Implement watcher**

```python
from __future__ import annotations

import time
from collections.abc import Sequence

from football_live_agent.models import Preferences
from football_live_agent.notifiers.base import Notifier
from football_live_agent.providers.base import FootballProvider
from football_live_agent.state import JsonState


def run_once(provider: FootballProvider, preferences: Preferences, state: JsonState, notifiers: Sequence[Notifier]) -> int:
    sent = 0
    for match in provider.live_matches():
        for event in provider.events_for_fixture(match.fixture_id):
            if not preferences.should_notify(match, event):
                continue
            if not state.mark_seen(event):
                continue
            for notifier in notifiers:
                notifier.send(match, event)
            sent += 1
    return sent


def watch_forever(provider: FootballProvider, preferences: Preferences, state: JsonState, notifiers: Sequence[Notifier], poll_seconds: int) -> None:
    while True:
        try:
            run_once(provider, preferences, state, notifiers)
        except Exception as exc:
            print(f"Watcher cycle failed: {exc}")
        time.sleep(poll_seconds)
```

- [ ] **Step 6: Run watcher tests**

Run: `pytest tests/test_watcher.py -q`

Expected: test passes.

## Task 6: CLI

**Files:**
- Create: `E:\Football agent or skill\football_live_agent\cli.py`

- [ ] **Step 1: Implement CLI**

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from football_live_agent.config import load_settings
from football_live_agent.models import Event, Match
from football_live_agent.notifiers.console import ConsoleNotifier
from football_live_agent.notifiers.webhook import WebhookNotifier
from football_live_agent.onboarding import load_preferences, run_onboarding
from football_live_agent.providers.api_football import ApiFootballProvider
from football_live_agent.providers.sportscore import SportScoreProvider
from football_live_agent.state import JsonState
from football_live_agent.watcher import run_once, watch_forever


def build_provider(settings):
    if settings.provider == "sportscore":
        return SportScoreProvider()
    if settings.provider != "api-football":
        raise SystemExit(f"Unsupported provider: {settings.provider}")
    return ApiFootballProvider(settings.api_football_key)


def build_notifiers(settings, preferences):
    notifiers = [ConsoleNotifier()]
    webhook_url = settings.webhook_url or preferences.webhook_url
    if webhook_url:
        notifiers.append(WebhookNotifier(webhook_url))
    return notifiers


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Football live notification agent")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("onboard")
    sub.add_parser("preferences")
    sub.add_parser("once")
    sub.add_parser("watch")
    sub.add_parser("test-notification")
    args = parser.parse_args(argv)

    settings = load_settings()
    pref_path = settings.data_dir / "preferences.json"
    state = JsonState(settings.data_dir / "state.json")

    if args.command == "onboard":
        run_onboarding(pref_path)
        print(f"Saved preferences to {pref_path}")
        return 0

    if not pref_path.exists():
        raise SystemExit("No preferences found. Run: football-live-agent onboard")

    preferences = load_preferences(pref_path)

    if args.command == "preferences":
        print(json.dumps(preferences.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "test-notification":
        match = Match("test", "Your Team", "Opponent", "Test Match", "LIVE", 1, 1, 0)
        event = Event("test-event", "test", "goal", 1, "Your Team", "Favorite Player", "Test")
        for notifier in build_notifiers(settings, preferences):
            notifier.send(match, event)
        return 0

    provider = build_provider(settings)
    notifiers = build_notifiers(settings, preferences)

    if args.command == "once":
        sent = run_once(provider, preferences, state, notifiers)
        print(f"Sent {sent} notification(s).")
        return 0

    if args.command == "watch":
        watch_forever(provider, preferences, state, notifiers, settings.poll_seconds)
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Run CLI help**

Run: `python -m football_live_agent.cli --help`

Expected: help text lists `onboard`, `preferences`, `once`, `watch`, and `test-notification`.

## Task 7: Portable Skill Package

**Files:**
- Create: `E:\Football agent or skill\skills\football-live-agent\SKILL.md`
- Create: `E:\Football agent or skill\skills\football-live-agent\agents\openai.yaml`
- Create: `E:\Football agent or skill\skills\football-live-agent\references\provider-notes.md`

- [ ] **Step 1: Initialize skill folder**

Run: `python "C:\Users\Abid khan afridi\.codex\skills\.system\skill-creator\scripts\init_skill.py" football-live-agent --path "E:\Football agent or skill\skills" --resources references --interface display_name="Football Live Agent" --interface short_description="Live football alerts and match context" --interface default_prompt="Use $football-live-agent to set up my football favorites and live match alerts."`

Expected: skill folder is created with `SKILL.md`, `agents/openai.yaml`, and `references`.

- [ ] **Step 2: Replace skill instructions**

```markdown
---
name: football-live-agent
description: Use when the user wants football or soccer match information, favorite-team setup, live score monitoring, goal alerts, match reminders, player/team tracking, World Cup or league updates, or help configuring OpenClaw/Hermes football notifications through the football-live-agent watcher.
---

# Football Live Agent

Use this skill to help users configure and operate a football live notification agent.

## Workflow

1. Check whether local preferences exist in `.football-live-agent/preferences.json`.
2. If preferences are missing, run onboarding with `python -m football_live_agent.cli onboard`.
3. Ask for or confirm the user's favorite country, favorite teams, favorite players, competitions, alert types, timezone, and notification channel.
4. For live alerts, make sure `API_FOOTBALL_KEY` is set and run `python -m football_live_agent.cli watch`.
5. For a single check, run `python -m football_live_agent.cli once`.
6. For webhook delivery to Hermes, OpenClaw, Discord, Telegram, or an automation bridge, set `FOOTBALL_AGENT_WEBHOOK_URL`.

## User Preferences

Collect these fields during setup:

- Favorite country.
- Favorite club or national teams.
- Favorite players.
- Competitions to follow.
- Alert types: `goal`, `penalty`, `missed_penalty`, `red_card`, `yellow_card`, `kickoff`, `halftime`, `fulltime`, `substitution`, `var_goal_cancelled`, `var_penalty_confirmed`, or `all`.
- Timezone.
- Optional quiet hours.
- Optional webhook URL.

## Answering Football Requests

For schedule, score, lineup, and event questions, use the watcher when local provider configuration exists. If no provider key exists, explain that live data requires a sports data API key and help the user complete setup.

Prefer concise updates:

`55' GOAL Argentina 2-1 Brazil - Messi`

Include the source provider and observed update time when precision matters.

## Safety

Do not store API keys in prompt text or skill files. Use environment variables.

Do not provide betting instructions, odds advice, illegal streams, or paywall bypass steps.

## Provider Notes

Read `references/provider-notes.md` when configuring live data providers or explaining latency tradeoffs.
```

- [ ] **Step 3: Add provider notes**

```markdown
# Provider Notes

## API-Football

Default provider is SportScore. It requires no API key and uses live/in-play football matches plus match detail incidents. API-Football is optional: configure `API_FOOTBALL_KEY` and set `FOOTBALL_AGENT_PROVIDER=api-football` when using that provider.

Expected latency is near-real-time, commonly around one polling interval plus provider update delay. Start with `FOOTBALL_AGENT_POLL_SECONDS=20`.

## Sportmonks

Sportmonks can be added through the provider interface in `football_live_agent.providers.base.FootballProvider`. Use it when the user already has Sportmonks credentials or coverage requirements.

## AnySport

AnySport can be added later for WebSocket push events. Prefer it when the user needs lower latency than polling and has access to its football event feed.

## OpenClaw And Hermes

OpenClaw can use the skill folder directly as a local skill. Hermes can use the same skill instructions and route webhook notifications through its messaging or gateway setup.
```

- [ ] **Step 4: Validate skill**

Run: `python "C:\Users\Abid khan afridi\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "E:\Football agent or skill\skills\football-live-agent"`

Expected: validation passes.

## Task 8: Full Verification

**Files:**
- Verify all created files.

- [ ] **Step 1: Run all unit tests**

Run: `pytest -q`

Expected: all tests pass.

- [ ] **Step 2: Run CLI help**

Run: `python -m football_live_agent.cli --help`

Expected: command help exits with status 0.

- [ ] **Step 3: Run skill validation**

Run: `python "C:\Users\Abid khan afridi\.codex\skills\.system\skill-creator\scripts\quick_validate.py" "E:\Football agent or skill\skills\football-live-agent"`

Expected: validation passes.
