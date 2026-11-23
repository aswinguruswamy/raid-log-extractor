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


def _times(repo: Path, *args: str) -> list[int]:
    out = subprocess.run(["git", "-C", str(repo), "log", "--format=%ct", *args],
                         check=True, capture_output=True, text=True).stdout
    return [int(line) for line in out.split()]


def check_key_order(repo: Path, heldout: str = "evals/heldout") -> list[str]:
    """Answer keys changed after the first held-out run output was committed (AC39).
    An empty list means every key is older than every run."""
    outputs = _times(repo, "--", f"{heldout}/outputs")
    if not outputs:
        return []
    first_run = min(outputs)
    answers = subprocess.run(["git", "-C", str(repo), "ls-files", f"{heldout}/answers"],
                             check=True, capture_output=True, text=True).stdout.split()
    return [path for path in answers if max(_times(repo, "--", path)) > first_run]
