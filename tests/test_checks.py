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


def test_one_sentence_with_three_tasks_keeps_three_actions():
    # Spec R2.2 / AC6 (catalogue B1): one quote gives three different tasks. Not duplicates.
    quote = "Jon, Alisa, Crab – the test plan, the pipeline and the release notes."
    notes = "Carmen Diaz: " + quote
    log = RaidLog(items=[
        RaidItem(type="Action", description=d, source_quote=quote, owner_state="Not confirmed")
        for d in ("Write the test plan.", "Build the pipeline.", "Write the release notes.")
    ])
    assert DUPLICATE not in [a.text for a in run_checks(log, notes)]
    assert len(log.items) == 3


# --- review of PR 13 ---

def test_same_opening_but_different_tasks_are_both_kept():
    notes = "Ana Ruiz: We need to update the API docs by Friday.\nAna Ruiz: We need to update the test plan by Friday."
    log = RaidLog(items=[
        RaidItem(type="Action", description="Update the API docs.", source_quote="We need to update the API docs by Friday"),
        RaidItem(type="Action", description="Update the test plan.", source_quote="We need to update the test plan by Friday"),
    ])
    run_checks(log, notes)
    assert len(log.items) == 2


def test_common_word_owner_is_not_found_in_i_will():
    log = RaidLog(items=[item(owner="Will", date_words="")])
    attention = run_checks(log, NOTES)
    assert log.items[0].owner == NOT_STATED
    assert OWNER_NOT_IN_NOTES in lines_for(attention, "ACT-1")


def test_role_made_of_common_words_must_appear_whole():
    notes = NOTES + "\nBen Ortiz: The data is ready and the team is happy."
    log = RaidLog(items=[item(owner="Data team", date_words="")])
    run_checks(log, notes)
    assert log.items[0].owner == NOT_STATED


def test_short_lines_do_not_widen_the_context():
    # "Yes." is in the quote's text but is its own line; the owner two turns away is not near.
    notes = "Ben Ortiz: Priya is out.\nBen Ortiz: Okay.\nAna Ruiz: Can someone send the report?\nMo Rahman: Thanks."
    log = RaidLog(items=[RaidItem(type="Action", description="Send the report.", owner="Priya",
                                  owner_state="Not confirmed", source_quote="Okay.")])
    attention = run_checks(log, notes)
    # The quote "Okay." holds only line 2; lines 1-3 are near, so Priya (line 1) is near.
    assert NOT_NEAR_QUOTE not in lines_for(attention, "ACT-1")
    log = RaidLog(items=[RaidItem(type="Action", description="Send the report.", owner="Priya",
                                  owner_state="Not confirmed", source_quote="Thanks.")])
    assert NOT_NEAR_QUOTE in lines_for(run_checks(log, notes), "ACT-1")


def test_owners_by_list_tasks_with_the_same_note_are_kept():
    # Live spec example AC6: the model wrote the owner note into each description.
    quote = "Jon, Alisa, Crab – the test plan, the pipeline and the release notes."
    note = "owners by list: Jon, Alisa, Crab – confirm"
    log = RaidLog(items=[
        RaidItem(type="Action", description=f"{d} (owner to be confirmed from the list Jon, Alisa, Crab).",
                 source_quote=quote, owner_state="Not confirmed", owner_note=note)
        for d in ("Prepare the test plan", "Set up the pipeline", "Write the release notes")
    ])
    run_checks(log, "Carmen Diaz: " + quote)
    assert len(log.items) == 3
