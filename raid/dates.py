"""Date words + meeting date -> YYYY-MM-DD (RAID v2 spec R4, decision RD1, task A4).

The model copies the date words from the notes ("by Friday", "2 November"); this code
makes the date, so the date is deterministic and testable (constitution P1).

Rules:
  - A full date with a year converts always ("2027-01-15", "15 January 2027").
  - A day and month take the year of the meeting date ("2 November" -> 2026-11-02), or the
    next year when that date is more than 30 days before the meeting ("by 5 January" in a
    December meeting -> January of the next year; spec v1.2).
  - A weekday is the next such day after the meeting date; the same weekday is next
    week ("by Tuesday" on Tuesday 1 Dec 2026 -> 2026-12-08). "today" and "tomorrow"
    count from the meeting date.
  - Everything else is "Not stated": numbers only ("02/11"), "next Friday",
    "Friday next week", "every Friday",
    "next sprint", "end of month", "soon", "EOD", events ("after the release").
  - With no meeting date, only full dates with a year convert.
"""

from __future__ import annotations

import re
from datetime import date, timedelta

from .schema import NOT_STATED, RaidLog

NEEDS_MEETING_DATE = "Enter the meeting date to convert dates."

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_MONTHS = ["january", "february", "march", "april", "may", "june", "july",
           "august", "september", "october", "november", "december"]

_WEEKDAY = r"(mon|tue|tues|wed|thu|thur|thurs|fri|sat|sun)(day|sday|nesday|rsday|urday)?"
_MONTH = (r"(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|(?-i:May)|jun(?:e)?|jul(?:y)?|aug(?:ust)?"
          r"|sep(?:t(?:ember)?)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?")
_DAY = r"(\d{1,2})(?:st|nd|rd|th)?"

_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_DAY_MONTH = re.compile(rf"\b{_DAY}\s+(?:of\s+)?{_MONTH}\b(?:,?\s+(\d{{4}}))?", re.I)
_MONTH_DAY = re.compile(rf"\b{_MONTH}\s+{_DAY}\b(?:,?\s+(\d{{4}}))?", re.I)
_WEEKDAY_RE = re.compile(rf"\b(next|this|last)?\s*{_WEEKDAY}\b", re.I)
_NOT_ONE_WEEKDAY = re.compile(r"\b(week|weeks|after|every|each|fortnight|other)\b", re.I)
_NUMERIC = re.compile(r"\b\d{1,2}[/.]\d{1,2}(?:[/.]\d{2,4})?\b")


def _month(name: str) -> int:
    return next(i for i, m in enumerate(_MONTHS, start=1) if m.startswith(name.lower()[:3]))


def _make(year: int, month: int, day: int) -> str:
    try:
        return date(year, month, day).isoformat()
    except ValueError:  # 30 February and the like
        return NOT_STATED


NEXT_YEAR_AFTER_DAYS = 30


def _with_year(meeting_date: date, month: int, day: int) -> str:
    """The meeting's year; the next year when that date is more than 30 days before the
    meeting ("by 5 January" in a December meeting). Spec v1.2, R4.3."""
    same_year = _make(meeting_date.year, month, day)
    if same_year != NOT_STATED and (meeting_date - date.fromisoformat(same_year)).days > NEXT_YEAR_AFTER_DAYS:
        return _make(meeting_date.year + 1, month, day)
    return same_year


def to_date(date_words: str, meeting_date: date | None) -> str:
    """Convert date words to YYYY-MM-DD, or 'Not stated' when the words do not give one date."""
    words = (date_words or "").strip()
    if not words:
        return NOT_STATED

    if m := _ISO.search(words):
        return _make(int(m[1]), int(m[2]), int(m[3]))
    if _NUMERIC.search(words):
        return NOT_STATED  # "02/11": day/month order unknown (C3)
    for pattern, day_group, month_group in ((_DAY_MONTH, 1, 2), (_MONTH_DAY, 2, 1)):
        if m := pattern.search(words):
            year = m[3]
            if year:
                return _make(int(year), _month(m[month_group]), int(m[day_group]))
            if meeting_date is None:
                return NOT_STATED
            return _with_year(meeting_date, _month(m[month_group]), int(m[day_group]))

    if meeting_date is None:
        return NOT_STATED
    lower = words.lower()
    if re.search(r"\btoday\b", lower):
        return meeting_date.isoformat()
    if re.search(r"\btomorrow\b", lower):
        return (meeting_date + timedelta(days=1)).isoformat()
    if m := _WEEKDAY_RE.search(words):
        if m[1] or _NOT_ONE_WEEKDAY.search(words):
            return NOT_STATED  # "next Friday", "Friday next week", "every Friday": not one clear day
        target = next(i for i, d in enumerate(_WEEKDAYS) if d.startswith(m[2].lower()[:3]))
        ahead = (target - meeting_date.weekday()) % 7 or 7
        return (meeting_date + timedelta(days=ahead)).isoformat()
    return NOT_STATED


def apply_dates(log: RaidLog, meeting_date: date | None) -> list[str]:
    """Set each item's due date from its date words. Return the warnings for the page."""
    needs_meeting_date = False
    for item in log.items:
        item.due_date = to_date(item.date_words, meeting_date)
        if meeting_date is None and item.date_words and item.due_date == NOT_STATED:
            needs_meeting_date = True
    return [NEEDS_MEETING_DATE] if needs_meeting_date else []
