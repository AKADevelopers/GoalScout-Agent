import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_codex_plugin_manifest_has_professional_interface():
    manifest_path = ROOT / ".codex-plugin" / "plugin.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["name"] == "goalscout-agent"
    assert manifest["version"] == "0.1.0"
    assert manifest["skills"] == "./skills/"
    assert "[TODO:" not in manifest_path.read_text(encoding="utf-8")

    interface = manifest["interface"]
    assert interface["displayName"] == "GoalScout Agent"
    assert interface["category"] == "Sports"
    assert interface["brandColor"] == "#16A34A"
    assert "Live football goals" in interface["shortDescription"]
    assert "$goalscout-agent" in " ".join(interface["defaultPrompt"])

    for field in ("composerIcon", "logo"):
        asset_path = ROOT / interface[field].removeprefix("./")
        assert asset_path.is_file(), f"missing plugin asset: {asset_path}"


def test_repository_metadata_uses_akadevelopers_profile():
    checked_files = [
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / "pyproject.toml",
        ROOT / "README.md",
    ]

    for path in checked_files:
        text = path.read_text(encoding="utf-8")
        assert "AKADevelopers/GoalScout-Agent" in text
        assert "YOUR_USERNAME" not in text


def test_skill_interface_metadata_references_icons():
    metadata_path = ROOT / "skills" / "goalscout-agent" / "agents" / "openai.yaml"
    metadata = metadata_path.read_text(encoding="utf-8")

    assert 'brand_color: "#16A34A"' in metadata
    assert "$goalscout-agent" in metadata

    for field in ("icon_small", "icon_large"):
        match = re.search(rf'{field}: "([^"]+)"', metadata)
        assert match is not None, f"missing {field}"
        asset_path = metadata_path.parents[1] / match.group(1).removeprefix("./")
        assert asset_path.is_file(), f"missing skill asset: {asset_path}"
