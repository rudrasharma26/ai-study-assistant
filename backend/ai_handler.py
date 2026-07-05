"""
Backend/ai_handler.py

Handles all communication with the OpenRouter API.

This is the evolved version of the original gemini_handler.py:
- Same OpenRouter endpoint
- Same model: deepseek/deepseek-chat-v3-0324
- Same .env-based API key loading (OPENROUTER_API_KEY)

What's new:
- A request timeout, so a hung request can no longer freeze the app
- Structured (success, data_or_message) return values instead of raw
  strings/crashes, so the UI can show clean error messages
- Distinguishes between missing key, network errors, rate limits, server
  errors, and malformed responses
- generate_study_material() builds its prompt via Backend.prompts, with
  difficulty and study-mode support
- explain_topic() kept as a backward-compatible wrapper
- grade_quiz_answer() provides AI-based grading of free-text quiz answers
  (tolerant of paraphrasing/typos), with an automatic fallback to the local
  heuristic in Backend.parser.check_answer() if the AI call or its response
  isn't usable -- this function NEVER raises and ALWAYS returns a result.
"""

import os
import json
import re
import requests
from dotenv import load_dotenv

from backend.prompts import (
    build_prompt,
    build_grading_prompt,
    build_compare_prompt,
    build_auto_difficulty_prompt,
    build_followup_prompt,
    build_study_schedule_prompt,
    GRADE_VERDICTS,
    DEFAULT_DIFFICULTY,
    DEFAULT_STUDY_MODE,
)
from backend.parser import check_answer, parse_compare_material, parse_study_schedule

# Load environment variables (.env in project root)
load_dotenv()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "deepseek/deepseek-chat-v3-0324"
REQUEST_TIMEOUT = 60  # seconds

# Caps the AI's response length to keep token usage (and cost) bounded.
# 3000 tokens is generous enough for a full Explanation + Summary +
# Important Points + Quiz, including "Exam Mode" with 10 quiz questions
# (5 MCQ with 4 options each + 5 short-answer), without ever cutting a
# study session short mid-section.
MAX_RESPONSE_TOKENS = 3000

API_KEY = os.getenv("OPENROUTER_API_KEY")


