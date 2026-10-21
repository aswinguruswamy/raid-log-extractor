# Project RAID log

The RAID log of this project itself, kept in the same six types that the tool extracts. It starts from the risks and assumptions in the charter (approved 2026-10-20) and records what happened to each one.

**Last update:** 2026-10-21 · **Owner:** Aswin Guruswamy · **Bugs:** see [`corrective-actions.md`](corrective-actions.md) and Jira (issue type Bug)

## Risks

| # | Risk (from the charter) | Owner | Status | What happened |
|---|---|---|---|---|
| R1 | Recruiters do not open the repository, or leave it in seconds | Aswin Guruswamy | Open (watched for 3 months) | Live demo link and GIF at the top of the README. Measured by the reach tracker after release |
| R2 | Users send notes with confidential client data to a third-party API | Aswin Guruswamy | Mitigated | Privacy note in the README and on the page; the page stores no notes and no key; name removal is in the 1.1 backlog (L-01) |
| R3 | The model invents owners or dates | Aswin Guruswamy | Closed | "Not stated" rule, source quotes, and a word-for-word quote check. Eval run 2: 0 invented owners or dates, 0 guessed owners |
| R4 | The eval set is too small, or the labels have bias | Aswin Guruswamy | Open (accepted for v1.0) | 10 samples, answers committed before the first run. The prompt was tuned on the same samples. Held-out set planned (L-06, KAN-38) |
| R5 | Scope grows (for example, a Jira sync) | Aswin Guruswamy | Closed | Change control held: no new scope; the Markdown export (Could) moved to 1.1 |
| R6 | An API key goes into the repository | Aswin Guruswamy | Closed | `.env` in `.gitignore`; release gate: 0 keys in the Git history; no key on the public site |
| R7 | A new package release breaks the live demo (found in the audit) | Aswin Guruswamy | Mitigated | Tested version ranges in `requirements.txt` (BUG-22); CI runs the tests on each push |
| R8 | The free Streamlit site sleeps when nobody visits it | Aswin Guruswamy | Open (accepted) | The first visitor waits about 30 seconds. Open the site before an interview or an application |

## Assumptions

| # | Assumption (from the charter) | Status | Result |
|---|---|---|---|
| A1 | The notes are in English and name the people in the call | Held | True for all 10 samples; other languages are in the 1.1 backlog (L-04) |
| A2 | A manual RAID log takes 20 to 40 minutes for each call | Partly checked | 6 to 8 minutes for 3 short samples (about 150 words each). A full 1-hour call was not timed |
| A3 | Sample notes with no real data are enough to show the quality | Held, with a limit | Enough for a portfolio demo. The samples were written with AI help and are cleaner than real notes |
| A4 | Users of their own notes have a Claude API key | Held | The page asks for the user's own key and explains why |
| A5 | Streamlit Community Cloud hosts the demo at no cost | Held | Live at no cost since 2026-10-20 |

## Issues

| # | Issue | Owner | Status |
|---|---|---|---|
| I1 | 22 bugs found during the build (BUG-01 to BUG-22), plus 1 accepted mismatch (BUG-23) | Aswin Guruswamy | See [`corrective-actions.md`](corrective-actions.md) |
| I2 | Jira timed out or was unavailable for some calls on 2026-10-21 | Aswin Guruswamy | Worked around: each change was checked with a search, then done again where needed |

## Dependencies

| # | Dependency | Used for | Risk if it fails |
|---|---|---|---|
| D1 | Anthropic API (`claude-sonnet-5-5`) | Extraction in "Your own notes" mode and in the evals | No new extractions; the demo mode still works (saved results) |
| D2 | Streamlit Community Cloud | The live demo | No live demo; the code still runs on a computer |
| D3 | GitHub | Code, CI, releases | No public repository |
| D4 | Jira (KAN project) | Backlog, sprints, bugs | Tracking only; no effect on the tool |

## Actions

| # | Action | Owner | Due date | Status |
|---|---|---|---|---|
| AC1 | Time the review of the tool's log on s02, s05, and s07 (value metric) | Aswin Guruswamy | 2026-10-26 | Open |
| AC2 | Publish the GitHub release v1.0.0 | Aswin Guruswamy | 2026-10-26 | Open |
| AC3 | Add the project to the LinkedIn profile (Projects section) | Aswin Guruswamy | 2026-10-27 | Open |
| AC4 | Write and approve the one-page case study | Aswin Guruswamy | 2026-10-27 | Open |
| AC5 | Do the retrospective | Aswin Guruswamy | 2026-10-28 | Open |
| AC6 | Update the reach tracker each month | Aswin Guruswamy | 2027-01-27 | Open |

## Decisions

The product decisions, with their trade-offs, are in [`product-decisions.md`](product-decisions.md). Project decisions:

| Date | Decision |
|---|---|
| 2026-10-20 | Solo project; the schedule moved to three 2-day sprints (Oct 20–25) with extra hours |
| 2026-10-20 | Jira is the system of record for the backlog, sprints, and bugs |
| 2026-10-21 | The Markdown export (Could) moved to version 1.1 |
| 2026-10-21 | Release gate passed: release version 1.0, not 0.9 beta |
| 2026-10-21 | No LinkedIn release post; the project goes into the LinkedIn profile instead |
| 2026-10-21 | The Git history is not rewritten (BUG-21, BUG-23) |
