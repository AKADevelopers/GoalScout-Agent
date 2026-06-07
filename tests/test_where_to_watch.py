import json

from football_live_agent.models import Preferences
from football_live_agent.where_to_watch import (
    SportmonksTVProvider,
    TheSportsDBTVProvider,
    WatchOption,
    format_watch_summary,
    legal_platform_categories,
)


def test_legal_platform_categories_include_famous_services():
    categories = legal_platform_categories()

    assert "global_streaming" in categories
    assert "DAZN" in categories["global_streaming"]
    assert "Peacock" in categories["us"]
    assert "Sky Sports" in categories["uk_ireland"]


def test_format_watch_summary_highlights_user_platform_match():
    preferences = Preferences(
        favorite_country="Argentina",
        watch_country="United States",
        watch_platforms=["Peacock", "Fubo"],
    )
    options = [
        WatchOption(provider="sportmonks", name="Peacock", country="United States", url="https://www.peacocktv.com"),
        WatchOption(provider="sportmonks", name="Telemundo", country="United States"),
    ]

    summary = format_watch_summary(preferences, options, provider_name="sportmonks", fixture_id="123")

    assert "Official options found by sportmonks for fixture 123:" in summary
    assert "[you have this]" in summary
    assert "Peacock" in summary
    assert "Telemundo" in summary


def test_format_watch_summary_without_fixture_gives_simple_user_guide():
    preferences = Preferences(
        favorite_country="",
        watch_country="Pakistan",
        watch_platforms=["Tapmad", "Prime Video"],
        watch_provider="guide",
    )

    summary = format_watch_summary(preferences, [], provider_name="guide", fixture_id=None)

    assert "Where to watch setup" in summary
    assert "Pakistan" in summary
    assert "Tapmad, Prime Video" in summary
    assert "Sportmonks" in summary


def test_sportmonks_tv_provider_normalizes_fixture_response(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "data": [
                        {
                            "name": "beIN SPORTS CONNECT",
                            "url": "https://connect.beinsports.com",
                            "image_path": "https://cdn.example/bein.png",
                            "type": "tv",
                        }
                    ]
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    options = SportmonksTVProvider("secret").options_for_fixture("fixture-1")

    assert "tv-stations/fixtures/fixture-1" in captured["url"]
    assert "api_token=secret" in captured["url"]
    assert captured["timeout"] == 12
    assert options == [
        WatchOption(
            provider="sportmonks",
            name="beIN SPORTS CONNECT",
            url="https://connect.beinsports.com",
            logo_url="https://cdn.example/bein.png",
            kind="tv",
        )
    ]


def test_thesportsdb_provider_normalizes_tv_event_response(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps(
                {
                    "tvevent": [
                        {
                            "strChannel": "BT Sport ESPN",
                            "strCountry": "Ireland",
                            "strLogo": "https://cdn.example/bt.png",
                        }
                    ]
                }
            ).encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    options = TheSportsDBTVProvider("abc123").options_for_fixture("584911")

    assert "lookuptv.php?id=584911" in captured["url"]
    assert "/abc123/" in captured["url"]
    assert captured["timeout"] == 12
    assert options == [
        WatchOption(
            provider="thesportsdb",
            name="BT Sport ESPN",
            country="Ireland",
            logo_url="https://cdn.example/bt.png",
            kind="tv",
        )
    ]
