"""Tests for KAN-13 (command line) and KAN-14 (cost and time). v2 writes Markdown, not Excel (task A9)."""

from raid.__main__ import main
from raid.cost import COST_TARGET_USD, format_run, run_cost

from .test_extract import NOTES, FakeClient, item

# --- KAN-13: command line ---------------------------------------------------

def test_command_writes_markdown_and_no_excel(tmp_path, capsys):
    # RAID v2 spec R8.6, R9.1 (task A9).
    notes = tmp_path / "notes.txt"
    notes.write_text(NOTES, encoding="utf-8")
    out = tmp_path / "output"
    code = main(["extract", str(notes), "--out", str(out), "--meeting-date", "2026-12-01"],
                client=FakeClient([item()]))
    assert code == 0
    text = (out / "notes_raid_log.md").read_text(encoding="utf-8")
    assert "## Run details" in text and "2026-12-01" in text
    assert not list(out.glob("*.xlsx"))
    printed = capsys.readouterr().out
    assert "Risk          1" in printed
    assert "Saved:" in printed


def test_command_rejects_unsupported_file(tmp_path, capsys):
    notes = tmp_path / "notes.pdf"
    notes.write_text("x", encoding="utf-8")
    assert main(["extract", str(notes)], client=FakeClient([])) == 2
    assert "Supported file types" in capsys.readouterr().err


def test_command_needs_an_api_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("raid.__main__._load_dotenv", lambda: None)
    notes = tmp_path / "notes.txt"
    notes.write_text(NOTES, encoding="utf-8")
    assert main(["extract", str(notes)]) == 2
    assert "ANTHROPIC_API_KEY is not set" in capsys.readouterr().err


# --- KAN-14: cost and time --------------------------------------------------

def test_cost_for_sonnet():
    # 12,000 in x $2/M + 2,000 out x $10/M = $0.024 + $0.020
    assert abs(run_cost("claude-sonnet-5-5", 12_000, 2_000) - 0.044) < 1e-9


def test_one_hour_transcript_estimate_is_under_target():
    assert run_cost("claude-sonnet-5-5", 13_000, 3_000) < COST_TARGET_USD


def test_unknown_model_has_no_cost():
    assert run_cost("some-other-model", 1000, 1000) is None


def test_command_prints_tokens_cost_and_time(tmp_path, capsys):
    notes = tmp_path / "notes.txt"
    notes.write_text(NOTES, encoding="utf-8")
    main(["extract", str(notes), "--out", str(tmp_path)], client=FakeClient([item()]))
    line = capsys.readouterr().out
    assert "Tokens: 1,200 in / 300 out" in line
    assert "Cost: $0.0054" in line  # 1,200 x $2/M + 300 x $10/M
    assert "Time:" in line


def test_format_run_with_unknown_model():
    assert "unknown" in format_run("x", 1, 1, 0.5)
