# Installation

GoalScout Agent is a professional football alert agent with a Python CLI and portable agent skill metadata.

## One-line CLI install

```bash
python -m pip install "goalscout-agent @ git+https://github.com/AKADevelopers/GoalScout-Agent.git"
```

Verify the install:

```bash
goalscout-agent --help
goalscout-agent doctor
```

## Local development install

```bash
git clone https://github.com/AKADevelopers/GoalScout-Agent.git
cd GoalScout-Agent
python -m pip install -e ".[dev]"
python scripts/validate_repo.py
python -m pytest -q
```

## First run

```bash
goalscout-agent onboard
goalscout-agent once
```

## Always-on watcher

```bash
goalscout-agent start-background
goalscout-agent status
goalscout-agent stop
```

## Agent-tool usage

GoalScout ships these professional agent integration files:

- `.codex-plugin/plugin.json` for Codex-style plugin metadata.
- `skills/goalscout-agent/SKILL.md` for portable agent behavior.
- `skills/goalscout-agent/agents/openai.yaml` for UI metadata.
- `assets/` and `skills/goalscout-agent/assets/` for icons.

Use the same CLI install above for Codex, Hermes, OpenClaw, OpenCode, Cursor, or Copilot workflows, then point the agent tool at `skills/goalscout-agent/SKILL.md`.
