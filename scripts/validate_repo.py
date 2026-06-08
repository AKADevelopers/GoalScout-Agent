from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "README.md",
    "docs/installation.md",
    "docs/architecture.md",
    "docs/security.md",
    "docs/troubleshooting.md",
    "docs/validation.md",
    "docs/examples.md",
    "CONTRIBUTING.md",
    "SUPPORT.md",
]

ONE_LINE_INSTALL = 'python -m pip install "goalscout-agent @ git+https://github.com/AKADevelopers/GoalScout-Agent.git"'


def fail(message: str) -> None:
    raise SystemExit(f"repo validation failed: {message}")


def run(args: list[str]) -> None:
    proc = subprocess.run(args, cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
    if proc.returncode != 0:
        fail(f"command failed: {' '.join(args)}\n{proc.stdout}")
    print(proc.stdout.strip())


def check_files() -> None:
    for rel in REQUIRED_DOCS:
        path = ROOT / rel
        if not path.is_file():
            fail(f"missing required documentation file: {rel}")
    if ONE_LINE_INSTALL not in (ROOT / "README.md").read_text(encoding="utf-8") and ONE_LINE_INSTALL not in (ROOT / "docs" / "installation.md").read_text(encoding="utf-8"):
        fail("missing one-line GitHub CLI install command")
    for rel in ["assets/app-icon.svg", "assets/composer-icon.svg", "skills/goalscout-agent/SKILL.md", ".codex-plugin/plugin.json"]:
        if not (ROOT / rel).is_file():
            fail(f"missing required package file: {rel}")


def check_pyproject() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data.get("project", {})
    if project.get("name") != "goalscout-agent":
        fail("pyproject project.name must be goalscout-agent")
    scripts = project.get("scripts", {})
    if scripts.get("goalscout-agent") != "football_live_agent.cli:main":
        fail("missing goalscout-agent console script")
    urls = project.get("urls", {})
    if "AKADevelopers/GoalScout-Agent" not in urls.get("Repository", ""):
        fail("pyproject repository URL is not set correctly")


def check_manifest() -> None:
    manifest = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("name") != "goalscout-agent":
        fail("plugin manifest name must be goalscout-agent")
    if manifest.get("skills") != "./skills/":
        fail("plugin manifest skills path must be ./skills/")
    interface = manifest.get("interface", {})
    if interface.get("displayName") != "GoalScout Agent":
        fail("plugin displayName must be GoalScout Agent")
    if not interface.get("longDescription") or len(interface["longDescription"]) < 120:
        fail("plugin longDescription is too short")


def main() -> int:
    check_files()
    check_pyproject()
    check_manifest()
    run([sys.executable, "scripts/validate_plugin.py"])
    run([sys.executable, "scripts/validate_skill.py", "skills/goalscout-agent"])
    run([sys.executable, "scripts/smoke_test_cli.py"])
    print("repo validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
