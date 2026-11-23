# Changelog

All notable changes to this project. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the version numbers follow [Semantic Versioning](https://semver.org/).

## [2.0.0] - Unreleased (set the date at the release review)

Hard cases right, proved on a held-out set (spec v1.2).

### Added

- Owner states (Confirmed, Tentative, Not confirmed, Declined, Not stated) and owner notes ("ask Tom", "not on the call", "owners by list – confirm", "withdrawn").
- Prompt 2.1: decisions need agreement words; proposals, hypotheticals and reversed or pending decisions give no decision; negations and status updates give no item; instructions inside the notes are treated as notes.
- Dates from code: the model copies the date words; the code converts them with the meeting date.
- Code checks before display: owner not in the notes, owner or date far from the quote, date words not in the notes, duplicates, owner from a one-word reply.
- Needs attention box; one table (Type · Item · Owner · Due date · Reviewed); quote of any item; Markdown download with run details and quotes; meeting date input; input warnings; privacy warning; Teams and Zoom export guide.
- Eval v2: invented and wrong owners and dates, owner-state accuracy, 5-run consistency; spec examples in CI; CI fails a prompt change on any invented owner or date.
- Held-out set: 28 calls, one per hard case, keys approved by Aswin Guruswamy before the run. Result (28 × 5): recall 95%, precision 99%, 0 invented owners, 0 invented dates. Release gate passed.
- Keyless demo with saved v2 results; `?demo=<call>` opens one sample; README screenshots of 2 demo calls (no video).

### Changed

- An answer cut off at the output limit is an error with no log (v1: a warning).
- Python 3.11 or later; anthropic SDK 2.x.

### Removed

- The Excel export (the Markdown file replaces it).

## [1.0.0] - 2026-10-21

The first public release. It passed the release gate in [`docs/release-gate-v1.0.md`](docs/release-gate-v1.0.md).

### Added

- Extraction of six item types (risks, assumptions, issues, dependencies, actions, decisions) with Claude tool use and a JSON schema.
- A source quote for every item, checked word for word against the notes.
- "Not stated" when the notes give no owner or no full date.
- Input: .txt, .docx (with tables), and Teams or Zoom .vtt transcripts.
- Excel export: a Summary sheet, one sheet for each type, a Status dropdown, and filters.
- Command line: `python -m raid extract <notes>`, with the tokens, the cost, and the time of each run.
- Streamlit web page: a demo mode with no API key, and a "Your own notes" mode with the user's own key.
- Eval: 10 sample calls, 68 correct answers committed before the first run, and a scoring script. Run 2: 100% recall and 100% precision.
- CI: offline tests on Python 3.9 and 3.12 on each push.
- Documents: product decisions, eval findings, the corrective action log, the project RAID log, and the release gate.

### Fixed before the release

- 22 bugs fixed and 1 mismatch accepted, each with a root cause. See [`docs/corrective-actions.md`](docs/corrective-actions.md).

### Known limits

- The prompt was tuned on the same 10 samples that the eval uses. A held-out eval set is planned for 1.1.
- English only, and one call at a time.
- The public demo shows 3 fixed samples. New notes need the user's own API key.

### Planned for 1.1

- A held-out eval set (KAN-38).
- A Markdown export (KAN-27).
