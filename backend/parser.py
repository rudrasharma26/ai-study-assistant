"""
Backend/parser.py

Turns the raw AI response into structured data the frontend can render.

This replaces the original app.py's `result.split("###")`, which assumed
exactly 4 sections in a fixed order with nothing else in the text.

This module provides:
- parse_study_material(raw_text) -> dict with explanation/summary/
  important_points/quiz (quiz is a list of {"question", "answer"} dicts)
- check_answer(user_answer, correct_answer) -> (verdict, score) for the
  interactive "Attempt the Quiz" mode

Nothing here makes network calls or touches Streamlit -- it's pure text
processing, which makes it easy to test in isolation.
"""

import re
import difflib

from backend.prompts import (
    SECTION_EXPLANATION,
    SECTION_SUMMARY,
    SECTION_IMPORTANT_POINTS,
    SECTION_QUIZ,
    SECTION_HEADERS,
)

# ---------------------------------------------------------------------------
# Section parsing
# ---------------------------------------------------------------------------

# Matches a markdown heading like "### Explanation" on its own line and
# captures the heading text. Allows any number of leading #'s (### or ##)
# in case the model varies heading depth slightly.
_HEADING_PATTERN = re.compile(r'^#{2,4}\s*(.+?)\s*$', re.MULTILINE)

# Alternate header names the model might use, mapped to our canonical names.
_HEADER_ALIASES = {
    "explanation": SECTION_EXPLANATION,
    "concept explanation": SECTION_EXPLANATION,
    "summary": SECTION_SUMMARY,
    "revision notes": SECTION_SUMMARY,
    "important points": SECTION_IMPORTANT_POINTS,
    "key points": SECTION_IMPORTANT_POINTS,
    "important notes": SECTION_IMPORTANT_POINTS,
    "quiz": SECTION_QUIZ,
    "quiz questions": SECTION_QUIZ,
    "practice questions": SECTION_QUIZ,
}


def _match_header(header_text: str):
    """Map a heading found in the AI output to one of our canonical
    section names, or return None if it doesn't match anything known."""
    normalized = header_text.strip().lower()
    for canonical in SECTION_HEADERS:
        if canonical.lower() == normalized:
            return canonical
    return _HEADER_ALIASES.get(normalized)


def parse_sections(raw_text: str) -> dict:
    """
    Split the raw AI response into the four known sections by NAME, not by
    position. Any content under an unrecognized heading (or before the
    first heading) is appended to the Explanation section so nothing is
    silently lost.
    """
    sections = {header: "" for header in SECTION_HEADERS}

    if not raw_text or not raw_text.strip():
        return sections

    matches = list(_HEADING_PATTERN.finditer(raw_text))

    if not matches:
        # No headings at all -- treat the whole response as the explanation.
        sections[SECTION_EXPLANATION] = raw_text.strip()
        return sections

    # Anything before the first heading (rare, but don't lose it)
    preamble = raw_text[: matches[0].start()].strip()
    if preamble:
        sections[SECTION_EXPLANATION] = preamble

    for i, match in enumerate(matches):
        header_text = match.group(1)
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
        content = raw_text[start:end].strip()

        canonical = _match_header(header_text)
        if canonical is None:
            # Unknown heading -- keep it, attached to the explanation,
            # rather than dropping it.
            extra = f"#### {header_text.strip()}\n{content}"
            sections[SECTION_EXPLANATION] = (
                f"{sections[SECTION_EXPLANATION]}\n\n{extra}".strip()
                if sections[SECTION_EXPLANATION]
                else extra
            )
            continue

        if sections[canonical]:
            sections[canonical] = f"{sections[canonical]}\n\n{content}"
        else:
            sections[canonical] = content

    return sections


# ---------------------------------------------------------------------------
# Quiz parsing
# ---------------------------------------------------------------------------
#
# Two formats are produced by Backend.prompts.build_prompt():
#
#   MCQ:
#     **Q1 [MCQ]:** <question text>
#     A) <option>
#     B) <option>
#     C) <option>
#     D) <option>
#     **Answer:** B
#
#   SHORT:
#     **Q2 [SHORT]:** <question text>
#     **Answer:** <answer text>
#
# Each parsed item is a dict:
#   {"type": "mcq", "question": str, "options": {"A": ..., "B": ..., "C": ..., "D": ...}, "answer": "B"}
#   {"type": "short", "question": str, "answer": str}
#
# Older raw text (no [MCQ]/[SHORT] tag, plain "**Q1:** ... **Answer:** ...")
# is still supported and parsed as "short" -- so previously-generated
# content (or a model that ignores the tag instruction) doesn't break.

