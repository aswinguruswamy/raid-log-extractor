"""Code checks before the log is shown (RAID v2 spec R5, constitution P2, task A5).

Each check writes a "Needs attention" line for an item; some also correct the item:
  R5.2 owner name not in the notes      -> owner and state "Not stated"
  R5.3 owner or date words not near the quote (quote, reply quote, turn before/after)
  R5.4 date words not in the notes      -> due date "Not stated" (the words stay)
  R5.5 same or half-overlapping quote   -> keep the first item of that type
  R5.6 owner from a one-word reply ("Yes.")
R5.1 (quote found word for word) runs at extraction (raid.extract.quote_in_notes).

R5.5 applies within one item type and one task: catalogue case A5 needs an Action and
a Dependency from the same sentence ("If the budget is approved, I'll start …"), and
case B1 needs three Actions from one sentence ("Jon, Alisa, Crab – X, Y and Z").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

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


# Words that are also common English words do not prove a name ("Will" in "I will").
_COMMON_WORDS = {
    "will", "may", "can", "team", "data", "the", "and", "lead", "owner", "everyone", "all", "someone",
    "ops", "it", "we", "us", "they", "he", "she", "group", "new", "head", "manager", "person",
}


def _owner_in(owner: str, text: str) -> bool:
    """The full name (any case), or a capitalised part of it that is not a common word
    ("Aiko" for "Aiko Sato"; case kept), appears in the text."""
    if owner.strip().lower() not in _COMMON_WORDS and _has_words(owner, text):
        return True
    flat = re.sub(r"\s+", " ", (text or "").translate(_QUOTE_CHARS))
    return any(
        re.search(rf"(?<![\w]){re.escape(part)}(?![\w])", flat)
        for part in _WORD.findall(owner)
        if len(part) > 1 and part[0].isupper() and part.lower() not in _COMMON_WORDS
    )


class _Notes:
    """The notes as one normalised string, with the start of each line."""

    def __init__(self, notes: str):
        self.lines = [line for line in notes.splitlines() if line.strip()]
        self.text, self.starts = "", []
        for line in self.lines:
            self.starts.append(len(self.text))
            self.text += _norm(line) + " "

    def span(self, quote: str) -> tuple[int, int] | None:
        q = _norm(quote).strip(" \"'")
        pos = self.text.find(q) if q else -1
        return (pos, pos + len(q)) if pos >= 0 else None

    def context(self, quote: str) -> str:
        """The lines that hold the quote, with one line before and after ('' if not found)."""
        span = self.span(quote)
        if span is None:
            return ""
        ends = self.starts[1:] + [len(self.text)]
        hit = [i for i, (a, b) in enumerate(zip(self.starts, ends)) if a < span[1] and span[0] < b]
        keep = {j for i in hit for j in (i - 1, i, i + 1) if 0 <= j < len(self.lines)}
        return "\n".join(self.lines[j] for j in sorted(keep))


def _overlap(a: tuple[int, int] | None, b: tuple[int, int] | None) -> float:
    """Shared part of two quote places in the notes, as a share of the shorter quote."""
    if a is None or b is None:
        return 0.0
    shared = min(a[1], b[1]) - max(a[0], b[0])
    return max(shared, 0) / max(min(a[1] - a[0], b[1] - b[0]), 1)


_STOP = {"the", "a", "an", "to", "of", "and", "for", "on", "in", "by", "with", "do", "is", "be", "will"}


def _task_words(text: str) -> set[str]:
    text = re.sub(r"\([^)]*\)", " ", text.lower())  # "(owner to be confirmed …)" is not the task
    return {w for w in _WORD.findall(text) if w not in _STOP}


def _same_task(a: str, b: str) -> bool:
    """Descriptions share half or more of the shorter one's words (stop words and text in
    brackets left out)."""
    wa, wb = _task_words(a), _task_words(b)
    return bool(wa and wb) and len(wa & wb) / min(len(wa), len(wb)) >= 0.5


def _is_duplicate(a: RaidItem, b: RaidItem, notes: _Notes) -> bool:
    """Same type, the same quote or quotes that cover the same place in the notes by half or
    more, and the same task (one sentence can hold three tasks: spec R2.2, catalogue B1)."""
    if a.type != b.type or not _same_task(a.description, b.description):
        return False
    if a.owner_note.lower().startswith("owners by list") and b.owner_note.lower().startswith("owners by list"):
        return False  # one sentence, several tasks (R2.2)
    if _norm(a.source_quote) == _norm(b.source_quote):
        return True
    return _overlap(notes.span(a.source_quote), notes.span(b.source_quote)) >= 0.5


def run_checks(log: RaidLog, notes: str) -> list[Attention]:
    """Check every item against the notes; correct the item where the spec says so."""
    parsed = _Notes(notes)
    kept: list[RaidItem] = []
    duplicates_of: list[RaidItem] = []
    for item in log.items:
        first = next((k for k in kept if _is_duplicate(k, item, parsed)), None)
        if first is None:
            kept.append(item)
        elif first not in duplicates_of:
            duplicates_of.append(first)
    log.items = kept
    log.assign_short_ids()

    attention = [Attention(item.short_id, DUPLICATE) for item in duplicates_of]
    for item in log.items:
        attention += [Attention(item.short_id, text) for text in _check_item(item, notes, parsed)]
    order = {item.short_id: n for n, item in enumerate(log.items)}
    return sorted(attention, key=lambda a: order.get(a.short_id, -1))


def _check_item(item: RaidItem, notes: str, parsed: _Notes) -> list[str]:
    found: list[str] = []
    if item.owner != NOT_STATED and not _owner_in(item.owner, notes):
        item.owner, item.owner_state = NOT_STATED, OwnerState.NOT_STATED
        found.append(OWNER_NOT_IN_NOTES)
    if item.date_words and not _has_words(item.date_words, notes):
        item.due_date = NOT_STATED
        found.append(DATE_NOT_IN_NOTES)

    near = "\n".join(filter(None, [item.source_quote, item.reply_quote, parsed.context(item.source_quote),
                                   parsed.context(item.reply_quote) if item.reply_quote else ""]))
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
