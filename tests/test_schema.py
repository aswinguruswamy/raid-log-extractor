"""Tests for KAN-8: the data model for one RAID item."""

import pytest
from pydantic import ValidationError

from raid.schema import NOT_STATED, ItemType, RaidItem, RaidLog, Status


def make(**changes):
    values = {
        "type": "Risk",
        "description": "The vendor may not deliver the API by Friday.",
        "source_quote": "The vendor may not deliver the API by Friday.",
    }
    values.update(changes)
    return RaidItem(**values)


def test_six_item_types():
    assert [t.value for t in ItemType] == [
        "Risk", "Assumption", "Issue", "Dependency", "Action", "Decision",
    ]


def test_all_fields_and_defaults():
    item = make()
    assert item.type is ItemType.RISK
    assert item.owner == NOT_STATED
    assert item.due_date == NOT_STATED
    assert item.status is Status.OPEN


@pytest.mark.parametrize("owner", [None, "", "   "])
def test_empty_owner_becomes_not_stated(owner):
    assert make(owner=owner).owner == NOT_STATED


def test_valid_due_date():
    assert make(due_date="2026-10-26").due_date == "2026-10-26"


@pytest.mark.parametrize("bad_date", ["next Friday", "26/10/2026", "Oct 26"])
def test_invalid_due_date_is_rejected(bad_date):
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
        make(due_date=bad_date)


def test_unknown_type_is_rejected():
    with pytest.raises(ValidationError):
        make(type="Opportunity")


def test_source_quote_is_required():
    with pytest.raises(ValidationError):
        make(source_quote="")


def test_log_groups_items_by_type_in_fixed_order():
    log = RaidLog(items=[make(type="Action"), make(type="Risk"), make(type="Action")])
    groups = log.by_type()
    assert list(groups) == list(ItemType)
    assert len(groups[ItemType.ACTION]) == 2
    assert len(groups[ItemType.RISK]) == 1
    assert groups[ItemType.DECISION] == []
