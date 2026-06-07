from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


class WatchProviderError(Exception):
    pass


@dataclass(frozen=True)
class WatchOption:
    provider: str
    name: str
    country: str | None = None
    url: str | None = None
    logo_url: str | None = None
    kind: str = "streaming"


def legal_platform_categories() -> dict[str, list[str]]:
    return {
        "global_streaming": [
            "DAZN",
            "Prime Video",
            "Apple TV",
            "MLS Season Pass",
            "FIFA+",
            "YouTube",
        ],
        "us": [
            "ESPN",
            "ESPN+",
            "FOX Sports",
            "Fubo",
            "Peacock",
            "NBC Sports",
            "Paramount+",
            "CBS Sports Golazo",
            "Telemundo",
            "Univision",
            "ViX",
            "YouTube TV",
            "Sling",
            "Hulu Live TV",
        ],
        "uk_ireland": [
            "Sky Sports",
            "NOW",
            "TNT Sports",
            "discovery+",
            "BBC iPlayer",
            "ITV",
            "Premier Sports",
        ],
        "europe_middle_east": [
            "beIN Sports",
            "beIN SPORTS CONNECT",
            "Canal+",
            "Movistar Plus+",
            "Viaplay",
            "Ziggo Sport",
            "Star+",
        ],
        "south_asia": [
            "SonyLIV",
            "JioCinema",
            "FanCode",
            "Tapmad",
            "Tamasha",
            "PTV Sports",
        ],
        "enterprise_lookup": [
            "Sportmonks TV Stations",
            "TheSportsDB TV Broadcasts",
            "Sportradar tv_channels",
            "Gracenote On API",
            "JustWatch Partner API",
        ],
    }


def known_watch_providers() -> dict[str, str]:
    return {
        "guide": "Built-in legal platform guide and user subscription matching. No API key.",
        "sportmonks": "Sportmonks TV Stations. Set SPORTMONKS_API_KEY.",
        "thesportsdb": "TheSportsDB Event TV Broadcasts. Set THESPORTSDB_API_KEY.",
        "sportradar": "Enterprise Sportradar fixture tv_channels. BYOK placeholder.",
        "gracenote": "Enterprise Gracenote On API live sports where-to-watch data. BYOK placeholder.",
        "justwatch": "JustWatch Partner API / Sports Widget. Set JUSTWATCH_PARTNER_TOKEN when contracted.",
    }


def normalize_provider(value: str | None) -> str:
    normalized = (value or "guide").strip().casefold().replace("_", "-")
    aliases = {
        "built-in": "guide",
        "builtin": "guide",
        "simple": "guide",
        "sportmonks-tv": "sportmonks",
        "the-sports-db": "thesportsdb",
        "sportsdb": "thesportsdb",
        "the-sportsdb": "thesportsdb",
        "just-watch": "justwatch",
    }
    return aliases.get(normalized, normalized)


def format_watch_summary(
    preferences: Any,
    options: list[WatchOption],
    *,
    provider_name: str,
    fixture_id: str | None,
) -> str:
    watch_country = getattr(preferences, "watch_country", "") or "not set"
    user_platforms = [platform for platform in getattr(preferences, "watch_platforms", []) if platform.strip()]

    if not fixture_id and not options:
        platforms = ", ".join(user_platforms) if user_platforms else "none saved yet"
        provider_help = "; ".join(f"{name}: {description}" for name, description in known_watch_providers().items())
        return (
            "Where to watch setup\n"
            f"Country: {watch_country}\n"
            f"Your platforms: {platforms}\n"
            "Use `goalscout-agent where-to-watch <provider-fixture-id> --provider sportmonks` "
            "or `--provider thesportsdb` when you have a fixture ID from that provider.\n"
            f"Provider categories: {provider_help}"
        )

    if not options:
        return (
            f"No official watch options found by {provider_name}"
            + (f" for fixture {fixture_id}." if fixture_id else ".")
            + " Check your provider key, fixture ID, country, and subscription plan."
        )

    platform_keys = {_clean_platform(platform) for platform in user_platforms}
    lines = [f"Official options found by {provider_name}" + (f" for fixture {fixture_id}:" if fixture_id else ":")]
    for option in options:
        suffix = " [you have this]" if _clean_platform(option.name) in platform_keys else ""
        country = f" ({option.country})" if option.country else ""
        url = f" - {option.url}" if option.url else ""
        lines.append(f"- {option.name}{country}{suffix}{url}")
    return "\n".join(lines)


def _clean_platform(value: str) -> str:
    return "".join(char for char in value.casefold() if char.isalnum())


class GuideWatchProvider:
    provider_name = "guide"

    def options_for_fixture(self, fixture_id: str) -> list[WatchOption]:
        return []


class SportmonksTVProvider:
    provider_name = "sportmonks"

    def __init__(self, api_key: str, base_url: str = "https://api.sportmonks.com/v3/football", timeout: int = 12) -> None:
        if not api_key:
            raise WatchProviderError("SPORTMONKS_API_KEY is required for Sportmonks where-to-watch lookup.")
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def options_for_fixture(self, fixture_id: str) -> list[WatchOption]:
        payload = self._get(f"/tv-stations/fixtures/{urllib.parse.quote(str(fixture_id))}", {"api_token": self.api_key})
        return [
            WatchOption(
                provider=self.provider_name,
                name=str(item.get("name") or "").strip(),
                url=_optional_str(item.get("url")),
                logo_url=_optional_str(item.get("image_path")),
                kind=str(item.get("type") or "tv"),
            )
            for item in payload.get("data", [])
            if str(item.get("name") or "").strip()
        ]

    def _get(self, path: str, params: dict[str, str]) -> dict[str, Any]:
        url = f"{self.base_url}{path}?{urllib.parse.urlencode(params)}"
        request = urllib.request.Request(url, headers={"User-Agent": "goalscout-agent/0.1"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode("utf-8"))


class TheSportsDBTVProvider:
    provider_name = "thesportsdb"

    def __init__(self, api_key: str, base_url: str = "https://www.thesportsdb.com/api/v1/json", timeout: int = 12) -> None:
        if not api_key:
            raise WatchProviderError("THESPORTSDB_API_KEY is required for TheSportsDB where-to-watch lookup.")
        self.api_key = api_key.strip("/")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def options_for_fixture(self, fixture_id: str) -> list[WatchOption]:
        url = f"{self.base_url}/{urllib.parse.quote(self.api_key)}/lookuptv.php?id={urllib.parse.quote(str(fixture_id))}"
        request = urllib.request.Request(url, headers={"User-Agent": "goalscout-agent/0.1"})
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return [
            WatchOption(
                provider=self.provider_name,
                name=str(item.get("strChannel") or "").strip(),
                country=_optional_str(item.get("strCountry")),
                logo_url=_optional_str(item.get("strLogo")),
                kind="tv",
            )
            for item in payload.get("tvevent") or []
            if str(item.get("strChannel") or "").strip()
        ]


class SetupOnlyWatchProvider:
    def __init__(self, provider_name: str, setup_message: str) -> None:
        self.provider_name = provider_name
        self.setup_message = setup_message

    def options_for_fixture(self, fixture_id: str) -> list[WatchOption]:
        raise WatchProviderError(self.setup_message)


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
