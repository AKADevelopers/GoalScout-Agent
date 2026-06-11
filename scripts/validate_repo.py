from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DOCS = [
    "README.md",
    "docs/agent-platforms.md",
    "docs/installation.md",
    "docs/architecture.md",
    "docs/security.md",
    "docs/troubleshooting.md",
    "docs/validation.md",
    "docs/examples.md",
    "CONTRIBUTING.md",
    "SUPPORT.md",
]

NPM_GITHUB_INSTALL = "npm install -g github:AKADevelopers/GoalScout-Agent"
PIPX_GITHUB_INSTALL = "pipx install git+https://github.com/AKADevelopers/GoalScout-Agent.git"
PIP_GITHUB_INSTALL = 'python -m pip install "goalscout-agent @ git+https://github.com/AKADevelopers/GoalScout-Agent.git"'
CURL_GITHUB_INSTALL = "curl -fsSL https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.sh | sh"
POWERSHELL_GITHUB_INSTALL = "irm https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.ps1 | iex"
RAW_SKILL_URL = "https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/skills/goalscout-agent/SKILL.md"
RAW_OPENCODE_INSTALL = "https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/.opencode/INSTALL.md"


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
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    installation = (ROOT / "docs" / "installation.md").read_text(encoding="utf-8")
    agent_platforms = (ROOT / "docs" / "agent-platforms.md").read_text(encoding="utf-8")
    open_code_install = (ROOT / ".opencode" / "INSTALL.md").read_text(encoding="utf-8")
    combined_docs = f"{readme}\n{installation}\n{agent_platforms}\n{open_code_install}"
    for command in [CURL_GITHUB_INSTALL, POWERSHELL_GITHUB_INSTALL, NPM_GITHUB_INSTALL, PIPX_GITHUB_INSTALL, PIP_GITHUB_INSTALL, RAW_SKILL_URL, RAW_OPENCODE_INSTALL]:
        if command not in combined_docs:
            fail(f"missing documented install command: {command}")
    if "small Linux " + "host" in combined_docs:
        fail("documentation should mention Pi Coding Agent, not generic device wording")
    for client in ["Codex", "OpenCode", "Claude Code", "Pi Coding Agent", "OpenClaw", "Hermes", "Cursor", "GitHub Copilot CLI"]:
        if client not in combined_docs:
            fail(f"missing agent platform documentation for: {client}")
    for phrase in [
        "progressive disclosure",
        "directory name becomes the command",
        "parent and nested directories",
        "slash command menu",
    ]:
        if phrase not in agent_platforms:
            fail(f"missing skill behavior documentation: {phrase}")
    for rel in [
        "assets/app-icon.svg",
        "assets/composer-icon.svg",
        "bin/goalscout-agent.js",
        "package.json",
        "scripts/install.ps1",
        "scripts/install.sh",
        ".opencode/INSTALL.md",
        "skills/goalscout-agent/SKILL.md",
        ".codex-plugin/plugin.json",
    ]:
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


def check_package_json() -> None:
    data = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    if data.get("name") != "goalscout-agent":
        fail("package.json name must be goalscout-agent")
    bin_scripts = data.get("bin", {})
    if bin_scripts.get("goalscout-agent") != "./bin/goalscout-agent.js":
        fail("package.json must expose goalscout-agent bin")
    if bin_scripts.get("football-live-agent") != "./bin/goalscout-agent.js":
        fail("package.json must expose football-live-agent bin")


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
    check_package_json()
    check_manifest()
    run([sys.executable, "scripts/validate_plugin.py"])
    run([sys.executable, "scripts/validate_skill.py", "skills/goalscout-agent"])
    run([sys.executable, "scripts/smoke_test_cli.py"])
    print("repo validation passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
