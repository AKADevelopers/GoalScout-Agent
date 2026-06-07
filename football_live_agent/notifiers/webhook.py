from __future__ import annotations

import json
import urllib.error
import urllib.request

from football_live_agent.models import Event, Match


class WebhookNotifier:
    def __init__(self, url: str) -> None:
        self.url = url

    def send(self, match: Match, event: Event) -> None:
        payload = {
            "event_type": event.event_type,
            "minute": event.minute,
            "team": event.team,
            "player": event.player,
            "detail": event.detail,
            "fixture_id": event.fixture_id,
            "match": {
                "home_team": match.home_team,
                "away_team": match.away_team,
                "scoreline": match.scoreline,
                "league": match.league,
                "status": match.status,
            },
            "text": f"{event.event_type.upper()} {match.scoreline}",
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10):
                return
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Webhook notification failed: {exc}") from exc
