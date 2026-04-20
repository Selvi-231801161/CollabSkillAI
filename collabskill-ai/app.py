# app.py  —  CollabSkill AI  |  Professional Production Build
import streamlit as st
import pandas as pd
from database import init_db, db_fetchone, db_fetchall, db_execute
from auth import (register_user, login_user, get_user,
                  update_profile, update_avatar_color, update_avatar_photo,
                  update_trust_score, get_top_users, AVATAR_COLORS)
from tasks_db import (
    create_task, get_all_open_tasks, get_my_tasks, get_all_tasks_admin,
    update_task_status, delete_task, apply_to_task,
    get_my_applications, get_feedback_for_user,
    submit_feedback, add_notification, get_notifications,
    get_unread_count, mark_all_read,
    CATEGORIES, KNOWLEDGE_TOPICS,
    TYPE_TASK, TYPE_KNOWLEDGE,
    INTENT_LEARN, INTENT_TEACH,
    SKILL_CATEGORIES, SKILLS_BY_CATEGORY,
)
from ai_matching import (
    match_users_to_task, recommend_tasks_for_user,
    recommend_users_for_collaboration,
)
from badges     import assign_badges, render_badges_html, compute_trust_score
from network    import (send_request, accept_request, reject_request,
                        get_connection_status, get_incoming_requests,
                        get_my_network, get_connection_count)
from chat       import (send_message, get_messages, get_conversations,
                        send_group_message, get_group_messages,
                        create_group, add_member_to_group, get_user_groups,
                        get_group_members)
from project_db import (create_project, get_project, get_my_projects,
                        send_project_invite, get_pending_invites,
                        accept_project_invite, reject_project_invite,
                        get_project_members, is_project_member,
                        add_resource, get_resources, update_project_chat)
from learning   import (express_interest, get_interested_teachers,
                        get_interest_count, accept_teacher, reject_interest,
                        get_accepted_pair, is_teacher_accepted,
                        is_learner_accepted, get_interested_learners,
                        accept_learner,
                        get_my_teaching_pairs, get_my_learning_pairs)
from sessions   import (book_session, get_my_sessions,
                        get_upcoming_sessions, get_past_sessions,
                        mark_session_complete, count_sessions)

init_db()

# ── Init extended tables ──────────────────────────────────────
try:
    from database import init_extended_tables
    init_extended_tables()
except Exception:
    pass

