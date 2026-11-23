"""Rules for the held-out set (RAID v2 spec R13.1, R13.2; AC38, AC39; task A8)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

# One held-out call for each P1 case of the failure catalogue (spec R13.1).
P1_CASES = [
    "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A11",
    "B1", "B2", "B6", "B7", "B8", "B10",
    "C1", "C2", "C3", "C4",
    "D1", "D2", "D3", "D4", "D6", "D12",
    "E1", "E7", "F1", "G1",
]


def missing_cases(heldout_dir: Path) -> list[str]:
    """The P1 cases that have no committed answer key yet, in catalogue order."""
    have = {json.loads(f.read_text(encoding="utf-8")).get("case") for f in (heldout_dir / "answers").glob("*.json")}
    return [case for case in P1_CASES if case not in have]


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout


def _times(repo: Path, *paths: str) -> list[int]:
    return [int(t) for t in _git(repo, "log", "--format=%ct", "--", *paths).split()]


def check_key_order(repo: Path, heldout: str = "evals/heldout") -> list[str]:
    """Problems with "keys first" (AC39): a key committed after the first run output of its
    own call, a key with changes that are not committed, or a history too short to check.
    An empty list means every key is older than every run of its call."""
    if _git(repo, "rev-parse", "--is-shallow-repository").strip() == "true":
        return ["The Git history is shallow; fetch the full history to check the key order."]
    problems = [f"{line[3:]} (not committed)"
                for line in _git(repo, "status", "--porcelain", "--", f"{heldout}/answers").splitlines()]
    for path in _git(repo, "ls-files", f"{heldout}/answers").split():
        key_times = _times(repo, path)
        if not key_times:
            continue  # staged, never committed: reported above
        name = Path(path).name
        output_times = _times(repo, f"{heldout}/outputs/*/{name}")
        if output_times and max(key_times) > min(output_times):
            problems.append(path)
    return problems
