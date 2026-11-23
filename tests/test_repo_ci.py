"""Shared CI standard SH1 and release workflow SH6 (RAID v2 spec R17.1, R18.1)."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = ROOT / ".github" / "workflows"


def _load(name: str) -> dict:
    data = yaml.safe_load((WORKFLOWS / name).read_text(encoding="utf-8"))
    data["on"] = data.pop(True, data.get("on"))  # YAML 1.1 reads "on" as True
    return data


def test_every_action_is_pinned_to_a_commit_sha():
    for workflow in WORKFLOWS.glob("*.yml"):
        for line in workflow.read_text(encoding="utf-8").splitlines():
            if "uses:" in line:
                assert re.search(r"@[0-9a-f]{40} # v\d", line), (workflow.name, line)


def test_tests_run_on_python_3_11_to_3_13_with_lint():
    job = _load("tests.yml")["jobs"]["offline-tests"]
    assert job["strategy"]["matrix"]["python-version"] == ["3.11", "3.12", "3.13"]
    commands = "\n".join(step.get("run", "") for step in job["steps"])
    assert "ruff check ." in commands
    assert "pytest" in commands


def test_secret_dependency_and_licence_scans_run_on_each_pull_request():
    wf = _load("tests.yml")
    assert "pull_request" in wf["on"]
    steps = wf["jobs"]["scans"]["steps"]
    text = "\n".join(str(step) for step in steps)
    assert "gitleaks/gitleaks-action@" in text
    assert "pip-audit" in text
    assert "pip-licenses" in text and "--fail-on=" in text


def test_dependabot_watches_pip_and_actions():
    config = yaml.safe_load((ROOT / ".github" / "dependabot.yml").read_text(encoding="utf-8"))
    assert {u["package-ecosystem"] for u in config["updates"]} == {"pip", "github-actions"}


def test_release_workflow_runs_tests_and_publishes_on_version_tags():
    wf = _load("release.yml")
    assert wf["on"]["push"]["tags"] == ["v*.*.*"]
    assert wf["permissions"] == {"contents": "write"}
    commands = "\n".join(step.get("run", "") for step in wf["jobs"]["release"]["steps"])
    assert "pytest" in commands
    assert "release_notes.py" in commands
    assert "gh release create" in commands


def test_release_notes_come_from_the_changelog():
    out = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "release_notes.py"), "v1.0.0"],
        capture_output=True, text=True, check=True,
    ).stdout
    assert "The first public release." in out
    assert "## [" not in out


def test_known_limits_is_the_first_readme_section():
    # RAID v2 spec R19.1 (shared item SH5).
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    first = next(line for line in readme.splitlines() if line.startswith("## "))
    assert first == "## Known limits"
    limits = readme.split("\n## Known limits")[1].split("\n## ")[0]
    assert "tuned" in limits and "held-out" in limits


def test_contributing_rules_exist():
    # Shared rules for MCF, SRG and RAID (constitution P9, P12; SH4).
    text = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    for words in ("specs/", "test first", "bug", "CI"):
        assert words in text, words
