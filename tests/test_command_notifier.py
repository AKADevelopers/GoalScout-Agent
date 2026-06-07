from football_live_agent.models import Event, Match
from football_live_agent.notifiers.command import CommandNotifier, build_platform_command


def test_command_notifier_renders_message_channel_and_target():
    captured = {}

    def runner(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs

        class Result:
            returncode = 0
            stderr = ""

        return Result()

    notifier = CommandNotifier(
        ["openclaw", "message", "send", "--channel", "{channel}", "--target", "{target}", "--message", "{message}"],
        channel="telegram",
        target="@football",
        runner=runner,
    )
    match = Match("1", "Argentina", "Brazil", "World Cup", "LIVE", 55, 2, 1)
    event = Event("1-goal-55", "1", "goal", 55, "Argentina", "Messi", "Normal Goal")

    notifier.send(match, event)

    assert captured["args"] == [
        "openclaw",
        "message",
        "send",
        "--channel",
        "telegram",
        "--target",
        "@football",
        "--message",
        "[55'] GOAL Argentina 2-1 Brazil (Argentina - Messi)",
    ]
    assert captured["kwargs"]["check"] is False


def test_build_platform_command_uses_openclaw_message_send():
    command = build_platform_command("openclaw")

    assert command == [
        "openclaw",
        "message",
        "send",
        "--channel",
        "{channel}",
        "--target",
        "{target}",
        "--message",
        "{message}",
    ]


def test_build_platform_command_uses_hermes_message_send():
    command = build_platform_command("hermes")

    assert command == [
        "hermes",
        "message",
        "send",
        "--channel",
        "{channel}",
        "--target",
        "{target}",
        "--message",
        "{message}",
    ]
