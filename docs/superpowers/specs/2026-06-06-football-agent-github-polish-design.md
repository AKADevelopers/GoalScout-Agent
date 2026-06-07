# GoalScout Agent GitHub Polish Design

## Goal

Make GoalScout Agent look professional when published to GitHub and when installed as a skill/plugin in Codex, OpenClaw, Hermes, or similar agent platforms.

## Scope

- Add a root Codex plugin manifest with interface metadata.
- Add professional icon assets for plugin and skill UI.
- Add GitHub-facing repository files: README, license, ignore rules, attributes, CI workflow, and agent notes.
- Improve `skills/goalscout-agent/agents/openai.yaml` with icons, brand color, and policy metadata.
- Add tests that verify metadata and asset paths exist.

## Out of Scope

- Changing the live football alert behavior.
- Copying code, branding, or visual assets from `obra/superpowers`.
- Publishing to GitHub from this workspace.

## Validation

- `python -m pytest -q`
- Skill validation with `quick_validate.py`
- Plugin validation with `validate_plugin.py`
