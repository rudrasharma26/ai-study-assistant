"""
utils/storage.py

Handles persistence of:
- Username (per-device, via browser cookies)
- Search History (per-device, via browser cookies)
- Favorites (per-device, via browser cookies)
- A developer-facing usage log (name + topic + timestamp), sent to a
  Google Form so the developer can review usage across all devices.

PER-DEVICE STORAGE
------------------
Username, history, and favorites are stored as browser cookies via
`extra_streamlit_components.CookieManager`. This means:

- Each browser/device has its own independent name, history, and
  favorites.
- Data persists across page reloads and future visits on the same
  browser (cookies are set with a long expiry -- see _COOKIE_EXPIRY_DAYS)
  until the user clears site data.
- A different person on a different device (or a different browser /
  incognito session) gets their own onboarding prompt and their own
  history -- nothing is shared between devices.

app.py should call `init_storage()` once near the top of the script
(after st.set_page_config), then use the helpers below.

DEVELOPER USAGE LOG
--------------------
Every time a user generates study material, `log_event(name, topic)` is
called. This fires a best-effort POST to a Google Form's `/formResponse`
endpoint, which appends a row (name, topic, timestamp-by-Forms) to a
linked Google Sheet that only the developer can see.

This is fire-and-forget:
- Wrapped in try/except -- a network hiccup or blocked request NEVER
  breaks the app or the user's experience.
- Short timeout so it can't noticeably delay the UI.
- The user is never shown this data and it does not affect their
  local history/favorites in any way.
"""

import json
import datetime
import requests
import streamlit as st
import extra_streamlit_components as stx


# ---------------------------------------------------------------------------
# Cookie keys
# ---------------------------------------------------------------------------
CK_USERNAME = "study_assistant_username"
CK_HISTORY = "study_assistant_history"
CK_FAVORITES = "study_assistant_favorites"
CK_CACHE = "study_assistant_cache"

MAX_HISTORY_ITEMS = 10

# How many full generated results to keep cached per device. Kept small
# because each cached entry stores the full raw AI response text, and
# cookies have a practical size limit (~4KB).
MAX_CACHE_ITEMS = 2

# How long these cookies last (persists across visits on the same browser).
_COOKIE_EXPIRY_DAYS = 365


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
# Cookie manager setup
# ---------------------------------------------------------------------------

def init_storage() -> "stx.CookieManager":
    """
    Initialize (or fetch) the CookieManager for this session.

    Must be called once near the top of app.py, before any of the
    get_*/set_* helpers below.

    NOTE: declare_component-based components (like CookieManager) return
    a `default` value on their first render and only return the real
    value (here, the actual browser cookies) after the frontend responds
    and the script reruns. So: keep re-invoking CookieManager(key=...)
    with the SAME key on each rerun until it returns a non-empty cookie
    jar (or we've already confirmed cookies are loaded), THEN cache it.
    Re-invoking with the same key is cheap -- Streamlit reuses the same
    component instance.
    """
    if st.session_state.get("_cookies_loaded"):
        if "_cookie_manager" not in st.session_state:
            st.session_state._cookie_manager = stx.CookieManager(key="study_assistant_cookies")
        return st.session_state._cookie_manager

    manager = stx.CookieManager(key="study_assistant_cookies")
    if manager.cookies:
        st.session_state._cookies_loaded = True
    st.session_state._cookie_manager = manager
    return manager


def _cm() -> "stx.CookieManager":
    return st.session_state._cookie_manager


def _expiry():
    return datetime.datetime.now() + datetime.timedelta(days=_COOKIE_EXPIRY_DAYS)


def _get_json(cookie_key: str, default):
    """Read a JSON-encoded value from cookies, with a safe default."""
    raw = _cm().get(cookie_key)
    if raw is None or raw == "":
        return default
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return default


def _set_json(cookie_key: str, value, set_key: str) -> None:
    """Write a JSON-encoded value to a cookie."""
    _cm().set(
        cookie_key,
        json.dumps(value),
        key=set_key,
        expires_at=_expiry(),
    )


