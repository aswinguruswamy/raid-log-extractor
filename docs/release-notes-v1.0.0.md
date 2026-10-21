# RAID Log Extractor v1.0.0

Turn the notes from a team call into a RAID log in less than one minute.

**[Try the live demo](https://raid-log-extractor.streamlit.app/)**: no sign-in and no API key.

## What it does

The tool reads call notes or a transcript (.txt, .docx, Teams or Zoom .vtt) and finds risks, assumptions, issues, dependencies, actions, and decisions. Each item has an owner, a due date, a status, and a source quote from the notes. The code checks every quote word for word, and the tool writes "Not stated" instead of a guess. The result downloads as an Excel file.

## Results

| Metric | Target | Result |
|---|---|---|
| Recall on risks, issues, dependencies, actions | 85% or more | 100% |
| Precision on all item types | 80% or more | 100% |
| Invented owners or dates | 0 | 0 |
| Cost for a 1-hour transcript (Sprint 1 live test) | less than $0.10 | $0.046 |
| Time for a 1-hour transcript (Sprint 1 live test) | less than 60 s | 5.2 s |

Eval set: 10 sample calls with 68 expected items, model `claude-sonnet-5-5`. The correct answers were committed before the first tool run.

## Known limits

- The prompt was tuned on the same 10 samples that the eval uses, so new notes may score lower. A held-out eval set is the first item for 1.1.
- The samples were written with AI help and are cleaner than real notes.
- English only, and one call at a time.

## Quality record

- 22 bugs fixed and 1 mismatch accepted during the build, each with a root cause: [`docs/corrective-actions.md`](https://github.com/aswinguruswamy/raid-log-extractor/blob/main/docs/corrective-actions.md)
- Release gate, 15 checks on a fresh clone: [`docs/release-gate-v1.0.md`](https://github.com/aswinguruswamy/raid-log-extractor/blob/main/docs/release-gate-v1.0.md)
- Product decisions and trade-offs: [`docs/product-decisions.md`](https://github.com/aswinguruswamy/raid-log-extractor/blob/main/docs/product-decisions.md)

Full list of changes: [`CHANGELOG.md`](https://github.com/aswinguruswamy/raid-log-extractor/blob/main/CHANGELOG.md)
