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
MAX_UPLOAD_MB = 2

load_dotenv()


# --- data -------------------------------------------------------------------

def load_demo(stem: str) -> dict:
    """A saved run: the RAID log plus model, tokens, and time."""
    data = json.loads((DEMO_DIR / f"{stem}.json").read_text(encoding="utf-8"))
    items = [RaidItem(**{k: v for k, v in item.items()}) for item in data["items"]]
    data["log"] = RaidLog(source_file=data["sample"], items=items)
    return data


def demo_options() -> dict[str, str]:
    """Label -> file stem, for the demo select box."""
    options = {}
    for path in sorted(DEMO_DIR.glob("*.json")):
        options[json.loads(path.read_text(encoding="utf-8"))["label"]] = path.stem
    return options


def items_table(items: list[RaidItem]) -> pd.DataFrame:
    table = pd.DataFrame(
        [
            {
                "Description": item.description,
                "Owner": item.owner,
                "Due date": item.due_date,
                "Status": item.status.value,
                "Source quote": item.source_quote,
                "Quote checked": {True: "Yes", False: "Not found", None: "-"}[item.quote_verified],
            }
            for item in items
        ]
    )
    table.index = pd.RangeIndex(1, len(table) + 1, name="#")
    return table


# --- page parts ---------------------------------------------------------------

def show_results(log: RaidLog, *, run_line: str, warnings: list[str], file_stem: str) -> None:
    groups = log.by_type()
    st.subheader(f"Results: {len(log.items)} items")
    columns = st.columns(len(groups))
    for column, (item_type, items) in zip(columns, groups.items()):
        column.metric(SHEET_NAMES[item_type], len(items))

    tabs = st.tabs([f"{SHEET_NAMES[t]} ({len(i)})" for t, i in groups.items()])
    for tab, (item_type, items) in zip(tabs, groups.items()):
        with tab:
            if items:
                st.table(items_table(items))  # st.table wraps long quotes; st.dataframe cuts them off
            else:
                st.caption(f"The notes have no {SHEET_NAMES[item_type].lower()}.")

    st.caption(run_line)
    for warning in warnings:
        st.warning(warning)

    st.download_button(
        "Download the RAID log (Excel)",
        data=to_excel_bytes(log),
        file_name=f"{file_stem}_raid_log.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )


def demo_mode() -> None:
    st.info("Demo mode shows saved results from the eval run. It makes no API call and needs no API key.")
    options = demo_options()
    label = st.selectbox("Choose a sample call", list(options))
    data = load_demo(options[label])

    notes_path = SAMPLES_DIR / data["sample"]
    if notes_path.exists():
        with st.expander("Show the call notes"):
            st.text(read_notes(notes_path))

    run_line = format_run(data["model"], data["input_tokens"], data["output_tokens"], data["seconds"])
    show_results(data["log"], run_line=run_line, warnings=data.get("warnings", []), file_stem=Path(data["sample"]).stem)


def own_notes_mode() -> None:
    st.markdown(
        "**Privacy:** the page sends your notes to the Anthropic API and does not store them. "
        "Do not upload confidential client data. Your API key stays in this browser session only."
    )
    key = os.getenv("ANTHROPIC_API_KEY") or st.text_input(
        "Anthropic API key", type="password", help="Get a key at console.anthropic.com. The page does not save it."
    )
    upload = st.file_uploader("Upload call notes or a transcript", type=["txt", "docx", "vtt"])
    if upload is None:
        return
    if upload.size > MAX_UPLOAD_MB * 1024 * 1024:
        st.error(f"The file is larger than {MAX_UPLOAD_MB} MB.")
        return

    try:
        text = notes_from_upload(upload.name, upload.getvalue())
    except (UnsupportedFileError, EmptyNotesError) as error:
        st.error(str(error))
        return
    st.caption(f"{upload.name}: {len(text.split()):,} words")

    if not st.button("Extract the RAID log", type="primary", disabled=not key):
        if not key:
            st.caption("Enter an API key to continue.")
        return

    import anthropic

    from raid.extract import ExtractionError, extract_items

    with st.spinner("Claude reads the notes..."):
        try:
            result = extract_items(text, client=anthropic.Anthropic(api_key=key), source_file=upload.name)
        except anthropic.AuthenticationError:
            st.error("The API key is not valid.")
            return
        except (anthropic.APIError, ExtractionError) as error:
            st.error(f"The extraction failed: {error}")
            return

    run_line = format_run(result.model, result.input_tokens, result.output_tokens, result.seconds)
    show_results(result.log, run_line=run_line, warnings=result.warnings, file_stem=Path(upload.name).stem)


def notes_from_upload(name: str, content: bytes) -> str:
    """Write the upload to a temporary file with the same suffix, then read it."""
    suffix = Path(name).suffix.lower()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / f"upload{suffix}"
        path.write_bytes(content)
        return read_notes(path)


# --- page -------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="RAID Log Extractor", layout="wide")
    st.title("RAID Log Extractor")
    st.write(
        "Turn meeting notes or a call transcript into a RAID log: risks, assumptions, issues, "
        "dependencies, actions, and decisions. Each item has a source quote from the notes, "
        "and the tool writes \"Not stated\" when the notes give no owner or date."
    )
    mode = st.radio("Mode", ["Demo (no API key)", "Your own notes"], horizontal=True)
    if mode.startswith("Demo"):
        demo_mode()
    else:
        own_notes_mode()


if __name__ == "__main__":  # Streamlit runs the page as __main__; tests can import it
    main()
