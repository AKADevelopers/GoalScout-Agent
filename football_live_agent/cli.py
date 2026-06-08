from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from football_live_agent.config import Settings, load_settings
from football_live_agent.memory import FootballMemory
from football_live_agent.models import Event, Match, Preferences
from football_live_agent.notifiers.base import Notifier
from football_live_agent.notifiers.command import CommandNotifier, build_platform_command, split_command_template
from football_live_agent.notifiers.console import ConsoleNotifier
from football_live_agent.notifiers.webhook import WebhookNotifier
from football_live_agent.onboarding import load_preferences, run_onboarding, save_preferences
from football_live_agent.preferences import repair_preferences, validate_preferences
from football_live_agent.providers.api_football import ApiFootballProvider, ProviderError
from football_live_agent.providers.base import FootballProvider
from football_live_agent.providers.sportscore import SportScoreProvider
from football_live_agent.service import pid_status, start_background, stop_background
from football_live_agent.state import JsonState
from football_live_agent.watcher import calculate_poll_delay, run_once, watch_forever
from football_live_agent.where_to_watch import (
    GuideWatchProvider,
    SetupOnlyWatchProvider,
    SportmonksTVProvider,
    TheSportsDBTVProvider,
    WatchProviderError,
    format_watch_summary,
    normalize_provider,
)


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


def build_watch_provider(settings: Settings, preferences: Preferences, provider_name: str | None = None):
    provider = normalize_provider(provider_name or settings.watch_provider or preferences.watch_provider)
    if provider == "guide":
        return GuideWatchProvider()
    if provider == "sportmonks":
        return SportmonksTVProvider(settings.sportmonks_key or "")
    if provider == "thesportsdb":
        return TheSportsDBTVProvider(settings.thesportsdb_key or "")
    if provider == "sportradar":
        return SetupOnlyWatchProvider(
            "sportradar",
            "Sportradar where-to-watch lookup is an enterprise BYOK option. Set SPORTRADAR_API_KEY after your Sportradar contract is active.",
        )
    if provider == "gracenote":
        return SetupOnlyWatchProvider(
            "gracenote",
            "Gracenote On API is an enterprise BYOK option for official live sports broadcast and streaming listings. Set GRACENOTE_API_KEY after your contract is active.",
        )
    if provider == "justwatch":
        return SetupOnlyWatchProvider(
            "justwatch",
            "JustWatch sports/partner lookup requires a partner token. Set JUSTWATCH_PARTNER_TOKEN after your partner access is active.",
        )
    raise SystemExit(f"Unsupported where-to-watch provider: {provider}")


def _load_preferences_with_repair(path: Path, *, save_repaired: bool) -> tuple[Preferences, list[str]]:
    preferences = load_preferences(path)
    repaired, changes = repair_preferences(preferences)
    if changes and save_repaired:
        save_preferences(path, repaired)
    return repaired, changes


def _print_preference_diagnostics(issues: list[str]) -> None:
    if not issues:
        print("No preference issues found.")
        return
    print("Preference issues:")
    for issue in issues:
        print(f"- {issue}")


def _print_repair_diagnostics(changes: list[str]) -> None:
    if not changes:
        print("No changes were needed.")
        return
    print("Repaired preferences:")
    for change in changes:
        print(f"- {change}")


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
    doctor_parser = subcommands.add_parser("doctor")
    doctor_parser.add_argument("--fix", action="store_true")
    subcommands.add_parser("repair")
    watch_parser = subcommands.add_parser("where-to-watch")
    watch_parser.add_argument("fixture_id", nargs="?")
    watch_parser.add_argument("--provider", dest="watch_provider")
    watch_parser.add_argument("--team")
    watch_parser.add_argument("--competition")
    watch_parser.add_argument("--date")
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
        preferences = run_onboarding(pref_path)
        repaired, changes = repair_preferences(preferences)
        if changes:
            save_preferences(pref_path, repaired)
            _print_repair_diagnostics(changes)
        print(f"Saved preferences to {pref_path}")
        return 0

    if not pref_path.exists():
        raise SystemExit("No preferences found. Run: goalscout-agent onboard")

    if args.command == "doctor":
        preferences = load_preferences(pref_path)
        issues = validate_preferences(preferences)
        _print_preference_diagnostics(issues)
        if args.fix:
            repaired, changes = repair_preferences(preferences)
            if changes:
                save_preferences(pref_path, repaired)
                _print_repair_diagnostics(changes)
        return 0

    if args.command == "repair":
        preferences = load_preferences(pref_path)
        repaired, changes = repair_preferences(preferences)
        save_preferences(pref_path, repaired)
        _print_repair_diagnostics(changes)
        return 0

    preferences, changes = _load_preferences_with_repair(pref_path, save_repaired=True)
    if changes and args.command != "preferences":
        # Keep migrations quiet during normal use.
        pass

    if args.command == "preferences":
        print(json.dumps(preferences.to_dict(), indent=2, sort_keys=True))
        return 0

    if args.command == "memory":
        print(memory.summary())
        return 0

    if args.command == "health-check":
        send_health_check(build_notifiers(settings, preferences))
        return 0

    if args.command == "where-to-watch":
        provider = build_watch_provider(settings, preferences, getattr(args, "watch_provider", None))
        try:
            options = provider.options_for_fixture(args.fixture_id) if args.fixture_id else []
        except WatchProviderError as exc:
            raise SystemExit(str(exc)) from exc
        print(
            format_watch_summary(
                preferences,
                options,
                provider_name=provider.provider_name,
                fixture_id=args.fixture_id,
                team_name=getattr(args, "team", None),
                competition_name=getattr(args, "competition", None),
                match_date=getattr(args, "date", None),
            )
        )
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
                detail="Football status: the live football provider is unavailable right now.",
            )
            raise SystemExit(f"Provider error: {exc}") from exc
        if sent == 0:
            update = provider_update(provider)
            detail = "Football status: no live matching football alert was found right now."
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
