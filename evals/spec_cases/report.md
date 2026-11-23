# Evaluation report

**Samples:** 13 | **Expected items:** 15 | **Model:** claude-sonnet-5-5 | **Run date:** 2026-11-23 | **Report date:** 2026-11-23

## v2 scores (spec R15.1)

**Set:** spec | **Calls:** 13 | **Runs per call:** 1 | **Prompt version:** 2.1 | **Calls written by:** Spec v1.1 acceptance examples (AC1–AC11, AC16, AC28), written by Claude (AI), approved with the spec by Aswin Guruswamy

| Metric | Result |
|---|---|
| Recall | 100% |
| Precision | 100% |
| Invented owners (release gate: 0) | 0 |
| Invented dates (release gate: 0) | 0 |
| Wrong owners | 0 |
| Wrong dates | 0 |
| Owner state correct | 15 of 15 |
| Items found in all 1 runs | - |
| Owner the key forbids (release gate: 0) | 0 |
| Extra items with an owner or a date (check by hand) | 0 |


## Scores by item type

| Type | Expected | Found by tool | Recall | Precision |
|---|---|---|---|---|
| Risk | 1 | 1 | 100% | 100% |
| Assumption | 0 | 0 | - | - |
| Issue | 0 | 0 | - | - |
| Dependency | 1 | 1 | 100% | 100% |
| Action | 12 | 12 | 100% | 100% |
| Decision | 1 | 1 | 100% | 100% |
| **All** | **15** | **15** | **100%** | **100%** |

## Charter targets

| Metric | Target | Result | Met |
|---|---|---|---|
| Recall on risks, issues, dependencies, actions | 85% or more | 100% | ✅ |
| Precision on all item types | 80% or more | 100% | ✅ |
| Owners or dates that the tool invents (v2 definitions) | 0 | 0 | ✅ |

## Owners and dates (on matched items)

| Check | Result |
|---|---|
| Correct owner | 9 of 9 (100%) |
| Correct due date | 1 of 1 (100%) |
| Owner given where the notes name nobody | 0 |
| Owner not in the notes at all (v1 check) | 0 |
| Date not written as YYYY-MM-DD in the notes (v1 check; v2 converts date words) | 1 |

## Cost and time

All 13 call runs: $0.0963 in total, 25.1 s in total (average $0.0074 and 1.9 s for each call run).

## Manual baseline (story S2-03, KAN-17)

| Sample | Manual RAID log | Tool run |
|---|---|---|
| s02_crm_migration.txt | 8 min | - |
| s05_erp_steering.docx | 6 min | - |
| s07_cloud_migration.vtt | 6 min | - |

Manual times were measured on 2026-10-20 (s02: 17:32-17:40, s05: 17:46-17:52, s07: 17:57-18:03). These samples are short (about 140-160 words). Notes from a 1-hour call are much longer, so the manual time for a real call is higher. The charter's assumption of 20-40 minutes for a full call is not yet measured.

## Details by sample

**ac01_weak_yes.txt** — expected 1, found 1, matched 1

**ac02_refusal.txt** — expected 1, found 1, matched 1

**ac03_no_reply.txt** — expected 1, found 1, matched 1

**ac04_non_committal.txt** — expected 2, found 2, matched 2

**ac05_self_commitment.txt** — expected 1, found 1, matched 1

**ac06_owners_by_list.txt** — expected 3, found 3, matched 3

**ac07_hand_off.txt** — expected 1, found 1, matched 1

**ac08_not_on_call.txt** — expected 1, found 1, matched 1

**ac09_proposal.txt** — expected 0, found 0, matched 0

**ac10_decision.txt** — expected 1, found 1, matched 1

**ac11_vp_approval.txt** — expected 1, found 1, matched 1

**ac16_changed_date.txt** — expected 1, found 1, matched 1

**ac28_injection.txt** — expected 1, found 1, matched 1

## How to read this report

- **Recall:** of the items that are in the notes, the share that the tool found with an accepted type.
- **Precision:** of the items that the tool reported, the share that are correct.
- **Matching:** a tool item matches an expected item when its source quote shares most of its words with the expected evidence (see `raid/evaluate.py`).

## Known limits

- 13 samples and 15 expected items: the scores show a direction, not a statistical proof.
- The samples and the correct answers were written with AI help (Claude), and the tool also uses Claude. This can make the samples easier for the tool than real notes.
- The correct answers were committed before the tool ran on the samples (see the Git history).
