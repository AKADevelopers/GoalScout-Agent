---
name: goalscout-agent
description: Use when the user wants GoalScout Agent help for football or soccer match information, favorite-team setup, live score monitoring, goal alerts, match reminders, player/team tracking, World Cup or league updates, or configuring OpenClaw/Hermes football notifications.
---

# GoalScout Agent

Use this skill to help users configure and operate GoalScout Agent, a football live notification agent.

## Workflow

1. Check whether local preferences exist in `.football-live-agent/preferences.json`.
2. If preferences are missing, run onboarding with `goalscout-agent onboard` or `python -m football_live_agent.cli onboard`.
3. Ask for or confirm the user's favorite country, favorite teams, favorite players, competitions, alert types, timezone, delivery mode, channel, and target chat.
4. For free live alerts, use the default SportScore provider and run `goalscout-agent watch`.
5. For a single check, run `goalscout-agent once`. If no matching football event is live, it sends a health-check message plus a SportScore football update using recent results and upcoming fixtures.
6. For webhook delivery to Hermes, OpenClaw, Discord, Telegram, or an automation bridge, set `FOOTBALL_AGENT_WEBHOOK_URL`.
7. For API-Football instead of SportScore, set `FOOTBALL_AGENT_PROVIDER=api-football` and provide `API_FOOTBALL_KEY`.
8. For always-on alerts after setup, run `goalscout-agent start-background`.

## User Preferences

Collect these fields during setup:

- Favorite country.
- Favorite club or national teams.
- Favorite players.
- Competitions to follow.
- Alert types: `goal`, `penalty`, `missed_penalty`, `red_card`, `yellow_card`, `kickoff`, `halftime`, `fulltime`, `substitution`, `var_goal_cancelled`, `var_penalty_confirmed`, or `all`.
- Timezone.
- Optional quiet hours.
- Delivery mode: `console`, `openclaw`, `hermes`, `webhook`, or `command`.
- Messaging channel, for example `telegram` or `whatsapp`.
- Message target, chat ID, username, or group name.
- Optional webhook URL.
- Optional custom channel command.

## Answering Football Requests

For schedule, score, lineup, and event questions, use the watcher when local provider configuration exists. The default SportScore provider needs no API key. If the user selects API-Football, explain that it requires a provider API key and help the user complete setup.

Prefer concise updates:

```text
55' GOAL Argentina 2-1 Brazil - Messi
```

Include the source provider and observed update time when precision matters.

## Runtime Commands

Use these commands from the project root:

```powershell
goalscout-agent onboard
goalscout-agent preferences
goalscout-agent memory
goalscout-agent health-check
goalscout-agent test-notification
goalscout-agent once
goalscout-agent watch
goalscout-agent start-background
goalscout-agent status
goalscout-agent stop
```

## Environment

Use environment variables for secrets and runtime settings:

```powershell
$env:FOOTBALL_AGENT_PROVIDER = "sportscore"
$env:FOOTBALL_AGENT_POLL_SECONDS = "60"
$env:FOOTBALL_AGENT_WEBHOOK_URL = "<optional-webhook-url>"
```

For OpenClaw channel delivery:

```powershell
$env:FOOTBALL_AGENT_DELIVERY = "openclaw"
$env:FOOTBALL_AGENT_CHANNEL = "telegram"
$env:FOOTBALL_AGENT_TARGET = "@your-chat-or-group"
```

For Hermes channel delivery:

```powershell
$env:FOOTBALL_AGENT_DELIVERY = "hermes"
$env:FOOTBALL_AGENT_CHANNEL = "telegram"
$env:FOOTBALL_AGENT_TARGET = "@your-chat-or-group"
```

For custom local installs, set a command template:

```powershell
$env:FOOTBALL_AGENT_CHANNEL_COMMAND = "openclaw message send --channel {channel} --target {target} --message {message}"
```

For API-Football:

```powershell
$env:FOOTBALL_AGENT_PROVIDER = "api-football"
$env:API_FOOTBALL_KEY = "<provider-api-key>"
```

## Safety

Do not store API keys in prompt text or skill files. Use environment variables.

Do not provide betting instructions, odds advice, illegal streams, or paywall bypass steps.

## Provider Notes

Read `references/provider-notes.md` when configuring live data providers or explaining latency tradeoffs.

## Memory

The runtime writes memory into `.football-live-agent/memory.json`.

Use `goalscout-agent memory` to answer questions such as "where were we last time?" or "what happened last minute?".

The memory tracks the last checked match, scoreline, elapsed minute, recent events, and recent sent notifications.

## No-Live Update

SportScore's public API exposes live/recent matches, match details, fixtures, standings, top scorers, player data, and tracker data. It does not currently expose a general football news-headline endpoint in the public OpenAPI spec. When there is no live football alert, use recent results and upcoming fixtures as the latest football update, then tell the user the watcher will notify them when matches start or goals happen.
