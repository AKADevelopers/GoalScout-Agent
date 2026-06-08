# Examples

## One-line install

```bash
npm install -g github:AKADevelopers/GoalScout-Agent
```

Python CLI alternative:

```bash
pipx install git+https://github.com/AKADevelopers/GoalScout-Agent.git
```

Pip alternative:

```bash
python -m pip install "goalscout-agent @ git+https://github.com/AKADevelopers/GoalScout-Agent.git"
```

After an npm registry release:

```bash
npm install -g goalscout-agent
```

## Console setup

```bash
goalscout-agent onboard
goalscout-agent briefing
goalscout-agent health-check
goalscout-agent once
```

## Background watcher

```bash
goalscout-agent start-background
goalscout-agent status
goalscout-agent stop
```

## Hermes-style delivery

```bash
export FOOTBALL_AGENT_DELIVERY=hermes
export FOOTBALL_AGENT_CHANNEL=telegram
export FOOTBALL_AGENT_TARGET=@your-chat-or-group
goalscout-agent test-notification
```

## Webhook delivery

```bash
export FOOTBALL_AGENT_DELIVERY=webhook
export FOOTBALL_AGENT_WEBHOOK_URL=<your-webhook-url>
goalscout-agent test-notification
```

## Where-to-watch guide

```bash
goalscout-agent where-to-watch
goalscout-agent where-to-watch --team "Manchester United" --date 2026-06-15
```

## Preference repair

```bash
goalscout-agent doctor
goalscout-agent repair
```
