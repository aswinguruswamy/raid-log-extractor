"""The page table and the Markdown file (RAID v2 spec R8.1-R8.6, R9.1, R10.1; AC29-AC35, AC45; task A9)."""

from datetime import date
from pathlib import Path

from raid.checks import Attention
from raid.export import to_markdown
from raid.pipeline import Analysis
from raid.schema import RaidItem, RaidLog
from raid.view import COLUMNS, due_cell, item_cell, owner_cell, sorted_items, table_rows

GOLDEN = Path(__file__).parent / "fixtures" / "golden_v2.md"


def sample_analysis() -> Analysis:
    items = [
        RaidItem(type="Decision", description="Use Postgres.", source_quote="Agreed – we go with Postgres.",
                 quote_verified=True),
        RaidItem(type="Action", description="Do the deck.", owner="Aiko Sato", owner_state="Tentative",
                 date_words="by Friday", due_date="2026-12-04", source_quote="Aiko, can you do the deck by Friday?",
                 reply_quote="I can try.", quote_verified=True),
        RaidItem(type="Risk", description="The vendor may be late | again.", source_quote="vendor may be late",
                 quote_verified=False),
        RaidItem(type="Action", description="Send the notes.", owner="Ben Ortiz", owner_state="Confirmed",
                 source_quote="I'll send the notes.", quote_verified=True),
    ]
    log = RaidLog(source_file="call.txt", items=items)
    attention = [Attention("", "Enter the meeting date to convert dates."),
                 Attention("ACT-1", "Owner tentative – confirm."), Attention("RSK-1", "Check the quote."),
                 Attention("ACT-2", "Action has no due date.")]
    return Analysis(log=log, attention=attention, model="claude-sonnet-5-5", prompt_version="2.1",
                    run_date=date(2026, 12, 2), source_file="call.txt", meeting_date=date(2026, 12, 1))


def test_ac30_columns_and_order():
    analysis = sample_analysis()
    assert COLUMNS == ["Type", "Item", "Owner", "Due date", "Reviewed"]
    ids = [i.short_id for i in sorted_items(analysis.log, analysis.attention)]
    # Rows with a Needs attention line first (by type order, then ID), then the rest.
    assert ids == ["ACT-1", "ACT-2", "RSK-1", "DEC-1"]


def test_ac31_ac45_owner_state_as_a_word_and_quote_mark():
    a = sample_analysis().log.items
    assert owner_cell(a[1]) == "Aiko Sato (tentative)"
    assert owner_cell(a[3]) == "Ben Ortiz"
    assert owner_cell(a[0]) == "Not stated"
    assert owner_cell(RaidItem(type="Action", description="Test plan.", source_quote="x",
                               owner_state="Not confirmed")) == "Not stated (not confirmed)"
    assert item_cell(a[1]) == "ACT-1 Do the deck. ✓"
    assert item_cell(a[2]) == "RSK-1 The vendor may be late | again. (quote not found)"


def test_due_cell_shows_the_date_words():
    a = sample_analysis().log.items
    assert due_cell(a[1]) == "2026-12-04 · by Friday"
    assert due_cell(a[3]) == "Not stated"
    assert due_cell(RaidItem(type="Action", description="Plan it.", source_quote="x",
                             date_words="next sprint")) == "Not stated · next sprint"


def test_reviewed_starts_unticked():
    rows = table_rows(sample_analysis(), reviewed=set())
    assert [r["Reviewed"] for r in rows] == [False] * 4
    assert list(rows[0]) == COLUMNS + ["ID"]


def test_ac33_markdown_shows_reviewed_ticks():
    text = to_markdown(sample_analysis(), reviewed={"ACT-1"})
    assert "| ✓ reviewed |" in text and text.count("| not reviewed |") == 3


def test_ac34_ac35_markdown_equals_the_golden_file():
    text = to_markdown(sample_analysis(), reviewed={"ACT-1"})
    assert text == GOLDEN.read_text(encoding="utf-8")
    for words in ("## Run details", "claude-sonnet-5-5", "2.1", "2026-12-02", "call.txt", "## Needs attention",
                  "## RAID log", "## Evidence", "I can try."):
        assert words in text


def test_ac29_action_without_date_is_in_needs_attention_of_the_markdown():
    assert "- ACT-2: Action has no due date." in to_markdown(sample_analysis(), reviewed=set())


def test_saved_analysis_round_trip():
    analysis = sample_analysis()
    again = Analysis.from_saved(analysis.to_saved())
    assert to_markdown(again, reviewed=set()) == to_markdown(analysis, reviewed=set())


def test_quotes_and_lines_stay_one_line_and_literal():
    analysis = sample_analysis()
    analysis.log.items[0].source_quote = "Agreed –\n\nwe go with *Postgres*_v2"
    text = to_markdown(analysis, reviewed=set())
    assert '"Agreed – we go with \\*Postgres\\*\\_v2"' in text


def test_v1_saved_file_gets_its_needs_attention_lines():
    saved = sample_analysis().to_saved()
    del saved["needs_attention"]
    lines = [(a.short_id, a.text) for a in Analysis.from_saved(saved).attention]
    assert ("ACT-1", "Owner tentative – confirm.") in lines and ("ACT-2", "Action has no due date.") in lines
