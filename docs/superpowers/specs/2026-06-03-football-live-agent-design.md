# Football Live Agent Design

## Goal

Build a portable football skill plus an always-running notification agent for OpenClaw, Hermes, and other Agent Skills-compatible clients. The system should collect user football preferences, answer football information requests, and send near-real-time notifications when followed matches produce important events.

## Scope

The first version will create:

- A portable `football-live-agent` skill with `SKILL.md` and UI metadata.
- A Python watcher service that polls a live football data provider and detects new match events.
- A first-run onboarding flow for favorite country, team, player, competitions, alert types, timezone, quiet hours, and notification channel.
- Provider adapters for SportScore first, API-Football second, plus documented adapter interfaces for Sportmonks and AnySport.
- Notification channels for console output and webhook delivery. Hermes/OpenClaw messaging delivery is handled by their gateway or webhook integration when configured.
- Notification channels for OpenClaw/Hermes command delivery when their local messaging CLIs are available.
- Local JSON state for preferences, known matches, already-notified events, and football memory.

## Non-Goals

- No betting, gambling, odds advice, or wagering automation.
- No scraped unofficial live-stream sources.
- No guarantee of sub-second alerts. API-Football-style polling is expected to be around 15-30 seconds depending on plan, network, and competition coverage. WebSocket providers can be added later for lower latency.
- No automatic installation of API keys or third-party accounts.

## Architecture

The project has two layers.

The skill layer is a portable Agent Skills folder. It tells an agent when to use the football workflow, how to ask onboarding questions, how to interpret configuration, and how to run or inspect the watcher.

The runtime layer is a Python command-line package. It owns provider calls, event normalization, deduplication, preference matching, scheduling decisions, and notification dispatch.

## Components

`skills/football-live-agent/SKILL.md`

Portable skill instructions for OpenClaw, Hermes, Codex, and compatible clients. It guides the agent through onboarding, live match checks, notification setup, troubleshooting, and safe handling of API keys.

`skills/football-live-agent/references/provider-notes.md`

Short reference for supported providers, expected latency, required API keys, and endpoint behavior.

`football_live_agent/config.py`

Loads and validates local settings from environment variables and JSON files.

`football_live_agent/onboarding.py`

Interactive first-run setup. Produces a preferences file without requiring the agent to remember private details in prompt text.

`football_live_agent/providers/base.py`

Defines normalized models for matches and events and the provider interface.

`football_live_agent/providers/sportscore.py`

Implements SportScore calls for no-key football matches and match-detail incidents. The watcher filters for live/in-play matches only. This is the default provider because it can run without a private API key.

`football_live_agent/providers/api_football.py`

Implements API-Football calls for live fixtures and fixture events. Use this when a user provides an API-Football key and wants that provider's coverage.

`football_live_agent/notifiers/base.py`

Defines the notification interface.

`football_live_agent/notifiers/console.py`

Prints notifications locally for testing and simple desktop use.

`football_live_agent/notifiers/webhook.py`

Posts notifications to a configured webhook URL for Hermes, OpenClaw, Discord, Telegram bridge, or any automation tool.

`football_live_agent/notifiers/command.py`

Sends notifications through a local OpenClaw/Hermes/custom command template. This bridges already-connected Telegram, WhatsApp, Discord, or other channels when the host platform exposes a local message-send command.

`football_live_agent/state.py`

Persists seen event IDs and last snapshots to avoid duplicate alerts across restarts.

`football_live_agent/memory.py`

Persists the last checked match, last scoreline, last minute, recent events, and recent notifications for resume-style answers.

`football_live_agent/service.py`

Starts, checks, and stops the watcher as a background process.

`football_live_agent/watcher.py`

Main polling loop. Fetches live matches, filters by preferences, detects important events, and sends notifications.

`football_live_agent/cli.py`

Provides commands: `onboard`, `watch`, `once`, `preferences`, and `test-notification`.

## Data Flow

1. User invokes the skill or starts the CLI.
2. If no preferences exist, onboarding asks for favorite country, team, player, competitions, alert types, timezone, quiet hours, and notification target.
3. Watcher loads preferences and provider credentials.
4. Watcher polls live fixtures and events at the configured interval.
5. Events are normalized into a common event shape.
6. Preferences filter events by team, country, player, competition, and alert type.
7. State storage suppresses duplicate alerts.
8. Memory storage records the current match state and event history.
9. Notifier sends a concise message with match, minute, event type, score, and involved player/team.

## Event Types

Version 1 supports:

- kickoff
- halftime
- fulltime
- goal
- penalty
- missed penalty
- red card
- yellow card
- substitution
- VAR goal cancelled
- VAR penalty confirmed
- lineup available
- match reminder

Unknown provider events are ignored unless configured as `all`.

## Configuration

Environment variables:

- `FOOTBALL_AGENT_PROVIDER=sportscore`
- `API_FOOTBALL_KEY=<secret, only for api-football>`
- `FOOTBALL_AGENT_POLL_SECONDS=60`
- `FOOTBALL_AGENT_DATA_DIR=<optional path>`
- `FOOTBALL_AGENT_WEBHOOK_URL=<optional URL>`
- `FOOTBALL_AGENT_DELIVERY=console|openclaw|hermes|webhook|command`
- `FOOTBALL_AGENT_CHANNEL=<optional channel>`
- `FOOTBALL_AGENT_TARGET=<optional chat target>`
- `FOOTBALL_AGENT_CHANNEL_COMMAND=<optional command template>`

Default local data directory:

`./.football-live-agent/`

Files:

- `preferences.json`
- `state.json`
- `memory.json`
- `watcher.pid`
- `watcher.log`

## Error Handling

Missing API key produces a clear setup message and exits non-zero only when the selected provider requires a key.

Provider request failures are retried on the next polling cycle with a clear log line. The watcher does not crash for a single network error.

Rate-limit responses back off by increasing the next polling delay.

Malformed provider records are skipped and counted in logs, rather than stopping the watcher.

Notification delivery failures are logged and retried only on future new events. Duplicate events are not resent unless state is manually cleared.

## Security

API keys must be read from environment variables, not stored in `SKILL.md`, prompt text, or committed files. The default SportScore provider does not require an API key.

Webhook URLs are treated as secrets and stored only in local preferences or environment variables.

The skill must not ask the agent to browse unofficial streams, bypass paywalls, or automate gambling decisions.

## Testing

Unit tests will cover:

- Preference matching.
- Event normalization.
- Deduplication.
- Console and webhook notifier behavior.
- CLI onboarding validation using temporary files.

Integration tests will use mocked provider responses. Live provider calls are optional and require an API key.

## Success Criteria

- A user can install or copy the skill into an OpenClaw/Hermes-compatible skills folder.
- Running onboarding creates valid local preferences.
- Running one polling cycle against mocked data emits a goal notification once.
- Running the same polling cycle again emits no duplicate notification.
- The watcher can run continuously and recover from temporary provider errors.
- The project documents how to connect webhook output into Hermes/OpenClaw messaging gateways.
