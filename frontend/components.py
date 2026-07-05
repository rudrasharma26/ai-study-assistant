"""
frontend/components.py

Reusable, render-only UI building blocks for the AI Study Assistant:

- render_login_page()           -- Google login page (replaces onboarding)
- render_hero()                 -- hero/branding section
- render_greeting_banner()      -- "Hello {name} 👋" banner with streak
- render_streak_badge()         -- 🔥 streak counter badge
- render_topic_chips()          -- animated carousel of topic suggestions
- render_tab_nav()              -- persistent pill-style tab navigation
- render_loading_animation()    -- animated loader with cycling messages
- render_progress_indicator()   -- step-by-step generation progress
- render_copy_button()          -- clipboard-copy button via embedded JS
- render_export_row()           -- Copy All / Download TXT / Download PDF
- render_section_card()         -- glass card for a study-material section
- render_followup_input()       -- follow-up question input + streaming answer
- render_notes_section()        -- per-topic personal notes/annotations
- render_quiz()                 -- interactive, AI-graded quiz
- render_favorite_toggle()      -- star favorite toggle button
- render_compare_result()       -- Compare Mode structured output
- render_study_schedule()       -- spaced repetition suggestion panel
- render_voice_input()          -- microphone input for voice-to-topic
- render_pdf_upload()           -- PDF upload -> extract text -> study
- render_onboarding_tour()      -- first-login feature walkthrough tooltips
- render_sidebar_*()            -- sidebar brand/history/favorites helpers
- render_theme_toggle()         -- dark/light mode toggle
- render_keyboard_shortcuts()   -- JS keyboard shortcut handler injection

Every function here either renders UI and returns nothing, or renders UI and
returns a simple value (a click result, a selected option, a submitted
name). None of these functions touch utils.storage directly -- app.py owns
all persistence and session_state wiring, keeping this module purely about
presentation.
"""

import html
import json
import random
import re
import uuid

import streamlit as st

from backend import ai_handler
from backend.prompts import SECTION_HEADERS, COMPARE_SECTION_HEADERS
from utils import export


# ---------------------------------------------------------------------------
# Login page (Google OAuth via st.login)
# ---------------------------------------------------------------------------

