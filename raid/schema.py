"""Data model for one RAID item (story S1-03, KAN-8; RAID v2 spec §4, task A3).

Every output of the tool (Markdown, the web page, the evals) uses these models, so
all outputs have the same fields. ModelItem holds the fields the model fills in; the
tool schema is made from it, so the prompt's tool and the validation never drift
apart. RaidItem adds the fields that only code writes.
"""

from __future__ import annotations

import re
from collections import defaultdict
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

NOT_STATED = "Not stated"

_ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ItemType(str, Enum):
    """The six item types that the tool extracts."""

    RISK = "Risk"
    ASSUMPTION = "Assumption"
    ISSUE = "Issue"
    DEPENDENCY = "Dependency"
    ACTION = "Action"
    DECISION = "Decision"


class Status(str, Enum):
    """Status of an item. The tool always writes OPEN; the user changes it later."""

    OPEN = "Open"
    IN_PROGRESS = "In progress"
    CLOSED = "Closed"


class OwnerState(str, Enum):
    """Did the owner accept the item? (spec §4, R1)."""

    CONFIRMED = "Confirmed"
    TENTATIVE = "Tentative"
    NOT_CONFIRMED = "Not confirmed"
    DECLINED = "Declined"
    NOT_STATED = "Not stated"


_STATE_WORDS = {state.value.lower() for state in OwnerState}

SHORT_ID_PREFIX = {
    ItemType.ACTION: "ACT",
    ItemType.ISSUE: "ISS",
    ItemType.RISK: "RSK",
    ItemType.DEPENDENCY: "DEP",
    ItemType.ASSUMPTION: "ASM",
    ItemType.DECISION: "DEC",
}


class ModelItem(BaseModel):
    """The fields of one item that the model fills in (the tool schema is made from this)."""

    type: ItemType
    description: str = Field(min_length=3, description="What the item is, in one sentence.")
    owner: str = Field(default=NOT_STATED, description=f"Person or role responsible, or '{NOT_STATED}'. Never a state.")
    owner_state: OwnerState | None = Field(default=None, description="Did the owner accept? See the rules.")
    owner_note: str = Field(default="", description="Short note on the owner, for example 'ask Tom', or ''.")
    due_date: str = Field(default=NOT_STATED, description=f"YYYY-MM-DD, or '{NOT_STATED}'.")
    date_words: str = Field(default="", description="The exact words in the notes that give the date, or ''.")
    source_quote: str = Field(min_length=1, description="Exact words from the notes.")
    reply_quote: str = Field(default="", description="Exact words of the reply that names the owner, or ''.")

    @field_validator("description", "source_quote", "owner_note", "date_words", "reply_quote", mode="before")
    @classmethod
    def _strip(cls, value: str | None) -> str:
        if value is None:
            return ""
        return value.strip() if isinstance(value, str) else value

    @field_validator("owner", mode="before")
    @classmethod
    def _owner_or_not_stated(cls, value: str | None) -> str:
        if value is None or not str(value).strip():
            return NOT_STATED
        return str(value).strip()

    @field_validator("due_date", mode="before")
    @classmethod
    def _date_or_not_stated(cls, value: str | None) -> str:
        if value is None or not str(value).strip():
            return NOT_STATED
        text = str(value).strip()
        if text.lower() == NOT_STATED.lower():
            return NOT_STATED
        if not _ISO_DATE.match(text):
            raise ValueError(f"due_date must be YYYY-MM-DD or '{NOT_STATED}', not '{text}'")
        return text

    @model_validator(mode="after")
    def _owner_and_state_agree(self):
        if self.owner.lower() in _STATE_WORDS:  # a state is never an owner (spec §4)
            self.owner = NOT_STATED
        if self.owner_state is None:  # v1 outputs: a named owner was an agreed owner
            self.owner_state = OwnerState.NOT_STATED if self.owner == NOT_STATED else OwnerState.CONFIRMED
        if self.owner == NOT_STATED and self.owner_state in (
            OwnerState.CONFIRMED, OwnerState.TENTATIVE, OwnerState.DECLINED
        ):
            self.owner_state = OwnerState.NOT_STATED  # nobody named, so nobody agreed
        return self


class RaidItem(ModelItem):
    """One item in the RAID log: the model's fields plus the fields that code writes."""

    status: Status = Status.OPEN
    quote_verified: bool | None = Field(
        default=None, description="True when the quote was found word for word in the notes (KAN-11)."
    )
    short_id: str = Field(default="", description="ACT-1, RSK-2 …, given by code (spec R8.2).")


class RaidLog(BaseModel):
    """All items that the tool found in one file of notes."""

    source_file: str = ""
    items: list[RaidItem] = Field(default_factory=list)

    def by_type(self) -> dict[ItemType, list[RaidItem]]:
        """Group the items by type, in the fixed order of ItemType (empty types included)."""
        groups: dict[ItemType, list[RaidItem]] = defaultdict(list)
        for item in self.items:
            groups[item.type].append(item)
        return {item_type: groups[item_type] for item_type in ItemType}

    def assign_short_ids(self) -> None:
        """Give each item a short ID by type and order: ACT-1, ACT-2, RSK-1 … (spec R8.2)."""
        counts: dict[ItemType, int] = defaultdict(int)
        for item in self.items:
            counts[item.type] += 1
            item.short_id = f"{SHORT_ID_PREFIX[item.type]}-{counts[item.type]}"


def _inline(node, defs: dict):
    """Resolve $ref and drop titles, so the tool schema is one plain JSON schema."""
    if isinstance(node, dict):
        if "$ref" in node:
            return _inline(defs[node["$ref"].split("/")[-1]], defs)
        if "anyOf" in node:  # Optional[X] -> X (the model always sends a value)
            options = [o for o in node["anyOf"] if o.get("type") != "null"]
            if len(options) == 1:
                merged = {k: v for k, v in node.items() if k not in ("anyOf", "default")}
                return {**_inline(options[0], defs), **_inline(merged, defs)}
        return {k: _inline(v, defs) for k, v in node.items() if k not in ("title", "default", "$defs")}
    if isinstance(node, list):
        return [_inline(v, defs) for v in node]
    return node


def tool_input_schema() -> dict:
    """The tool's input schema, made from ModelItem; every field is required."""
    raw = ModelItem.model_json_schema()
    item = _inline(raw, raw.get("$defs", {}))
    item["required"] = list(ModelItem.model_fields)
    for prop in item["properties"].values():
        prop.pop("minLength", None)  # length is checked by pydantic, with a clear warning
    return {"type": "object", "properties": {"items": {"type": "array", "items": item}}, "required": ["items"]}
