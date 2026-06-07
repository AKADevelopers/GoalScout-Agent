from football_live_agent.models import Event, Match, Preferences


def test_preferences_match_favorite_team_and_goal_type():
    preferences = Preferences(
        favorite_country="Argentina",
        favorite_teams=["Argentina", "Inter Miami"],
        favorite_players=["Messi"],
        competitions=["World Cup"],
        alert_types=["goal", "red_card"],
        timezone="Asia/Karachi",
    )
    match = Match(
        fixture_id="10",
        home_team="Argentina",
        away_team="Brazil",
        league="World Cup",
        status="LIVE",
        elapsed=55,
        home_goals=2,
        away_goals=1,
    )
    event = Event(
        event_id="10-goal-55-Messi",
        fixture_id="10",
        event_type="goal",
        minute=55,
        team="Argentina",
        player="Messi",
        detail="Normal Goal",
    )

    assert preferences.should_notify(match, event) is True


def test_preferences_reject_unfollowed_team():
    preferences = Preferences(
        favorite_country="Pakistan",
        favorite_teams=["Pakistan"],
        favorite_players=[],
        competitions=[],
        alert_types=["goal"],
        timezone="Asia/Karachi",
    )
    match = Match(
        fixture_id="11",
        home_team="France",
        away_team="Germany",
        league="Friendly",
        status="LIVE",
        elapsed=20,
        home_goals=0,
        away_goals=1,
    )
    event = Event(
        event_id="11-goal-20",
        fixture_id="11",
        event_type="goal",
        minute=20,
        team="Germany",
        player="",
        detail="Normal Goal",
    )

    assert preferences.should_notify(match, event) is False


def test_preferences_store_delivery_memory_fields():
    preferences = Preferences(
        favorite_country="Argentina",
        delivery="openclaw",
        channel="telegram",
        target="@football",
        channel_command=None,
    )

    reloaded = Preferences.from_dict(preferences.to_dict())

    assert reloaded.delivery == "openclaw"
    assert reloaded.channel == "telegram"
    assert reloaded.target == "@football"
