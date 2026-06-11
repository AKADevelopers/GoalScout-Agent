# GoalScout Agent For OpenCode

GoalScout Agent is a football intelligence CLI and portable agent skill. OpenCode can use it today by installing the CLI, reading the skill instructions, and running GoalScout before answering football questions.

## Install

Use one install command:

```bash
curl -fsSL https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.sh | sh
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.ps1 | iex"
```

```bash
npm install -g github:AKADevelopers/GoalScout-Agent
```

## Skill Instructions

Read and follow:

```text
https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/skills/goalscout-agent/SKILL.md
```

## How OpenCode Should Use GoalScout

For broad football questions, run:

```bash
goalscout-agent briefing
```

Use the briefing as source context for the answer. It includes saved onboarding preferences, SportScore football data, World Cup context when available, connected matches, interesting football, and an agent note.

For direct current results, run:

```bash
goalscout-agent once
```

For first setup, run:

```bash
goalscout-agent onboard
```

For always-on alerts, run:

```bash
goalscout-agent start-background
```

Do not invent scores, fixtures, alerts, providers, or watch links. If GoalScout output is missing a detail, say that it was not returned and run the most relevant GoalScout command again.

Detailed docs:

```text
https://github.com/AKADevelopers/GoalScout-Agent/blob/main/docs/agent-platforms.md
```