# Matches one question block. Requires the bold markers (**) and at
# least one digit around "Q<n>" -- this is intentionally STRICTER than
# a loose "any Q, any digits" pattern, because a loose version can
# false-match on a bare letter "Q" appearing inside the question or
# answer text itself (e.g. the word "Query"), which truncated questions
# mid-word in earlier versions of this parser. The prompt in
# Backend.prompts always produces "**Q<n> [TAG]:**", so this is safe.
_QUIZ_BLOCK_PATTERN = re.compile(
    r'\*{2}Q\s*\d+\s*(?:\[\s*(MCQ|SHORT)\s*\])?\s*:?\*{2}\s*'
    r'(.*?)'
    r'(?=\*{2}Q\s*\d+\s*(?:\[\s*(?:MCQ|SHORT)\s*\])?\s*:?\*{2}|\Z)',
    re.DOTALL | re.IGNORECASE,
)

# Within an MCQ block: pulls out "A) text" / "B) text" / etc. and the
# final "**Answer:** <letter>" line.
_MCQ_OPTION_PATTERN = re.compile(
    r'^\s*\*{0,2}([A-D])[).]\s*\*{0,2}\s*(.+?)\s*$',
    re.MULTILINE | re.IGNORECASE,
)
_MCQ_ANSWER_LETTER_PATTERN = re.compile(
    r'\*{0,2}Answer\s*[:.)]?\*{0,2}\s*\(?([A-D])\)?',
    re.IGNORECASE,
)

# Within a SHORT (or untagged) block: question text, then
# "**Answer:** <free text>".
_SHORT_ANSWER_PATTERN = re.compile(
    r'^(.*?)\s*\*{0,2}Answer\s*[:.)]?\*{0,2}\s*(.*)$',
    re.DOTALL | re.IGNORECASE,
)


def _parse_mcq_block(body: str):
    """
    Parse an [MCQ]-tagged block body into
    {"type": "mcq", "question": ..., "options": {...}, "answer": "A"},
    or None if it doesn't look like a valid MCQ (missing options/answer).
    """
    # The question text is everything before the first "A) ..." option line.
    first_option_match = _MCQ_OPTION_PATTERN.search(body)
    if not first_option_match:
        return None

    question = body[:first_option_match.start()].strip()

    options = {}
    for letter, text in _MCQ_OPTION_PATTERN.findall(body):
        options[letter.upper()] = text.strip()

    answer_match = _MCQ_ANSWER_LETTER_PATTERN.search(body)
    if not answer_match:
        return None
    answer_letter = answer_match.group(1).upper()

    if not question or len(options) < 2 or answer_letter not in options:
        return None

    return {
        "type": "mcq",
        "question": question,
        "options": options,
        "answer": answer_letter,
    }


def _parse_short_block(body: str):
    """
    Parse a [SHORT]-tagged (or untagged, legacy) block body into
    {"type": "short", "question": ..., "answer": ...}, or None if it
    doesn't contain a recognizable "**Answer:** ..." split.
    """
    match = _SHORT_ANSWER_PATTERN.match(body)
    if not match:
        return None

    question = match.group(1).strip()
    answer = match.group(2).strip()

    if not question or not answer:
        return None

    return {"type": "short", "question": question, "answer": answer}


