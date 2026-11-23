# RAID v2 – Requirements

Version 1.4 · 2026-11-23 · Status: **APPROVED by Aswin Guruswamy, 2026-11-22** (v1.1–v1.3 = his output and demo decisions, same day; v1.4 = screenshots in place of a video, 2026-11-23)

---

## 1. What RAID v2 is

A free tool that turns the notes from a project call into a **RAID log you can trust**, in under a minute.
v1 already does this, and it scores 100% on its 10 sample calls. But the prompt was tuned on those same 10 calls, so the score does not prove much.
v2 has two jobs:
1. **Get the hard cases right:** who really agreed to an action, what was only proposed, and which dates are real.
2. **Prove it** on new test calls that the tool was never tuned on.

**Pick one line for the README and the demo** (or write your own):
1. "A RAID log from your call notes – every item backed by a quote the code checked."
2. "The AI RAID log that writes 'Not stated' instead of guessing – and proves it."
3. "Call notes to RAID log in a minute, tested on calls it has never seen."

## 2. Who uses it, and the problem

**User:** a PM who runs project calls and must keep a RAID log current.

**Problem:** writing the log by hand takes 6–8 minutes for a short call, and items get lost. AI meeting tools are fast, but they invent owners, treat a proposal as a decision, or credit a task to the wrong person. Most give no proof, so the PM must check every row again.

## 3. How a PM uses it

1. **Upload** the call notes (.txt, .docx, or a Teams or Zoom transcript) and **enter the meeting date**.
2. **Read "Needs attention" first:** items with an unclear owner, a tentative "I'll try", or a missing date.
3. **Scan the table:** one row per item – **Type · Item · Owner · Due date · Reviewed ☐**. The owner shows its state, for example "Aiko (tentative)". The item shows ✓ when the code found the quote. Tick **Reviewed** after you check a row.
4. **Download** the Markdown file (reviewed rows marked ✓).

## 4. What changes from v1

| | v1 (today) | v2 |
|---|---|---|
| 6 item types, quote checked word for word | ✅ | ✅ same |
| "Not stated" in place of a guess | ✅ | ✅ same |
| Owner | A name or "Not stated" | **Owner state:** Confirmed · Tentative · Not confirmed · Declined · Not stated |
| "Can you do X?" → "Maybe" | Owner = that person | **Tentative** – shows in Needs attention |
| Proposal ("we could use X") | Can become a Decision | **Not a decision** without agreement words |
| "By Friday" | Model guesses the date | **Meeting date** in; date shown with the original words |
| Code checks | Quote only | Quote **+ owner + date + duplicates** |
| Long notes cut off | Can lose items silently | **Error** – never a partial log |
| Test score | 100% on the tuning samples | Score on **28 new test calls**, published with its limits |
| Output | Excel, one sheet per type | **Table on the page** + Needs attention + **Markdown download** (Excel removed) |
| Run details | Not recorded | Model, prompt version, run date in the output |

## 5. Benefits

| For | Benefit |
|---|---|
| The PM | **Trust the owner column**: "Tentative" and "Not confirmed" are flagged, not hidden. |
| The PM | Read only "Needs attention" – check 3 items, not 30. |
| The PM | Real dates from "by Friday", with the original words beside them. |
| The team | No one gets an action they never accepted. |
| Recruiters | An AI tool with an **honest, independent test score** and a catalogue of 66 failure cases – rare in AI demos. |

## 6. What it does (functional requirements)

Priority is my proposal. **You decide.** M = Must, S = Should.

### Get the hard cases right
| # | Requirement | Priority |
|---|---|---|
| R1 | Give each owner a state: **Confirmed** (clearly accepts), **Tentative** ("I'll try"), **Not confirmed** (asked, no clear yes), **Declined**, **Not stated**. | M |
| R2 | The speaker owns an action only when they say "I will…". A "yes" makes the person who was asked the owner. Never map people to tasks by list order or by guess. | M |
| R3 | A proposal is a Decision only with agreement words ("agreed", "decided", "let's go with"). | M |
| R4 | Take the meeting date as input. Turn "by Friday" into a date, and keep "by Friday" beside it. | M |
| R5 | Check in code: the owner's name is in the notes; the owner (or the reply) is in or next to the quote; the date or its words are in the notes; no item appears twice. | M |
| R6 | A cut-off answer is an error, never a partial log. Warn when the notes are very long, not in English, or have no speaker names. | M |

