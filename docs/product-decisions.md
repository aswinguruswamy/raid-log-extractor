# Product decisions

This file records the main design choices and their trade-offs (story S3-06, KAN-26).

| Date | Decision | Why | Trade-off |
|---|---|---|---|
| 2026-10-20 | Python with a Streamlit web page | Fast to build; free hosting on Streamlit Community Cloud | Less control over the page design than a custom web app |
| 2026-10-20 | "Not stated" when the notes give no owner or date | A RAID log with invented owners is worse than one with gaps | Some logs show many "Not stated" values |
| 2026-10-20 | Tool use with `tool_choice: auto`, a prompt rule to call the tool, and one retry | The first live run showed that Claude Sonnet 5.5 rejects a forced `tool_choice` ("tool"/"any") | A small chance of a second call (more cost and time) when the model answers in plain text first |
| 2026-10-20 | Validate every item with Pydantic; repair bad dates to "Not stated"; drop items with an unknown type | The output must always pass validation, even when the model makes a mistake | A dropped item is lost; the tool reports it as a warning so the user can check the notes |
