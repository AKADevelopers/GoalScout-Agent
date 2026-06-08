from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"skill validation failed: {message}")


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end == -1:
        fail("SKILL.md frontmatter is not closed")
    raw = text[4:end]
    body = text[end + 5 :].strip()
    fields: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip()] = value.strip().strip('"')
    return fields, body


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    skill_dir = Path(args[0]) if args else ROOT / "skills" / "goalscout-agent"
    if not skill_dir.is_absolute():
        skill_dir = ROOT / skill_dir
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        fail(f"missing SKILL.md at {skill_file}")

    text = skill_file.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(text)
    for field in ["name", "description"]:
        if not fields.get(field):
            fail(f"missing frontmatter field: {field}")
    if fields["name"] != "goalscout-agent":
        fail("skill name must be goalscout-agent")
    if len(fields["description"]) > 1024:
        fail("description is too long")
    if not body:
        fail("SKILL.md body is empty")
    for phrase in ["goalscout-agent onboard", "goalscout-agent doctor", "goalscout-agent briefing", "goalscout-agent once", "where-to-watch"]:
        if phrase not in text:
            fail(f"missing expected command guidance: {phrase}")

    metadata = skill_dir / "agents" / "openai.yaml"
    if not metadata.is_file():
        fail("missing agents/openai.yaml")
    metadata_text = metadata.read_text(encoding="utf-8")
    for field in ["icon_small", "icon_large", "brand_color", "default_prompt"]:
        if field not in metadata_text:
            fail(f"missing openai.yaml field: {field}")
    for match in re.finditer(r'icon_(?:small|large):\s*"([^"]+)"', metadata_text):
        asset = skill_dir / match.group(1).removeprefix("./")
        if not asset.is_file():
            fail(f"missing skill asset: {asset}")

    print("skill validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
