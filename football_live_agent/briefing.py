from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from football_live_agent.models import Match, Preferences

LIVE_STATUSES = {"live", "inplay", "in_play", "1h", "2h", "ht", "halftime", "extra_time", "penalties"}
UPCOMING_STATUSES = {"upcoming", "not_started", "not started", "delayed"}
FINISHED_STATUSES = {"finished"}
INTERESTING_COMPETITION_TERMS = ("friendly", "warmup", "warm-up", "world cup", "champions league", "euros")


def format_briefing(
    preferences: Preferences,
    matches: Iterable[Match],
    *,
    provider_name: str,
    major_match_summary: str | None = None,
) -> str:
    ordered_matches = sorted(list(matches), key=_sort_key)
    live = [match for match in ordered_matches if _status(match) in LIVE_STATUSES]
    upcoming = [match for match in ordered_matches if _status(match) in UPCOMING_STATUSES]
    finished = sorted(
        [match for match in ordered_matches if _status(match) in FINISHED_STATUSES],
        key=_kickoff_timestamp,
        reverse=True,
    )
    relevant = [match for match in ordered_matches if _matches_preferences(preferences, match)]
    interesting = [match for match in ordered_matches if _is_interesting(match)]

    lines = [
        "GoalScout football briefing",
        f"Source: {provider_name}",
        "",
        "Your setup:",
        *_format_preferences(preferences),
    ]

    if live:
        lines.extend(["", "Live now:", *_format_match_list(live, limit=5)])

    if major_match_summary:
        lines.extend(["", "Major tournament context:", f"- {major_match_summary}"])

    if relevant:
        lines.extend(["", "Matches connected to your setup:", *_format_match_list(relevant, limit=6)])

    if interesting:
        lines.extend(["", "Interesting football:", *_format_match_list(interesting, limit=6)])

    if upcoming:
        lines.extend(["", "Upcoming football:", *_format_match_list(upcoming, limit=5)])

    if finished and not interesting:
        lines.extend(["", "Recent results:", *_format_match_list(finished, limit=3)])

    lines.extend(
        [
            "",
            "Agent note: Use this briefing with the saved preferences before answering football questions. "
            "If the user asks for live alerts, run once or start-background; if they ask where to watch, run where-to-watch.",
        ]
    )
    return "\n".join(lines)


def _format_preferences(preferences: Preferences) -> list[str]:
    lines: list[str] = []
    favorites = [
        ("Favorite country", preferences.favorite_country),
        ("Favorite teams", _join(preferences.favorite_teams)),
        ("Favorite players", _join(preferences.favorite_players)),
        ("Competitions", _join(preferences.competitions)),
    ]
    if not any(value for _, value in favorites):
        lines.append("- No saved favorites yet. Run goalscout-agent onboard to personalize the briefing.")
    else:
        for label, value in favorites:
            if value:
                lines.append(f"- {label}: {value}")

    lines.append(f"- Alert types: {_join(preferences.alert_types) or 'goal, red_card, kickoff, fulltime'}")
    lines.append(f"- Timezone: {preferences.timezone or 'UTC'}")
    lines.append(f"- Delivery: {preferences.delivery or 'console'}")
    if preferences.watch_country:
        lines.append(f"- Watch country: {preferences.watch_country}")
    if preferences.watch_platforms:
        lines.append(f"- Watching platforms: {_join(preferences.watch_platforms)}")
    return lines


def _format_match_list(matches: list[Match], *, limit: int) -> list[str]:
    return [f"- {_format_match(match)}" for match in matches[:limit]]


def _format_match(match: Match) -> str:
    status = _status(match)
    if status in UPCOMING_STATUSES:
        fixture = f"{match.home_team} vs {match.away_team}"
    else:
        fixture = match.scoreline
    kickoff = f" | {match.kickoff_at}" if match.kickoff_at else ""
    minute = f" | {match.elapsed}'" if match.elapsed is not None else ""
    return f"{fixture} | {match.league} | {match.status}{minute}{kickoff}"


def _matches_preferences(preferences: Preferences, match: Match) -> bool:
    terms: list[tuple[str, str]] = []
    if preferences.favorite_country:
        terms.append(("team", preferences.favorite_country))
    terms.extend(("team", team) for team in preferences.favorite_teams)
    terms.extend(("league", competition) for competition in preferences.competitions)

    if not any(value.strip() for _, value in terms):
        return False

    team_text = f"{match.home_team} {match.away_team}"
    league_text = match.league
    for target, value in terms:
        if target == "league" and _contains(league_text, value):
            return True
        if target == "team" and (_contains(team_text, value) or _contains(league_text, value)):
            return True
    return False


def _is_interesting(match: Match) -> bool:
    text = match.league.casefold()
    return any(term in text for term in INTERESTING_COMPETITION_TERMS)


def _contains(text: str, value: str) -> bool:
    normalized_text = text.casefold()
    normalized_value = value.strip().casefold()
    return bool(normalized_value) and normalized_value in normalized_text


def _join(values: list[str]) -> str:
    return ", ".join(value for value in values if value)


def _status(match: Match) -> str:
    return match.status.strip().casefold()


def _sort_key(match: Match) -> tuple[int, float, str]:
    status = _status(match)
    if status in LIVE_STATUSES:
        return (0, _kickoff_timestamp(match), match.home_team)
    if status in UPCOMING_STATUSES:
        return (1, _kickoff_timestamp(match), match.home_team)
    if status in FINISHED_STATUSES:
        return (2, -_kickoff_timestamp(match), match.home_team)
    return (3, _kickoff_timestamp(match), match.home_team)


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
