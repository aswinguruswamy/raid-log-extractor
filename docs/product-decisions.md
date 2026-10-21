# Product decisions

This document explains the main product choices, the options I did not take, and the trade-offs (story S3-06, KAN-26). The [decision log](#decision-log) at the end lists every decision with its date.

## The problem

After a project call, a project manager writes the RAID log by hand: risks, assumptions, issues, dependencies, actions, and decisions. My own timed test took 6 to 8 minutes for a short call (about 150 words); a full 1-hour call takes much longer. Items get lost, and owners and dates get guessed.

**The user:** a project manager who has the notes or the transcript of a call and needs a RAID log that they can trust and edit.

**The main product risk:** an AI tool that writes a confident but wrong log. A wrong owner or an invented date is worse than a gap, because the team acts on it. Most decisions below reduce this risk.

## 1. Structured output with tool use

**Decision:** Claude returns the items through a tool with a JSON schema. The code validates every item with Pydantic before it goes into the log.

**Options I did not take:**
- *Free text that the code parses.* Simple, but the format changes from run to run, and the parser breaks.
- *JSON mode from the prompt only.* Better, but nothing forces the field names and the six types.

**Why:** the schema fixes the six types and the fields, and the validation catches what the schema cannot (for example, a date in the wrong format). A bad date becomes "Not stated" with a warning; an item with an unknown type is dropped with a warning. The log always opens in Excel.

**Trade-off:** the first live run showed that Claude Sonnet 5.5 rejects a forced tool call (`tool_choice` "tool" or "any"). The tool now uses `tool_choice: auto`, a prompt rule to call the tool, and one retry. This adds a small chance of a second API call.

## 2. A source quote for every item

**Decision:** every item carries the exact words from the notes that support it. The code then checks the quote word for word against the notes (it ignores only spaces, line breaks, curly quotes, and long dashes). The page and the Excel file show "Yes" or "Not found" for each quote.

**Why:** a project manager will not trust an item that they cannot check. The quote lets them check an item in seconds, without the full notes. The word-for-word check is done by code, not by the model, so a made-up quote cannot pass.

**Trade-off:** the quote makes the output longer (more output tokens, so a little more cost). A correct item can also show "Not found" if the model changes one word in the quote; the user then checks it by hand.

## 3. "Not stated" instead of a guess

**Decision:** when the notes give no owner or no full date, the tool writes "Not stated". A relative date ("by Friday") stays in the description, because the tool does not know the date of the call. The person who reports an item is not its owner.

**Why:** a gap is visible, and the project manager fills it. A guess looks like a fact, and nobody checks it.

**Trade-off:** some logs show many "Not stated" values, which can look less complete. The eval counts guessed owners as errors, so the tool cannot score well by guessing.

## 4. The eval method

**Decision:** I wrote 10 sample calls (invented names; .txt, .docx, and Teams and Zoom .vtt files; several note styles) and 68 correct answers. The answers were committed to Git **before** the first tool run, so the history shows that they were not changed to fit the output. The eval matches each tool item to an answer by quote overlap, then scores recall and precision for each type, the owners and dates, and the invented or guessed owners and dates. Every run is kept in `evals/runs/` and never changed.

**Why:** a demo shows that a tool can work; an eval shows how often it works. Recall matters most (a missed risk is the costly error), and precision stops the tool from filling the log with noise. Charter targets: 85% recall on risks, issues, dependencies, and actions; 80% precision; 0 invented owners or dates.

**Results:** run 1 scored 97% recall and 99% precision. One round of prompt changes (run 2) scored 100% and 100%, with 0 guessed owners, for $0.10 for all 10 samples. See [`evals/FINDINGS.md`](../evals/FINDINGS.md).

**Limits:**
- I changed the prompt after I saw the run 1 errors on the same 10 samples. The run 2 score is a tuning score, not proof for new notes. A held-out set (KAN-38) is the next step.
- The samples and the answers were written with AI help, and the tool also uses Claude. Real notes are likely to be messier.
- 10 short samples are a small test.

## 5. Demo mode with no key on the public site

**Decision:** the public site has no API key. The demo mode shows the saved results of eval run 2 for 3 samples (one of each format: Teams .vtt, bullet .txt, Word .docx). To use their own notes, a visitor enters their own key.

**Options I did not take:**
- *My key on the site.* Anybody could spend my money or abuse the key.
- *My key with a rate limit.* Less risk, but more to build, and still a cost with no limit on total use.

**Why:** a recruiter must see the tool work in one click, with no sign-in and no key. The demo shows real tool output, not a mock-up, and it costs nothing.

**Trade-off:** the demo shows only 3 fixed samples. A visitor cannot try new notes without a key.

## 6. Out of scope for version 1.0

| Item | Why it is out of scope | Backlog |
|---|---|---|
| Remove names from the notes automatically | Hard to do well; a bad redaction gives a false sense of privacy. For now, the privacy note tells the user not to upload confidential data | L-01 (KAN-33) |
| Sync the log to Jira or Asana | Each tool needs its own API and sign-in. Excel works with every tool and lets the user check items first | L-02 (KAN-34) |
| Merge items across more than one call | Needs item matching and history; one call at a time is the core job | L-03 (KAN-35) |
| Languages other than English | The eval covers English only; I cannot measure quality in other languages yet | L-04 (KAN-36) |
| Live audio or a live call | Needs speech-to-text and a different product; transcripts from Teams and Zoom already exist | L-05 (KAN-37) |
| A held-out eval set | Planned as the first item for version 1.1 | L-06 (KAN-38) |

## Decision log

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
