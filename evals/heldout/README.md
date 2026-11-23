# Held-out set

28 new sample calls, one for each P1 case of the failure catalogue (RAID v2 spec R13.1). They are never used to tune the prompt (R13.3).

- `calls/` – the call notes (invented names, no real data).
- `answers/` – the answer key for each call: the case it tests, the meeting date, the writer, and the expected items with owner, owner state, owner note, due date and date words.

Rules (spec R13.2, AC39):
- Claude drafts each call and key; Aswin Guruswamy approves each key.
- The keys are committed in their own commit, before any held-out run. `evals/heldout_rules.py` checks this order.
- Key rules agreed at approval: a date said for a task stays when the owner is not confirmed; a dependency with a date gets that date.
