from football_live_agent.models import Preferences
from football_live_agent.preferences import repair_preferences, validate_preferences


def test_validate_preferences_reports_invalid_delivery_and_provider():
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=[],
        competitions=[],
        alert_types=["goal"],
        timezone="Asia/Karachi",
        delivery="sms",
        watch_provider="unknown",
    )

    issues = validate_preferences(preferences)

    assert any("delivery" in issue for issue in issues)
    assert any("watch provider" in issue for issue in issues)


def test_repair_preferences_normalizes_saved_values():
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=[],
        competitions=[],
        alert_types=["Goal", "missed penalty", "VAR Goal Cancelled", ""],
        timezone="Asia/Karachi",
        delivery="Hermes",
        channel="telegram",
        target="@football",
        watch_provider="TheSportsDB",
    )

    repaired, changes = repair_preferences(preferences)

    assert repaired.delivery == "hermes"
    assert repaired.watch_provider == "thesportsdb"
    assert repaired.alert_types == ["goal", "missed_penalty", "var_goal_cancelled"]
    assert changes


def test_repair_preferences_falls_back_to_console_when_delivery_is_incomplete():
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=[],
        competitions=[],
        alert_types=["goal"],
        timezone="Asia/Karachi",
        delivery="openclaw",
        channel=None,
        target=None,
        webhook_url=None,
        channel_command=None,
    )

    repaired, changes = repair_preferences(preferences)

    assert repaired.delivery == "console"
    assert any("console" in change for change in changes)