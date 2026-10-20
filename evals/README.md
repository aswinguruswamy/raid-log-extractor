# Evaluation

The correct answers for each sample and the eval script (stories S2-02 and S2-04, KAN-16 and KAN-18).

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
