import urllib.error
from pathlib import Path

from football_live_agent.providers.sportscore import (
    SportScoreProvider,
    normalize_incident,
    normalize_match,
)


class FakeSportScoreProvider(SportScoreProvider):
    def __init__(self):
        super().__init__()

    def _get(self, path, params):
        assert path == "/matches/"
        return {
            "matches": [
                {
                    "home": "Live Home",
                    "away": "Live Away",
                    "home_score": 1,
                    "away_score": 0,
                    "status": "inplay",
                    "status_text": "55'",
                    "competition": "Live League",
                    "url": "/football/match/live-away-vs-live-home/",
                    "live_minute": 55,
                },
                {
                    "home": "Future Home",
                    "away": "Future Away",
                    "home_score": None,
                    "away_score": None,
                    "status": "upcoming",
                    "status_text": "Not started",
                    "competition": "Future League",
                    "url": "/football/match/future-away-vs-future-home/",
                    "live_minute": None,
                },
                {
                    "home": "Finished Home",
                    "away": "Finished Away",
                    "home_score": 1,
                    "away_score": 1,
                    "status": "finished",
                    "status_text": "Finished",
                    "competition": "Finished League",
                    "url": "/football/match/finished-away-vs-finished-home/",
                    "live_minute": None,
                },
            ]
        }


class DigestSportScoreProvider(SportScoreProvider):
    def __init__(self):
        super().__init__()

    def _get(self, path, params):
        assert path == "/matches/"
        return {
            "matches": [
                {
                    "home": "Finished Home",
                    "away": "Finished Away",
                    "home_score": 2,
                    "away_score": 1,
                    "status": "finished",
                    "status_text": "Finished",
                    "competition": "Finished League",
                    "url": "/football/match/finished-away-vs-finished-home/",
                    "time": "2026-06-04T12:00:00+00:00",
                },
                {
                    "home": "Future Home",
                    "away": "Future Away",
                    "home_score": None,
                    "away_score": None,
                    "status": "upcoming",
                    "status_text": "Not started",
                    "competition": "Future League",
                    "url": "/football/match/future-away-vs-future-home/",
                    "time": "2026-06-04T18:00:00+00:00",
                },
            ]
        }


def test_live_matches_only_returns_in_play_matches():
    matches = FakeSportScoreProvider().live_matches()

    assert [match.fixture_id for match in matches] == ["live-away-vs-live-home"]


def test_sportscore_falls_back_to_powershell_when_urllib_fails(monkeypatch):
    attempts = {"count": 0}

    def failing_urlopen(*_args, **_kwargs):
        attempts["count"] += 1
        raise urllib.error.URLError("timed out")

    class Result:
        returncode = 0
        stdout = """
        {
          "matches": [
            {
              "home": "Live Home",
              "away": "Live Away",
              "home_score": 1,
              "away_score": 0,
              "status": "inplay",
              "status_text": "55'",
              "competition": "Live League",
              "url": "/football/match/live-away-vs-live-home/",
              "live_minute": 55
            }
          ]
        }
        """
        stderr = ""

    captured = {}

    def runner(args, **kwargs):
        captured["args"] = args
        captured["kwargs"] = kwargs
        return Result()

    monkeypatch.setattr("urllib.request.urlopen", failing_urlopen)

    matches = SportScoreProvider(powershell_runner=runner).live_matches()

    assert matches[0].fixture_id == "live-away-vs-live-home"
    assert captured["args"][0] == "powershell"
    assert "-TimeoutSec 15" in captured["args"][3]
    assert captured["kwargs"]["timeout"] == 20
    assert attempts["count"] == 1


def test_sportscore_uses_short_http_timeout_for_live_polling(monkeypatch):
    captured = {}

    def successful_urlopen(_request, timeout):
        captured["timeout"] = timeout

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"matches":[]}'

        return Response()

    monkeypatch.setattr("urllib.request.urlopen", successful_urlopen)

    assert SportScoreProvider().live_matches() == []
    assert captured["timeout"] == 12


