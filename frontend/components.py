"""
frontend/components.py

Reusable, render-only UI building blocks for the AI Study Assistant:

- render_onboarding()         -- first-time "what's your name?" screen
- render_bhabhi_reveal()       -- secret romantic reveal screen
- render_hero()                 -- hero/branding section
- render_greeting_banner()      -- "Hello {name} 👋" banner
- render_topic_chips()          -- dynamic example/related topic chips
- render_tab_nav()              -- persistent pill-style tab navigation
- render_loading_animation()    -- animated loader with cycling messages
- render_copy_button()          -- clipboard-copy button via embedded JS
- render_export_row()           -- Copy All / Download TXT / Download PDF
- render_section_card()         -- glass card for a study-material section
- render_quiz()                 -- interactive, AI-graded quiz
- render_favorite_toggle()      -- star favorite toggle button
- render_sidebar_*()            -- sidebar brand/history/favorites helpers

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
from backend.prompts import SECTION_HEADERS
from utils import export


# ---------------------------------------------------------------------------
# Onboarding screen
# ---------------------------------------------------------------------------

def render_onboarding():
    """
    Render the first-time welcome screen asking for the user's name.

    Returns the submitted name (str) if the form was submitted with a
    non-empty name on this run, otherwise None.
    """
    submitted_name = None

    with st.container(key="onboarding-screen"):
        st.markdown(
            """
            <div class="onboarding-card">
                <div class="onboarding-icon">✨</div>
                <div class="onboarding-title">
                    May I have the privilege<br>of knowing your name?
                </div>
                <p class="onboarding-subtitle">
                    Just your name -- no sign-up, no password.
                    We'll remember it so your study space feels like yours.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.container(key="onboarding-form"):
            _, mid, _ = st.columns([1, 2, 1])
            with mid:
                with st.form("onboarding_form", clear_on_submit=False):
                    name = st.text_input(
                        "Your name",
                        placeholder="Enter your name...",
                        label_visibility="collapsed",
                    )
                    submitted = st.form_submit_button(
                        "Continue ✨", use_container_width=True, type="primary"
                    )

    if submitted and name.strip():
        submitted_name = name.strip()

    return submitted_name


# ---------------------------------------------------------------------------
# Secret romantic reveal screen
# ---------------------------------------------------------------------------

_PARTICLE_EMOJIS = ["💖", "💕", "🌸", "✨", "💗", "🩷"]


def render_bhabhi_reveal() -> bool:
    """
    Render the secret romantic reveal screen shown only when
    utils.storage.is_bhabhi_mode(name) is True.

    Returns True if the "Enter Study Space" button was clicked this run.
    """
    # Fixed seed -> particle positions stay stable across reruns instead of
    # jumping around every time the user interacts with something.
    rng = random.Random(1234)
    particles_html = ""
    for _ in range(16):
        emoji = rng.choice(_PARTICLE_EMOJIS)
        left = rng.randint(2, 96)
        delay = round(rng.uniform(0, 8), 1)
        duration = round(rng.uniform(7, 13), 1)
        size = round(rng.uniform(1.0, 1.9), 2)
        particles_html += (
            f'<span class="romantic-particle" '
            f'style="left:{left}%; animation-delay:{delay}s; '
            f'animation-duration:{duration}s; font-size:{size}rem;">'
            f'{emoji}</span>'
        )

    with st.container(key="bhabhi-reveal"):
        st.markdown(
            f"""
            {particles_html}
            <div class="romantic-card">
                <div class="romantic-hearts">💞</div>
                <div class="romantic-title">🌸 Areey Bhabhiji Aap 😌✨</div>
                <div class="romantic-divider"></div>
                <div class="romantic-subtitle">Aaj kya seekhna pasand karengi?</div>
                <p class="romantic-text">
                    A special study space has been prepared just for you 💖<br>
                    Explanations, summaries, important points, and quizzes --
                    all ready whenever you are.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)

        left, mid, right = st.columns([1, 1.4, 1])
        with mid:
            with st.container(key="bhabhi-enter-btn"):
                clicked = st.button("Enter Study Space 💖", use_container_width=True)

    return clicked


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
# Greeting banner
# ---------------------------------------------------------------------------

def render_greeting_banner(username: str, bhabhi_mode: bool = False):
    """
    Render the personalized greeting banner shown above the hero on the
    main app screen.
    """
    if bhabhi_mode:
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
    Render a row of clickable topic-suggestion chips. Clicking a chip sets
    st.session_state[topic_key] to that topic and triggers a rerun.

    IMPORTANT: call this BEFORE the st.text_input/st.form that uses
    `topic_key`, otherwise Streamlit will raise an error about modifying a
    widget's session state after it has been instantiated.
    """
    suggestions = get_topic_suggestions(current_topic)
    label = "Try one of these" if not (current_topic or "").strip() else "Related topics"

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


def render_tab_nav(options=None, key: str = "main_tabs", icons: dict = None) -> str:
    """
    Render a pill-style tab bar built on st.radio(horizontal=True).

    Unlike st.tabs, a radio widget's selection is stored in
    st.session_state[key] and survives reruns -- so clicking "Reveal Answer"
    or "Check Answer" inside the Quiz tab no longer jumps back to the
    Explanation tab.

    Returns the currently selected option (e.g. "Explanation").
    """
    options = options or SECTION_HEADERS
    icons = icons if icons is not None else SECTION_TAB_ICONS

    labels = [f"{icons.get(opt, '')} {opt}".strip() for opt in options]
    label_to_option = dict(zip(labels, options))

    with st.container(key="main-tabs"):
        selected_label = st.radio(
            "Section",
            labels,
            key=key,
            horizontal=True,
            label_visibility="collapsed",
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

    with st.container(border=True):

        st.markdown(
            f"## {icon} {title}"
        )

        st.markdown(content)


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

    In Attempt Mode, the student's free-text answer is graded via
    Backend.ai_handler.grade_quiz_answer(), which tolerates paraphrasing and
    falls back to a local heuristic if the AI call isn't available -- so
    this never "feels broken" even offline.
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

    for i, item in enumerate(quiz_items):
        question = item.get("question", "")
        answer = item.get("answer", "")

        with st.container(border=True):
            st.markdown(f"**Q{i + 1}.** {question}")

            if mode.startswith("📖"):
                _render_reveal_mode(topic_slug, i, answer)
            else:
                _render_attempt_mode(topic_slug, i, question, answer)


def _render_reveal_mode(topic_slug: str, index: int, answer: str):
    reveal_key = f"quiz_reveal_{topic_slug}_{index}"
    is_revealed = st.session_state.get(reveal_key, False)

    button_label = "🙈 Hide Answer" if is_revealed else "👁️ Reveal Answer"
    if st.button(button_label, key=f"{reveal_key}_btn"):
        st.session_state[reveal_key] = not is_revealed

    if st.session_state.get(reveal_key, False):
        st.markdown(f"**Answer:** {answer}")


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