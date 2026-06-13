"""
Backend/prompts.py

Builds dynamic, mode-aware prompts for the AI Study Assistant.

This module has ONE job: turn (topic, difficulty, study_mode) into a single
prompt string for the model. It does not make any network calls — that lives
in ai_handler.py.

The model used is deepseek/deepseek-chat-v3-0324 (via OpenRouter), unchanged
from the original project.
"""

# ---------------------------------------------------------------------------
# Section headers — single source of truth.
# Backend/parser.py imports these so the prompt format and the parser can
# never drift apart.
# ---------------------------------------------------------------------------
SECTION_EXPLANATION = "Explanation"
SECTION_SUMMARY = "Summary"
SECTION_IMPORTANT_POINTS = "Important Points"
SECTION_QUIZ = "Quiz"

SECTION_HEADERS = [
    SECTION_EXPLANATION,
    SECTION_SUMMARY,
    SECTION_IMPORTANT_POINTS,
    SECTION_QUIZ,
]

# Allowed values for the UI dropdowns. app.py imports these so the dropdown
# options and the prompt logic can never get out of sync.
DIFFICULTY_LEVELS = ["Beginner", "Intermediate", "Advanced"]
STUDY_MODES = ["Learn Mode", "Revision Mode", "Exam Mode"]

DEFAULT_DIFFICULTY = "Intermediate"
DEFAULT_STUDY_MODE = "Learn Mode"


# ---------------------------------------------------------------------------
# Difficulty-specific instructions
# ---------------------------------------------------------------------------
_DIFFICULTY_INSTRUCTIONS = {
    "Beginner": (
        "Explain as if teaching someone completely new to this subject. "
        "Use simple everyday language, avoid jargon (or explain it the "
        "moment you use it), and use relatable real-world analogies."
    ),
    "Intermediate": (
        "Explain at the level of a student who already knows the basics "
        "of the subject area. You can use standard technical terminology, "
        "but still clarify any non-obvious concepts and include at least "
        "one example."
    ),
    "Advanced": (
        "Explain at the level of someone preparing for an interview or "
        "advanced exam. Use precise technical terminology, go into "
        "underlying mechanisms/trade-offs, and avoid oversimplification."
    ),
}

# ---------------------------------------------------------------------------
# Study-mode-specific instructions and quiz sizing
# ---------------------------------------------------------------------------
_STUDY_MODE_INSTRUCTIONS = {
    "Learn Mode": (
        "The student is learning this topic for the first time. The "
        "Explanation section should be the most detailed part of the "
        "response, walking through the concept step by step."
    ),
    "Revision Mode": (
        "The student already knows this topic and is revising before a "
        "test. Keep the Explanation section short (a quick refresher only) "
        "and put more effort into the Summary and Important Points "
        "sections, which should be dense, scannable, and easy to skim."
    ),
    "Exam Mode": (
        "The student is preparing for an exam. Frame the Explanation and "
        "Important Points around what is most likely to be tested. The "
        "Quiz section is the priority — make it exam-style with a slightly "
        "harder, more probing set of questions."
    ),
}

_QUIZ_QUESTION_COUNT = {
    "Learn Mode": 3,
    "Revision Mode": 4,
    "Exam Mode": 6,
}


