"""Tests for the web page (KAN-21, KAN-22). No API call is made."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).parent.parent / "app.py")


def run_app():
    app = AppTest.from_file(APP, default_timeout=30)
    app.run()
    assert not app.exception, app.exception
    return app


def test_demo_mode_shows_results_without_a_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    assert app.radio[0].value.startswith("Demo")
    assert len(app.selectbox[0].options) == 4
    assert app.subheader[1].value.startswith("2. RAID log")
    assert any("Cost:" in c.value for c in app.caption)
    assert any("Prompt version:" in c.value for c in app.caption)  # R10.1


def test_every_demo_sample_renders(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    for option in app.selectbox[0].options:
        app.selectbox[0].select(option).run()
        assert not app.exception, option
        assert app.subheader[1].value.startswith("2. RAID log · ")


def test_own_notes_mode_asks_for_a_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    app.radio[0].set_value("Your own notes").run()
    assert not app.exception
    assert app.text_input[0].label == "Anthropic API key"
    assert app.button[0].disabled  # no key and no file yet
    assert len(app.subheader) == 1  # no results before a run


def test_upload_is_read_with_its_suffix():
    import importlib.util
    import sys
    from unittest import mock

    with mock.patch.dict(sys.modules, {"streamlit": mock.MagicMock()}):
        spec = importlib.util.spec_from_file_location("app_module", APP)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    vtt = b"WEBVTT\n\n00:00:01.000 --> 00:00:04.000\n<v Ana>We decided to ship on Friday.</v>\n"
    assert module.notes_from_upload("call.vtt", vtt) == "Ana: We decided to ship on Friday."


def test_dollar_signs_show_as_plain_text(monkeypatch):
    """Two "$" signs in Markdown become a maths formula; the page must escape them."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    app.radio[0].set_value("Your own notes").run()
    texts = [m.value for m in app.markdown] + [c.value for c in app.caption]
    for text in texts:
        unescaped = text.replace("\\$", "")
        assert "$" not in unescaped, text
    app.radio[0].set_value("Demo (no API key)").run()
    run_line = next(c.value for c in app.caption if "Cost:" in c.value)
    assert "\\$" in run_line


def _demo_table(app):
    return app.dataframe[0].value


def test_ac30_one_table_with_five_columns(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    table = _demo_table(app)
    assert [c for c in table.columns if c != "ID"] == ["Type", "Item", "Owner", "Due date", "Reviewed"]
    assert not table["Reviewed"].any()  # R8.5: unticked at start
    assert all(item.endswith("✓") or item.endswith("(quote not found)") for item in table["Item"])


def test_ac32_choosing_an_item_shows_its_quote(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    quote_box = next(s for s in app.selectbox if s.label == "Show the quote for an item")
    quote_box.select("ACT-1").run()
    assert any(i.value.startswith("**ACT-1**") for i in app.info)


def test_needs_attention_and_markdown_download_no_excel(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    assert any(m.value == "**Needs attention**" for m in app.markdown)
    labels = [b.label for b in app.get("download_button")]
    assert labels == ["Download Markdown"]  # R8.6: no Excel


def test_ac36_privacy_warning_before_the_upload_box(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    app.radio[0].set_value("Your own notes").run()
    assert app.warning[0].value == "Your notes go to the Anthropic API. Do not upload notes you may not share."
    assert app.date_input[0].label == "Meeting date"


def test_ac37_export_guide_is_linked_and_exists(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    app.radio[0].set_value("Your own notes").run()
    links = [m.value for m in app.markdown if "export-guide.md" in m.value]
    assert links and "blob/main/docs/export-guide.md" in links[0]
    guide = (Path(APP).parent / "docs" / "export-guide.md").read_text(encoding="utf-8")
    assert "## Microsoft Teams" in guide and "## Zoom" in guide


def test_reviewed_ticks_do_not_carry_over_to_another_sample(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    keys = set()
    for option in app.selectbox[0].options:
        app.selectbox[0].select(option).run()
        keys.add(app.dataframe[0].key)
    assert len(keys) == len(app.selectbox[0].options)


def test_demo_shows_needs_attention_lines(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    app = run_app()
    assert app.warning and "Action has no due date." in app.warning[0].value
