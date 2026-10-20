"""Live tests against the real Claude API. They cost a few cents.

Run them on your own machine, with ANTHROPIC_API_KEY in .env:

    pytest -m live -v
"""

import os
from pathlib import Path

import pytest

from raid.extract import extract_items
from raid.parse import read_notes
from raid.schema import NOT_STATED

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

pytestmark = [
    pytest.mark.live,
    pytest.mark.skipif(not os.getenv("ANTHROPIC_API_KEY"), reason="ANTHROPIC_API_KEY is not set"),
]

FIXTURES = Path(__file__).parent / "fixtures"


def test_kan9_extracts_items_from_a_teams_transcript():
    result = extract_items(read_notes(FIXTURES / "teams_call.vtt"))
    print(f"\n{len(result.log.items)} items, {result.input_tokens} in / {result.output_tokens} out, "
          f"{result.seconds:.1f} s")
    for item in result.log.items:
        print(f"  {item.type.value:<10} {item.owner:<12} {item.due_date:<11} {item.description}")
    types = {item.type.value for item in result.log.items}
    assert {"Risk", "Issue", "Action", "Decision"} <= types


def test_kan9_one_hour_transcript_works():
    # About 9,000 words: the length of a 1-hour call.
    base = read_notes(FIXTURES / "teams_call.vtt")
    long_notes = "\n".join(f"[Part {n}]\n{base}" for n in range(1, 44))
    assert len(long_notes.split()) >= 9000
    result = extract_items(long_notes)
    print(f"\n1-hour test: {len(long_notes.split())} words, {result.input_tokens} in / "
          f"{result.output_tokens} out, {result.seconds:.1f} s")
    assert result.log.items
    assert not any("cut off" in w for w in result.warnings)


@pytest.mark.parametrize("name", ["no_owner_1.txt", "no_owner_2.txt"])
def test_kan10_no_owners_in_notes_gives_not_stated(name):
    result = extract_items(read_notes(FIXTURES / name))
    assert result.log.items
    owners = {item.owner for item in result.log.items}
    print(f"\n{name}: owners = {owners}")
    assert owners == {NOT_STATED}


def test_kan11_all_quotes_are_word_for_word():
    result = extract_items(read_notes(FIXTURES / "teams_call.vtt"))
    for item in result.unverified:
        print(f"\nUNVERIFIED: {item.source_quote}")
    assert result.unverified == []
