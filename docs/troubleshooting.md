# Troubleshooting

## Start here

```bash
goalscout-agent doctor
```

If issues are reported:

```bash
goalscout-agent repair
goalscout-agent doctor
```

## Validate a source checkout

```bash
python scripts/validate_repo.py
python -m pytest -q
```

## No notification arrived

1. Run `goalscout-agent test-notification`.
2. Confirm `FOOTBALL_AGENT_DELIVERY`.
3. For Hermes/OpenClaw-style delivery, confirm `FOOTBALL_AGENT_CHANNEL` and `FOOTBALL_AGENT_TARGET`.
4. For webhook delivery, confirm `FOOTBALL_AGENT_WEBHOOK_URL`.
5. For custom command delivery, confirm `FOOTBALL_AGENT_CHANNEL_COMMAND`.
6. Run `goalscout-agent once` to verify provider data and matching preferences.

## Provider unavailable

SportScore is the default no-key provider, but public endpoints can be delayed or unavailable. GoalScout logs provider errors and backs off rather than crashing. BYOK providers require valid credentials in environment variables.

## Duplicate alerts

GoalScout stores seen event IDs in local state. For testing, use a temporary `FOOTBALL_AGENT_DATA_DIR` rather than deleting production state.

## Where-to-watch does not show a platform

Run:

```bash
goalscout-agent where-to-watch
```

Then confirm your watch country and saved platforms. Official broadcast availability depends on provider coverage and fixture IDs.
