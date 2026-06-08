from __future__ import annotations

import json
from pathlib import Path

from football_live_agent.models import Preferences

DEFAULT_ALERTS = ["goal", "red_card", "kickoff", "fulltime"]


def ask_csv(prompt: str) -> list[str]:
    value = input(prompt).strip()
    return [item.strip() for item in value.split(",") if item.strip()]


def run_onboarding(path: Path) -> Preferences:
    print("GoalScout Agent setup")
    favorite_country = input("Favorite country: ").strip()
    favorite_teams = ask_csv("Favorite teams or clubs, comma-separated: ")
    favorite_players = ask_csv("Favorite players, comma-separated: ")
    competitions = ask_csv("Competitions to follow, comma-separated: ")
    watch_country = input("Country where you watch matches, optional: ").strip()
    watch_platforms = ask_csv("Watching platforms you have, comma-separated, optional: ")
    watch_provider = (
        input("Where-to-watch provider: guide, sportmonks, or thesportsdb: ")
        .strip()
        .casefold()
        or "guide"
    )
    alerts = ask_csv("Alert types, comma-separated. Leave blank for goals, red cards, kickoff, fulltime: ")
    timezone = input("Timezone, for example Asia/Karachi: ").strip() or "UTC"
    quiet_hours_start = input("Quiet hours start, optional HH:MM: ").strip() or None
    quiet_hours_end = input("Quiet hours end, optional HH:MM: ").strip() or None
    delivery = input("Delivery mode: console, openclaw, hermes, webhook, or command: ").strip().casefold() or "console"
    channel = input("Messaging channel, for example telegram or whatsapp, optional: ").strip() or None
    target = input("Message target, chat id, username, or group, optional: ").strip() or None
    webhook_url = input("Webhook URL, optional: ").strip() or None
    channel_command = input("Custom channel command, optional: ").strip() or None

    preferences = Preferences(
        favorite_country=favorite_country,
        favorite_teams=favorite_teams,
        favorite_players=favorite_players,
        competitions=competitions,
        alert_types=alerts or DEFAULT_ALERTS,
        timezone=timezone,
        quiet_hours_start=quiet_hours_start,
        quiet_hours_end=quiet_hours_end,
        webhook_url=webhook_url,
        delivery=delivery,
        channel=channel,
        target=target,
        channel_command=channel_command,
        watch_country=watch_country,
        watch_platforms=watch_platforms,
        watch_provider=watch_provider,
    )
    save_preferences(path, preferences)
    return preferences


def load_preferences(path: Path) -> Preferences:
    with path.open("r", encoding="utf-8-sig") as handle:
        return Preferences.from_dict(json.load(handle))


def save_preferences(path: Path, preferences: Preferences) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(preferences.to_dict(), handle, indent=2, sort_keys=True)
        handle.write("\n")
