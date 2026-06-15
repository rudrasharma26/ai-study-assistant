"""
utils/storage.py

Handles persistence of:
- Username (per-device)
- Search History (per-device)
- Favorites (per-device)
- A developer-facing usage log (name + topic + timestamp), sent to a
  Google Form so the developer can review usage across all devices.

PER-DEVICE STORAGE -- HOW IT WORKS
-----------------------------------
Earlier versions of this app tried to use browser cookies (via
streamlit-local-storage / extra-streamlit-components) for per-device
persistence. Both libraries rely on an async `declare_component` round
trip to read the browser's cookie jar, which on Streamlit Cloud
intermittently returned an incomplete/empty cookie set on page load --
causing usernames, history, and favorites to randomly "reset".

This version replaces that entirely with a simple, fully synchronous
approach:

1. Each browser gets a random `device` ID, stored in the page's URL via
   `st.query_params`. Reading/writing query params is synchronous and
   built into Streamlit core -- no component round trip, no race
   conditions.
2. All per-device data (username, history, favorites) is stored
   server-side in a single JSON file (data/devices.json), keyed by that
   device ID:

       {
         "<device_id>": {
             "username": "Rudra",
             "history":   [ {"topic", "difficulty", "study_mode"}, ... ],
             "favorites": [ {"topic", "difficulty", "study_mode"}, ... ]
         },
         ...
       }

KNOWN TRADEOFF (free hosting, no database)
-------------------------------------------
On Streamlit Community Cloud, the filesystem is ephemeral: data/devices.json
persists while the app instance is running, but is WIPED on every reboot
or redeploy. This means a redeploy resets everyone's saved name/history/
favorites back to "new device" (they'll be asked for their name again).
This is an accepted tradeoff for a free-tier deployment with no external
database. If this becomes annoying, the fix is to point this file's
read/write functions at an external store (e.g. a free-tier hosted
Postgres/SQLite-over-HTTP service) -- the function signatures below
wouldn't need to change.

DEVELOPER USAGE LOG
--------------------
Every time a user generates study material, `log_event(name, topic)` is
called. This fires a best-effort POST to a Google Form's `/formResponse`
endpoint, which appends a row (name, topic, timestamp-by-Forms) to a
linked Google Sheet that only the developer can see. This is unaffected
by the storage rewrite above and survives reboots (it's external).

This is fire-and-forget:
- Wrapped in try/except -- a network hiccup or blocked request NEVER
  breaks the app or the user's experience.
- Short timeout so it can't noticeably delay the UI.
- The user is never shown this data and it does not affect their
  local history/favorites in any way.
"""

import os
import json
import uuid
import requests
import streamlit as st


# ---------------------------------------------------------------------------
# Device-data file (per-device username/history/favorites)
# ---------------------------------------------------------------------------
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA_DIR = os.path.join(_BASE_DIR, "data")
_DEVICES_FILE = os.path.join(_DATA_DIR, "devices.json")

MAX_HISTORY_ITEMS = 10

_DEFAULT_DEVICE = {"username": "", "history": [], "favorites": []}


def _ensure_data_file() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)
    if not os.path.exists(_DEVICES_FILE):
        _write_all({})


def _read_all() -> dict:
    """
    Load data/devices.json. Returns {} if the file is missing,
    unreadable, or corrupted -- never raises.
    """
    _ensure_data_file()
    try:
        with open(_DEVICES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}
    return data


def _write_all(data: dict) -> bool:
    """
    Write data to data/devices.json atomically (write to a temp file,
    then replace) so a crash mid-write can't corrupt the file. Returns
    True on success, False otherwise -- never raises.
    """
    os.makedirs(_DATA_DIR, exist_ok=True)
    tmp_path = _DEVICES_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, _DEVICES_FILE)
        return True
    except OSError:
        return False


def _get_device_record(device_id: str) -> dict:
    """Return this device's record, backfilled with defaults."""
    all_data = _read_all()
    record = all_data.get(device_id, {})
    if not isinstance(record, dict):
        record = {}

    record.setdefault("username", "")
    record.setdefault("history", [])
    record.setdefault("favorites", [])

    if not isinstance(record["history"], list):
        record["history"] = []
    if not isinstance(record["favorites"], list):
        record["favorites"] = []
    if not isinstance(record["username"], str):
        record["username"] = ""

    return record


def _save_device_record(device_id: str, record: dict) -> None:
    all_data = _read_all()
    all_data[device_id] = record
    _write_all(all_data)


# ---------------------------------------------------------------------------
# Device ID (via URL query params -- synchronous, no component round trip)
# ---------------------------------------------------------------------------

