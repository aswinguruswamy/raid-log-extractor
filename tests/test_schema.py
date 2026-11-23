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


# --- RAID v2 (task A3, spec §4): owner state, notes, date words, reply quote, short ID ---

from raid.schema import ModelItem, OwnerState, tool_input_schema  # noqa: E402


def test_five_owner_states():
    assert [s.value for s in OwnerState] == [
        "Confirmed", "Tentative", "Not confirmed", "Declined", "Not stated",
    ]


def test_v2_fields_and_defaults():
    item = make(type="Action", owner="Aiko", owner_state="Tentative", owner_note="ask Tom",
                date_words="by Friday", reply_quote="I can try.")
    assert item.owner_state is OwnerState.TENTATIVE
    assert (item.owner_note, item.date_words, item.reply_quote, item.short_id) == (
        "ask Tom", "by Friday", "I can try.", "")


def test_missing_state_is_confirmed_for_a_named_owner_and_not_stated_without_one():
    # v1 outputs have no owner_state: a named owner was an agreed owner.
    assert make(owner="Aiko").owner_state is OwnerState.CONFIRMED
    assert make().owner_state is OwnerState.NOT_STATED


@pytest.mark.parametrize("state_word", ["Not confirmed", "Tentative", "Declined", "confirmed"])
def test_owner_never_holds_a_state(state_word):
    item = make(owner=state_word, owner_state="Not confirmed")
    assert item.owner == NOT_STATED
    assert item.owner_state is OwnerState.NOT_CONFIRMED


@pytest.mark.parametrize("state", ["Confirmed", "Tentative", "Declined"])
def test_no_owner_cannot_be_agreed(state):
    assert make(owner_state=state).owner_state is OwnerState.NOT_STATED


def test_no_owner_can_be_not_confirmed_for_a_list_of_people():
    # Spec R2.2: "Jon, Alisa, Crab – do X, Y, Z" gives owner Not stated, state Not confirmed.
    item = make(type="Action", owner_state="Not confirmed", owner_note="owners by list: Jon, Alisa – confirm")
    assert (item.owner, item.owner_state) == (NOT_STATED, OwnerState.NOT_CONFIRMED)


def test_short_ids_by_type_and_order():
    log = RaidLog(items=[make(type="Action"), make(type="Risk"), make(type="Action"),
                         make(type="Decision"), make(type="Issue"), make(type="Dependency"),
                         make(type="Assumption")])
    log.assign_short_ids()
    assert [i.short_id for i in log.items] == [
        "ACT-1", "RSK-1", "ACT-2", "DEC-1", "ISS-1", "DEP-1", "ASM-1"]


def test_tool_schema_comes_from_the_model_item():
    schema = tool_input_schema()
    item = schema["properties"]["items"]["items"]
    assert set(item["properties"]) == set(ModelItem.model_fields)
    assert set(item["required"]) == set(ModelItem.model_fields)
    assert item["properties"]["type"]["enum"] == [t.value for t in ItemType]
    assert item["properties"]["owner_state"]["enum"] == [s.value for s in OwnerState]
    assert "$ref" not in str(schema) and "$defs" not in str(schema)
    # Code fields are not asked from the model.
    for code_field in ("status", "quote_verified", "short_id"):
        assert code_field not in item["properties"]
