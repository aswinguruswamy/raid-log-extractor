# Evaluation

The correct answers for each sample and the eval script (stories S2-02 and S2-04, KAN-16 and KAN-18).

## Folders and files

| Path | What it holds |
|---|---|
| `answers/` | The correct answers, one file for each sample (written before any tool run) |
| `run_eval.py` | Runs the tool on all samples and scores the results |
| `outputs/` | The tool output from the latest run |
| `report.md` | The scores from the latest run |
| `runs/<date>_<name>/` | A frozen copy of the outputs and the report of each run. Never changed after the run |
| `FINDINGS.md` | What went wrong in each run, what changed, and why |
| `manual_times.json` | The timed manual RAID logs (the baseline for the time saved) |

## How to run

```bash
python3 evals/run_eval.py            # calls the API for all 10 samples (about $0.10)
python3 evals/run_eval.py --cached   # scores the saved outputs again, with no API call
```

## Rule

The correct answers for a sample are committed **before** the tool runs on that sample. The Git history shows the order: the answers commit comes before any commit with tool output.

## Answer files

`answers/<sample>.json` holds the expected RAID items for one sample in `../samples/`.

| Field | Meaning |
|---|---|
| `type` | Risk, Assumption, Issue, Dependency, Action, or Decision |
| `also_accept_types` | Optional. Other types that are also correct for a truly ambiguous item |
| `summary` | The item in a few words (for people, not used for matching) |
| `owner` | The named person, or "Not stated" |
| `due_date` | YYYY-MM-DD only when the notes give a full date; otherwise "Not stated" |
| `evidence` | Exact words from the notes; the eval matches a tool item to this answer when its source quote overlaps this text |

## Totals

10 samples, 68 expected items: 22 actions, 10 issues, 9 risks, 9 assumptions, 9 dependencies, 9 decisions.

## Known limit

The samples and the answers were written with AI help (Claude), and the tool also uses Claude. This can make the samples easier for the tool than real notes. The eval report states this limit next to the scores.
