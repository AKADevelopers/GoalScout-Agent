# Architecture

GoalScout Agent has two layers: the football runtime and the agent integration package.

## Runtime layer

The runtime layer is a Python command-line package.

- `football_live_agent/cli.py` exposes commands such as `onboard`, `doctor`, `once`, `watch`, and `where-to-watch`.
- `football_live_agent/config.py` loads environment settings.
- `football_live_agent/onboarding.py` saves user preferences locally.
- `football_live_agent/preferences.py` validates and repairs saved preferences.
- `football_live_agent/watcher.py` polls providers, suppresses duplicate alerts, adapts polling, and sends kickoff reminders.
- `football_live_agent/providers/` contains live-score and where-to-watch adapters.
- `football_live_agent/notifiers/` delivers messages to console, webhook, Hermes/OpenClaw-style command channels, or custom commands.
- `football_live_agent/state.py` and `football_live_agent/memory.py` store local runtime state and useful match context.

## Agent integration layer

The integration layer makes the runtime easy to discover and use from agent tools.

- `.codex-plugin/plugin.json` provides plugin metadata.
- `skills/goalscout-agent/SKILL.md` describes when agents should use GoalScout and which CLI commands to run.
- `skills/goalscout-agent/agents/openai.yaml` provides interface metadata.
- `assets/` provides icons for plugin and skill UIs.

## Data flow

1. The user runs `goalscout-agent onboard` or an agent invokes it.
2. Preferences are stored in `.football-live-agent/` or `FOOTBALL_AGENT_DATA_DIR`.
3. `doctor` and `repair` validate saved preferences.
4. The watcher polls the selected provider.
5. Provider records are normalized into `Match` and `Event` models.
6. Preferences decide whether an event should notify.
7. State suppresses duplicates.
8. Memory records match context.
9. Notifiers deliver the alert.

## Safety boundaries

- API keys and webhook URLs belong in environment variables.
- Runtime data stays local and is not committed.
- Where-to-watch guidance only points users to official/legal platforms.
- Enterprise provider placeholders are explicit BYOK setup-only integrations until real credentials are configured.
