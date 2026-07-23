"""
frontend/styles.py

All custom CSS for the AI Study Assistant's premium, futuristic, colorful
dark theme -- deep-space gradients, glassmorphism cards, glowing accents,
pill-style tabs, a styled sidebar.

This module exposes ONE function, inject_custom_css(), which app.py calls
once near the top of the script.

Many selectors below rely on Streamlit's `st.container(key="...")` feature
(Streamlit >= 1.32), which adds a `.st-key-<key>` class to that container's
wrapper div. frontend/components.py uses matching `key=` values, so the two
files must stay in sync -- the key names used here are documented next to
each section.
"""

import streamlit as st

CUSTOM_CSS = """
<style>

/* ==========================================================================
   FONTS
   ========================================================================== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Sora:wght@600;700;800&display=swap');

/* ==========================================================================
   COLOR PALETTE / DESIGN TOKENS
   ========================================================================== */
:root {
    --bg-deep: #060814;
    --bg-card: rgba(17, 20, 38, 0.86);
    --bg-card-hover: rgba(24, 28, 50, 0.94);
    --border-color: rgba(255, 255, 255, 0.09);
    --border-glow: rgba(167, 139, 250, 0.55);

    --accent-blue: #60A5FA;
    --accent-purple: #A78BFA;
    --accent-pink: #F472B6;
    --accent-cyan: #22D3EE;

    --text-primary: #F8FAFC;
    --text-secondary: #A5B4CB;
    --text-muted: #64748B;

    --success: #34D399;
    --warning: #FBBF24;
    --danger: #F87171;
}

/* ==========================================================================
   GLOBAL APP BACKGROUND -- deep space gradient + starfield
   ========================================================================== */
.stApp {
    background-color: var(--bg-deep);
    background-image:
        radial-gradient(ellipse 70% 45% at 15% -5%, rgba(96, 165, 250, 0.22), transparent 60%),
        radial-gradient(ellipse 60% 45% at 95% 5%, rgba(167, 139, 250, 0.20), transparent 60%),
        radial-gradient(ellipse 65% 55% at 50% 105%, rgba(244, 114, 182, 0.16), transparent 60%),
        radial-gradient(circle, rgba(255, 255, 255, 0.45) 1px, transparent 1.5px);
    background-size: auto, auto, auto, 64px 64px;
    background-attachment: fixed;
    color: var(--text-primary);
    font-family: 'Inter', sans-serif;
}

/* Hide default Streamlit chrome for a cleaner, branded look */
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent !important; }

/* Tighten default top padding */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 2.5rem !important;
}

/* Smooth fade for the whole app on load */
section.main > div {
    animation: fadeIn 0.4s ease;
}


/* ==========================================================================
   TYPOGRAPHY HELPERS
   ========================================================================== */
.gradient-text {
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    background: linear-gradient(135deg, #93C5FD 0%, #A78BFA 50%, #F0ABFC 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}


/* ==========================================================================
   GREETING BANNER  (components.render_greeting_banner -> key="greeting-banner")
   ========================================================================== */
.st-key-greeting-banner {
    margin-bottom: 0.5rem;
}
.greeting-title {
    font-family: 'Sora', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}
.greeting-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    margin: 0.15rem 0 0;
}


/* ==========================================================================
   HERO SECTION  (components.render_hero -> key="hero-section")
   ========================================================================== */
.st-key-hero-section {
    text-align: left;
    padding: 1.5rem 1rem 0.5rem;
    animation: fadeInUp 0.7s ease;
}

.hero-icon-wrapper {
    width: 96px;
    height: 96px;
    margin: 0 0 0.75rem;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.6rem;
    background: radial-gradient(circle, rgba(96, 165, 250, 0.22), rgba(167, 139, 250, 0.04) 70%);
    border: 1px solid rgba(167, 139, 250, 0.35);
    box-shadow: 0 0 40px rgba(99, 102, 241, 0.30), inset 0 0 25px rgba(96, 165, 250, 0.12);
    animation: pulseGlow 3.2s ease-in-out infinite;
}

.hero-title {
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 3rem;
    margin: 0.2rem 0 0.4rem;
    background: linear-gradient(135deg, #93C5FD 0%, #A78BFA 50%, #F0ABFC 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    filter: drop-shadow(0 0 24px rgba(167, 139, 250, 0.35));
}

.hero-subtitle {
    color: var(--text-secondary);
    font-size: 1.05rem;
    max-width: 560px;
    margin: 0 0 0.5rem;
    line-height: 1.6;
}


/* ==========================================================================
   ONBOARDING SCREEN  (components.render_onboarding -> key="onboarding-screen")
   ========================================================================== */
.st-key-onboarding-screen {
    min-height: 65vh;
    display: flex;
    align-items: center;
    justify-content: center;
}

.onboarding-card {
    max-width: 480px;
    margin: 0 auto;
    text-align: center;
    padding: 2.5rem 2rem;
    border-radius: 24px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    backdrop-filter: blur(14px);
    box-shadow: 0 0 50px rgba(99, 102, 241, 0.12), 0 20px 50px rgba(0, 0, 0, 0.35);
    animation: fadeInUp 0.7s ease;
}

.onboarding-icon {
    font-size: 2.75rem;
    margin-bottom: 0.5rem;
    display: inline-block;
    animation: floatY 3s ease-in-out infinite;
}

.onboarding-title {
    font-family: 'Sora', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    margin: 0.25rem 0 0.6rem;
    background: linear-gradient(135deg, #93C5FD 0%, #A78BFA 50%, #F0ABFC 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.onboarding-subtitle {
    color: var(--text-secondary);
    font-size: 1rem;
    line-height: 1.6;
    max-width: 380px;
    margin: 0 auto 1.5rem;
}

/* The onboarding name input + button, scoped via key="onboarding-form" */
.st-key-onboarding-form .stTextInput input {
    text-align: center;
    font-size: 1.05rem;
}
.st-key-onboarding-form div[data-testid="stFormSubmitButton"] button {
    width: 100%;
    margin-top: 0.5rem;
}



/* ==========================================================================
   BUTTONS -- smaller, elegant, premium hover (global default)
   ========================================================================== */
.stButton > button {
    border-radius: 10px;
    border: 1px solid var(--border-color);
    background: rgba(255, 255, 255, 0.035);
    color: var(--text-primary);
    font-weight: 500;
    font-size: 0.88rem;
    padding: 0.4rem 1rem;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: var(--accent-purple);
    background: rgba(167, 139, 250, 0.12);
    transform: translateY(-1px);
    box-shadow: 0 4px 14px rgba(167, 139, 250, 0.18);
    color: var(--text-primary);
}
.stButton > button:active {
    transform: translateY(0);
}

/* Primary CTA (form submit buttons), e.g. "Generate" / onboarding submit */
div[data-testid="stFormSubmitButton"] button,
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-blue), var(--accent-purple), var(--accent-pink)) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 0.92rem !important;
    padding: 0.55rem 1.6rem !important;
    box-shadow: 0 6px 22px rgba(167, 139, 250, 0.35) !important;
}
div[data-testid="stFormSubmitButton"] button:hover,
.stButton > button[kind="primary"]:hover {
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 10px 32px rgba(167, 139, 250, 0.5) !important;
}


/* ==========================================================================
   TOPIC CHIPS  (components.render_topic_chips -> key="topic-chips")
   Colorful, cycling per-chip accent colors using nth-of-type on the
   column wrapper produced by st.columns().
   ========================================================================== */
.st-key-topic-chips {
    margin: 0.75rem 0 0.25rem;
}
.chip-label {
    color: var(--text-secondary);
    font-size: 0.85rem;
    font-weight: 500;
    margin-bottom: 0.5rem;
}
.st-key-topic-chips .stButton > button {
    width: 100%;
    border-radius: 999px;
    font-size: 0.82rem;
    padding: 0.35rem 0.9rem;
    white-space: nowrap;
}

/* Color-cycle every 6 chips: blue, purple, pink, cyan, amber, green */
.st-key-topic-chips div[data-testid="stColumn"]:nth-of-type(6n+1) .stButton > button {
    border-color: rgba(96, 165, 250, 0.35); color: var(--accent-blue);
}
.st-key-topic-chips div[data-testid="stColumn"]:nth-of-type(6n+2) .stButton > button {
    border-color: rgba(167, 139, 250, 0.35); color: var(--accent-purple);
}
.st-key-topic-chips div[data-testid="stColumn"]:nth-of-type(6n+3) .stButton > button {
    border-color: rgba(244, 114, 182, 0.35); color: var(--accent-pink);
}
.st-key-topic-chips div[data-testid="stColumn"]:nth-of-type(6n+4) .stButton > button {
    border-color: rgba(34, 211, 238, 0.35); color: var(--accent-cyan);
}
.st-key-topic-chips div[data-testid="stColumn"]:nth-of-type(6n+5) .stButton > button {
    border-color: rgba(251, 191, 36, 0.35); color: var(--warning);
}
.st-key-topic-chips div[data-testid="stColumn"]:nth-of-type(6n+0) .stButton > button {
    border-color: rgba(52, 211, 153, 0.35); color: var(--success);
}
.st-key-topic-chips .stButton > button:hover {
    background: rgba(255, 255, 255, 0.06);
    transform: translateY(-1px);
}


/* ==========================================================================
   GLASS CARDS  (any st.container(border=True) -- section cards, quiz cards)
   ========================================================================== */
   
/* ============================================================
   STUDY MATERIAL READABLE CARD
============================================================ */

.study-content-card {

    background:
        linear-gradient(
            160deg,
            rgba(8, 10, 18, 0.98),
            rgba(12, 14, 26, 0.99)
        ) !important;

    border:
        1px solid rgba(255,255,255,0.08);

    border-radius:
        22px;

    padding:
        1.8rem;

    backdrop-filter:
        blur(18px);

    box-shadow:
        0 12px 36px rgba(0,0,0,0.45);

    position:
        relative;

    overflow:
        hidden;
}

.study-content-card::before {

    content: "";

    position: absolute;

    top: 0;
    left: 0;
    right: 0;

    height: 4px;

    background:
        linear-gradient(
            90deg,
            #60A5FA,
            #8B5CF6,
            #EC4899,
            #22D3EE
        );
}

.study-header {

    display: flex;
    align-items: center;
    gap: 0.8rem;

    margin-bottom: 1.4rem;
}

.study-title {

    font-size: 1.8rem;
    font-weight: 800;
    color: #FFFFFF;
}

.study-icon {

    font-size: 1.8rem;
}

.study-content {

    color: #F8FAFC;
    font-size: 1.06rem;
    line-height: 2;
    font-weight: 500;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    position: relative;
    overflow: hidden;

    background:
        linear-gradient(
            160deg,
            rgba(8, 10, 20, 0.98) 0%,
            rgba(12, 14, 28, 0.99) 100%
        ) !important;

    border:
        1px solid rgba(255,255,255,0.08) !important;

    border-left:
        4px solid rgba(96,165,250,0.85) !important;

    border-radius:
        18px !important;

    backdrop-filter:
        blur(18px);

    padding:
        1.2rem !important;

    box-shadow:
        0 8px 28px rgba(0,0,0,0.45);

    transition:
        all 0.25s ease;
}

[data-testid="stVerticalBlockBorderWrapper"]::before {
    content: "";

    position: absolute;
    top: 0;
    left: 0;
    right: 0;

    height: 4px;

    background:
        linear-gradient(
            90deg,
            #60A5FA,
            #8B5CF6,
            #EC4899,
            #22D3EE
        );

    opacity: 0.95;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color:
        rgba(167,139,250,0.45) !important;

    box-shadow:
        0 10px 35px rgba(99,102,241,0.25);

    transform:
        translateY(-2px);
}


/* Headings and body copy inside cards */
[data-testid="stVerticalBlockBorderWrapper"] h4 {
    font-family: 'Sora', sans-serif;
    font-size: 1.45rem;
    font-weight: 800;
    margin-bottom: 1rem;
    color: #FFFFFF !important;
}
[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] li,
[data-testid="stVerticalBlockBorderWrapper"] span {
    color: #F8FAFC !important;
    line-height: 1.95;
    font-size: 1.02rem;
    font-weight: 500;
}
[data-testid="stVerticalBlockBorderWrapper"] strong {
    color: #ffffff;
}


/* ==========================================================================
   STUDY MATERIAL ACTION ROW (Copy All / Download TXT / Download PDF)
   (components.render_export_row -> key="export-row")
   ========================================================================== */
.st-key-export-row .stButton > button,
.st-key-export-row .stDownloadButton > button {
    font-size: 0.8rem;
    padding: 0.35rem 0.9rem;
    border-radius: 8px;
    background: rgba(255, 255, 255, 0.03);
}
.st-key-export-row .stDownloadButton > button:hover,
.st-key-export-row .stButton > button:hover {
    border-color: var(--accent-cyan);
    color: var(--accent-cyan);
    background: rgba(34, 211, 238, 0.08);
}


/* ==========================================================================
   PILL-STYLE TAB NAVIGATION
   (components.render_tab_nav -> key="main-tabs")
   Built on st.radio(horizontal=True) so the active tab survives reruns.
   ========================================================================== */
.st-key-main-tabs div[role="radiogroup"] {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 6px;
}
.st-key-main-tabs div[role="radiogroup"] label {
    flex: 1 1 auto;
    display: flex !important;
    align-items: center;
    justify-content: center;
    gap: 0.4rem;
    margin: 0 !important;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.92rem;
    color: var(--text-secondary);
    transition: all 0.2s ease;
    text-align: center;
}
/* Hide the native radio circle, keep only the label text as a "tab" */
.st-key-main-tabs div[role="radiogroup"] label > div:first-child {
    display: none;
}
.st-key-main-tabs div[role="radiogroup"] label:hover {
    background: rgba(255, 255, 255, 0.05);
    color: var(--text-primary);
}
.st-key-main-tabs div[role="radiogroup"] label:has(input:checked) {
    background: linear-gradient(135deg, rgba(96, 165, 250, 0.35), rgba(167, 139, 250, 0.35), rgba(244, 114, 182, 0.30));
    color: #ffffff;
    box-shadow: inset 0 0 0 1px rgba(167, 139, 250, 0.55), 0 4px 20px rgba(99, 102, 241, 0.35);
}


/* ==========================================================================
   SECTION CONTENT CARDS
   (components.render_section_card -> key="section-card-<key>")
   Glass card background so generated text doesn't sit directly on the
   page's gradient/dotted background.
   ========================================================================== */
div[class*="st-key-section-card-"],
.st-key-section-card {
    background: var(--bg-card);
    border: 1px solid var(--border-color) !important;
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    backdrop-filter: blur(14px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
}


/* ==========================================================================
   INPUTS -- premium styling with glow on focus
   ========================================================================== */
.stTextInput input,
.stTextArea textarea {
    background: rgba(255, 255, 255, 0.035) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    padding: 0.7rem 1rem !important;
    font-size: 0.95rem !important;
    transition: all 0.2s ease !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
    border-color: var(--accent-purple) !important;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.18) !important;
}
.stTextInput input::placeholder {
    color: var(--text-muted) !important;
}

/* Selectbox / dropdown */
.stSelectbox [data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.035) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
}
.stSelectbox [data-baseweb="select"] > div:focus-within {
    border-color: var(--accent-purple) !important;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.18) !important;
}


/* ==========================================================================
   SIDEBAR
   ========================================================================== */
[data-testid="stSidebar"] {
    background: rgba(10, 12, 24, 0.92);
    border-right: 1px solid var(--border-color);
}
[data-testid="stSidebar"] .block-container {
    padding-top: 1.25rem;
}

.sidebar-brand-title {
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 1.15rem;
    margin: 0;
    background: linear-gradient(135deg, #93C5FD 0%, #A78BFA 50%, #F0ABFC 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}
.sidebar-brand-subtitle {
    color: var(--text-muted);
    font-size: 0.78rem;
    margin: 0.1rem 0 0.75rem;
}
.sidebar-section-label {
    color: var(--text-secondary);
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin: 1.1rem 0 0.4rem;
}

/* Sidebar dropdowns slightly more compact */
[data-testid="stSidebar"] .stSelectbox label {
    font-size: 0.85rem;
    color: var(--text-secondary);
}

/* History / favorites row buttons rendered as st.button(use_container_width=True) */
.st-key-sidebar-history .stButton > button,
.st-key-sidebar-favorites .stButton > button {
    text-align: left;
    justify-content: flex-start;
    font-size: 0.82rem;
    padding: 0.4rem 0.7rem;
    background: rgba(255, 255, 255, 0.02);
    border-color: var(--border-color);
}
.st-key-sidebar-history .stButton > button:hover,
.st-key-sidebar-favorites .stButton > button:hover {
    border-color: var(--accent-cyan);
    color: var(--accent-cyan);
}

/* "Clear history" danger button */
.st-key-clear-history-btn .stButton > button {
    color: var(--danger);
    border-color: rgba(248, 113, 113, 0.3);
    background: rgba(248, 113, 113, 0.06);
    font-size: 0.8rem;
}
.st-key-clear-history-btn .stButton > button:hover {
    background: rgba(248, 113, 113, 0.16);
    border-color: var(--danger);
    color: var(--danger);
}


/* ==========================================================================
   QUIZ REACTION BADGES
   ========================================================================== */
.quiz-reaction {
    border-radius: 10px;
    padding: 0.6rem 1rem;
    margin: 0.6rem 0;
    font-weight: 600;
    font-size: 0.92rem;
    line-height: 1.5;
    animation: popIn 0.3s ease;
}
.quiz-correct {
    background: rgba(52, 211, 153, 0.10);
    color: var(--success);
    border: 1px solid rgba(52, 211, 153, 0.30);
}
.quiz-partial {
    background: rgba(251, 191, 36, 0.10);
    color: var(--warning);
    border: 1px solid rgba(251, 191, 36, 0.30);
}
.quiz-incorrect, .quiz-empty {
    background: rgba(248, 113, 113, 0.10);
    color: var(--danger);
    border: 1px solid rgba(248, 113, 113, 0.30);
}
.quiz-reference {
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-top: 0.3rem;
    line-height: 1.6;
}


/* ==========================================================================
   ANIMATIONS
   ========================================================================== */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(16px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes popIn {
    from { opacity: 0; transform: scale(0.96); }
    to { opacity: 1; transform: scale(1); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 28px rgba(99, 102, 241, 0.28), inset 0 0 18px rgba(96, 165, 250, 0.10); }
    50%      { box-shadow: 0 0 48px rgba(167, 139, 250, 0.48), inset 0 0 32px rgba(96, 165, 250, 0.22); }
}
@keyframes pulseScale {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.12); }
}
@keyframes floatY {
    0%, 100% { transform: translateY(0); }
    50%      { transform: translateY(-8px); }
}
@keyframes floatUp {
    0%   { transform: translateY(15vh) translateX(0) rotate(0deg); opacity: 0; }
    10%  { opacity: 0.65; }
    90%  { opacity: 0.5; }
    100% { transform: translateY(-95vh) translateX(20px) rotate(25deg); opacity: 0; }
}


/* ==========================================================================
   SCROLLBAR
   ========================================================================== */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.12);
    border-radius: 8px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(167, 139, 250, 0.4);
}


/* ==========================================================================
   RESPONSIVE / MOBILE
   ========================================================================== */
@media (max-width: 768px) {
    .hero-title { font-size: 2.1rem; }
    .hero-subtitle { font-size: 0.92rem; }
    .hero-icon-wrapper { width: 76px; height: 76px; font-size: 2rem; }

    .onboarding-card { padding: 1.75rem 1.25rem; }
    .onboarding-title { font-size: 1.6rem; }

    

    .st-key-main-tabs div[role="radiogroup"] label {
        font-size: 0.82rem;
        padding: 0.45rem 0.6rem;
        flex: 1 1 45%;
    }

    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }

    /* Mobile: stack compare columns */
    .compare-table-wrapper { overflow-x: auto; }

    /* Mobile: hide chip carousel overflow cleanly */
    .chip-carousel-track { gap: 0.5rem; }
}


/* ==========================================================================
   LIGHT THEME  (toggled by adding class "light-theme" to .stApp)
   When the user toggles light mode, app.py injects a small <style> block
   that overrides these CSS variables. All components use var() so they
   automatically pick up the overrides.
   ========================================================================== */
.light-theme {
    --bg-deep: #F0F4FF;
    --bg-card: rgba(255, 255, 255, 0.90);
    --bg-card-hover: rgba(255, 255, 255, 0.98);
    --border-color: rgba(0, 0, 0, 0.08);
    --border-glow: rgba(109, 40, 217, 0.35);
    --text-primary: #0F172A;
    --text-secondary: #475569;
    --text-muted: #94A3B8;
    background-color: #F0F4FF !important;
    background-image:
        radial-gradient(ellipse 70% 45% at 15% -5%, rgba(96, 165, 250, 0.10), transparent 60%),
        radial-gradient(ellipse 60% 45% at 95% 5%, rgba(167, 139, 250, 0.10), transparent 60%) !important;
}
.light-theme .stApp { color: #0F172A; }
.light-theme [data-testid="stSidebar"] {
    background: rgba(240, 244, 255, 0.96) !important;
    border-right: 1px solid rgba(0,0,0,0.08) !important;
}
.light-theme .stTextInput input,
.light-theme .stTextArea textarea {
    background: rgba(0, 0, 0, 0.03) !important;
    color: #0F172A !important;
    border-color: rgba(0,0,0,0.12) !important;
}


/* ==========================================================================
   THEME TOGGLE BUTTON  (in sidebar)
   ========================================================================== */
.st-key-theme-toggle .stButton > button {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid var(--border-color);
    border-radius: 10px;
    color: var(--text-secondary);
    font-size: 0.82rem;
    padding: 0.35rem 0.75rem;
    width: 100%;
    text-align: left;
    transition: all 0.2s ease;
}
.st-key-theme-toggle .stButton > button:hover {
    border-color: var(--accent-purple);
    color: var(--accent-purple);
}


/* ==========================================================================
   STREAK DISPLAY  (components.render_streak -> key="streak-display")
   ========================================================================== */
.streak-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: linear-gradient(135deg, rgba(251,191,36,0.15), rgba(248,113,113,0.10));
    border: 1px solid rgba(251,191,36,0.30);
    border-radius: 20px;
    padding: 0.28rem 0.75rem;
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--warning);
    margin-bottom: 0.5rem;
    animation: pulseScale 2.5s ease-in-out infinite;
}
.streak-badge.streak-zero {
    background: rgba(255,255,255,0.04);
    border-color: var(--border-color);
    color: var(--text-muted);
    animation: none;
}


/* ==========================================================================
   ANIMATED CHIP CAROUSEL  (components.render_topic_chips)
   ========================================================================== */
.chip-carousel-wrapper {
    overflow: hidden;
    width: 100%;
    mask-image: linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%);
    -webkit-mask-image: linear-gradient(to right, transparent 0%, black 6%, black 94%, transparent 100%);
}
.chip-carousel-track {
    display: flex;
    gap: 0.65rem;
    animation: chipScroll 28s linear infinite;
    width: max-content;
}
.chip-carousel-track:hover {
    animation-play-state: paused;
}
@keyframes chipScroll {
    0%   { transform: translateX(0); }
    100% { transform: translateX(-50%); }
}


/* ==========================================================================
   GENERATION PROGRESS INDICATOR
   (components.render_progress_indicator -> key="gen-progress")
   ========================================================================== */
.st-key-gen-progress {
    padding: 1.25rem;
    border-radius: 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    margin: 0.75rem 0;
}
.progress-step {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.35rem 0;
    font-size: 0.88rem;
    color: var(--text-muted);
    transition: color 0.3s ease;
}
.progress-step.active {
    color: var(--accent-purple);
    font-weight: 600;
}
.progress-step.done {
    color: var(--success);
}
.progress-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: currentColor;
    flex-shrink: 0;
}
.progress-step.active .progress-dot {
    animation: pulseScale 1s ease-in-out infinite;
}


/* ==========================================================================
   FOLLOW-UP QUESTION INPUT
   (components.render_followup_input -> key="followup-section")
   ========================================================================== */
.st-key-followup-section {
    margin-top: 1rem;
    padding: 1rem 1.25rem;
    border-radius: 14px;
    background: rgba(96, 165, 250, 0.05);
    border: 1px solid rgba(96, 165, 250, 0.15);
}
.followup-label {
    font-size: 0.82rem;
    color: var(--accent-blue);
    font-weight: 600;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}


/* ==========================================================================
   TOPIC NOTES / ANNOTATIONS
   (components.render_notes_section -> key="notes-section-<slug>")
   ========================================================================== */
div[class*="st-key-notes-section-"] {
    margin-top: 1rem;
    padding: 1rem 1.25rem;
    border-radius: 14px;
    background: rgba(167, 139, 250, 0.05);
    border: 1px dashed rgba(167, 139, 250, 0.25);
}
.notes-label {
    font-size: 0.82rem;
    color: var(--accent-purple);
    font-weight: 600;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}


/* ==========================================================================
   STUDY SCHEDULE / SPACED REPETITION PANEL
   (components.render_study_schedule -> key="study-schedule")
   ========================================================================== */
.st-key-study-schedule {
    padding: 1rem 1.25rem;
    border-radius: 14px;
    background: rgba(34, 211, 238, 0.05);
    border: 1px solid rgba(34, 211, 238, 0.15);
    margin-bottom: 1rem;
}
.schedule-item {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid var(--border-color);
}
.schedule-item:last-child { border-bottom: none; }
.schedule-topic {
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text-primary);
}
.schedule-reason {
    font-size: 0.8rem;
    color: var(--text-muted);
}


/* ==========================================================================
   COMPARE MODE
   (components.render_compare_result -> key="compare-result")
   ========================================================================== */
.st-key-compare-result {
    animation: fadeInUp 0.5s ease;
}
.compare-header {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1rem;
}
.compare-topic-badge {
    flex: 1;
    text-align: center;
    padding: 0.5rem 1rem;
    border-radius: 10px;
    font-weight: 700;
    font-size: 1rem;
}
.compare-topic-badge.topic-a {
    background: rgba(96, 165, 250, 0.12);
    border: 1px solid rgba(96, 165, 250, 0.30);
    color: var(--accent-blue);
}
.compare-topic-badge.topic-b {
    background: rgba(167, 139, 250, 0.12);
    border: 1px solid rgba(167, 139, 250, 0.30);
    color: var(--accent-purple);
}
.compare-vs {
    font-weight: 800;
    font-size: 1.1rem;
    color: var(--text-muted);
}

/* Compare Mode section cards */
div[class*="st-key-compare-card-"] {
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 0.75rem;
    backdrop-filter: blur(12px);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
}
div[class*="st-key-compare-card-"]:hover {
    border-color: rgba(167, 139, 250, 0.30);
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.12);
}
.compare-section-title {
    font-family: 'Sora', sans-serif;
    font-size: 0.78rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--accent-purple);
    margin-bottom: 0.6rem;
}

/* Diff table inside Compare Mode -- style markdown tables */
div[class*="st-key-compare-card-differences"] table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.88rem;
}
div[class*="st-key-compare-card-differences"] th {
    background: rgba(167, 139, 250, 0.12);
    color: var(--accent-purple);
    padding: 0.5rem 0.75rem;
    text-align: left;
    font-weight: 600;
    border-bottom: 1px solid rgba(167, 139, 250, 0.25);
}
div[class*="st-key-compare-card-differences"] td {
    padding: 0.45rem 0.75rem;
    border-bottom: 1px solid var(--border-color);
    color: var(--text-secondary);
    vertical-align: top;
}
div[class*="st-key-compare-card-differences"] tr:hover td {
    background: rgba(255,255,255,0.02);
}


/* ==========================================================================
   ANIMATED GRADIENT BORDER -- premium "glow" card effect
   Applied to section cards on hover via the .glow-border class
   (components.py adds this class to container cards)
   ========================================================================== */
@property --border-angle {
    syntax: '<angle>';
    inherits: false;
    initial-value: 0deg;
}
@keyframes rotateBorder {
    to { --border-angle: 360deg; }
}
.glow-border {
    position: relative;
    border-radius: 16px;
}
.glow-border::before {
    content: '';
    position: absolute;
    inset: -1px;
    border-radius: 17px;
    background: conic-gradient(
        from var(--border-angle),
        rgba(96,165,250,0) 0%,
        rgba(96,165,250,0.6) 25%,
        rgba(167,139,250,0.6) 50%,
        rgba(244,114,182,0.6) 75%,
        rgba(96,165,250,0) 100%
    );
    animation: rotateBorder 4s linear infinite;
    z-index: 0;
    opacity: 0;
    transition: opacity 0.3s ease;
}
.glow-border:hover::before {
    opacity: 1;
}
.glow-border > * {
    position: relative;
    z-index: 1;
}


/* ==========================================================================
   ONBOARDING TOUR TOOLTIPS
   (injected via st.html when user first logs in)
   ========================================================================== */
.tour-tooltip {
    position: fixed;
    z-index: 9999;
    background: var(--bg-card);
    border: 1px solid var(--border-glow);
    border-radius: 14px;
    padding: 0.85rem 1.1rem;
    max-width: 260px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.35), 0 0 0 1px rgba(167,139,250,0.2);
    animation: fadeInUp 0.4s ease;
    backdrop-filter: blur(16px);
}
.tour-tooltip-title {
    font-weight: 700;
    font-size: 0.9rem;
    color: var(--accent-purple);
    margin-bottom: 0.3rem;
}
.tour-tooltip-body {
    font-size: 0.82rem;
    color: var(--text-secondary);
    line-height: 1.5;
}
.tour-tooltip-arrow {
    font-size: 0.75rem;
    color: var(--text-muted);
    margin-top: 0.5rem;
    cursor: pointer;
    text-align: right;
}
.tour-tooltip-arrow:hover {
    color: var(--accent-purple);
}


/* ==========================================================================
   KEYBOARD SHORTCUT HINTS
   Shown as small <kbd> tags in tooltips and button labels
   ========================================================================== */
kbd {
    display: inline-block;
    padding: 0.1rem 0.4rem;
    font-family: 'Inter', monospace;
    font-size: 0.72rem;
    color: var(--text-secondary);
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-bottom-width: 2px;
    border-radius: 5px;
    line-height: 1.4;
    white-space: nowrap;
}


/* ==========================================================================
   VOICE INPUT BUTTON
   (components.render_voice_input -> key="voice-input-section")
   ========================================================================== */
.st-key-voice-input-section {
    margin-top: 0.5rem;
}
.voice-hint {
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 0.25rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}


/* ==========================================================================
   AUTO-DIFFICULTY BADGE
   Shown next to difficulty dropdown when auto-detect fires
   ========================================================================== */
.auto-diff-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--accent-cyan);
    background: rgba(34,211,238,0.08);
    border: 1px solid rgba(34,211,238,0.20);
    border-radius: 20px;
    padding: 0.15rem 0.6rem;
    margin-left: 0.5rem;
    vertical-align: middle;
}


/* ==========================================================================
   LOGIN PAGE
   (storage.render_login_page uses this via inline styles + st.html)
   ========================================================================== */
.st-key-login-page {
    min-height: 75vh;
    display: flex;
    align-items: center;
    justify-content: center;
}
.login-card {
    max-width: 420px;
    margin: 0 auto;
    text-align: center;
    padding: 3rem 2.5rem;
    border-radius: 28px;
    background: var(--bg-card);
    border: 1px solid var(--border-color);
    backdrop-filter: blur(20px);
    box-shadow: 0 0 60px rgba(99,102,241,0.14), 0 24px 60px rgba(0,0,0,0.40);
    animation: fadeInUp 0.7s ease;
}
.login-app-icon {
    font-size: 3rem;
    margin-bottom: 0.75rem;
    display: inline-block;
    animation: floatY 3s ease-in-out infinite;
}
.login-title {
    font-family: 'Sora', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #93C5FD, #A78BFA, #F0ABFC);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    margin-bottom: 0.4rem;
}
.login-subtitle {
    color: var(--text-secondary);
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 2rem;
}
.login-privacy-note {
    font-size: 0.72rem;
    color: var(--text-muted);
    margin-top: 1rem;
    line-height: 1.5;
}


/* ==========================================================================
   PDF UPLOAD SECTION
   (components.render_pdf_upload -> key="pdf-upload-section")
   ========================================================================== */
.st-key-pdf-upload-section {
    padding: 1rem 1.25rem;
    border-radius: 14px;
    background: rgba(244,114,182,0.04);
    border: 1px dashed rgba(244,114,182,0.20);
    margin-bottom: 0.75rem;
}
.pdf-upload-label {
    font-size: 0.82rem;
    color: var(--accent-pink);
    font-weight: 600;
    margin-bottom: 0.4rem;
}


/* ==========================================================================
   SCORE SUMMARY  (after attempting quiz)
   (components._render_score_summary)
   ========================================================================== */
.score-summary-bar {
    height: 8px;
    border-radius: 8px;
    background: rgba(255,255,255,0.06);
    overflow: hidden;
    margin: 0.5rem 0 0.75rem;
}
.score-summary-fill {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-purple));
    transition: width 0.6s ease;
}

</style>
"""


def inject_custom_css() -> None:
    """Inject the full custom CSS theme into the current page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)