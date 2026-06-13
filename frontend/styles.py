"""
frontend/styles.py

All custom CSS for the AI Study Assistant's premium, futuristic, colorful
dark theme -- deep-space gradients, glassmorphism cards, glowing accents,
pill-style tabs, a styled sidebar, and a secret romantic "reveal" screen.

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
    text-align: center;
    padding: 1.5rem 1rem 0.5rem;
    animation: fadeInUp 0.7s ease;
}

.hero-icon-wrapper {
    width: 96px;
    height: 96px;
    margin: 0 auto 0.75rem;
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
    margin: 0 auto 0.5rem;
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
   SECRET ROMANTIC REVEAL SCREEN
   (components.render_bhabhi_reveal -> key="bhabhi-reveal")
   ========================================================================== */
.st-key-bhabhi-reveal {
    position: relative;
    min-height: 70vh;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 28px;
    overflow: hidden;
    padding: 2.5rem 1rem;
    background:
        radial-gradient(ellipse 60% 50% at 25% 15%, rgba(244, 114, 182, 0.35), transparent 60%),
        radial-gradient(ellipse 55% 50% at 80% 85%, rgba(167, 139, 250, 0.30), transparent 60%),
        linear-gradient(160deg, #2A0E2E 0%, #4A1942 55%, #2A0E2E 100%);
    animation: fadeInUp 0.8s ease;
}

/* Floating heart/sparkle particles -- rendered as plain spans by
   components.render_bhabhi_reveal, positioned via inline style */
.romantic-particle {
    position: absolute;
    font-size: 1.4rem;
    opacity: 0;
    pointer-events: none;
    animation: floatUp 9s linear infinite;
}

.romantic-card {
    position: relative;
    z-index: 2;
    max-width: 560px;
    width: 100%;
    margin: 0 auto;
    text-align: center;
    padding: 2.75rem 2rem;
    border-radius: 24px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(244, 114, 182, 0.35);
    backdrop-filter: blur(16px);
    box-shadow: 0 0 60px rgba(244, 114, 182, 0.25), 0 20px 60px rgba(0, 0, 0, 0.4);
}

.romantic-hearts {
    font-size: 2.1rem;
    margin-bottom: 0.5rem;
    animation: pulseScale 2.2s ease-in-out infinite;
}

.romantic-title {
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 2rem;
    margin: 0.2rem 0 0.9rem;
    line-height: 1.3;
    background: linear-gradient(135deg, #ffffff 0%, #F9A8D4 60%, #F472B6 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.romantic-divider {
    width: 80px;
    height: 1px;
    margin: 0 auto 0.9rem;
    background: linear-gradient(90deg, transparent, rgba(244, 114, 182, 0.6), transparent);
}

.romantic-subtitle {
    color: #F9D7EA;
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0 0 0.6rem;
}

.romantic-text {
    color: rgba(255, 255, 255, 0.82);
    line-height: 1.7;
    font-size: 0.98rem;
    margin: 0 0 1.6rem;
}

/* The "Enter Study Space" button, scoped via key="bhabhi-enter-btn" */
.st-key-bhabhi-enter-btn .stButton button {
    background: linear-gradient(135deg, #F472B6, #EC4899) !important;
    border: none !important;
    color: #fff !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.65rem 2rem !important;
    border-radius: 999px !important;
    box-shadow: 0 8px 24px rgba(244, 114, 182, 0.4) !important;
}
.st-key-bhabhi-enter-btn .stButton button:hover {
    transform: translateY(-2px) scale(1.02);
    box-shadow: 0 12px 32px rgba(244, 114, 182, 0.55) !important;
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

    .romantic-card { padding: 1.75rem 1.25rem; }
    .romantic-title { font-size: 1.5rem; }

    .st-key-main-tabs div[role="radiogroup"] label {
        font-size: 0.82rem;
        padding: 0.45rem 0.6rem;
        flex: 1 1 45%;
    }

    .block-container {
        padding-left: 0.75rem !important;
        padding-right: 0.75rem !important;
    }
}

</style>
"""


def inject_custom_css() -> None:
    """Inject the full custom CSS theme into the current page."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)