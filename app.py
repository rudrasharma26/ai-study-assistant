"""
app.py

AI Study Assistant -- main entrypoint.

Flow:
1. Page config + global CSS injection.
2. Session-state initialization (username, bhabhi mode, settings, results).
3. Onboarding gate: ask for the user's name if not yet known.
4. Secret "Bhabhi Mode" gate: a one-time romantic reveal screen for a small
   list of recognized names (see utils.storage.is_bhabhi_mode).
5. Main app: sidebar (settings, favorites, history), hero, dynamic topic
   chips, search form (Enter-to-submit), generation with animated loading
   and structured error handling, and the tabbed study-material display
   (Explanation / Summary / Important Points / Quiz).

This file is orchestration only -- all rendering lives in
frontend.components, all AI/parsing logic in Backend.*, and all persistence
in utils.storage / utils.export.
"""

import time

import streamlit as st

from backend import ai_handler
from backend.parser import parse_study_material
from backend.prompts import (
    DIFFICULTY_LEVELS,
    STUDY_MODES,
    DEFAULT_DIFFICULTY,
    DEFAULT_STUDY_MODE,
)
from frontend.styles import inject_custom_css
from frontend import components as C
from utils import storage


# ---------------------------------------------------------------------------
# Page config + global styling (must run before any other st.* call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()


# ---------------------------------------------------------------------------
# Per-device local storage (username, history, favorites)
# ---------------------------------------------------------------------------
storage.init_local_storage()


# ---------------------------------------------------------------------------
# Session state initialization
# ---------------------------------------------------------------------------
if "username" not in st.session_state:
    st.session_state.username = storage.get_username() or None

if "bhabhi_mode" not in st.session_state:
    st.session_state.bhabhi_mode = (
        storage.is_bhabhi_mode(st.session_state.username)
        if st.session_state.username
        else False
    )

if "bhabhi_revealed" not in st.session_state:
    st.session_state.bhabhi_revealed = False

if "difficulty" not in st.session_state:
    st.session_state.difficulty = DEFAULT_DIFFICULTY

if "study_mode" not in st.session_state:
    st.session_state.study_mode = DEFAULT_STUDY_MODE

if "current_topic" not in st.session_state:
    st.session_state.current_topic = ""

if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "current_settings" not in st.session_state:
    st.session_state.current_settings = {}

if "generation_error" not in st.session_state:
    st.session_state.generation_error = None


# ---------------------------------------------------------------------------
# Gate 1: Onboarding -- ask for the user's name (no auth, just a name)
# ---------------------------------------------------------------------------
if not st.session_state.username:
    submitted_name = C.render_onboarding()
    if submitted_name:

        st.session_state.username = submitted_name
        storage.set_username(submitted_name)
        st.session_state.bhabhi_mode = storage.is_bhabhi_mode(submitted_name)
        st.rerun()
    st.stop()


# ---------------------------------------------------------------------------
# Gate 2: Secret romantic reveal screen (one-time per session)
# ---------------------------------------------------------------------------
if st.session_state.bhabhi_mode and not st.session_state.bhabhi_revealed:
    with st.spinner("✨ Preparing your study space..."):
        time.sleep(1.2)

    if C.render_bhabhi_reveal():
        st.session_state.bhabhi_revealed = True
        st.rerun()

    st.stop()


# ---------------------------------------------------------------------------
# Generation helper (shared by the search form and the retry button)
# ---------------------------------------------------------------------------
def _run_generation(topic: str) -> None:
    success, data = ai_handler.generate_study_material(
        topic, st.session_state.difficulty, st.session_state.study_mode
    )

    if success:
        st.session_state.current_topic = topic
        st.session_state.current_result = parse_study_material(data)
        st.session_state.current_settings = {
            "difficulty": st.session_state.difficulty,
            "study_mode": st.session_state.study_mode,
        }
        st.session_state.generation_error = None
        storage.add_to_history(topic, st.session_state.difficulty, st.session_state.study_mode)
        storage.log_event(st.session_state.username, topic)
        # Always land on the Explanation tab for a freshly generated topic.
        st.session_state["main_tabs"] = "📘 Explanation"
    else:
        st.session_state.generation_error = data


