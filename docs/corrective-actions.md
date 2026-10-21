# Corrective action log

Every bug and mismatch found in the project, from the first live test to the release audit. Each entry has the root cause, the fix, the evidence, and the step that stops the problem from coming back.

- **System of record:** Jira (issue type Bug, KAN-39 to KAN-60). Each bug links to the story where it was found.
- **Rule:** a bug closes only when the fix is verified. The commit ids below are on the `main` branch.
- **Severity:** High = wrong output, privacy, or cost risk for the user. Medium = a visible defect or a gap in the evidence. Low = a cosmetic or process defect.

## Summary

| Status | High | Medium | Low | Total |
|---|---|---|---|---|
| Fixed | 6 | 7 | 4 | 17 |
| Open (release backlog) | 0 | 2 | 3 | 5 |
| **Total** | **6** | **9** | **7** | **22** |

| Where the bugs were found | Count |
|---|---|
| Live tests and real use on the Mac | 4 (BUG-01, 02, 03, 13) |
| Eval runs | 3 (BUG-04, 05, 06) |
| Page reviews with screenshots | 5 (BUG-09 to 12, 16) |
| Project reviews and the SOP audit | 10 (BUG-07, 08, 14, 15, 17 to 22) |

## Fixed

| Bug | Jira | Sev. | Found in | Problem | Root cause | Fix and evidence | Prevention |
|---|---|---|---|---|---|---|---|
| BUG-01 | KAN-39 | High | KAN-9 live test | Claude API rejected a forced `tool_choice` (HTTP 400) | The model does not accept a forced tool call; the offline tests used a fake client | `tool_choice: auto`, a prompt rule, and one retry (`2a7e579`); 5 of 5 live tests passed | Run the live tests before an API story is Done |
| BUG-02 | KAN-40 | High | KAN-8, Mac | Import error on Python 3.9 (`bool \| None`) | Built and tested on Python 3.13 only | `Optional[bool]` (`aac01bb`); 61 tests pass on 3.9 | Test on the lowest Python version (CI) |
| BUG-03 | KAN-41 | Medium | KAN-9 criterion | The "1-hour transcript" test text was too short | Word count not checked | 43 copies, at least 9,000 words; live run $0.0461, 5.2 s | Put test-data sizes in the criterion as numbers |
| BUG-04 | KAN-42 | High | Eval run 1 | Missed an action with no owner (s02) | The prompt defined an action by its owner | Prompt v2 rule 2 (`a7ec47b`); run 2 recall 100% | Keep the ownerless sample in the eval set |
| BUG-05 | KAN-43 | High | Eval run 1 | The speaker was recorded as the owner (s01, s03) | No owner rule for non-action items | Prompt v2 rule 3 (`a7ec47b`); run 2: 0 guessed owners | The eval counts guessed owners |
| BUG-06 | KAN-44 | Medium | Eval run 1 | A two-turn action quoted the "yes" reply (s07) | No rule for which turn to quote | Prompt v2 rule 6 (`a7ec47b`); run 2 precision 100% | Keep two-turn actions in the eval set |
| BUG-07 | KAN-45 | Low | KAN-17 | Manual times typed in the wrong column | Unclear hint text in the workbook | Times read from column C and confirmed (`8897043`) | Label and colour every input cell |
| BUG-08 | KAN-46 | Medium | KAN-20 | Eval run 2 outputs not committed | Run steps had no commit step | Commit `1013d87`; run folder matches the outputs | End every run instruction with commit and push |
| BUG-09 | KAN-47 | High | KAN-21 | Results disappeared after the Excel download (a second paid call to see them again) | Streamlit reruns the page; no session state | Result kept in `st.session_state` (`373c3ba`); browser test: 1 API call for each run | Test every button in a browser |
| BUG-10 | KAN-48 | Medium | KAN-21 | Long quotes cut off in the table | `st.dataframe` does not wrap | `st.table` (`446ab1b`); screenshots on a computer and a phone | Check a screenshot of each page change |
| BUG-11 | KAN-49 | Low | KAN-22 | Demo label said "Zoom" for a Teams transcript | Labels typed by hand | Demo set s01/s02/s05, labels checked (`373c3ba`) | Check labels against the source files |
| BUG-12 | KAN-50 | Low | KAN-21 | Upload box said 200 MB; the page accepts 2 MB | Streamlit default not changed | `maxUploadSize = 2` (`373c3ba`) | One limit, linked by a comment |
| BUG-13 | KAN-51 | Medium | KAN-21, live site | "$" amounts showed as a maths formula | Markdown reads `$...$` as LaTeX | Escape "$" (`1f2db4a`) and a new test | The test stays in the suite |
| BUG-14 | KAN-52 | Medium | Review | README clone URL was a placeholder | Stub never checked again | Real URL and full quick start (`b837ee2`) | The release gate runs the README steps |
| BUG-15 | KAN-53 | Medium | Review | `.gitignore` did not block the personal workbook | Covered secrets, not personal files | `samples/*.xlsx`, `.pytest_cache/` (`b837ee2`) | The release gate checks the tracked files |
| BUG-16 | KAN-54 | High | KAN-25 | Demo recording showed personal file names in the save window | No warning in the recording steps | Part cut, button cropped (`99a4f8a`); 168-frame scan clean | Save downloads without a prompt; check every frame |
| BUG-17 | KAN-55 | Low | Review | Epics stayed in To Do after all stories were Done | No epic step in the workflow | Epics closed on Oct 20 and 21 | Close the epic with its last story |

## Open (fix before the GitHub release)

| Bug | Jira | Sev. | Problem | Root cause | Planned fix | Owner |
|---|---|---|---|---|---|---|
| BUG-18 | KAN-56 | Low | Excel "Quote checked" and page "Quote found" do not match | Page column renamed, Excel column not | Rename in `raid/export.py`; tests (M3) | Claude |
| BUG-19 | KAN-57 | Medium | Charter does not match the project as built (6 points) | No change record against the approved baseline | Correct the charter, add a change log and actual dates (M1); measure the value metric (Y1) | Claude, Aswin |
| BUG-20 | KAN-60 | Low | Backlog document statuses do not match Jira | Jira became the system of record without a note | Update the document (M2) | Claude |
| BUG-21 | KAN-58 | Low | Mac commits show the author "aswingurswamy" | Typo in Git `user.name` on the Mac | `git config --global user.name "Aswin Guruswamy"`; old commits stay, because their ids are in Jira and the docs | Aswin |
| BUG-22 | KAN-59 | Medium | Package versions not pinned; a new release can break the live demo | No tested versions recorded | Pin the tested versions; test on 3.9 and 3.12 (M4) | Claude |

## Lessons for the next project

1. **Test against the real service early.** The fake client hid BUG-01 until the first live run.
2. **Test on the user's platform.** BUG-02 appeared only on the Mac.
3. **Look at the output, not only the tests.** The tests passed for BUG-09, 10, 12, and 16. Screenshots and a frame check found them.
4. **Keep the baseline documents alive.** BUG-19 and BUG-20 came from approved documents that nobody updated after a change.
5. **Check privacy before anything goes public.** BUG-15 and BUG-16 were found before publication because a check step existed.