def _call_openrouter(prompt: str):
    """
    Low-level call to OpenRouter's chat completions endpoint.

    Returns:
        (True, content)        on success
        (False, error_message) on any failure
    """
    if not API_KEY:
        return False, (
            "Missing API key. Please set OPENROUTER_API_KEY in your .env file."
        )

    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": MAX_RESPONSE_TOKENS,
            },
            timeout=REQUEST_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        return False, "The request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return False, "Could not connect to the AI service. Check your internet connection."
    except requests.exceptions.RequestException as exc:
        return False, f"Network error: {exc}"

    # Handle HTTP-level failures with friendly messages
    if response.status_code == 401:
        return False, "Invalid API key. Please check your OPENROUTER_API_KEY."
    if response.status_code == 429:
        return False, "Rate limit reached. Please wait a moment and try again."
    if response.status_code >= 500:
        return False, "The AI service is currently unavailable. Please try again shortly."
    if response.status_code != 200:
        return False, f"Unexpected error (status {response.status_code}). Please try again."

    # Parse JSON body
    try:
        result = response.json()
    except ValueError:
        return False, "Received an invalid response from the AI service."

    # OpenRouter sometimes returns 200 with an "error" payload
    if "error" in result:
        message = result["error"].get("message", "Unknown error from the AI service.")
        return False, f"AI service error: {message}"

    # Extract the actual generated text
    try:
        content = result["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        return False, "The AI response was empty or malformed. Please try again."

    if not content or not content.strip():
        return False, "The AI returned an empty response. Please try again."

    return True, content


def generate_study_material(topic: str, difficulty: str = DEFAULT_DIFFICULTY,
                              study_mode: str = DEFAULT_STUDY_MODE):
    """
    Main entry point used by the app.

    Builds a difficulty/study-mode-aware prompt via Backend.prompts and
    sends it to OpenRouter.

    Returns:
        (True, content)        on success
        (False, error_message) on any failure
    """
    topic = (topic or "").strip()
    if not topic:
        return False, "Please enter a topic before generating study material."

    prompt = build_prompt(topic, difficulty, study_mode)
    return _call_openrouter(prompt)


def explain_topic(topic: str) -> str:
    """
    Backward-compatible wrapper matching the original gemini_handler.py
    signature: explain_topic(topic) -> str.

    Returns the generated content as a string, or an "Error: ..." string
    on failure (never raises).
    """
    success, data = generate_study_material(topic)
    if success:
        return data
    return f"Error: {data}"


# ---------------------------------------------------------------------------
# Interactive quiz grading ("Attempt the Quiz" mode)
# ---------------------------------------------------------------------------

# Matches the first {...} block in the model's response, even if it wrapped
# the JSON in a sentence or code fence despite instructions not to.
_JSON_OBJECT_PATTERN = re.compile(r"\{.*\}", re.DOTALL)

# User-facing feedback used when falling back to the local heuristic
# (Backend.parser.check_answer) -- either because the AI call failed, or
# because its response couldn't be parsed as valid grading JSON.
_FALLBACK_FEEDBACK = {
    "correct": "Correct! Nice work.",
    "partial": "You're on the right track, but missing a part of the full answer.",
    "incorrect": "Not quite -- take a look at the correct answer below.",
    "empty": "You didn't enter an answer -- here's the correct one to review.",
}


def _parse_grading_response(content: str):
    """
    Try to extract {"verdict": ..., "feedback": ...} from the model's raw
    response text.

    Returns a dict with "verdict" and "feedback" on success, or None if the
    response isn't valid/usable (missing JSON, malformed JSON, or an
    unrecognized verdict value).
    """
    if not content:
        return None

    match = _JSON_OBJECT_PATTERN.search(content)
    if not match:
        return None

    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    verdict = str(data.get("verdict", "")).strip().lower()
    if verdict not in GRADE_VERDICTS:
        return None

    feedback = str(data.get("feedback", "")).strip()
    if not feedback:
        feedback = _FALLBACK_FEEDBACK.get(verdict, "")

    return {"verdict": verdict, "feedback": feedback}


def grade_quiz_answer(question: str, correct_answer: str, user_answer: str) -> dict:
    """
    Grade a student's free-text quiz answer for the interactive
    "Attempt the Quiz" mode.

    Tries an AI-based grading call first via Backend.prompts.build_grading_prompt
    -- this tolerates paraphrasing, synonyms, and minor spelling mistakes far
    better than simple string matching. If the API call fails, times out, or
    returns something that can't be parsed as valid grading JSON, this
    silently falls back to the local word-overlap heuristic in
    Backend.parser.check_answer().

    This function NEVER raises and ALWAYS returns a usable dict:

        {
            "verdict": "correct" | "partial" | "incorrect" | "empty",
            "feedback": str,
            "source": "ai" | "heuristic",
        }
    """
    if not (user_answer or "").strip():
        return {
            "verdict": "empty",
            "feedback": _FALLBACK_FEEDBACK["empty"],
            "source": "heuristic",
        }

    prompt = build_grading_prompt(question, correct_answer, user_answer)
    success, content = _call_openrouter(prompt)

    if success:
        parsed = _parse_grading_response(content)
        if parsed is not None:
            return {**parsed, "source": "ai"}

    # Fallback: local heuristic (no network dependency, always available)
    verdict, _score = check_answer(user_answer, correct_answer)
    return {
        "verdict": verdict,
        "feedback": _FALLBACK_FEEDBACK.get(verdict, _FALLBACK_FEEDBACK["incorrect"]),
        "source": "heuristic",
    }


# ---------------------------------------------------------------------------
# Streaming helper
# ---------------------------------------------------------------------------

def _stream_openrouter(prompt: str, max_tokens: int = 1024):
    """
    Low-level streaming call to OpenRouter using SSE (Server-Sent Events).
    Yields text chunks as they arrive, for use with st.write_stream().

    OpenRouter follows the OpenAI SSE spec:
      - Each chunk is a line: "data: {json}"
      - The content delta is in choices[0].delta.content
      - The stream ends with: "data: [DONE]"

    Yields:
        str chunks on success.
        Raises RuntimeError with a user-friendly message on failure.
    """
    if not API_KEY:
        raise RuntimeError("Missing API key. Set OPENROUTER_API_KEY.")

    try:
        response = requests.post(
            url=OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": MODEL_NAME,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "stream": True,
            },
            timeout=REQUEST_TIMEOUT,
            stream=True,
        )
    except requests.exceptions.Timeout:
        raise RuntimeError("The request timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Could not connect to the AI service.")
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Network error: {exc}")

    if response.status_code != 200:
        raise RuntimeError(f"AI service error (status {response.status_code}).")

    for line in response.iter_lines():
        if not line:
            continue
        # Each line is b"data: {json}" or b"data: [DONE]"
        decoded = line.decode("utf-8", errors="replace")
        if not decoded.startswith("data:"):
            continue
        payload = decoded[5:].strip()
        if payload == "[DONE]":
            break
        try:
            chunk = json.loads(payload)
            delta = chunk["choices"][0]["delta"].get("content", "")
            if delta:
                yield delta
        except (json.JSONDecodeError, KeyError, IndexError):
            continue


# ---------------------------------------------------------------------------
# Compare Mode
# ---------------------------------------------------------------------------

