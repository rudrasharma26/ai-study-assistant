"""
app.py

AI Study Assistant -- main entrypoint.

Flow:
1. Page config + global CSS injection.
2. Google auth gate via storage.init_auth() -- shows login page if not
   logged in. On first login, Supabase record is created and streak updated.
3. Session-state initialization (settings, results, notes, compare state).
4. First-login onboarding tour (shown once per session after login).
5. Sidebar: branding, logout, streak, theme toggle, study settings,
   Compare Mode inputs, study schedule, favorites, history.
6. Main area: greeting, hero, voice input, PDF upload, topic chips,
   search form, auto-difficulty detection, generation with progress
   indicator, tabbed study material display with follow-up and notes.

Orchestration only -- rendering lives in frontend.components, AI/parsing
logic in backend.*, persistence in utils.storage / utils.export.
"""

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
# Page config + global styling (must be the very first st.* call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Study Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_custom_css()


# ---------------------------------------------------------------------------
# Auth gate -- shows Google login page if user is not logged in.
# init_auth() returns True if logged in, False otherwise.
# On True: st.session_state._user_id and _username are populated,
#          streak is updated, and Supabase record is ready.
# ---------------------------------------------------------------------------
if not storage.init_auth():
    C.render_login_page()
    st.stop()


# ---------------------------------------------------------------------------
# Session-state initialization (safe to reference st.user here)
# ---------------------------------------------------------------------------
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

if "compare_result" not in st.session_state:
    st.session_state.compare_result = None

if "compare_error" not in st.session_state:
    st.session_state.compare_error = None

# Per-topic notes stored in session_state for this session
if "_notes" not in st.session_state:
    st.session_state._notes = {}


# ---------------------------------------------------------------------------
# Onboarding tour (shown once per session on first login)
# ---------------------------------------------------------------------------
C.render_onboarding_tour()


# ---------------------------------------------------------------------------
# Generation helper
# ---------------------------------------------------------------------------
def _run_generation(topic: str) -> None:
    """
    Call the AI to generate study material for `topic`.
    Uses the current difficulty/study_mode from session_state.
    Updates session_state and Supabase history on success.
    """
    success, data = ai_handler.generate_study_material(
        topic,
        st.session_state.difficulty,
        st.session_state.study_mode,
    )

    if success:
        st.session_state.current_topic = topic
        st.session_state.current_result = parse_study_material(data)
        st.session_state.current_settings = {
            "difficulty": st.session_state.difficulty,
            "study_mode": st.session_state.study_mode,
        }
        st.session_state.generation_error = None
        st.session_state.compare_result = None

        storage.add_to_history(topic, st.session_state.difficulty, st.session_state.study_mode)
        storage.log_event(storage.get_username(), topic)

        # Reset tab bar to default (Explanation or Quiz for Exam Mode).
        st.session_state.pop("main_tabs", None)
    else:
        st.session_state.generation_error = data


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    C.render_sidebar_brand()

    # Signed-in user info + logout
    st.caption(f"Signed in as {st.user.email}")
    storage.render_logout_button()

    st.divider()

    # Streak badge
    streak = storage.get_streak()
    C.render_streak_badge(streak)

    # Theme toggle
    C.render_theme_toggle()

    st.divider()

    # Study settings
    C.render_sidebar_section_label("Study Settings")
    st.selectbox("Difficulty Level", DIFFICULTY_LEVELS, key="difficulty")
    st.selectbox("Study Mode", STUDY_MODES, key="study_mode")

    st.divider()

    # Compare Mode inputs
    topic_a, topic_b, compare_clicked = C.render_sidebar_compare_inputs()
    if compare_clicked:
        if topic_a.strip() and topic_b.strip():
            with st.spinner("Comparing..."):
                success, result = ai_handler.generate_compare_material(
                    topic_a.strip(), topic_b.strip(), st.session_state.difficulty
                )
            if success:
                st.session_state.compare_result = result
                st.session_state.compare_error = None
                st.session_state.current_result = None
            else:
                st.session_state.compare_error = result
        else:
            st.warning("Enter both topics to compare.")

    st.divider()

    # Study schedule (spaced repetition suggestions)
    history_items = storage.get_history()
    if history_items:
        schedule = ai_handler.get_study_suggestions(history_items)
        C.render_study_schedule(schedule, topic_key="topic_input")
        st.divider()

    # Favorites
    C.render_sidebar_section_label("Favorites")
    C.render_sidebar_favorites(storage.get_favorites(), topic_key="topic_input")

    # Recent searches
    C.render_sidebar_section_label("Recent Searches")
    C.render_sidebar_history(history_items, topic_key="topic_input")

    if history_items:
        if C.render_clear_history_button():
            storage.clear_history()
            st.rerun()


