from __future__ import annotations

from football_live_agent.models import Event, Match


class ConsoleNotifier:
    def send(self, match: Match, event: Event) -> None:
        print(format_notification(match, event))


def format_notification(match: Match, event: Event) -> str:
    if event.event_type == "health_check":
        return event.detail or "GoalScout Agent is working."
    player = f" - {event.player}" if event.player else ""
    return f"[{event.display_minute}] {event.event_type.upper()} {match.scoreline} ({event.team}{player})"
