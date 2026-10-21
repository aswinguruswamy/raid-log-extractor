# Release gate: version 1.0 (story R-01, KAN-28)

**Date:** 2026-10-21 · **Commit checked:** `99a4f8a` · **Method:** a fresh clone from GitHub, new virtual environments, no files from the build machine.

## Charter rule

- Recall 85% or more on risks, issues, dependencies, and actions, and 0 invented owners or dates: release **v1.0**.
- If not: release **v0.9 beta**.

## Result: PASS, release v1.0

| # | Check | Result |
|---|---|---|
| 1 | Recall on risks, issues, dependencies, actions (target 85% or more) | 100% ✅ |
| 2 | Precision on all item types (target 80% or more) | 100% ✅ |
| 3 | Invented owners or dates (target 0) | 0 ✅ |
| 4 | Fresh install and offline tests on Python 3.9 (Streamlit 1.50) | 61 passed ✅ |
| 5 | Fresh install and offline tests on Python 3.12 (Streamlit 1.66, as on Streamlit Cloud) | 61 passed ✅ |
| 6 | Eval re-scored from the saved outputs | Same scores; only the report date changes ✅ |
| 7 | Command line: help text, and a clear error with exit code 2 when no API key is set | ✅ |
| 8 | Relative links in all Markdown files | 0 broken ✅ |
| 9 | API keys in the Git history | 0 ✅ |
| 10 | Personal or secret files in the repository (.env, .xlsx, .mov) | 0 ✅ |
| 11 | Names in the samples | All invented ✅ |
| 12 | Live demo in a private browser window: no sign-in, 3 samples, Excel download | Checked by the owner on 2026-10-21 ✅ |
| 13 | Live API test of the web page (own notes, s02) | 8 of 8 items, checked on 2026-10-20 ✅ |
| 14 | README: demo link and GIF at the top; problem, quick start, eval, privacy | ✅ |
| 15 | MIT license | ✅ |

## Known limits that go into the release notes

- The prompt was tuned on the same 10 samples that the eval uses. A held-out set is the first item for version 1.1 (KAN-38).
- The samples and answers were written with AI help, and the tool also uses Claude.
- The demo shows 3 fixed samples. New notes need the user's own API key.
- English only. One call at a time.

## Scope change

- KAN-27 (Markdown export, a Could story) moved to the version 1.1 backlog on 2026-10-21.
