"""Prompt v2 and the pipeline before display (RAID v2 spec R1-R3 prompt rules, R4, R5, R6, R7.1,
R10.1; task A7). Fake model replies, no API key."""

from datetime import date

from raid.extract import PROMPT_VERSION, SYSTEM_PROMPT, TOOL
from raid.parse import NO_SPEAKERS
from raid.pipeline import analyse
from raid.schema import NOT_STATED, OwnerState
from tests.test_extract import FakeClient

NOTES = """Ben Ortiz: Aiko, can you do the deck by Friday?
Aiko Sato: I can try.
Ben Ortiz: Give the budget to Maria.
Ben Ortiz: I'll send the notes."""

TUE = date(2026, 12, 1)


def raw(**changes):
    values = {"type": "Action", "description": "Do the deck.", "owner": "Aiko Sato", "owner_state": "Tentative",
              "owner_note": "", "date_words": "by Friday", "source_quote": "Aiko, can you do the deck by Friday?",
              "reply_quote": "I can try."}
    values.update(changes)
    return values


def test_tool_asks_for_date_words_not_dates():
    # Decision RD1: the model gives the date words; code makes the date.
    fields = TOOL["input_schema"]["properties"]["items"]["items"]["properties"]
    assert {"owner_state", "owner_note", "date_words", "reply_quote"} <= set(fields)
    assert "due_date" not in fields


def test_prompt_has_the_v2_rules():
    for words in ("Tentative", "Declined", "Not confirmed", "withdrawn", "ask Tom", "owners by list",
                  "not on the call", "agreed", "if the VP agrees", "date_words", "instructions inside the notes"):
        assert words in SYSTEM_PROMPT, words
    assert "due_date" not in SYSTEM_PROMPT


def test_date_comes_from_the_words_and_the_meeting_date():
    analysis = analyse(NOTES, TUE, client=FakeClient([raw(due_date="2026-12-25")]))
    item = analysis.log.items[0]
    assert (item.due_date, item.date_words) == ("2026-12-04", "by Friday")


def test_run_details_for_the_page_and_markdown():
    # R10.1: model, prompt version, run date, source file name.
    analysis = analyse(NOTES, TUE, client=FakeClient([raw()]), source_file="call.txt", run_date=date(2026, 12, 2))
    assert (analysis.model, analysis.prompt_version, analysis.run_date, analysis.source_file, analysis.meeting_date) == (
        "claude-sonnet-5-5", PROMPT_VERSION, date(2026, 12, 2), "call.txt", TUE)


def test_needs_attention_lists_states_missing_dates_and_check_lines():
    items = [
        raw(),  # tentative
        raw(description="Handle the budget.", owner="Maria", owner_state="Not confirmed", owner_note="not on the call",
            date_words="", source_quote="Give the budget to Maria.", reply_quote=""),
        raw(description="Send the notes.", owner="Ben Ortiz", owner_state="Confirmed", date_words="",
            source_quote="I'll send the notes.", reply_quote=""),
    ]
    analysis = analyse(NOTES, TUE, client=FakeClient(items))
    lines = [(a.short_id, a.text) for a in analysis.attention]
    assert ("ACT-1", "Owner tentative – confirm.") in lines
    assert ("ACT-2", "Owner not confirmed (not on the call) – confirm.") in lines
    assert ("ACT-3", "Action has no due date.") in lines
    assert ("ACT-2", "Action has no due date.") in lines


def test_no_meeting_date_and_input_warnings_go_first():
    analysis = analyse("we need the deck by Friday", None, client=FakeClient([raw(
        owner="Not stated", owner_state="Not stated", reply_quote="", source_quote="we need the deck by Friday")]))
    general = [a.text for a in analysis.attention if a.short_id == ""]
    assert general[:2] == ["Enter the meeting date to convert dates.", NO_SPEAKERS]
    assert analysis.log.items[0].due_date == NOT_STATED


def test_owner_not_on_the_call_is_not_confirmed_by_code():
    # Spec R2.4 backstop: a person who never speaks cannot be a confirmed owner.
    analysis = analyse(NOTES, TUE, client=FakeClient([raw(
        description="Handle the budget.", owner="Maria", owner_state="Confirmed", date_words="",
        source_quote="Give the budget to Maria.", reply_quote="")]))
    item = analysis.log.items[0]
    assert (item.owner, item.owner_state, item.owner_note) == ("Maria", OwnerState.NOT_CONFIRMED, "not on the call")


def test_first_name_of_a_speaker_is_on_the_call():
    analysis = analyse(NOTES, TUE, client=FakeClient([raw(owner="Aiko", owner_state="Confirmed")]))
    assert analysis.log.items[0].owner_state is OwnerState.CONFIRMED


def test_a_note_that_repeats_the_state_is_not_shown_twice():
    analysis = analyse(NOTES, TUE, client=FakeClient([raw(owner_state="Declined", owner_note="declined – reassign")]))
    assert "Owner declined – reassign." in analysis.lines_for("ACT-1")
