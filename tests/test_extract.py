"""Tests for KAN-9, KAN-10, and KAN-11 with a simulated Claude client (no API key, no cost)."""

from types import SimpleNamespace

import pytest

from raid.extract import TOOL, TOOL_NAME, ExtractionError, extract_items, quote_in_notes
from raid.schema import NOT_STATED, ItemType, Status

NOTES = """Priya Shah: The vendor may not deliver the API by Friday.
Tom Lee: I will send the test data on 2026-10-26.
Priya Shah: We decided to use PostgreSQL for the new service."""


class FakeClient:
    """Records the request and returns a prepared tool_use answer."""

    def __init__(self, items, stop_reason="tool_use", call_tool=True):
        self.items, self.stop_reason, self.call_tool = items, stop_reason, call_tool
        self.request = None
        self.messages = self

    def create(self, **request):
        self.request = request
        block = (
            SimpleNamespace(type="tool_use", name=TOOL_NAME, input={"items": self.items})
            if self.call_tool
            else SimpleNamespace(type="text", text="Here are the items...")
        )
        return SimpleNamespace(
            content=[block],
            stop_reason=self.stop_reason,
            usage=SimpleNamespace(input_tokens=1200, output_tokens=300),
        )


def item(**changes):
    values = {
        "type": "Risk",
        "description": "The vendor may deliver the API late.",
        "owner": NOT_STATED,
        "due_date": NOT_STATED,
        "source_quote": "The vendor may not deliver the API by Friday.",
    }
    values.update(changes)
    return values


# --- KAN-9: tool use with a JSON schema; every output passes validation ------

def test_request_forces_the_tool_with_a_json_schema():
    client = FakeClient([item()])
    extract_items(NOTES, client=client)
    assert client.request["tools"] == [TOOL]
    assert client.request["tool_choice"] == {"type": "tool", "name": TOOL_NAME}
    assert TOOL["input_schema"]["properties"]["items"]["items"]["properties"]["type"]["enum"] == [
        t.value for t in ItemType
    ]
    assert NOTES in client.request["messages"][0]["content"]


def test_valid_answer_gives_a_validated_log_with_usage():
    client = FakeClient([
        item(),
        item(type="Action", description="Tom sends the test data.", owner="Tom Lee",
             due_date="2026-10-26", source_quote="I will send the test data on 2026-10-26."),
        item(type="Decision", description="Use PostgreSQL.",
             source_quote="We decided to use PostgreSQL for the new service."),
    ])
    result = extract_items(NOTES, client=client, source_file="notes.txt")
    assert [i.type for i in result.log.items] == [ItemType.RISK, ItemType.ACTION, ItemType.DECISION]
    assert all(i.status is Status.OPEN for i in result.log.items)
    assert result.log.source_file == "notes.txt"
    assert (result.input_tokens, result.output_tokens) == (1200, 300)
    assert result.warnings == []


def test_invalid_type_is_dropped_with_a_warning():
    result = extract_items(NOTES, client=FakeClient([item(type="Opportunity"), item()]))
    assert len(result.log.items) == 1
    assert any("Skipped an invalid item" in w for w in result.warnings)


def test_no_tool_call_is_an_error():
    with pytest.raises(ExtractionError):
        extract_items(NOTES, client=FakeClient([], call_tool=False))


def test_cut_off_answer_gives_a_warning():
    result = extract_items(NOTES, client=FakeClient([item()], stop_reason="max_tokens"))
    assert any("cut off" in w for w in result.warnings)


# --- KAN-10: "Not stated", never a guess -----------------------------------

@pytest.mark.parametrize("owner", ["", "   ", None])
def test_empty_owner_becomes_not_stated(owner):
    result = extract_items(NOTES, client=FakeClient([item(owner=owner)]))
    assert result.log.items[0].owner == NOT_STATED


def test_relative_date_becomes_not_stated_with_a_warning():
    result = extract_items(NOTES, client=FakeClient([item(due_date="Friday")]))
    assert result.log.items[0].due_date == NOT_STATED
    assert any("not YYYY-MM-DD" in w for w in result.warnings)


def test_prompt_forbids_guessing():
    client = FakeClient([item()])
    extract_items(NOTES, client=client)
    assert "Never guess an owner" in client.request["system"]
    assert NOT_STATED in client.request["system"]


# --- KAN-11: quote checked word for word -----------------------------------

def test_exact_quote_is_verified():
    result = extract_items(NOTES, client=FakeClient([item()]))
    assert result.log.items[0].quote_verified is True
    assert result.unverified == []


def test_invented_quote_is_flagged():
    result = extract_items(NOTES, client=FakeClient([item(source_quote="The vendor will surely be late.")]))
    assert result.log.items[0].quote_verified is False
    assert len(result.unverified) == 1
    assert any("not found word for word" in w for w in result.warnings)


def test_quote_check_ignores_only_invisible_differences():
    notes = "We   decided to use\nPostgreSQL — it’s faster."
    assert quote_in_notes("We decided to use PostgreSQL - it's faster.", notes)
    assert quote_in_notes('"We decided to use PostgreSQL"', notes)
    assert not quote_in_notes("We decided to use MySQL", notes)
    assert not quote_in_notes("", notes)
