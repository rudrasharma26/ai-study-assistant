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
    "Exam Mode": 10,
}

# For Exam Mode only: how many of the questions should be MCQ vs
# short-answer. Other modes are all short-answer (no MCQ).
_EXAM_MODE_MCQ_COUNT = 5
_EXAM_MODE_SHORT_COUNT = 5


def _build_quiz_instructions(study_mode: str, quiz_count: int) -> str:
    """
    Build the Quiz-section instructions for the prompt.

    - Exam Mode: a fixed mix of MCQ and short-answer questions, using a
      [MCQ]/[SHORT] tag on each question so Backend.parser can tell them
      apart and Backend.ai_handler/frontend.components can render/grade
      them differently (radio buttons + exact match for MCQ, free text +
      AI grading for short answer).
    - Learn Mode / Revision Mode: all short-answer, using the original
      simple Q/Answer format (tagged [SHORT] for a single consistent
      parser path).
    """
    if study_mode == "Exam Mode":
        mcq_count = _EXAM_MODE_MCQ_COUNT
        short_count = _EXAM_MODE_SHORT_COUNT
        return f"""Create exactly {quiz_count} quiz questions: {mcq_count} multiple-choice
questions (MCQ) followed by {short_count} short-answer questions. Format
EVERY question EXACTLY like one of the two patterns below, with nothing
else in between:

MCQ pattern:
**Q1 [MCQ]:** <question text>
A) <option text>
B) <option text>
C) <option text>
D) <option text>
**Answer:** <the single correct letter, e.g. B>

Short-answer pattern:
**Q{mcq_count + 1} [SHORT]:** <question text>
**Answer:** <answer text>

Use the [MCQ] tag for questions {1} through {mcq_count}, and the [SHORT]
tag for questions {mcq_count + 1} through {quiz_count}. Each MCQ MUST have
exactly 4 options labeled A) B) C) D), with exactly one correct answer
given as a single letter (A, B, C, or D) on the **Answer:** line -- nothing
else on that line. Make the MCQs exam-style and slightly harder, with
plausible distractors (wrong options that are common misconceptions, not
obviously wrong)."""

    return f"""Create exactly {quiz_count} quiz questions to test understanding of this
topic. Format EVERY question and answer EXACTLY like this, with nothing else
in between:

**Q1 [SHORT]:** <question text>
**Answer:** <answer text>

**Q2 [SHORT]:** <question text>
**Answer:** <answer text>

(continue this exact Q/Answer pattern, using the [SHORT] tag, for all
{quiz_count} questions)"""


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
    quiz_instructions = _build_quiz_instructions(study_mode, quiz_count)

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
{quiz_instructions}

MATH AND FORMULA FORMATTING (applies to ALL sections above):
- Whenever you write a mathematical expression, formula, or equation,
  wrap it in Markdown math delimiters so it renders properly: use
  single dollar signs for inline math, e.g. $E = mc^2$, and double
  dollar signs on their own lines for standalone/block equations, e.g.
  $$F = ma$$
- Use standard LaTeX syntax inside the dollar signs (e.g. \\frac{{a}}{{b}},
  \\vec{{v}}, x^2, \\sqrt{{x}}, \\sum, \\int).
- NEVER write formulas inside square brackets like [ ... ] or as plain
  text like (a) is acceleration -- always use $...$ or $$...$$ instead.
- For topics with no math, simply don't use math notation -- don't force
  formulas where they don't belong.

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


# ---------------------------------------------------------------------------
# Compare Mode
# ---------------------------------------------------------------------------
# Compare Mode generates a structured side-by-side comparison of two topics.
# It uses a completely different section structure from the standard study
# material, so we define separate section headers here.

SECTION_COMPARE_OVERVIEW = "Overview"
SECTION_COMPARE_SIMILARITIES = "Similarities"
SECTION_COMPARE_DIFFERENCES = "Key Differences"
SECTION_COMPARE_USECASES = "When to Use Which"
SECTION_COMPARE_SUMMARY = "Quick Summary"

