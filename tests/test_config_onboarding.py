import json

from football_live_agent.config import load_settings
from football_live_agent.models import Preferences
from football_live_agent.onboarding import load_preferences, run_onboarding, save_preferences


def test_load_settings_uses_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("FOOTBALL_AGENT_PROVIDER", "api-football")
    monkeypatch.setenv("API_FOOTBALL_KEY", "secret")
    monkeypatch.setenv("FOOTBALL_AGENT_POLL_SECONDS", "5")
    monkeypatch.setenv("FOOTBALL_AGENT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("FOOTBALL_AGENT_WEBHOOK_URL", "https://example.test/hook")

    settings = load_settings()

    assert settings.provider == "api-football"
    assert settings.api_football_key == "secret"
    assert settings.poll_seconds == 10
    assert settings.data_dir == tmp_path
    assert settings.webhook_url == "https://example.test/hook"
    assert settings.delivery == "console"


def test_load_settings_defaults_to_no_key_sportscore(monkeypatch):
    monkeypatch.delenv("FOOTBALL_AGENT_PROVIDER", raising=False)
    monkeypatch.delenv("API_FOOTBALL_KEY", raising=False)
    monkeypatch.delenv("FOOTBALL_AGENT_POLL_SECONDS", raising=False)

    settings = load_settings()

    assert settings.provider == "sportscore"
    assert settings.api_football_key is None
    assert settings.poll_seconds == 60


def test_load_settings_reads_channel_delivery(monkeypatch):
    monkeypatch.setenv("FOOTBALL_AGENT_DELIVERY", "openclaw")
    monkeypatch.setenv("FOOTBALL_AGENT_CHANNEL", "telegram")
    monkeypatch.setenv("FOOTBALL_AGENT_TARGET", "@football")
    monkeypatch.setenv("FOOTBALL_AGENT_CONSOLE", "0")

    settings = load_settings()

    assert settings.delivery == "openclaw"
    assert settings.channel == "telegram"
    assert settings.target == "@football"
    assert settings.console_enabled is False


def test_preferences_round_trip(tmp_path):
    path = tmp_path / "preferences.json"
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina"],
        favorite_players=["Messi"],
        competitions=["World Cup"],
        alert_types=["goal"],
        timezone="Asia/Karachi",
        webhook_url="https://example.test/hook",
    )

    save_preferences(path, preferences)

    assert json.loads(path.read_text(encoding="utf-8"))["favorite_country"] == "Argentina"
    assert load_preferences(path) == preferences


def test_load_preferences_accepts_utf8_bom(tmp_path):
    path = tmp_path / "preferences.json"
    path.write_bytes(
        b'\xef\xbb\xbf{"favorite_country":"Argentina","favorite_teams":[],"favorite_players":[],"competitions":[],"alert_types":["goal"],"timezone":"Asia/Karachi"}'
    )

    assert load_preferences(path).favorite_country == "Argentina"


def test_run_onboarding_saves_channel_delivery(monkeypatch, tmp_path):
    answers = iter(
        [
            "Argentina",
            "Argentina, Inter Miami",
            "Messi",
            "World Cup",
            "goal, red_card",
            "Asia/Karachi",
            "",
            "",
            "openclaw",
            "telegram",
            "@football",
            "",
            "",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    preferences = run_onboarding(tmp_path / "preferences.json")

    assert preferences.delivery == "openclaw"
    assert preferences.channel == "telegram"
    assert preferences.target == "@football"