def build_prompt(topic: str, difficulty: str = DEFAULT_DIFFICULTY,
                  study_mode: str = DEFAULT_STUDY_MODE) -> str:
    """
    Build the full prompt sent to the model.

    Falls back to sensible defaults if an unknown difficulty/study_mode
    value is passed in, so this function never raises on bad input.
    """
    difficulty_instruction = _DIFFICULTY_INSTRUCTIONS.get(
        difficulty, _DIFFICULTY_INSTRUCTIONS[DEFAULT_DIFFICULTY]
    )
    mode_instruction = _STUDY_MODE_INSTRUCTIONS.get(
        study_mode, _STUDY_MODE_INSTRUCTIONS[DEFAULT_STUDY_MODE]
    )
    quiz_count = _QUIZ_QUESTION_COUNT.get(study_mode, 3)

    topic = topic.strip()

    prompt = f"""You are an elite AI Study Assistant helping a student learn the topic below.

TOPIC: {topic}

DIFFICULTY LEVEL: {difficulty}
{difficulty_instruction}

STUDY MODE: {study_mode}
{mode_instruction}

You MUST respond using EXACTLY this structure, with these exact section
headers (do not rename, reorder, merge, or skip any of them):

### {SECTION_EXPLANATION}
A clear explanation of the topic, following the difficulty and study mode
instructions above.

### {SECTION_SUMMARY}
Concise revision notes, written as short paragraphs or bullet points.

### {SECTION_IMPORTANT_POINTS}
A bulleted list of the most important facts, terms, or formulas. Use "-" for
each bullet. No long paragraphs here.

### {SECTION_QUIZ}
Create exactly {quiz_count} quiz questions to test understanding of this
topic. Format EVERY question and answer EXACTLY like this, with nothing else
in between:

**Q1:** <question text>
**Answer:** <answer text>

**Q2:** <question text>
**Answer:** <answer text>

(continue this exact Q/Answer pattern for all {quiz_count} questions)

FORMATTING RULES:
- Use the exact "### " headers shown above, spelled exactly as given.
- Do not add any extra top-level "###" headers.
- Do not add any introduction or closing remarks outside the four sections.
- Keep the tone clear, encouraging, and student-friendly.
"""

    return prompt


# ---------------------------------------------------------------------------
# Quiz answer grading prompt (interactive "Attempt the Quiz" mode)
# ---------------------------------------------------------------------------

# The only verdict values the grading prompt is allowed to return.
# Backend.ai_handler.grade_quiz_answer() validates against this list and
# falls back to a local heuristic if the model returns anything else.
GRADE_VERDICTS = ["correct", "partial", "incorrect"]


def build_grading_prompt(question: str, correct_answer: str, user_answer: str) -> str:
    """
    Build a prompt asking the model to grade a student's free-text quiz
    answer against the reference answer.

    The model is instructed to tolerate paraphrasing, synonyms, different
    levels of detail, and minor spelling mistakes -- and to respond with
    STRICT JSON only:

        {"verdict": "correct" | "partial" | "incorrect", "feedback": "..."}

    This prompt's exact wording is not safety-critical: if the model's
    response can't be parsed as valid JSON with a known verdict,
    Backend.ai_handler.grade_quiz_answer() falls back to the local
    word-overlap heuristic in Backend.parser.check_answer().
    """
    question = (question or "").strip()
    correct_answer = (correct_answer or "").strip()
    user_answer = (user_answer or "").strip()

    return f"""You are grading a student's answer to a quiz question. Be fair and
generous: focus on whether the student understood the CONCEPT, not on exact
wording. Tolerate paraphrasing, synonyms, minor spelling mistakes, and
different levels of detail or completeness.

QUESTION:
{question}

REFERENCE ANSWER:
{correct_answer}

STUDENT'S ANSWER:
{user_answer}

Grade the student's answer as exactly one of:
- "correct": captures the key idea/concept of the reference answer, even if
  worded very differently, less formally, or with minor mistakes.
- "partial": shows some real understanding but misses an important part of
  the reference answer, or is incomplete.
- "incorrect": wrong, unrelated, off-topic, or left blank.

Respond with ONLY a single JSON object on one line. No extra text, no
explanation outside the JSON, no markdown formatting, no code fences.
Respond in EXACTLY this format:

{{"verdict": "correct", "feedback": "short 1-2 sentence encouraging feedback"}}

Rules:
- "verdict" must be exactly one of: "correct", "partial", "incorrect"
  (lowercase, no other values).
- "feedback" must be at most 2 short sentences, warm and encouraging,
  briefly noting what was right or what was missed.
"""