# Product decisions

This file records the main design choices and their trade-offs (story S3-06, KAN-26).

| Date | Decision | Why | Trade-off |
|---|---|---|---|
| 2026-10-20 | Python with a Streamlit web page | Fast to build; free hosting on Streamlit Community Cloud | Less control over the page design than a custom web app |
| 2026-10-20 | "Not stated" when the notes give no owner or date | A RAID log with invented owners is worse than one with gaps | Some logs show many "Not stated" values |
| 2026-10-20 | Tool use with `tool_choice: auto`, a prompt rule to call the tool, and one retry | The first live run showed that Claude Sonnet 5.5 rejects a forced `tool_choice` ("tool"/"any") | A small chance of a second call (more cost and time) when the model answers in plain text first |
| 2026-10-20 | Prompt v2: record ownerless actions; owner rules by item type (the speaker is not the owner); quote the request for two-turn actions | Eval run 1 found one missed ownerless action, two guessed owners, and one unhelpful "yes" quote | Run 2 scored 100% recall and precision for $0.005 more on 10 samples. Risk: the prompt was tuned on the eval samples, so a held-out set is needed to confirm the gain |
| 2026-10-20 | Validate every item with Pydantic; repair bad dates to "Not stated"; drop items with an unknown type | The output must always pass validation, even when the model makes a mistake | A dropped item is lost; the tool reports it as a warning so the user can check the notes |
| 2026-10-20 | Demo mode with saved eval results; no API key on the public site | A reviewer can try the tool in one click, and the owner's key is never exposed or spent by strangers | The demo shows 3 fixed samples. To run on new notes, a user enters their own key |
| 2026-10-20 | Web page tables use `st.table` (wrapped text), not `st.dataframe`; the page leaves out the Status column | Source quotes are long; a reader must see the full quote to trust the item. Every new item is "Open", so the column adds nothing on the page | No sort or filter in the page; the Excel file has filters and the Status dropdown |
| 2026-10-20 | Demo samples: one of each input format (Teams .vtt, bullet .txt, Word .docx) | A visitor sees that the tool reads all three formats | The demo does not show a Zoom transcript; the eval set has two |
| 2026-10-20 | Page in two numbered boxes (1. input, 2. RAID log); help text in the sidebar and in expanders; counts only in the tab names | A first-time visitor reads the page from top to bottom with no repeated numbers | Less information on the screen at first; the sidebar is closed on a phone |
