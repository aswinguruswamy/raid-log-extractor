"""The page table: one row per item (RAID v2 spec R8.1, R8.2, R8.4, R8.5; task A9).

Columns: Type · Item · Owner · Due date · Reviewed. Rows with a Needs attention line come
first, then by type (Action, Issue, Risk, Dependency, Assumption, Decision), then by short ID.
States and "quote not found" are words, never colour only (N7).
"""

from __future__ import annotations

from .checks import Attention
from .schema import NOT_STATED, ItemType, OwnerState, RaidItem, RaidLog

COLUMNS = ["Type", "Item", "Owner", "Due date", "Reviewed"]
TYPE_ORDER = [ItemType.ACTION, ItemType.ISSUE, ItemType.RISK, ItemType.DEPENDENCY,
              ItemType.ASSUMPTION, ItemType.DECISION]


def owner_cell(item: RaidItem) -> str:
    """'Aiko (tentative)'; the state is left out when it is Confirmed or says the same as the owner."""
    if item.owner_state in (OwnerState.CONFIRMED, None) or (
        item.owner == NOT_STATED and item.owner_state is OwnerState.NOT_STATED
    ):
        return item.owner
    return f"{item.owner} ({item.owner_state.value.lower()})"


def item_cell(item: RaidItem) -> str:
    mark = "✓" if item.quote_verified else "(quote not found)"
    return f"{item.short_id} {item.description} {mark}"


def due_cell(item: RaidItem) -> str:
    return f"{item.due_date} · {item.date_words}" if item.date_words else item.due_date


def _id_number(item: RaidItem) -> int:
    tail = item.short_id.rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else 0


def sorted_items(log: RaidLog, attention: list[Attention]) -> list[RaidItem]:
    flagged = {a.short_id for a in attention if a.short_id}
    return sorted(log.items, key=lambda i: (i.short_id not in flagged, TYPE_ORDER.index(i.type), _id_number(i)))


def table_rows(analysis, reviewed: set[str]) -> list[dict]:
    """Rows for the page table; 'ID' is a hidden key column for the Reviewed ticks."""
    return [
        {"Type": item.type.value, "Item": item_cell(item), "Owner": owner_cell(item), "Due date": due_cell(item),
         "Reviewed": item.short_id in reviewed, "ID": item.short_id}
        for item in sorted_items(analysis.log, analysis.attention)
    ]
