"""Run the tool on a set of calls, score it, and write the set's report.

    python evals/run_eval.py                          # tuning set, 1 run (about $0.10)
    python evals/run_eval.py --gate                   # ... and exit 1 on an invented owner or date (CI, R16.1)
    python evals/run_eval.py --cached                 # re-score the saved outputs, no API call
    python evals/run_eval.py --set spec --gate        # the spec's eval examples AC1-AC11, AC16, AC28
    python evals/run_eval.py --set heldout --runs 5   # held-out set, 5 runs (release, R13-R15)
    python evals/run_eval.py --set heldout --cached --gate   # release gate (N1, AC41)

Story S2-04 (KAN-18), S2-05 (KAN-19); RAID v2 task A8 (spec R14-R16, N1).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from evals.heldout_rules import check_key_order, missing_cases  # noqa: E402
from raid.cost import run_cost  # noqa: E402
from raid.evaluate import (  # noqa: E402
    build_report,
    consistency,
    misses_and_extras,
    score_sample,
    v2_scores,
)
from raid.extract import DEFAULT_MODEL  # noqa: E402
from raid.parse import read_notes  # noqa: E402
from raid.pipeline import analyse  # noqa: E402
from raid.schema import ItemType  # noqa: E402

EVALS = ROOT / "evals"
ANSWERS = EVALS / "answers"
OUTPUTS = EVALS / "outputs"
SAMPLES = ROOT / "samples"
MANUAL_TIMES = EVALS / "manual_times.json"
HELDOUT = EVALS / "heldout"

# name: (answers, calls, outputs, report, key with the call's file name)
SETS = {
    "tuning": (ANSWERS, SAMPLES, OUTPUTS, EVALS / "report.md", "sample"),
    "heldout": (HELDOUT / "answers", HELDOUT / "calls", HELDOUT / "outputs", HELDOUT / "report.md", "call"),
    # The spec's own eval examples (AC1-AC11, AC16, AC28): tuning material, not held out.
    "spec": (EVALS / "spec_cases" / "answers", EVALS / "spec_cases" / "calls", EVALS / "spec_cases" / "outputs",
             EVALS / "spec_cases" / "report.md", "call"),
}
TUNING_WRITER = "Claude (AI) with the project owner, v1 (see Known limits)"

TARGETS = {"recall": 0.85, "precision": 0.80}
RECALL_TARGET_TYPES = ["Risk", "Issue", "Dependency", "Action"]


def _output_file(outputs: Path, set_name: str, run_no: int, name: str) -> Path:
    if set_name == "tuning" and run_no == 1:
        return outputs / name  # v1 place, kept
    return outputs / f"run{run_no}" / name


def run(cached: bool, model: str, set_name: str = "tuning", runs: int = 1, gate: bool = False) -> int:
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass

    answers_dir, calls_dir, outputs, report_file, call_key = SETS[set_name]
    answer_files = sorted(answers_dir.glob("*.json"))
    if not answer_files:
        print(f"No answer keys in {answers_dir}.", file=sys.stderr)
        return 2

    all_runs: list[list] = []
    outputs_seen: list[dict] = []
    writers = set()
    for run_no in range(1, runs + 1):
        scores = []
        for answer_file in answer_files:
            answer = json.loads(answer_file.read_text(encoding="utf-8"))
            writers.add(answer.get("writer", TUNING_WRITER))
            call = answer[call_key]
            notes = read_notes(calls_dir / call)
            output_file = _output_file(outputs, set_name, run_no, answer_file.name)

            if cached:
                if not output_file.exists():
                    print(f"No saved output for {call} (run {run_no}). Run without --cached first.", file=sys.stderr)
                    return 2
                output = json.loads(output_file.read_text(encoding="utf-8"))
            else:
                print(f"Run {run_no}: {call}...")
                meeting = answer.get("meeting_date")
                result = analyse(notes, date.fromisoformat(meeting) if meeting else None, model=model,
                                 source_file=call)  # same code steps as the page (task A7)
                output = {
                    "sample": call,
                    "model": result.model,
                    "prompt_version": result.prompt_version,
                    "run_date": date.today().isoformat(),
                    "meeting_date": meeting,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "seconds": round(result.seconds, 2),
                    "warnings": result.warnings,
                    "needs_attention": [[a.short_id, a.text] for a in result.attention],
                    "items": [item.model_dump(mode="json") for item in result.log.items],
                }
                output_file.parent.mkdir(parents=True, exist_ok=True)
                output_file.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")

            outputs_seen.append(output)
            label = call if runs == 1 else f"{call} (run {run_no})"
            scores.append(score_sample(label, notes, answer["items"], output["items"]))
        all_runs.append(scores)

    report = build_report([s for scores in all_runs for s in scores])
    v2 = v2_scores(report)
    spread = consistency(all_runs) if runs > 1 else None
    first_run = outputs_seen[: len(answer_files)]
    report_file.write_text(render(report, first_run, v2=v2, set_name=set_name, runs_count=runs, spread=spread,
                                  writers=sorted(writers), all_outputs=outputs_seen), encoding="utf-8")
    print(summary_line(report) + f" | Wrong owners {len(v2.wrong_owners)} | Wrong dates {len(v2.wrong_dates)}")
    print(f"Report: {report_file}")

    if gate:
        failures = list(v2.gate_failures)
        if set_name == "heldout":
            failures += [f"No held-out call yet for case {case}" for case in missing_cases(HELDOUT)]
            failures += [f"Answer key changed after the first held-out run: {path}" for path in check_key_order(ROOT)]
        if failures:
            print("GATE FAILED (0 invented owners and 0 invented dates required):", file=sys.stderr)
            for failure in failures:
                print(f"  - {failure}", file=sys.stderr)
            return 1
        print("Gate passed: 0 invented owners, 0 invented dates.")
    return 0


def pct(value) -> str:
    return "-" if value is None else f"{value:.0%}"


def summary_line(report) -> str:
    v2 = v2_scores(report)
    return (
        f"Recall {pct(report.total.recall)} | Precision {pct(report.total.precision)} | "
        f"Invented owners {len(v2.invented_owners)} | Invented dates {len(v2.invented_dates)}"
    )


def render(report, runs, *, v2=None, set_name: str = "tuning", runs_count: int = 1, spread=None,
           writers=(), all_outputs=None) -> str:
    """`runs`: the outputs of run 1 (one per call); `all_outputs`: every run, for cost and time."""
    v2 = v2 or v2_scores(report)
    every = all_outputs or runs
    models = sorted({r["model"] for r in every})
    run_dates = sorted({r["run_date"] for r in every})
    cost = sum(run_cost(r["model"], r["input_tokens"], r["output_tokens"]) or 0 for r in every)
    seconds = sum(r["seconds"] for r in every)
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
        "## v2 scores (spec R15.1)",
        "",
        f"**Set:** {set_name} | **Calls:** {len(runs)} | **Runs per call:** {runs_count} | "
        f"**Prompt version:** {', '.join(sorted({str(r.get('prompt_version', '1')) for r in runs}))} | "
        f"**Calls written by:** {'; '.join(writers) or '-'}",
        "",
        "| Metric | Result |",
        "|---|---|",
        f"| Recall | {pct(total.recall)} |",
        f"| Precision | {pct(total.precision)} |",
        f"| Invented owners (release gate: 0) | {len(v2.invented_owners)} |",
        f"| Invented dates (release gate: 0) | {len(v2.invented_dates)} |",
        f"| Wrong owners | {len(v2.wrong_owners)} |",
        f"| Wrong dates | {len(v2.wrong_dates)} |",
        f"| Owner state correct | {v2.state_correct} of {v2.state_checked} |",
        f"| Items found in all {runs_count} runs | {pct(spread)} |",
        "",
    ]
    for label, entries in (("Invented owner", v2.invented_owners), ("Invented date", v2.invented_dates),
                           ("Wrong owner", v2.wrong_owners), ("Wrong date", v2.wrong_dates)):
        lines += [f"- {label}: {entry}" for entry in entries]
    lines += [
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
        f"All {len(every)} call runs: ${cost:.4f} in total, {seconds:.1f} s in total "
        f"(average ${cost / max(len(every), 1):.4f} and {seconds / max(len(every), 1):.1f} s for each call run).",
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
    parser = argparse.ArgumentParser(description="Evaluate the RAID Log Extractor on a set of calls.")
    parser.add_argument("--cached", action="store_true", help="Score the saved outputs; no API call.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--set", dest="set_name", choices=sorted(SETS), default="tuning")
    parser.add_argument("--runs", type=int, default=1, help="Runs per call (5 for the held-out run).")
    parser.add_argument("--gate", action="store_true", help="Exit 1 on any invented owner or date.")
    args = parser.parse_args()
    sys.exit(run(args.cached, args.model, args.set_name, args.runs, args.gate))
