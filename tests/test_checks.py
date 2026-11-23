"""Code checks before display (RAID v2 spec R5, constitution P2, task A5). Fake items, no API."""

from raid.checks import (
    DATE_NOT_IN_NOTES,
    DUPLICATE,
    NOT_NEAR_QUOTE,
    ONE_WORD_REPLY,
    OWNER_NOT_IN_NOTES,
    run_checks,
)
from raid.schema import NOT_STATED, OwnerState, RaidItem, RaidLog

NOTES = """Ben Ortiz: Aiko, can you do the deck by Friday?
Aiko Sato: Yes.
Ben Ortiz: The vendor may be late with the API.
Mo Rahman: I'll ask Tom to update the budget.
Ben Ortiz: Okay. Next topic is the office move.
Ben Ortiz: Priya will look at the risk register.
Mo Rahman: Thanks."""


def item(**changes):
    values = {"type": "Action", "description": "Do the deck.", "owner": "Aiko Sato", "owner_state": "Confirmed",
              "source_quote": "Aiko, can you do the deck by Friday?", "date_words": "by Friday"}
    values.update(changes)
    return RaidItem(**values)


def lines_for(attention, short_id):
    return [a.text for a in attention if a.short_id == short_id]


def test_clean_item_has_no_lines():
    log = RaidLog(items=[item(reply_quote="")])
    assert run_checks(log, NOTES) == []
    assert log.items[0].short_id == "ACT-1"


def test_ac19_owner_not_in_the_notes_becomes_not_stated():
    log = RaidLog(items=[item(owner="Carla Mendes")])
    attention = run_checks(log, NOTES)
    assert (log.items[0].owner, log.items[0].owner_state) == (NOT_STATED, OwnerState.NOT_STATED)
    assert OWNER_NOT_IN_NOTES in lines_for(attention, "ACT-1")


def test_first_name_or_role_in_the_notes_is_enough():
    log = RaidLog(items=[item(owner="Aiko")])
    assert run_checks(log, NOTES) == []


def test_ac20_owner_not_near_the_quote():
    # Priya is in the notes, but not in the quote or the turns next to it.
    log = RaidLog(items=[item(owner="Priya", date_words="")])
    attention = run_checks(log, NOTES)
    assert lines_for(attention, "ACT-1") == [NOT_NEAR_QUOTE]
    assert log.items[0].owner == "Priya"  # kept, but flagged


def test_owner_in_the_next_turn_is_near():
    log = RaidLog(items=[item(owner="Tom", source_quote="update the budget", date_words="",
                              owner_state="Not confirmed")])
    # "Tom" is in the same turn as the quote.
    assert run_checks(log, NOTES) == []


def test_date_words_not_near_the_quote():
    log = RaidLog(items=[item(source_quote="The vendor may be late with the API.", owner="Ben Ortiz",
                              date_words="by Friday", type="Risk")])
    # "by Friday" is two turns away from the quote.
    assert NOT_NEAR_QUOTE in lines_for(run_checks(log, NOTES), "RSK-1")


def test_ac21_date_words_not_in_the_notes():
    log = RaidLog(items=[item(date_words="by Monday", due_date="2026-12-07")])
    attention = run_checks(log, NOTES)
    assert log.items[0].due_date == NOT_STATED
    assert log.items[0].date_words == "by Monday"
    assert DATE_NOT_IN_NOTES in lines_for(attention, "ACT-1")


def test_ac22_same_quote_keeps_the_first_item():
    first = item(description="Do the deck.")
    second = item(description="Prepare the deck.", source_quote="Aiko, can you do the deck by Friday")
    log = RaidLog(items=[first, second])
    attention = run_checks(log, NOTES)
    assert [i.description for i in log.items] == ["Do the deck."]
    assert DUPLICATE in lines_for(attention, "ACT-1")


def test_quotes_overlapping_by_half_are_duplicates():
    a = item(source_quote="can you do the deck by Friday?")
    b = item(source_quote="Aiko, can you do the deck")
    log = RaidLog(items=[a, b])
    run_checks(log, NOTES)
    assert len(log.items) == 1


def test_small_overlap_is_not_a_duplicate():
    a = item(source_quote="Aiko, can you do the deck by Friday?")
    b = item(source_quote="The vendor may be late with the API.", type="Risk", owner=NOT_STATED, date_words="")
    log = RaidLog(items=[a, b])
    run_checks(log, NOTES)
    assert len(log.items) == 2


def test_same_quote_with_another_type_is_kept():
    # Catalogue A5: one sentence can give an Action and a Dependency.
    action = item()
    dependency = item(type="Dependency", owner=NOT_STATED)
    log = RaidLog(items=[action, dependency])
    run_checks(log, NOTES)
    assert [i.type.value for i in log.items] == ["Action", "Dependency"]


def test_ac23_one_word_reply():
    log = RaidLog(items=[item(reply_quote="Yes.")])
    assert ONE_WORD_REPLY in lines_for(run_checks(log, NOTES), "ACT-1")


def test_longer_reply_is_fine():
    notes = NOTES.replace("Aiko Sato: Yes.", "Aiko Sato: Yes, will do.")
    log = RaidLog(items=[item(reply_quote="Yes, will do.")])
    assert run_checks(log, notes) == []


def test_line_texts_match_the_spec():
    assert NOT_NEAR_QUOTE == "Owner/date not near the quote – check."
    assert ONE_WORD_REPLY == "Owner from a one-word reply – check the speaker."
