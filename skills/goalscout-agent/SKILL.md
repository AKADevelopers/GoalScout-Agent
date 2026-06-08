---
name: goalscout-agent
description: Use when the user wants GoalScout Agent help for football or soccer match information, favorite-team setup, live score monitoring, goal alerts, match reminders, player/team tracking, World Cup or league updates, or configuring Codex, Claude Code, OpenCode, OpenClaw, or Hermes football notifications.
---

# GoalScout Agent

Use this skill to help users configure and operate GoalScout Agent, a football live notification agent for terminal users and agent CLIs.

## Workflow

1. Check whether local preferences exist in `.football-live-agent/preferences.json`.
2. If preferences are missing, run onboarding with `goalscout-agent onboard` or `python -m football_live_agent.cli onboard`.
3. If preferences exist but alerts or delivery are broken, run `goalscout-agent doctor` and then `goalscout-agent repair` to normalize delivery, alert types, where-to-watch provider, and missing command fields.
4. Ask for or confirm the user's favorite country, favorite teams, favorite players, competitions, alert types, timezone, delivery mode, channel, target chat, watch country, watching platforms, and where-to-watch provider.
5. For broad football questions, run `goalscout-agent briefing` first. Use its saved-preference summary, connected matches, interesting football, and agent note to answer naturally.
6. For free live alerts, use the default SportScore provider and run `goalscout-agent watch`.
7. For a single check, run `goalscout-agent once`. If no matching football event is live, it sends a football status update using recent results and upcoming fixtures.
8. For webhook delivery to Hermes, OpenClaw, Discord, Telegram, or an automation bridge, set `FOOTBALL_AGENT_WEBHOOK_URL`.
9. For API-Football instead of SportScore, set `FOOTBALL_AGENT_PROVIDER=api-football` and provide `API_FOOTBALL_KEY`.
10. For always-on alerts after setup, run `goalscout-agent start-background`. The watcher now uses faster polling around active/favorite matches and can send kickoff reminders for followed upcoming fixtures.
11. For legal TV/streaming guidance, run `goalscout-agent where-to-watch`, `goalscout-agent where-to-watch --team "Team Name" --date YYYY-MM-DD`, or `goalscout-agent where-to-watch <provider-fixture-id> --provider sportmonks`.

## Install And Agent CLI Use

Install the CLI with npm when a Node-based workflow is preferred:

```bash
npm install -g github:AKADevelopers/GoalScout-Agent
```

Install with pipx when a Python CLI workflow is preferred:

```bash
pipx install git+https://github.com/AKADevelopers/GoalScout-Agent.git
```

Codex, Claude Code, OpenCode, OpenClaw, Hermes, Cursor, Copilot-style agents, and Raspberry Pi/Linux hosts can all use the same `goalscout-agent` commands. If the agent client supports skills, point it at `skills/goalscout-agent/SKILL.md`; otherwise, ask it to run the CLI commands directly.

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
- Watch country.
- Watching platforms the user has, such as DAZN, ESPN+, Peacock, Paramount+, Apple TV, Sky Sports, beIN Sports, Fubo, Prime Video, FIFA+, Tapmad, or SonyLIV.
- Where-to-watch provider: `guide`, `sportmonks`, `thesportsdb`, `sportradar`, `gracenote`, or `justwatch`.

## Answering Football Requests

For schedule, score, lineup, and event questions, use the watcher when local provider configuration exists. The default SportScore provider needs no API key. If the user selects API-Football, explain that it requires a provider API key and help the user complete setup.

For open-ended questions such as "what is happening today?", "what matches should I watch?", or "what is interesting for my favorites?", run `goalscout-agent briefing`. Use the briefing to explain the user's saved onboarding setup, relevant matches, friendlies/warmups, and next actions. Do not answer as if the user's favorites are unknown when the briefing includes them.

Prefer concise updates:

```text
55' GOAL Argentina 2-1 Brazil - Messi
```

Include the source provider and observed update time when precision matters.

## Runtime Commands

Use these commands from the project root:

```powershell
goalscout-agent onboard
goalscout-agent doctor
goalscout-agent repair
goalscout-agent preferences
goalscout-agent briefing
goalscout-agent memory
goalscout-agent health-check
goalscout-agent test-notification
goalscout-agent where-to-watch
goalscout-agent where-to-watch <provider-fixture-id> --provider sportmonks
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

Read `references/watch-providers.md` when configuring legal where-to-watch lookup, official TV/streaming provider categories, or BYOK broadcast-listing providers.

## Where To Watch

GoalScout Agent can store the user's legal watching platforms and compare official broadcast listings against them. It must not provide illegal streams, paywall bypasses, account sharing, stream ripping, or unofficial rebroadcast links.

Supported where-to-watch modes:

- `guide`: no API key, shows saved country/platforms and provider categories.
- `sportmonks`: requires `SPORTMONKS_API_KEY`, uses Sportmonks TV Stations by fixture ID.
- `thesportsdb`: requires `THESPORTSDB_API_KEY`, uses TheSportsDB event TV broadcasts by event ID.
- `sportradar`, `gracenote`, `justwatch`: enterprise/partner BYOK placeholders.

## Memory

The runtime writes memory into `.football-live-agent/memory.json`.

Use `goalscout-agent memory` to answer questions such as "where were we last time?" or "what happened last minute?".

The memory tracks the last checked match, scoreline, elapsed minute, recent events, and recent sent notifications.

## No-Live Update

SportScore's public API exposes live/recent matches, match details, fixtures, standings, top scorers, player data, and tracker data. It does not currently expose a general football news-headline endpoint in the public OpenAPI spec. When there is no live football alert, use recent results and upcoming fixtures as the latest football update, then tell the user the watcher will notify them when matches start or goals happen.
