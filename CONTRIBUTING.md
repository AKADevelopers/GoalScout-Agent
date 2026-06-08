# Contributing

Thank you for improving GoalScout Agent.

## Local setup

```bash
git clone https://github.com/AKADevelopers/GoalScout-Agent.git
cd GoalScout-Agent
python -m pip install -e ".[dev]"
```

## Before committing

```bash
python scripts/validate_repo.py
python -m pytest -q
```

## Development rules

- Keep provider credentials out of git.
- Add or update tests for behavior changes.
- Keep CLI examples copy-pasteable.
- Prefer explicit provider limitations over vague claims.
- Where-to-watch features must point only to official/legal platforms.
- Update docs when CLI behavior changes.
