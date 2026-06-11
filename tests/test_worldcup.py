import json

from football_live_agent.worldcup import WorldCupFixture, parse_fox_world_cup_fixtures, world_cup_today_summary


def _nuxt_html(data):
    return (
        '<script type="application/json" data-nuxt-data="nuxt-app" data-ssr="true" id="__NUXT_DATA__">'
        + json.dumps(data)
        + "</script>"
    )


def test_parse_fox_world_cup_fixtures_from_nuxt_payload():
    data = [
        {"parsedScoreboard": 1, "parsedSegmentRes": 2},
        {"title": 3},
        {"events": 4},
        "TOP SCORES",
        [5, 16, 5],
        {"league": 6, "eventHeadline": 7, "eventTime": 8, "upperTeam": 9, "lowerTeam": 12, "gameNotes": 15},
        "WORLD CUP",
        "Mexico meets South Africa in Mexico City Stadium",
        "2026-06-11T19:00:00Z",
        {"longName": 10},
        "Mexico",
        "MEX",
        {"longName": 13},
        "South Africa",
        "RSA",
        "GROUP A",
        {"league": 17, "eventTime": 8, "upperTeam": 18, "lowerTeam": 20, "gameNotes": 15},
        "International Friendly",
        {"longName": 19},
        "Austria",
        {"longName": 21},
        "Guatemala",
    ]

    fixtures = parse_fox_world_cup_fixtures(_nuxt_html(data))

    assert fixtures == [
        WorldCupFixture(
            home_team="Mexico",
            away_team="South Africa",
            group="GROUP A",
            kickoff_at="2026-06-11T19:00:00Z",
            headline="Mexico meets South Africa in Mexico City Stadium",
        )
    ]


def test_world_cup_today_summary_formats_fixtures(monkeypatch):
    monkeypatch.setattr(
        "football_live_agent.worldcup.fetch_fox_world_cup_fixtures",
        lambda: [
            WorldCupFixture("Mexico", "South Africa", "GROUP A", "2026-06-11T19:00:00Z"),
            WorldCupFixture("South Korea", "Czechia", "GROUP A", "2026-06-12T02:00:00Z"),
        ],
    )

    assert (
        world_cup_today_summary()
        == "World Cup today: Mexico vs South Africa, GROUP A, 19:00 UTC; South Korea vs Czechia, GROUP A, 02:00 UTC"
    )
