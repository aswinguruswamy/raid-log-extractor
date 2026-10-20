"""Find the six item types in the notes with Claude.

Stories:
  S1-04 (KAN-9)  Claude tool use with a JSON schema; every output passes validation.
  S1-05 (KAN-10) "Not stated" when the notes give no owner or date. No guesses.
  S1-06 (KAN-11) A source quote for each item, checked word for word against the notes.
"""

from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass, field

from pydantic import ValidationError

from .schema import NOT_STATED, ItemType, RaidItem, RaidLog

DEFAULT_MODEL = os.getenv("RAID_MODEL", "claude-sonnet-5-5")
MAX_OUTPUT_TOKENS = 8000
TOOL_NAME = "record_raid_items"

SYSTEM_PROMPT = f"""You read the notes or transcript of a project team call and record its RAID items.

Item types (use exactly one per item):
- Risk: something that MAY happen in the future and would hurt the project.
- Assumption: something the team treats as true without proof.
- Issue: a problem that is happening NOW.
- Dependency: work that needs another team, vendor, or task first.
- Action: a task that a person agreed to do.
- Decision: a choice the team made in the call.

Rules:
1. Record only what the notes say. Do not add advice or items of your own.
2. owner: the person the notes name as responsible. If the notes name nobody, write "{NOT_STATED}". Never guess an owner from who spoke.
3. due_date: YYYY-MM-DD only when the notes give a full calendar date. For a relative date such as "by Friday" or "next week", write "{NOT_STATED}" and keep the relative words in the description.
4. description: one clear sentence in your own words.
5. source_quote: copy the exact words from the notes that support the item. Copy them character for character, as one continuous span, 5 to 40 words. Do not fix spelling or grammar in the quote.
6. One fact gives one item. Do not repeat an item under two types.
7. If the notes have no items of a type, record none of that type.

Call the {TOOL_NAME} tool once with all items."""

TOOL = {
    "name": TOOL_NAME,
    "description": "Record every RAID item found in the call notes.",
    "input_schema": {
        "type": "object",
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": [t.value for t in ItemType]},
                        "description": {"type": "string"},
                        "owner": {"type": "string", "description": f"Named person, or '{NOT_STATED}'."},
                        "due_date": {"type": "string", "description": f"YYYY-MM-DD, or '{NOT_STATED}'."},
                        "source_quote": {"type": "string", "description": "Exact words from the notes."},
                    },
                    "required": ["type", "description", "owner", "due_date", "source_quote"],
                },
            }
        },
        "required": ["items"],
    },
}


@dataclass
class ExtractionResult:
    log: RaidLog
    model: str
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)

    @property
    def unverified(self) -> list[RaidItem]:
        return [item for item in self.log.items if item.quote_verified is False]


class ExtractionError(RuntimeError):
    """Claude did not return the RAID items in the expected form."""


def extract_items(text: str, *, client=None, model: str = DEFAULT_MODEL, source_file: str = "") -> ExtractionResult:
    """Send the notes to Claude and return a validated RAID log."""
    if client is None:
        import anthropic

        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    started = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=MAX_OUTPUT_TOKENS,
        system=SYSTEM_PROMPT,
        tools=[TOOL],
        tool_choice={"type": "tool", "name": TOOL_NAME},
        messages=[{"role": "user", "content": f"<notes>\n{text}\n</notes>"}],
    )
    seconds = time.perf_counter() - started

    raw_items = _tool_input(response).get("items")
    if not isinstance(raw_items, list):
        raise ExtractionError("Claude's answer has no 'items' list.")

    warnings: list[str] = []
    if getattr(response, "stop_reason", None) == "max_tokens":
        warnings.append("The answer was cut off at the output limit; some items may be missing.")

    items = [item for raw in raw_items if (item := _to_item(raw, text, warnings)) is not None]

    usage = getattr(response, "usage", None)
    return ExtractionResult(
        log=RaidLog(source_file=source_file, items=items),
        model=model,
        input_tokens=getattr(usage, "input_tokens", 0) or 0,
        output_tokens=getattr(usage, "output_tokens", 0) or 0,
        seconds=seconds,
        warnings=warnings,
    )


def _tool_input(response) -> dict:
    for block in getattr(response, "content", []) or []:
        if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == TOOL_NAME:
            return block.input or {}
    raise ExtractionError("Claude did not call the record_raid_items tool.")


def _to_item(raw: dict, notes: str, warnings: list[str]) -> RaidItem | None:
    """Validate one item. Repair a bad date to 'Not stated'; drop items that cannot be repaired."""
    if not isinstance(raw, dict):
        warnings.append(f"Skipped an item that was not an object: {raw!r}")
        return None
    data = {key: raw.get(key) for key in ("type", "description", "owner", "due_date", "source_quote")}
    try:
        item = RaidItem(**data)
    except ValidationError as error:
        if any(e["loc"] == ("due_date",) for e in error.errors()):
            warnings.append(f"Date '{data['due_date']}' is not YYYY-MM-DD; written as '{NOT_STATED}'.")
            data["due_date"] = NOT_STATED
            try:
                item = RaidItem(**data)
            except ValidationError as second:
                warnings.append(f"Skipped an invalid item: {second.errors()[0]['msg']}")
                return None
        else:
            warnings.append(f"Skipped an invalid item: {error.errors()[0]['msg']}")
            return None
    item.quote_verified = quote_in_notes(item.source_quote, notes)
    if not item.quote_verified:
        warnings.append(f"Quote not found word for word in the notes: \"{item.source_quote[:80]}\"")
    return item


# --- KAN-11: word-for-word quote check ------------------------------------

_QUOTE_CHARS = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-"})


def _normalize(text: str) -> str:
    """Ignore only differences a reader cannot see: spaces, line breaks, and curly quotes."""
    return re.sub(r"\s+", " ", text.translate(_QUOTE_CHARS)).strip()


def quote_in_notes(quote: str, notes: str) -> bool:
    """True when the quote appears word for word in the notes."""
    quote_n = _normalize(quote).strip(" \"'")
    return bool(quote_n) and quote_n in _normalize(notes)
