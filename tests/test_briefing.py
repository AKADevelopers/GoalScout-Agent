from football_live_agent.briefing import format_briefing
from football_live_agent.models import Match, Preferences


def test_briefing_summarizes_preferences_and_relevant_matches():
    preferences = Preferences(
        favorite_country="France",
        favorite_teams=["Manchester United"],
        favorite_players=["Mbappe"],
        competitions=["International Friendly"],
        alert_types=["goal", "red_card", "kickoff"],
        timezone="Asia/Karachi",
        watch_country="Pakistan",
        watch_platforms=["Tapmad", "FIFA+"],
    )
    matches = [
        Match("france-u23", "France Women U23", "USA Women U20", "International Friendly", "finished", None, 1, 2, "2026-06-08T11:00:00+00:00"),
        Match("uganda", "Uganda", "Madagascar", "International Friendly", "upcoming", None, None, None, "2026-06-08T12:00:00+00:00"),
        Match("local", "Local Club", "Other Club", "Regional League", "upcoming", None, None, None, "2026-06-08T13:00:00+00:00"),
    ]

    briefing = format_briefing(
        preferences,
        matches,
        provider_name="SportScore",
        major_match_summary="World Cup today: Mexico vs South Africa, GROUP A, 19:00 UTC",
    )

    assert "GoalScout football briefing" in briefing
    assert "Favorite country: France" in briefing
    assert "Favorite teams: Manchester United" in briefing
    assert "Favorite players: Mbappe" in briefing
    assert "Watch country: Pakistan" in briefing
    assert "Watching platforms: Tapmad, FIFA+" in briefing
    assert "Major tournament context:" in briefing
    assert "World Cup today: Mexico vs South Africa" in briefing
    assert "Matches connected to your setup:" in briefing
    assert "France Women U23 1-2 USA Women U20" in briefing
    assert "Uganda vs Madagascar" in briefing
    assert "Interesting football:" in briefing
    assert "International Friendly" in briefing


def test_briefing_handles_empty_preferences_with_general_matches():
    preferences = Preferences(favorite_country="", favorite_teams=[], favorite_players=[], competitions=[])
    matches = [
        Match("live", "Home", "Away", "Live League", "inplay", 55, 1, 0, None),
        Match("future", "Future Home", "Future Away", "Future League", "upcoming", None, None, None, "2026-06-08T18:00:00+00:00"),
    ]

    briefing = format_briefing(preferences, matches, provider_name="SportScore")

    assert "No saved favorites yet" in briefing
    assert "Live now:" in briefing
    assert "Home 1-0 Away" in briefing
    assert "Upcoming football:" in briefing
    assert "Future Home vs Future Away" in briefing