# ---------------------------------------------------------------------------
# Sidebar: branding, study settings, favorites, history
# ---------------------------------------------------------------------------
with st.sidebar:
    C.render_sidebar_brand()

    C.render_sidebar_section_label("Study Settings")
    st.selectbox("Difficulty Level", DIFFICULTY_LEVELS, key="difficulty")
    st.selectbox("Study Mode", STUDY_MODES, key="study_mode")

    C.render_sidebar_section_label("Favorites")
    C.render_sidebar_favorites(storage.get_favorites(), topic_key="topic_input")

    C.render_sidebar_section_label("Recent Searches")
    history_items = storage.get_history()
    C.render_sidebar_history(history_items, topic_key="topic_input")

    if history_items:
        if C.render_clear_history_button():
            storage.clear_history()
            st.rerun()


# ---------------------------------------------------------------------------
# Greeting + hero
# ---------------------------------------------------------------------------
C.render_greeting_banner(st.session_state.username, st.session_state.bhabhi_mode)
C.render_hero()


# ---------------------------------------------------------------------------
# Dynamic topic chips -- MUST render before the text_input that shares
# the "topic_input" key (sidebar buttons above already follow this rule too).
# ---------------------------------------------------------------------------
C.render_topic_chips("topic_input", st.session_state.get("topic_input", ""))


# ---------------------------------------------------------------------------
# Search form (Enter-to-submit via st.form)
# ---------------------------------------------------------------------------
with st.form("search_form", clear_on_submit=False):
    input_col, button_col = st.columns([5, 1])
    with input_col:
        st.text_input(
            "Topic",
            key="topic_input",
            placeholder="Enter any topic you want to study...",
            label_visibility="collapsed",
        )
    with button_col:
        submitted = st.form_submit_button(
            "✨ Generate", use_container_width=True, type="primary"
        )


# ---------------------------------------------------------------------------
# Handle generation
# ---------------------------------------------------------------------------
if submitted:
    topic = st.session_state.get("topic_input", "").strip()
    if not topic:
        st.warning("Please enter a topic first.")
    else:
        loading_placeholder = st.empty()
        with loading_placeholder.container():
            C.render_loading_animation()

        _run_generation(topic)

        loading_placeholder.empty()


# ---------------------------------------------------------------------------
# Error display with retry
# ---------------------------------------------------------------------------
if st.session_state.generation_error:
    st.error(f"⚠️ {st.session_state.generation_error}")

    retry_topic = st.session_state.get("topic_input", "").strip()
    if retry_topic and st.button("🔄 Retry", key="retry_btn"):
        with st.spinner("Retrying..."):
            _run_generation(retry_topic)
        st.rerun()


# ---------------------------------------------------------------------------
# Display results
# ---------------------------------------------------------------------------
result = st.session_state.current_result
topic = st.session_state.current_topic

if result:
    settings = st.session_state.current_settings

    header_col, fav_col = st.columns([5, 1])
    with header_col:
        st.markdown(f"## 📖 Study Material: {topic}")
        st.caption(
            f"Difficulty: {settings.get('difficulty', '')} • "
            f"Study Mode: {settings.get('study_mode', '')}"
        )
    with fav_col:
        st.markdown("<div style='height: 1.6rem;'></div>", unsafe_allow_html=True)
        is_fav = storage.is_favorite(topic)
        if C.render_favorite_toggle(topic, is_fav):
            storage.toggle_favorite(
                topic, settings.get("difficulty", ""), settings.get("study_mode", "")
            )
            st.rerun()

    C.render_export_row(
        result, topic, settings.get("difficulty", ""), settings.get("study_mode", "")
    )

    selected_tab = C.render_tab_nav(key="main_tabs")

    if selected_tab == "Explanation":
        C.render_section_card("Explanation", "📘", result["explanation"], key="explanation")
    elif selected_tab == "Summary":
        C.render_section_card("Summary", "📝", result["summary"], key="summary")
    elif selected_tab == "Important Points":
        C.render_section_card("Important Points", "⭐", result["important_points"], key="important_points")
    elif selected_tab == "Quiz":
        C.render_quiz(result["quiz"], topic=topic)

else:
    st.info("👆 Enter a topic above (or pick one of the suggestions) to get started.")