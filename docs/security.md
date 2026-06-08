# Security

GoalScout Agent avoids storing secrets in committed files.

## Rules

- Do not commit `.football-live-agent/`.
- Do not put API keys in README examples, `SKILL.md`, tests, docs, or prompts.
- Use environment variables for provider credentials and webhook URLs.
- Treat webhook URLs as secrets.
- Do not use GoalScout for illegal streams, paywall bypasses, pirated rebroadcasts, gambling automation, or betting advice.

## Secret-bearing environment variables

- `API_FOOTBALL_KEY`
- `SPORTMONKS_API_KEY`
- `THESPORTSDB_API_KEY`
- `SPORTRADAR_API_KEY`
- `GRACENOTE_API_KEY`
- `JUSTWATCH_PARTNER_TOKEN`
- `FOOTBALL_AGENT_WEBHOOK_URL`

## Validation

```bash
python scripts/validate_repo.py
```

The validator checks packaging and documentation invariants. It is not a replacement for a full secret scan before public release.
