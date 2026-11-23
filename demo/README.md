# Demo data

Saved v2 results for 4 sample calls from the held-out run (run 1, prompt 2.1, model `claude-sonnet-5-5`). The web page uses these files in demo mode, so a visitor can see the v2 table, Needs attention and the Markdown download with no API key and no API call.

| File | What it shows |
|---|---|
| `h01_warehouse_scanners.json` | A reply that does not commit, and dates from weekdays |
| `h02_website_redesign.json` | A weak yes: tentative owner |
| `h03_mobile_release.json` | A refusal: declined owner |
| `h12_clinic_scheduling.json` | A task given to someone not on the call |

The notes are in `evals/heldout/calls/`. Rebuild the files with `python scripts/make_demo.py` (no API call: it reads the saved run and redoes the code checks).
