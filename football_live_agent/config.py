from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    provider: str
    poll_seconds: int
    data_dir: Path
    api_football_key: str | None
    webhook_url: str | None
    delivery: str
    channel_command: str | None
    channel: str | None
    target: str | None
    console_enabled: bool
    watch_provider: str = "guide"
    sportmonks_key: str | None = None
    thesportsdb_key: str | None = None
    sportradar_key: str | None = None
    gracenote_key: str | None = None
    justwatch_token: str | None = None


def load_settings() -> Settings:
    data_dir = Path(os.environ.get("FOOTBALL_AGENT_DATA_DIR", ".football-live-agent"))
    poll_raw = os.environ.get("FOOTBALL_AGENT_POLL_SECONDS", "60")
    try:
        poll_seconds = max(10, int(poll_raw))
    except ValueError:
        poll_seconds = 20

    return Settings(
        provider=os.environ.get("FOOTBALL_AGENT_PROVIDER", "sportscore"),
        poll_seconds=poll_seconds,
        data_dir=data_dir,
        api_football_key=os.environ.get("API_FOOTBALL_KEY"),
        webhook_url=os.environ.get("FOOTBALL_AGENT_WEBHOOK_URL"),
        delivery=os.environ.get("FOOTBALL_AGENT_DELIVERY", "console").strip().casefold(),
        channel_command=os.environ.get("FOOTBALL_AGENT_CHANNEL_COMMAND"),
        channel=os.environ.get("FOOTBALL_AGENT_CHANNEL"),
        target=os.environ.get("FOOTBALL_AGENT_TARGET"),
        console_enabled=os.environ.get("FOOTBALL_AGENT_CONSOLE", "1").strip().casefold() not in {"0", "false", "no", "off"},
        watch_provider=os.environ.get("GOALSCOUT_WATCH_PROVIDER", os.environ.get("FOOTBALL_AGENT_WATCH_PROVIDER", "guide")),
        sportmonks_key=os.environ.get("SPORTMONKS_API_KEY") or os.environ.get("SPORTMONKS_API_TOKEN"),
        thesportsdb_key=os.environ.get("THESPORTSDB_API_KEY"),
        sportradar_key=os.environ.get("SPORTRADAR_API_KEY"),
        gracenote_key=os.environ.get("GRACENOTE_API_KEY"),
        justwatch_token=os.environ.get("JUSTWATCH_PARTNER_TOKEN"),
    )
