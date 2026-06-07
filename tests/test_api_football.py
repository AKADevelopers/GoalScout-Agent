from football_live_agent.providers.api_football import normalize_event, normalize_match


def test_normalize_match_from_api_football_fixture():
    raw = {
        "fixture": {"id": 123, "status": {"short": "1H", "elapsed": 44}},
        "teams": {"home": {"name": "Argentina"}, "away": {"name": "Brazil"}},
        "league": {"name": "World Cup"},
        "goals": {"home": 1, "away": 0},
    }

    match = normalize_match(raw)

    assert match.fixture_id == "123"
    assert match.scoreline == "Argentina 1-0 Brazil"


def test_normalize_goal_event_from_api_football_event():
    raw = {
        "time": {"elapsed": 44},
        "team": {"name": "Argentina"},
        "player": {"name": "Messi"},
        "type": "Goal",
        "detail": "Normal Goal",
    }

    event = normalize_event("123", raw)

    assert event.event_type == "goal"
    assert event.event_id == "123-goal-44-Argentina-Messi-Normal Goal"
