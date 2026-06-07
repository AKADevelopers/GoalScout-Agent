import pytest

from football_live_agent import cli
from football_live_agent.cli import build_notifiers, build_provider, main
from football_live_agent.config import Settings
from football_live_agent.models import Preferences
from football_live_agent.notifiers.command import CommandNotifier
from football_live_agent.onboarding import save_preferences
from football_live_agent.providers.api_football import ProviderError
from football_live_agent.providers.sportscore import SportScoreProvider


def test_cli_help_exits_zero(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    assert "GoalScout Agent live football notification watcher" in capsys.readouterr().out


def test_cli_preferences_requires_onboarding(monkeypatch, tmp_path):
    monkeypatch.setenv("FOOTBALL_AGENT_DATA_DIR", str(tmp_path))

    try:
        main(["preferences"])
    except SystemExit as exc:
        assert str(exc) == "No preferences found. Run: goalscout-agent onboard"


def test_build_provider_uses_sportscore_without_api_key(tmp_path):
    settings = Settings(
        provider="sportscore",
        poll_seconds=60,
        data_dir=tmp_path,
        api_football_key=None,
        webhook_url=None,
        delivery="console",
        channel_command=None,
        channel=None,
        target=None,
        console_enabled=True,
    )

    assert isinstance(build_provider(settings), SportScoreProvider)


def test_build_notifiers_adds_openclaw_command_notifier(tmp_path):
    settings = Settings(
        provider="sportscore",
        poll_seconds=60,
        data_dir=tmp_path,
        api_football_key=None,
        webhook_url=None,
        delivery="openclaw",
        channel_command=None,
        channel="telegram",
        target="@football",
        console_enabled=False,
    )
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=[],
        competitions=[],
        alert_types=["goal"],
        timezone="Asia/Karachi",
    )

    notifiers = build_notifiers(settings, preferences)

    assert len(notifiers) == 1
    assert isinstance(notifiers[0], CommandNotifier)


def test_build_notifiers_uses_saved_delivery_preferences(tmp_path):
    settings = Settings(
        provider="sportscore",
        poll_seconds=60,
        data_dir=tmp_path,
        api_football_key=None,
        webhook_url=None,
        delivery="console",
        channel_command=None,
        channel=None,
        target=None,
        console_enabled=False,
    )
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=[],
        competitions=[],
        alert_types=["goal"],
        timezone="Asia/Karachi",
        delivery="hermes",
        channel="telegram",
        target="@football",
    )

    notifiers = build_notifiers(settings, preferences)

    assert len(notifiers) == 1
    assert isinstance(notifiers[0], CommandNotifier)


def test_once_reports_provider_error_without_traceback(monkeypatch, tmp_path, capsys):
    save_preferences(
        tmp_path / "preferences.json",
        Preferences(
            favorite_country="",
            favorite_teams=[],
            favorite_players=[],
            competitions=[],
            alert_types=["goal"],
            timezone="Asia/Karachi",
        ),
    )
    monkeypatch.setenv("FOOTBALL_AGENT_DATA_DIR", str(tmp_path))

    class FailingProvider:
        def live_matches(self):
            raise ProviderError("SportScore network error: timed out")

        def events_for_fixture(self, fixture_id):
            return []

    monkeypatch.setattr(cli, "build_provider", lambda _settings: FailingProvider())

    with pytest.raises(SystemExit) as exc:
        main(["once"])

    assert str(exc.value) == "Provider error: SportScore network error: timed out"
    assert "GoalScout Agent is working, but the live football provider is unavailable right now." in capsys.readouterr().out


def test_once_sends_health_message_when_no_notifications(monkeypatch, tmp_path, capsys):
    save_preferences(
        tmp_path / "preferences.json",
        Preferences(
            favorite_country="",
            favorite_teams=[],
            favorite_players=[],
            competitions=[],
            alert_types=["goal"],
            timezone="Asia/Karachi",
        ),
    )
    monkeypatch.setenv("FOOTBALL_AGENT_DATA_DIR", str(tmp_path))

    class EmptyProvider:
        def live_matches(self):
            return []

        def events_for_fixture(self, fixture_id):
            return []

        def football_update(self):
            return "Football is not live for your alert right now. Latest result: A 1-0 B. Next fixture: C vs D."

    monkeypatch.setattr(cli, "build_provider", lambda _settings: EmptyProvider())

    assert main(["once"]) == 0

    output = capsys.readouterr().out
    assert "GoalScout Agent is working" in output
    assert "Latest result: A 1-0 B" in output
    assert "Sent 0 notification(s)." in output


def test_health_check_sends_status_message(monkeypatch, tmp_path, capsys):
    save_preferences(
        tmp_path / "preferences.json",
        Preferences(
            favorite_country="",
            favorite_teams=[],
            favorite_players=[],
            competitions=[],
            alert_types=["goal"],
            timezone="Asia/Karachi",
        ),
    )
    monkeypatch.setenv("FOOTBALL_AGENT_DATA_DIR", str(tmp_path))

    assert main(["health-check"]) == 0

    assert "GoalScout Agent is working" in capsys.readouterr().out


def test_where_to_watch_command_prints_user_platform_guide(monkeypatch, tmp_path, capsys):
    save_preferences(
        tmp_path / "preferences.json",
        Preferences(
            favorite_country="",
            favorite_teams=[],
            favorite_players=[],
            competitions=[],
            alert_types=["goal"],
            timezone="Asia/Karachi",
            watch_country="United States",
            watch_platforms=["Peacock", "Fubo"],
            watch_provider="guide",
        ),
    )
    monkeypatch.setenv("FOOTBALL_AGENT_DATA_DIR", str(tmp_path))

    assert main(["where-to-watch"]) == 0

    output = capsys.readouterr().out
    assert "Where to watch setup" in output
    assert "United States" in output
    assert "Peacock, Fubo" in output
