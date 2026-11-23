"""Tests for KAN-7: read .txt, .docx, and .vtt files."""

from pathlib import Path

import pytest

from raid.parse import EmptyNotesError, UnsupportedFileError, read_notes

TEAMS_VTT = """WEBVTT

a1b2c3d4-0001
00:00:01.000 --> 00:00:04.500
<v Priya Shah>Morning all. Let's go through the migration plan.</v>

a1b2c3d4-0002
00:00:05.000 --> 00:00:09.000
<v Priya Shah>The vendor may not deliver the API by Friday.</v>

a1b2c3d4-0003
00:00:09.500 --> 00:00:12.000
<v Tom Lee>I will send the test data by Monday.</v>
"""

ZOOM_VTT = """WEBVTT

1
00:00:01.000 --> 00:00:03.000
Priya Shah: We decided to use PostgreSQL.

2
00:00:03.500 --> 00:00:06.000
Tom Lee: Security sign-off is still pending.
"""


def test_txt_gives_plain_text(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_text("Risk: the vendor is late.\n\n\n\nAction: Tom sends the plan.", encoding="utf-8")
    assert read_notes(notes) == "Risk: the vendor is late.\n\nAction: Tom sends the plan."


def test_txt_with_windows_encoding(tmp_path):
    notes = tmp_path / "notes.txt"
    notes.write_bytes("Café launch – risk noted".encode("cp1252"))
    assert read_notes(notes) == "Café launch – risk noted"


def test_docx_gives_paragraphs_and_tables(tmp_path):
    from docx import Document

    document = Document()
    document.add_paragraph("Weekly call notes")
    document.add_paragraph("The staging server is down.")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Owner"
    table.cell(0, 1).text = "Tom Lee"
    path = tmp_path / "notes.docx"
    document.save(path)

    text = read_notes(path)
    assert "Weekly call notes" in text
    assert "The staging server is down." in text
    assert "Owner | Tom Lee" in text


def test_teams_vtt_removes_time_stamps_and_keeps_speakers(tmp_path):
    path = tmp_path / "call.vtt"
    path.write_text(TEAMS_VTT, encoding="utf-8")
    text = read_notes(path)

    assert "-->" not in text
    assert "00:00" not in text
    assert "a1b2c3d4" not in text
    # Two cues from the same speaker merge into one turn.
    assert text.splitlines() == [
        "Priya Shah: Morning all. Let's go through the migration plan. "
        "The vendor may not deliver the API by Friday.",
        "Tom Lee: I will send the test data by Monday.",
    ]


def test_zoom_vtt_keeps_speakers(tmp_path):
    path = tmp_path / "call.vtt"
    path.write_text(ZOOM_VTT, encoding="utf-8")
    assert read_notes(path).splitlines() == [
        "Priya Shah: We decided to use PostgreSQL.",
        "Tom Lee: Security sign-off is still pending.",
    ]


@pytest.mark.parametrize("name", ["notes.pdf", "notes.mp3", "notes"])
def test_other_file_types_give_a_clear_error(tmp_path, name):
    path = tmp_path / name
    path.write_text("text", encoding="utf-8")
    with pytest.raises(UnsupportedFileError, match="Supported file types: .txt, .docx, .vtt"):
        read_notes(path)


def test_empty_file_gives_a_clear_error(tmp_path):
    path = tmp_path / "empty.txt"
    path.write_text("   \n\n", encoding="utf-8")
    with pytest.raises(EmptyNotesError):
        read_notes(path)


def test_missing_file_gives_a_clear_error(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_notes(tmp_path / "missing.txt")


# --- RAID v2 spec R6.2 (task A6): input warnings and the speaker list ---------------

from raid.parse import (  # noqa: E402
    MAX_WORDS,
    NO_SPEAKERS,
    NOT_ENGLISH,
    TOO_LONG,
    input_warnings,
    speakers,
)

CALL = """Ben Ortiz: Aiko, can you do the deck by Friday?
Aiko Sato: I can try, it is a busy week for the team.
Ben Ortiz: Thanks. We will look at the budget next."""


def test_normal_call_has_no_warnings():
    assert input_warnings(CALL) == []


def test_speakers_in_order_of_first_turn():
    assert speakers(CALL) == ["Ben Ortiz", "Aiko Sato"]


def test_headings_are_not_speakers_and_attendees_are_on_the_call():
    text = ("Present: Gemma Clarke (chair), Felix Novak and Ines Duarte\nAction: Felix to order desks\n"
            "Agreed: keep the date\nQ3 Budget: on track\nBlockers: none\nGemma Clarke: We decided to keep the date.")
    assert speakers(text) == ["Gemma Clarke", "Felix Novak", "Ines Duarte"]


@pytest.mark.parametrize("sample", ["s01_mobile_release.vtt", "s02_crm_migration.txt", "s04_office_move.txt",
                                    "s05_erp_steering.docx", "s08_graduate_onboarding.docx", "s09_audit_prep.txt"])
def test_sample_calls_have_speakers_and_no_warnings(sample):
    # Review of PR 14: minutes with an attendee list are not "no speaker names".
    text = read_notes(Path(__file__).parent.parent / "samples" / sample)
    assert speakers(text)
    assert input_warnings(text) == []


def test_ac25_more_than_15000_words_warns():
    long_call = "Ben Ortiz: " + " ".join(["the plan is on track and we will ship"] * 1700)
    assert len(long_call.split()) > MAX_WORDS == 15_000
    assert TOO_LONG in input_warnings(long_call)


def test_ac26_no_speaker_names_warns():
    minutes = "Minutes of the weekly call.\nThe team agreed to move the release to the next sprint."
    assert NO_SPEAKERS in input_warnings(minutes)


def test_ac26_vtt_with_no_voice_tags_warns(tmp_path):
    path = tmp_path / "call.vtt"
    path.write_text("WEBVTT\n\n1\n00:00:01.000 --> 00:00:04.000\nwe need the deck by Friday and the budget\n",
                    encoding="utf-8")
    assert NO_SPEAKERS in input_warnings(read_notes(path))


def test_ac27_spanish_notes_warn():
    spanish = ("Ana Ruiz: Necesitamos el informe para el viernes. Carlos Gil: Lo haré mañana por la tarde, "
               "pero el proveedor todavía no ha enviado los datos del proyecto.")
    assert NOT_ENGLISH in input_warnings(spanish)


def test_warning_texts_say_what_to_do():
    for text in (TOO_LONG, NO_SPEAKERS, NOT_ENGLISH):
        assert text.endswith(".") and len(text) < 160


def test_speaker_formats_from_other_tools():
    # Review of PR 15: accents, a role in brackets, a time stamp, a bullet.
    text = "Zoë: I'll do it.\nJosé Ruiz: Fine.\nSarah (PM): Next.\n[10:02] Aiko: Yes.\n- Ben Ortiz: Ok."
    assert speakers(text) == ["Zoë", "José Ruiz", "Sarah", "Aiko", "Ben Ortiz"]