def parse_quiz(quiz_text: str) -> list:
    """
    Parse the Quiz section into a list of question dicts (see module-level
    docstring above for the two shapes: "mcq" and "short").

    Falls back to a single raw item if no question blocks can be parsed,
    so the quiz tab never ends up empty when the model has actually
    written *something* there.
    """
    quiz_text = (quiz_text or "").strip()
    if not quiz_text:
        return []

    items = []
    for tag, body in _QUIZ_BLOCK_PATTERN.findall(quiz_text):
        body = body.strip()
        if not body:
            continue

        tag = (tag or "").strip().upper()
        parsed = None

        if tag == "MCQ":
            parsed = _parse_mcq_block(body)
        elif tag == "SHORT":
            parsed = _parse_short_block(body)
        else:
            # No tag (legacy format): try MCQ first (in case the model
            # added options without the tag), then fall back to short.
            parsed = _parse_mcq_block(body) or _parse_short_block(body)

        if parsed:
            items.append(parsed)

    if items:
        return items

    # Fallback: model didn't follow the expected format at all. Show the
    # raw text as a single "question" so the user still sees content
    # instead of an empty quiz tab.
    return [{
        "type": "short",
        "question": "Quiz (shown as provided by the AI)",
        "answer": quiz_text,
    }]


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def parse_study_material(raw_text: str) -> dict:
    """
    Parse a full raw AI response into a structured dict:

    {
        "explanation": str,
        "summary": str,
        "important_points": str,
        "quiz": [{"question": str, "answer": str}, ...],
        "raw": str,   # original text, for export/copy
    }
    """
    sections = parse_sections(raw_text)
    return {
        "explanation": sections.get(SECTION_EXPLANATION, "").strip(),
        "summary": sections.get(SECTION_SUMMARY, "").strip(),
        "important_points": sections.get(SECTION_IMPORTANT_POINTS, "").strip(),
        "quiz": parse_quiz(sections.get(SECTION_QUIZ, "")),
        "raw": raw_text or "",
    }


# ---------------------------------------------------------------------------
# Interactive "Attempt the Quiz" answer checking
# ---------------------------------------------------------------------------

_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "of", "to", "in", "on",
    "for", "and", "or", "it", "its", "this", "that", "these", "those",
    "with", "as", "by", "be", "been", "being", "at", "from", "into",
    "their", "they", "which", "what", "who", "whom", "than", "then",
    "so", "but", "if", "we", "you", "your", "i",
}


def _significant_words(text: str) -> set:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {w for w in words if w not in _STOPWORDS and len(w) > 1}


def check_answer(user_answer: str, correct_answer: str):
    """
    Heuristically compare a student's free-text answer to the AI's
    reference answer for the interactive "Attempt the Quiz" mode.

    NOTE: This is intentionally a lightweight, zero-cost heuristic
    (word overlap + sequence similarity) -- NOT a perfect grader.
    True free-text grading would need another AI call. The verdict is
    meant to set the tone of an encouraging reveal, not to be the final
    word -- the reference answer is always shown alongside it.

    Returns:
        (verdict, score) where:
          - verdict is one of "correct", "partial", "incorrect", "empty"
          - score is a float 0.0-1.0 indicating overlap with the
            reference answer
    """
    user_answer = (user_answer or "").strip()
    correct_answer = (correct_answer or "").strip()

    if not user_answer:
        return "empty", 0.0

    user_words = _significant_words(user_answer)
    correct_words = _significant_words(correct_answer)

    if correct_words:
        overlap = len(user_words & correct_words) / len(correct_words)
    else:
        overlap = 0.0

    similarity = difflib.SequenceMatcher(
        None, user_answer.lower(), correct_answer.lower()
    ).ratio()

    score = max(overlap, similarity)

    if score >= 0.55:
        verdict = "correct"
    elif score >= 0.25:
        verdict = "partial"
    else:
        verdict = "incorrect"

    return verdict, round(score, 2)


# ---------------------------------------------------------------------------
# Compare Mode parser
# ---------------------------------------------------------------------------

# Import Compare Mode section headers (defined in prompts.py).
# Done here rather than at module top to avoid a circular-import risk if
# prompts.py ever imported from parser.py.
from backend.prompts import (  # noqa: E402
    COMPARE_SECTION_HEADERS,
    SECTION_COMPARE_OVERVIEW,
    SECTION_COMPARE_SIMILARITIES,
    SECTION_COMPARE_DIFFERENCES,
    SECTION_COMPARE_USECASES,
    SECTION_COMPARE_SUMMARY,
)

# Aliases the model might use for Compare Mode sections.
_COMPARE_HEADER_ALIASES = {
    "overview": SECTION_COMPARE_OVERVIEW,
    "introduction": SECTION_COMPARE_OVERVIEW,
    "similarities": SECTION_COMPARE_SIMILARITIES,
    "similar": SECTION_COMPARE_SIMILARITIES,
    "key differences": SECTION_COMPARE_DIFFERENCES,
    "differences": SECTION_COMPARE_DIFFERENCES,
    "when to use which": SECTION_COMPARE_USECASES,
    "when to use": SECTION_COMPARE_USECASES,
    "use cases": SECTION_COMPARE_USECASES,
    "quick summary": SECTION_COMPARE_SUMMARY,
    "summary": SECTION_COMPARE_SUMMARY,
    "conclusion": SECTION_COMPARE_SUMMARY,
}