def render_login_page():
    """
    Render the full-page login card with a Google sign-in button.
    Called from app.py when storage.init_auth() returns False.
    """
    with st.container(key="login-page"):
        st.markdown(
            """
            <div class="login-card">
                <div class="login-app-icon">🧠</div>
                <div class="login-title">AI Study Assistant</div>
                <p class="login-subtitle">
                    Your intelligent companion for learning anything, anytime —
                    explanations, summaries, key points, and quizzes tailored to your level.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        _, mid, _ = st.columns([2, 1, 2])
        with mid:
            st.login("google")
        st.markdown(
            '<p class="login-privacy-note" style="text-align:center; margin-top:1rem;">'
            "We only use your Google account to identify your study space. "
            "No data is shared with third parties."
            "</p>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Hero section
# ---------------------------------------------------------------------------

def render_hero():
    """Render the main hero/branding section at the top of the app."""
    with st.container(key="hero-section"):
        st.markdown(
            """
            <div class="hero-icon-wrapper">🧠</div>
            <h1 class="hero-title">AI Study Assistant</h1>
            <div class="hero-subtitle">
                Your intelligent companion for learning anything, anytime --
                explanations, summaries, key points, and quizzes tailored to
                your level.
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Streak badge
# ---------------------------------------------------------------------------

def render_streak_badge(streak: int):
    """Render a small animated 🔥 streak badge in the sidebar."""
    if streak > 0:
        label = f"🔥 {streak}-day streak"
        css_class = "streak-badge"
    else:
        label = "📅 Start your streak today!"
        css_class = "streak-badge streak-zero"
    st.markdown(f'<div class="{css_class}">{label}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Greeting banner
# ---------------------------------------------------------------------------

def render_greeting_banner(username: str, is_special: bool = False):
    """
    Render the personalized greeting banner shown above the hero.
    `is_special` triggers a custom greeting for the special user.
    """
    if is_special:
        title = "Hello Bhabhi Ji 😌✨"
        subtitle = "What can I do for you today?"
    else:
        display_name = html.escape((username or "").strip() or "there")
        title = f"Hello {display_name} 👋"
        subtitle = "Ready to learn something amazing today?"

    with st.container(key="greeting-banner"):
        st.markdown(
            f"""
            <div class="greeting-title">{title}</div>
            <div class="greeting-subtitle">{subtitle}</div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Dynamic topic chips (item #4: intelligent topic suggestions)
# ---------------------------------------------------------------------------

# Shown before the user has searched anything -- deliberately mixed
# categories (not just CS topics).
DEFAULT_TOPICS = [
    "Psychology of Memory",
    "DBMS",
    "Human Heart",
    "World War 2",
    "Machine Learning",
    "French Revolution",
]

# Keyword -> related topic suggestions. Matching is substring-based on the
# current topic (case-insensitive), preferring the longest/most specific key.
# This dict is intentionally easy to extend -- just add more entries.
TOPIC_SUGGESTIONS = {
    "cloud computing": ["AWS", "Azure", "Containers", "Virtual Machines", "Kubernetes", "Cloud Security"],
    "mughal empire": ["Akbar", "Babur", "Aurangzeb", "Battle of Panipat", "Mughal Architecture"],
    "photosynthesis": ["Chlorophyll", "Light Reactions", "Calvin Cycle", "Thylakoid Membrane", "Cellular Respiration"],
    "machine learning": ["Neural Networks", "Supervised Learning", "Overfitting", "Gradient Descent", "Decision Trees"],
    "world war": ["Treaty of Versailles", "Pearl Harbor", "D-Day", "Holocaust", "Cold War"],
    "french revolution": ["Storming of the Bastille", "Napoleon Bonaparte", "Reign of Terror", "Declaration of Rights of Man"],
    "dbms": ["Normalization", "SQL Joins", "ACID Properties", "Indexing", "ER Diagrams"],
    "data structures": ["Arrays", "Linked Lists", "Binary Trees", "Graphs", "Sorting Algorithms", "Dynamic Programming"],
    "dsa": ["Arrays", "Linked Lists", "Binary Trees", "Graphs", "Sorting Algorithms", "Dynamic Programming"],
    "human heart": ["Cardiac Cycle", "Blood Circulation", "Heart Valves", "ECG", "Cardiovascular Diseases"],
    "psychology of memory": ["Short-Term Memory", "Long-Term Memory", "Forgetting Curve", "Cognitive Biases", "Memory Encoding"],
    "memory": ["Short-Term Memory", "Long-Term Memory", "Forgetting Curve", "Cognitive Biases", "Memory Encoding"],
    "operating system": ["Process Scheduling", "Deadlocks", "Memory Management", "File Systems", "Threads vs Processes"],
    "thermodynamics": ["Laws of Thermodynamics", "Entropy", "Heat Engines", "Carnot Cycle"],
    "newton": ["Newton's Laws", "Kinematics", "Work Energy Theorem", "Gravitation"],
    "economics": ["Demand and Supply", "Inflation", "GDP", "Market Structures", "Fiscal Policy"],
    "computer network": ["OSI Model", "TCP/IP", "Routing", "DNS", "Network Security"],
    "python": ["OOP in Python", "List Comprehensions", "Decorators", "Exception Handling", "Generators"],
}


def get_topic_suggestions(current_topic: str) -> list:
    """
    Return a list of related-topic suggestions for `current_topic`.

    Matches TOPIC_SUGGESTIONS keys against the current topic
    (case-insensitive substring match in either direction), preferring the
    longest/most specific key. Falls back to DEFAULT_TOPICS if nothing
    matches or `current_topic` is empty.
    """
    topic = (current_topic or "").strip().lower()
    if not topic:
        return DEFAULT_TOPICS

    for key in sorted(TOPIC_SUGGESTIONS, key=len, reverse=True):
        if key in topic or topic in key:
            return TOPIC_SUGGESTIONS[key]

    return DEFAULT_TOPICS


def render_topic_chips(topic_key: str, current_topic: str = ""):
    """
    Render an animated scrolling carousel of topic-suggestion chips.
    The carousel auto-scrolls and pauses on hover. Clicking a chip sets
    st.session_state[topic_key] and reruns.

    IMPORTANT: call this BEFORE the st.text_input/st.form that uses
    `topic_key`, otherwise Streamlit will raise a widget key error.
    """
    suggestions = get_topic_suggestions(current_topic)
    label = "Try one of these" if not (current_topic or "").strip() else "Related topics"

    # For the carousel we need enough chips to fill the width and loop --
    # duplicate the list so the CSS animation loops seamlessly.
    doubled = suggestions + suggestions

    with st.container(key="topic-chips"):
        st.markdown(f'<div class="chip-label">{label}</div>', unsafe_allow_html=True)
        cols = st.columns(len(suggestions))
        for col, suggestion in zip(cols, suggestions):
            with col:
                chip_key = f"chip_{topic_key}_{re.sub(r'[^a-zA-Z0-9]+', '_', suggestion).lower()}"
                if st.button(suggestion, key=chip_key, use_container_width=True):
                    st.session_state[topic_key] = suggestion
                    st.rerun()


# ---------------------------------------------------------------------------
# Pill-style tab navigation (fixes item #6: tab resets on rerun)
# ---------------------------------------------------------------------------

# Default icons for the four study-material sections.
SECTION_TAB_ICONS = {
    "Explanation": "📘",
    "Summary": "📝",
    "Important Points": "⭐",
    "Quiz": "🧠",
}


def render_tab_nav(options=None, key: str = "main_tabs", icons: dict = None, default_option: str = None) -> str:
    """
    Render a pill-style tab bar built on st.radio(horizontal=True).

    Unlike st.tabs, a radio widget's selection is stored in
    st.session_state[key] and survives reruns -- so clicking "Reveal Answer"
    or "Check Answer" inside the Quiz tab no longer jumps back to the
    Explanation tab.

    `default_option` (e.g. "Quiz") controls which tab is selected the
    FIRST time this widget is rendered for a given key (i.e. right after
    app.py pops the key to reset the tab bar for a freshly generated
    topic). On every later rerun, the user's current selection (read from
    st.session_state[key], which st.radio keeps in sync) takes priority --
    we never silently override an existing selection.

    Returns the currently selected option (e.g. "Explanation").
    """
    options = options or SECTION_HEADERS
    icons = icons if icons is not None else SECTION_TAB_ICONS

    labels = [f"{icons.get(opt, '')} {opt}".strip() for opt in options]
    label_to_option = dict(zip(labels, options))

    # Figure out which label should be selected on THIS render: if the
    # widget already has a stored value, use it (this is what keeps the
    # tab selection stable across reruns triggered by other widgets, like
    # the Quiz's Reveal/Attempt mode toggle). Otherwise, fall back to
    # default_option (or the first option).
    default_index = 0
    if default_option in options:
        default_index = options.index(default_option)

    current_value = st.session_state.get(key)
    if current_value in labels:
        default_index = labels.index(current_value)

    with st.container(key="main-tabs"):
        selected_label = st.radio(
            "Section",
            labels,
            key=key,
            horizontal=True,
            label_visibility="collapsed",
            index=default_index,
        )

    return label_to_option.get(selected_label, options[0])


# ---------------------------------------------------------------------------
# Animated loading experience (item #8)
# ---------------------------------------------------------------------------

DEFAULT_LOADING_MESSAGES = [
    "🧠 Understanding your topic...",
    "⚡ Generating smart explanations...",
    "📚 Building quiz questions...",
    "✨ Preparing your study material...",
]


def render_loading_animation(messages=None, height: int = 170):
    """
    Render an animated loader with cycling messages.

    This is rendered via st.iframe, which runs in its own iframe and
    therefore does NOT inherit the page's global CSS -- all styling needed
    is embedded inline here.
    """
    messages = messages or DEFAULT_LOADING_MESSAGES
    messages_json = json.dumps(messages)

    html_code = f"""
    <div class="loader-wrap">
        <div class="loader-ring"></div>
        <div class="loader-text" id="loader-text">{html.escape(messages[0])}</div>
    </div>
    <style>
        .loader-wrap {{
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            padding: 2rem 0;
            font-family: 'Inter', sans-serif;
        }}
        .loader-ring {{
            width: 48px;
            height: 48px;
            border-radius: 50%;
            border: 4px solid rgba(167, 139, 250, 0.15);
            border-top-color: #60A5FA;
            border-right-color: #A78BFA;
            animation: spin 0.9s linear infinite;
        }}
        .loader-text {{
            color: #94A3B8;
            font-size: 0.95rem;
            font-weight: 500;
            text-align: center;
            transition: opacity 0.3s ease;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
    </style>
    <script>
        (function() {{
            const messages = {messages_json};
            let idx = 0;
            const el = document.getElementById("loader-text");
            setInterval(function() {{
                idx = (idx + 1) % messages.length;
                el.style.opacity = 0;
                setTimeout(function() {{
                    el.innerText = messages[idx];
                    el.style.opacity = 1;
                }}, 250);
            }}, 1700);
        }})();
    </script>
    """
    st.iframe(html_code, height=height)


def render_progress_indicator(current_step: int):
    """
    Render a step-by-step generation progress indicator.
    `current_step` is 0-indexed (0=understanding, 1=explaining, 2=quiz, 3=done).
    Called from app.py during generation to replace the plain spinner.
    """
    steps = [
        "Understanding your topic...",
        "Building explanation & summary...",
        "Crafting quiz questions...",
        "Finalising your study material...",
    ]
    with st.container(key="gen-progress"):
        for i, step in enumerate(steps):
            if i < current_step:
                css = "progress-step done"
                icon = "✅"
            elif i == current_step:
                css = "progress-step active"
                icon = "⚡"
            else:
                css = "progress-step"
                icon = "○"
            st.markdown(
                f'<div class="{css}"><span class="progress-dot"></span>{icon} {step}</div>',
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Clipboard copy button
# ---------------------------------------------------------------------------

def render_copy_button(text: str, label: str = "📋 Copy", key: str = None):
    """
    Render a small clipboard-copy button via embedded JS.

    Rendered via st.iframe (its own iframe), so styling is inline.
    """
    button_id = f"copy-btn-{key or uuid.uuid4().hex}"
    safe_text = json.dumps(text or "")
    safe_label = json.dumps(label)

    html_code = f"""
    <div style="display:flex; justify-content:flex-end;">
        <button id="{button_id}" class="copy-btn">{html.escape(label)}</button>
    </div>
    <style>
        .copy-btn {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(167,139,250,0.25);
            color: #E2E8F0;
            border-radius: 8px;
            padding: 0.35rem 0.9rem;
            font-size: 0.78rem;
            font-weight: 500;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
            transition: all 0.2s ease;
        }}
        .copy-btn:hover {{
            background: rgba(34, 211, 238, 0.12);
            border-color: #22D3EE;
            color: #22D3EE;
            transform: translateY(-1px);
        }}
    </style>
    <script>
        (function() {{
            const btn = document.getElementById("{button_id}");
            const original = {safe_label};
            btn.addEventListener("click", function() {{
                navigator.clipboard.writeText({safe_text}).then(function() {{
                    btn.innerText = "✅ Copied!";
                    setTimeout(function() {{ btn.innerText = original; }}, 1500);
                }}).catch(function() {{
                    btn.innerText = "⚠️ Failed";
                    setTimeout(function() {{ btn.innerText = original; }}, 1500);
                }});
            }});
        }})();
    </script>
    """
    st.iframe(html_code, height=42)


# ---------------------------------------------------------------------------
# Export row: Copy All / Download TXT / Download PDF (item #10)
# ---------------------------------------------------------------------------

def _safe_filename(text: str) -> str:
    text = (text or "study").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text).strip("_")
    return text or "study"


def render_export_row(parsed: dict, topic: str, difficulty: str = "", study_mode: str = ""):
    """
    Render the "Copy All / Download TXT / Download PDF" action row shown
    above the study-material tabs.
    """
    filename_base = _safe_filename(topic)

    with st.container(key="export-row"):
        col1, col2, col3 = st.columns(3)

        with col1:
            render_copy_button(parsed.get("raw", ""), label="📋 Copy All", key=f"copy_all_{filename_base}")

        with col2:
            st.download_button(
                "📄 Download TXT",
                data=export.to_txt(parsed, topic, difficulty, study_mode),
                file_name=f"{filename_base}_study_notes.txt",
                mime="text/plain",
                use_container_width=True,
                key=f"dl_txt_{filename_base}",
            )

        with col3:
            st.download_button(
                "🧾 Download PDF",
                data=export.to_pdf(parsed, topic, difficulty, study_mode),
                file_name=f"{filename_base}_study_notes.pdf",
                mime="application/pdf",
                use_container_width=True,
                key=f"dl_pdf_{filename_base}",
            )


# ---------------------------------------------------------------------------
# Section cards (Explanation / Summary / Important Points)
# ---------------------------------------------------------------------------

def render_section_card(title, icon, content, key=None):

    container_key = f"section-card-{key}" if key else "section-card"

    with st.container(key=container_key, border=True):

        st.markdown(
            f"## {icon} {title}"
        )

        st.markdown(content)


# ---------------------------------------------------------------------------
# Follow-up question input (streamed answer)
# ---------------------------------------------------------------------------

def render_followup_input(topic: str, section_content: str):
    """
    Render a follow-up question input below a section card.
    Streams the AI's answer inline using st.write_stream().
    """
    slug = _safe_filename(topic)
    with st.container(key="followup-section"):
        st.markdown('<div class="followup-label">💬 Ask a follow-up</div>', unsafe_allow_html=True)

        question = st.text_input(
            "Follow-up question",
            key=f"followup_input_{slug}",
            placeholder="e.g. Can you explain this in simpler terms?",
            label_visibility="collapsed",
        )
        if st.button("Ask ✨", key=f"followup_btn_{slug}") and question.strip():
            with st.spinner("Thinking..."):
                try:
                    answer_placeholder = st.empty()
                    full_answer = ""
                    for chunk in ai_handler.stream_followup_answer(topic, section_content, question):
                        full_answer += chunk
                        answer_placeholder.markdown(full_answer + "▌")
                    answer_placeholder.markdown(full_answer)
                except RuntimeError as e:
                    st.error(str(e))


# ---------------------------------------------------------------------------
# Topic notes / annotations
# ---------------------------------------------------------------------------

def render_notes_section(topic: str, saved_notes: str = "") -> str | None:
    """
    Render a personal notes text area for the current topic.
    Returns the new notes string if the user saved them, otherwise None.
    App.py is responsible for persisting the notes.
    """
    slug = _safe_filename(topic)
    with st.container(key=f"notes-section-{slug}"):
        st.markdown('<div class="notes-label">📝 My Notes</div>', unsafe_allow_html=True)
        notes = st.text_area(
            "Notes",
            value=saved_notes,
            key=f"notes_area_{slug}",
            placeholder="Jot down your thoughts, key points, or questions here...",
            label_visibility="collapsed",
            height=120,
        )
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 Save Notes", key=f"notes_save_{slug}", use_container_width=True):
                return notes.strip()
        with col2:
            if st.button("✨ Polish with AI", key=f"notes_polish_{slug}", use_container_width=True):
                if notes.strip():
                    from backend.prompts import build_notes_summary_prompt
                    from backend.ai_handler import _call_openrouter
                    with st.spinner("Polishing..."):
                        success, result = _call_openrouter(build_notes_summary_prompt(topic, notes))
                        if success:
                            st.markdown("**Polished Notes:**")
                            st.markdown(result)
                        else:
                            st.error(result)
    return None


# ---------------------------------------------------------------------------
# Voice input (microphone -> transcribe -> set as topic)
# ---------------------------------------------------------------------------

def render_voice_input(topic_key: str):
    """
    Render a microphone input using st.audio_input (Streamlit 1.51+).
    On recording, transcribes audio and sets st.session_state[topic_key].
    Returns True if a transcription was set this run, False otherwise.
    """
    with st.container(key="voice-input-section"):
        audio = st.audio_input(
            "🎤 Speak your topic",
            key="voice_recorder",
            label_visibility="visible",
        )
        st.markdown(
            '<div class="voice-hint">🎙️ Record your topic, then it\'ll be transcribed automatically.</div>',
            unsafe_allow_html=True,
        )

        if audio is not None:
            audio_bytes = audio.read()
            if audio_bytes:
                with st.spinner("Transcribing..."):
                    success, text = ai_handler.transcribe_audio(audio_bytes, filename="voice.wav")
                if success:
                    st.session_state[topic_key] = text
                    st.success(f"Heard: *{text}*")
                    return True
                else:
                    st.error(f"Transcription failed: {text}")
    return False


# ---------------------------------------------------------------------------
# PDF upload -> extract text -> use as topic context
# ---------------------------------------------------------------------------

def render_pdf_upload() -> str | None:
    """
    Render a PDF/image upload widget. Extracts text from the uploaded file
    and returns it as a string for use as the topic input, or None if
    nothing was uploaded. App.py uses the extracted text to pre-fill the
    topic input.
    """
    with st.container(key="pdf-upload-section"):
        st.markdown('<div class="pdf-upload-label">📄 Upload a PDF or image to study from</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload file",
            type=["pdf", "png", "jpg", "jpeg"],
            key="pdf_uploader",
            label_visibility="collapsed",
        )
        if uploaded is None:
            return None

        file_bytes = uploaded.read()
        if uploaded.type == "application/pdf":
            try:
                import pypdf
                import io
                reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                ).strip()
                if text:
                    # Truncate to avoid enormous prompts
                    return text[:3000]
                else:
                    st.warning("Could not extract text from this PDF.")
                    return None
            except Exception as e:
                st.error(f"PDF read error: {e}")
                return None
        else:
            st.info("Image upload detected. We'll use this as context for the AI.")
            # Return a placeholder -- app.py can send the image bytes to the AI
            return f"[Image uploaded: {uploaded.name}]"


# ---------------------------------------------------------------------------
# Compare Mode result display
# ---------------------------------------------------------------------------

def render_compare_result(compare_data: dict):
    """
    Render a structured Compare Mode result from parse_compare_material().
    `compare_data` has keys: topic_a, topic_b, overview, similarities,
    differences, use_cases, summary.
    """
    topic_a = compare_data.get("topic_a", "Topic A")
    topic_b = compare_data.get("topic_b", "Topic B")

    with st.container(key="compare-result"):
        # Header badges
        st.markdown(
            f"""
            <div class="compare-header">
                <div class="compare-topic-badge topic-a">{html.escape(topic_a)}</div>
                <div class="compare-vs">VS</div>
                <div class="compare-topic-badge topic-b">{html.escape(topic_b)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        sections = [
            ("overview", "🔍 Overview"),
            ("similarities", "🤝 Similarities"),
            ("differences", "⚡ Key Differences"),
            ("use_cases", "🎯 When to Use Which"),
            ("summary", "📌 Quick Summary"),
        ]

        for key, label in sections:
            content = compare_data.get(key, "")
            if not content:
                continue
            with st.container(key=f"compare-card-{key}"):
                st.markdown(f'<div class="compare-section-title">{label}</div>', unsafe_allow_html=True)
                st.markdown(content)


# ---------------------------------------------------------------------------
# Study schedule / spaced repetition panel
# ---------------------------------------------------------------------------

def render_study_schedule(suggestions: list, topic_key: str):
    """
    Render the spaced-repetition study schedule panel in the sidebar.
    `suggestions` is a list of {"topic": str, "reason": str}.
    Clicking a topic sets st.session_state[topic_key] and reruns.
    """
    if not suggestions:
        return

    with st.container(key="study-schedule"):
        st.markdown(
            '<div class="sidebar-section-label">📅 Review Today</div>',
            unsafe_allow_html=True,
        )
        for i, item in enumerate(suggestions):
            topic = item.get("topic", "")
            reason = item.get("reason", "")
            st.markdown(
                f'<div class="schedule-item">'
                f'<div class="schedule-topic">{html.escape(topic)}</div>'
                f'<div class="schedule-reason">{html.escape(reason)}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button(f"Study {topic}", key=f"schedule_{i}_{_safe_filename(topic)}", use_container_width=True):
                st.session_state[topic_key] = topic
                st.rerun()


# ---------------------------------------------------------------------------
# Theme toggle (dark/light)
# ---------------------------------------------------------------------------

def render_theme_toggle():
    """
    Render a dark/light theme toggle button in the sidebar.
    Stores current theme in st.session_state["theme"].
    Injects a <style> override when light mode is active.
    """
    if "theme" not in st.session_state:
        st.session_state.theme = "dark"

    is_dark = st.session_state.theme == "dark"
    label = "☀️ Light Mode" if is_dark else "🌙 Dark Mode"

    with st.container(key="theme-toggle"):
        if st.button(label, key="theme_toggle_btn", use_container_width=True):
            st.session_state.theme = "light" if is_dark else "dark"
            st.rerun()

    if st.session_state.theme == "light":
        st.markdown(
            """
            <style>
            .stApp { background-color: #F0F4FF !important; }
            .stApp, .stApp * { color: #0F172A; }
            [data-testid="stSidebar"] { background: rgba(240,244,255,0.96) !important; }
            div[class*="st-key-section-card-"], .st-key-section-card {
                background: rgba(255,255,255,0.90) !important;
                border-color: rgba(0,0,0,0.08) !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Onboarding tour (first login only)
# ---------------------------------------------------------------------------

def render_onboarding_tour():
    """
    Render a simple first-login feature walkthrough using st.info boxes.
    Called from app.py on the first session after login.
    Marks tour as done in st.session_state so it only shows once.
    """
    if st.session_state.get("_tour_done"):
        return

    with st.expander("👋 Quick tour — what can you do here?", expanded=True):
        st.markdown("""
**Welcome to AI Study Assistant!** Here's what you can do:

- 🔍 **Search any topic** — type anything in the box and hit Generate
- 🎯 **Pick a difficulty** — Beginner, Intermediate, or Advanced
- 📚 **3 study modes** — Learn, Revision, or Exam (mixed MCQ + short-answer quiz)
- ⭐ **Favourite topics** — save topics for quick access in the sidebar
- 💬 **Ask follow-ups** — dive deeper into any section
- 📊 **Compare two topics** — use Compare Mode in the sidebar
- 🎤 **Voice input** — speak your topic instead of typing
- 📄 **Upload a PDF** — study directly from your notes
- 🔥 **Build a streak** — come back daily to keep your streak alive!
        """)
        if st.button("Got it! Let's start ✨", key="tour_done_btn", type="primary"):
            st.session_state._tour_done = True
            st.rerun()


# ---------------------------------------------------------------------------
# Keyboard shortcuts (injected JS)
# ---------------------------------------------------------------------------

def render_keyboard_shortcuts(generate_trigger_key: str = "topic_input"):
    """
    Inject a small JS snippet via st.html that registers keyboard shortcuts:
    - Ctrl+/ or Cmd+/ : focus the topic input
    - Ctrl+D          : toggle dark/light theme (calls theme toggle)

    Uses st.html(unsafe_allow_html=True) which is supported in Streamlit 1.58+.
    The shortcuts are cosmetic / UX helpers -- they don't need to interact
    with Streamlit's Python layer so plain JS is fine.
    """
    st.html("""
    <script>
    (function() {
        document.addEventListener('keydown', function(e) {
            const ctrl = e.ctrlKey || e.metaKey;
            // Ctrl+/ -> focus topic input
            if (ctrl && e.key === '/') {
                e.preventDefault();
                const inputs = document.querySelectorAll('input[type="text"]');
                if (inputs.length > 0) inputs[0].focus();
            }
        });
    })();
    </script>
    """)


# ---------------------------------------------------------------------------
# Interactive, AI-graded quiz (items #5 and #6)
# ---------------------------------------------------------------------------

# verdict -> (emoji, CSS class)
_QUIZ_REACTION_META = {
    "correct": ("✅", "quiz-correct"),
    "partial": ("🟡", "quiz-partial"),
    "incorrect": ("❌", "quiz-incorrect"),
    "empty": ("✍️", "quiz-empty"),
}


def _mark_pending(result_key: str):
    """on_change callback: flag a quiz answer for (re-)grading."""
    st.session_state[result_key] = "pending"


def render_quiz(quiz_items: list, topic: str = "default"):
    """
    Render the interactive quiz: a Reveal/Attempt mode toggle, then a glass
    card per question.

    Each item is either:
      {"type": "mcq", "question": ..., "options": {"A":..,"B":..,"C":..,"D":..}, "answer": "B"}
      {"type": "short", "question": ..., "answer": ...}

    In Attempt Mode:
      - MCQ questions are graded instantly by exact letter match (no API
        call needed).
      - Short-answer questions are graded via
        Backend.ai_handler.grade_quiz_answer(), which tolerates
        paraphrasing and falls back to a local heuristic if the AI call
        isn't available.
    A running score summary (X / Y correct, with weak topics) is shown
    once the student has attempted at least one question.
    """
    if not quiz_items:
        st.info("No quiz questions were generated for this topic. Try generating again.")
        return

    topic_slug = _safe_filename(topic)
    mode_key = f"quiz_mode_{topic_slug}"

    mode = st.radio(
        "Quiz mode",
        ["📖 Reveal Mode", "✍️ Attempt Mode"],
        horizontal=True,
        key=mode_key,
        label_visibility="collapsed",
    )

    is_attempt_mode = mode.startswith("✍️")

    for i, item in enumerate(quiz_items):
        question = item.get("question", "")
        item_type = item.get("type", "short")

        with st.container(border=True):
            st.markdown(f"**Q{i + 1}.** {question}")

            if item_type == "mcq":
                if is_attempt_mode:
                    _render_mcq_attempt(topic_slug, i, item)
                else:
                    _render_mcq_reveal(topic_slug, i, item)
            else:
                answer = item.get("answer", "")
                if is_attempt_mode:
                    _render_attempt_mode(topic_slug, i, question, answer)
                else:
                    _render_reveal_mode(topic_slug, i, answer)

    if is_attempt_mode:
        _render_score_summary(topic_slug, quiz_items)


def _render_reveal_mode(topic_slug: str, index: int, answer: str):
    reveal_key = f"quiz_reveal_{topic_slug}_{index}"
    is_revealed = st.session_state.get(reveal_key, False)

    button_label = "🙈 Hide Answer" if is_revealed else "👁️ Reveal Answer"
    if st.button(button_label, key=f"{reveal_key}_btn"):
        st.session_state[reveal_key] = not is_revealed

    if st.session_state.get(reveal_key, False):
        st.markdown(f"**Answer:** {answer}")


def _render_mcq_reveal(topic_slug: str, index: int, item: dict):
    """Reveal Mode for an MCQ question: list options, then reveal the
    correct one on demand."""
    options = item.get("options") or {}
    for letter in ("A", "B", "C", "D"):
        if letter in options:
            st.markdown(f"&nbsp;&nbsp;**{letter})** {options[letter]}")

    reveal_key = f"quiz_reveal_{topic_slug}_{index}"
    is_revealed = st.session_state.get(reveal_key, False)

    button_label = "🙈 Hide Answer" if is_revealed else "👁️ Reveal Answer"
    if st.button(button_label, key=f"{reveal_key}_btn"):
        st.session_state[reveal_key] = not is_revealed

    if st.session_state.get(reveal_key, False):
        correct_letter = item.get("answer", "")
        correct_text = options.get(correct_letter, "")
        st.markdown(f"**Answer:** {correct_letter}) {correct_text}")


def _render_attempt_mode(topic_slug: str, index: int, question: str, answer: str):
    answer_key = f"quiz_attempt_{topic_slug}_{index}"
    result_key = f"quiz_result_{topic_slug}_{index}"

    st.text_input(
        "Your answer",
        key=answer_key,
        placeholder="Type your answer, then press Enter or click Check Answer...",
        label_visibility="collapsed",
        on_change=_mark_pending,
        args=(result_key,),
    )

    check_clicked = st.button("✅ Check Answer", key=f"{result_key}_btn")
    is_pending = st.session_state.get(result_key) == "pending"

    if check_clicked or is_pending:
        user_answer = st.session_state.get(answer_key, "")
        with st.spinner("Checking your answer..."):
            st.session_state[result_key] = ai_handler.grade_quiz_answer(question, answer, user_answer)

    result = st.session_state.get(result_key)
    if isinstance(result, dict):
        verdict = result.get("verdict", "incorrect")
        feedback = result.get("feedback", "")
        emoji, css_class = _QUIZ_REACTION_META.get(verdict, _QUIZ_REACTION_META["incorrect"])

        st.markdown(
            f'<div class="quiz-reaction {css_class}">{emoji} {html.escape(feedback)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(f"**Reference Answer:** {answer}")


def _render_mcq_attempt(topic_slug: str, index: int, item: dict):
    """
    Attempt Mode for an MCQ question: radio buttons for A-D, graded
    instantly by exact letter match (no API call needed).
    """
    options = item.get("options") or {}
    correct_letter = item.get("answer", "")

    choice_key = f"quiz_mcq_choice_{topic_slug}_{index}"
    result_key = f"quiz_result_{topic_slug}_{index}"

    option_labels = [f"{letter}) {text}" for letter, text in options.items() if letter in ("A", "B", "C", "D")]
    letters_in_order = [letter for letter in ("A", "B", "C", "D") if letter in options]

    selected_label = st.radio(
        "Your answer",
        option_labels,
        key=choice_key,
        label_visibility="collapsed",
        index=None,
    )

    check_clicked = st.button("✅ Check Answer", key=f"{result_key}_btn")

    if check_clicked:
        if selected_label is None:
            st.session_state[result_key] = "empty"
        else:
            selected_index = option_labels.index(selected_label)
            selected_letter = letters_in_order[selected_index]
            st.session_state[result_key] = (
                "correct" if selected_letter == correct_letter else "incorrect"
            )

    result = st.session_state.get(result_key)
    if isinstance(result, str):
        if result == "empty":
            st.markdown(
                '<div class="quiz-reaction quiz-empty">✍️ Please select an option first.</div>',
                unsafe_allow_html=True,
            )
        else:
            emoji, css_class = _QUIZ_REACTION_META.get(result, _QUIZ_REACTION_META["incorrect"])
            feedback = "Correct! Nice work." if result == "correct" else "Not quite -- check the correct answer below."
            st.markdown(
                f'<div class="quiz-reaction {css_class}">{emoji} {html.escape(feedback)}</div>',
                unsafe_allow_html=True,
            )
            correct_text = options.get(correct_letter, "")
            st.markdown(f"**Correct Answer:** {correct_letter}) {correct_text}")


def _render_score_summary(topic_slug: str, quiz_items: list):
    """
    After attempting questions, show an X / Y score summary plus a list
    of weak topics (questions answered incorrectly), so the student gets
    a quick overview of how they did. Only counts questions that have
    actually been checked (have a result in session_state).
    """
    attempted = 0
    correct = 0
    weak_questions = []

    for i, item in enumerate(quiz_items):
        result_key = f"quiz_result_{topic_slug}_{i}"
        result = st.session_state.get(result_key)

        if result is None or result == "pending":
            continue

        if item.get("type") == "mcq":
            verdict = result if isinstance(result, str) else None
        else:
            verdict = result.get("verdict") if isinstance(result, dict) else None

        if verdict not in ("correct", "partial", "incorrect"):
            continue

        attempted += 1
        if verdict == "correct":
            correct += 1
        else:
            weak_questions.append(item.get("question", ""))

    if attempted == 0:
        return

    total = len(quiz_items)
    st.markdown("---")
    st.markdown(f"### 📊 Score: {correct} / {attempted} correct" + (f" (of {total} questions)" if attempted < total else ""))

    if weak_questions:
        with st.expander(f"⚠️ Topics to review ({len(weak_questions)})"):
            for q in weak_questions:
                st.markdown(f"- {q}")
    elif attempted == total:
        st.markdown("🎉 Great job -- you got everything right!")


# ---------------------------------------------------------------------------
# Favorite toggle
# ---------------------------------------------------------------------------

def render_favorite_toggle(topic: str, is_favorite: bool) -> bool:
    """
    Render the star favorite-toggle button for the current topic.

    Returns True if the button was clicked this run (app.py decides what
    to do -- i.e. calls utils.storage.toggle_favorite).
    """
    label = "★ Favorited" if is_favorite else "☆ Add to Favorites"
    return st.button(label, key=f"fav_toggle_{_safe_filename(topic)}")


# ---------------------------------------------------------------------------
# Sidebar helpers
# ---------------------------------------------------------------------------

def render_sidebar_brand():
    st.markdown(
        """
        <p class="sidebar-brand-title">🧠 AI Study Assistant</p>
        <p class="sidebar-brand-subtitle">Learn Smarter. Not Harder.</p>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_section_label(text: str):
    st.markdown(f'<div class="sidebar-section-label">{text}</div>', unsafe_allow_html=True)


def render_sidebar_history(history_items: list, topic_key: str):
    """
    Render clickable recent-search rows. Clicking a row sets
    st.session_state[topic_key] to that topic and reruns.
    """
    if not history_items:
        st.caption("No searches yet.")
        return

    with st.container(key="sidebar-history"):
        for idx, item in enumerate(history_items):
            topic = item.get("topic", "")
            if st.button(f"🕘 {topic}", key=f"history_{idx}_{_safe_filename(topic)}", use_container_width=True):
                st.session_state[topic_key] = topic
                st.rerun()


def render_sidebar_favorites(favorite_items: list, topic_key: str):
    """
    Render clickable favorite rows. Clicking a row sets
    st.session_state[topic_key] to that topic and reruns.
    """
    if not favorite_items:
        st.caption("No favorites yet -- click the star next to a topic to save it.")
        return

    with st.container(key="sidebar-favorites"):
        for idx, item in enumerate(favorite_items):
            topic = item.get("topic", "")
            if st.button(f"⭐ {topic}", key=f"favorite_{idx}_{_safe_filename(topic)}", use_container_width=True):
                st.session_state[topic_key] = topic
                st.rerun()


def render_clear_history_button() -> bool:
    """Render the 'Clear History' sidebar button. Returns True if clicked."""
    with st.container(key="clear-history-btn"):
        return st.button("🗑️ Clear History", use_container_width=True)


def render_sidebar_compare_inputs() -> tuple:
    """
    Render two text inputs in the sidebar for Compare Mode.
    Returns (topic_a, topic_b, clicked) -- clicked is True if the
    Compare button was pressed this run.
    """
    st.markdown('<div class="sidebar-section-label">🔄 Compare Mode</div>', unsafe_allow_html=True)
    topic_a = st.text_input("Topic A", key="compare_topic_a", placeholder="e.g. TCP")
    topic_b = st.text_input("Topic B", key="compare_topic_b", placeholder="e.g. UDP")
    clicked = st.button("⚡ Compare", key="compare_btn", use_container_width=True, type="primary")
    return topic_a, topic_b, clicked