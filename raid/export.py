"""Write the checked RAID log as Markdown (RAID v2 spec R9.1, R10.1; task A9).

The file has: run details, Needs attention, the table (Reviewed as "✓ reviewed" or
"not reviewed") and an Evidence list (ID, quote, reply quote). v2 writes no Excel file (R8.6).
"""

from __future__ import annotations

from .view import COLUMNS, sorted_items, table_rows


def _text(text: str) -> str:
    """One line of plain text: no line breaks, and *, _, ` shown as written."""
    text = " ".join(str(text).split())
    for char in ("\\", "*", "_", "`"):
        text = text.replace(char, "\\" + char)
    return text


def _cell(text: str) -> str:
    return _text(text).replace("|", "\\|")


def to_markdown(analysis, reviewed: set[str]) -> str:
    log, attention = analysis.log, analysis.attention
    meeting = analysis.meeting_date.isoformat() if analysis.meeting_date else "Not entered"
    lines = [
        f"# RAID log – {_cell(analysis.source_file or log.source_file)}",
        "",
        "## Run details",
        "",
        "| Model | Prompt version | Run date | Meeting date | Source file |",
        "|---|---|---|---|---|",
        f"| {analysis.model} | {analysis.prompt_version} | "
        f"{analysis.run_date.isoformat() if analysis.run_date else '-'} | {meeting} | "
        f"{_cell(analysis.source_file or log.source_file)} |",
        "",
        "## Needs attention",
        "",
    ]
    lines += [f"- {a.short_id + ': ' if a.short_id else ''}{_text(a.text)}" for a in attention] or ["Nothing to check."]
    lines += ["", f"## RAID log ({len(log.items)} items)", ""]
    if log.items:
        lines += ["| " + " | ".join(COLUMNS) + " |", "|" + "---|" * len(COLUMNS)]
        for row in table_rows(analysis, reviewed):
            done = "✓ reviewed" if row["Reviewed"] else "not reviewed"
            lines.append(f"| {row['Type']} | {_cell(row['Item'])} | {_cell(row['Owner'])} | "
                         f"{_cell(row['Due date'])} | {done} |")
    else:
        lines.append("No items found.")
    lines += ["", "## Evidence", ""]
    for item in sorted_items(log, attention):
        found = "found" if item.quote_verified else "not found"
        line = f"- **{item.short_id}** ({found}): \"{_text(item.source_quote)}\""
        if item.reply_quote:
            line += f" — reply: \"{_text(item.reply_quote)}\""
        lines.append(line)
    return "\n".join(lines) + "\n"
