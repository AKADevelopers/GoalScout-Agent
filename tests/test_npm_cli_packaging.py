import json
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_npm_manifest_exposes_goalscout_cli_wrapper():
    manifest_path = ROOT / "package.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["name"] == "goalscout-agent"
    assert manifest["bin"]["goalscout-agent"] == "./bin/goalscout-agent.js"
    assert manifest["bin"]["football-live-agent"] == "./bin/goalscout-agent.js"

    wrapper = ROOT / "bin" / "goalscout-agent.js"
    assert wrapper.is_file()
    assert wrapper.read_text(encoding="utf-8").startswith("#!/usr/bin/env node")


def test_npm_cli_wrapper_runs_python_cli_help():
    proc = subprocess.run(
        ["node", str(ROOT / "bin" / "goalscout-agent.js"), "--help"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "GoalScout Agent live football notification watcher" in proc.stdout
    assert "where-to-watch" in proc.stdout


def test_installation_docs_include_npm_and_agent_cli_paths():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    installation = (ROOT / "docs" / "installation.md").read_text(encoding="utf-8")
    agent_platforms = (ROOT / "docs" / "agent-platforms.md").read_text(encoding="utf-8")
    open_code_install = (ROOT / ".opencode" / "INSTALL.md").read_text(encoding="utf-8")
    combined = f"{readme}\n{installation}\n{agent_platforms}\n{open_code_install}"

    assert "curl -fsSL https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.sh | sh" in combined
    assert 'irm https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/main/scripts/install.ps1 | iex' in combined
    assert "npm install -g github:AKADevelopers/GoalScout-Agent" in combined
    assert "pipx install git+https://github.com/AKADevelopers/GoalScout-Agent.git" in combined
    assert "https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/skills/goalscout-agent/SKILL.md" in combined
    assert "https://raw.githubusercontent.com/AKADevelopers/GoalScout-Agent/refs/heads/main/.opencode/INSTALL.md" in combined
    assert "small Linux " + "host" not in combined
    for client in ["Codex", "Claude Code", "OpenCode", "Pi Coding Agent", "OpenClaw", "Hermes", "Cursor", "GitHub Copilot CLI"]:
        assert client in combined
    assert "goalscout-agent briefing" in combined
    assert "goalscout-agent once" in combined
    assert "Do not invent scores" in combined


def test_one_line_install_scripts_use_github_npm_package():
    shell_script = (ROOT / "scripts" / "install.sh").read_text(encoding="utf-8")
    powershell_script = (ROOT / "scripts" / "install.ps1").read_text(encoding="utf-8")

    assert "github:AKADevelopers/GoalScout-Agent" in shell_script
    assert "github:AKADevelopers/GoalScout-Agent" in powershell_script
    assert "GOALSCOUT_INSTALL_DRY_RUN" in shell_script
    assert "GOALSCOUT_INSTALL_DRY_RUN" in powershell_script
    assert "Python 3.11" in shell_script
    assert "Python 3.11" in powershell_script


def test_powershell_install_script_supports_dry_run():
    proc = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(ROOT / "scripts" / "install.ps1"),
        ],
        cwd=ROOT,
        env={**os.environ, "GOALSCOUT_INSTALL_DRY_RUN": "1"},
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
    )

    assert proc.returncode == 0
    assert "npm install -g github:AKADevelopers/GoalScout-Agent" in proc.stdout
