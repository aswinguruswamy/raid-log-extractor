"""Code checks before the log is shown (RAID v2 spec R5, constitution P2, task A5).

Each check writes a "Needs attention" line for an item; some also correct the item:
  R5.2 owner name not in the notes      -> owner and state "Not stated"
  R5.3 owner or date words not near the quote (quote, reply quote, turn before/after)
  R5.4 date words not in the notes      -> due date "Not stated" (the words stay)
  R5.5 same or half-overlapping quote   -> keep the first item of that type
  R5.6 owner from a one-word reply ("Yes.")
R5.1 (quote found word for word) runs at extraction (raid.extract.quote_in_notes).

R5.5 applies within one item type: catalogue case A5 needs an Action and a
Dependency from the same sentence ("If the budget is approved, I'll start …").
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from .schema import NOT_STATED, OwnerState, RaidItem, RaidLog

OWNER_NOT_IN_NOTES = "Owner name not in the notes – owner set to Not stated."
NOT_NEAR_QUOTE = "Owner/date not near the quote – check."
DATE_NOT_IN_NOTES = "Date words not in the notes – due date set to Not stated."
DUPLICATE = "Another item had the same quote and was removed – check."
ONE_WORD_REPLY = "Owner from a one-word reply – check the speaker."
REPLY_NOT_FOUND = "Reply quote not found word for word in the notes – check."

_QUOTE_CHARS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})
_WORD = re.compile(r"[\w'-]+")


@dataclass(frozen=True)
class Attention:
    """One "Needs attention" line: the item's short ID (or "" for the whole log) and the text."""

    short_id: str
    text: str


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").translate(_QUOTE_CHARS)).strip().lower()


def _has_words(words: str, text: str) -> bool:
    """True when `words` appear in `text` as whole words (case and spacing ignored)."""
    needle = _norm(words).strip(" .,;:!?\"'")
    return bool(needle) and re.search(rf"(?<![\w]){re.escape(needle)}(?![\w])", _norm(text)) is not None


def _owner_in(owner: str, text: str) -> bool:
    """A full name, or any part of it ("Aiko" for "Aiko Sato"), appears in the text."""
    return _has_words(owner, text) or any(
        _has_words(part, text) for part in _WORD.findall(owner) if len(part) > 1
    )


def _context(quote: str, lines: list[str]) -> str:
    """The lines that hold the quote, with one line before and after."""
    q = _norm(quote).strip(" \"'")
    hits = [i for i, line in enumerate(lines) if q and (q in _norm(line) or _norm(line) and _norm(line) in q)]
    if not hits:  # quote across lines: find lines that share a long piece with it
        hits = [i for i, line in enumerate(lines) if _overlap(q, _norm(line)) >= 0.5]
    keep = {j for i in hits for j in (i - 1, i, i + 1) if 0 <= j < len(lines)}
    return "\n".join(lines[j] for j in sorted(keep))


def _overlap(a: str, b: str) -> float:
    """Longest shared piece of text, as a share of the shorter text."""
    if not a or not b:
        return 0.0
    match = SequenceMatcher(None, a, b, autojunk=False).find_longest_match(0, len(a), 0, len(b))
    return match.size / min(len(a), len(b))


def _is_duplicate(a: RaidItem, b: RaidItem) -> bool:
    return a.type == b.type and _overlap(_norm(a.source_quote), _norm(b.source_quote)) >= 0.5


def run_checks(log: RaidLog, notes: str) -> list[Attention]:
    """Check every item against the notes; correct the item where the spec says so."""
    kept: list[RaidItem] = []
    duplicates_of: list[RaidItem] = []
    for item in log.items:
        first = next((k for k in kept if _is_duplicate(k, item)), None)
        if first is None:
            kept.append(item)
        elif first not in duplicates_of:
            duplicates_of.append(first)
    log.items = kept
    log.assign_short_ids()

    lines = [line for line in notes.splitlines() if line.strip()]
    attention = [Attention(item.short_id, DUPLICATE) for item in duplicates_of]
    for item in log.items:
        attention += [Attention(item.short_id, text) for text in _check_item(item, notes, lines)]
    order = {item.short_id: n for n, item in enumerate(log.items)}
    return sorted(attention, key=lambda a: order.get(a.short_id, -1))


def _check_item(item: RaidItem, notes: str, lines: list[str]) -> list[str]:
    found: list[str] = []
    if item.owner != NOT_STATED and not _owner_in(item.owner, notes):
        item.owner, item.owner_state = NOT_STATED, OwnerState.NOT_STATED
        found.append(OWNER_NOT_IN_NOTES)
    if item.date_words and not _has_words(item.date_words, notes):
        item.due_date = NOT_STATED
        found.append(DATE_NOT_IN_NOTES)

    near = "\n".join(filter(None, [item.source_quote, item.reply_quote, _context(item.source_quote, lines),
                                   _context(item.reply_quote, lines) if item.reply_quote else ""]))
    owner_far = item.owner != NOT_STATED and not _owner_in(item.owner, near)
    date_far = bool(item.date_words) and DATE_NOT_IN_NOTES not in found and not _has_words(item.date_words, near)
    if owner_far or date_far:
        found.append(NOT_NEAR_QUOTE)

    if item.reply_quote:
        if not _has_words(item.reply_quote, notes):
            found.append(REPLY_NOT_FOUND)
        if len(_WORD.findall(item.reply_quote)) <= 1:
            found.append(ONE_WORD_REPLY)
    return found