COMPARE_SECTION_HEADERS = [
    SECTION_COMPARE_OVERVIEW,
    SECTION_COMPARE_SIMILARITIES,
    SECTION_COMPARE_DIFFERENCES,
    SECTION_COMPARE_USECASES,
    SECTION_COMPARE_SUMMARY,
]


def build_compare_prompt(topic_a: str, topic_b: str,
                          difficulty: str = DEFAULT_DIFFICULTY) -> str:
    """
    Build a prompt for Compare Mode: a structured side-by-side comparison
    of two topics. Returns a single prompt string for the model.

    The response structure is different from standard study material --
    it uses COMPARE_SECTION_HEADERS instead of SECTION_HEADERS, so
    parser.py has a separate parse_compare_material() function.
    """
    topic_a = (topic_a or "").strip()
    topic_b = (topic_b or "").strip()

    difficulty_instruction = _DIFFICULTY_INSTRUCTIONS.get(
        difficulty, _DIFFICULTY_INSTRUCTIONS[DEFAULT_DIFFICULTY]
    )

    return f"""You are an expert AI tutor. A student wants to understand the
difference between two related topics.

TOPIC A: {topic_a}
TOPIC B: {topic_b}

DIFFICULTY LEVEL: {difficulty}
{difficulty_instruction}

Produce a clear, structured comparison. Use EXACTLY these section headers
(do not rename, reorder, or skip any):

### {SECTION_COMPARE_OVERVIEW}
One short paragraph each introducing {topic_a} and {topic_b} -- what each
one IS, in plain terms.

### {SECTION_COMPARE_SIMILARITIES}
A bulleted list ("-") of the most important ways {topic_a} and {topic_b}
are similar or serve the same purpose.

### {SECTION_COMPARE_DIFFERENCES}
A markdown table with columns: Feature | {topic_a} | {topic_b}
Include at least 5 rows covering the most important distinguishing
characteristics (e.g. performance, use case, complexity, syntax, etc.).

### {SECTION_COMPARE_USECASES}
Clear guidance on WHEN to pick {topic_a} vs {topic_b}. Use two short
subsections:
- **Choose {topic_a} when:** (3-4 bullet points)
- **Choose {topic_b} when:** (3-4 bullet points)

### {SECTION_COMPARE_SUMMARY}
A 2-3 sentence plain-English summary a student can memorize: the single
most important distinction between the two topics, and the simplest rule
for choosing between them.

MATH AND FORMULA FORMATTING:
- Use $...$ for inline math and $$...$$ on its own line for block equations.
- Never use square brackets [ ... ] for formulas.

FORMATTING RULES:
- Use exactly the "### " headers above, spelled exactly as given.
- Do not add any extra headers, introduction, or closing remarks.
- Keep the tone clear, student-friendly, and direct.
"""


# ---------------------------------------------------------------------------
# Auto-difficulty detection
# ---------------------------------------------------------------------------

def build_auto_difficulty_prompt(topic: str) -> str:
    """
    Build a short, cheap prompt that asks the model to classify a topic's
    natural difficulty level (Beginner / Intermediate / Advanced).

    Used in ai_handler.py for the auto-difficulty feature: when a user
    types a topic, we fire this lightweight call first and pre-select the
    difficulty dropdown. The model is instructed to respond with ONLY the
    one-word level so we can parse the response without JSON handling.
    """
    topic = (topic or "").strip()
    levels = " / ".join(DIFFICULTY_LEVELS)

    return f"""You are a curriculum expert. Classify the academic difficulty of
the following topic for a typical student:

TOPIC: {topic}

Respond with ONLY one word -- exactly one of: {levels}
Do not add any explanation, punctuation, or extra text. Just the single word.

Rules:
- Beginner: a topic covered in high school or in the first year of university,
  or something a curious non-specialist could pick up quickly.
- Intermediate: a topic typically covered in later undergraduate study, or
  something that requires prerequisite knowledge to understand properly.
- Advanced: a topic at graduate level, or one that requires significant
  prior expertise and is unlikely to be understood without it."""


