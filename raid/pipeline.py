"""From notes to a checked RAID log, before anything is shown (RAID v2 spec R4-R7, R10; task A7).

    extract (model) -> on-the-call check -> dates (code) -> checks (code) -> Needs attention

The page, the Markdown file and the evals all use analyse(), so they show the same facts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .checks import Attention, run_checks
from .dates import apply_dates
from .extract import DEFAULT_MODEL, extract_items
from .parse import input_warnings, speakers
from .schema import NOT_STATED, ItemType, OwnerState, RaidLog

NOT_ON_CALL = "not on the call"
STATE_LINES = {
    OwnerState.TENTATIVE: "Owner tentative – confirm.",
    OwnerState.NOT_CONFIRMED: "Owner not confirmed – confirm.",
    OwnerState.DECLINED: "Owner declined – reassign.",
}
NO_DUE_DATE = "Action has no due date."


@dataclass
class Analysis:
    """One run: the checked log, the Needs attention lines and the run details (R10.1)."""

    log: RaidLog
    attention: list[Attention] = field(default_factory=list)
    model: str = DEFAULT_MODEL
    prompt_version: str = ""
    run_date: date | None = None
    source_file: str = ""
    meeting_date: date | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)  # extraction warnings (skipped items, quotes)

    def lines_for(self, short_id: str) -> list[str]:
        return [a.text for a in self.attention if a.short_id == short_id]

    def to_saved(self) -> dict:
        """A JSON-ready copy (demo files and eval outputs)."""
        return {
            "sample": self.source_file, "model": self.model, "prompt_version": self.prompt_version,
            "run_date": self.run_date.isoformat() if self.run_date else None,
            "meeting_date": self.meeting_date.isoformat() if self.meeting_date else None,
            "input_tokens": self.input_tokens, "output_tokens": self.output_tokens,
            "seconds": round(self.seconds, 2), "warnings": self.warnings,
            "needs_attention": [[a.short_id, a.text] for a in self.attention],
            "items": [item.model_dump(mode="json") for item in self.log.items],
        }

    @classmethod
    def from_saved(cls, data: dict) -> Analysis:
        """Read a saved run back. The items keep their saved short IDs, dates and checks."""
        def day(value):
            return date.fromisoformat(value) if value else None

        log = RaidLog(source_file=data.get("sample", ""), items=data.get("items", []))
        if "needs_attention" in data:
            attention = [Attention(short_id, text) for short_id, text in data["needs_attention"]]
        else:  # a v1 file: rebuild the lines that need no notes (owner states, no due date)
            attention = needs_attention(log, [], [])
        return cls(
            log=log,
            attention=attention,
            model=data.get("model", DEFAULT_MODEL), prompt_version=str(data.get("prompt_version", "1")),
            run_date=day(data.get("run_date")), source_file=data.get("sample", ""),
            meeting_date=day(data.get("meeting_date")), input_tokens=data.get("input_tokens", 0),
            output_tokens=data.get("output_tokens", 0), seconds=data.get("seconds", 0.0),
            warnings=data.get("warnings", []),
        )


def _first_names(names: list[str]) -> set[str]:
    return {part.lower() for name in names for part in re.findall(r"[\w'-]+", name)}


def mark_not_on_the_call(log: RaidLog, notes: str) -> None:
    """A named person who is not on the call cannot be a confirmed owner (spec R2.4, B7).
    Applies only when the notes show who was on the call."""
    on_call = _first_names(speakers(notes))
    if not on_call:
        return
    for item in log.items:
        if item.owner == NOT_STATED or item.owner_state not in (OwnerState.CONFIRMED, OwnerState.TENTATIVE):
            continue
        if not _first_names([item.owner]) & on_call:
            item.owner_state = OwnerState.NOT_CONFIRMED
            item.owner_note = NOT_ON_CALL


def needs_attention(log: RaidLog, general: list[str], check_lines: list[Attention]) -> list[Attention]:
    """R7.1: general lines first, then per item (log order): owner state, no due date, checks."""
    attention = [Attention("", text) for text in general]
    by_item: dict[str, list[str]] = {}
    for item in log.items:
        texts = []
        if item.owner_state in STATE_LINES:
            line = STATE_LINES[item.owner_state]
            note = item.owner_note
            if note and not note.lower().startswith(item.owner_state.value.lower()):  # no "declined (declined …)"
                line = line.replace(" – ", f" ({note}) – ")
            texts.append(line)
        if item.type is ItemType.ACTION and item.due_date == NOT_STATED:
            texts.append(NO_DUE_DATE)
        by_item[item.short_id] = texts
    for line in check_lines:
        by_item.setdefault(line.short_id, []).append(line.text)
    for item in log.items:
        attention += [Attention(item.short_id, text) for text in by_item.get(item.short_id, [])]
    return attention


def analyse(notes: str, meeting_date: date | None, *, client=None, model: str = DEFAULT_MODEL,
            source_file: str = "", run_date: date | None = None) -> Analysis:
    """Extract the items, then run the code steps. Raises NotesTooLongError on a cut-off answer."""
    result = extract_items(notes, client=client, model=model, source_file=source_file)
    log = result.log
    mark_not_on_the_call(log, notes)
    general = apply_dates(log, meeting_date) + input_warnings(notes)
    check_lines = run_checks(log, notes)

    attention = needs_attention(log, general, check_lines)

    return Analysis(
        log=log, attention=attention, model=result.model, prompt_version=result.prompt_version,
        run_date=run_date or date.today(), source_file=source_file, meeting_date=meeting_date,
        input_tokens=result.input_tokens, output_tokens=result.output_tokens, seconds=result.seconds,
        warnings=result.warnings,
    )
