"""Run the tool on every sample, score it, and write evals/report.md.

    python evals/run_eval.py            # calls the Claude API (about $0.10 for all samples)
    python evals/run_eval.py --cached   # re-scores the saved outputs, no API call

Story S2-04 (KAN-18). The report format is story S2-05 (KAN-19).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from raid.cost import run_cost  # noqa: E402
from raid.evaluate import build_report, misses_and_extras, score_sample  # noqa: E402
from raid.extract import DEFAULT_MODEL, extract_items  # noqa: E402
from raid.parse import read_notes  # noqa: E402
from raid.schema import ItemType  # noqa: E402

EVALS = ROOT / "evals"
ANSWERS = EVALS / "answers"
OUTPUTS = EVALS / "outputs"
SAMPLES = ROOT / "samples"
MANUAL_TIMES = EVALS / "manual_times.json"

TARGETS = {"recall": 0.85, "precision": 0.80}
RECALL_TARGET_TYPES = ["Risk", "Issue", "Dependency", "Action"]


def run(cached: bool, model: str) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    OUTPUTS.mkdir(exist_ok=True)
    scores, runs = [], []
    for answer_file in sorted(ANSWERS.glob("*.json")):
        answer = json.loads(answer_file.read_text(encoding="utf-8"))
        notes = read_notes(SAMPLES / answer["sample"])
        output_file = OUTPUTS / answer_file.name

        if cached:
            if not output_file.exists():
                print(f"No saved output for {answer['sample']}. Run without --cached first.", file=sys.stderr)
                return 2
            output = json.loads(output_file.read_text(encoding="utf-8"))
        else:
            print(f"Running {answer['sample']}...")
            result = extract_items(notes, model=model, source_file=answer["sample"])
            output = {
                "sample": answer["sample"],
                "model": result.model,
                "run_date": date.today().isoformat(),
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "seconds": round(result.seconds, 2),
                "warnings": result.warnings,
                "items": [item.model_dump(mode="json") for item in result.log.items],
            }
            output_file.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

        runs.append(output)
        scores.append(score_sample(answer["sample"], notes, answer["items"], output["items"]))

    report = build_report(scores)
    (EVALS / "report.md").write_text(render(report, runs), encoding="utf-8")
    print(summary_line(report))
    print(f"Report: {EVALS / 'report.md'}")
    return 0


def pct(value) -> str:
    return "-" if value is None else f"{value:.0%}"


def summary_line(report) -> str:
    return (
        f"Recall {pct(report.total.recall)} | Precision {pct(report.total.precision)} | "
        f"Invented owners {len(report.invented_owners)} | Invented dates {len(report.invented_dates)}"
    )


def render(report, runs) -> str:
    models = sorted({r["model"] for r in runs})
    run_dates = sorted({r["run_date"] for r in runs})
    cost = sum(run_cost(r["model"], r["input_tokens"], r["output_tokens"]) or 0 for r in runs)
    seconds = sum(r["seconds"] for r in runs)
    total = report.total
    key_recall_hits = sum(report.by_type[t].recall_hits for t in RECALL_TARGET_TYPES)
    key_recall_total = sum(report.by_type[t].expected for t in RECALL_TARGET_TYPES)
    key_recall = key_recall_hits / key_recall_total if key_recall_total else None

    lines = [
        "# Evaluation report",
        "",
        f"**Samples:** {len(runs)} | **Expected items:** {total.expected} | **Model:** {', '.join(models)} | "
        f"**Run date:** {', '.join(run_dates)} | **Report date:** {date.today().isoformat()}",
        "",
        "## Scores by item type",
        "",
        "| Type | Expected | Found by tool | Recall | Precision |",
        "|---|---|---|---|---|",
    ]
    for item_type in ItemType:
        s = report.by_type[item_type.value]
        lines.append(f"| {item_type.value} | {s.expected} | {s.found} | {pct(s.recall)} | {pct(s.precision)} |")
    lines.append(f"| **All** | **{total.expected}** | **{total.found}** | **{pct(total.recall)}** | **{pct(total.precision)}** |")

    def check(ok):
        return "✅" if ok else "❌"

    owner_acc = report.owner_correct / report.owner_checked if report.owner_checked else None
    date_acc = report.date_correct / report.date_checked if report.date_checked else None
    lines += [
        "",
        "## Charter targets",
        "",
        "| Metric | Target | Result | Met |",
        "|---|---|---|---|",
        f"| Recall on risks, issues, dependencies, actions | 85% or more | {pct(key_recall)} | {check(key_recall is not None and key_recall >= TARGETS['recall'])} |",
        f"| Precision on all item types | 80% or more | {pct(total.precision)} | {check(total.precision is not None and total.precision >= TARGETS['precision'])} |",
        f"| Owners or dates that the tool invents | 0 | {len(report.invented_owners) + len(report.invented_dates)} | {check(not report.invented_owners and not report.invented_dates)} |",
        "",
        "## Owners and dates (on matched items)",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Correct owner | {report.owner_correct} of {report.owner_checked} ({pct(owner_acc)}) |",
        f"| Correct due date | {report.date_correct} of {report.date_checked} ({pct(date_acc)}) |",
        f"| Owner given where the notes name nobody | {len(report.guessed_owners)} |",
        f"| Owner not in the notes at all (invented) | {len(report.invented_owners)} |",
        f"| Date not in the notes at all (invented) | {len(report.invented_dates)} |",
        "",
        "## Cost and time",
        "",
        f"All {len(runs)} samples: ${cost:.4f} in total, {seconds:.1f} s in total "
        f"(average ${cost / max(len(runs), 1):.4f} and {seconds / max(len(runs), 1):.1f} s for each sample).",
    ]

    if MANUAL_TIMES.exists():
        manual = json.loads(MANUAL_TIMES.read_text(encoding="utf-8"))
        by_sample = {r["sample"]: r for r in runs}
        lines += [
            "",
            "## Manual baseline (story S2-03, KAN-17)",
            "",
            "| Sample | Manual RAID log | Tool run |",
            "|---|---|---|",
        ]
        for name, minutes in manual.get("minutes", {}).items():
            tool = by_sample.get(name)
            lines.append(f"| {name} | {minutes} min | {tool['seconds']:.1f} s |" if tool else f"| {name} | {minutes} min | - |")
        if manual.get("note"):
            lines += ["", manual["note"]]

    lines += ["", "## Details by sample", ""]
    for s in report.samples:
        misses, extras, mixups = misses_and_extras(s)
        lines.append(f"**{s.sample}** — expected {len(s.expected)}, found {len(s.found)}, matched {len(s.pairs)}")
        for label, entries in (("Missed", misses), ("Extra", extras), ("Type mix-up", mixups),
                               ("Guessed owner", s.guessed_owners), ("Invented owner", s.invented_owners),
                               ("Invented date", s.invented_dates)):
            for entry in entries:
                lines.append(f"- {label}: {entry}")
        lines.append("")

    lines += [
        "## How to read this report",
        "",
        "- **Recall:** of the items that are in the notes, the share that the tool found with an accepted type.",
        "- **Precision:** of the items that the tool reported, the share that are correct.",
        "- **Matching:** a tool item matches an expected item when its source quote shares most of its words "
        "with the expected evidence (see `raid/evaluate.py`).",
        "",
        "## Known limits",
        "",
        f"- {len(runs)} samples and {total.expected} expected items: the scores show a direction, not a statistical proof.",
        "- The samples and the correct answers were written with AI help (Claude), and the tool also uses Claude. "
        "This can make the samples easier for the tool than real notes.",
        "- The correct answers were committed before the tool ran on the samples (see the Git history).",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the RAID Log Extractor on the samples.")
    parser.add_argument("--cached", action="store_true", help="Score the saved outputs; no API call.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()
    sys.exit(run(args.cached, args.model))
