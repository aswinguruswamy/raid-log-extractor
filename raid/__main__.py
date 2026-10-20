"""Command-line tool (story S1-08, KAN-13).

    python -m raid extract notes.txt
    python -m raid extract call.vtt --out reports/ --model claude-opus-5-5
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .cost import format_run
from .extract import DEFAULT_MODEL, ExtractionError, extract_items
from .export import SHEET_NAMES, to_excel
from .parse import EmptyNotesError, UnsupportedFileError, read_notes


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m raid", description="Turn call notes into a RAID log.")
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="Extract a RAID log from one notes file.")
    extract.add_argument("notes", help="A .txt, .docx, or .vtt file.")
    extract.add_argument("--out", default="output", help="Output folder (default: output).")
    extract.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model (default: {DEFAULT_MODEL}).")
    return parser


def main(argv: list[str] | None = None, *, client=None) -> int:
    args = build_parser().parse_args(argv)
    _load_dotenv()

    try:
        text = read_notes(args.notes)
    except (UnsupportedFileError, EmptyNotesError, FileNotFoundError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2

    if client is None and not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY is not set. Put it in the .env file (see .env.example).", file=sys.stderr)
        return 2

    notes_path = Path(args.notes)
    print(f"Reading {notes_path.name} ({len(text.split()):,} words)...")
    try:
        result = extract_items(text, client=client, model=args.model, source_file=notes_path.name)
    except ExtractionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # API errors: bad key, no credit, network
        print(f"Error from the Claude API: {error}", file=sys.stderr)
        return 1

    out_path = to_excel(result.log, Path(args.out) / f"{notes_path.stem}_raid_log.xlsx")

    print()
    for item_type, items in result.log.by_type().items():
        print(f"  {SHEET_NAMES[item_type]:<13} {len(items)}")
    print(f"  {'Total':<13} {len(result.log.items)}")
    for warning in result.warnings:
        print(f"Warning: {warning}")
    print()
    print(format_run(result.model, result.input_tokens, result.output_tokens, result.seconds))
    print(f"Saved: {out_path}")
    return 0


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


if __name__ == "__main__":
    sys.exit(main())
