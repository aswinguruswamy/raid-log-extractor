# Eval findings

A short record of each eval run: what the scores were, what went wrong, and what changed next.
Scores are never changed after a run, and the correct answers are never changed after the tool has seen the samples.

## Run 1 — baseline (2026-10-20)

Report: [`runs/2026-10-20_baseline/report.md`](runs/2026-10-20_baseline/report.md) · Model: `claude-sonnet-5-5` · Prompt: as of commit `d29b642`

| Metric | Result | Target |
|---|---|---|
| Recall (all types) | 97% (66 of 68) | — |
| Recall on risks, issues, dependencies, actions | 96% | 85% or more ✅ |
| Precision (all types) | 99% (66 of 67) | 80% or more ✅ |
| Invented owners or dates | 0 | 0 ✅ |
| Guessed owners (owner given where the notes name nobody) | 2 | — |
| Cost and time, 10 samples | $0.09, 38 s | — |

### What went wrong

| # | Sample | Finding | Cause | Tool error? |
|---|---|---|---|---|
| 1 | s02 | Missed the action "Ask the CRM vendor about raising the import limit" | The action has no owner in the notes, and the tool skipped it | Yes |
| 2 | s01, s03 | Owner given to a dependency (Daniel Kim) and an assumption (Priya Raman) | The tool used the person who spoke as the owner, against the prompt rule | Yes |
| 3 | s08 | Due date 2027-01-11 on the laptop dependency; the answer says "Not stated" | The date is the graduates' start date, a fair deadline for the dependency | Debatable — counted as an error, answer not changed |
| 4 | s07 | Claire's action counted as one miss plus one extra item | The tool found it with the correct owner, but quoted the reply ("Yes, I'll do it right after this call.") instead of the request, so the quote-based matching did not connect them | No — a limit of the eval matching. The quote is also less useful to a reader |

### Planned change (story S2-06, KAN-20)

One round of prompt changes aimed at findings 1, 2, and 4:

1. Record every task that someone must do, even when the notes name no owner.
2. The owner of a risk, assumption, issue, dependency, or decision is "Not stated" unless the notes give that item to a person. The speaker is not the owner.
3. For an action agreed in two turns (a request and a "yes"), quote the request that names the task.

Rule: the change stays only if the scores are better than this baseline.
