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
    kickoff_at: str | None = None

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
    delivery: str = "console"
    channel: str | None = None
    target: str | None = None
    channel_command: str | None = None
    watch_country: str = ""
    watch_platforms: list[str] = field(default_factory=list)
    watch_provider: str = "guide"

    def should_notify(self, match: Match, event: Event) -> bool:
        if "all" not in self._alert_types and _norm(event.event_type) not in self._alert_types:
            return False

        followed_teams = {_norm(team) for team in self.favorite_teams if team.strip()}
        followed_players = {_norm(player) for player in self.favorite_players if player.strip()}
        competitions = {_norm(name) for name in self.competitions if name.strip()}
        country = _norm(self.favorite_country)

        team_hit = (
            _norm(event.team) in followed_teams
            or _norm(match.home_team) in followed_teams
            or _norm(match.away_team) in followed_teams
        )
        country_hit = bool(country) and (
            country == _norm(match.home_team)
            or country == _norm(match.away_team)
            or country == _norm(event.team)
        )
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
    def from_dict(cls, data: dict[str, Any]) -> Preferences:
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
            delivery=str(data.get("delivery", "console")),
            channel=data.get("channel"),
            target=data.get("target"),
            channel_command=data.get("channel_command"),
            watch_country=str(data.get("watch_country", "")),
            watch_platforms=list(data.get("watch_platforms", [])),
            watch_provider=str(data.get("watch_provider", "guide")),
        )
