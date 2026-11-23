"""Command-line tool (story S1-08, KAN-13).

    python -m raid extract notes.txt --meeting-date 2026-12-01
    python -m raid extract call.vtt --out reports/ --model claude-opus-5-5

Writes <notes>_raid_log.md (RAID v2 spec R9.1; v2 writes no Excel file, R8.6).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

from .cost import format_run
from .export import to_markdown
from .extract import DEFAULT_MODEL, ExtractionError
from .parse import EmptyNotesError, UnsupportedFileError, read_notes
from .pipeline import analyse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m raid", description="Turn call notes into a RAID log.")
    commands = parser.add_subparsers(dest="command", required=True)
    extract = commands.add_parser("extract", help="Extract a RAID log from one notes file.")
    extract.add_argument("notes", help="A .txt, .docx, or .vtt file.")
    extract.add_argument("--out", default="output", help="Output folder (default: output).")
    extract.add_argument("--model", default=DEFAULT_MODEL, help=f"Claude model (default: {DEFAULT_MODEL}).")
    extract.add_argument("--meeting-date", type=date.fromisoformat, default=None,
                         help="YYYY-MM-DD; needed to convert 'by Friday' and similar.")
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
        result = analyse(text, args.meeting_date, client=client, model=args.model, source_file=notes_path.name)
    except ExtractionError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    except Exception as error:  # API errors: bad key, no credit, network
        print(f"Error from the Claude API: {error}", file=sys.stderr)
        return 1

    out_path = Path(args.out) / f"{notes_path.stem}_raid_log.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(to_markdown(result, reviewed=set()), encoding="utf-8")

    print()
    for item_type, items in result.log.by_type().items():
        print(f"  {item_type.value:<13} {len(items)}")
    print(f"  {'Total':<13} {len(result.log.items)}")
    for line in result.attention:
        print(f"Needs attention: {line.short_id + ': ' if line.short_id else ''}{line.text}")
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
