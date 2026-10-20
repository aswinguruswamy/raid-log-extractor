"""Read .txt, .docx, and .vtt files into plain text (story S1-02, KAN-7)."""

from __future__ import annotations

import re
from pathlib import Path

SUPPORTED_TYPES = (".txt", ".docx", ".vtt")


class UnsupportedFileError(ValueError):
    """The file type is not one the tool can read."""


class EmptyNotesError(ValueError):
    """The file has no text in it."""


def read_notes(path: str | Path) -> str:
    """Return the text of a notes file as plain text.

    .txt  -> the text as it is
    .docx -> paragraphs and table cells, one per line
    .vtt  -> 'Speaker: words' lines, with time stamps and cue numbers removed
    """
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_TYPES:
        raise UnsupportedFileError(
            f"Cannot read '{path.name}'. Supported file types: {', '.join(SUPPORTED_TYPES)}."
        )
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    if suffix == ".txt":
        text = _read_text_file(path)
    elif suffix == ".docx":
        text = _read_docx(path)
    else:
        text = _vtt_to_text(_read_text_file(path))

    text = _tidy(text)
    if not text:
        raise EmptyNotesError(f"'{path.name}' has no text in it.")
    return text


# --- .txt -----------------------------------------------------------------

def _read_text_file(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


# --- .docx ----------------------------------------------------------------

def _read_docx(path: Path) -> str:
    from docx import Document  # imported here so .txt/.vtt work without python-docx

    document = Document(str(path))
    lines = [paragraph.text for paragraph in document.paragraphs]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            # Merged cells repeat their text; keep each value once per row.
            unique = list(dict.fromkeys(cell for cell in cells if cell))
            if unique:
                lines.append(" | ".join(unique))
    return "\n".join(lines)


# --- .vtt (Teams, Zoom, Google Meet transcripts) ------------------------

_TIMESTAMP = re.compile(r"^\s*(\d{1,2}:)?\d{2}:\d{2}[.,]\d{3}\s*-->\s*(\d{1,2}:)?\d{2}:\d{2}[.,]\d{3}")
_VOICE_TAG = re.compile(r"<v(?:\.[^\s>]+)*\s+([^>]+)>(.*?)(?:</v>|$)", re.DOTALL)
_ANY_TAG = re.compile(r"</?[^>]+>")


def _vtt_to_text(content: str) -> str:
    blocks = re.split(r"\n\s*\n", content.replace("\r\n", "\n").replace("\r", "\n"))
    turns: list[tuple[str, str]] = []  # (speaker, words)

    for block in blocks:
        lines = [line for line in block.split("\n") if line.strip()]
        if not lines:
            continue
        first = lines[0].strip()
        if first.startswith("WEBVTT") or first.startswith(("NOTE", "STYLE", "REGION")):
            continue
        # Drop everything up to and including the time stamp line (cue numbers or ids).
        stamp_index = next((i for i, line in enumerate(lines) if _TIMESTAMP.match(line)), None)
        if stamp_index is None:
            continue
        cue_text = " ".join(line.strip() for line in lines[stamp_index + 1 :])
        speaker, words = _split_speaker(cue_text)
        if not words:
            continue
        if turns and turns[-1][0] == speaker:
            turns[-1] = (speaker, f"{turns[-1][1]} {words}")
        else:
            turns.append((speaker, words))

    return "\n".join(f"{speaker}: {words}" if speaker else words for speaker, words in turns)


def _split_speaker(cue_text: str) -> tuple[str, str]:
    """Teams writes '<v Name>words</v>'. Zoom writes 'Name: words'."""
    voice = _VOICE_TAG.search(cue_text)
    if voice:
        speaker = voice.group(1).strip()
        words = _ANY_TAG.sub("", voice.group(2)).strip()
        return speaker, words
    words = _ANY_TAG.sub("", cue_text).strip()
    zoom = re.match(r"^([A-Z][\w.'\- ]{0,40}?):\s+(.*)$", words)
    if zoom:
        return zoom.group(1).strip(), zoom.group(2).strip()
    return "", words


# --- shared -----------------------------------------------------------------

def _tidy(text: str) -> str:
    lines = [line.rstrip() for line in text.replace("\r\n", "\n").split("\n")]
    tidy: list[str] = []
    for line in lines:
        if line or (tidy and tidy[-1]):  # keep single blank lines, drop runs of them
            tidy.append(line)
    return "\n".join(tidy).strip()
