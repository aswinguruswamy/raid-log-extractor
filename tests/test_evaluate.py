"""Tests for KAN-18: the eval scoring."""

from raid.evaluate import (
    build_report,
    misses_and_extras,
    overlap,
    same_person,
    score_sample,
)
from raid.schema import NOT_STATED

NOTES = (
    "Priya Shah: The vendor may not deliver the API by Friday. "
    "Tom Lee: I will send the test data by 2026-10-26. "
    "Priya Shah: We decided to use PostgreSQL."
)

EXPECTED = [
    {"type": "Risk", "summary": "Vendor late", "owner": NOT_STATED, "due_date": NOT_STATED,
     "evidence": "The vendor may not deliver the API"},
    {"type": "Action", "summary": "Send test data", "owner": "Tom Lee", "due_date": "2026-10-26",
     "evidence": "I will send the test data"},
    {"type": "Decision", "summary": "Use PostgreSQL", "owner": NOT_STATED, "due_date": NOT_STATED,
     "evidence": "We decided to use PostgreSQL", "also_accept_types": ["Action"]},
]


def found(type, quote, owner=NOT_STATED, due=NOT_STATED, description="x"):
    return {"type": type, "source_quote": quote, "owner": owner, "due_date": due, "description": description}


def test_overlap():
    assert overlap("The vendor may not deliver", "Priya: The vendor may not deliver the API by Friday.") == 1.0
    assert overlap("send the test data by Monday", "send test data Monday") > 0.6
    assert overlap("We decided to use PostgreSQL", "The staging server is down") < 0.6
    assert overlap("", "anything") == 0.0


def test_same_person():
    assert same_person("Mei Lin", "Mei")
    assert same_person("Tom Lee", "tom lee")
    assert same_person(NOT_STATED, NOT_STATED)
    assert not same_person("Tom Lee", NOT_STATED)
    assert not same_person("Tom Lee", "Priya Shah")


def test_perfect_answer_scores_100_percent():
    tool = [
        found("Risk", "The vendor may not deliver the API by Friday."),
        found("Action", "I will send the test data by 2026-10-26.", "Tom Lee", "2026-10-26"),
        found("Decision", "We decided to use PostgreSQL."),
    ]
    report = build_report([score_sample("s", NOTES, EXPECTED, tool)])
    assert report.total.recall == 1.0 and report.total.precision == 1.0
    assert (report.owner_correct, report.owner_checked) == (1, 1)
    assert (report.date_correct, report.date_checked) == (1, 1)
    assert not report.invented_owners and not report.invented_dates and not report.guessed_owners


def test_miss_extra_and_wrong_type():
    tool = [
        found("Issue", "The vendor may not deliver the API by Friday."),   # matched, wrong type
        found("Risk", "The staging server is down", description="Staging down"),  # extra
    ]
    sample = score_sample("s", NOTES, EXPECTED, tool)
    report = build_report([sample])
    assert report.by_type["Risk"].recall == 0.0          # found, but as the wrong type
    assert report.by_type["Issue"].precision == 0.0
    assert report.by_type["Risk"].precision == 0.0       # the extra
    assert report.total.recall == 0.0
    misses, extras, mixups = misses_and_extras(sample)
    assert len(misses) == 2 and len(extras) == 1 and len(mixups) == 1


def test_also_accepted_type_counts_as_correct():
    tool = [found("Action", "We decided to use PostgreSQL.")]
    report = build_report([score_sample("s", NOTES, EXPECTED, tool)])
    assert report.by_type["Decision"].recall == 1.0
    assert report.by_type["Action"].precision == 1.0


def test_invented_and_guessed_owners_and_dates():
    tool = [
        found("Risk", "The vendor may not deliver the API", owner="Priya Shah"),   # guessed: notes name nobody
        found("Action", "I will send the test data", owner="Ravi Kumar", due="2026-11-30"),  # invented
    ]
    sample = score_sample("s", NOTES, EXPECTED, tool)
    assert len(sample.guessed_owners) == 1
    assert len(sample.invented_owners) == 1 and "Ravi Kumar" in sample.invented_owners[0]
    assert len(sample.invented_dates) == 1 and "2026-11-30" in sample.invented_dates[0]


def test_one_tool_item_matches_only_one_expected_item():
    tool = [found("Risk", "The vendor may not deliver the API by Friday.")]
    expected = EXPECTED[:1] + [dict(EXPECTED[0], summary="duplicate")]
    sample = score_sample("s", NOTES, expected, tool)
    assert len(sample.pairs) == 1


# --- RAID v2 metrics (spec §4 definitions, R14.1, R15.1, N1; task A8) ---------------

from raid.evaluate import consistency, v2_scores  # noqa: E402

NOTES_V2 = "Ben Ortiz: Aiko, can you do the deck by Friday? Aiko Sato: I can try. Ben Ortiz: Give it to Maria."


def key(owner="Aiko Sato", state="Tentative", due="2026-12-04", evidence="Aiko, can you do the deck"):
    return {"type": "Action", "summary": "Deck", "owner": owner, "owner_state": state, "due_date": due,
            "evidence": evidence}


def tool(owner="Aiko Sato", state="Tentative", due="2026-12-04", quote="Aiko, can you do the deck by Friday?"):
    return {"type": "Action", "source_quote": quote, "owner": owner, "owner_state": state, "due_date": due,
            "description": "Do the deck."}


def v2(expected, found):
    return v2_scores(build_report([score_sample("s", NOTES_V2, expected, found)]))


def test_correct_item_has_no_v2_errors():
    s = v2([key()], [tool()])
    assert (s.invented_owners, s.wrong_owners, s.invented_dates, s.wrong_dates) == ([], [], [], [])
    assert (s.state_correct, s.state_checked) == (1, 1)


def test_invented_owner_is_a_confirmed_or_tentative_person_where_the_key_has_none_or_not_confirmed():
    assert v2([key(state="Not confirmed")], [tool(state="Confirmed")]).invented_owners
    assert v2([key(state="Declined")], [tool(state="Tentative")]).invented_owners
    assert v2([key(owner="Not stated", state="Not stated")], [tool(state="Confirmed")]).invented_owners
    # A named owner with state Not confirmed is honest, not invented.
    assert not v2([key(owner="Not stated", state="Not confirmed")], [tool(state="Not confirmed")]).invented_owners


def test_wrong_owner_is_a_different_person():
    s = v2([key()], [tool(owner="Ben Ortiz")])
    assert len(s.wrong_owners) == 1 and not s.invented_owners


def test_invented_and_wrong_dates():
    assert v2([key(due="Not stated")], [tool(due="2026-12-04")]).invented_dates
    s = v2([key(due="2026-12-04")], [tool(due="2026-12-11")])
    assert len(s.wrong_dates) == 1 and not s.invented_dates
    assert not v2([key(due="2026-12-04")], [tool(due="Not stated")]).invented_dates


def test_v1_keys_without_owner_state_use_the_default():
    k = key()
    del k["owner_state"]  # tuning keys from v1: a named owner was an agreed owner
    assert not v2([k], [tool(state="Confirmed")]).invented_owners


def test_consistency_is_the_share_of_expected_items_found_in_every_run():
    expected = [key(), key(evidence="Give it to Maria", owner="Maria", state="Not confirmed", due="Not stated")]
    run_a = [tool(), tool(quote="Give it to Maria.", owner="Maria", state="Not confirmed", due="Not stated")]
    run_b = [tool()]
    runs = [[score_sample("s", NOTES_V2, expected, run_a)], [score_sample("s", NOTES_V2, expected, run_b)]]
    assert consistency(runs) == 0.5
