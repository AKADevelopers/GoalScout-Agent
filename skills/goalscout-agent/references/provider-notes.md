# Provider Notes

## SportScore

Default provider. It uses `https://sportscore.com/api/widget/` and does not require an API key. Configure `FOOTBALL_AGENT_PROVIDER=sportscore`, or leave the provider unset.

The watcher filters for live/in-play football matches, then uses match detail incidents to normalize goals, cards, and substitutions. SportScore asks projects using its free data to provide visible attribution when the data is shown in a user-facing page. Console-only local use does not need any embedded UI badge.

SportScore responses are cached at the edge, so keep polling at 60 seconds or slower for normal use. Lower values can work, but do not create more real-time accuracy than the upstream cache allows.

SportScore's public OpenAPI spec does not include a general football news-headline endpoint. For a no-live status update, use `/api/widget/matches/` to summarize recent results and upcoming fixtures.

## API-Football

Optional provider. Configure `API_FOOTBALL_KEY` and set `FOOTBALL_AGENT_PROVIDER=api-football`. The watcher calls live fixtures and fixture events, then normalizes goals, cards, substitutions, penalties, and VAR events.

Expected latency is near-real-time, commonly around one polling interval plus provider update delay. Start with `FOOTBALL_AGENT_POLL_SECONDS=20`.

## Sportmonks

Sportmonks can be added through the provider interface in `football_live_agent.providers.base.FootballProvider`. Use it when the user already has Sportmonks credentials or coverage requirements.

## AnySport

AnySport can be added later for WebSocket push events. Prefer it when the user needs lower latency than polling and has access to its football event feed.

## OpenClaw And Hermes

OpenClaw can use the skill folder directly as a local skill. Hermes can use the same skill instructions and route notifications through its messaging or gateway setup.

For direct channel delivery, the watcher can call a local command:

```powershell
$env:FOOTBALL_AGENT_DELIVERY = "openclaw"
$env:FOOTBALL_AGENT_CHANNEL = "telegram"
$env:FOOTBALL_AGENT_TARGET = "@your-chat-or-group"
python -m football_live_agent.cli start-background
```

Use `FOOTBALL_AGENT_DELIVERY=hermes` for Hermes installs that expose a compatible `hermes message send` command. If the local install uses different arguments, set `FOOTBALL_AGENT_CHANNEL_COMMAND` with `{channel}`, `{target}`, and `{message}` placeholders.

Run `python -m football_live_agent.cli health-check` after configuring delivery. It sends a non-football status message through the same notification path, which proves the channel is connected even when no live match event is happening.
