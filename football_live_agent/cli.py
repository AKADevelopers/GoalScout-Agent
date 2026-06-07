from __future__ import annotations

import argparse
import json
from typing import Sequence

from football_live_agent.config import Settings, load_settings
from football_live_agent.memory import FootballMemory
from football_live_agent.models import Event, Match, Preferences
from football_live_agent.notifiers.base import Notifier
from football_live_agent.notifiers.command import CommandNotifier, build_platform_command, split_command_template
from football_live_agent.notifiers.console import ConsoleNotifier
from football_live_agent.notifiers.webhook import WebhookNotifier
from football_live_agent.onboarding import load_preferences, run_onboarding
from football_live_agent.providers.api_football import ApiFootballProvider, ProviderError
from football_live_agent.providers.base import FootballProvider
from football_live_agent.providers.sportscore import SportScoreProvider
from football_live_agent.service import pid_status, start_background, stop_background
from football_live_agent.state import JsonState
from football_live_agent.watcher import run_once, watch_forever


def build_provider(settings: Settings) -> FootballProvider:
    if settings.provider == "sportscore":
        return SportScoreProvider(cache_dir=settings.data_dir)
    if settings.provider != "api-football":
        raise SystemExit(f"Unsupported provider: {settings.provider}")
    return ApiFootballProvider(settings.api_football_key)


def build_notifiers(settings: Settings, preferences: Preferences) -> list[Notifier]:
    notifiers: list[Notifier] = []
    delivery = settings.delivery if settings.delivery != "console" else preferences.delivery
    channel = settings.channel or preferences.channel
    target = settings.target or preferences.target
    channel_command = settings.channel_command or preferences.channel_command
    webhook_url = settings.webhook_url or preferences.webhook_url

    if settings.console_enabled or delivery == "console":
        notifiers.append(ConsoleNotifier())
    if webhook_url or delivery == "webhook":
        if not webhook_url:
            raise SystemExit("FOOTBALL_AGENT_WEBHOOK_URL is required for webhook delivery.")
        notifiers.append(WebhookNotifier(webhook_url))
    if channel_command:
        notifiers.append(
            CommandNotifier(
                split_command_template(channel_command),
                channel=channel,
                target=target,
            )
        )
    elif delivery in {"openclaw", "hermes"}:
        if not channel or not target:
            raise SystemExit("FOOTBALL_AGENT_CHANNEL and FOOTBALL_AGENT_TARGET are required for channel delivery.")
        notifiers.append(
            CommandNotifier(
                build_platform_command(delivery),
                channel=channel,
                target=target,
            )
        )
    return notifiers


def send_health_check(notifiers: Sequence[Notifier], detail: str | None = None) -> None:
    match = Match("health", "GoalScout Agent", "Delivery", "Health Check", "OK", None, None, None)
    event = Event(
        "health-check",
        "health",
        "health_check",
        None,
        "GoalScout Agent",
        "",
        detail or "GoalScout Agent is working. No live matching football alert was found right now.",
    )
    for notifier in notifiers:
        notifier.send(match, event)


def provider_update(provider: FootballProvider) -> str | None:
    update = getattr(provider, "football_update", None)
    if update is None:
        return None
    return str(update())


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="GoalScout Agent live football notification watcher")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("onboard")
    subcommands.add_parser("preferences")
    subcommands.add_parser("once")
    subcommands.add_parser("watch")
    subcommands.add_parser("memory")
    subcommands.add_parser("health-check")
    subcommands.add_parser("start-background")
    subcommands.add_parser("status")
    subcommands.add_parser("stop")
    subcommands.add_parser("test-notification")
    args = parser.parse_args(list(argv) if argv is not None else None)

    settings = load_settings()
    pref_path = settings.data_dir / "preferences.json"
    state = JsonState(settings.data_dir / "state.json")
    memory = FootballMemory(settings.data_dir / "memory.json")

    if args.command == "status":
        print(pid_status(settings.data_dir / "watcher.pid"))
        return 0

    if args.command == "stop":
        print(stop_background(settings.data_dir / "watcher.pid"))
        return 0

    if args.command == "onboard":
        run_onboarding(pref_path)
        print(f"Saved preferences to {pref_path}")
        return 0

    if not pref_path.exists():
        raise SystemExit("No preferences found. Run: goalscout-agent onboard")

    preferences = load_preferences(pref_path)

    if args.command == "preferences":
        print(json.dumps(preferences.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "memory":
        print(memory.summary())
        return 0

    if args.command == "health-check":
        send_health_check(build_notifiers(settings, preferences))
        return 0

    if args.command == "start-background":
        pid = start_background(settings)
        print(f"GoalScout Agent watcher started in background with pid {pid}.")
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
        try:
            sent = run_once(provider, preferences, state, notifiers, memory=memory)
        except ProviderError as exc:
            send_health_check(
                notifiers,
                detail="GoalScout Agent is working, but the live football provider is unavailable right now.",
            )
            raise SystemExit(f"Provider error: {exc}") from exc
        if sent == 0:
            update = provider_update(provider)
            detail = "GoalScout Agent is working. No live matching football alert was found right now."
            if update:
                detail = f"{detail} {update}"
            send_health_check(notifiers, detail=detail)
        print(f"Sent {sent} notification(s).")
        return 0

    if args.command == "watch":
        watch_forever(provider, preferences, state, notifiers, settings.poll_seconds, memory=memory)
        return 0

    raise SystemExit(f"Unknown command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
