"""RAID Log Extractor web page (stories S3-01 KAN-21 and S3-02 KAN-22).

Run it with:  streamlit run app.py

Two modes:
  * Demo: saved results for 3 sample calls. No API key and no API call.
  * Your own notes: upload a .txt, .docx, or .vtt file and use your own Anthropic API key.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from raid.cost import format_run
from raid.export import SHEET_NAMES, to_excel_bytes
from raid.parse import EmptyNotesError, UnsupportedFileError, read_notes
from raid.schema import ItemType, RaidItem, RaidLog

ROOT = Path(__file__).parent
DEMO_DIR = ROOT / "demo"
SAMPLES_DIR = ROOT / "samples"
REPO_URL = "https://github.com/aswinguruswamy/raid-log-extractor"
MAX_UPLOAD_MB = 2  # keep in step with server.maxUploadSize in .streamlit/config.toml

DEMO = "Demo (no API key)"
OWN = "Your own notes"

TYPE_MEANING = {
    ItemType.RISK: "Something that may happen and hurt the project",
    ItemType.ASSUMPTION: "Something the team treats as true without proof",
    ItemType.ISSUE: "A problem that is happening now",
    ItemType.DEPENDENCY: "Work that needs another team, vendor, or task first",
    ItemType.ACTION: "A task that a person agreed to do",
    ItemType.DECISION: "A choice the team made in the call",
}

load_dotenv()


# --- data -------------------------------------------------------------------

def load_demo(stem: str) -> dict:
    """A saved run: the RAID log plus model, tokens, and time."""
    data = json.loads((DEMO_DIR / f"{stem}.json").read_text(encoding="utf-8"))
    items = [RaidItem(**item) for item in data["items"]]
    data["log"] = RaidLog(source_file=data["sample"], items=items)
    return data


def demo_options() -> dict[str, str]:
    """Select-box label -> file stem."""
    options = {}
    for path in sorted(DEMO_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        options[f"{data['label']} · {data['format']}"] = path.stem
    return options


def items_table(items: list[RaidItem]) -> pd.DataFrame:
    """The page table. Status is left out (every new item is Open); the Excel file has it."""
    table = pd.DataFrame(
        [
            {
                "Description": item.description,
                "Owner": item.owner,
                "Due date": item.due_date,
                "Source quote": item.source_quote,
                "Quote found": {True: "Yes", False: "Not found", None: "-"}[item.quote_verified],
            }
            for item in items
        ]
    )
    table.index = pd.RangeIndex(1, len(table) + 1, name="#")
    return table


def notes_from_upload(name: str, content: bytes) -> str:
    """Write the upload to a temporary file with the same suffix, then read it."""
    suffix = Path(name).suffix.lower()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / f"upload{suffix}"
        path.write_bytes(content)
        return read_notes(path)


# --- page parts ---------------------------------------------------------------

def sidebar() -> None:
    with st.sidebar:
        st.header("How it works")
        st.markdown(
            "1. Claude reads the notes and finds the RAID items.\n"
            "2. The code checks each source quote word for word against the notes.\n"
            "3. You check the items and download the Excel file."
        )
        st.header("Rules")
        st.markdown(
            "- No owner or date in the notes: **Not stated**. The tool never guesses.\n"
            "- A relative date (\"by Friday\") stays in the description.\n"
            "- Every item has a source quote."
        )
        st.header("Eval")
        st.markdown(
            "10 test calls, 68 expected items: **100% recall and precision** (run 2). "
            "The prompt was tuned on these calls, so new notes may score lower."
        )
        st.markdown(f"[Code, eval, and decisions on GitHub]({REPO_URL})")


def show_results(log: RaidLog, *, run_line: str, warnings: list[str], file_stem: str, key: str) -> None:
    groups = log.by_type()
    with st.container(border=True):
        st.subheader(f"2. RAID log · {len(log.items)} items")
        tabs = st.tabs([f"{SHEET_NAMES[t]} ({len(i)})" for t, i in groups.items()])
        for tab, (item_type, items) in zip(tabs, groups.items()):
            with tab:
                st.caption(TYPE_MEANING[item_type] + ".")
                if items:
                    st.table(items_table(items))
                else:
                    st.write(f"The notes have no {SHEET_NAMES[item_type].lower()}.")

        if warnings:
            with st.expander(f"{len(warnings)} warning(s) to check"):
                for warning in warnings:
                    st.warning(warning)

        left, right = st.columns([3, 1], vertical_alignment="center")
        left.caption(run_line)
        right.download_button(
            "Download Excel",
            data=to_excel_bytes(log),
            file_name=f"{file_stem}_raid_log.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            width="stretch",
            key=f"download_{key}",
            help="One sheet per item type, plus a Status column (Open, In progress, Closed) for you to update.",
        )


def demo_mode() -> None:
    options = demo_options()
    with st.container(border=True):
        st.subheader("1. Choose a sample call")
        st.caption("Saved results from the eval run. No API key, no API call, no cost.")
        label = st.selectbox("Sample call", list(options), label_visibility="collapsed")
        data = load_demo(options[label])
        st.write(f"**What this sample tests:** {data['tests']}")
        notes_path = SAMPLES_DIR / data["sample"]
        if notes_path.exists():
            with st.expander("Show the call notes"):
                st.text(read_notes(notes_path))

    run_line = format_run(data["model"], data["input_tokens"], data["output_tokens"], data["seconds"])
    show_results(
        data["log"], run_line=run_line, warnings=data.get("warnings", []),
        file_stem=Path(data["sample"]).stem, key="demo",
    )


def own_notes_mode() -> None:
    env_key = os.getenv("ANTHROPIC_API_KEY")
    with st.container(border=True):
        st.subheader("1. Upload your notes")
        with st.expander("Why a key? · Privacy"):
            st.markdown(
                "**Why a key?** This mode sends your notes to Claude through the Anthropic API, and the API "
                "needs a key for each request. Anthropic bills your account: about $0.01 for a short call and "
                "about $0.05 for a 1-hour transcript. This site has no key of its own.\n\n"
                "**Privacy:** the page sends your notes to the Anthropic API and does not store them or the key. "
                "Do not upload confidential client data."
            )
        if env_key:
            key = env_key
            st.caption("Using the API key from your .env file.")
        else:
            key = st.text_input(
                "Anthropic API key", type="password", placeholder="sk-ant-...",
                help="Get a key at console.anthropic.com.",
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
        run = st.button("Extract the RAID log", type="primary", disabled=not (key and text))
        if text is not None and not key:
            st.caption("Enter an API key to continue.")

    # Keep the result for this file, so the download click (a page rerun) does not clear it
    # or run the API call again.
    upload_id = f"{upload.name}:{upload.size}" if upload is not None else None
    saved = st.session_state.get("own_result")
    if saved and saved["upload_id"] != upload_id:
        st.session_state.pop("own_result")
        saved = None

    if run:
        saved = extract(text, key, upload.name, upload_id)
    if saved:
        result = saved["result"]
        run_line = format_run(result.model, result.input_tokens, result.output_tokens, result.seconds)
        show_results(
            result.log, run_line=run_line, warnings=result.warnings,
            file_stem=Path(upload.name).stem, key="own",
        )


def extract(text: str, key: str, name: str, upload_id: str) -> dict | None:
    import anthropic

    from raid.extract import ExtractionError, extract_items

    with st.spinner("Claude reads the notes..."):
        try:
            result = extract_items(text, client=anthropic.Anthropic(api_key=key), source_file=name)
        except anthropic.AuthenticationError:
            st.error("The API key is not valid.")
            return None
        except (anthropic.APIError, ExtractionError) as error:
            st.error(f"The extraction failed: {error}")
            return None
    saved = {"upload_id": upload_id, "result": result}
    st.session_state["own_result"] = saved
    return saved


# --- page -------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="RAID Log Extractor", page_icon="📋", layout="wide")
    sidebar()
    st.title("RAID Log Extractor")
    st.write(
        "Turn call notes or a transcript into a RAID log: risks, assumptions, issues, dependencies, "
        "actions, and decisions. Each item has a source quote, and a missing owner or date shows as **Not stated**."
    )
    mode = st.radio("Mode", [DEMO, OWN], horizontal=True, label_visibility="collapsed")
    if mode == DEMO:
        demo_mode()
    else:
        own_notes_mode()


if __name__ == "__main__":  # Streamlit runs the page as __main__; tests can import it
    main()