st.set_page_config(
    page_title="CollabSkill AI",
    page_icon="C",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session state ─────────────────────────────────────────────
for k, v in {
    "page":           "landing",
    "user":           None,
    "history":        [],
    "ai_matches":     [],
    "ai_done":        False,
    "mode":           "work",
    "know_intent":    INTENT_LEARN,
    "chat_partner":   None,
    "chat_group":     None,
    "active_project": None,
    "book_post_id":    None,
    "book_teacher_id": None,
    "book_learner_id": None,  # set when teacher books from their TEACH post
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════
#  NAVIGATION
# ═══════════════════════════════════════════════════════════════
def go(page):
    if st.session_state.page != page:
        st.session_state.history.append(st.session_state.page)
    st.session_state.page = page
    st.rerun()

def go_back():
    if st.session_state.history:
        st.session_state.page = st.session_state.history.pop()
    else:
        st.session_state.page = "landing"
    st.rerun()

def require_login():
    if not st.session_state.user:
        go("login")

def require_admin():
    if not st.session_state.user:
        go("login")
    elif st.session_state.user.get("role") != "admin":
        go("dashboard")

def is_admin():
    return (st.session_state.user or {}).get("role") == "admin"

def logged_in():
    return st.session_state.user is not None

def is_learn_mode():
    return st.session_state.get("mode", "work") == "learn"


# ═══════════════════════════════════════════════════════════════
#  CSS  —  Clean Professional White SaaS Theme
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ══ ANIMATIONS ═════════════════════════════════════════════ */
@keyframes fadeIn {
    from { opacity:0; transform:translateY(6px); }
    to   { opacity:1; transform:translateY(0); }
}
.main .block-container { animation: fadeIn 0.3s ease-in-out; }

/* ══ BASE & RESET ═══════════════════════════════════════════ */
header, #MainMenu, footer { visibility: hidden; }
.block-container {
    padding-top: 0 !important;
    max-width: 1300px;
    padding-bottom: 60px !important;
}
html, body, .stApp, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #FFFFFF !important;
    color: #111827 !important;
}
.stApp { background-color: #FFFFFF !important; }

/* ══ INPUTS ═════════════════════════════════════════════════ */
.stTextInput input, .stTextArea textarea {
    background: #FFFFFF !important;
    color: #111827 !important;
    border: 1.5px solid #D1D5DB !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    font-weight: 400 !important;
    padding: 10px 14px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,.04) !important;
    transition: all 0.2s ease-in-out !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #3B82F6 !important;
    box-shadow: 0 0 0 3px rgba(59,130,246,.12) !important;
    outline: none !important;
}
input::placeholder, textarea::placeholder { color: #9CA3AF !important; }

/* ══ SELECTBOX ══════════════════════════════════════════════ */
.stSelectbox > div > div {
    background: #FFFFFF !important;
    color: #111827 !important;
    border: 1.5px solid #D1D5DB !important;
    border-radius: 10px !important;
    box-shadow: 0 1px 2px rgba(0,0,0,.04) !important;
}
.stSelectbox [data-baseweb="select"]   { cursor: pointer !important; }
.stSelectbox [data-baseweb="select"] * { cursor: pointer !important; }
[data-baseweb="popover"] {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 10px !important;
    box-shadow: 0 8px 24px rgba(0,0,0,.10) !important;
}
[data-baseweb="option"] { color: #111827 !important; background: #FFFFFF !important; }
[data-baseweb="option"]:hover { background: #EFF6FF !important; color: #3B82F6 !important; }

/* ══ LABELS ═════════════════════════════════════════════════ */
label, .stTextInput label, .stTextArea label,
.stSelectbox label, .stSlider label, .stCheckbox label {
    color: #6B7280 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    letter-spacing: .08em !important;
    text-transform: uppercase !important;
}

/* ══ BUTTONS ════════════════════════════════════════════════ */
/* Form submit — blue accent */
.stFormSubmitButton > button {
    background: #3B82F6 !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 22px !important;
    height: 42px !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 2px 8px rgba(59,130,246,.28) !important;
}
.stFormSubmitButton > button:hover {
    background: #2563EB !important;
    transform: scale(1.02) !important;
    box-shadow: 0 4px 16px rgba(59,130,246,.40) !important;
}

/* Regular buttons */
.stButton > button {
    background: #F9FAFB !important;
    color: #374151 !important;
    border: 1.5px solid #E5E7EB !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 8px 16px !important;
    height: 38px !important;
    line-height: 1.2 !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    transition: all 0.2s ease-in-out !important;
    box-shadow: 0 1px 2px rgba(0,0,0,.05) !important;
}
.stButton > button:hover {
    background: #F3F4F6 !important;
    color: #111827 !important;
    border-color: #D1D5DB !important;
    box-shadow: 0 2px 8px rgba(0,0,0,.08) !important;
}

/* Accent button — blue */
.btn-accent .stButton > button {
    background: #3B82F6 !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 2px 8px rgba(59,130,246,.28) !important;
}
.btn-accent .stButton > button:hover {
    background: #2563EB !important;
    transform: scale(1.02) !important;
    box-shadow: 0 4px 16px rgba(59,130,246,.40) !important;
}

/* Danger button */
.btn-danger .stButton > button {
    background: #FFF5F5 !important;
    color: #DC2626 !important;
    border: 1.5px solid #FECACA !important;
    box-shadow: none !important;
}
.btn-danger .stButton > button:hover {
    background: #FEE2E2 !important;
    border-color: #FCA5A5 !important;
}

/* ══ METRICS ════════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: transparent !important;
    border: none !important;
    padding: 10px 10px !important;
   
    box-shadow: none !important;
    
}
[data-testid="metric-container"]:hover {
    box-shadow: 0 6px 20px rgba(0,0,0,.10) !important;
    transform: translateY(-2px) !important;
    
}
[data-testid="metric-container"] label {
    color: #6B7280 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
}
[data-testid="stMetricValue"] {
    color: #3B82F6 !important;
    font-size: 26px !important;
    font-weight: 800 !important;
}
div[data-testid="stHorizontalBlock"] {
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

div[data-testid="stHorizontalBlock"] > div {
    background: transparent !important;
}
section.main > div {
    background: transparent !important;
}

/* Remove inner container spacing */
section.main > div > div {
    background: transparent !important;
    padding-bottom: 0 !important;
    margin-bottom: 0 !important;
}

/* ══ EXPANDER ═══════════════════════════════════════════════ */
.streamlit-expanderHeader {
    background: #FFFFFF !important;
    border: 1px solid #E5E7EB !important;
    border-radius: 12px !important;
    color: #111827 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    padding: 12px 18px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,.04) !important;
    transition: all 0.2s ease-in-out !important;
}
.streamlit-expanderHeader:hover {
    border-color: #D1D5DB !important;
    box-shadow: 0 3px 10px rgba(0,0,0,.08) !important;
}
.streamlit-expanderContent {
    background: #F9FAFB !important;
    border: 1px solid #E5E7EB !important;
    border-top: none !important;
    border-radius: 0 0 12px 12px !important;
}

/* ══ SIDEBAR ════════════════════════════════════════════════ */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E5E7EB !important;
    box-shadow: 2px 0 8px rgba(0,0,0,.04) !important;
}
[data-testid="stSidebar"] * { color: #374151 !important; }

/* ══ TABS ═══════════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 2px solid #E5E7EB !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #6B7280 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 20px !important;
    transition: all 0.2s ease-in-out !important;
}
.stTabs [data-baseweb="tab"]:hover { color: #3B82F6 !important; }
.stTabs [aria-selected="true"] {
    color: #3B82F6 !important;
    border-bottom-color: #3B82F6 !important;
}

/* ══ MISC ═══════════════════════════════════════════════════ */
.stCheckbox > label > div { border-color: #D1D5DB !important; }
hr { border-color: #E5E7EB !important; margin: 20px 0 !important; }
.stSlider [data-baseweb="slider"] { background: #E5E7EB !important; }
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; border: 1px solid #E5E7EB !important; }
.stColorPicker label { color: #6B7280 !important; }

/* ══ CARDS ══════════════════════════════════════════════════ */
.cs-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 20px 22px;
    margin-bottom: 12px;
    box-shadow: 0 1px 6px rgba(0,0,0,.06);
    transition: all 0.2s ease-in-out;
}
.cs-card:hover {
    border-color: #D1D5DB;
    box-shadow: 0 6px 24px rgba(0,0,0,.10);
    transform: translateY(-2px);
}

/* ══ BADGES — light pill ════════════════════════════════════ */
.cs-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: .02em;
    margin: 2px 3px 2px 0;
}
.badge-green  { background: #DCFCE7; color: #16A34A; border: 1px solid #BBF7D0; }
.badge-amber  { background: #FEF9C3; color: #CA8A04; border: 1px solid #FEF08A; }
.badge-red    { background: #FEE2E2; color: #DC2626; border: 1px solid #FECACA; }
.badge-cyan   { background: #E0F2FE; color: #0284C7; border: 1px solid #BAE6FD; }
.badge-violet { background: #EDE9FE; color: #7C3AED; border: 1px solid #DDD6FE; }
.badge-slate  { background: #F3F4F6; color: #6B7280; border: 1px solid #E5E7EB; }
.badge-teal   { background: #CCFBF1; color: #0D9488; border: 1px solid #99F6E4; }
.badge-blue   { background: #EFF6FF; color: #3B82F6; border: 1px solid #BFDBFE; }
.badge-learn  { background: #CCFBF1; color: #0D9488; border: 1px solid #99F6E4; }
.badge-teach  { background: #F3E8FF; color: #9333EA; border: 1px solid #E9D5FF; }

/* ══ TYPOGRAPHY ═════════════════════════════════════════════ */
.page-title {
    font-size: 22px; font-weight: 800;
    color: #111827; letter-spacing: -.02em; margin-bottom: 4px;
}
.page-sub { color: #6B7280; font-size: 13px; margin-bottom: 20px; }

/* ══ TRUST BAR ══════════════════════════════════════════════ */
.trust-bar-bg   { background: #E5E7EB; border-radius: 999px; height: 6px; margin-top: 6px; }
.trust-bar-fill { height: 6px; border-radius: 999px; background: linear-gradient(90deg,#3B82F6,#8B5CF6); }

/* ══ ADMIN BANNER ═══════════════════════════════════════════ */
.admin-banner {
    background: #FFF1F2; border: 1px solid #FECDD3;
    border-radius: 10px; padding: 10px 16px;
    color: #BE123C; font-size: 12px; font-weight: 500; margin-bottom: 16px;
}

/* ══ MODE PILLS ═════════════════════════════════════════════ */
.mode-pill-work {
    display: inline-flex; align-items: center; gap: 6px;
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-radius: 999px; padding: 5px 14px;
    color: #3B82F6; font-size: 11px; font-weight: 700;
    letter-spacing: .06em; text-transform: uppercase; margin-bottom: 16px;
}
.mode-pill-learn {
    display: inline-flex; align-items: center; gap: 6px;
    background: #F0FDFA; border: 1px solid #99F6E4;
    border-radius: 999px; padding: 5px 14px;
    color: #0D9488; font-size: 11px; font-weight: 700;
    letter-spacing: .06em; text-transform: uppercase; margin-bottom: 16px;
}

/* ══ NAVBAR — Clean white, first stHorizontalBlock ══════════ */
div[data-testid="stHorizontalBlock"]:first-of-type {
    background: #FFFFFF !important;
    border-bottom: 1px solid #E5E7EB !important;
    box-shadow: 0 1px 0 #F3F4F6, 0 2px 12px rgba(0,0,0,.06) !important;
    padding: 0 16px !important;
    margin-bottom: 28px !important;
    align-items: center !important;
    min-height: 60px !important;
    position: sticky !important;
    top: 0 !important;
    z-index: 9999 !important;
}
div[data-testid="stHorizontalBlock"]:first-of-type
    > div[data-testid="column"] {
    padding: 0 1px !important;
    display: flex !important;
    align-items: center !important;
}
/* All nav links */
div[data-testid="stHorizontalBlock"]:first-of-type
    .stButton > button {
    background: transparent !important;
    color: #6B7280 !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-weight: 500 !important;
    font-size: 13.5px !important;
    padding: 7px 12px !important;
    height: 40px !important;
    white-space: nowrap !important;
    overflow: visible !important;
    text-overflow: clip !important;
    box-shadow: none !important;
    min-width: max-content !important;
    width: 100% !important;
    letter-spacing: .01em !important;
    transition: background .18s ease, color .18s ease !important;
}
div[data-testid="stHorizontalBlock"]:first-of-type
    .stButton > button:hover {
    background: #F9FAFB !important;
    color: #111827 !important;
    border: none !important;
    box-shadow: none !important;
}
/* Logo (first col) */
div[data-testid="stHorizontalBlock"]:first-of-type
    > div[data-testid="column"]:first-child .stButton > button {
    font-size: 16px !important;
    font-weight: 800 !important;
    color: #111827 !important;
    letter-spacing: -.03em !important;
    padding: 7px 20px 7px 4px !important;
    background: transparent !important;
}
div[data-testid="stHorizontalBlock"]:first-of-type
    > div[data-testid="column"]:first-child .stButton > button:hover {
    background: transparent !important;
    color: #3B82F6 !important;
}
/* Sign Out (last col) */
div[data-testid="stHorizontalBlock"]:first-of-type
    > div[data-testid="column"]:last-child .stButton > button {
    color: #DC2626 !important;
    border: 1.5px solid #FECACA !important;
    padding: 6px 14px !important;
    background: #FFF5F5 !important;
}
div[data-testid="stHorizontalBlock"]:first-of-type
    > div[data-testid="column"]:last-child .stButton > button:hover {
    background: #FEE2E2 !important;
    border-color: #FCA5A5 !important;
    color: #B91C1C !important;
}

/* ══ HERO ════════════════════════════════════════════════════ */
.hero-wrap { text-align: center; padding: 64px 0 40px; }
.hero-eyebrow {
    display: inline-block; font-size: 10px; font-weight: 700;
    letter-spacing: .18em; text-transform: uppercase; color: #3B82F6;
    background: #EFF6FF; border: 1px solid #BFDBFE;
    border-radius: 999px; padding: 5px 16px; margin-bottom: 28px;
}
.hero-h1 {
    font-size: clamp(36px, 5.5vw, 64px);
    font-weight: 900; line-height: 1.06;
    letter-spacing: -.04em; color: #111827; margin: 0;
}
.hero-gradient {
    font-size: clamp(36px, 5.5vw, 64px);
    font-weight: 900; line-height: 1.06; letter-spacing: -.04em;
    background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 55%, #EC4899 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero-sub {
    font-size: 16px; color: #6B7280; line-height: 1.75;
    max-width: 520px; margin: 20px auto 0;
}

/* ══ MODE CARDS ══════════════════════════════════════════════ */
.mode-card {
    background: #FFFFFF;
    border: 1.5px solid #E5E7EB;
    border-radius: 18px; padding: 36px 28px;
    transition: all 0.25s ease-in-out;
    text-align: center; height: 100%;
    box-shadow: 0 2px 12px rgba(0,0,0,.05);
}
.mode-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 14px 40px rgba(0,0,0,.12);
}
.mode-card-work:hover  { border-color: #3B82F6; }
.mode-card-learn:hover { border-color: #0D9488; }
.mode-card-icon {
    width: 60px; height: 60px; border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    margin: 0 auto 20px;
}
.mode-card-title { font-size: 20px; font-weight: 800; color: #111827; margin-bottom: 10px; }
.mode-card-desc  { font-size: 14px; color: #6B7280; line-height: 1.7; }
.mode-card-cta   {
    font-size: 11px; font-weight: 700; letter-spacing: .08em;
    text-transform: uppercase; display: inline-block; margin-top: 22px;
}
.cta-work  { color: #3B82F6; }
.cta-learn { color: #0D9488; }

/* ══ STAT STRIP ══════════════════════════════════════════════ */
.stat-strip {
    display: grid; grid-template-columns: repeat(4, 1fr);
    border: 1px solid #E5E7EB; border-radius: 14px;
    background: #FFFFFF; margin: 40px 0; overflow: hidden;
    box-shadow: 0 2px 12px rgba(0,0,0,.05);
}
.stat-item { padding: 28px 0; text-align: center; border-right: 1px solid #E5E7EB; }
.stat-item:last-child { border-right: none; }
.stat-num  { font-size: 32px; font-weight: 900; color: #111827; line-height: 1; }
.stat-lbl  { font-size: 10px; color: #9CA3AF; margin-top: 6px; letter-spacing: .1em; text-transform: uppercase; }

/* ══ INTENT CARDS ════════════════════════════════════════════ */
.intent-card {
    background: #FFFFFF; border: 2px solid #E5E7EB;
    border-radius: 14px; padding: 26px 22px;
    cursor: pointer; transition: all 0.2s ease-in-out;
    text-align: center; box-shadow: 0 1px 4px rgba(0,0,0,.05);
}
.intent-card:hover { box-shadow: 0 6px 20px rgba(0,0,0,.10); transform: translateY(-2px); }
.intent-card-active-learn { border-color: #0D9488 !important; background: #F0FDFA !important; box-shadow: 0 0 0 3px rgba(13,148,136,.12) !important; }
.intent-card-active-teach { border-color: #9333EA !important; background: #FAF5FF !important; box-shadow: 0 0 0 3px rgba(147,51,234,.12) !important; }
.intent-card-title { font-size: 15px; font-weight: 700; color: #111827; margin-bottom: 6px; }
.intent-card-desc  { font-size: 12px; color: #6B7280; line-height: 1.6; }

/* ══ AVATAR RING ═════════════════════════════════════════════ */
.profile-avatar-ring {
    display: inline-flex; align-items: center; justify-content: center;
    border-radius: 50%;
    box-shadow: 0 0 0 3px #E5E7EB, 0 0 0 6px rgba(59,130,246,.08);
}

/* ══ SECTION DIVIDER ═════════════════════════════════════════ */
.section-divider {
    font-size: 10px; font-weight: 700; letter-spacing: .12em;
    text-transform: uppercase; color: #9CA3AF;
    display: flex; align-items: center; gap: 12px; margin: 32px 0 20px;
}
.section-divider::before, .section-divider::after {
    content: ''; flex: 1; height: 1px; background: #E5E7EB;
}

/* ══ NOTIFICATION DOT ════════════════════════════════════════ */
.notif-unread-dot {
    width: 6px; height: 6px; background: #3B82F6;
    border-radius: 50%; display: inline-block;
    margin-left: 5px; vertical-align: middle;
}

/* ══ SCROLLBAR — light ═══════════════════════════════════════ */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F9FAFB; }
::-webkit-scrollbar-thumb { background: #D1D5DB; border-radius: 999px; }
::-webkit-scrollbar-thumb:hover { background: #3B82F6; }
section.main > div > div > div > div[data-testid="stHorizontalBlock"]:has(.lp-feature) {
    background: transparent !important;
    box-shadow: none !important;
    padding: 0 !important;
div[data-testid="stHorizontalBlock"] {
    border-bottom: none !important;
    box-shadow: none !important;
    background: transparent !important;
}

/* Remove Streamlit divider */
hr {
    display: none !important;
}
}
section.main div[data-testid="stHorizontalBlock"] {
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
}

/* 🔥 REMOVE INNER COLUMN BACKGROUND */
section.main div[data-testid="stHorizontalBlock"] > div {
    background: transparent !important;
}

/* 🔥 REMOVE ANY DEFAULT BOTTOM LINE */
section.main div[data-testid="stHorizontalBlock"]::after {
    display: none !important;
}

/* 🔥 REMOVE STREAMLIT BLOCK CONTAINER BG JUST FOR SAFETY */
section.main .block-container > div {
    background: transparent !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  UI HELPERS
# ═══════════════════════════════════════════════════════════════
def status_badge(s):
    c = {
        "open": "badge-green", "in_progress": "badge-amber",
        "closed": "badge-slate", "pending": "badge-amber",
        "accepted": "badge-green", "rejected": "badge-red",
    }.get(s, "badge-slate")
    return f"<span class='cs-badge {c}'>{s.replace('_',' ').title()}</span>"

def priority_badge(p):
    c = {"Urgent": "badge-red", "Normal": "badge-cyan", "Low": "badge-slate"}.get(p, "badge-slate")
    return f"<span class='cs-badge {c}'>{p}</span>"

def type_badge(t, intent=""):
    if t == TYPE_KNOWLEDGE:
        if intent == INTENT_TEACH:
            return "<span class='cs-badge badge-teach'>Can Teach</span>"
        return "<span class='cs-badge badge-learn'>Wants to Learn</span>"
    return "<span class='cs-badge badge-cyan'>Task</span>"

def mode_pill():
    if is_learn_mode():
        st.markdown("<div class='mode-pill-learn'>Knowledge Exchange Mode</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<div class='mode-pill-work'>Task Collaboration Mode</div>",
                    unsafe_allow_html=True)

def mk_avatar_html(name, size=40, color="#2563EB", photo_bytes=None):
    """Renders a circular avatar — photo takes priority over color initial."""
    if photo_bytes:
        import base64
        b64 = base64.b64encode(photo_bytes).decode()
        return (f"<img src='data:image/jpeg;base64,{b64}' "
                f"style='width:{size}px;height:{size}px;border-radius:50%;"
                f"object-fit:cover;flex-shrink:0;"
                f"box-shadow:0 0 0 2px #E5E7EB;' />")
    ini = "".join(w[0].upper() for w in (name or "U").split()[:2])
    return (f"<div class='profile-avatar-ring' "
            f"style='width:{size}px;height:{size}px;background:{color};flex-shrink:0;'>"
            f"<span style='font-size:{size//3}px;font-weight:700;color:#fff;'>{ini}</span></div>")

def empty_state(title, desc="", action_label=None, action_key=None, action_fn=None):
    st.markdown(f"""
    <div class='cs-card' style='text-align:center;padding:48px 32px;'>
        <div style='width:44px;height:44px;border-radius:10px;background:#F9FAFB;
            display:flex;align-items:center;justify-content:center;margin:0 auto 14px;'>
            <svg width="18" height="18" fill="none" stroke="#1e2d45" stroke-width="2" viewBox="0 0 24 24">
            <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2"/>
            <rect x="9" y="3" width="6" height="4" rx="1"/></svg>
        </div>
        <div style='font-size:14px;font-weight:700;color:#6B7280;margin-bottom:5px;'>{title}</div>
        <div style='font-size:12px;color:#6B7280;'>{desc}</div>
    </div>""", unsafe_allow_html=True)
    if action_label and action_key:
        _, mc, _ = st.columns([2, 1, 2])
        with mc:
            if st.button(action_label, key=action_key, use_container_width=True):
                if action_fn: action_fn()

def back_btn():
    if st.button("Back", key=f"back__{st.session_state.page}"):
        go_back()

def breadcrumb(*parts):
    html = " / ".join(
        f"<span style='color:#9CA3AF;'>{p}</span>" if i < len(parts)-1
        else f"<span style='color:#6B7280;font-weight:500;'>{p}</span>"
        for i, p in enumerate(parts))
    st.markdown(f"<div style='font-size:11px;margin-bottom:10px;'>{html}</div>",
                unsafe_allow_html=True)

def section_header(title, subtitle=""):
    st.markdown(f"""
    <div style='margin-bottom:18px;'>
        <div class='page-title'>{title}</div>
        {f"<div class='page-sub'>{subtitle}</div>" if subtitle else ""}
    </div>""", unsafe_allow_html=True)

def section_divider(label=""):
    st.markdown(f"<div class='section-divider'>{label}</div>", unsafe_allow_html=True)

def trust_bar_html(score, max_score=10):
    pct = int((score / max_score) * 100)
    return (f"<div class='trust-bar-bg'>"
            f"<div class='trust-bar-fill' style='width:{pct}%;'></div></div>")

def stars_html(rating, max_stars=5):
    filled = "★" * int(rating)
    empty  = "☆" * (max_stars - int(rating))
    return (f"<span style='color:#f59e0b;letter-spacing:1px;'>{filled}</span>"
            f"<span style='color:#9CA3AF;letter-spacing:1px;'>{empty}</span>")


# ═══════════════════════════════════════════════════════════════
#  SKILL DROPDOWN  — runs OUTSIDE forms to fix the cursor bug
#  The bug: selectbox inside st.form with disabled=True causes
#  "not-allowed" cursor. Fix: use session_state outside the form.
# ═══════════════════════════════════════════════════════════════
def render_skill_selector(cat_key, skill_key, label_prefix=""):
    """
    Renders two dependent selectboxes OUTSIDE any form.
    Returns (category_str, skill_str) or (None, None).
    Must be called outside st.form().
    """
    cat_opts    = ["Select a category"] + SKILL_CATEGORIES
    selected_cat = st.selectbox(
        f"{label_prefix}Skill Category",
        cat_opts, key=cat_key)

    if selected_cat == "Select a category":
        st.selectbox(f"{label_prefix}Skill", ["— select category first —"],
                     key=skill_key, disabled=False)
        return None, None

    skill_opts   = SKILLS_BY_CATEGORY.get(selected_cat, []) + ["Other"]
    selected_skill = st.selectbox(f"{label_prefix}Skill", skill_opts, key=skill_key)
    return selected_cat, selected_skill


def render_navbar():
    """
    Premium dark navbar — black bg, white text.
    Same safe pattern: one flat column row, no wrapper divs.
    Active page = white text + subtle highlight.
    Sign Out = red tint (last col via CSS nth-child).
    Notification badge rendered in button label.
    """
    u        = st.session_state.user
    unread   = get_unread_count(u["id"]) if u else 0
    cur      = st.session_state.page
    is_guest = not logged_in()
    is_adm   = is_admin()

    # Notification label with badge count
    notif_lbl = f"Notifs  🔴{unread}" if unread else "Notifs"

    # ── Build nav list ───────────────────────────────────────
    if is_guest:
        nav_items=[]
        
    elif is_adm:
        nav_items = [
            
            ("Dashboard",       "admin_dashboard"),
            ("Users",           "admin_users"),
            ("All Posts",       "admin_tasks"),
            ("Browse",          "browse_tasks"),
            (notif_lbl,         "notifications"),
            ("Profile",         "profile"),
            ("Sign Out",        "__logout__"),
        ]
    else:
        nav_items = [
           
            ("Home",            "landing"),
            ("Dashboard",       "dashboard"),
            ("Browse",          "browse_tasks"),
            ("Post",            "post_task"),
            ("Network",         "network"),
            ("Projects",        "projects"),
            ("Chat",            "chat"),
            ("Sessions",        "my_sessions"),
            (notif_lbl,         "notifications"),
            ("Profile",         "profile"),
            ("Sign Out",        "__logout__"),
        ]

    total = len(nav_items)

    # ── Active-page highlight via nth-child ─────────────────
    active_idx = 0
    for i, (_, pg) in enumerate(nav_items):
        if pg == cur:
            active_idx = i + 1
            break

    # Dynamic CSS for active page + guest Sign Up blue
    guest_extra = ""
    if is_guest:
        guest_extra = """
        div[data-testid="stHorizontalBlock"]:first-of-type
            > div[data-testid="column"]:last-child .stButton > button {
            background: #2563EB !important;
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 8px !important;
            font-weight: 600 !important;
            padding: 7px 18px !important;
        }
        div[data-testid="stHorizontalBlock"]:first-of-type
            > div[data-testid="column"]:last-child .stButton > button:hover {
            background: #1D4ED8 !important;
            color: #FFFFFF !important;
        }
        div[data-testid="stHorizontalBlock"]:first-of-type
            > div[data-testid="column"]:nth-last-child(2) .stButton > button {
            border: 1.5px solid #D1D5DB !important;
            color: #374151 !important;
        }
        div[data-testid="stHorizontalBlock"]:first-of-type
            > div[data-testid="column"]:nth-last-child(2) .stButton > button:hover {
            border-color: #9CA3AF !important;
            color: #111827 !important;
            background: #F9FAFB !important;
        }
        """

    active_css = ""
    if active_idx > 0:
        active_css = f"""
        div[data-testid="stHorizontalBlock"]:first-of-type
            > div[data-testid="column"]:nth-child({active_idx}) .stButton > button {{
            color: #3B82F6 !important;
            background: #EFF6FF !important;
            font-weight: 600 !important;
        }}
        """

    st.markdown(f"""
<style>
{active_css}
{guest_extra}
</style>
""", unsafe_allow_html=True)

    # ── Flat column row — ZERO wrapper divs ─────────────────
    cols = st.columns([2.0] + [1.0] * (total - 1))
    for col, (lbl, pg) in zip(cols, nav_items):
        with col:
            if st.button(lbl, key=f"nav__{pg}", use_container_width=True):
                if pg in ("__logo__", "landing"):
                    go("landing")
                elif pg == "__logout__":
                    st.session_state.user    = None
                    st.session_state.history = []
                    go("landing")
                else:
                    go(pg)



def page_landing():
    col1, col2 = st.columns([6, 2])

    with col1:
        st.markdown("""
        <div style='padding:10px 0 2px 12px;
                    font-size:22px;
                    font-weight:900;'>
            <span style='color:#111827;'>Collab</span>
            <span style='color:#3B82F6;'>Skill</span>
            <span style='color:#111827;'> AI</span>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        c1, c2 = st.columns(2)

        with c1:
            if st.button("Sign In", key="top_login"):
                st.session_state.page = "login"
                st.rerun()

        with c2:
            if st.button("Sign Up", key="top_signup"):
                st.session_state.page = "register"
                st.rerun()

    
    
    render_navbar()

    # ── Hero Section ─────────────────────────────────────────
    st.markdown("""
    <style>
    /* Landing page: white background */
    .stApp { background: #FFFFFF !important; }
    html, body, [class*="css"] { background-color: #FFFFFF !important; }

    /* Hero */
    .lp-hero {
        text-align: center;
        padding:60px 24px 20px;
        max-width: 820px;
        margin: 0 auto;
    }
    .lp-eyebrow {
        display: inline-block;
        font-size: 11px; font-weight: 700;
        letter-spacing: .18em; text-transform: uppercase;
        color: #3B82F6;
        background: rgba(59,130,246,.1); border: 1px solid #BFDBFE;
        border-radius: 999px; padding: 6px 18px;
        margin-bottom: 32px;
    }
    .lp-h1 {
        font-size: clamp(38px, 5.5vw, 64px);
        font-weight: 900; line-height: 1.06;
        letter-spacing: -.04em; color: #111827;
        margin: 0 0 6px;
    }
    .lp-gradient {
        font-size: clamp(38px, 5.5vw, 64px);
        font-weight: 900; line-height: 1.06;
        letter-spacing: -.04em;
        background: linear-gradient(135deg, #2563EB 0%, #4F46E5 55%, #7C3AED 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    .lp-sub {
        font-size: 17px; color: #808080;
        line-height: 1.7; max-width: 520px;
        margin: 22px auto 0;
    }
    .lp-choose {
        font-size: 11px; font-weight: 700;
        letter-spacing: .18em; text-transform: uppercase;
        color: #4A4A4A; text-align: center;
        margin: 48px 0 20px;
    }

    /* Mode Cards */
    .lp-card {
        background: #FAFAFA;
        border: 1.5px solid #E5E7EB;
        border-radius: 20px;
        padding: 40px 32px;
        text-align: center;
        transition: all .22s ease;
        min-height: 320px;
        display: flex; flex-direction: column;
        align-items: center;
    }
    .lp-card:hover {
        border-color: #3B82F6;
        box-shadow: 0 16px 48px rgba(37,99,235,.12);
        transform: translateY(-4px);
        background: #FFFFFF;
    }
    .lp-card-learn:hover { border-color: #0D9488; box-shadow: 0 16px 48px rgba(13,148,136,.12); }
    .lp-icon-wrap {
        width: 72px; height: 72px; border-radius: 18px;
        display: flex; align-items: center; justify-content: center;
        margin: 0 auto 24px;
    }
    .lp-card-title {
        font-size: 22px; font-weight: 800; color: #111827;
        margin-bottom: 12px; letter-spacing: -.02em;
    }
    .lp-card-desc {
        font-size: 14px; color: #808080;
        line-height: 1.7; flex: 1;
    }
    .lp-card-cta {
        display: inline-block; margin-top: 24px;
        font-size: 12px; font-weight: 700;
        letter-spacing: .1em; text-transform: uppercase;
    }
    .lp-cta-work  { color: #3B82F6; }
    .lp-cta-learn { color: #0D9488; }

    /* Stats strip */
    .lp-stats {
        display: grid; grid-template-columns: repeat(4, 1fr);
        border: 1.5px solid #E5E7EB; border-radius: 16px;
        background: #FFFFFF; margin: 48px 0; overflow: hidden;
        box-shadow: 0 2px 16px rgba(0,0,0,.05);
    }
    .lp-stat { padding: 28px 0; text-align: center; border-right: 1.5px solid #E5E7EB; }
    .lp-stat:last-child { border-right: none; }
    .lp-stat-num { font-size: 32px; font-weight: 900; color: #111827; line-height: 1; }
    .lp-stat-lbl { font-size: 11px; color: #4A4A4A; margin-top: 6px; letter-spacing: .1em; text-transform: uppercase; }

    /* Feature cards */
    .lp-feature {
        background: #FFFFFF; border: 1.5px solid #E5E7EB;
        border-radius: 16px; padding: 28px 24px;
        transition: all .2s ease;
        box-shadow: 0 2px 8px rgba(0,0,0,.04);
    }
    .lp-feature:hover { box-shadow: 0 8px 32px rgba(0,0,0,.10); transform: translateY(-3px); }
    .lp-feature-icon {
        width: 44px; height: 44px; border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 16px;
    }
    .lp-feature-title { font-size: 15px; font-weight: 700; color: #111827; margin-bottom: 8px; }
    .lp-feature-desc  { font-size: 13px; color: #808080; line-height: 1.65; }

    /* Steps */
    .lp-step {
        background: #FFFFFF; border: 1.5px solid #E5E7EB;
        border-radius: 14px; padding: 24px 20px;
    }
    .lp-step-num { font-size: 32px; font-weight: 900; color: #E2E8F0; line-height: 1; margin-bottom: 12px; }
    .lp-step-title { font-size: 13px; font-weight: 700; color: #111827; margin-bottom: 6px; }
    .lp-step-desc  { font-size: 12px; color: #808080; line-height: 1.6; }

    /* Section label */
    .lp-section-lbl {
        text-align: center; font-size: 11px; font-weight: 700;
        letter-spacing: .14em; text-transform: uppercase;
        color: #4A4A4A; margin: 56px 0 28px;
    }
    </style>

    <div class="lp-hero">
        <div class="lp-eyebrow">AI-Powered Skill Exchange Platform</div>
        <div class="lp-h1">Connect. Collaborate.</div>
        <div class="lp-gradient">Exchange Skills Smarter.</div>
        <div class="lp-sub">
            An intelligent platform that matches you with the right people —
            connecting skill providers with those who need them.
        </div>
    </div>
    <div class="lp-choose">Choose how you want to get started</div>
    """, unsafe_allow_html=True)

    # ── Mode Cards ────────────────────────────────────────────
    lc, rc = st.columns(2, gap="large")

    with lc:
        st.markdown("""
        <div class="lp-card">
            <div class="lp-icon-wrap" style="background:#EFF6FF;">
                <svg width="28" height="28" fill="none" stroke="#2563EB" stroke-width="1.8"
                    viewBox="0 0 24 24">
                    <rect x="2" y="7" width="20" height="14" rx="2"/>
                    <path d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/>
                    <line x1="12" y1="12" x2="12" y2="16"/>
                    <line x1="10" y1="14" x2="14" y2="14"/>
                </svg>
            </div>
            <div class="lp-card-title">Work</div>
            <div class="lp-card-desc">
                Post tasks, find skilled collaborators, and get projects done.
                Connect with professionals ready to help.
            </div>
            <div class="lp-card-cta lp-cta-work">TASK COLLABORATION &rarr;</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Get Started — Work Mode", key="land_work", use_container_width=True):
            st.session_state.mode = "work"
            go("register" if not logged_in() else ("admin_dashboard" if is_admin() else "dashboard"))

    with rc:
        st.markdown("""
        <div class="lp-card lp-card-learn">
            <div class="lp-icon-wrap" style="background:#CCFBF1;">
                <svg width="28" height="28" fill="none" stroke="#0D9488" stroke-width="1.8"
                    viewBox="0 0 24 24">
                    <path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/>
                    <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/>
                </svg>
            </div>
            <div class="lp-card-title">Learn</div>
            <div class="lp-card-desc">
                Request tutoring, share your expertise, and grow your skills.
                Connect with experts who guide your learning journey.
            </div>
            <div class="lp-card-cta lp-cta-learn">KNOWLEDGE EXCHANGE &rarr;</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Get Started — Learn Mode", key="land_learn", use_container_width=True):
            st.session_state.mode = "learn"
            go("register" if not logged_in() else ("admin_dashboard" if is_admin() else "dashboard"))

    # ── Stats Strip ───────────────────────────────────────────
    total_users = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    total_tasks = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE type='task'")["c"]
    open_tasks  = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open' AND type='task'")["c"]
    total_know  = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE type='knowledge'")["c"]

    st.markdown(f"""
    <div class="lp-stats">
        <div class="lp-stat"><div class="lp-stat-num">{total_users}</div><div class="lp-stat-lbl">Members</div></div>
        <div class="lp-stat"><div class="lp-stat-num">{total_tasks}</div><div class="lp-stat-lbl">Tasks Posted</div></div>
        <div class="lp-stat"><div class="lp-stat-num">{open_tasks}</div><div class="lp-stat-lbl">Open Tasks</div></div>
        <div class="lp-stat"><div class="lp-stat-num">{total_know}</div><div class="lp-stat-lbl">Knowledge Posts</div></div>
    </div>""", unsafe_allow_html=True)

    # ── Platform Features ─────────────────────────────────────
    st.markdown("<div class='lp-section-lbl'>Platform Features</div>", unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    features = [
        ("🤖", "AI Matching",         "#EFF6FF", "#2563EB",
         "Our AI reads task requirements and user profiles to surface the best skill matches instantly."),
        ("🏆", "Trust Score System",  "#F5F3FF", "#7C3AED",
         "Every collaboration builds your reputation through peer-reviewed ratings and badges."),
        ("⚡", "Dual Mode Platform",  "#F0FDFA", "#0D9488",
         "Switch between Task Collaboration and Knowledge Exchange anytime — one platform, two modes."),
    ]
    for col, (icon, title, bg, accent, desc) in zip([fc1, fc2, fc3], features):
        col.markdown(f"""
        <div class="lp-feature">
            <div class="lp-feature-icon" style="background:{bg};">
                <span style="font-size:20px;">{icon}</span>
            </div>
            <div class="lp-feature-title">{title}</div>
            <div class="lp-feature-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

    # ── How It Works ──────────────────────────────────────────
    st.markdown("<div class='lp-section-lbl'>How It Works</div>", unsafe_allow_html=True)
    h1, h2, h3, h4 = st.columns(4)
    steps = [
        ("01", "Create Account",    "Register and build your profile with skills and experience."),
        ("02", "Choose Your Mode",  "Work for task collaboration or Learn for knowledge exchange."),
        ("03", "Post or Browse",    "Post what you need or discover opportunities that match you."),
        ("04", "Collaborate",       "Connect, complete work, rate each other, and grow together."),
    ]
    for col, (num, title, desc) in zip([h1, h2, h3, h4], steps):
        col.markdown(f"""
        <div class="lp-step">
            <div class="lp-step-num">{num}</div>
            <div class="lp-step-title">{title}</div>
            <div class="lp-step-desc">{desc}</div>
        </div>""", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;padding:24px 0;border-top:1.5px solid #E5E7EB;'>
        <div style='font-size:15px;font-weight:800;color:#111827;letter-spacing:-.02em;'>
            Collab<span style='color:#3B82F6;'>Skill</span> AI
        </div>
        <div style='font-size:12px;color:#9CA3AF;margin-top:6px;'>
            Connecting skilled people with those who need them.
        </div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════════
def page_login():
    
    st.markdown("""
    <div style='padding:10px 0 2px 12px;
                font-size:22px;
                font-weight:900;
                color:#111827;'>
        Collab<span style='color:#3B82F6;'>Skill</span> AI
    </div>
    """, unsafe_allow_html=True)
    render_navbar()
    back_btn()

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<div style='height:20px;'></div>", unsafe_allow_html=True)
        mode_label = "Knowledge Exchange" if is_learn_mode() else "Task Collaboration"
        st.markdown(f"""
        <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:14px;padding:36px;'>
            <div style='text-align:center;margin-bottom:26px;'>
                <div style='font-size:20px;font-weight:800;color:#111827;margin-bottom:4px;'>Sign in to CollabSkill AI</div>
                <div style='font-size:12px;color:#6B7280;'>{mode_label} Mode</div>
            </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Your username", key="lp_username")
        password = st.text_input("Password", type="password", placeholder="Your password", key="lp_password")
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)

        if st.button("Sign In", key="lp_submit", use_container_width=True):
            if not username or not password:
                st.warning("Please enter both username and password.")
            else:
                user = login_user(username, password)
                if user:
                    st.session_state.user    = user
                    st.session_state.history = []
                    go("admin_dashboard" if user["role"] == "admin" else "dashboard")
                else:
                    st.error("Invalid username or password.")

        st.markdown("""
        <div style='text-align:center;margin-top:18px;padding-top:18px;
            border-top:1px solid #1F1F1F;font-size:12px;color:#6B7280;'>
            Do not have an account yet?
        </div>""", unsafe_allow_html=True)

        if st.button("Create an Account", key="lp_to_register", use_container_width=True):
            go("register")


# ═══════════════════════════════════════════════════════════════
#  REGISTER  — cascading skill dropdowns OUTSIDE form
# ═══════════════════════════════════════════════════════════════
def page_register():
    
    st.markdown("""
    <div style='padding:10px 0 2px 12px;
                font-size:22px;
                font-weight:900;
                color:#111827;'>
        Collab<span style='color:#3B82F6;'>Skill</span> AI
    </div>
    """, unsafe_allow_html=True)
    render_navbar()
    back_btn()
    st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
    section_header("Create Your Account",
                   "Join CollabSkill AI and start collaborating or learning today.")

    # ── Main form (account + profile details) ─────────────────
    with st.form("register_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Account Details**")
            username  = st.text_input("Username *",         placeholder="Choose a unique username", key="rp_user")
            email     = st.text_input("Email Address *",    placeholder="you@email.com",            key="rp_email")
            password  = st.text_input("Password *",         placeholder="Minimum 6 characters",     key="rp_pass",    type="password")
            confirm   = st.text_input("Confirm Password *", placeholder="Repeat your password",     key="rp_confirm", type="password")
        with c2:
            st.markdown("**Profile Details**")
            experience   = st.selectbox("Experience Level",
                                        ["Beginner","Intermediate","Advanced","Expert"], key="rp_exp")
            phone_number = st.text_input("Phone Number (optional)", placeholder="+91 98765 43210", key="rp_phone")
            portfolio    = st.text_input("Portfolio / GitHub URL (optional)",
                                         placeholder="https://github.com/yourname", key="rp_port")
            bio          = st.text_area("Short Bio", placeholder="Tell others about yourself...",
                                        height=80, key="rp_bio")

        agree    = st.checkbox("I agree to the Terms and Conditions", key="rp_agree")
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    # ── Primary Skill — BELOW account details, OUTSIDE form ───
    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='background:#FFFFFF;border:1px solid #E5E7EB;border-radius:14px;
        padding:20px 22px;margin-bottom:12px;box-shadow:0 2px 10px rgba(0,0,0,.05);'>
        <div style='font-size:13px;font-weight:700;color:#111827;margin-bottom:14px;'>
            Primary Skill
        </div>
    """, unsafe_allow_html=True)

    sk1, sk2 = st.columns(2)
    with sk1:
        sel_cat = st.selectbox(
            "Skill Category",
            ["Select a category"] + SKILL_CATEGORIES,
            key="rp_skill_cat")
    with sk2:
        if sel_cat == "Select a category":
            st.selectbox("Skill", ["Select a category first"], key="rp_skill_val")
            sel_skill = None
        else:
            skill_opts = SKILLS_BY_CATEGORY.get(sel_cat, []) + ["Other — type your own"]
            sel_skill  = st.selectbox("Skill", skill_opts, key="rp_skill_val")

    # If "Other — type your own" is selected, show a text input
    custom_skill = None
    if sel_skill == "Other — type your own":
        custom_skill = st.text_input(
            "Enter your skill",
            placeholder="Type your specific skill here...",
            key="rp_custom_skill")


    if submitted:
        # Resolve the final skill string
        if sel_skill == "Other — type your own":
            resolved_skill = custom_skill.strip() if custom_skill else ""
            skill_str = f"{sel_cat} - {resolved_skill}" if (sel_cat and sel_cat != "Select a category" and resolved_skill) else ""
        else:
            skill_str = (f"{sel_cat} - {sel_skill}"
                         if sel_cat and sel_cat != "Select a category" and sel_skill else "")
        if not agree:
            st.warning("Please accept the Terms and Conditions.")
        elif not all([username, email, password, skill_str]):
            st.warning("Please fill all required fields and select your skill.")
        elif len(password) < 6:
            st.warning("Password must be at least 6 characters.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            success, result = register_user(
                username, email, password, skill_str, bio, portfolio, experience, phone_number)
            if success:
                st.session_state.user    = result
                st.session_state.history = []
                st.success("Account created. Welcome to CollabSkill AI.")
                go("admin_dashboard" if result["role"] == "admin" else "dashboard")
            else:
                st.error(result)

    st.markdown("<div style='font-size:12px;color:#6B7280;margin-top:10px;'>Already have an account?</div>",
                unsafe_allow_html=True)
    if st.button("Sign In Instead", key="rp_to_login"):
        go("login")


# ═══════════════════════════════════════════════════════════════
#  USER DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_dashboard():
    
    st.markdown("""
    <div style='padding:10px 0 2px 12px;
                font-size:22px;
                font-weight:900;
                color:#111827;'>
        Collab<span style='color:#3B82F6;'>Skill</span> AI
    </div>
    """, unsafe_allow_html=True)
    require_login()
    if is_admin(): go("admin_dashboard"); return

    render_navbar()
    u = get_user(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = u

    breadcrumb("Home", "Dashboard")

    mode_label = "Knowledge Exchange" if is_learn_mode() else "Task Collaboration"
    st.markdown(
        f"<div class='page-title'>Welcome, {u['username']}</div>"
        f"<div class='page-sub'>{mode_label} — your personal workspace</div>",
        unsafe_allow_html=True)
    mode_pill()

    mode_type  = TYPE_KNOWLEDGE if is_learn_mode() else TYPE_TASK
    my_entries = get_my_tasks(u["id"], entry_type=mode_type)
    my_apps    = get_my_applications(u["id"])
    open_cnt   = sum(1 for t in my_entries if t["status"] == "open")
    sess_cnt   = count_sessions(u["id"])

    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    m1.metric("My Posts", len(my_entries))
    m2.metric("Active", open_cnt)
    m3.metric("Applications", len(my_apps))
    m4.metric("Trust Score", f"{u['trust_score']}/10")
    m5.metric("Ratings", u["total_ratings"])
    m6.metric("Sessions", sess_cnt)


    st.markdown("<br>", unsafe_allow_html=True)

    # Profile banner — just avatar info + Edit Profile, NO sign out here
    avatar_color = u.get("avatar_color", "#2563EB")
    pc1, pc2 = st.columns([6, 1])
    with pc1:
        st.markdown(f"""
        <div class='cs-card' style='display:flex;align-items:center;gap:16px;margin-bottom:0;'>
            {mk_avatar_html(u['username'], 48, avatar_color)}
            <div>
                <div style='font-size:15px;font-weight:800;color:#111827;'>{u['username']}</div>
                <div style='font-size:12px;color:#6B7280;margin-top:3px;'>{u['skills'] or 'No skills listed'}</div>
                <div style='font-size:11px;color:#9CA3AF;margin-top:2px;'>{u['experience']}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with pc2:
        st.markdown("<div style='padding-top:8px;'>", unsafe_allow_html=True)
        if st.button("Edit Profile", key="dash_edit", use_container_width=True):
            go("profile")

    st.markdown("<br>", unsafe_allow_html=True)

    t1_lbl = "My Knowledge Posts" if is_learn_mode() else "My Tasks"
    tab1, tab2, tab3 = st.tabs([t1_lbl, "My Applications", "Quick Actions"])

    with tab1:
        if not my_entries:
            desc = "Share expertise or post a learning request." if is_learn_mode() \
                   else "Post your first task to find collaborators."
            empty_state("No posts yet", desc,
                        action_label="Post Now", action_key="dash_post_empty",
                        action_fn=lambda: go("post_task"))
        else:
            for t in my_entries:
                _render_entry_card(t, owner=True)

    with tab2:
        if not my_apps:
            empty_state("No applications yet", "Browse and apply to help others.",
                        action_label="Browse", action_key="dash_browse_empty",
                        action_fn=lambda: go("browse_tasks"))
        else:
            for a in my_apps:
                tp = type_badge(a.get("task_type", TYPE_TASK))
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='font-weight:600;color:#111827;margin-bottom:6px;'>{a['task_title']}</div>
                    <div>{status_badge(a['status'])} {tp}
                        <span class='cs-badge badge-violet'>{a['category']}</span>
                        <span class='cs-badge badge-slate'>{a['owner_name']}</span>
                    </div>
                    <div style='color:#9CA3AF;font-size:11px;margin-top:6px;'>{str(a['created_at'])[:10]}</div>
                </div>""", unsafe_allow_html=True)

    with tab3:
        st.markdown("""
        <style>
        div[data-testid="column"] .stButton > button {
            height: 44px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        </style>""", unsafe_allow_html=True)

        lbl1 = "Post Knowledge" if is_learn_mode() else "Post a Task"
        lbl2 = "Browse Knowledge" if is_learn_mode() else "Browse Tasks"

        q1, q2, q3, q4 = st.columns(4)
        with q1:
            if st.button(lbl1, key="qa_post", use_container_width=True): go("post_task")
        with q2:
            if st.button(lbl2,         key="qa_browse",    use_container_width=True): go("browse_tasks")
        with q3:
            if st.button("AI Matching", key="qa_ai",        use_container_width=True): go("ai_match")
        with q4:
            if st.button("Community",   key="qa_community", use_container_width=True): go("community")

        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
       

    # ── My Learning Connections (only in Learn mode) ──────────
    if is_learn_mode():
        section_divider("My Learning Connections")
        my_learn  = get_my_learning_pairs(u["id"])
        my_teach  = get_my_teaching_pairs(u["id"])
        all_pairs = [("learning", p) for p in my_learn] + [("teaching", p) for p in my_teach]

        if not all_pairs:
            st.markdown(
                "<div style='color:#9CA3AF;font-size:13px;'>No active learning connections yet. "
                "Browse Knowledge posts and express interest to connect with learners or teachers.</div>",
                unsafe_allow_html=True)
        else:
            for role, pair in all_pairs:
                partner_name  = pair["teacher_name"] if role == "learning" else pair["learner_name"]
                role_label    = "Learning from" if role == "learning" else "Teaching"
                role_color    = "#0D9488" if role == "learning" else "#7C3AED"
                role_bg       = "#F0FDFA" if role == "learning" else "#FAF5FF"
                partner_id_key = "teacher_id" if role == "learning" else "learner_id"
                pid            = pair[partner_id_key] if partner_id_key in pair else None

                st.markdown(
                    f"<div class='cs-card' style='display:flex;align-items:center;"
                    f"gap:14px;padding:14px;margin-bottom:8px;'>"
                    f"<div style='flex:1;'>"
                    f"<span style='background:{role_bg};color:{role_color};border-radius:999px;"
                    f"padding:3px 10px;font-size:10px;font-weight:700;margin-bottom:6px;"
                    f"display:inline-block;'>{role_label}</span>"
                    f"<div style='font-weight:700;color:#111827;font-size:13px;'>{partner_name}</div>"
                    f"<div style='font-size:11px;color:#6B7280;'>{pair.get('post_title','')}</div>"
                    f"</div></div>",
                    unsafe_allow_html=True)

                lc1, lc2 = st.columns(2)
                with lc1:
                    if pid and st.button("Chat", key=f"dash_lc_chat_{pair['id']}",
                                         use_container_width=True):
                        st.session_state.chat_partner = pid
                        go("chat")
                with lc2:
                    if st.button("Book Session", key=f"dash_lc_book_{pair['id']}",
                                 use_container_width=True):
                        st.session_state.book_post_id    = pair["post_id"]
                        st.session_state.book_teacher_id = pair.get("teacher_id")
                        go("book_session")

    # ── AI Recommendations ────────────────────────────────────
    render_ai_recommendations(u)


# ═══════════════════════════════════════════════════════════════
#  SHARED ENTRY CARD
# ═══════════════════════════════════════════════════════════════
def _render_entry_card(t, owner=False):
    is_know = t.get("type") == TYPE_KNOWLEDGE
    intent  = t.get("knowledge_intent", "")
    header  = f"{t['title']}  —  {t['status'].upper()}"

    with st.expander(header):
        c1, c2 = st.columns([3, 1])
        with c1:
            interest_cnt = get_interest_count(t["id"]) if is_know else t.get("applicant_count", 0)
            interest_lbl = f"{interest_cnt} interested" if is_know else f"{interest_cnt} applicants"
            st.markdown(
                f"<div style='color:#6B7280;font-size:13px;margin-bottom:10px;line-height:1.7;'>"
                f"{t['description']}</div>"
                f"{type_badge(t.get('type', TYPE_TASK), intent)}"
                f"{status_badge(t['status'])}"
                f"{priority_badge(t.get('priority','Normal'))}"
                f"<span class='cs-badge badge-violet'>{t.get('category','')}</span>"
                f"<span class='cs-badge badge-slate'>{t['skills']}</span>"
                f"<span class='cs-badge badge-blue'>{interest_lbl}</span>",
                unsafe_allow_html=True)
        with c2:
            if owner:
                if t["status"] == "open":
                    if st.button("Close",  key=f"tc_{t['id']}"): update_task_status(t["id"], "closed"); st.rerun()
                else:
                    if st.button("Reopen", key=f"to_{t['id']}"): update_task_status(t["id"], "open"); st.rerun()
                if st.button("Delete", key=f"td_{t['id']}"): delete_task(t["id"]); st.rerun()
                # For knowledge LEARN posts — show interested teachers
                if is_know and intent == INTENT_LEARN and interest_cnt > 0:
                    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                    if st.button(f"View Interested ({interest_cnt})", key=f"vi_{t['id']}",
                                 use_container_width=True):
                        st.session_state[f"show_interested_{t['id']}"] = \
                            not st.session_state.get(f"show_interested_{t['id']}", False)

                # For knowledge TEACH posts — show interested learners
                if is_know and intent == INTENT_TEACH and interest_cnt > 0:
                    st.markdown("<div style='margin-top:8px;'>", unsafe_allow_html=True)
                    if st.button(f"View Interested ({interest_cnt})", key=f"vi_teach_{t['id']}",
                                 use_container_width=True):
                        st.session_state[f"show_interested_{t['id']}"] = \
                            not st.session_state.get(f"show_interested_{t['id']}", False)

        # ── Show interested users panel ────────────────────────
        if (owner and is_know
                and st.session_state.get(f"show_interested_{t['id']}", False)):
            if intent == INTENT_LEARN:
                _render_interested_teachers(t)
            elif intent == INTENT_TEACH:
                _render_interested_learners(t)

def _render_interested_teachers(t):
    """Show list of teachers who expressed interest — learner can Accept/Reject."""
    uid      = st.session_state.user["id"]
    teachers = get_interested_teachers(t["id"])
    st.markdown(
        "<div style='background:#F3F4F6;border:1px solid #E5E7EB;border-radius:10px;"
        "padding:16px;margin-top:8px;'>",
        unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:12px;font-weight:700;color:#111827;margin-bottom:12px;'>"
        "Users interested in teaching you</div>",
        unsafe_allow_html=True)

    accepted_exists = any(r["status"] == "accepted" for r in teachers)

    for r in teachers:
        ini = "".join(w[0].upper() for w in r["teacher_name"].split()[:2])
        av  = r.get("teacher_color", "#2563EB")
        status_html = {
            "accepted": "<span class='cs-badge badge-green'>Accepted</span>",
            "rejected": "<span class='cs-badge badge-red'>Rejected</span>",
            "pending":  "<span class='cs-badge badge-amber'>Pending</span>",
        }.get(r["status"], "")

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:12px;"
            f"background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;"
            f"padding:12px 14px;margin-bottom:8px;'>"
            f"<div style='width:40px;height:40px;border-radius:50%;background:{av};"
            f"display:inline-flex;align-items:center;justify-content:center;"
            f"font-size:14px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>"
            f"<div style='flex:1;'>"
            f"<div style='font-weight:700;color:#111827;font-size:13px;'>{r['teacher_name']}</div>"
            f"<div style='font-size:11px;color:#6B7280;'>{r.get('teacher_skills','')}</div>"
            f"<div style='font-size:11px;color:#9CA3AF;'>{r.get('teacher_exp','')} "
            f"— Trust {r.get('teacher_trust',5)}/10</div>"
            f"</div>"
            f"{status_html}"
            f"</div>",
            unsafe_allow_html=True)

        if r["status"] == "pending" and not accepted_exists:
            ba, br = st.columns(2)
            with ba:
                if st.button("Accept", key=f"acc_teach_{r['id']}_{t['id']}",
                             use_container_width=True):
                    accept_teacher(r["id"], t["id"])
                    add_notification(r["teacher_id"], "Your Offer Was Accepted",
                        f"{st.session_state.user['username']} accepted your offer to teach: {t['title']}")
                    st.session_state["_interest_msg"] = ("ok", f"Accepted {r['teacher_name']}! You can now chat and book sessions.")
                    st.rerun()
            with br:
                if st.button("Decline", key=f"rej_teach_{r['id']}_{t['id']}",
                             use_container_width=True):
                    reject_interest(r["id"])
                    st.rerun()

        elif r["status"] == "accepted":
            # Show Chat + Book Session buttons for accepted teacher
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("Open Chat", key=f"chat_teach_{r['id']}_{t['id']}",
                             use_container_width=True):
                    st.session_state.chat_partner = r["teacher_id"]
                    go("chat")
            with bc2:
                if st.button("Book Session", key=f"book_{r['id']}_{t['id']}",
                             use_container_width=True):
                    st.session_state.book_post_id    = t["id"]
                    st.session_state.book_teacher_id = r["teacher_id"]
                    go("book_session")



def _render_interested_learners(t):
    """For TEACH posts — show learners who want to learn, teacher can Accept/Reject."""
    uid      = st.session_state.user["id"]
    learners = get_interested_learners(t["id"])

    st.markdown(
        "<div style='background:#FAF5FF;border:1px solid #E9D5FF;border-radius:10px;"
        "padding:16px;margin-top:8px;'>",
        unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:12px;font-weight:700;color:#111827;margin-bottom:12px;'>"
        "Learners interested in your teaching offer</div>",
        unsafe_allow_html=True)

    accepted_exists = any(r["status"] == "accepted" for r in learners)

    for r in learners:
        ini = "".join(w[0].upper() for w in r["learner_name"].split()[:2])
        av  = r.get("learner_color", "#7C3AED")
        status_html = {
            "accepted": "<span class='cs-badge badge-green'>Accepted</span>",
            "rejected": "<span class='cs-badge badge-red'>Declined</span>",
            "pending":  "<span class='cs-badge badge-amber'>Pending</span>",
        }.get(r["status"], "")

        st.markdown(
            f"<div style='display:flex;align-items:center;gap:12px;"
            f"background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;"
            f"padding:12px 14px;margin-bottom:8px;'>"
            f"<div style='width:40px;height:40px;border-radius:50%;background:{av};"
            f"display:inline-flex;align-items:center;justify-content:center;"
            f"font-size:14px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>"
            f"<div style='flex:1;'>"
            f"<div style='font-weight:700;color:#111827;font-size:13px;'>{r['learner_name']}</div>"
            f"<div style='font-size:11px;color:#6B7280;'>{r.get('learner_skills', '')}</div>"
            f"<div style='font-size:11px;color:#9CA3AF;'>{r.get('learner_exp', '')} "
            f"— Trust {r.get('learner_trust', 5)}/10</div>"
            f"</div>"
            f"{status_html}"
            f"</div>",
            unsafe_allow_html=True)

        if r["status"] == "pending" and not accepted_exists:
            ba, br = st.columns(2)
            with ba:
                if st.button("Accept", key=f"acc_learn_{r['id']}_{t['id']}",
                             use_container_width=True):
                    accept_learner(r["id"], t["id"])
                    add_notification(r["learner_id"], "Your Request Was Accepted",
                        f"{st.session_state.user['username']} accepted you as a student for: {t['title']}")
                    st.session_state["_interest_msg"] = ("ok", f"Accepted {r['learner_name']}! You can now chat and book sessions.")
                    st.rerun()
            with br:
                if st.button("Decline", key=f"rej_learn_{r['id']}_{t['id']}",
                             use_container_width=True):
                    reject_interest(r["id"])
                    st.rerun()

        elif r["status"] == "accepted":
            # Teacher can chat and book session with accepted learner
            bc1, bc2 = st.columns(2)
            with bc1:
                if st.button("Open Chat", key=f"chat_learn_{r['id']}_{t['id']}",
                             use_container_width=True):
                    st.session_state.chat_partner = r["learner_id"]
                    go("chat")
            with bc2:
                if st.button("Book Session", key=f"book_learn_{r['id']}_{t['id']}",
                             use_container_width=True):
                    # For teach posts: teacher is the post owner (uid), learner is accepted
                    st.session_state.book_post_id    = t["id"]
                    st.session_state.book_teacher_id = uid         # teacher = post owner
                    st.session_state.book_learner_id = r["learner_id"]
                    go("book_session")

def page_book_session():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "Knowledge", "Book Session")
    section_header("Book a Learning Session",
                   "Schedule a structured session between learner and teacher.")

    u          = st.session_state.user
    post_id    = st.session_state.get("book_post_id")
    teacher_id = st.session_state.get("book_teacher_id")
    # For TEACH posts booked by the teacher, learner_id is stored separately
    learner_id = st.session_state.get("book_learner_id") or u["id"]

    if not post_id or not teacher_id:
        st.warning("Invalid session — please go back and try again.")
        return

    teacher = db_fetchone("SELECT * FROM users WHERE id=?", (teacher_id,))
    learner = db_fetchone("SELECT * FROM users WHERE id=?", (learner_id,))
    post    = db_fetchone("SELECT * FROM tasks WHERE id=?", (post_id,))
    if not teacher or not post:
        st.warning("Could not find session details.")
        return

    # Determine display: who is the other person from current user's POV
    is_teacher = (u["id"] == teacher_id)
    other      = learner if is_teacher else teacher
    other_role = "Student" if is_teacher else "Teacher"

    ini = "".join(w[0].upper() for w in other["username"].split()[:2])
    av  = other.get("avatar_color", "#2563EB")

    st.markdown(
        f"<div class='cs-card' style='display:flex;align-items:center;gap:14px;"
        f"padding:16px;margin-bottom:20px;'>"
        f"<div style='width:48px;height:48px;border-radius:50%;background:{av};"
        f"display:inline-flex;align-items:center;justify-content:center;"
        f"font-size:17px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>"
        f"<div>"
        f"<div style='font-weight:800;color:#111827;font-size:15px;'>"
        f"Session with {other['username']} ({other_role})</div>"
        f"<div style='font-size:12px;color:#6B7280;margin-top:3px;'>Topic: {post['title']}</div>"
        f"</div></div>",
        unsafe_allow_html=True)

    with st.form("book_session_form"):
        bc1, bc2 = st.columns(2)
        with bc1:
            s_date = st.date_input("Session Date")
            s_dur  = st.selectbox("Duration",
                                  ["30 minutes", "1 hour", "1.5 hours", "2 hours", "Custom"])
        with bc2:
            s_time = st.time_input("Session Time")
            s_type = st.selectbox("Session Type",
                                  ["Video Call", "Chat Session", "Audio Call"])

        s_notes = st.text_area(
            "Notes (optional)",
            placeholder="What do you want to focus on in this session?",
            height=80)

        if st.form_submit_button("Confirm Booking", use_container_width=True):
            sid = book_session(
                learner_id   = learner_id,
                teacher_id   = teacher_id,
                post_id      = post_id,
                topic        = post["title"],
                date         = str(s_date),
                time         = str(s_time),
                duration     = s_dur,
                session_type = s_type,
                notes        = s_notes,
            )
            # Notify the other party
            notify_id  = learner_id if is_teacher else teacher_id
            notify_who = other["username"]
            add_notification(notify_id, "New Session Booked",
                f"{u['username']} booked a {s_type} with you on {s_date} at {s_time}.")
            st.success(
                f"Session booked for {s_date} at {s_time}. "
                f"{notify_who} has been notified.")
            # Clear booking state
            st.session_state.book_post_id    = None
            st.session_state.book_teacher_id = None
            st.session_state.book_learner_id = None
            go("my_sessions")


# ═══════════════════════════════════════════════════════════════
#  PAGE: MY SESSIONS
# ═══════════════════════════════════════════════════════════════
def page_my_sessions():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "My Sessions")
    section_header("My Sessions", "Upcoming and past learning sessions.")

    # Show deferred messages safely outside any column/tab context
    if "_sess_msg" in st.session_state:
        st.success(st.session_state.pop("_sess_msg"))

    u  = st.session_state.user
    tab1, tab2 = st.tabs(["Upcoming Sessions", "Past Sessions"])

    def _session_card(s, uid):
        is_learner = s["learner_id"] == uid
        partner    = s["teacher_name"] if is_learner else s["learner_name"]
        partner_av = s.get("teacher_color","#2563EB") if is_learner else s.get("learner_color","#2563EB")
        role_lbl   = "You are learning" if is_learner else "You are teaching"
        ini        = "".join(w[0].upper() for w in partner.split()[:2])

        type_color = {"Video Call":"#2563EB","Chat Session":"#0D9488","Audio Call":"#7C3AED"}.get(s["session_type"],"#64748B")
        type_bg    = {"Video Call":"#EFF6FF","Chat Session":"#CCFBF1","Audio Call":"#F3E8FF"}.get(s["session_type"],"#F1F5F9")

        st.markdown(
            f"<div class='cs-card' style='padding:18px;'>"
            f"<div style='display:flex;align-items:flex-start;gap:14px;'>"
            f"<div style='width:44px;height:44px;border-radius:50%;background:{partner_av};"
            f"display:inline-flex;align-items:center;justify-content:center;"
            f"font-size:15px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>"
            f"<div style='flex:1;'>"
            f"<div style='font-weight:800;font-size:14px;color:#111827;'>{s['topic']}</div>"
            f"<div style='font-size:12px;color:#6B7280;margin-top:3px;'>{role_lbl} with <strong>{partner}</strong></div>"
            f"<div style='margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;'>"
            f"<span style='background:{type_bg};color:{type_color};border-radius:999px;"
            f"padding:3px 12px;font-size:11px;font-weight:700;'>{s['session_type']}</span>"
            f"<span class='cs-badge badge-slate'>{s['date']} at {s['time'][:5]}</span>"
            f"<span class='cs-badge badge-slate'>{s['duration']}</span>"
            f"<span class='cs-badge badge-{'green' if s['status']=='completed' else 'amber'}'>"
            f"{s['status'].capitalize()}</span>"
            f"</div>"
            + (f"<div style='font-size:12px;color:#6B7280;margin-top:8px;'>{s['notes']}</div>"
               if s.get("notes") else "")
            + f"</div></div></div>",
            unsafe_allow_html=True)

        # Action buttons
        if s["status"] == "scheduled":
            btn_cols = st.columns(3)
            with btn_cols[0]:
                partner_id = s["teacher_id"] if is_learner else s["learner_id"]
                if st.button("Open Chat", key=f"schat_{s['id']}"):
                    st.session_state.chat_partner = partner_id
                    go("chat")
            with btn_cols[1]:
                if st.button("Join Session", key=f"sjoin_{s['id']}"):
                    st.info("Video sessions open in your external conferencing tool. Use the chat to share your meeting link.")
            with btn_cols[2]:
                if st.button("Mark Complete", key=f"scomp_{s['id']}"):
                    mark_session_complete(s["id"])
                    st.session_state["_sess_msg"] = "Session marked as completed."
                    st.rerun()

    with tab1:
        upcoming = get_upcoming_sessions(u["id"])
        if not upcoming:
            empty_state("No upcoming sessions",
                        "Book a session from your accepted knowledge connections.")
        else:
            st.markdown(f"<div style='color:#6B7280;font-size:12px;margin-bottom:12px;'>"
                        f"{len(upcoming)} upcoming session(s)</div>", unsafe_allow_html=True)
            for s in upcoming:
                _session_card(s, u["id"])

    with tab2:
        past = get_past_sessions(u["id"])
        if not past:
            empty_state("No past sessions yet.")
        else:
            for s in past:
                _session_card(s, u["id"])



def page_browse_tasks():
    render_navbar()
    back_btn()

    # Deferred messages from column/expander contexts
    if "_br_msg" in st.session_state:
        kind, msg = st.session_state.pop("_br_msg")
        if kind == "ok": st.success(msg)
        else: st.warning(msg)

    is_know    = is_learn_mode()
    entry_type = TYPE_KNOWLEDGE if is_know else TYPE_TASK

    if is_know:
        breadcrumb("Home", "Browse Knowledge")
        section_header("Browse Knowledge Exchange",
                       "Discover people who want to learn or who can teach.")
    else:
        breadcrumb("Home", "Browse Tasks")
        section_header("Browse Tasks",
                       "Find tasks that match your skills and start collaborating.")
    mode_pill()

    # ── Filters ──────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([3, 1.5, 1.5])
    with fc1:
        search = st.text_input("", placeholder="Search by title, skill or keyword...",
                               key=f"br_search_{entry_type}", label_visibility="collapsed")
    with fc2:
        topic_list = KNOWLEDGE_TOPICS if is_know else CATEGORIES
        category   = st.selectbox("", ["All"] + topic_list,
                                  key=f"br_cat_{entry_type}", label_visibility="collapsed")
    with fc3:
        sort_by = st.selectbox("", ["Newest First","Oldest First","Priority"],
                               key=f"br_sort_{entry_type}", label_visibility="collapsed")

    # For knowledge mode: filter by intent
    intent_filter = ""
    if is_know:
        fi1, fi2, fi3 = st.columns([1, 1, 4])
        with fi1:
            if st.button("All Posts", key="br_intent_all"):
                st.session_state["br_intent"] = ""
        with fi2:
            if st.button("Wants to Learn", key="br_intent_learn"):
                st.session_state["br_intent"] = INTENT_LEARN
        with fi3:
            if st.button("Can Teach", key="br_intent_teach"):
                st.session_state["br_intent"] = INTENT_TEACH
        intent_filter = st.session_state.get("br_intent", "")

    sort_map = {"Newest First": "newest", "Oldest First": "oldest", "Priority": "priority"}

    if logged_in():
        post_lbl = "Post Knowledge" if is_know else "Post a Task"
        if st.button(post_lbl, key=f"br_post_{entry_type}"):
            go("post_task")

    entries = get_all_open_tasks(
        search, category, sort_map.get(sort_by, "newest"),
        entry_type=entry_type, knowledge_intent=intent_filter)

    count_noun = "knowledge post(s)" if is_know else "task(s)"
    st.markdown(
        f"<div style='color:#6B7280;font-size:12px;margin:10px 0;'>{len(entries)} {count_noun}</div>",
        unsafe_allow_html=True)

    if not entries:
        empty_state("No posts found", "Be the first to post one.",
                    action_label="Post Now", action_key=f"br_empty_{entry_type}",
                    action_fn=lambda: go("post_task"))
        return

    for t in entries:
        creator = t.get("creator_name", "")
        intent  = t.get("knowledge_intent", "")
        apply_lbl = "I Can Help Teach" if (is_know and intent == INTENT_LEARN) else \
                    "I Want to Learn This" if (is_know and intent == INTENT_TEACH) else "I Can Help"

        with st.expander(f"{t['title']}  —  {creator}"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div style='color:#6B7280;font-size:13px;line-height:1.7;margin-bottom:10px;'>{t['description']}</div>
                {type_badge(t.get('type', TYPE_TASK), intent)}
                {status_badge(t['status'])}
                {priority_badge(t.get('priority','Normal'))}
                <span class='cs-badge badge-violet'>{t['category']}</span>
                <span class='cs-badge badge-slate'>{t['skills']}</span>
                {'<span class="cs-badge badge-slate">Deadline: ' + t["deadline"] + '</span>' if t.get("deadline") else ''}
                <span class='cs-badge badge-slate'>By {creator}</span>
                <span class='cs-badge badge-slate'>Trust {t.get("creator_trust",0)}/10</span>
                <span class='cs-badge badge-slate'>{t.get("applicant_count",0)} {'interested' if is_know else 'applied'}</span>
                <div style='font-size:11px;color:#9CA3AF;margin-top:8px;'>Posted {str(t.get("created_at",""))[:10]}</div>
                """, unsafe_allow_html=True)
            with c2:
                if logged_in() and st.session_state.user["id"] != t["created_by"]:
                    uid = st.session_state.user["id"]

                    # ── LEARN post: teacher expresses interest ────────
                    if is_know and intent == INTENT_LEARN:
                        already = db_fetchone(
                            "SELECT id,status FROM learning_interests "
                            "WHERE post_id=? AND teacher_id=?",
                            (t["id"], uid))
                        if already:
                            if already["status"] == "accepted":
                                st.markdown("<span class='cs-badge badge-green'>Accepted</span>",
                                            unsafe_allow_html=True)
                                if st.button("Open Chat", key=f"br_chat_{t['id']}",
                                             use_container_width=True):
                                    st.session_state.chat_partner = t["created_by"]
                                    go("chat")
                                if st.button("Book Session", key=f"br_book_{t['id']}",
                                             use_container_width=True):
                                    st.session_state.book_post_id    = t["id"]
                                    st.session_state.book_teacher_id = uid
                                    go("book_session")
                            else:
                                st.markdown(
                                    "<span class='cs-badge badge-amber'>Interest Sent</span>",
                                    unsafe_allow_html=True)
                        else:
                            if st.button("I Can Help Teach", key=f"apply_{t['id']}",
                                         use_container_width=True):
                                ok, msg = express_interest(t["id"], t["created_by"], uid)
                                if ok:
                                    add_notification(t["created_by"], "New Interest in Your Post",
                                        f"{st.session_state.user['username']} wants to help teach: {t['title']}")
                                    st.session_state["_br_msg"] = ("ok", "Interest sent! The learner will review and accept.")
                                    st.rerun()
                                else:
                                    st.session_state["_br_msg"] = ("warn", msg)
                                    st.rerun()

                    # ── TEACH post: learner expresses interest ────────
                    elif is_know and intent == INTENT_TEACH:
                        already = db_fetchone(
                            "SELECT id,status FROM learning_interests "
                            "WHERE post_id=? AND learner_id=?",
                            (t["id"], uid))
                        if already:
                            if already["status"] == "accepted":
                                st.markdown("<span class='cs-badge badge-green'>Accepted</span>",
                                            unsafe_allow_html=True)
                                if st.button("Open Chat", key=f"br_chat_teach_{t['id']}",
                                             use_container_width=True):
                                    st.session_state.chat_partner = t["created_by"]
                                    go("chat")
                                if st.button("Book Session", key=f"br_book_teach_{t['id']}",
                                             use_container_width=True):
                                    st.session_state.book_post_id    = t["id"]
                                    st.session_state.book_teacher_id = t["created_by"]
                                    st.session_state.book_learner_id = uid
                                    go("book_session")
                            else:
                                st.markdown(
                                    "<span class='cs-badge badge-amber'>Request Sent</span>",
                                    unsafe_allow_html=True)
                        else:
                            if st.button("I Want to Learn This", key=f"apply_{t['id']}",
                                         use_container_width=True):
                                # learner_id = uid, teacher_id = post owner
                                ok, msg = express_interest(t["id"], uid, t["created_by"])
                                if ok:
                                    add_notification(t["created_by"], "New Student Request",
                                        f"{st.session_state.user['username']} wants to learn from you: {t['title']}")
                                    st.session_state["_br_msg"] = ("ok", "Request sent! The teacher will review and accept.")
                                    st.rerun()
                                else:
                                    st.session_state["_br_msg"] = ("warn", msg)
                                    st.rerun()

                    # ── Task mode or other posts ──────────────────────
                    else:
                        if st.button(apply_lbl, key=f"apply_{t['id']}",
                                     use_container_width=True):
                            ok, msg = apply_to_task(t["id"], uid)
                            if ok:
                                ntitle = "New Interest in Your Post" if is_know else "New Application"
                                nmsg   = f"{st.session_state.user['username']} responded to: {t['title']}"
                                add_notification(t["created_by"], ntitle, nmsg)
                            st.session_state["_br_msg"] = ("ok" if ok else "warn", msg)
                            st.rerun()

                elif not logged_in():
                    if st.button("Sign In to Apply", key=f"la_{t['id']}"): go("login")


# ═══════════════════════════════════════════════════════════════
#  POST TASK / KNOWLEDGE REQUEST
# ═══════════════════════════════════════════════════════════════
def page_post_task():
    require_login()
    render_navbar()
    back_btn()

    is_know    = is_learn_mode()
    entry_type = TYPE_KNOWLEDGE if is_know else TYPE_TASK

    if not is_know:
        # ── WORK MODE: existing task form ─────────────────────
        breadcrumb("Home", "Dashboard", "Post a Task")
        section_header("Post a Task", "Describe what you need and find the right collaborator.")
        mode_pill()

        c_form, c_tip = st.columns([2, 1])
        with c_form:
            with st.form("post_task_form"):
                title = st.text_input("Task Title *",
                                      placeholder="e.g., React developer for dashboard project")
                desc  = st.text_area("Description *",
                                     placeholder="Describe requirements, expected output, tools needed...",
                                     height=130)
                sk1, sk2 = st.columns(2)
                with sk1:
                    skills   = st.text_input("Required Skills *", placeholder="e.g., React, Node.js")
                    deadline = st.text_input("Deadline",           placeholder="e.g., Within 2 weeks")
                with sk2:
                    category = st.selectbox("Category", CATEGORIES)
                    priority = st.selectbox("Priority", ["Normal","Urgent","Low"])
                if st.form_submit_button("Post Task", use_container_width=True):
                    if not all([title, desc, skills]):
                        st.warning("Please fill Title, Description and Skills.")
                    else:
                        create_task(title, desc, skills, category, deadline, priority,
                                    st.session_state.user["id"], entry_type=TYPE_TASK)
                        st.success("Task posted successfully.")
                        go("dashboard")
        with c_tip:
            st.markdown("""
            <div class='cs-card'>
                <div style='font-size:12px;font-weight:700;color:#3B82F6;margin-bottom:12px;letter-spacing:.04em;'>
                    TIPS FOR A GOOD TASK POST
                </div>
                <div style='font-size:12px;color:#6B7280;line-height:2.1;'>
                    Be specific about deliverables<br>
                    List the exact skills required<br>
                    Provide a clear deadline<br>
                    Describe the expected output<br>
                    Choose the correct category
                </div>
            </div>""", unsafe_allow_html=True)
        return

    # ── LEARN MODE: two intent options ───────────────────────
    breadcrumb("Home", "Dashboard", "Post Knowledge")
    section_header("Knowledge Exchange", "Choose what you want to do.")
    mode_pill()

    # Intent selection — two cards
    current_intent = st.session_state.get("know_intent", INTENT_LEARN)

    ic1, ic2 = st.columns(2)
    with ic1:
        learn_active = "intent-card-active-learn" if current_intent == INTENT_LEARN else ""
        st.markdown(f"""
        <div class='intent-card {learn_active}'>
            <div class='intent-card-title' style='color:#2dd4bf;'>I Want to Learn</div>
            <div class='intent-card-desc'>
                Post a learning request. Describe what you want to learn or what doubt you have.
                Others who know this topic will offer to help you.
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Select — I Want to Learn", key="intent_learn", use_container_width=True):
            st.session_state.know_intent = INTENT_LEARN
            st.rerun()

    with ic2:
        teach_active = "intent-card-active-teach" if current_intent == INTENT_TEACH else ""
        st.markdown(f"""
        <div class='intent-card {teach_active}'>
            <div class='intent-card-title' style='color:#c084fc;'>I Can Teach / Help</div>
            <div class='intent-card-desc'>
                Offer your expertise. Post what topic you can teach or help with.
                Learners who need your skill will connect with you.
            </div>
        </div>""", unsafe_allow_html=True)
        if st.button("Select — I Can Teach", key="intent_teach", use_container_width=True):
            st.session_state.know_intent = INTENT_TEACH
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    section_divider("Fill in the details below")

    c_form, c_tip = st.columns([2, 1])

    with c_form:
        if current_intent == INTENT_LEARN:
            # ── LEARN: what do you want to learn ──────────────
            with st.form("post_learn_form"):
                title = st.text_input(
                    "What do you want to learn? *",
                    placeholder="e.g., I want to learn Python from scratch")
                doubt = st.text_area(
                    "Describe your doubt or goal in detail *",
                    placeholder="What exactly do you need help with? What is your current level? What outcome do you expect?",
                    height=130)
                sk1, sk2 = st.columns(2)
                with sk1:
                    topic    = st.text_input("Topic / Skill *", placeholder="e.g., Python, Data Science")
                    deadline = st.text_input("Preferred Timeframe", placeholder="e.g., Within 1 week")
                with sk2:
                    category = st.selectbox("Topic Category", KNOWLEDGE_TOPICS)
                    priority = st.selectbox("Urgency", ["Normal","Urgent","Low"])
                if st.form_submit_button("Post Learning Request", use_container_width=True):
                    if not all([title, doubt, topic]):
                        st.warning("Please fill the title, description and topic.")
                    else:
                        create_task(title, doubt, topic, category, deadline, priority,
                                    st.session_state.user["id"],
                                    entry_type=TYPE_KNOWLEDGE,
                                    knowledge_intent=INTENT_LEARN)
                        st.success("Learning request posted. Experts will reach out to help you.")
                        go("dashboard")

        else:
            # ── TEACH: what can you teach ──────────────────────
            with st.form("post_teach_form"):
                title = st.text_input(
                    "What can you teach or help with? *",
                    placeholder="e.g., I can teach Python programming to beginners")
                about = st.text_area(
                    "Describe your expertise and what you offer *",
                    placeholder="What topic can you teach? What is your expertise level? What will learners gain?",
                    height=130)
                sk1, sk2 = st.columns(2)
                with sk1:
                    topic       = st.text_input("Skill / Topic *",    placeholder="e.g., Python, React")
                    availability= st.text_input("Availability",        placeholder="e.g., Weekends, 2 hrs/day")
                with sk2:
                    category = st.selectbox("Topic Category", KNOWLEDGE_TOPICS)
                    priority = st.selectbox("Priority", ["Normal","Urgent","Low"])
                if st.form_submit_button("Post Teaching Offer", use_container_width=True):
                    if not all([title, about, topic]):
                        st.warning("Please fill the title, description and topic.")
                    else:
                        create_task(title, about, topic, category, availability, priority,
                                    st.session_state.user["id"],
                                    entry_type=TYPE_KNOWLEDGE,
                                    knowledge_intent=INTENT_TEACH)
                        st.success("Teaching offer posted. Learners will reach out to you.")
                        go("dashboard")

    with c_tip:
        if current_intent == INTENT_LEARN:
            st.markdown("""
            <div class='cs-card'>
                <div style='font-size:12px;font-weight:700;color:#2dd4bf;margin-bottom:12px;letter-spacing:.04em;'>
                    TIPS FOR A LEARNING REQUEST
                </div>
                <div style='font-size:12px;color:#6B7280;line-height:2.1;'>
                    State your current knowledge level<br>
                    Describe exactly what you are stuck on<br>
                    Mention your preferred learning format<br>
                    Set a realistic timeframe<br>
                    Be clear about your availability
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='cs-card'>
                <div style='font-size:12px;font-weight:700;color:#c084fc;margin-bottom:12px;letter-spacing:.04em;'>
                    TIPS FOR A TEACHING OFFER
                </div>
                <div style='font-size:12px;color:#6B7280;line-height:2.1;'>
                    Clearly state your expertise level<br>
                    Describe what learners will gain<br>
                    Mention session format (1-on-1, video)<br>
                    Share your availability<br>
                    Be specific about the skill you teach
                </div>
            </div>""", unsafe_allow_html=True)

        mode_type = TYPE_KNOWLEDGE
        recent    = get_my_tasks(st.session_state.user["id"], entry_type=mode_type)[:5]
        if recent:
            section_divider("My Recent Posts")
            for t in recent:
                dot = "#4ade80" if t["status"] == "open" else "#1e2d45"
                intent_lbl = " (Teach)" if t.get("knowledge_intent") == INTENT_TEACH else " (Learn)"
                st.markdown(
                    f"<div style='font-size:11px;color:#6B7280;padding:5px 0;"
                    f"border-bottom:1px solid #E5E7EB;display:flex;align-items:center;gap:7px;'>"
                    f"<span style='width:5px;height:5px;border-radius:50%;background:{dot};flex-shrink:0;display:inline-block;'></span>"
                    f"{t['title']}<span style='color:#9CA3AF;'>{intent_lbl}</span></div>",
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PROFILE  — with profile picture, phone number, avatar color
# ═══════════════════════════════════════════════════════════════
def page_profile():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "Dashboard", "Profile")

    u = get_user(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = u

    section_header("My Profile", "Manage your account, skills and reputation.")

    sidebar, main = st.columns([1, 2.2])

    with sidebar:
        avatar_color = u.get("avatar_color") or "#2563EB"
        ini = "".join(w[0].upper() for w in (u["username"] or "U").split()[:2])
        avatar_photo = u.get("avatar_photo")   # bytes or None

        # ── Profile picture display ────────────────────────────
        if avatar_photo:
            import base64
            b64 = base64.b64encode(avatar_photo).decode()
            st.markdown(f"""
            <div style='text-align:center;margin-bottom:12px;'>
                <img src='data:image/jpeg;base64,{b64}'
                    style='width:88px;height:88px;border-radius:50%;
                    object-fit:cover;
                    box-shadow:0 0 0 3px #E2E8F0,0 0 0 7px rgba(37,99,235,.08);'/>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style='text-align:center;margin-bottom:12px;'>
                <div style='width:88px;height:88px;border-radius:50%;background:{avatar_color};
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:30px;font-weight:800;color:#fff;
                    box-shadow:0 0 0 3px #E2E8F0,0 0 0 7px rgba(37,99,235,.08);'>
                    {ini}
                </div>
            </div>""", unsafe_allow_html=True)

        # ── Photo options ──────────────────────────────────────
        st.markdown("""
        <div style='font-size:11px;font-weight:700;color:#6B7280;
            letter-spacing:.08em;text-transform:uppercase;
            text-align:center;margin-bottom:8px;'>
            Profile Photo
        </div>""", unsafe_allow_html=True)

        photo_option = st.selectbox(
            "Photo option",
            ["Keep current", "Upload from Device", "Take a Photo",
             "Remove / Delete Photo"] if avatar_photo
            else ["Keep current", "Upload from Device", "Take a Photo"],
            key="prof_photo_opt",
            label_visibility="collapsed")

        if photo_option == "Upload from Device":
            uploaded = st.file_uploader(
                "Choose an image", type=["jpg","jpeg","png","webp"],
                key="prof_upload", label_visibility="collapsed")
            if uploaded is not None:
                photo_bytes = uploaded.read()
                update_avatar_photo(u["id"], photo_bytes)
                st.success("Profile photo updated.")
                fresh = get_user(u["id"])
                st.session_state.user = fresh
                st.rerun()

        elif photo_option == "Take a Photo":
            camera_img = st.camera_input("Take a selfie", key="prof_camera",
                                         label_visibility="collapsed")
            if camera_img is not None:
                photo_bytes = camera_img.read()
                update_avatar_photo(u["id"], photo_bytes)
                st.success("Profile photo updated.")
                fresh = get_user(u["id"])
                st.session_state.user = fresh
                st.rerun()

        elif photo_option == "Remove / Delete Photo":
            if st.button("Confirm Remove Photo", key="prof_remove_photo",
                         use_container_width=True):
                update_avatar_photo(u["id"], None)
                st.success("Profile photo removed.")
                fresh = get_user(u["id"])
                st.session_state.user = fresh
                st.rerun()

        # ── Avatar color picker (when no photo) ───────────────
        if not avatar_photo:
            st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
            new_color = st.color_picker("Avatar Color", value=avatar_color, key="prof_color")
            if new_color != avatar_color:
                update_avatar_color(u["id"], new_color)
                fresh = get_user(u["id"])
                st.session_state.user = fresh
                st.rerun()

        st.markdown(f"""
        <div style='text-align:center;margin-top:12px;'>
            <div style='font-size:17px;font-weight:800;color:#111827;'>{u['username']}</div>
            <div style='font-size:12px;color:#6B7280;margin-top:3px;'>{u['email']}</div>
        </div>""", unsafe_allow_html=True)

        admin_b = '<span class="cs-badge badge-cyan" style="font-size:10px;">Admin</span>' if u["role"]=="admin" else ""
        st.markdown(f"""
        <div style='text-align:center;margin:10px 0;'>
            <span class='cs-badge badge-violet'>{u['experience']}</span>{admin_b}
        </div>""", unsafe_allow_html=True)

        if u.get("phone_number"):
            st.markdown(f"""
            <div style='text-align:center;font-size:12px;color:#6B7280;margin-bottom:6px;'>
                {u['phone_number']}
            </div>""", unsafe_allow_html=True)

        if u.get("bio"):
            st.markdown(f"""
            <div style='font-size:12px;color:#6B7280;line-height:1.65;
                text-align:center;margin-bottom:12px;'>{u['bio']}</div>""",
                unsafe_allow_html=True)

        if u.get("portfolio"):
            st.markdown(
                f"<div style='text-align:center;margin-bottom:10px;'>"
                f"<a href='{u['portfolio']}' target='_blank' "
                f"style='font-size:12px;color:#3B82F6;font-weight:600;'>Portfolio / GitHub</a></div>",
                unsafe_allow_html=True)

        # ── Enhanced trust score display ───────────────────────
        computed_trust = compute_trust_score(u["id"])
        trust_pct = computed_trust
        st.markdown(f"""
        <div style='margin-top:12px;padding-top:12px;border-top:1px solid #1F1F1F;'>
            <div style='display:flex;justify-content:space-between;color:#6B7280;font-size:10px;margin-bottom:4px;'>
                <span>Trust Score</span><span style='font-weight:700;color:#3B82F6;'>{computed_trust} / 100</span>
            </div>
            <div style='background:#E2E8F0;border-radius:999px;height:6px;'>
                <div style='width:{trust_pct}%;height:6px;border-radius:999px;background:linear-gradient(90deg,#2563EB,#4F46E5);'></div>
            </div>
            <div style='font-size:10px;color:#9CA3AF;margin-top:5px;'>{u['total_ratings']} ratings received</div>
        </div>""", unsafe_allow_html=True)

        # Connections count
        conn_cnt = get_connection_count(u["id"])
        st.markdown(f"""
        <div style='text-align:center;margin-top:10px;font-size:12px;color:#6B7280;'>
            <strong style='color:#3B82F6;'>{conn_cnt}</strong> connections
        </div>""", unsafe_allow_html=True)

        if u.get("skills"):
            tags = "".join(
                f"<span class='cs-badge badge-slate' style='font-size:10px;margin:2px;'>{s.strip()}</span>"
                for s in u["skills"].split(",") if s.strip())
            st.markdown(f"""
            <div style='margin-top:14px;padding-top:12px;border-top:1px solid #1F1F1F;'>
                <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.08em;color:#9CA3AF;margin-bottom:8px;'>Skills</div>
                {tags}
            </div>""", unsafe_allow_html=True)

    with main:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Edit Profile", "My Tasks", "My Knowledge Posts",
            "Feedback & Ratings", "Badges", "Give Rating",
        ])

        with tab1:
            # Skill dropdowns outside any form
            st.markdown(
                "<div style='font-size:11px;font-weight:700;color:#6B7280;"
                "letter-spacing:.08em;text-transform:uppercase;margin-bottom:8px;'>"
                "Update Primary Skill</div>",
                unsafe_allow_html=True)

            existing = (u["skills"] or "").split(" - ")
            def_cat  = existing[0] if len(existing) > 1 and existing[0] in SKILL_CATEGORIES else None
            def_sk   = existing[1] if len(existing) > 1 else None

            ep1, ep2 = st.columns(2)
            with ep1:
                cat_opts   = ["Select a category"] + SKILL_CATEGORIES
                cat_idx    = (SKILL_CATEGORIES.index(def_cat) + 1) if def_cat else 0
                new_cat    = st.selectbox("Skill Category", cat_opts, index=cat_idx, key="ep_scat")
            with ep2:
                if new_cat == "Select a category":
                    st.selectbox("Skill", ["Select a category first"], key="ep_sval")
                    new_skill = None
                else:
                    sk_opts   = SKILLS_BY_CATEGORY.get(new_cat, []) + ["Other — type your own"]
                    sk_idx    = sk_opts.index(def_sk) if def_sk in sk_opts else 0
                    new_skill = st.selectbox("Skill", sk_opts, index=sk_idx, key="ep_sval")

            # Show text input when Other is selected
            ep_custom = None
            if new_skill == "Other — type your own":
                ep_custom = st.text_input(
                    "Enter your skill",
                    placeholder="Type your specific skill here...",
                    key="ep_custom_skill")

            with st.form("edit_profile_form"):
                eu1, eu2 = st.columns(2)
                with eu1:
                    n_user  = st.text_input("Username",     value=u["username"])
                    n_phone = st.text_input("Phone Number", value=u.get("phone_number",""))
                    n_port  = st.text_input("Portfolio",    value=u.get("portfolio",""))
                with eu2:
                    n_exp = st.selectbox(
                        "Experience Level",
                        ["Beginner","Intermediate","Advanced","Expert"],
                        index=["Beginner","Intermediate","Advanced","Expert"].index(u["experience"])
                              if u["experience"] in ["Beginner","Intermediate","Advanced","Expert"] else 0)
                    n_bio = st.text_area("Bio", value=u.get("bio",""), height=100)

                if st.form_submit_button("Save Changes", use_container_width=True):
                    if new_skill == "Other — type your own":
                        resolved = ep_custom.strip() if ep_custom else ""
                        new_skills = (f"{new_cat} - {resolved}"
                                      if new_cat and new_cat != "Select a category" and resolved
                                      else u["skills"])
                    else:
                        new_skills = (f"{new_cat} - {new_skill}"
                                      if new_cat and new_cat != "Select a category" and new_skill
                                      else u["skills"])
                    update_profile(u["id"], n_user, new_skills, n_exp, n_bio, n_port, n_phone)
                    fresh = get_user(u["id"])
                    st.session_state.user = fresh
                    st.success("Profile updated.")
                    st.rerun()

        with tab2:
            my_tasks = get_my_tasks(u["id"], entry_type=TYPE_TASK)
            if not my_tasks:
                empty_state("No tasks posted yet", "Post your first task to find collaborators.")
            for t in my_tasks:
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div style='font-weight:600;color:#111827;font-size:13px;'>{t['title']}</div>
                        {status_badge(t['status'])}
                    </div>
                    <div style='margin-top:6px;'>
                        <span class='cs-badge badge-slate'>{t['skills']}</span>
                        <span class='cs-badge badge-violet'>{t['category']}</span>
                    </div>
                    <div style='font-size:11px;color:#9CA3AF;margin-top:5px;'>{str(t['created_at'])[:10]}</div>
                </div>""", unsafe_allow_html=True)

        with tab3:
            my_know = get_my_tasks(u["id"], entry_type=TYPE_KNOWLEDGE)
            if not my_know:
                empty_state("No knowledge posts yet", "Share expertise or post a learning request.")
            for t in my_know:
                intent  = t.get("knowledge_intent","")
                i_badge = ("<span class='cs-badge badge-learn'>Wants to Learn</span>"
                           if intent == INTENT_LEARN else
                           "<span class='cs-badge badge-teach'>Can Teach</span>")
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div style='font-weight:600;color:#111827;font-size:13px;'>{t['title']}</div>
                        {status_badge(t['status'])}
                    </div>
                    <div style='margin-top:6px;'>
                        {i_badge}
                        <span class='cs-badge badge-slate'>{t['skills']}</span>
                        <span class='cs-badge badge-violet'>{t['category']}</span>
                    </div>
                    <div style='font-size:11px;color:#9CA3AF;margin-top:5px;'>{str(t['created_at'])[:10]}</div>
                </div>""", unsafe_allow_html=True)

        with tab4:
            fbs = get_feedback_for_user(u["id"])
            if not fbs:
                empty_state("No feedback yet", "Complete collaborations to receive ratings.")
            else:
                avg = round(sum(f["rating"] for f in fbs) / len(fbs), 1)
                st.markdown(f"""
                <div class='cs-card' style='text-align:center;padding:20px;margin-bottom:14px;'>
                    <div style='font-size:30px;font-weight:900;color:#3B82F6;'>{avg}</div>
                    <div style='margin-top:4px;'>{stars_html(round(avg))}</div>
                    <div style='font-size:12px;color:#6B7280;margin-top:5px;'>
                        Average from {len(fbs)} reviews
                    </div>
                </div>""", unsafe_allow_html=True)
                for f in fbs:
                    st.markdown(f"""
                    <div class='cs-card' style='padding:14px;'>
                        <div style='display:flex;justify-content:space-between;align-items:center;'>
                            <span style='font-weight:600;color:#111827;font-size:13px;'>{f['from_name']}</span>
                            <span>{stars_html(f['rating'])}</span>
                        </div>
                        <div style='font-size:12px;color:#6B7280;margin-top:6px;'>{f['comment'] or 'No comment.'}</div>
                        <div style='font-size:11px;color:#9CA3AF;margin-top:4px;'>{str(f['created_at'])[:10]}</div>
                    </div>""", unsafe_allow_html=True)

        with tab5:
            # ── Badge System ──────────────────────────────────
            computed_trust = compute_trust_score(u["id"])
            badges         = assign_badges(u["id"])

            # Trust score card
            st.markdown(f"""
            <div class='cs-card' style='display:flex;align-items:center;gap:20px;padding:18px;margin-bottom:16px;'>
                <div style='text-align:center;flex-shrink:0;'>
                    <div style='font-size:36px;font-weight:900;color:#3B82F6;line-height:1;'>{computed_trust}</div>
                    <div style='font-size:10px;color:#9CA3AF;font-weight:700;letter-spacing:.06em;text-transform:uppercase;margin-top:2px;'>Trust Score</div>
                </div>
                <div style='flex:1;'>
                    <div style='background:#E2E8F0;border-radius:999px;height:10px;margin-bottom:6px;'>
                        <div style='width:{computed_trust}%;height:10px;border-radius:999px;
                            background:linear-gradient(90deg,#2563EB,#4F46E5);'></div>
                    </div>
                    <div style='font-size:11px;color:#6B7280;'>
                        Score out of 100 — based on completed tasks, ratings, profile completeness and knowledge contributions.
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

            # Badges
            st.markdown(
                "<div style='font-size:12px;font-weight:700;color:#111827;margin-bottom:10px;'>"
                f"Earned Badges ({len(badges)})</div>",
                unsafe_allow_html=True)
            st.markdown(render_badges_html(badges), unsafe_allow_html=True)

        with tab6:
            others = db_fetchall(
                "SELECT id, username, skills, trust_score FROM users "
                "WHERE id != ? AND is_active = 1 AND role = 'user'", (u["id"],))
            if not others:
                empty_state("No other users yet", "More members will appear here as they join.")
            else:
                opts   = [f"{x['username']} — {x['skills'] or 'no skills listed'}" for x in others]
                chosen = st.selectbox("Select a collaborator to rate", opts, key="gr_select")
                to_id  = others[opts.index(chosen)]["id"]
                rating = st.slider("Rating (1 to 5)", 1, 5, 4, key="gr_slider")
                st.markdown(f"<div style='font-size:22px;margin:4px 0;'>{stars_html(rating)}</div>",
                            unsafe_allow_html=True)
                comment = st.text_area("Comment (optional)",
                                       placeholder="Describe your experience...", key="gr_comment")
                if st.button("Submit Rating", key="gr_submit", use_container_width=True):
                    ok, msg = submit_feedback(u["id"], to_id, rating, comment)
                    if ok:
                        update_trust_score(to_id, rating)
                        add_notification(to_id, "New Rating Received",
                                         f"{u['username']} rated you {rating} out of 5.")
                        st.success(msg)
                    else:
                        st.warning(msg)


# ═══════════════════════════════════════════════════════════════
#  AI MATCH  — fixed "no such column: name" error
# ═══════════════════════════════════════════════════════════════
def page_ai_match():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "AI Skill Matching")
    section_header("AI Skill Matching",
                   "Local AI — no API key required. Powered by TF-IDF and skill overlap.")

    left, right = st.columns([3, 2])
    with left:
        with st.form("ai_match_form"):
            ai_title  = st.text_input("Task Title",      placeholder="e.g., Build a data dashboard")
            ai_desc   = st.text_area("Description",       placeholder="Describe what you need...", height=110)
            ai_skills = st.text_input("Skills Required",  placeholder="e.g., Python, Plotly, Pandas")
            run = st.form_submit_button("Find Best Matches", use_container_width=True)

        if run:
            if not all([ai_title, ai_desc, ai_skills]):
                st.warning("Please fill in all three fields.")
            else:
                with st.spinner("Analyzing profiles locally..."):
                    try:
                        matches = match_users_to_task(
                            ai_title, ai_desc, ai_skills, st.session_state.user["id"])
                        st.session_state.ai_matches = matches
                        st.session_state.ai_done    = True
                    except Exception as e:
                        st.session_state.ai_done = False
                        st.error(f"Matching error: {e}")

    with right:
        st.markdown("""
        <div class='cs-card'>
            <div style='font-size:12px;font-weight:700;color:#3B82F6;margin-bottom:14px;letter-spacing:.04em;'>
                HOW AI MATCHING WORKS
            </div>
            <div style='font-size:12px;color:#6B7280;line-height:2.2;'>
                1. Describe your task requirements<br>
                2. AI reads all user profiles<br>
                3. Skills and experience are compared<br>
                4. Trust scores are factored in<br>
                5. Top 3 matches are returned<br>
                6. Notify and start collaborating
            </div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.ai_done and st.session_state.ai_matches:
        matches = st.session_state.ai_matches
        section_divider(f"Top {len(matches)} Matches")

        ranks = ["#1", "#2", "#3"]
        for i, m in enumerate(matches, 1):
            score = m.get("match_score", 0)
            sc    = "#38bdf8" if score >= 80 else "#f59e0b" if score >= 60 else "#64748b"
            row   = db_fetchone("SELECT * FROM users WHERE username=?", (m["name"],))
            u_sk  = row["skills"]      if row else "N/A"
            u_exp = row["experience"]  if row else "N/A"
            u_tr  = row["trust_score"] if row else 0
            u_pt  = row["portfolio"]   if row else ""
            u_av  = row.get("avatar_color","#1d4ed8") if row else "#1d4ed8"

            mc1, mc2 = st.columns([4, 1])
            with mc1:
                st.markdown(f"""
                <div class='cs-card'>
                    <div style='display:flex;align-items:center;gap:14px;margin-bottom:12px;'>
                        <span style='font-size:11px;font-weight:700;color:#9CA3AF;'>{ranks[i-1] if i<=3 else ""}</span>
                        {mk_avatar_html(m['name'], 40, u_av)}
                        <div>
                            <div style='font-size:14px;font-weight:800;color:#111827;'>{m['name']}</div>
                            <div style='font-size:11px;color:#6B7280;'>{u_exp}</div>
                        </div>
                    </div>
                    <div style='margin-bottom:8px;'>
                        <span class='cs-badge badge-slate'>{u_sk}</span>
                    </div>
                    <div style='font-size:12px;color:#6B7280;line-height:1.6;'>{m.get('reason','')}</div>
                    {'<div style="margin-top:10px;"><a href="'+u_pt+'" target="_blank" style="font-size:11px;color:#3B82F6;font-weight:600;">Portfolio / GitHub</a></div>' if u_pt else ''}
                </div>""", unsafe_allow_html=True)
            with mc2:
                st.markdown(f"""
                <div style='text-align:center;padding:12px;background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;'>
                    <div style='font-size:26px;font-weight:900;color:{sc};line-height:1;'>{score}%</div>
                    <div style='font-size:9px;color:#9CA3AF;margin-top:2px;text-transform:uppercase;letter-spacing:.06em;'>Match</div>
                    <div style='font-size:16px;font-weight:800;color:#3B82F6;margin-top:10px;'>{u_tr}</div>
                    <div style='font-size:9px;color:#9CA3AF;text-transform:uppercase;letter-spacing:.06em;'>Trust</div>
                </div>""", unsafe_allow_html=True)
            if row:
                if st.button(f"Notify {m['name']}", key=f"notify_{i}"):
                    add_notification(row["id"], "AI Match Alert",
                        f"{st.session_state.user['username']} wants to collaborate with you.")
                    st.session_state["_ai_msg"] = f"{m['name']} has been notified."
                    st.rerun()

    elif st.session_state.ai_done and not st.session_state.ai_matches:
        if "_ai_msg" in st.session_state:
            st.success(st.session_state.pop("_ai_msg"))
        st.info("No matches found. Invite more people to join the platform.")


# ═══════════════════════════════════════════════════════════════
#  COMMUNITY  — with skill category filter
# ═══════════════════════════════════════════════════════════════
def page_community():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "Community")
    section_header("Community", "Browse all members and explore their skills.")

    # ── Filters ───────────────────────────────────────────────
    sc1, sc2, sc3 = st.columns([2.5, 1.5, 1.5])
    with sc1:
        search = st.text_input("", placeholder="Search by name or skill...",
                               key="cm_search", label_visibility="collapsed")
    with sc2:
        # Skill category filter — lists members per skill category
        skill_cat_filter = st.selectbox(
            "", ["All Skill Categories"] + SKILL_CATEGORIES,
            key="cm_skill_cat", label_visibility="collapsed")
    with sc3:
        exp_f = st.selectbox(
            "", ["All Levels","Beginner","Intermediate","Advanced","Expert"],
            key="cm_exp", label_visibility="collapsed")

    uid = st.session_state.user["id"]
    where, params = ["role='user'", "is_active=1", f"id!='{uid}'"], []

    if search:
        where.append("(username LIKE ? OR skills LIKE ?)")
        params += [f"%{search}%"] * 2

    # Skill category filter: match members whose skills start with the selected category
    if skill_cat_filter != "All Skill Categories":
        where.append("skills LIKE ?")
        params.append(f"{skill_cat_filter}%")

    if exp_f != "All Levels":
        where.append("experience=?")
        params.append(exp_f)

    users = db_fetchall(
        f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY trust_score DESC",
        tuple(params))

    st.markdown(
        f"<div style='color:#6B7280;font-size:12px;margin:10px 0 16px;'>{len(users)} member(s)</div>",
        unsafe_allow_html=True)

    # Show active skill category filter label
    if skill_cat_filter != "All Skill Categories":
        st.markdown(
            f"<div style='margin-bottom:12px;'>"
            f"<span class='cs-badge badge-cyan'>{skill_cat_filter}</span>"
            f"<span style='font-size:11px;color:#6B7280;margin-left:6px;'>Showing members with this skill</span></div>",
            unsafe_allow_html=True)

    if not users:
        empty_state("No members found", "Try adjusting your filters.")
        return

    exp_badge = {
        "Beginner":     "badge-cyan",
        "Intermediate": "badge-violet",
        "Advanced":     "badge-amber",
        "Expert":       "badge-red",
    }

    for i in range(0, len(users), 3):
        cols = st.columns(3)
        for col, u in zip(cols, users[i:i+3]):
            pct         = int((u["trust_score"] / 10) * 100)
            ini         = "".join(w[0].upper() for w in u["username"].split()[:2])
            avatar_color= u.get("avatar_color") or "#1d4ed8"
            skills_list = [s.strip() for s in (u["skills"] or "").split(",") if s.strip()]
            tags        = "".join(
                f"<span class='cs-badge badge-slate' style='font-size:10px;margin:2px;'>{s}</span>"
                for s in skills_list[:2])
            port = (
                f'<div style="margin-top:10px;">'
                f'<a href="{u["portfolio"]}" target="_blank" '
                f'style="font-size:11px;color:#3B82F6;font-weight:600;">Portfolio</a></div>'
                if u.get("portfolio") else ""
            )
            col.markdown(f"""
            <div class='cs-card'>
                <div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>
                    <div style='width:42px;height:42px;border-radius:50%;background:{avatar_color};
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:14px;font-weight:700;color:#fff;flex-shrink:0;
                        box-shadow:0 0 0 2px #E2E8F0;'>{ini}</div>
                    <div style='flex:1;min-width:0;'>
                        <div style='font-weight:700;color:#111827;font-size:13px;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>
                            {u['username']}</div>
                        <span class='cs-badge {exp_badge.get(u["experience"],"badge-slate")}'
                            style='font-size:9px;'>{u['experience']}</span>
                    </div>
                    <div style='text-align:right;flex-shrink:0;'>
                        <div style='font-size:17px;font-weight:800;color:#3B82F6;'>{u['trust_score']}</div>
                        <div style='font-size:9px;color:#9CA3AF;'>trust</div>
                    </div>
                </div>
                <div style='font-size:11px;color:#6B7280;line-height:1.55;margin-bottom:10px;'>
                    {(u['bio'] or 'No bio provided.')[:90]}...</div>
                <div>{tags}</div>
                <div class='trust-bar-bg'>
                    <div class='trust-bar-fill' style='width:{pct}%;'></div>
                </div>
                <div style='font-size:10px;color:#9CA3AF;margin-top:4px;'>{u['total_ratings']} ratings</div>
                {port}
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════
def page_notifications():
    require_login()
    render_navbar()
    back_btn()
    mark_all_read(st.session_state.user["id"])
    section_header("Notifications", "Your latest activity and alerts.")

    notifs = get_notifications(st.session_state.user["id"])
    if not notifs:
        empty_state("No notifications", "Start collaborating to see activity here.")
        return

    for n in notifs:
        is_unread = not n["is_read"]
        bg        = "#EFF6FF" if is_unread else "#FFFFFF"
        border    = "#BFDBFE" if is_unread else "#E2E8F0"
        title_col = "#1D4ED8" if is_unread else "#0F172A"
        dot       = (
            "<span style='width:7px;height:7px;background:#2563EB;border-radius:50%;"
            "display:inline-block;margin-left:8px;vertical-align:middle;'></span>"
            if is_unread else ""
        )
        ts = str(n.get("created_at", ""))[:16]
        st.markdown(
            f"<div style='background:{bg};border:1px solid {border};border-radius:12px;"
            f"padding:16px 20px;margin-bottom:10px;box-shadow:0 1px 4px rgba(0,0,0,.04);'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center;gap:12px;'>"
            f"<div style='font-weight:700;font-size:13px;color:{title_col};'>{n['title']}{dot}</div>"
            f"<div style='font-size:11px;color:#9CA3AF;white-space:nowrap;'>{ts}</div>"
            f"</div>"
            f"<div style='font-size:13px;color:#6B7280;margin-top:6px;line-height:1.55;'>"
            f"{n['message']}</div>"
            f"</div>",
            unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN SIDEBAR
# ═══════════════════════════════════════════════════════════════
def admin_sidebar():
    with st.sidebar:
        st.markdown("**Admin Panel**")
        st.markdown(f"*{st.session_state.user['username']}*")
        st.markdown("---")
        if st.button("Dashboard",  key="asb_dash",   use_container_width=True): go("admin_dashboard")
        if st.button("Users",      key="asb_users",  use_container_width=True): go("admin_users")
        if st.button("All Posts",  key="asb_tasks",  use_container_width=True): go("admin_tasks")
        if st.button("Browse",     key="asb_browse", use_container_width=True): go("browse_tasks")
        st.markdown("---")
        st.markdown("<div style='color:#f87171;'>", unsafe_allow_html=True)
        if st.button("Sign Out", key="asb_logout", use_container_width=True):
            st.session_state.user = None; go("landing")


# ═══════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_admin_dashboard():
    require_admin()
    render_navbar()
    admin_sidebar()
    breadcrumb("Admin", "Dashboard")

    st.markdown("<div class='admin-banner'>Admin View — This data is not visible to regular users.</div>",
                unsafe_allow_html=True)
    section_header("Admin Dashboard", "Platform-wide analytics and management.")

    total_users  = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    total_admins = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE role='admin'")["c"]
    active_users = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE is_active=1")["c"]
    new_week     = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE created_at>=datetime('now','-7 days')")["c"]
    total_tasks  = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE type='task'")["c"]
    open_tasks   = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open' AND type='task'")["c"]
    total_know   = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE type='knowledge'")["c"]
    open_know    = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open' AND type='knowledge'")["c"]
    total_apps   = db_fetchone("SELECT COUNT(*) AS c FROM applications")["c"]

    section_divider("Users")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Users",   total_users)
    m2.metric("Admins",        total_admins)
    m3.metric("Active",        active_users)
    m4.metric("New This Week", new_week)

    section_divider("Task Collaboration")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Total Tasks",  total_tasks)
    t2.metric("Open",         open_tasks)
    t3.metric("Closed",       total_tasks - open_tasks)
    t4.metric("Applications", total_apps)

    section_divider("Knowledge Exchange")
    k1, k2, k3, _ = st.columns(4)
    k1.metric("Total Posts",  total_know)
    k2.metric("Active",       open_know)
    k3.metric("Completed",    total_know - open_know)

    col1, col2 = st.columns(2)
    with col1:
        section_divider("Posts by Category")
        cat_data = db_fetchall(
            "SELECT category, COUNT(*) AS cnt FROM tasks GROUP BY category ORDER BY cnt DESC")
        if cat_data:
            df = pd.DataFrame(cat_data); df.columns = ["Category","Count"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.markdown("<div style='color:#6B7280;font-size:12px;'>No data yet.</div>",
                        unsafe_allow_html=True)

    with col2:
        section_divider("Recent Activity")
        rec_u = db_fetchall("SELECT username AS name,'User registered' AS action,created_at FROM users ORDER BY created_at DESC LIMIT 5")
        rec_t = db_fetchall("SELECT title AS name,'Task posted' AS action,created_at FROM tasks WHERE type='task' ORDER BY created_at DESC LIMIT 3")
        rec_k = db_fetchall("SELECT title AS name,'Knowledge posted' AS action,created_at FROM tasks WHERE type='knowledge' ORDER BY created_at DESC LIMIT 3")
        activity = sorted(rec_u + rec_t + rec_k, key=lambda x: x["created_at"], reverse=True)[:10]
        for a in activity:
            dot_c = ("#38bdf8" if "registered" in a["action"]
                     else "#2dd4bf" if "Knowledge" in a["action"] else "#a78bfa")
            st.markdown(f"""
            <div style='display:flex;gap:10px;padding:6px 0;border-bottom:1px solid #E5E7EB;'>
                <div style='width:5px;height:5px;border-radius:50%;background:{dot_c};
                    margin-top:5px;flex-shrink:0;'></div>
                <div>
                    <div style='font-size:12px;color:#6B7280;'>{a['action']}: <strong>{a['name']}</strong></div>
                    <div style='font-size:10px;color:#9CA3AF;'>{str(a['created_at'])[:16]}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    section_divider("Leaderboard — Top Users")
    top    = get_top_users(8)
    medals = ["1st","2nd","3rd","4th","5th","6th","7th","8th"]
    lc1, lc2 = st.columns(2)
    for i, u in enumerate(top):
        col = lc1 if i % 2 == 0 else lc2
        av  = u.get("avatar_color","#1d4ed8")
        ini = "".join(w[0].upper() for w in u["username"].split()[:2])
        col.markdown(f"""
        <div class='cs-card' style='padding:12px;'>
            <div style='display:flex;align-items:center;gap:12px;'>
                <div style='width:34px;height:34px;border-radius:50%;background:{av};
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:11px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                <div style='flex:1;'>
                    <div style='font-size:10px;color:#9CA3AF;font-weight:700;text-transform:uppercase;letter-spacing:.04em;'>{medals[i]}</div>
                    <div style='font-size:13px;font-weight:700;color:#111827;'>{u['username']}</div>
                    <div style='font-size:10px;color:#6B7280;'>{u['skills'] or '—'}</div>
                </div>
                <div style='text-align:right;'>
                    <div style='font-size:18px;font-weight:900;color:#3B82F6;'>{u['trust_score']}</div>
                    <div style='font-size:9px;color:#9CA3AF;'>{u['total_ratings']} ratings</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN USERS
# ═══════════════════════════════════════════════════════════════
def page_admin_users():
    require_admin()
    render_navbar(); admin_sidebar()
    breadcrumb("Admin","Manage Users"); back_btn()
    section_header("Manage Users","View, search and manage all registered users.")

    sc1, sc2 = st.columns([3,1])
    with sc1:
        search = st.text_input("",placeholder="Search username or email...",
                               key="au_search",label_visibility="collapsed")
    with sc2:
        role_f = st.selectbox("",["All Roles","user","admin"],
                              key="au_role",label_visibility="collapsed")

    where,params = ["1=1"],[]
    if search:
        where.append("(username LIKE ? OR email LIKE ?)"); params+=[f"%{search}%"]*2
    if role_f != "All Roles":
        where.append("role=?"); params.append(role_f)

    users = db_fetchall(
        f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY created_at DESC",
        tuple(params))
    st.markdown(f"<div style='color:#6B7280;font-size:12px;margin-bottom:12px;'>{len(users)} user(s)</div>",
                unsafe_allow_html=True)

    for u in users:
        with st.expander(f"{u['username']}  [{u['role'].upper()}]  {u['email']}"):
            c1, c2, c3 = st.columns([2,2,1])
            with c1:
                st.markdown(f"""
                <div style='font-size:12px;color:#6B7280;line-height:2.1;'>
                    <strong style='color:#6B7280;'>Role</strong><br>{u['role']}<br>
                    <strong style='color:#6B7280;'>Skills</strong><br>{u['skills'] or '—'}<br>
                    <strong style='color:#6B7280;'>Level</strong><br>{u['experience']}<br>
                    <strong style='color:#6B7280;'>Phone</strong><br>{u.get('phone_number') or '—'}
                </div>""", unsafe_allow_html=True)
            with c2:
                tc = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE created_by=? AND type='task'",      (u["id"],))["c"]
                kc = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE created_by=? AND type='knowledge'", (u["id"],))["c"]
                rc = db_fetchone("SELECT COUNT(*) AS c FROM feedback WHERE to_user_id=?",                   (u["id"],))["c"]
                st.markdown(f"""
                <div style='font-size:12px;color:#6B7280;line-height:2.1;'>
                    <strong style='color:#6B7280;'>Tasks / Knowledge</strong><br>{tc} / {kc}<br>
                    <strong style='color:#6B7280;'>Ratings Received</strong><br>{rc}<br>
                    <strong style='color:#6B7280;'>Status</strong><br>{'Active' if u['is_active'] else 'Inactive'}<br>
                    <strong style='color:#6B7280;'>Joined</strong><br>{str(u['created_at'])[:10]}
                </div>""", unsafe_allow_html=True)
            with c3:
                if u["role"] != "admin":
                    if u["is_active"]:
                        if st.button("Deactivate", key=f"deact_{u['id']}"):
                            db_execute("UPDATE users SET is_active=0 WHERE id=?",(u["id"],))
                            st.success("Deactivated."); st.rerun()
                        st.markdown("</div>",unsafe_allow_html=True)
                    else:
                        if st.button("Activate", key=f"act_{u['id']}"):
                            db_execute("UPDATE users SET is_active=1 WHERE id=?",(u["id"],))
                            st.success("Activated."); st.rerun()
                        st.markdown("</div>",unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN TASKS
# ═══════════════════════════════════════════════════════════════
def page_admin_tasks():
    require_admin()
    render_navbar(); admin_sidebar()
    breadcrumb("Admin","All Posts"); back_btn()
    section_header("All Tasks and Knowledge Posts","Monitor and moderate all content.")

    sc1,sc2,sc3,sc4 = st.columns([2.5,1.2,1.2,1.2])
    with sc1:
        search   = st.text_input("",placeholder="Search...",key="at_search",label_visibility="collapsed")
    with sc2:
        type_f   = st.selectbox("",["All Types","Tasks Only","Knowledge Only"],key="at_type",label_visibility="collapsed")
    with sc3:
        status_f = st.selectbox("",["All Status","open","closed"],key="at_status",label_visibility="collapsed")
    with sc4:
        cat_f    = st.selectbox("",["All Categories"]+CATEGORIES,key="at_cat",label_visibility="collapsed")

    type_map   = {"Tasks Only": TYPE_TASK, "Knowledge Only": TYPE_KNOWLEDGE}
    entry_type = type_map.get(type_f, None)
    tasks = get_all_tasks_admin(entry_type=entry_type)

    if search:
        s = search.lower()
        tasks = [t for t in tasks if s in t["title"].lower() or s in (t["skills"] or "").lower()]
    if status_f != "All Status":
        tasks = [t for t in tasks if t["status"] == status_f]
    if cat_f != "All Categories":
        tasks = [t for t in tasks if t["category"] == cat_f]

    st.markdown(f"<div style='color:#6B7280;font-size:12px;margin-bottom:12px;'>{len(tasks)} record(s)</div>",
                unsafe_allow_html=True)
    if not tasks:
        empty_state("No records found","Try adjusting filters."); return

    for t in tasks:
        is_know = t.get("type") == TYPE_KNOWLEDGE
        intent  = t.get("knowledge_intent","")
        header  = f"{'[K] ' if is_know else '[T] '}{t['title']}  —  {t['creator_name']}  —  {t['status'].upper()}"

        with st.expander(header):
            tc1, tc2 = st.columns([3,1])
            with tc1:
                st.markdown(f"""
                <div style='color:#6B7280;font-size:12px;line-height:1.7;margin-bottom:8px;'>{t['description']}</div>
                {type_badge(t.get('type',TYPE_TASK), intent)}
                {status_badge(t['status'])}
                {priority_badge(t.get('priority','Normal'))}
                <span class='cs-badge badge-violet'>{t['category']}</span>
                <span class='cs-badge badge-slate'>{t['skills']}</span>
                <span class='cs-badge badge-slate'>{t.get('applicant_count',0)} interested</span>
                <div style='font-size:10px;color:#9CA3AF;margin-top:6px;'>Posted {str(t['created_at'])[:10]}</div>
                """,unsafe_allow_html=True)
            with tc2:
                new_s = st.selectbox("Status",["open","in_progress","closed"],
                    index=["open","in_progress","closed"].index(t["status"]),
                    key=f"at_stat_{t['id']}")
                if st.button("Update",key=f"at_upd_{t['id']}"): update_task_status(t["id"],new_s); st.success("Updated."); st.rerun()
                st.markdown("</div>",unsafe_allow_html=True)
                if st.button("Delete",key=f"at_del_{t['id']}"): delete_task(t["id"]); st.success("Deleted."); st.rerun()
                st.markdown("</div>",unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  AI RECOMMENDATIONS WIDGET (used in dashboard)
# ═══════════════════════════════════════════════════════════════
def render_ai_recommendations(u):
    """Render AI Recommendations panel inside dashboard."""
    user_skills = u.get("skills","")
    user_bio    = u.get("bio","")
    uid         = u["id"]
    mode_type   = TYPE_KNOWLEDGE if is_learn_mode() else TYPE_TASK

    section_divider("AI Recommendations")

    tab_t, tab_u = st.tabs(["Recommended Posts", "Recommended Collaborators"])

    with tab_t:
        recs = recommend_tasks_for_user(uid, user_skills, user_bio,
                                         entry_type=mode_type, top_n=5)
        if not recs:
            st.markdown("<div style='color:#6B7280;font-size:13px;'>No recommendations yet. Post or browse to get started.</div>",
                        unsafe_allow_html=True)
        for task, score in recs:
            pct   = int(min(score, 100))
            color = "#16A34A" if pct >= 70 else "#D97706" if pct >= 40 else "#64748B"
            best  = " <span style='background:#DCFCE7;color:#16A34A;border-radius:999px;font-size:10px;font-weight:700;padding:2px 8px;margin-left:6px;'>Best Match</span>" if pct >= 80 else ""
            st.markdown(f"""
            <div class='cs-card' style='padding:14px;margin-bottom:8px;'>
                <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                    <div style='flex:1;'>
                        <div style='font-weight:700;color:#111827;font-size:13px;'>{task['title']}{best}</div>
                        <div style='font-size:11px;color:#6B7280;margin-top:3px;'>{task.get('skills','')}</div>
                        <div style='font-size:11px;color:#9CA3AF;margin-top:2px;'>By {task.get('creator_name','')}</div>
                    </div>
                    <div style='text-align:right;flex-shrink:0;margin-left:12px;'>
                        <div style='font-size:20px;font-weight:900;color:{color};'>{pct}%</div>
                        <div style='font-size:10px;color:#9CA3AF;'>match</div>
                    </div>
                </div>
                <div style='background:#F9FAFB;border-radius:999px;height:5px;margin-top:8px;'>
                    <div style='width:{pct}%;height:5px;border-radius:999px;background:{color};'></div>
                </div>
            </div>""", unsafe_allow_html=True)

    with tab_u:
        rec_users = recommend_users_for_collaboration(uid, user_skills, user_bio, top_n=5)
        if not rec_users:
            st.markdown("<div style='color:#6B7280;font-size:13px;'>No collaborator recommendations yet.</div>",
                        unsafe_allow_html=True)
        for usr, score in rec_users:
            pct   = int(min(score, 100))
            color = "#16A34A" if pct >= 70 else "#D97706" if pct >= 40 else "#64748B"
            av    = usr.get("avatar_color","#2563EB")
            ini   = "".join(w[0].upper() for w in usr["username"].split()[:2])
            btn_lbl = "Connect" if is_learn_mode() else "Collab"
            st.markdown(f"""
            <div class='cs-card' style='padding:14px;display:flex;align-items:center;gap:14px;margin-bottom:8px;'>
                <div style='width:40px;height:40px;border-radius:50%;background:{av};
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:14px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                <div style='flex:1;'>
                    <div style='font-weight:700;color:#111827;font-size:13px;'>{usr['username']}</div>
                    <div style='font-size:11px;color:#6B7280;'>{usr.get('skills','')}</div>
                </div>
                <div style='text-align:right;flex-shrink:0;'>
                    <div style='font-size:18px;font-weight:800;color:{color};'>{pct}%</div>
                    <div style='font-size:10px;color:#9CA3AF;'>match</div>
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button(f"{btn_lbl} — {usr['username']}", key=f"rec_conn_{usr['id']}"):
                ok, msg = send_request(uid, usr["id"], st.session_state.mode)
                if ok:
                    add_notification(usr["id"], f"New {btn_lbl} Request",
                                     f"{u['username']} wants to {btn_lbl.lower()} with you.")
                st.success(msg) if ok else st.warning(msg)


# ═══════════════════════════════════════════════════════════════
#  PAGE: CHAT  (1:1)
# ═══════════════════════════════════════════════════════════════
def page_chat():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "Chat")
    section_header("Messages", "Chat with your connections.")

    u = st.session_state.user
    conversations = get_conversations(u["id"])
    partner_id    = st.session_state.chat_partner

    c_list, c_chat = st.columns([1, 2])

    with c_list:
        st.markdown("<div style='font-size:12px;font-weight:700;color:#6B7280;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;'>Conversations</div>",
                    unsafe_allow_html=True)

        # Also show network connections not yet chatted
        network = get_my_network(u["id"])
        all_ids = {c["id"] for c in conversations}
        for nu in network:
            if nu["id"] not in all_ids:
                conversations.append(nu)

        if not conversations:
            st.markdown("<div style='color:#9CA3AF;font-size:12px;'>No conversations yet. Connect with users to start chatting.</div>",
                        unsafe_allow_html=True)

        for partner in conversations:
            ini = "".join(w[0].upper() for w in partner["username"].split()[:2])
            av  = partner.get("avatar_color","#2563EB")
            selected = partner_id == partner["id"]
            bg = "#EFF6FF" if selected else "#FFFFFF"
            bc = "#2563EB" if selected else "#E2E8F0"
            st.markdown(f"""
            <div style='background:{bg};border:1px solid {bc};border-radius:10px;
                padding:10px 12px;margin-bottom:6px;cursor:pointer;
                display:flex;align-items:center;gap:10px;'>
                <div style='width:36px;height:36px;border-radius:50%;background:{av};
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:13px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                <div>
                    <div style='font-weight:600;font-size:13px;color:#111827;'>{partner['username']}</div>
                    <div style='font-size:11px;color:#9CA3AF;'>{partner.get('skills','')[:28]}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            if st.button("Open", key=f"chat_open_{partner['id']}", use_container_width=True):
                st.session_state.chat_partner = partner["id"]
                st.rerun()

    with c_chat:
        if not partner_id:
            st.markdown("""
            <div style='text-align:center;padding:60px;color:#9CA3AF;'>
                <div style='font-size:36px;margin-bottom:12px;'>💬</div>
                <div style='font-size:14px;'>Select a conversation to start chatting</div>
            </div>""", unsafe_allow_html=True)
            return

        partner_user = db_fetchone("SELECT * FROM users WHERE id=?", (partner_id,))
        if not partner_user:
            return

        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:12px;
            background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;
            padding:12px 16px;margin-bottom:14px;'>
            {mk_avatar_html(partner_user['username'],40,partner_user.get('avatar_color','#2563EB'))}
            <div>
                <div style='font-weight:700;font-size:14px;color:#111827;'>{partner_user['username']}</div>
                <div style='font-size:11px;color:#9CA3AF;'>{partner_user.get('skills','')}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        messages = get_messages(u["id"], partner_id)

        # Chat bubble area
        st.markdown("<div style='max-height:360px;overflow-y:auto;'>", unsafe_allow_html=True)
        for msg in messages:
            is_me = msg["sender_id"] == u["id"]
            align = "flex-end" if is_me else "flex-start"
            bubble_bg = "#3B82F6" if is_me else "#F3F4F6"
            text_col  = "#FFFFFF" if is_me else "#111827"
            st.markdown(f"""
            <div style='display:flex;justify-content:{align};margin-bottom:8px;'>
                <div style='max-width:70%;background:{bubble_bg};color:{text_col};
                    border-radius:14px;padding:10px 14px;font-size:13px;
                    box-shadow:0 1px 4px rgba(0,0,0,.07);'>
                    {msg['message']}
                    <div style='font-size:10px;opacity:.6;margin-top:4px;text-align:right;'>
                        {str(msg['timestamp'])[11:16]}
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        # Send message
        with st.form(f"chat_form_{partner_id}", clear_on_submit=True):
            msg_text = st.text_input("", placeholder="Type a message...",
                                     label_visibility="collapsed", key="chat_input")
            if st.form_submit_button("Send", use_container_width=True):
                if msg_text.strip():
                    send_message(u["id"], partner_id, msg_text.strip())
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  PAGE: NETWORK
# ═══════════════════════════════════════════════════════════════
def page_network():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "My Network")
    section_header("My Network", "Your professional connections.")

    # Deferred messages — shown outside any column/tab context
    for key in ("_net_msg", "_req_msg", "_interest_msg"):
        if key in st.session_state:
            ok, msg = st.session_state.pop(key)
            if ok == "ok": st.success(msg)
            else: st.warning(msg)

    u       = st.session_state.user
    mode    = st.session_state.mode
    btn_lbl = "Connect" if is_learn_mode() else "Collab"

    tab1, tab2, tab3 = st.tabs(["My Network", "Requests", "Find People"])

    with tab1:
        connections = get_my_network(u["id"])
        conn_count  = get_connection_count(u["id"])
        st.markdown(f"<div style='color:#6B7280;font-size:12px;margin-bottom:12px;'>{conn_count} connection(s)</div>",
                    unsafe_allow_html=True)

        if not connections:
            empty_state("No connections yet",
                        f"Search for users and send {btn_lbl} requests to build your network.")
        else:
            for i in range(0, len(connections), 3):
                cols = st.columns(3)
                for col, cu in zip(cols, connections[i:i+3]):
                    ini = "".join(w[0].upper() for w in cu["username"].split()[:2])
                    av  = cu.get("avatar_color","#2563EB")
                    col.markdown(f"""
                    <div class='cs-card' style='text-align:center;padding:16px;'>
                        <div style='width:52px;height:52px;border-radius:50%;background:{av};
                            display:flex;align-items:center;justify-content:center;
                            font-size:18px;font-weight:700;color:#fff;margin:0 auto 10px;'>{ini}</div>
                        <div style='font-weight:700;color:#111827;font-size:13px;'>{cu['username']}</div>
                        <div style='font-size:11px;color:#6B7280;margin-top:3px;'>{cu.get('skills','')[:30]}</div>
                        <span class='cs-badge badge-green' style='margin-top:8px;'>Connected</span>
                    </div>""", unsafe_allow_html=True)
                    if col.button("Chat", key=f"net_chat_{cu['id']}"):
                        st.session_state.chat_partner = cu["id"]
                        go("chat")

    with tab2:
        requests = get_incoming_requests(u["id"])
        if not requests:
            empty_state("No pending requests", "You have no incoming connection requests.")
        else:
            for r in requests:
                ini = "".join(w[0].upper() for w in r["sender_name"].split()[:2])
                av  = r.get("sender_color","#2563EB")
                st.markdown(f"""
                <div class='cs-card' style='display:flex;align-items:center;gap:14px;padding:14px;'>
                    <div style='width:44px;height:44px;border-radius:50%;background:{av};
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:16px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                    <div style='flex:1;'>
                        <div style='font-weight:700;color:#111827;font-size:13px;'>{r['sender_name']}</div>
                        <div style='font-size:11px;color:#6B7280;'>{r.get('sender_skills','')}</div>
                        <div style='font-size:11px;color:#9CA3AF;margin-top:2px;'>Mode: {r.get('mode','work').capitalize()}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
                ra1, ra2 = st.columns(2)
                with ra1:
                    if st.button("Accept", key=f"acc_{r['id']}"):
                        accept_request(r["id"])
                        add_notification(r["sender"], "Connection Accepted",
                                         f"{u['username']} accepted your request.")
                        st.session_state["_req_msg"] = ("ok", "Connected!")
                        st.rerun()
                with ra2:
                    if st.button("Decline", key=f"rej_{r['id']}"):
                        reject_request(r["id"]); st.rerun()

    with tab3:
        search = st.text_input("", placeholder=f"Search by username or skill to send {btn_lbl} requests...",
                               label_visibility="collapsed", key="net_search")
        if search:
            found = db_fetchall("""
                SELECT id,username,skills,bio,avatar_color,experience,trust_score
                FROM users WHERE id!=? AND is_active=1
                  AND (username LIKE ? OR skills LIKE ?)
                ORDER BY trust_score DESC LIMIT 20
            """, (u["id"], f"%{search}%", f"%{search}%"))

            if not found:
                st.markdown("<div style='color:#9CA3AF;font-size:12px;'>No users found.</div>",
                            unsafe_allow_html=True)
            for fu in found:
                status = get_connection_status(u["id"], fu["id"])
                ini    = "".join(w[0].upper() for w in fu["username"].split()[:2])
                av     = fu.get("avatar_color","#2563EB")
                status_badge_html = {
                    "accepted": "<span class='cs-badge badge-green'>Connected</span>",
                    "pending":  "<span class='cs-badge badge-amber'>Pending</span>",
                    "rejected": "<span class='cs-badge badge-red'>Rejected</span>",
                }.get(status, "")
                col_card, col_btn = st.columns([5, 1])
                with col_card:
                    trust = fu.get('trust_score', 5)
                    st.markdown(
                        f"<div class='cs-card' style='display:flex;align-items:center;"
                        f"gap:14px;padding:14px;margin-bottom:0;'>"
                        f"<div style='width:44px;height:44px;border-radius:50%;background:{av};"
                        f"display:inline-flex;align-items:center;justify-content:center;"
                        f"font-size:15px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>"
                        f"<div style='flex:1;'>"
                        f"<div style='font-weight:700;color:#111827;font-size:13px;'>{fu['username']}</div>"
                        f"<div style='font-size:11px;color:#6B7280;'>{fu.get('skills','')}</div>"
                        f"<div style='font-size:11px;color:#9CA3AF;'>{fu.get('experience','')}</div>"
                        f"{status_badge_html}"
                        f"</div>"
                        f"<div style='font-size:16px;font-weight:800;color:#3B82F6;'>{trust}</div>"
                        f"</div>",
                        unsafe_allow_html=True)
                with col_btn:
                    if status == "none":
                        if st.button(btn_lbl, key=f"send_conn_{fu['id']}",
                                     use_container_width=True):
                            ok, msg = send_request(u["id"], fu["id"], mode)
                            if ok:
                                add_notification(
                                    fu["id"], f"New {btn_lbl} Request",
                                    f"{u['username']} wants to {btn_lbl.lower()} with you.")
                            st.session_state["_net_msg"] = (ok, msg)
                            st.rerun()
            # Show message outside column context
            if "_net_msg" in st.session_state:
                ok, msg = st.session_state.pop("_net_msg")
                if ok: st.success(msg)
                else:  st.warning(msg)


# ═══════════════════════════════════════════════════════════════
#  PAGE: PROJECTS
# ═══════════════════════════════════════════════════════════════
def page_projects():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "Projects")
    section_header("My Projects", "Create and manage team collaboration projects.")

    u = st.session_state.user

    tab1, tab2, tab3 = st.tabs(["My Projects", "Create Project", "Project Invites"])

    with tab1:
        projects = get_my_projects(u["id"])
        if not projects:
            empty_state("No projects yet", "Create your first project to start team collaboration.")
        else:
            for proj in projects:
                st.markdown(f"""
                <div class='cs-card' style='padding:16px;'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                        <div style='flex:1;'>
                            <div style='font-weight:800;font-size:15px;color:#111827;'>{proj['title']}</div>
                            <div style='font-size:12px;color:#6B7280;margin-top:4px;'>{proj['description'][:100]}...</div>
                            <div style='margin-top:8px;'>
                                <span class='cs-badge badge-blue'>{proj['skills_required'][:40]}</span>
                                <span class='cs-badge badge-slate'>{proj['member_count']} members</span>
                                <span class='cs-badge badge-green'>{proj['status'].capitalize()}</span>
                            </div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
                if st.button("Open Workspace", key=f"open_proj_{proj['id']}"):
                    st.session_state.active_project = proj["id"]
                    go("project_workspace")

    with tab2:
        with st.form("create_project_form"):
            p_title  = st.text_input("Project Title *",      placeholder="e.g., AI Chatbot Platform")
            p_desc   = st.text_area("Description *",          placeholder="Describe the project goals...", height=100)
            p_skills = st.text_input("Required Skills *",     placeholder="e.g., Python, React, ML")
            pc1, pc2 = st.columns(2)
            with pc1:
                p_dur  = st.text_input("Project Duration",   placeholder="e.g., 3 months")
            with pc2:
                p_size = st.number_input("Team Size",        min_value=1, max_value=50, value=3)

            if st.form_submit_button("Create Project", use_container_width=True):
                if not all([p_title, p_desc, p_skills]):
                    st.warning("Please fill Title, Description and Skills.")
                else:
                    pid = create_project(u["id"], p_title, p_desc,
                                         p_skills, p_dur, int(p_size))
                    # Auto-create group chat
                    from chat import create_group
                    gid = create_group(f"{p_title} — Team", u["id"], pid)
                    update_project_chat(pid, gid)
                    st.success(f"Project '{p_title}' created! Opening workspace...")
                    st.session_state.active_project = pid
                    go("project_workspace")

    with tab3:
        invites = get_pending_invites(u["id"])
        if not invites:
            empty_state("No invites", "You have no pending project invitations.")
        else:
            for inv in invites:
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='font-weight:700;color:#111827;'>{inv['project_title']}</div>
                    <div style='font-size:12px;color:#6B7280;margin-top:4px;'>{inv['description'][:80]}...</div>
                    <div style='margin-top:6px;'>
                        <span class='cs-badge badge-blue'>{inv['skills_required'][:40]}</span>
                        <span class='cs-badge badge-slate'>From: {inv['sender_name']}</span>
                    </div>
                </div>""", unsafe_allow_html=True)
                ia1, ia2 = st.columns(2)
                with ia1:
                    if st.button("Accept", key=f"pinv_acc_{inv['id']}"):
                        accept_project_invite(inv["id"], u["id"], inv["project_id"])
                        # Add to group chat
                        proj = get_project(inv["project_id"])
                        if proj and proj.get("group_chat_id"):
                            add_member_to_group(proj["group_chat_id"], u["id"])
                        add_notification(inv["sender_id"], "Invite Accepted",
                                         f"{u['username']} joined '{inv['project_title']}'.")
                        st.success("Joined project!"); st.rerun()
                with ia2:
                    if st.button("Decline", key=f"pinv_rej_{inv['id']}"):
                        reject_project_invite(inv["id"]); st.rerun()


# ═══════════════════════════════════════════════════════════════
#  PAGE: PROJECT WORKSPACE
# ═══════════════════════════════════════════════════════════════
def page_project_workspace():
    require_login()
    render_navbar()
    back_btn()

    proj_id = st.session_state.get("active_project")
    if not proj_id:
        go("projects"); return

    u    = st.session_state.user
    proj = get_project(proj_id)
    if not proj or not is_project_member(proj_id, u["id"]):
        st.error("Project not found or access denied.")
        go("projects"); return

    breadcrumb("Home", "Projects", proj["title"])
    section_header(proj["title"], proj["description"][:100])

    # Project header badges
    dur_badge = (f"<span class='cs-badge badge-slate'>Duration: {proj['duration']}</span>"
                 if proj.get('duration') else "")
    st.markdown(
        f"<div style='margin-bottom:14px;'>"
        f"<span class='cs-badge badge-blue'>{proj['skills_required'][:60]}</span>"
        f"{dur_badge}"
        f"<span class='cs-badge badge-green'>{proj['status'].capitalize()}</span>"
        f"</div>",
        unsafe_allow_html=True)

    tab_chat, tab_members, tab_res, tab_invite = st.tabs([
        "Group Chat", "Team Members", "Resources", "Invite Users"])

    # ── Group Chat ─────────────────────────────────────────────
    with tab_chat:
        gid = proj.get("group_chat_id","")
        if not gid:
            st.info("Group chat not set up. Recreating...")
            gid = create_group(f"{proj['title']} — Team", u["id"], proj_id)
            update_project_chat(proj_id, gid)
            add_member_to_group(gid, u["id"])

        messages = get_group_messages(gid)
        st.markdown("<div style='max-height:380px;overflow-y:auto;'>", unsafe_allow_html=True)
        for msg in messages:
            is_me     = msg["sender_id"] == u["id"]
            align     = "flex-end" if is_me else "flex-start"
            bubble_bg = "#3B82F6" if is_me else "#F3F4F6"
            text_col  = "#FFFFFF" if is_me else "#111827"
            st.markdown(f"""
            <div style='display:flex;justify-content:{align};margin-bottom:8px;'>
                <div style='max-width:72%;'>
                    {'<div style="font-size:10px;color:#9CA3AF;margin-bottom:2px;">'+msg["sender_name"]+'</div>' if not is_me else ''}
                    <div style='background:{bubble_bg};color:{text_col};
                        border-radius:14px;padding:10px 14px;font-size:13px;
                        box-shadow:0 1px 4px rgba(0,0,0,.07);'>
                        {msg['message']}
                        <div style='font-size:10px;opacity:.6;margin-top:4px;text-align:right;'>
                            {str(msg['timestamp'])[11:16]}
                        </div>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        with st.form(f"gc_form_{gid}", clear_on_submit=True):
            gmsg = st.text_input("", placeholder="Type a message to the team...",
                                 label_visibility="collapsed")
            if st.form_submit_button("Send", use_container_width=True):
                if gmsg.strip():
                    send_group_message(u["id"], gid, gmsg.strip())
                    st.rerun()

    # ── Members ────────────────────────────────────────────────
    with tab_members:
        members = get_project_members(proj_id)
        for m in members:
            ini = "".join(w[0].upper() for w in m["username"].split()[:2])
            av  = m.get("avatar_color","#2563EB")
            role_badge = "<span class='cs-badge badge-violet'>Owner</span>" if m["role"]=="owner" else "<span class='cs-badge badge-slate'>Member</span>"
            st.markdown(f"""
            <div class='cs-card' style='padding:12px;display:flex;align-items:center;gap:12px;'>
                <div style='width:40px;height:40px;border-radius:50%;background:{av};
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:14px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                <div style='flex:1;'>
                    <div style='font-weight:700;color:#111827;font-size:13px;'>{m['username']} {role_badge}</div>
                    <div style='font-size:11px;color:#6B7280;'>{m.get('skills','')}</div>
                </div>
                <div style='font-size:16px;font-weight:800;color:#3B82F6;'>{m.get('trust_score',5)}/10</div>
            </div>""", unsafe_allow_html=True)

    # ── Resources ──────────────────────────────────────────────
    with tab_res:
        resources = get_resources(proj_id)
        if resources:
            for r in resources:
                icon = "🔗" if r["res_type"] == "link" else "📝"
                st.markdown(f"""
                <div class='cs-card' style='padding:12px;'>
                    <div style='font-size:12px;color:#9CA3AF;margin-bottom:4px;'>{icon} {r['res_type'].upper()} — {r['poster_name']} — {str(r['created_at'])[:10]}</div>
                    <div style='font-size:13px;color:#111827;'>{r['content']}</div>
                </div>""", unsafe_allow_html=True)
        else:
            empty_state("No resources yet", "Share notes and links with your team.")

        section_divider("Share a Resource")
        with st.form("res_form", clear_on_submit=True):
            res_type = st.selectbox("Type", ["note","link"])
            res_cont = st.text_area("Content", placeholder="Paste a link or write a note...", height=80)
            if st.form_submit_button("Share", use_container_width=True):
                if res_cont.strip():
                    add_resource(proj_id, u["id"], res_cont.strip(), res_type)
                    st.success("Resource shared!"); st.rerun()

    # ── Invite ─────────────────────────────────────────────────
    with tab_invite:
        if proj["creator_id"] != u["id"]:
            st.info("Only the project creator can invite members.")
            return

        section_divider("Manual Selection")
        all_users = db_fetchall("""
            SELECT id,username,skills,bio,avatar_color,trust_score
            FROM users WHERE id!=? AND is_active=1
            ORDER BY trust_score DESC
        """, (u["id"],))
        for fu in all_users:
            is_member = is_project_member(proj_id, fu["id"])
            ini = "".join(w[0].upper() for w in fu["username"].split()[:2])
            av  = fu.get("avatar_color","#2563EB")
            st.markdown(f"""
            <div class='cs-card' style='padding:12px;display:flex;align-items:center;gap:12px;'>
                <div style='width:38px;height:38px;border-radius:50%;background:{av};
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:13px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                <div style='flex:1;'>
                    <div style='font-weight:700;color:#111827;font-size:13px;'>{fu['username']}</div>
                    <div style='font-size:11px;color:#6B7280;'>{fu.get('skills','')}</div>
                </div>
            </div>""", unsafe_allow_html=True)
            if is_member:
                st.markdown("<span class='cs-badge badge-green'>Already a member</span>", unsafe_allow_html=True)
            else:
                if st.button("Invite to Project", key=f"inv_{proj_id}_{fu['id']}"):
                    ok, msg = send_project_invite(proj_id, u["id"], fu["id"])
                    if ok:
                        add_notification(fu["id"], "Project Invitation",
                                         f"{u['username']} invited you to join '{proj['title']}'.")
                    st.success(msg) if ok else st.warning(msg)

        section_divider("AI Recommendations")
        req_skills = proj.get("skills_required","")
        rec_users  = recommend_users_for_collaboration(u["id"], req_skills, proj.get("description",""), top_n=5)
        if not rec_users:
            st.markdown("<div style='color:#9CA3AF;font-size:12px;'>No recommendations available.</div>", unsafe_allow_html=True)
        for ru, score in rec_users:
            pct = int(min(score, 100))
            ini = "".join(w[0].upper() for w in ru["username"].split()[:2])
            av  = ru.get("avatar_color","#2563EB")
            is_member = is_project_member(proj_id, ru["id"])
            st.markdown(f"""
            <div class='cs-card' style='padding:12px;display:flex;align-items:center;gap:12px;'>
                <div style='width:38px;height:38px;border-radius:50%;background:{av};
                    display:inline-flex;align-items:center;justify-content:center;
                    font-size:13px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                <div style='flex:1;'>
                    <div style='font-weight:700;color:#111827;font-size:13px;'>{ru['username']}</div>
                    <div style='font-size:11px;color:#6B7280;'>{ru.get('skills','')}</div>
                </div>
                <div style='font-size:18px;font-weight:800;color:#16A34A;'>{pct}%</div>
            </div>""", unsafe_allow_html=True)
            if not is_member:
                if st.button(f"Invite {ru['username']}", key=f"ai_inv_{proj_id}_{ru['id']}"):
                    ok, msg = send_project_invite(proj_id, u["id"], ru["id"])
                    if ok:
                        add_notification(ru["id"], "Project Invitation",
                                         f"{u['username']} invited you to '{proj['title']}'.")
                    st.success(msg) if ok else st.warning(msg)


# ═══════════════════════════════════════════════════════════════
#  ROUTER
# ═══════════════════════════════════════════════════════════════
PAGES = {
    "landing":             page_landing,
    "login":               page_login,
    "register":            page_register,
    "dashboard":           page_dashboard,
    "browse_tasks":        page_browse_tasks,
    "post_task":           page_post_task,
    "profile":             page_profile,
    "ai_match":            page_ai_match,
    "community":           page_community,
    "notifications":       page_notifications,
    "chat":                page_chat,
    "network":             page_network,
    "projects":            page_projects,
    "project_workspace":   page_project_workspace,
    "book_session":        page_book_session,
    "my_sessions":         page_my_sessions,
    "admin_dashboard":     page_admin_dashboard,
    "admin_users":         page_admin_users,
    "admin_tasks":         page_admin_tasks,
}

PAGES.get(st.session_state.page, page_landing)()