def _match_compare_header(header_text: str):
    normalized = header_text.strip().lower()
    for canonical in COMPARE_SECTION_HEADERS:
        if canonical.lower() == normalized:
            return canonical
    return _COMPARE_HEADER_ALIASES.get(normalized)


def parse_compare_material(raw_text: str, topic_a: str = "", topic_b: str = "") -> dict:
    """
    Parse a Compare Mode AI response into a structured dict:

    {
        "topic_a": str,
        "topic_b": str,
        "overview": str,
        "similarities": str,
        "differences": str,       # contains a markdown table
        "use_cases": str,
        "summary": str,
        "raw": str,
    }

    Uses the same heading-scan approach as parse_sections() but maps
    to COMPARE_SECTION_HEADERS instead of SECTION_HEADERS.
    """
    sections = {header: "" for header in COMPARE_SECTION_HEADERS}

    if not raw_text or not raw_text.strip():
        return {
            "topic_a": topic_a,
            "topic_b": topic_b,
            "overview": "",
            "similarities": "",
            "differences": "",
            "use_cases": "",
            "summary": "",
            "raw": raw_text or "",
        }

    matches = list(_HEADING_PATTERN.finditer(raw_text))

    if not matches:
        sections[SECTION_COMPARE_OVERVIEW] = raw_text.strip()
    else:
        preamble = raw_text[: matches[0].start()].strip()
        if preamble:
            sections[SECTION_COMPARE_OVERVIEW] = preamble

        for i, match in enumerate(matches):
            header_text = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_text)
            content = raw_text[start:end].strip()

            canonical = _match_compare_header(header_text)
            if canonical is None:
                # Attach unknown sections to overview rather than dropping.
                sections[SECTION_COMPARE_OVERVIEW] = (
                    f"{sections[SECTION_COMPARE_OVERVIEW]}\n\n{content}".strip()
                )
                continue

            if sections[canonical]:
                sections[canonical] = f"{sections[canonical]}\n\n{content}"
            else:
                sections[canonical] = content

    return {
        "topic_a": topic_a,
        "topic_b": topic_b,
        "overview": sections.get(SECTION_COMPARE_OVERVIEW, "").strip(),
        "similarities": sections.get(SECTION_COMPARE_SIMILARITIES, "").strip(),
        "differences": sections.get(SECTION_COMPARE_DIFFERENCES, "").strip(),
        "use_cases": sections.get(SECTION_COMPARE_USECASES, "").strip(),
        "summary": sections.get(SECTION_COMPARE_SUMMARY, "").strip(),
        "raw": raw_text or "",
    }


# ---------------------------------------------------------------------------
# Study schedule / spaced repetition response parser
# ---------------------------------------------------------------------------

import json as _json  # noqa: E402 -- stdlib, no circular risk


def parse_study_schedule(raw_response: str) -> list:
    """
    Parse the JSON array returned by ai_handler.get_study_suggestions().

    Expected format from the model (see prompts.build_study_schedule_prompt):
        [{"topic": "...", "reason": "..."}, ...]

    Returns a list of {"topic": str, "reason": str} dicts.
    Falls back to [] if the response can't be parsed -- never raises.
    """
    if not raw_response or not raw_response.strip():
        return []

    # Strip any accidental markdown fences the model might have added.
    text = raw_response.strip()
    text = re.sub(r'^```(?:json)?\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'\s*```$', '', text, flags=re.MULTILINE)
    text = text.strip()

    # Find the first [...] array in the response.
    array_match = re.search(r'\[.*\]', text, re.DOTALL)
    if not array_match:
        return []

    try:
        items = _json.loads(array_match.group(0))
    except (_json.JSONDecodeError, ValueError):
        return []

    if not isinstance(items, list):
        return []

    # Validate and clean each item.
    result = []
    for item in items:
        if not isinstance(item, dict):
            continue
        topic = str(item.get("topic", "")).strip()
        reason = str(item.get("reason", "")).strip()
        if topic:
            result.append({"topic": topic, "reason": reason})

    return result