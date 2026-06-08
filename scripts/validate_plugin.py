from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fail(message: str) -> None:
    raise SystemExit(f"plugin validation failed: {message}")


def main() -> int:
    manifest_path = ROOT / ".codex-plugin" / "plugin.json"
    if not manifest_path.is_file():
        fail("missing .codex-plugin/plugin.json")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required = ["name", "version", "description", "homepage", "repository", "license", "skills", "interface"]
    for field in required:
        if field not in manifest:
            fail(f"missing manifest field: {field}")

    if manifest["name"] != "goalscout-agent":
        fail("manifest name must be goalscout-agent")
    if "AKADevelopers/GoalScout-Agent" not in manifest["repository"]:
        fail("repository must point to AKADevelopers/GoalScout-Agent")
    if manifest["skills"] != "./skills/":
        fail("skills path must be ./skills/")

    interface = manifest["interface"]
    for field in ["displayName", "shortDescription", "longDescription", "developerName", "category", "brandColor", "composerIcon", "logo"]:
        if not interface.get(field):
            fail(f"missing interface field: {field}")

    for field in ["composerIcon", "logo"]:
        asset = ROOT / interface[field].removeprefix("./")
        if not asset.is_file():
            fail(f"missing asset referenced by {field}: {asset}")

    prompts = " ".join(interface.get("defaultPrompt", []))
    if "$goalscout-agent" not in prompts:
        fail("default prompts should mention $goalscout-agent")

    print("plugin validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
