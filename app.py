"""RAID Log Extractor web page (stories S3-01 KAN-21 and S3-02 KAN-22; RAID v2 task A9).

Run it with:  streamlit run app.py

Two modes:
  * Demo: saved results for sample calls. No API key and no API call.
  * Your own notes: upload a .txt, .docx, or .vtt file and use your own Anthropic API key.

The page shows Needs attention, one table (Type · Item · Owner · Due date · Reviewed), the
quote of each item, and a Markdown download (RAID v2 spec R7-R12). v2 writes no Excel file.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from raid.cost import format_run
from raid.export import to_markdown
from raid.parse import EmptyNotesError, UnsupportedFileError, input_warnings, read_notes
from raid.pipeline import Analysis
from raid.view import COLUMNS, table_rows

ROOT = Path(__file__).parent
DEMO_DIR = ROOT / "demo"
SAMPLES_DIR = ROOT / "samples"
REPO_URL = "https://github.com/aswinguruswamy/raid-log-extractor"
EXPORT_GUIDE_URL = f"{REPO_URL}/blob/main/docs/export-guide.md"
MAX_UPLOAD_MB = 2  # keep in step with server.maxUploadSize in .streamlit/config.toml

DEMO = "Demo (no API key)"
OWN = "Your own notes"
PRIVACY_WARNING = "Your notes go to the Anthropic API. Do not upload notes you may not share."  # spec R11.1

load_dotenv()


# --- data -------------------------------------------------------------------

def load_demo(stem: str) -> dict:
    """A saved run plus its label: the checked log, Needs attention and run details."""
    data = json.loads((DEMO_DIR / f"{stem}.json").read_text(encoding="utf-8"))
    data["analysis"] = Analysis.from_saved(data)
    return data


def demo_options() -> dict[str, str]:
    """Select-box label -> file stem."""
    options = {}
    for path in sorted(DEMO_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        options[f"{data['label']} · {data['format']}"] = path.stem
    return options


def plain(text: str) -> str:
    """Escape "$" so that Streamlit does not show the text between two "$" signs as a maths formula."""
    return text.replace("$", "\\$")


def notes_from_upload(name: str, content: bytes) -> str:
    """Write the upload to a temporary file with the same suffix, then read it."""
    suffix = Path(name).suffix.lower()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / f"upload{suffix}"
        path.write_bytes(content)
        return read_notes(path)


def run_details(analysis: Analysis) -> str:
    """Model, prompt version, run date, source file and meeting date (spec R10.1)."""
    meeting = analysis.meeting_date.isoformat() if analysis.meeting_date else "not entered"
    run_day = analysis.run_date.isoformat() if analysis.run_date else "-"
    return (f"Model: {analysis.model} · Prompt version: {analysis.prompt_version} · Run date: {run_day} · "
            f"File: {analysis.source_file} · Meeting date: {meeting}")


# --- page parts ---------------------------------------------------------------

def sidebar() -> None:
    with st.sidebar:
        st.header("How it works")
        st.markdown(
            "1. Claude reads the notes and finds the RAID items, the owners and the date words.\n"
            "2. The code turns date words into dates and checks owners, dates and quotes.\n"
            "3. You check **Needs attention**, tick **Reviewed**, and download the Markdown file."
        )
        st.header("Rules")
        st.markdown(
            "- An owner is only **Confirmed** after a clear yes or an \"I will\".\n"
            "- \"I can try\" is **tentative**; no answer is **not confirmed**.\n"
            "- No owner or date in the notes: **Not stated**. The tool never guesses.\n"
            "- A proposal is not a decision."
        )
        st.markdown(f"[How to export a Teams or Zoom transcript]({EXPORT_GUIDE_URL})")
        st.markdown(f"[Code, eval, and decisions on GitHub]({REPO_URL})")


def show_results(analysis: Analysis, *, cost_line: str, file_stem: str, key: str) -> None:
    log = analysis.log
    with st.container(border=True):
        st.subheader(f"2. RAID log · {len(log.items)} items")
        st.caption(plain(run_details(analysis)))

        st.markdown("**Needs attention**")
        if analysis.attention:
            st.warning("\n".join(
                f"- {a.short_id + ': ' if a.short_id else ''}{plain(a.text)}" for a in analysis.attention))
        else:
            st.success("Nothing to check.")

        if not log.items:
            st.write("No items found.")
            return

        reviewed_key = f"reviewed_{key}"
        reviewed: set[str] = st.session_state.setdefault(reviewed_key, set())
        rows = pd.DataFrame(table_rows(analysis, reviewed)).set_index("ID")
        edited = st.data_editor(
            rows, column_order=COLUMNS, disabled=COLUMNS[:-1], hide_index=True, width="stretch",
            key=f"table_{key}",
            column_config={
                "Type": st.column_config.TextColumn("Type", width="small"),
                "Item": st.column_config.TextColumn("Item", width="large"),
                "Owner": st.column_config.TextColumn("Owner", width="medium"),
                "Due date": st.column_config.TextColumn("Due date", width="medium"),
                "Reviewed": st.column_config.CheckboxColumn("Reviewed", default=False, width="small"),
            },
        )
        reviewed.clear()
        reviewed.update(edited.index[edited["Reviewed"]].tolist())  # ticks last for this page session (R8.5)
        st.caption("✓ = the code found the quote word for word in the notes. Owner in brackets = not confirmed yet.")

        by_id = {item.short_id: item for item in log.items}
        choice = st.selectbox("Show the quote for an item", list(by_id), index=None,
                              placeholder="Choose an item, for example ACT-1", key=f"quote_{key}")
        if choice:
            item = by_id[choice]
            found = "✓ found word for word in the notes" if item.quote_verified else "quote not found in the notes"
            st.info(f"**{choice}** ({found}): \"{plain(item.source_quote)}\"" +
                    (f"\n\nReply: \"{plain(item.reply_quote)}\"" if item.reply_quote else ""))

        left, right = st.columns([3, 1], vertical_alignment="center")
        left.caption(plain(cost_line))
        right.download_button(
            "Download Markdown",
            data=to_markdown(analysis, reviewed),
            file_name=f"{file_stem}_raid_log.md",
            mime="text/markdown",
            type="primary",
            width="stretch",
            key=f"download_{key}",
            help="Run details, Needs attention, the table with your Reviewed ticks, and the quotes.",
        )


def demo_mode() -> None:
    options = demo_options()
    with st.container(border=True):
        st.subheader("1. Choose a sample call")
        st.caption("Saved results. No API key, no API call, no cost.")
        label = st.selectbox("Sample call", list(options), label_visibility="collapsed")
        data = load_demo(options[label])
        st.write(f"**What this sample tests:** {data['tests']}")
        notes_path = SAMPLES_DIR / data["sample"]
        if notes_path.exists():
            with st.expander("Show the call notes"):
                st.text(read_notes(notes_path))

    analysis = data["analysis"]
    cost_line = format_run(analysis.model, analysis.input_tokens, analysis.output_tokens, analysis.seconds)
    # One key per sample, so Reviewed ticks never carry over to another sample.
    show_results(analysis, cost_line=cost_line, file_stem=Path(data["sample"]).stem, key=f"demo_{options[label]}")


def own_notes_mode() -> None:
    env_key = os.getenv("ANTHROPIC_API_KEY")
    with st.container(border=True):
        st.subheader("1. Upload your notes")
        st.warning(PRIVACY_WARNING)
        st.markdown(f"[How to export a Teams or Zoom transcript]({EXPORT_GUIDE_URL})")
        with st.expander("Why a key?"):
            st.markdown(
                "This mode sends your notes to Claude through the Anthropic API, and the API needs a key for "
                "each request. Anthropic bills your account: about \\$0.01 for a short call and about \\$0.05 "
                "for a 1-hour transcript. This site has no key of its own and stores neither the notes nor the key."
            )
        if env_key:
            key = env_key
            st.caption("Using the API key from your .env file.")
        else:
            key = st.text_input(
                "Anthropic API key", type="password", placeholder="sk-ant-...",
                help="Get a key at console.anthropic.com.",
            )
        meeting_date = st.date_input(
            "Meeting date", value=None, format="YYYY-MM-DD",
            help="Needed to turn \"by Friday\" or \"2 November\" into a date.",
        )
        upload = st.file_uploader(
            "Call notes or transcript", type=["txt", "docx", "vtt"],
            help="Plain text notes, Word minutes, or a Teams or Zoom transcript.",
        )

        text = None
        if upload is not None:
            if upload.size > MAX_UPLOAD_MB * 1024 * 1024:
                st.error(f"The file is larger than {MAX_UPLOAD_MB} MB.")
            else:
                try:
                    text = notes_from_upload(upload.name, upload.getvalue())
                except (UnsupportedFileError, EmptyNotesError) as error:
                    st.error(str(error))

        if text is not None:
            st.caption(f"{upload.name}: {len(text.split()):,} words")
            for warning in input_warnings(text):  # spec R6.2: before the log
                st.warning(warning)
        run = st.button("Extract the RAID log", type="primary", disabled=not (key and text))
        if text is not None and not key:
            st.caption("Enter an API key to continue.")

    # Keep the result for this file and meeting date, so a tick or a download (a page rerun)
    # does not clear it or run the API call again.
    upload_id = f"{upload.name}:{upload.size}:{meeting_date}" if upload is not None else None
    saved = st.session_state.get("own_result")
    if saved and saved["upload_id"] != upload_id:
        st.session_state.pop("own_result")
        st.session_state.pop("reviewed_own", None)
        saved = None

    if run:
        saved = extract(text, key, upload.name, upload_id, meeting_date)
    if saved:
        analysis = saved["result"]
        cost_line = format_run(analysis.model, analysis.input_tokens, analysis.output_tokens, analysis.seconds)
        show_results(analysis, cost_line=cost_line, file_stem=Path(upload.name).stem, key="own")


def extract(text: str, key: str, name: str, upload_id: str, meeting_date: date | None) -> dict | None:
    import anthropic

    from raid.extract import ExtractionError, NotesTooLongError
    from raid.pipeline import analyse

    with st.spinner("Claude reads the notes..."):
        try:
            result = analyse(text, meeting_date, client=anthropic.Anthropic(api_key=key), source_file=name)
        except anthropic.AuthenticationError:
            st.error("The API key is not valid.")
            return None
        except NotesTooLongError as error:  # spec R6.1: an error and no log
            st.error(str(error))
            return None
        except (anthropic.APIError, ExtractionError) as error:
            st.error(f"The extraction failed: {error}")
            return None
    saved = {"upload_id": upload_id, "result": result}
    st.session_state["own_result"] = saved
    st.session_state["reviewed_own"] = set()
    return saved


# --- page -------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="RAID Log Extractor", page_icon="📋", layout="wide")
    sidebar()
    st.title("RAID Log Extractor")
    st.write(
        "Turn call notes or a transcript into a RAID log: risks, assumptions, issues, dependencies, "
        "actions, and decisions. Each item has a quote that the code checks, an owner state, and a "
        "**Needs attention** list of what to check before you share the log."
    )
    mode = st.radio("Mode", [DEMO, OWN], horizontal=True, label_visibility="collapsed")
    if mode == DEMO:
        demo_mode()
    else:
        own_notes_mode()


if __name__ == "__main__":  # Streamlit runs the page as __main__; tests can import it
    main()
