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


# --- Input warnings and the speaker list (RAID v2 spec R6.2, task A6) ---------------

MAX_WORDS = 15_000
MIN_COMMON_SHARE = 0.02
TOO_LONG = "The notes have more than 15,000 words. Items may be missed; split the notes and run each part."
NO_SPEAKERS = "No speaker names found (\"Name:\" lines or voice tags). Check every owner."
NOT_ENGLISH = "The notes do not look like English. The tool is tested on English only; check every item."

_SPEAKER = re.compile(r"^\s*([A-Z][A-Za-z'.-]*(?:\s+[A-Z][A-Za-z'.-]*){0,3})\s*:\s*\S", re.MULTILINE)
_ATTENDEES = re.compile(r"^\s*(?:present|attendees|participants|attending|in attendance)\s*:\s*(.+)$",
                        re.IGNORECASE | re.MULTILINE)
_HEADINGS = {
    "present", "attendees", "apologies", "absent", "action", "actions", "decision", "decisions", "note",
    "notes", "date", "agenda", "minutes", "subject", "re", "time", "location", "chair", "risk", "risks",
    "issue", "issues", "next steps", "summary", "owner", "due", "status", "webvtt", "note to self",
    "participants", "attending", "in attendance", "agreed", "update", "updates", "blocker", "blockers",
    "next", "todo", "to do", "follow up", "follow-up", "question", "questions", "answer", "comment",
    "comments", "background", "context", "goal", "goals", "result", "results", "outcome", "outcomes",
    "deadline", "priority", "topic", "item", "items", "discussion", "conclusion", "recap", "reminder",
    "warning", "fyi", "overall status", "assumption", "assumptions", "dependency", "dependencies",
    "open questions", "action items", "key decisions", "purpose", "scope", "objective", "objectives",
}
_COMMON = {
    "the", "and", "to", "is", "of", "in", "we", "it", "you", "that", "for", "on", "will", "be", "this",
    "with", "can", "are", "have", "not", "by", "it's", "i'll", "we'll", "was", "do", "so", "at", "our",
}
_TOKEN = re.compile(r"[a-z']+")


def speakers(text: str) -> list[str]:
    """The people on the call: names before a turn ("Aiko Sato: …") and names in a
    "Present:" or "Attendees:" line, in order of first appearance. Headings are skipped."""
    found: list[tuple[int, str]] = []
    for match in _ATTENDEES.finditer(text):
        people = re.sub(r"\([^)]*\)", "", match.group(1))
        for name in re.split(r",|;|\band\b", people):
            name = name.strip(" .")
            if name:
                found.append((match.start(), name))
    for match in _SPEAKER.finditer(text):
        name = match.group(1).strip()
        if name.lower() not in _HEADINGS:
            found.append((match.start(), name))
    names: list[str] = []
    for _, name in sorted(found, key=lambda pair: pair[0]):
        if name not in names:
            names.append(name)
    return names


def input_warnings(text: str) -> list[str]:
    """Warnings to show before the log: too long, no speaker names, not English."""
    warnings = []
    if len(text.split()) > MAX_WORDS:
        warnings.append(TOO_LONG)
    if not speakers(text):
        warnings.append(NO_SPEAKERS)
    tokens = _TOKEN.findall(text.lower().replace("’", "'"))
    if tokens and sum(token in _COMMON for token in tokens) / len(tokens) < MIN_COMMON_SHARE:
        warnings.append(NOT_ENGLISH)
    return warnings