# ---------------------------------------------------------------------------
# Follow-up / "Explain further" questions
# ---------------------------------------------------------------------------

def build_followup_prompt(topic: str, section_content: str,
                           question: str) -> str:
    """
    Build a prompt for the "Ask a follow-up" feature.

    Given the already-generated explanation for a topic and the user's
    specific follow-up question, produce a focused, concise answer --
    not a full study material regeneration.

    Used by ai_handler.py's answer_followup() function, which streams
    the response back to the UI.
    """
    topic = (topic or "").strip()
    question = (question or "").strip()
    # Truncate the section content to keep the prompt cheap -- we only
    # need enough context for the model to answer in context.
    context = (section_content or "")[:1500].strip()

    return f"""You are an AI tutor who has just explained the topic "{topic}" to
a student. Here is the explanation you gave:

---
{context}
---

The student has a follow-up question:

QUESTION: {question}

Answer the question directly and concisely. Stay focused on what was asked --
do not re-explain the whole topic. Aim for 2-5 sentences unless a longer
answer is genuinely necessary. Use the same math formatting rules as before
($...$ for inline math, $$...$$ for block equations). Keep the tone warm
and encouraging."""


# ---------------------------------------------------------------------------
# Study schedule / spaced repetition suggestions
# ---------------------------------------------------------------------------

def build_study_schedule_prompt(history: list) -> str:
    """
    Build a prompt that takes the user's search history and suggests which
    topics to review today, using basic spaced repetition principles.

    `history` is a list of dicts: {"topic", "difficulty", "study_mode"}.
    Returns a prompt whose response is a short structured suggestion list.

    Used by ai_handler.py's get_study_suggestions() function.
    """
    if not history:
        return ""

    # Format history as a readable list for the model (most recent first,
    # cap at 10 to keep prompt cheap).
    history_lines = "\n".join(
        f"{i+1}. {item.get('topic', '')} "
        f"({item.get('difficulty', '')} / {item.get('study_mode', '')})"
        for i, item in enumerate(history[:10])
    )

    return f"""You are a study coach. A student has recently studied the following
topics (most recent first):

{history_lines}

Based on spaced repetition principles, suggest which 2-3 topics from this
list the student should review TODAY to reinforce their memory most
effectively. Topics studied most recently need less immediate review; topics
from earlier in the list benefit more from a quick revisit now.

Respond with ONLY a JSON array on a single line. No extra text, no markdown,
no explanation. Each item should have "topic" and "reason" keys:

[{{"topic": "...", "reason": "1 short sentence why to review today"}}, ...]

The "reason" must be at most one sentence. Only include topics from the list
above -- do not invent new ones. Suggest 2-3 topics maximum."""


# ---------------------------------------------------------------------------
# Topic notes / annotations
# ---------------------------------------------------------------------------

def build_notes_summary_prompt(topic: str, notes: str) -> str:
    """
    Build a prompt that takes the user's raw personal notes on a topic
    and returns a cleaned-up, structured version.

    Used optionally when the user clicks "Polish my notes" in the notes
    annotation feature.
    """
    topic = (topic or "").strip()
    notes = (notes or "").strip()

    return f"""A student has written rough personal notes on the topic "{topic}".
Polish these notes into clean, well-structured bullet points that are easy
to revise from. Keep all the student's own ideas -- do not add new content
they didn't mention. Fix grammar and spelling. Group related points together.

STUDENT'S NOTES:
{notes}

Respond with ONLY the polished bullet points, using "-" for each bullet.
No introduction, no "Here are your notes:", just the bullets directly."""