# ---------------------------------------------------------------------------
# Username (per-device onboarding)
# ---------------------------------------------------------------------------

def get_username() -> str:
    """Return the saved username for this device, or "" if not set yet."""
    value = _cm().get(CK_USERNAME)
    return value or ""


def set_username(name: str) -> None:
    """Save the username for this device (persists across visits)."""
    name = (name or "").strip()
    if not name:
        return
    _cm().set(CK_USERNAME, name, key="set_username", expires_at=_expiry())


# ---------------------------------------------------------------------------
# History (per-device)
# ---------------------------------------------------------------------------

def get_history() -> list:
    """Return this device's search history, most-recent-first."""
    return _get_json(CK_HISTORY, [])


def add_to_history(topic: str, difficulty: str, study_mode: str) -> None:
    """
    Add/move `topic` to the front of this device's history.
    De-duplicated case-insensitively, capped at MAX_HISTORY_ITEMS.
    """
    history = get_history()

    history = [
        item for item in history
        if (item.get("topic") or "").strip().lower() != topic.strip().lower()
    ]

    history.insert(0, {
        "topic": topic,
        "difficulty": difficulty,
        "study_mode": study_mode,
    })

    history = history[:MAX_HISTORY_ITEMS]
    _set_json(CK_HISTORY, history, set_key="set_history")


def clear_history() -> None:
    """Clear this device's search history."""
    _set_json(CK_HISTORY, [], set_key="clear_history")


# ---------------------------------------------------------------------------
# Result cache (per-device)
# ---------------------------------------------------------------------------
# Avoids re-calling the AI API for a topic/difficulty/study_mode
# combination that was already generated recently on this device.
# Stores the raw AI response text so it can be re-parsed exactly as if
# it had just come back from the API.

def _cache_key(topic: str, difficulty: str, study_mode: str) -> str:
    return f"{(topic or '').strip().lower()}|{difficulty}|{study_mode}"


def get_cached_result(topic: str, difficulty: str, study_mode: str):
    """
    Return the cached raw AI response text for this exact
    topic/difficulty/study_mode combination, or None if not cached.
    """
    cache = _get_json(CK_CACHE, [])
    key = _cache_key(topic, difficulty, study_mode)
    for entry in cache:
        if entry.get("key") == key:
            return entry.get("raw")
    return None


def cache_result(topic: str, difficulty: str, study_mode: str, raw: str) -> None:
    """
    Save a generated result to this device's cache, most-recent-first,
    capped at MAX_CACHE_ITEMS.
    """
    cache = _get_json(CK_CACHE, [])
    key = _cache_key(topic, difficulty, study_mode)

    cache = [entry for entry in cache if entry.get("key") != key]
    cache.insert(0, {"key": key, "raw": raw})
    cache = cache[:MAX_CACHE_ITEMS]

    _set_json(CK_CACHE, cache, set_key="set_cache")


# ---------------------------------------------------------------------------
# Favorites (per-device)
# ---------------------------------------------------------------------------

def get_favorites() -> list:
    """Return this device's favorites."""
    return _get_json(CK_FAVORITES, [])


def is_favorite(topic: str) -> bool:
    topic = (topic or "").strip().lower()
    return any(
        (item.get("topic") or "").strip().lower() == topic
        for item in get_favorites()
    )


def toggle_favorite(topic: str, difficulty: str, study_mode: str) -> None:
    """Add `topic` to favorites if absent, remove it if present."""
    favorites = get_favorites()
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

    _set_json(CK_FAVORITES, favorites, set_key="set_favorites")


def remove_favorite(topic: str) -> None:
    """Remove a topic from favorites, if present."""
    topic_norm = (topic or "").strip().lower()
    if not topic_norm:
        return
    favorites = [
        item for item in get_favorites()
        if (item.get("topic") or "").strip().lower() != topic_norm
    ]
    _set_json(CK_FAVORITES, favorites, set_key="remove_favorite")


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