def generate_compare_material(topic_a: str, topic_b: str,
                               difficulty: str = DEFAULT_DIFFICULTY):
    """
    Generate a structured comparison of two topics.

    Returns:
        (True, compare_dict)   on success -- dict from parse_compare_material()
        (False, error_message) on any failure
    """
    topic_a = (topic_a or "").strip()
    topic_b = (topic_b or "").strip()

    if not topic_a or not topic_b:
        return False, "Please enter both topics to compare."

    prompt = build_compare_prompt(topic_a, topic_b, difficulty)
    success, content = _call_openrouter(prompt)

    if not success:
        return False, content

    return True, parse_compare_material(content, topic_a, topic_b)


# ---------------------------------------------------------------------------
# Auto-difficulty detection
# ---------------------------------------------------------------------------

def detect_difficulty(topic: str) -> str:
    """
    Ask the model to classify the natural difficulty level of a topic.
    Returns one of "Beginner", "Intermediate", "Advanced".
    Falls back to "Intermediate" on any failure -- never raises.

    This is a cheap, fast call (single-word response) designed to be
    fired as the user types, to pre-select the difficulty dropdown.
    """
    from backend.prompts import DIFFICULTY_LEVELS

    topic = (topic or "").strip()
    if not topic:
        return DEFAULT_DIFFICULTY

    prompt = build_auto_difficulty_prompt(topic)
    success, content = _call_openrouter(prompt)

    if not success:
        return DEFAULT_DIFFICULTY

    # The model should return exactly one word. Find it.
    content = (content or "").strip()
    for level in DIFFICULTY_LEVELS:
        if level.lower() in content.lower():
            return level

    return DEFAULT_DIFFICULTY


# ---------------------------------------------------------------------------
# Follow-up questions (streaming)
# ---------------------------------------------------------------------------

def stream_followup_answer(topic: str, section_content: str, question: str):
    """
    Stream a focused answer to the user's follow-up question about the
    current topic. Designed for use with st.write_stream().

    Yields str chunks. Raises RuntimeError on failure (caller should
    catch and display an error message).

    Uses a smaller max_tokens (512) since follow-up answers should be
    concise -- not a full study material regeneration.
    """
    prompt = build_followup_prompt(topic, section_content, question)
    yield from _stream_openrouter(prompt, max_tokens=512)


# ---------------------------------------------------------------------------
# Study schedule / spaced repetition
# ---------------------------------------------------------------------------

def get_study_suggestions(history: list) -> list:
    """
    Given the user's search history, return a list of topics the model
    suggests reviewing today (spaced repetition).

    Returns a list of {"topic": str, "reason": str} dicts (2-3 items).
    Returns [] on failure or if history is empty -- never raises.
    """
    if not history:
        return []

    prompt = build_study_schedule_prompt(history)
    if not prompt:
        return []

    success, content = _call_openrouter(prompt)

    if not success:
        return []

    return parse_study_schedule(content)


# ---------------------------------------------------------------------------
# Voice-to-topic (audio transcription via OpenRouter Whisper)
# ---------------------------------------------------------------------------

WHISPER_URL = "https://openrouter.ai/api/v1/audio/transcriptions"
WHISPER_MODEL = "openai/whisper-large-v3"
AUDIO_TIMEOUT = 30  # seconds -- audio files are small, 30s is generous


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> tuple:
    """
    Transcribe speech audio to text using OpenRouter's Whisper endpoint.

    `audio_bytes` is the raw audio file content (WAV, MP3, WebM, etc.)
    `filename` is used to set the MIME type hint for the API.

    Returns:
        (True, transcribed_text)   on success
        (False, error_message)     on any failure

    The returned text is trimmed and ready to use as a topic input.
    """
    if not API_KEY:
        return False, "Missing API key."

    if not audio_bytes:
        return False, "No audio data received."

    try:
        response = requests.post(
            url=WHISPER_URL,
            headers={"Authorization": f"Bearer {API_KEY}"},
            files={"file": (filename, audio_bytes, "audio/wav")},
            data={"model": WHISPER_MODEL},
            timeout=AUDIO_TIMEOUT,
        )
    except requests.exceptions.Timeout:
        return False, "Audio transcription timed out. Please try again."
    except requests.exceptions.RequestException as exc:
        return False, f"Network error during transcription: {exc}"

    if response.status_code == 404:
        return False, "Voice transcription not available on this plan."
    if response.status_code == 429:
        return False, "Rate limit reached. Please wait a moment."
    if response.status_code != 200:
        return False, f"Transcription error (status {response.status_code})."

    try:
        result = response.json()
        text = (result.get("text") or "").strip()
    except (ValueError, AttributeError):
        return False, "Could not parse transcription response."

    if not text:
        return False, "No speech detected in the audio. Please try again."

    return True, text