def init_storage() -> str:
    """
    Ensure this browser/tab has a `device` ID in the URL's query params,
    creating one (and storing an empty record for it) if needed.

    Must be called once near the top of app.py, before any of the
    get_*/set_* helpers below. Returns the device ID, and also caches it
    in st.session_state for fast access within this session.
    """
    if "_device_id" in st.session_state:
        return st.session_state._device_id

    device_id = st.query_params.get("device")

    if not device_id:
        device_id = uuid.uuid4().hex
        st.query_params["device"] = device_id

        # Make sure a record exists for this brand-new device so later
        # reads don't have to special-case "not yet in the file".
        all_data = _read_all()
        if device_id not in all_data:
            all_data[device_id] = dict(_DEFAULT_DEVICE)
            _write_all(all_data)

    st.session_state._device_id = device_id
    return device_id


def _device_id() -> str:
    return st.session_state._device_id


# ---------------------------------------------------------------------------
# Developer usage log (Google Form webhook)
# ---------------------------------------------------------------------------
# Replace these with your own Form's action URL + entry IDs.
_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdta0n2805kNlOtWE9AAnVQntiTBz16DMutH5rdAY2FXvGbvA/formResponse"
_FORM_ENTRY_NAME = "entry.427107502"
_FORM_ENTRY_TOPIC = "entry.1511327583"
_LOG_TIMEOUT = 3  # seconds


def log_event(name: str, topic: str) -> None:
    """
    Best-effort log of a search event to the developer's Google Form.

    Never raises and never blocks the UI for long -- any failure
    (network error, timeout, blocked domain, etc.) is silently ignored.
    """
    try:
        requests.post(
            _FORM_URL,
            data={
                _FORM_ENTRY_NAME: (name or "").strip(),
                _FORM_ENTRY_TOPIC: (topic or "").strip(),
            },
            timeout=_LOG_TIMEOUT,
        )
    except requests.exceptions.RequestException:
        pass


# ---------------------------------------------------------------------------
# Username (per-device onboarding)
# ---------------------------------------------------------------------------

def get_username() -> str:
    """Return the saved username for this device, or "" if not set yet."""
    record = _get_device_record(_device_id())
    return record.get("username", "")


def set_username(name: str) -> None:
    """Save the username for this device (persists until app reboot)."""
    name = (name or "").strip()
    if not name:
        return
    record = _get_device_record(_device_id())
    record["username"] = name
    _save_device_record(_device_id(), record)


# ---------------------------------------------------------------------------
# History (per-device)
# ---------------------------------------------------------------------------

def get_history() -> list:
    """Return this device's search history, most-recent-first."""
    record = _get_device_record(_device_id())
    return record.get("history", [])


def add_to_history(topic: str, difficulty: str, study_mode: str) -> None:
    """
    Add/move `topic` to the front of this device's history.
    De-duplicated case-insensitively, capped at MAX_HISTORY_ITEMS.
    """
    record = _get_device_record(_device_id())
    history = record.get("history", [])

    history = [
        item for item in history
        if (item.get("topic") or "").strip().lower() != topic.strip().lower()
    ]

    history.insert(0, {
        "topic": topic,
        "difficulty": difficulty,
        "study_mode": study_mode,
    })

    record["history"] = history[:MAX_HISTORY_ITEMS]
    _save_device_record(_device_id(), record)


def clear_history() -> None:
    """Clear this device's search history."""
    record = _get_device_record(_device_id())
    record["history"] = []
    _save_device_record(_device_id(), record)


# ---------------------------------------------------------------------------
# Favorites (per-device)
# ---------------------------------------------------------------------------

def get_favorites() -> list:
    """Return this device's favorites."""
    record = _get_device_record(_device_id())
    return record.get("favorites", [])


def is_favorite(topic: str) -> bool:
    topic = (topic or "").strip().lower()
    return any(
        (item.get("topic") or "").strip().lower() == topic
        for item in get_favorites()
    )


def toggle_favorite(topic: str, difficulty: str, study_mode: str) -> None:
    """Add `topic` to favorites if absent, remove it if present."""
    record = _get_device_record(_device_id())
    favorites = record.get("favorites", [])
    topic_norm = (topic or "").strip().lower()

    existing = next(
        (item for item in favorites if (item.get("topic") or "").strip().lower() == topic_norm),
        None,
    )

    if existing:
        favorites = [item for item in favorites if item is not existing]
    else:
        favorites.append({
            "topic": topic,
            "difficulty": difficulty,
            "study_mode": study_mode,
        })

    record["favorites"] = favorites
    _save_device_record(_device_id(), record)


def remove_favorite(topic: str) -> None:
    """Remove a topic from favorites, if present."""
    topic_norm = (topic or "").strip().lower()
    if not topic_norm:
        return
    record = _get_device_record(_device_id())
    record["favorites"] = [
        item for item in record.get("favorites", [])
        if (item.get("topic") or "").strip().lower() != topic_norm
    ]
    _save_device_record(_device_id(), record)


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
