# Validation

GoalScout should be easy to verify from a fresh checkout.

Run the complete local validation set:

```bash
python scripts/validate_plugin.py
python scripts/validate_skill.py skills/goalscout-agent
python scripts/smoke_test_cli.py
python scripts/validate_repo.py
python -m pytest -q
```

`validate_repo.py` is the top-level health check. It verifies:

- package metadata and console scripts
- Codex plugin metadata
- skill frontmatter and body
- required assets
- required professional docs
- one-line CLI install documentation
- basic CLI smoke behavior

CI runs repository validation before the test suite.
