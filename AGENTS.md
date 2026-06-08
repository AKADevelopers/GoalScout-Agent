# Agent Notes

This repository contains a portable football notification agent and a packaged skill.

## Important Commands

```powershell
python scripts/validate_repo.py
python -m pytest -q
python -m football_live_agent.cli doctor
python -m football_live_agent.cli repair
python -m football_live_agent.cli once
python -m football_live_agent.cli test-notification
python -m football_live_agent.cli start-background
python -m football_live_agent.cli stop
```

## Runtime Data

Local runtime state lives in `.football-live-agent/` and must not be committed. It can include preferences, memory, provider cache, logs, and watcher PID files.

## Provider Notes

SportScore is the default no-key provider. API-Football is optional and requires `API_FOOTBALL_KEY`.

## Packaging

Keep `.codex-plugin/plugin.json`, `skills/goalscout-agent/agents/openai.yaml`, and the icon assets in sync. Run tests after changing packaging metadata because `tests/test_packaging.py` checks the visible plugin and skill presentation.
