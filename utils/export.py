"""
utils/export.py

Turns parsed study material (the dict produced by Backend.parser) into
downloadable files:

- to_txt(): plain UTF-8 .txt bytes -- supports full Unicode (emojis, etc.)
- to_pdf(): a formatted .pdf using fpdf2 -- a lightweight, pure-Python PDF
  library with no system dependencies

Both functions return raw `bytes`, ready to be passed straight to
st.download_button(data=...).
"""

import re
from fpdf import FPDF
from fpdf.enums import XPos, YPos


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# fpdf2's built-in core fonts (Helvetica, etc.) only support Latin-1.
# These replacements swap common "smart" Unicode characters for plain ASCII
# equivalents before we drop anything else that can't be encoded (e.g. the
# emojis used throughout the UI).
_UNICODE_REPLACEMENTS = {
    "\u2018": "'", "\u2019": "'",      # smart single quotes
    "\u201c": '"', "\u201d": '"',      # smart double quotes
    "\u2013": "-", "\u2014": "-",      # en/em dash
    "\u2026": "...",                    # ellipsis
    "\u2022": "-",                      # bullet
    "\u2192": "->",                     # right arrow
    "\u00d7": "x",                      # multiplication sign
    "\u00f7": "/",                      # division sign
}

_BOLD_PATTERN = re.compile(r"\*\*(.*?)\*\*")
_ITALIC_PATTERN = re.compile(r"(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)")


def _strip_markdown(text: str) -> str:
    """Remove **bold** / *italic* markers, keeping the inner text."""
    text = _BOLD_PATTERN.sub(r"\1", text)
    text = _ITALIC_PATTERN.sub(r"\1", text)
    return text


def _pdf_safe(text: str) -> str:
    """
    Make text safe for fpdf2's core fonts: strip markdown emphasis, swap
    common "smart" Unicode characters for ASCII equivalents, then drop any
    remaining characters (e.g. emoji) that Latin-1 can't represent.
    """
    text = _strip_markdown(text or "")
    for src, dst in _UNICODE_REPLACEMENTS.items():
        text = text.replace(src, dst)
    return text.encode("latin-1", "ignore").decode("latin-1")


def _section_or_placeholder(text: str) -> str:
    text = (text or "").strip()
    return text if text else "(No content generated for this section.)"


def _quiz_item_lines(item: dict) -> list:
    """
    Return a list of plain-text lines representing one quiz item
    (question + options if MCQ + answer), for use in TXT/PDF export.
    Does not include the leading "Q{i}." -- callers prepend that.
    """
    lines = [item.get("question", "")]

    if item.get("type") == "mcq":
        options = item.get("options") or {}
        for letter in ("A", "B", "C", "D"):
            if letter in options:
                lines.append(f"  {letter}) {options[letter]}")
        correct_letter = item.get("answer", "")
        correct_text = options.get(correct_letter, "")
        if correct_text:
            lines.append(f"Answer: {correct_letter}) {correct_text}")
        else:
            lines.append(f"Answer: {correct_letter}")
    else:
        lines.append(f"Answer: {item.get('answer', '')}")

    return lines


def _line(pdf: FPDF, height: float, text: str) -> None:
    """
    multi_cell() wrapper that always resets the cursor back to the left
    margin on the next line afterwards. Without this, fpdf2 leaves the
    cursor at the right margin after a full-width multi_cell, causing the
    *next* multi_cell call to fail with "Not enough horizontal space".
    """
    pdf.multi_cell(0, height, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)


# ---------------------------------------------------------------------------
# TXT export
# ---------------------------------------------------------------------------

def to_txt(parsed: dict, topic: str, difficulty: str = "", study_mode: str = "") -> bytes:
    """
    Build a plain-text export of the study material.

    `parsed` is the dict returned by Backend.parser.parse_study_material().
    Full Unicode (emojis, etc.) is preserved since .txt files are UTF-8.
    """
    lines = []
    lines.append(f"AI STUDY ASSISTANT — {topic}")
    if difficulty or study_mode:
        meta = " | ".join(filter(None, [
            f"Difficulty: {difficulty}" if difficulty else "",
            f"Study Mode: {study_mode}" if study_mode else "",
        ]))
        lines.append(meta)
    lines.append("=" * 60)
    lines.append("")

    lines.append("EXPLANATION")
    lines.append("-" * 60)
    lines.append(_section_or_placeholder(parsed.get("explanation")))
    lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 60)
    lines.append(_section_or_placeholder(parsed.get("summary")))
    lines.append("")

    lines.append("IMPORTANT POINTS")
    lines.append("-" * 60)
    lines.append(_section_or_placeholder(parsed.get("important_points")))
    lines.append("")

    lines.append("QUIZ")
    lines.append("-" * 60)
    quiz = parsed.get("quiz") or []
    if quiz:
        for i, item in enumerate(quiz, 1):
            item_lines = _quiz_item_lines(item)
            lines.append(f"Q{i}. {item_lines[0]}")
            lines.extend(item_lines[1:])
            lines.append("")
    else:
        lines.append("(No quiz generated.)")
        lines.append("")

    lines.append("=" * 60)
    lines.append("Generated by AI Study Assistant")

    return "\n".join(lines).encode("utf-8")


