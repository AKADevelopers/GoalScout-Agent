import json
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
    combined = f"{readme}\n{installation}"

    assert "npm install -g github:AKADevelopers/GoalScout-Agent" in combined
    assert "pipx install git+https://github.com/AKADevelopers/GoalScout-Agent.git" in combined
    for client in ["Codex", "Claude Code", "OpenCode", "OpenClaw", "Hermes"]:
        assert client in combined
