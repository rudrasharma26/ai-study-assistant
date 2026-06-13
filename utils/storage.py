"""
utils/storage.py

Handles persistence of:
- Search History
- Favorites
- Username (for the onboarding / welcome flow)

All of this is stored in a single local JSON file (data/history.json), so it
survives an app restart.

This module is intentionally Streamlit-free -- it just reads/writes a JSON
file and returns plain Python dicts/lists/strings. app.py calls these
functions directly and/or keeps a copy in st.session_state for fast access
within a session.

Data shape (data/history.json):
{
    "history":   [ {"topic", "difficulty", "study_mode", "timestamp"}, ... ],
    "favorites": [ {"topic", "difficulty", "study_mode", "timestamp"}, ... ],
    "username":  "Some Name"
}

History is ordered most-recent-first and capped at MAX_HISTORY_ITEMS.
Topics are de-duplicated case-insensitively -- re-searching a topic moves it
back to the top instead of creating a duplicate entry.
"""

import os
import json
from datetime import datetime

# Project-root-relative data directory.
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_DATA_FILE = os.path.join(_DATA_DIR, "history.json")

MAX_HISTORY_ITEMS = 15

_DEFAULT_DATA = {"history": [], "favorites": [], "username": ""}


# ---------------------------------------------------------------------------
# Low-level load/save
# ---------------------------------------------------------------------------

def _ensure_data_file():
    """Create data/history.json with default content if it doesn't exist."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_DATA_FILE):
        _write_data(dict(_DEFAULT_DATA))


def _read_data() -> dict:
    """
    Load data/history.json. Returns a default empty structure if the file
    is missing, unreadable, or corrupted -- never raises.

    Any missing keys (e.g. an older history.json without "username") are
    backfilled with defaults, so the rest of the app can always rely on
    "history", "favorites", and "username" being present.
    """
    _ensure_data_file()
    try:
        with open(_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return dict(_DEFAULT_DATA)

    if not isinstance(data, dict):
        return dict(_DEFAULT_DATA)

    data.setdefault("history", [])
    data.setdefault("favorites", [])
    data.setdefault("username", "")

    if not isinstance(data["history"], list):
        data["history"] = []
    if not isinstance(data["favorites"], list):
        data["favorites"] = []
    if not isinstance(data["username"], str):
        data["username"] = ""

    return data


def _write_data(data: dict) -> bool:
    """Write data to data/history.json. Returns True on success."""
    os.makedirs(_DATA_DIR, exist_ok=True)
    try:
        with open(_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def get_history() -> list:
    """Return the history list, most-recent-first."""
    return _read_data()["history"]


def add_to_history(topic: str, difficulty: str, study_mode: str) -> list:
    """
    Add (or move-to-top) a topic in history.

    If a topic with the same name (case-insensitive) already exists, it is
    removed first, so re-searching a topic refreshes its position and
    difficulty/mode instead of creating a duplicate entry.

    Returns the updated history list.
    """
    topic = (topic or "").strip()
    if not topic:
        return get_history()

    data = _read_data()
    history = data["history"]

    history = [
        item for item in history
        if item.get("topic", "").strip().lower() != topic.lower()
    ]

    history.insert(0, {
        "topic": topic,
        "difficulty": difficulty,
        "study_mode": study_mode,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })

    history = history[:MAX_HISTORY_ITEMS]

    data["history"] = history
    _write_data(data)
    return history


def clear_history() -> None:
    """Remove all history entries (favorites and username are untouched)."""
    data = _read_data()
    data["history"] = []
    _write_data(data)


# ---------------------------------------------------------------------------
# Favorites
# ---------------------------------------------------------------------------

def get_favorites() -> list:
    """Return the favorites list."""
    return _read_data()["favorites"]


def is_favorite(topic: str) -> bool:
    """Check whether a topic (case-insensitive) is in favorites."""
    topic = (topic or "").strip().lower()
    if not topic:
        return False
    return any(
        item.get("topic", "").strip().lower() == topic
        for item in get_favorites()
    )


def toggle_favorite(topic: str, difficulty: str = "", study_mode: str = "") -> bool:
    """
    Add the topic to favorites if it's not already there, or remove it if
    it is (a toggle).

    Returns True if the topic IS a favorite after this call, False if it
    was removed.
    """
    topic = (topic or "").strip()
    if not topic:
        return False

    data = _read_data()
    favorites = data["favorites"]
    normalized = topic.lower()

    existing = [
        item for item in favorites
        if item.get("topic", "").strip().lower() == normalized
    ]

    if existing:
        favorites = [
            item for item in favorites
            if item.get("topic", "").strip().lower() != normalized
        ]
        data["favorites"] = favorites
        _write_data(data)
        return False

    favorites.insert(0, {
        "topic": topic,
        "difficulty": difficulty,
        "study_mode": study_mode,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
    })
    data["favorites"] = favorites
    _write_data(data)
    return True


def remove_favorite(topic: str) -> None:
    """Remove a topic from favorites, if present."""
    topic = (topic or "").strip().lower()
    if not topic:
        return
    data = _read_data()
    data["favorites"] = [
        item for item in data["favorites"]
        if item.get("topic", "").strip().lower() != topic
    ]
    _write_data(data)


# ---------------------------------------------------------------------------
# Username (onboarding / welcome flow)
# ---------------------------------------------------------------------------









# ---------------------------------------------------------------------------
# Secret personalization mode
# ---------------------------------------------------------------------------

# Names that trigger the special personalized greeting/reveal screen.
# Stored normalized (lowercase, single-spaced) for robust matching.
_SPECIAL_NAMES = {
    "kavya",
    "kavyaa",
    "kavya sharma",
    "bubu",
    "bulbul",
}


def _normalize_name(name: str) -> str:
    """Lowercase, strip, and collapse internal whitespace for comparison."""
    return " ".join((name or "").strip().lower().split())


def is_bhabhi_mode(name: str) -> bool:
    """
    Return True if `name` matches one of the special-recognition names
    (case-insensitive, whitespace-tolerant).

    This check is intentionally an exact match against a small fixed list
    after normalization -- it will NOT match unrelated names, substrings,
    or partial matches, so it can never trigger by accident.
    """
    return _normalize_name(name) in _SPECIAL_NAMES