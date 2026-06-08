# Installation

GoalScout Agent is a professional football alert agent with a Python CLI, an npm-compatible command wrapper, and portable agent skill metadata.

## One-line npm CLI install

Install from GitHub with npm:

```bash
npm install -g github:AKADevelopers/GoalScout-Agent
```

Verify the npm-installed command:

```bash
goalscout-agent --help
goalscout-agent doctor
```

This npm wrapper requires Python 3.11 or newer on the machine. It runs the existing Python CLI from the installed package source.

After a registry release, the shorter npm command will be:

```bash
npm install -g goalscout-agent
```

## Python CLI install

Use pipx for an isolated Python CLI install:

```bash
pipx install git+https://github.com/AKADevelopers/GoalScout-Agent.git
```

Or install with pip:

```bash
python -m pip install "goalscout-agent @ git+https://github.com/AKADevelopers/GoalScout-Agent.git"
```

Verify the Python install:

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
- `package.json` and `bin/goalscout-agent.js` for npm-style CLI installation.
- `skills/goalscout-agent/SKILL.md` for portable agent behavior.
- `skills/goalscout-agent/agents/openai.yaml` for UI metadata.
- `assets/` and `skills/goalscout-agent/assets/` for icons.

Use the same CLI install above for Codex, Claude Code, OpenCode, OpenClaw, Hermes, Cursor, Copilot-style workflows, or Raspberry Pi/Linux hosts, then point the agent tool at:

```text
skills/goalscout-agent/SKILL.md
```

Recommended agent CLI flow:

```bash
goalscout-agent doctor
goalscout-agent repair
goalscout-agent briefing
goalscout-agent once
goalscout-agent where-to-watch
```

If an agent client exposes its own skill import command, import or reference the `skills/goalscout-agent` folder. If it only runs shell commands, ask it to run the `goalscout-agent` commands above.
