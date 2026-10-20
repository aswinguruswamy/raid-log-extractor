# Evaluation report

**Samples:** 10 | **Expected items:** 68 | **Model:** claude-sonnet-5-5 | **Run date:** 2026-10-20 | **Report date:** 2026-10-20

## Scores by item type

| Type | Expected | Found by tool | Recall | Precision |
|---|---|---|---|---|
| Risk | 9 | 9 | 100% | 100% |
| Assumption | 9 | 9 | 100% | 100% |
| Issue | 10 | 10 | 100% | 100% |
| Dependency | 9 | 9 | 100% | 100% |
| Action | 22 | 22 | 100% | 100% |
| Decision | 9 | 9 | 100% | 100% |
| **All** | **68** | **68** | **100%** | **100%** |

## Charter targets

| Metric | Target | Result | Met |
|---|---|---|---|
| Recall on risks, issues, dependencies, actions | 85% or more | 100% | ✅ |
| Precision on all item types | 80% or more | 100% | ✅ |
| Owners or dates that the tool invents | 0 | 0 | ✅ |

## Owners and dates (on matched items)

| Check | Result |
|---|---|
| Correct owner | 21 of 21 (100%) |
| Correct due date | 11 of 11 (100%) |
| Owner given where the notes name nobody | 0 |
| Owner not in the notes at all (invented) | 0 |
| Date not in the notes at all (invented) | 0 |

## Cost and time

All 10 samples: $0.0960 in total, 38.6 s in total (average $0.0096 and 3.9 s for each sample).

## Manual baseline (story S2-03, KAN-17)

| Sample | Manual RAID log | Tool run |
|---|---|---|
| s02_crm_migration.txt | 8 min | 4.9 s |
| s05_erp_steering.docx | 6 min | 4.1 s |
| s07_cloud_migration.vtt | 6 min | 3.7 s |

Manual times were measured on 2026-10-20 (s02: 17:32-17:40, s05: 17:46-17:52, s07: 17:57-18:03). These samples are short (about 140-160 words). Notes from a 1-hour call are much longer, so the manual time for a real call is higher. The charter's assumption of 20-40 minutes for a full call is not yet measured.

## Details by sample

**s01_mobile_release.vtt** — expected 7, found 7, matched 7

**s02_crm_migration.txt** — expected 8, found 8, matched 8

**s03_payroll_vendor.vtt** — expected 7, found 7, matched 7

**s04_office_move.txt** — expected 7, found 7, matched 7

**s05_erp_steering.docx** — expected 8, found 8, matched 8

**s06_holiday_campaign.txt** — expected 7, found 7, matched 7

**s07_cloud_migration.vtt** — expected 7, found 7, matched 7

**s08_graduate_onboarding.docx** — expected 7, found 7, matched 7

**s09_audit_prep.txt** — expected 8, found 8, matched 8

**s10_standup.vtt** — expected 2, found 2, matched 2

## How to read this report

- **Recall:** of the items that are in the notes, the share that the tool found with an accepted type.
- **Precision:** of the items that the tool reported, the share that are correct.
- **Matching:** a tool item matches an expected item when its source quote shares most of its words with the expected evidence (see `raid/evaluate.py`).

## Known limits

- 10 samples and 68 expected items: the scores show a direction, not a statistical proof.
- The samples and the correct answers were written with AI help (Claude), and the tool also uses Claude. This can make the samples easier for the tool than real notes.
- The correct answers were committed before the tool ran on the samples (see the Git history).
