"""
utils/storage.py

Handles all per-user persistence and developer logging for the AI Study
Assistant.

AUTHENTICATION
--------------
Uses Streamlit's built-in st.login() / st.logout() / st.user (available
since Streamlit 1.40+). The app requires Google login -- no anonymous
access. After login, st.user.email is the stable, permanent identifier
for each user. No more random device UUIDs or ?device= query params.

STORAGE BACKEND: SUPABASE
--------------------------
All per-user data (username, history, favourites, streak) is stored in a
Supabase Postgres table called `devices`, keyed by the user's email:

    user_id      TEXT  PRIMARY KEY   -- the user's Google email
    username     TEXT                -- display name (from Google or custom)
    history      JSONB               -- list of {topic, difficulty, study_mode}
    favourites   JSONB               -- list of {topic, difficulty, study_mode}
    streak_count INT4                -- consecutive daily study streak
    last_active  TEXT                -- ISO date string of last activity

Supabase persists forever (survives reboots and redeploys), unlike the old
data/devices.json filesystem approach which reset on every redeploy.

All Supabase calls are wrapped in try/except -- a database hiccup never
crashes the app. Falls back to safe empty defaults if the DB is unreachable.

DEVELOPER USAGE LOG
-------------------
Every successful generation fires a best-effort POST to a Google Form,
appending a row (name, topic, timestamp) to a linked Google Sheet.
Wrapped in try/except -- never blocks the UI.
"""

import os
import json
import datetime
import requests
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Supabase client (lazy singleton cached in session_state)
# ---------------------------------------------------------------------------

_TABLE = "devices"
MAX_HISTORY_ITEMS = 10


def _supabase() -> Client:
    """
    Return a cached Supabase client. Created once per session, then reused.
    Reads credentials from st.secrets (deployed) with fallback to .env (local).
    """
    if "_supabase_client" not in st.session_state:
        url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY", "")
        if not url or not key:
            st.error("Supabase credentials missing. Check your secrets / .env file.")
            st.stop()
        st.session_state._supabase_client = create_client(url, key)
    return st.session_state._supabase_client


# ---------------------------------------------------------------------------
# Low-level DB helpers
# ---------------------------------------------------------------------------

