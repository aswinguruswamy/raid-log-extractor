"""Data model for one RAID item (story S1-03, KAN-8).

Every output of the tool (Excel, Markdown, the web page, the evals) uses these
models, so all outputs have the same fields.
"""

from __future__ import annotations

import re
from collections import defaultdict
from enum import Enum

from pydantic import BaseModel, Field, field_validator

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


class RaidItem(BaseModel):
    """One item in the RAID log."""

    type: ItemType
    description: str = Field(min_length=3, description="What the item is, in one sentence.")
    owner: str = Field(default=NOT_STATED, description="Person responsible, or 'Not stated'.")
    due_date: str = Field(default=NOT_STATED, description="YYYY-MM-DD, or 'Not stated'.")
    status: Status = Status.OPEN
    source_quote: str = Field(min_length=1, description="Exact words from the notes.")

    @field_validator("description", "source_quote", mode="before")
    @classmethod
    def _strip(cls, value: str) -> str:
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
