"""Build the keyless demo files from saved v2 runs (RAID v2 task A11; spec R20.1).

    python scripts/make_demo.py

Reads run 1 of the held-out run (evals/heldout/outputs/run1/), keeps the items as the
tool returned them, rebuilds the Needs attention lines with the current code (no API
call), and writes demo/<call>.json for the page's demo mode.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from raid.checks import run_checks  # noqa: E402
from raid.parse import input_warnings, read_notes  # noqa: E402
from raid.pipeline import Analysis, needs_attention  # noqa: E402

RUN = ROOT / "evals" / "heldout" / "outputs" / "run1"
CALLS = ROOT / "evals" / "heldout" / "calls"
DEMO = ROOT / "demo"

DEMOS = {
    "h01_warehouse_scanners": ("Warehouse scanners", "Plain-text notes (.txt)",
                               "A reply that does not commit (\"Not sure, I'll let you know\") and dates from weekdays."),
    "h02_website_redesign": ("Website redesign", "Plain-text notes (.txt)",
                             "A weak yes (\"I can try\") gives a tentative owner."),
    "h03_mobile_release": ("Mobile app release", "Plain-text notes (.txt)",
                           "A refusal (\"No, I'm full this week\") gives a declined owner."),
    "h12_clinic_scheduling": ("Clinic scheduling app", "Plain-text notes (.txt)",
                              "A task given to someone who is not on the call."),
}


def build(stem: str) -> dict:
    saved = json.loads((RUN / f"{stem}.json").read_text(encoding="utf-8"))
    notes = read_notes(CALLS / saved["sample"])
    analysis = Analysis.from_saved(saved)
    general = [] if analysis.meeting_date else ["Enter the meeting date to convert dates."]
    analysis.attention = needs_attention(analysis.log, general + input_warnings(notes),
                                         run_checks(analysis.log, notes))
    label, file_format, tests = DEMOS[stem]
    data = analysis.to_saved()
    data.update({
        "label": label, "format": file_format, "tests": tests,
        "notes": str((CALLS / saved["sample"]).relative_to(ROOT)),
        "source": "Held-out run 1 (prompt 2.1), saved output. No API call is made in demo mode.",
        "demo_built": date.today().isoformat(),
    })
    return data


def main() -> int:
    built = {stem: build(stem) for stem in DEMOS}  # build all first: a failure leaves the old files
    for old in DEMO.glob("*.json"):
        old.unlink()
    for stem, data in built.items():
        (DEMO / f"{stem}.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"demo/{stem}.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
