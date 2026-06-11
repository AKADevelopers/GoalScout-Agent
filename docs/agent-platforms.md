# Agent Platform Setup

GoalScout Agent is a football CLI plus a portable agent skill. Agent clients can use it by installing the `goalscout-agent` command, reading the skill instructions, and passing fresh football output into the LLM before it answers.

Raw skill URL:

```text
https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/skills/goalscout-agent/SKILL.md
```

OpenCode install URL:

```text
https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/.opencode/INSTALL.md
```

## How Skills Work

### Codex

Codex treats skills as reusable workflows packaged as a folder with `SKILL.md` plus optional `scripts/`, `references/`, `assets/`, and `agents/openai.yaml`. It loads the skill name, description, and path first, then reads the full instructions only when the skill is relevant. You can invoke a skill directly with `$goalscout-agent`, or let Codex choose it automatically from the description.

That loading pattern is progressive disclosure: Codex starts with the small summary and only expands into the full skill when the task matches.

For GoalScout, that means the portable repo skill at `skills/goalscout-agent/SKILL.md` is the source of truth. Keep the description sharp so Codex can match football questions correctly.

### Claude Code

Claude Code also uses `SKILL.md`, but it resolves skills from actual skill directories. Personal skills live at `~/.claude/skills/<skill-name>/SKILL.md`, project skills live at `.claude/skills/<skill-name>/SKILL.md`, and plugin skills live inside a plugin's `skills/` directory. The directory name becomes the command name, and Claude can load skills automatically when the description matches the task. Claude Code also discovers project skills from parent and nested directories.

For GoalScout, a Claude user can copy the portable skill into `.claude/skills/goalscout-agent/SKILL.md` or point Claude at the repo copy if their workflow supports external skill references.

### Cursor

Cursor's Agent Skills are `SKILL.md`-based workflows that the agent can discover and apply when the task matches. Cursor says skills are available in the editor and CLI, and they are better than always-on rules for procedural, task-specific guidance. Cursor also exposes skills through the slash command menu.

For GoalScout, the portable repo skill is the right source file. If you later publish a native Cursor plugin, Cursor's plugin spec uses `.cursor-plugin/marketplace.json` at the repo root, per-plugin `.cursor-plugin/plugin.json`, and a `skills/` folder inside each plugin.

## Universal Install

Use any one of these install paths:

```bash
curl -fsSL https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.sh | sh
```

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.ps1 | iex"
```

```bash
npm install -g github:AKADevelopers/GoalScout-Agent
```

```bash
pipx install git+https://github.com/AKADevelopers/GoalScout-Agent.git
```

Verify the command:

```bash
goalscout-agent doctor
goalscout-agent briefing
goalscout-agent once
```

## Command Contract For Agents

Use these commands from OpenCode, Codex, Claude Code, Pi Coding Agent, OpenClaw, Hermes, Cursor, GitHub Copilot CLI, or any other coding agent that can run shell commands.

- `goalscout-agent briefing` is the best LLM context command. It includes saved onboarding preferences, SportScore football data, World Cup context when available, relevant matches, interesting football, and a short agent note.
- `goalscout-agent once` is the best direct results command. It should return current football results, major tournament context, recent results, and upcoming fixtures without saying football has not started when useful football context exists.
- `goalscout-agent onboard` collects favorite country, teams, players, competitions, alert types, timezone, delivery mode, and legal watch platforms.
- `goalscout-agent where-to-watch` gives legal TV or streaming guidance only.
- `goalscout-agent start-background` starts always-on alerts after setup.

Agents should treat CLI output as source context, answer in natural language, and not invent scores, fixtures, providers, or watch links that were not returned by GoalScout or another verified source.

## OpenCode

OpenCode can run the GoalScout CLI today. Tell OpenCode:

```text
Fetch and follow instructions from https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/.opencode/INSTALL.md

Before answering broad football questions, run:
goalscout-agent briefing

For direct current football results, run:
goalscout-agent once
```

GoalScout is not currently published as a native OpenCode npm plugin. The working path is the CLI plus the portable skill instructions above.

## Codex, Claude Code, And Pi Coding Agent

Install GoalScout, then point the agent at the portable skill:

```text
https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/skills/goalscout-agent/SKILL.md
```

Tell the coding agent:

```text
Use GoalScout Agent for football questions. Run `goalscout-agent briefing` before open-ended football answers, run `goalscout-agent once` for direct results, and use the output as source context for the final answer.
```

## OpenClaw And Hermes

OpenClaw and Hermes can use the same skill and CLI command flow. Use `briefing` when the platform needs football context for the LLM, and use channel delivery when the platform exposes messaging.

OpenClaw delivery:

```bash
export FOOTBALL_AGENT_DELIVERY=openclaw
export FOOTBALL_AGENT_CHANNEL=telegram
export FOOTBALL_AGENT_TARGET=@your-chat-or-group
goalscout-agent test-notification
```

Hermes delivery:

```bash
export FOOTBALL_AGENT_DELIVERY=hermes
export FOOTBALL_AGENT_CHANNEL=telegram
export FOOTBALL_AGENT_TARGET=@your-chat-or-group
goalscout-agent test-notification
```

If the local platform command is different, use a command template:

```bash
export FOOTBALL_AGENT_CHANNEL_COMMAND='openclaw message send --channel {channel} --target {target} --message {message}'
```

The important LLM behavior is the same everywhere: run `goalscout-agent briefing`, share that context with the model, and answer from that fresh football data.

## Cursor

GoalScout is not currently published in the Cursor plugin marketplace. Use the working CLI and skill path now:

```text
Install GoalScout, then use this skill:
https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/skills/goalscout-agent/SKILL.md

Run `goalscout-agent briefing` before answering football questions.
Run `goalscout-agent once` for direct current results.
```

After GoalScout is published as a Cursor marketplace plugin, this section can add the marketplace install command. Until then, do not document a `/add-plugin goalscout-agent` command as if it already works.

## GitHub Copilot CLI

GoalScout is not currently published in a GitHub Copilot CLI marketplace. Use the working CLI and raw skill path now:

```text
Use GoalScout Agent instructions from:
https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/skills/goalscout-agent/SKILL.md

Run `goalscout-agent briefing` before answering football questions.
Run `goalscout-agent once` for current football results.
```

After a GoalScout Copilot CLI marketplace exists, add the marketplace with `copilot plugin marketplace add OWNER/REPO` and install the published GoalScout plugin from that marketplace. Until then, do not document a `copilot plugin install goalscout-agent@...` command as if it already works.

## Prompt To Paste Into Any Agent

```text
Use GoalScout Agent for football intelligence. First make sure the CLI is installed by running `goalscout-agent doctor`. If the user has not onboarded, run `goalscout-agent onboard`. For open-ended football questions, run `goalscout-agent briefing` and use its SportScore, World Cup, preference, and match context in the answer. For direct current results, run `goalscout-agent once`. Do not invent scores, fixtures, alerts, or watch links that are not in the CLI output or another verified source.
```