# ---------------------------------------------------------------------------
# PDF export
# ---------------------------------------------------------------------------

def _add_pdf_section(pdf: FPDF, title: str, content: str) -> None:
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    _line(pdf, 8, _pdf_safe(title))
    pdf.ln(1)

    pdf.set_font("Helvetica", "", 10.5)
    pdf.set_text_color(50, 50, 50)
    content = _section_or_placeholder(content)
    for raw_line in content.split("\n"):
        line = _pdf_safe(raw_line).strip()
        if not line:
            pdf.ln(2)
            continue
        if line.startswith(("- ", "* ")):
            line = "- " + line[2:].strip()
        _line(pdf, 6, line)
    pdf.ln(3)


def to_pdf(parsed: dict, topic: str, difficulty: str = "", study_mode: str = "") -> bytes:
    """
    Build a formatted PDF export of the study material using fpdf2.

    `parsed` is the dict returned by Backend.parser.parse_study_material().
    Returns raw PDF bytes suitable for st.download_button(data=...).
    """
    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 20, 20)
    _line(pdf, 10, _pdf_safe(f"AI Study Assistant: {topic}"))

    # Meta line (difficulty / study mode)
    if difficulty or study_mode:
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(120, 120, 120)
        meta = " | ".join(filter(None, [
            f"Difficulty: {difficulty}" if difficulty else "",
            f"Study Mode: {study_mode}" if study_mode else "",
        ]))
        _line(pdf, 6, _pdf_safe(meta))

    pdf.set_draw_color(200, 200, 200)
    pdf.ln(2)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    _add_pdf_section(pdf, "Explanation", parsed.get("explanation"))
    _add_pdf_section(pdf, "Summary", parsed.get("summary"))
    _add_pdf_section(pdf, "Important Points", parsed.get("important_points"))

    # Quiz section (rendered as Q/A pairs, not raw markdown)
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(30, 30, 30)
    _line(pdf, 8, "Quiz")
    pdf.ln(1)

    quiz = parsed.get("quiz") or []
    if quiz:
        for i, item in enumerate(quiz, 1):
            item_lines = _quiz_item_lines(item)

            pdf.set_font("Helvetica", "B", 10.5)
            pdf.set_text_color(40, 40, 40)
            _line(pdf, 6, _pdf_safe(f"Q{i}. {item_lines[0]}"))

            pdf.set_font("Helvetica", "", 10.5)
            pdf.set_text_color(70, 70, 70)
            for extra_line in item_lines[1:]:
                _line(pdf, 6, _pdf_safe(extra_line))
            pdf.ln(2)
    else:
        pdf.set_font("Helvetica", "", 10.5)
        pdf.set_text_color(70, 70, 70)
        _line(pdf, 6, "(No quiz generated.)")

    # fpdf2's output() returns a bytearray -- normalize to bytes
    return bytes(pdf.output())


# ---------------------------------------------------------------------------
# Compare Mode exports
# ---------------------------------------------------------------------------

def compare_to_txt(compare_data: dict) -> bytes:
    """
    Build a plain-text export of a Compare Mode result.
    `compare_data` is the dict returned by parser.parse_compare_material().
    """
    topic_a = compare_data.get("topic_a", "Topic A")
    topic_b = compare_data.get("topic_b", "Topic B")

    lines = []
    lines.append(f"AI STUDY ASSISTANT — COMPARE MODE")
    lines.append(f"{topic_a}  vs  {topic_b}")
    lines.append("=" * 60)
    lines.append("")

    sections = [
        ("overview",     "OVERVIEW"),
        ("similarities", "SIMILARITIES"),
        ("differences",  "KEY DIFFERENCES"),
        ("use_cases",    "WHEN TO USE WHICH"),
        ("summary",      "QUICK SUMMARY"),
    ]

    for key, label in sections:
        content = compare_data.get(key, "")
        lines.append(label)
        lines.append("-" * 60)
        lines.append(_section_or_placeholder(content))
        lines.append("")

    lines.append("=" * 60)
    lines.append("Generated by AI Study Assistant — Compare Mode")

    return "\n".join(lines).encode("utf-8")


def compare_to_pdf(compare_data: dict) -> bytes:
    """
    Build a formatted PDF export of a Compare Mode result using fpdf2.
    Returns raw PDF bytes suitable for st.download_button(data=...).
    """
    topic_a = compare_data.get("topic_a", "Topic A")
    topic_b = compare_data.get("topic_b", "Topic B")

    pdf = FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.set_text_color(20, 20, 20)
    _line(pdf, 10, _pdf_safe(f"Compare: {topic_a}  vs  {topic_b}"))

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    _line(pdf, 6, "Generated by AI Study Assistant — Compare Mode")

    pdf.set_draw_color(200, 200, 200)
    pdf.ln(2)
    pdf.line(pdf.get_x(), pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(4)

    sections = [
        ("overview",     "Overview"),
        ("similarities", "Similarities"),
        ("differences",  "Key Differences"),
        ("use_cases",    "When to Use Which"),
        ("summary",      "Quick Summary"),
    ]

    for key, label in sections:
        content = compare_data.get(key, "")
        _add_pdf_section(pdf, label, content)

    return bytes(pdf.output())