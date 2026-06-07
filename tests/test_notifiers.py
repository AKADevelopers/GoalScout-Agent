import json

from football_live_agent.models import Event, Match
from football_live_agent.notifiers.console import format_notification
from football_live_agent.notifiers.webhook import WebhookNotifier


def test_format_notification_includes_minute_type_score_and_player():
    match = Match("1", "Argentina", "Brazil", "World Cup", "LIVE", 55, 2, 1)
    event = Event("1-goal-55", "1", "goal", 55, "Argentina", "Messi", "Normal Goal")

    assert format_notification(match, event) == "[55'] GOAL Argentina 2-1 Brazil (Argentina - Messi)"


def test_format_notification_handles_health_check_message():
    match = Match("health", "GoalScout Agent", "Delivery", "Health", "OK", None, None, None)
    event = Event("health", "health", "health_check", None, "GoalScout Agent", "", "GoalScout Agent is working.")

    assert format_notification(match, event) == "GoalScout Agent is working."


def test_webhook_notifier_posts_json(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["content_type"] = request.headers["Content-type"]
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    match = Match("1", "Argentina", "Brazil", "World Cup", "LIVE", 55, 2, 1)
    event = Event("1-goal-55", "1", "goal", 55, "Argentina", "Messi", "Normal Goal")

    WebhookNotifier("https://example.test/hook").send(match, event)

    assert captured["url"] == "https://example.test/hook"
    assert captured["timeout"] == 10
    assert captured["content_type"] == "application/json"
    assert captured["body"]["event_type"] == "goal"
    assert captured["body"]["match"]["scoreline"] == "Argentina 2-1 Brazil"