# ---------------------------------------------------------------------------
# Inject keyboard shortcuts
# ---------------------------------------------------------------------------
C.render_keyboard_shortcuts()


# ---------------------------------------------------------------------------
# Greeting + hero
# ---------------------------------------------------------------------------
username = storage.get_username()

C.render_greeting_banner(username)
C.render_hero()


# ---------------------------------------------------------------------------
# Voice input (collapsible, above the search bar)
# ---------------------------------------------------------------------------
with st.expander("🎤 Speak your topic instead", expanded=False):
    C.render_voice_input("topic_input")


# ---------------------------------------------------------------------------
# PDF upload (collapsible, above the search bar)
# ---------------------------------------------------------------------------
with st.expander("📄 Upload a PDF or image to study from", expanded=False):
    extracted_text = C.render_pdf_upload()
    if extracted_text:
        st.session_state["topic_input"] = extracted_text[:120].strip()
        st.info("Content loaded. Edit the topic below if needed, then Generate.")


# ---------------------------------------------------------------------------
# Dynamic topic chips (must render BEFORE the text_input with "topic_input")
# ---------------------------------------------------------------------------
C.render_topic_chips("topic_input", st.session_state.get("topic_input", ""))


# ---------------------------------------------------------------------------
# Search form
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
# Auto-difficulty detection (non-blocking, fires on topic change)
# ---------------------------------------------------------------------------
current_topic_input = st.session_state.get("topic_input", "").strip()
if (
    current_topic_input
    and current_topic_input != st.session_state.get("_last_auto_diff_topic", "")
    and not submitted
):
    detected = ai_handler.detect_difficulty(current_topic_input)
    st.session_state._last_auto_diff_topic = current_topic_input
    if detected and detected != st.session_state.difficulty:
        col_badge, col_btn = st.columns([3, 1])
        with col_badge:
            st.markdown(
                f'<span class="auto-diff-badge">⚡ Suggested difficulty: {detected}</span>',
                unsafe_allow_html=True,
            )
        with col_btn:
            if st.button(f"Apply {detected}", key="apply_auto_diff"):
                st.session_state.difficulty = detected
                st.rerun()


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
        st.rerun()


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

if st.session_state.compare_error:
    st.error(f"⚠️ Compare failed: {st.session_state.compare_error}")


# ---------------------------------------------------------------------------
# Display: Compare Mode result
# ---------------------------------------------------------------------------
if st.session_state.compare_result:
    compare_data = st.session_state.compare_result
    st.markdown(
        f"## 🔄 Comparing: **{compare_data.get('topic_a', '')}** vs **{compare_data.get('topic_b', '')}**"
    )
    if st.button("✖ Close Compare", key="close_compare"):
        st.session_state.compare_result = None
        st.rerun()
    C.render_compare_result(compare_data)


# ---------------------------------------------------------------------------
# Display: Study material
# ---------------------------------------------------------------------------
result = st.session_state.current_result
topic = st.session_state.current_topic

if result and not st.session_state.compare_result:
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

    default_tab = "Quiz" if settings.get("study_mode") == "Exam Mode" else "Explanation"
    selected_tab = C.render_tab_nav(key="main_tabs", default_option=default_tab)

    if selected_tab == "Explanation":
        C.render_section_card("Explanation", "📘", result["explanation"], key="explanation")
        C.render_followup_input(topic, result.get("explanation", ""))
        saved_notes = st.session_state._notes.get(topic, "")
        new_notes = C.render_notes_section(topic, saved_notes)
        if new_notes is not None:
            st.session_state._notes[topic] = new_notes
            st.success("Notes saved!")

    elif selected_tab == "Summary":
        C.render_section_card("Summary", "📝", result["summary"], key="summary")
        C.render_followup_input(topic, result.get("summary", ""))

    elif selected_tab == "Important Points":
        C.render_section_card("Important Points", "⭐", result["important_points"], key="important_points")
        C.render_followup_input(topic, result.get("important_points", ""))

    elif selected_tab == "Quiz":
        C.render_quiz(result["quiz"], topic=topic)

elif not st.session_state.compare_result:
    st.info("👆 Enter a topic above (or pick one of the suggestions) to get started.")