### Output
| # | Requirement | Priority |
|---|---|---|
| R7 | Show a **Needs attention** box first: tentative, not confirmed or declined owners, missing dates, and warnings. | M |
| R8 | Show the log as one table on the page: **Type · Item · Owner · Due date · Reviewed**. Owner shows the state in brackets unless confirmed ("Aiko (tentative)"). Item shows ✓ when the code found the quote (click ✓ to see it). Reviewed = a checkbox the PM ticks after checking the row. | M |
| R9 | Download the table as Markdown, with Needs attention and run details; reviewed rows marked ✓, the others "not reviewed". Excel export is removed. | M |
| R10 | Write the model, prompt version, run date and source file name into every output. | M |
| R11 | Warn before upload that the notes go to the Anthropic API. | M |
| R12 | A short guide: how to export a transcript from Teams or Zoom. | S |

### Proof
| # | Requirement | Priority |
|---|---|---|
| R13 | Build a **held-out test set**: 28 new sample calls, one per hard case in the failure catalogue. Claude drafts each call and its answer key; Aswin checks and approves every answer key **before** the first run. The set is never used to tune the prompt. **Limit:** Claude also runs the tool, so the README says who wrote the test calls. | M |
| R14 | Also test: same call 5 times → same items; calls with hidden instructions → ignored. | M |
| R15 | Publish the held-out score as it is, beside the tuning score, with its limits. | M |
| R16 | Run the AI test automatically on each change to the prompt, the checks or the model. | M |

### Quality (shared standard)
| # | Requirement | Priority |
|---|---|---|
| R17 | Shared CI: tests on Python 3.11–3.13, lint, secret scan, pinned actions, Dependabot, dependency and licence scans. | M |
| R18 | Release workflow: tag → tests → build → release notes. | M |
| R19 | "Known limits" at the top of the README. Every bug gets a test (and a test call) before the fix. | M |
| R20 | Show 2–3 screenshots of the keyless v2 demo in the README (the table with Needs attention, the quote of an item, and an owner state), with links that open the demo. No video. The public demo stays keyless (saved results). | M |

## 7. How well it must work (non-functional requirements)

| # | Area | Requirement |
|---|---|---|
| N1 | Honesty | **0 invented owners or dates** on the held-out set. This is the release gate. Recall and precision are published as measured, with no pass bar. *(proposed – confirm)* |
| N2 | Evidence | Every item has a quote that the code found word for word in the notes. |
| N3 | Speed | A log for a 30-minute call in under 60 seconds. |
| N4 | Cost | About US$0.01–0.02 per call. The automatic AI test costs less than US$1 per run. *(proposed – confirm)* |
| N5 | Privacy | No notes or keys are stored. The warning shows before upload. The demo needs no key. The README states what the demo host (Streamlit) logs. |
| N6 | Plain language | Errors say what happened and what to do. |
| N7 | Accessibility | "Not found" and owner states show as words or icons, never colour only. |

## 8. Not in v2 (later, if RAID becomes popular)

- Excel or CSV export (v1 had Excel).
- A running log: merge a new call into an existing log.
- Push items to Jira or Confluence.
- Risk scoring (likelihood × impact).
- Several calls in one run.
- A team roster for role-based owners.
- Splitting very long calls into parts (v2 stops with an error).
- RAID risks into SRG.
- Other languages; a second "judge" model; per-row feedback; an installable package.
- Public meeting corpora (AMI, ICSI) as test data – licence checks first.

## 9. Sign-off

| | |
|---|---|
| Comments | None ("Approve as is") |
| Decision | ☑ Approved ☐ Approved with changes ☐ Rejected |
| Signed | Aswin Guruswamy · 2026-11-22 (in chat) |
| Note | Positioning line not picked yet. Proposed numbers (N1, N4) and the test-set plan accepted as written. |

## Change log
| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-11-22 | First draft, from the RAID analysis (failure catalogue, rules, DL1–DL4, I1–I9), the v1 README and the shared decisions |
| 1.0 | 2026-11-22 | Approved as is by Aswin. No content change. |
| 1.4 | 2026-11-23 | Aswin 2026-11-23 (SH-5.5): README screenshots in place of the video (R20). |
| 1.3 | 2026-11-22 | Aswin: AI key only for the build; demo stays keyless; a recorded video (R20). |
| 1.2 | 2026-11-22 | Aswin: drop the Confidence column; owner state goes in the Owner cell, quote ✓ in the Item cell. |
| 1.1 | 2026-11-22 | Aswin: Excel is outdated. Output = table on the page (Type, Item, Owner, Due date, Confidence, Reviewed) + Markdown download. R8, R9 now Must. |
