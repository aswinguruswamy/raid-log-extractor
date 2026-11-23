"""Date words + meeting date -> YYYY-MM-DD, by code (RAID v2 spec R4, decision RD1, task A4)."""

from datetime import date

import pytest

from raid.dates import NEEDS_MEETING_DATE, apply_dates, to_date
from raid.schema import NOT_STATED, RaidItem, RaidLog

TUE = date(2026, 12, 1)  # the spec's meeting date: Tuesday 1 December 2026


@pytest.mark.parametrize("words, expected", [
    ("by Friday", "2026-12-04"),        # AC12
    ("by Tuesday", "2026-12-08"),       # AC13: same weekday -> next week
    ("on Wednesday", "2026-12-02"),
    ("Tuesday works", "2026-12-08"),
    ("Monday", "2026-12-07"),
    ("by Fri", "2026-12-04"),
    ("on 2 November", "2026-11-02"),    # AC14: year from the meeting date, kept as given
    ("by 10 December", "2026-12-10"),
    ("December 10", "2026-12-10"),
    ("by the 3rd of December", "2026-12-03"),
    ("4 Dec", "2026-12-04"),
    ("on 5 May", "2027-05-05"),      # more than 30 days before the meeting -> next year (v1.2)
    ("by Sept 3", "2027-09-03"),
    ("on 2027-01-15", "2027-01-15"),
    ("by 15 January 2027", "2027-01-15"),
    ("January 15, 2027", "2027-01-15"),
    ("today", "2026-12-01"),
    ("by tomorrow", "2026-12-02"),
])
def test_converts_date_words(words, expected):
    assert to_date(words, TUE) == expected


@pytest.mark.parametrize("words", [
    "by 02/11",            # AC15: number-only, locale unknown
    "02/11/2026",
    "next sprint",         # AC17
    "end of month", "EOM", "soon", "next week", "EOD", "Q3",
    "next Friday",         # this week's or next week's Friday? Not stated.
    "after the release",
    "30 February",
    "",
    # review of PR 12: words that only start like a month, and weekdays that are not one day
    "sprint 3 may slip", "after sprint 2 decision", "before the 2 marketing calls", "in 3 decades",
    "by Friday next week", "Friday week", "the Friday after next", "every Friday",
])
def test_words_that_cannot_be_converted_are_not_stated(words):
    assert to_date(words, TUE) == NOT_STATED


def test_explicit_date_wins_over_weekday():
    assert to_date("Friday 11 December", TUE) == "2026-12-11"


@pytest.mark.parametrize("words, expected", [
    ("by Friday", NOT_STATED),          # AC18
    ("on 2 November", NOT_STATED),      # no year, no meeting date
    ("tomorrow", NOT_STATED),
    ("by 15 January 2027", "2027-01-15"),  # a full date still converts (R4.5)
    ("2027-01-15", "2027-01-15"),
])
def test_without_a_meeting_date_only_full_dates_convert(words, expected):
    assert to_date(words, None) == expected


def _item(words, due="Not stated"):
    return RaidItem(type="Action", description="Send the list.", owner="Dev", source_quote="send the list",
                    date_words=words, due_date=due)


def test_apply_dates_sets_due_date_from_the_words_and_keeps_the_words():
    log = RaidLog(items=[_item("by Friday"), _item("", due="2026-12-24")])
    warnings = apply_dates(log, TUE)
    assert [(i.due_date, i.date_words) for i in log.items] == [
        ("2026-12-04", "by Friday"),
        (NOT_STATED, ""),  # code writes the date; a date with no words is dropped (P1)
    ]
    assert warnings == []


def test_apply_dates_without_meeting_date_warns_once():
    log = RaidLog(items=[_item("by Friday"), _item("on Monday")])
    assert apply_dates(log, None) == [NEEDS_MEETING_DATE]
    assert NEEDS_MEETING_DATE == "Enter the meeting date to convert dates."
    assert all(i.due_date == NOT_STATED and i.date_words for i in log.items)


# --- Year rule (spec v1.2, R4.3; approved by Aswin Guruswamy 2026-11-23) ---

@pytest.mark.parametrize("words, meeting, expected", [
    ("by 5 January", date(2026, 12, 15), "2027-01-05"),   # more than 30 days before -> next year
    ("on 2 November", date(2026, 12, 1), "2026-11-02"),   # 29 days before -> same year (AC14)
    ("on 31 October", date(2026, 11, 30), "2026-10-31"),  # 30 days before -> same year
    ("on 31 October", date(2026, 12, 1), "2027-10-31"),   # 31 days before -> next year
])
def test_day_and_month_more_than_30_days_before_the_meeting_is_next_year(words, meeting, expected):
    assert to_date(words, meeting) == expected


def test_full_date_with_a_year_is_kept_as_given():
    assert to_date("by 5 January 2026", date(2026, 12, 15)) == "2026-01-05"