def test_sportscore_reuses_cached_response_when_network_fails(monkeypatch, tmp_path):
    provider = SportScoreProvider(cache_dir=tmp_path)
    cache_path = provider._cache_path("/matches/", {"sport": "football", "limit": "50", "src": "goalscout-agent"})
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        """
        {
          "matches": [
            {
              "home": "Cached Home",
              "away": "Cached Away",
              "home_score": 1,
              "away_score": 0,
              "status": "inplay",
              "status_text": "55'",
              "competition": "Cached League",
              "url": "/football/match/cached-away-vs-cached-home/",
              "live_minute": 55
            }
          ]
        }
        """,
        encoding="utf-8",
    )

    def failing_urlopen(*_args, **_kwargs):
        raise urllib.error.URLError("timed out")

    class Result:
        returncode = 1
        stdout = ""
        stderr = "timed out"

    monkeypatch.setattr("urllib.request.urlopen", failing_urlopen)

    matches = SportScoreProvider(cache_dir=tmp_path, powershell_runner=lambda *_args, **_kwargs: Result()).live_matches()

    assert matches[0].fixture_id == "cached-away-vs-cached-home"


def test_sportscore_retries_before_falling_back(monkeypatch, tmp_path):
    attempts = {"count": 0}

    def flaky_urlopen(*_args, **_kwargs):
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise urllib.error.URLError("timed out")

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            def read(self):
                return b'{"matches":[]}'

        return Response()

    monkeypatch.setattr("urllib.request.urlopen", flaky_urlopen)

    matches = SportScoreProvider(cache_dir=tmp_path, retries=2).live_matches()

    assert matches == []
    assert attempts["count"] == 2


def test_football_update_uses_recent_result_and_upcoming_fixture():
    update = DigestSportScoreProvider().football_update()

    assert "Football is not live for your alert right now" in update
    assert "Latest result: Finished Home 2-1 Finished Away" in update
    assert "Next fixture: Future Home vs Future Away" in update


def test_football_update_reuses_matches_loaded_by_live_matches():
    class CountingProvider(DigestSportScoreProvider):
        def __init__(self):
            super().__init__()
            self.calls = 0

        def _get(self, path, params):
            self.calls += 1
            return super()._get(path, params)

    provider = CountingProvider()

    assert provider.live_matches() == []
    assert "Latest result: Finished Home 2-1 Finished Away" in provider.football_update()
    assert provider.calls == 1


def test_normalize_match_uses_slug_from_sportscore_url():
    raw = {
        "home": "Birmingham Legion",
        "away": "Louisville City FC",
        "home_score": 1,
        "away_score": 1,
        "status": "inplay",
        "status_text": "57'",
        "competition": "USL Championship",
        "url": "/football/match/louisville-city-fc-vs-birmingham-legion/",
        "live_minute": 57,
    }

    match = normalize_match(raw)

    assert match.fixture_id == "louisville-city-fc-vs-birmingham-legion"
    assert match.scoreline == "Birmingham Legion 1-1 Louisville City FC"
    assert match.elapsed == 57


def test_normalize_goal_incident_uses_side_team_and_score():
    match = normalize_match(
        {
            "home": "Birmingham Legion",
            "away": "Louisville City FC",
            "home_score": 1,
            "away_score": 1,
            "status": "inplay",
            "status_text": "57'",
            "competition": "USL Championship",
            "url": "/football/match/louisville-city-fc-vs-birmingham-legion/",
            "live_minute": 57,
        }
    )
    raw = {
        "time": 42,
        "type": "Goal",
        "side": "away",
        "player": "babacar niang",
        "is_goal": True,
        "home_score": 1,
        "away_score": 1,
    }

    event = normalize_incident(match, raw)

    assert event.event_type == "goal"
    assert event.team == "Louisville City FC"
    assert event.player == "babacar niang"
    assert event.event_id == "louisville-city-fc-vs-birmingham-legion-goal-42-Louisville City FC-babacar niang-1-1"


def test_normalize_substitution_incident_includes_player_detail():
    match = normalize_match(
        {
            "home": "Birmingham Legion",
            "away": "Louisville City FC",
            "home_score": 1,
            "away_score": 1,
            "status": "inplay",
            "status_text": "57'",
            "competition": "USL Championship",
            "url": "/football/match/louisville-city-fc-vs-birmingham-legion/",
        }
    )
    raw = {
        "time": 45,
        "type": "Substitution",
        "side": "away",
        "player": "",
        "is_sub": True,
        "player_in": "Zach Duncan",
        "player_out": "babacar niang",
    }

    event = normalize_incident(match, raw)

    assert event.event_type == "substitution"
    assert event.player == "Zach Duncan"
    assert event.detail == "Zach Duncan for babacar niang"
