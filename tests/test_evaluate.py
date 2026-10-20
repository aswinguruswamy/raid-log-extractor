"""Tests for KAN-18: the eval scoring."""

from raid.evaluate import build_report, misses_and_extras, overlap, same_person, score_sample
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