def _get_record(user_id: str) -> dict:
    """
    Fetch this user's row from Supabase. Returns a dict with all fields
    backfilled to safe defaults if the row doesn't exist or DB is down.
    Never raises.
    """
    defaults = {
        "user_id": user_id,
        "username": "",
        "history": [],
        "favourites": [],
        "streak_count": 0,
        "last_active": "",
    }
    try:
        resp = (
            _supabase()
            .table(_TABLE)
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        if resp.data:
            row = resp.data[0]
            # Supabase returns JSONB as Python objects already -- no need to
            # json.loads(). But defensively coerce if they somehow come back
            # as strings.
            for field in ("history", "favourites"):
                if isinstance(row.get(field), str):
                    try:
                        row[field] = json.loads(row[field])
                    except (ValueError, TypeError):
                        row[field] = []
            defaults.update(row)
    except Exception:
        pass
    return defaults


def _save_record(record: dict) -> None:
    """
    Upsert this user's record to Supabase. Never raises -- a DB failure
    is silently swallowed so the app keeps working.
    """
    try:
        _supabase().table(_TABLE).upsert(record).execute()
    except Exception:
        pass


def _user_id() -> str:
    """Return the current logged-in user's email (our stable user identifier)."""
    return st.session_state._user_id


# ---------------------------------------------------------------------------
# Authentication (Google login via Streamlit's built-in auth)
# ---------------------------------------------------------------------------

def init_auth() -> bool:
    """
    Call this at the very top of app.py (after set_page_config).

    - If the user is not logged in: show a login page and return False.
      The caller should call st.stop() immediately after.
    - If the user IS logged in: populate session state with user info,
      initialize their Supabase record if needed, update streak, and
      return True.

    Uses Streamlit's built-in st.login() / st.user which reads from
    st.secrets[auth] and st.secrets[auth.google].
    """
    # Already initialized this session -- fast path.
    if st.session_state.get("_auth_done"):
        return True

    user = st.user

    if not user.is_logged_in:
        return False

    # User is logged in -- populate session state.
    email = user.email
    st.session_state._user_id = email

    # Load or create their Supabase record.
    record = _get_record(email)

    # Use Google display name as default username if not set yet.
    if not record.get("username"):
        record["username"] = user.name or email.split("@")[0]

    # Update streak.
    record = _update_streak(record)

    # Save back (covers both new-user creation and streak update).
    _save_record(record)

    # Cache username in session_state for fast access.
    st.session_state._username = record["username"]
    st.session_state._auth_done = True

    return True


def render_login_page() -> None:
    """
    Render a clean, minimal login page. Called from app.py when
    init_auth() returns False.
    """
    st.markdown(
        """
        <style>
        .login-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 70vh;
            gap: 1.5rem;
        }
        .login-title {
            font-size: 2.4rem;
            font-weight: 800;
            background: linear-gradient(135deg, #93C5FD, #A78BFA, #F0ABFC);
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            text-align: center;
        }
        .login-subtitle {
            color: rgba(255,255,255,0.6);
            font-size: 1.05rem;
            text-align: center;
        }
        </style>
        <div class="login-wrapper">
            <div class="login-title">🧠 AI Study Assistant</div>
            <div class="login-subtitle">
                Your intelligent companion for learning anything, anytime.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        st.login("google")


def render_logout_button() -> None:
    """Render a small logout button (call from the sidebar)."""
    if st.button("🚪 Logout", key="logout_btn", use_container_width=True):
        st.logout()


# ---------------------------------------------------------------------------
# Streak tracking
# ---------------------------------------------------------------------------

def _update_streak(record: dict) -> dict:
    """
    Update the streak_count and last_active fields.

    Rules:
    - If last_active is today: streak unchanged (already counted today).
    - If last_active was yesterday: streak += 1 (kept it going).
    - Anything older (or empty): streak resets to 1 (new streak started).
    """
    today = datetime.date.today().isoformat()
    yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    last = record.get("last_active", "")

    if last == today:
        pass  # Already updated today, don't touch streak
    elif last == yesterday:
        record["streak_count"] = (record.get("streak_count") or 0) + 1
        record["last_active"] = today
    else:
        record["streak_count"] = 1
        record["last_active"] = today

    return record


def get_streak() -> int:
    """Return the current user's study streak count."""
    record = _get_record(_user_id())
    return record.get("streak_count", 0)


# ---------------------------------------------------------------------------
# Developer usage log (Google Form webhook)
# ---------------------------------------------------------------------------

_FORM_URL = "https://docs.google.com/forms/d/e/1FAIpQLSdta0n2805kNlOtWE9AAnVQntiTBz16DMutH5rdAY2FXvGbvA/formResponse"
_FORM_ENTRY_NAME = "entry.427107502"
_FORM_ENTRY_TOPIC = "entry.1511327583"
_LOG_TIMEOUT = 3


def log_event(name: str, topic: str) -> None:
    """
    Best-effort POST to the developer's Google Form. Never raises.
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
# Username
# ---------------------------------------------------------------------------

def get_username() -> str:
    """Return the cached username for the current session."""
    return st.session_state.get("_username", "")


def set_username(name: str) -> None:
    """Update the display name for this user (persists to Supabase)."""
    name = (name or "").strip()
    if not name:
        return
    st.session_state._username = name
    record = _get_record(_user_id())
    record["username"] = name
    _save_record(record)


# ---------------------------------------------------------------------------
# History (per-user)
# ---------------------------------------------------------------------------

def get_history() -> list:
    """Return this user's search history, most-recent-first."""
    return _get_record(_user_id()).get("history", [])


def add_to_history(topic: str, difficulty: str, study_mode: str) -> None:
    """
    Add/move `topic` to the front of this user's history.
    De-duplicated case-insensitively, capped at MAX_HISTORY_ITEMS.
    """
    record = _get_record(_user_id())
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
    _save_record(record)


def clear_history() -> None:
    """Clear this user's search history."""
    record = _get_record(_user_id())
    record["history"] = []
    _save_record(record)


# ---------------------------------------------------------------------------
# Favourites (per-user)
# ---------------------------------------------------------------------------

def get_favorites() -> list:
    """Return this user's favourites."""
    return _get_record(_user_id()).get("favourites", [])


def is_favorite(topic: str) -> bool:
    topic_norm = (topic or "").strip().lower()
    return any(
        (item.get("topic") or "").strip().lower() == topic_norm
        for item in get_favorites()
    )


def toggle_favorite(topic: str, difficulty: str, study_mode: str) -> None:
    """Add `topic` to favourites if absent, remove it if present."""
    record = _get_record(_user_id())
    favourites = record.get("favourites", [])
    topic_norm = (topic or "").strip().lower()

    existing = next(
        (item for item in favourites
         if (item.get("topic") or "").strip().lower() == topic_norm),
        None,
    )

    if existing:
        favourites = [item for item in favourites if item is not existing]
    else:
        favourites.append({
            "topic": topic,
            "difficulty": difficulty,
            "study_mode": study_mode,
        })

    record["favourites"] = favourites
    _save_record(record)


def remove_favorite(topic: str) -> None:
    """Remove a topic from favourites, if present."""
    topic_norm = (topic or "").strip().lower()
    if not topic_norm:
        return
    record = _get_record(_user_id())
    record["favourites"] = [
        item for item in record.get("favourites", [])
        if (item.get("topic") or "").strip().lower() != topic_norm
    ]
    _save_record(record)


