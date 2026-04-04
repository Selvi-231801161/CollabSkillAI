# app.py  —  CollabSkill AI  |  Professional Production Build
import streamlit as st
import pandas as pd
from database import init_db, db_fetchone, db_fetchall, db_execute
from auth import (register_user, login_user, get_user,
                  update_profile, update_trust_score, get_top_users)
from tasks_db import (
    create_task, get_all_open_tasks, get_my_tasks, get_all_tasks_admin,
    update_task_status, delete_task, apply_to_task,
    get_my_applications, get_feedback_for_user,
    submit_feedback, add_notification, get_notifications,
    get_unread_count, mark_all_read,
    CATEGORIES, KNOWLEDGE_TOPICS,
    TYPE_TASK, TYPE_KNOWLEDGE,
    SKILL_CATEGORIES, SKILLS_BY_CATEGORY,
)

init_db()

st.set_page_config(
    page_title  = "CollabSkill AI",
    page_icon   = "C",
    layout      = "wide",
    initial_sidebar_state = "collapsed",
)

# ── Session defaults ──────────────────────────────────────────
for k, v in {
    "page":       "landing",
    "user":       None,
    "history":    [],
    "ai_matches": [],
    "ai_done":    False,
    "mode":       "work",
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
#  CSS
# ═══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Reset & Base ── */
header, #MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 0 !important; }
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #050816 !important;
    color: #e2e8f0;
}
.stApp { background-color: #050816; }

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
    font-size: 14px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #22d3ee !important;
    box-shadow: 0 0 0 3px rgba(34,211,238,.08) !important;
}
input::placeholder { color: #334155 !important; }

/* ── Select ── */
.stSelectbox > div > div {
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e293b !important;
    border-radius: 8px !important;
}

/* ── Labels ── */
label, .stTextInput label, .stTextArea label,
.stSelectbox label, .stSlider label, .stCheckbox label {
    color: #64748b !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: .06em !important;
    text-transform: uppercase !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #22d3ee, #7c3aed) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: .01em !important;
    transition: opacity .2s, transform .1s !important;
}
.stButton > button:hover { opacity: .88 !important; transform: translateY(-1px) !important; }
.stButton > button:active { transform: translateY(0) !important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    padding: 18px !important;
}
[data-testid="metric-container"] label {
    color: #475569 !important;
    font-size: 11px !important;
    text-transform: uppercase !important;
    letter-spacing: .08em !important;
}
[data-testid="stMetricValue"] {
    color: #22d3ee !important;
    font-size: 26px !important;
    font-weight: 800 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}
.streamlit-expanderContent {
    background: #070d1f !important;
    border: 1px solid #1e293b !important;
    border-top: none !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #070d1f !important;
    border-right: 1px solid #1e293b !important;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid #1e293b !important;
    gap: 0 !important;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #475569 !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 20px !important;
}
.stTabs [aria-selected="true"] {
    color: #22d3ee !important;
    border-bottom-color: #22d3ee !important;
}

/* ── Checkbox ── */
.stCheckbox > label > div { border-color: #334155 !important; }

/* ── Divider ── */
hr { border-color: #1e293b !important; margin: 16px 0 !important; }

/* ═══════════════════════════════
   CUSTOM COMPONENTS
   ═══════════════════════════════ */

/* Card */
.cs-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
    transition: border-color .2s;
}
.cs-card:hover { border-color: #334155; }

/* Badge */
.cs-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
    margin: 2px 3px 2px 0;
}
.badge-green  { background: rgba(34,197,94,.1);  color: #4ade80; border: 1px solid rgba(34,197,94,.2); }
.badge-amber  { background: rgba(245,158,11,.1); color: #fbbf24; border: 1px solid rgba(245,158,11,.2); }
.badge-red    { background: rgba(239,68,68,.1);  color: #f87171; border: 1px solid rgba(239,68,68,.2); }
.badge-cyan   { background: rgba(34,211,238,.1); color: #22d3ee; border: 1px solid rgba(34,211,238,.2); }
.badge-violet { background: rgba(124,58,237,.1); color: #a78bfa; border: 1px solid rgba(124,58,237,.2); }
.badge-slate  { background: #1e293b;             color: #64748b; border: 1px solid #334155; }
.badge-teal   { background: rgba(20,184,166,.1); color: #2dd4bf; border: 1px solid rgba(20,184,166,.2); }

/* Page heading */
.page-title {
    font-size: 24px;
    font-weight: 800;
    color: #f1f5f9;
    letter-spacing: -.02em;
    margin-bottom: 4px;
}
.page-sub {
    color: #475569;
    font-size: 14px;
    margin-bottom: 24px;
}

/* Trust bar */
.trust-bar-bg   { background: #1e293b; border-radius: 3px; height: 4px; margin-top: 6px; }
.trust-bar-fill { height: 4px; border-radius: 3px; background: linear-gradient(90deg, #22d3ee, #7c3aed); }

/* Admin banner */
.admin-only-banner {
    background: rgba(239,68,68,.07);
    border: 1px solid rgba(239,68,68,.2);
    border-radius: 8px;
    padding: 10px 16px;
    color: #f87171;
    font-size: 13px;
    margin-bottom: 16px;
}

/* Mode badge — small inline pill */
.mode-pill-work {
    display: inline-flex; align-items: center;
    background: rgba(34,211,238,.07);
    border: 1px solid rgba(34,211,238,.15);
    border-radius: 6px; padding: 4px 14px;
    color: #22d3ee; font-size: 12px; font-weight: 700;
    letter-spacing: .04em; margin-bottom: 16px;
}
.mode-pill-learn {
    display: inline-flex; align-items: center;
    background: rgba(20,184,166,.07);
    border: 1px solid rgba(20,184,166,.15);
    border-radius: 6px; padding: 4px 14px;
    color: #2dd4bf; font-size: 12px; font-weight: 700;
    letter-spacing: .04em; margin-bottom: 16px;
}

/* ═══════════════════════════════
   LANDING PAGE SPECIFIC
   ═══════════════════════════════ */

.hero-wrap { text-align: center; padding: 72px 0 40px; }
.hero-eyebrow {
    display: inline-block;
    font-size: 11px; font-weight: 700; letter-spacing: .14em;
    text-transform: uppercase; color: #22d3ee;
    background: rgba(34,211,238,.07);
    border: 1px solid rgba(34,211,238,.15);
    border-radius: 4px; padding: 5px 16px; margin-bottom: 28px;
}
.hero-h1 {
    font-size: clamp(40px, 6vw, 68px);
    font-weight: 900; line-height: 1.06;
    letter-spacing: -.04em; color: #f1f5f9;
    margin-bottom: 0;
}
.hero-gradient {
    font-size: clamp(40px, 6vw, 68px);
    font-weight: 900; line-height: 1.06;
    letter-spacing: -.04em;
    background: linear-gradient(135deg, #22d3ee 0%, #818cf8 50%, #a855f7 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub {
    font-size: 16px; color: #475569; line-height: 1.7;
    max-width: 520px; margin: 18px auto 0;
}

/* Mode choice cards on landing */
.mode-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 36px 28px;
    cursor: pointer;
    transition: border-color .25s, transform .2s, box-shadow .25s;
    text-align: center;
}
.mode-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 40px rgba(0,0,0,.4);
}
.mode-card-work:hover  { border-color: #22d3ee; }
.mode-card-learn:hover { border-color: #14b8a6; }
.mode-card-icon {
    width: 56px; height: 56px; border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    font-size: 22px; margin: 0 auto 18px;
}
.mode-card-title {
    font-size: 20px; font-weight: 800; letter-spacing: -.02em;
    color: #f1f5f9; margin-bottom: 8px;
}
.mode-card-desc {
    font-size: 13px; color: #475569; line-height: 1.6;
}
.mode-card-cta {
    display: inline-block; margin-top: 20px;
    font-size: 12px; font-weight: 700;
    letter-spacing: .04em; text-transform: uppercase;
}
.cta-work  { color: #22d3ee; }
.cta-learn { color: #2dd4bf; }

/* Stat strip */
.stat-strip {
    display: grid; grid-template-columns: repeat(4, 1fr);
    border-top: 1px solid #1e293b; border-bottom: 1px solid #1e293b;
    background: #0a0f1e; margin: 40px 0;
}
.stat-item { padding: 24px 0; text-align: center; border-right: 1px solid #1e293b; }
.stat-item:last-child { border-right: none; }
.stat-num  { font-size: 28px; font-weight: 900; color: #f1f5f9; line-height: 1; }
.stat-lbl  { font-size: 11px; color: #475569; margin-top: 5px; letter-spacing: .06em; text-transform: uppercase; }

/* Navbar */
.navbar-logo {
    font-size: 17px; font-weight: 800; color: #f1f5f9;
    letter-spacing: -.01em;
}
.navbar-logo span { color: #22d3ee; }
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
    return f"<span class='cs-badge {c}'>{s.replace('_', ' ').title()}</span>"

def priority_badge(p):
    c = {"Urgent": "badge-red", "Normal": "badge-cyan", "Low": "badge-slate"}.get(p, "badge-slate")
    return f"<span class='cs-badge {c}'>{p}</span>"

def type_badge(t):
    if t == TYPE_KNOWLEDGE:
        return "<span class='cs-badge badge-teal'>Knowledge</span>"
    return "<span class='cs-badge badge-cyan'>Task</span>"

def mode_pill():
    if is_learn_mode():
        st.markdown("<div class='mode-pill-learn'>Knowledge Exchange Mode</div>",
                    unsafe_allow_html=True)
    else:
        st.markdown("<div class='mode-pill-work'>Task Collaboration Mode</div>",
                    unsafe_allow_html=True)

def mk_avatar(name, size=40):
    ini = "".join(w[0].upper() for w in (name or "U").split()[:2])
    return (f"<div style='width:{size}px;height:{size}px;border-radius:50%;"
            f"background:linear-gradient(135deg,#22d3ee,#7c3aed);"
            f"display:inline-flex;align-items:center;justify-content:center;"
            f"font-size:{size//3}px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>")

def empty_state(title, desc="", action_label=None, action_key=None, action_fn=None):
    st.markdown(f"""
    <div class='cs-card' style='text-align:center;padding:56px 32px;'>
        <div style='width:48px;height:48px;border-radius:12px;background:#1e293b;
            display:flex;align-items:center;justify-content:center;margin:0 auto 16px;'>
            <svg width="20" height="20" fill="none" stroke="#475569" stroke-width="2"
                viewBox="0 0 24 24"><path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0
                002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2
                2 0 012 2"/></svg>
        </div>
        <div style='font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:6px;'>{title}</div>
        <div style='font-size:13px;color:#475569;'>{desc}</div>
    </div>""", unsafe_allow_html=True)
    if action_label and action_key:
        _, c, _ = st.columns([2, 1, 2])
        with c:
            if st.button(action_label, key=action_key, use_container_width=True):
                if action_fn:
                    action_fn()

def back_btn(label="Back"):
    if st.button(label, key=f"back__{st.session_state.page}"):
        go_back()

def breadcrumb(*parts):
    html = " / ".join(
        f"<a href='#' style='color:#334155;text-decoration:none;'>{p}</a>"
        if i < len(parts) - 1
        else f"<span style='color:#64748b;'>{p}</span>"
        for i, p in enumerate(parts)
    )
    st.markdown(
        f"<div style='font-size:12px;color:#334155;margin-bottom:12px;'>{html}</div>",
        unsafe_allow_html=True)

def section_header(title, subtitle=""):
    st.markdown(f"""
    <div style='margin-bottom:20px;'>
        <div class='page-title'>{title}</div>
        {f"<div class='page-sub'>{subtitle}</div>" if subtitle else ""}
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  SKILL DROPDOWN HELPER
#  Returns (category, skill) selected by user
# ═══════════════════════════════════════════════════════════════
def skill_dropdown_widget(cat_key="skill_cat", skill_key="skill_val",
                          default_cat=None, default_skill=None):
    """
    Renders two chained selectboxes: Category -> Skill.
    Returns (selected_category, selected_skill_string).
    """
    cat_options = ["Select a category"] + SKILL_CATEGORIES
    default_cat_idx = 0
    if default_cat and default_cat in SKILL_CATEGORIES:
        default_cat_idx = SKILL_CATEGORIES.index(default_cat) + 1

    selected_cat = st.selectbox(
        "Skill Category",
        cat_options,
        index=default_cat_idx,
        key=cat_key,
    )

    if selected_cat == "Select a category":
        st.selectbox("Skill", ["Select a category first"], key=skill_key, disabled=True)
        return None, None

    skill_options = SKILLS_BY_CATEGORY.get(selected_cat, []) + ["Other"]
    default_skill_idx = 0
    if default_skill and default_skill in skill_options:
        default_skill_idx = skill_options.index(default_skill)

    selected_skill = st.selectbox(
        "Skill",
        skill_options,
        index=default_skill_idx,
        key=skill_key,
    )
    return selected_cat, selected_skill


# ═══════════════════════════════════════════════════════════════
#  NAVBAR
# ═══════════════════════════════════════════════════════════════
def render_navbar():
    u      = st.session_state.user
    unread = get_unread_count(u["id"]) if u else 0
    notif_lbl = f"Notifications ({unread})" if unread else "Notifications"

    if is_admin():
        cols   = st.columns([3, 1, 1, 1, 1, 1, 1])
        labels = ["Dashboard", "Users", "Tasks", "Browse", notif_lbl, "Profile", "Sign Out"]
        pages  = ["admin_dashboard", "admin_users", "admin_tasks", "browse_tasks",
                  "notifications", "profile", "__logout__"]
    elif logged_in():
        cols   = st.columns([3, 1, 1, 1, 1, 1, 1])
        labels = ["Home", "Dashboard", "Browse", "Post", notif_lbl, "Profile", "Sign Out"]
        pages  = ["landing", "dashboard", "browse_tasks", "post_task",
                  "notifications", "profile", "__logout__"]
    else:
        cols = st.columns([5, 1, 1])
        with cols[0]:
            st.markdown(
                "<div class='navbar-logo' style='padding-top:10px;'>"
                "Collab<span>Skill</span> AI</div>",
                unsafe_allow_html=True)
        with cols[1]:
            if st.button("Sign In", key="nav_login_guest"):  go("login")
        with cols[2]:
            if st.button("Sign Up", key="nav_signup_guest"): go("register")
        st.markdown("<hr/>", unsafe_allow_html=True)
        return

    admin_pill = (
        " <span style='font-size:10px;background:rgba(34,211,238,.1);"
        "color:#22d3ee;border:1px solid rgba(34,211,238,.15);"
        "border-radius:4px;padding:2px 8px;letter-spacing:.04em;'>ADMIN</span>"
        if is_admin() else ""
    )
    with cols[0]:
        st.markdown(
            f"<div class='navbar-logo' style='padding-top:10px;'>"
            f"Collab<span>Skill</span> AI{admin_pill}</div>",
            unsafe_allow_html=True)

    for col, lbl, pg in zip(cols[1:], labels, pages):
        with col:
            if st.button(lbl, key=f"nav__{pg}", use_container_width=True):
                if pg == "__logout__":
                    st.session_state.user    = None
                    st.session_state.history = []
                    go("landing")
                else:
                    go(pg)

    st.markdown("<hr/>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  LANDING PAGE
#  Two prominent cards: LEARN and WORK
#  Both lead to login / register
# ═══════════════════════════════════════════════════════════════
def page_landing():
    render_navbar()

    # ── Hero ─────────────────────────────────────────────────
    st.markdown("""
    <div class='hero-wrap'>
        <div class='hero-eyebrow'>AI-Powered Skill Exchange Platform</div>
        <div class='hero-h1'>Connect. Collaborate.</div>
        <div class='hero-gradient'>Exchange Skills Smarter.</div>
        <div class='hero-sub'>
            An intelligent platform that matches you with the right people —
            connecting skill providers with those who need them, instantly.
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Mode Selection Cards ──────────────────────────────────
    st.markdown(
        "<div style='text-align:center;font-size:11px;font-weight:700;"
        "letter-spacing:.12em;text-transform:uppercase;color:#475569;"
        "margin-bottom:20px;'>Choose how you want to get started</div>",
        unsafe_allow_html=True)

    lc, rc = st.columns([1, 1], gap="large")

    with lc:
        st.markdown("""
        <div class='mode-card mode-card-work'>
            <div class='mode-card-icon'
                style='background:rgba(34,211,238,.08);'>
                <svg width="24" height="24" fill="none" stroke="#22d3ee" stroke-width="2"
                    viewBox="0 0 24 24"><rect x="2" y="7" width="20" height="14" rx="2"/><path
                    d="M16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2"/><line x1="12" y1="12"
                    x2="12" y2="16"/><line x1="10" y1="14" x2="14" y2="14"/></svg>
            </div>
            <div class='mode-card-title'>Work</div>
            <div class='mode-card-desc'>
                Post tasks, find collaborators, and get things done.
                Connect with skilled professionals ready to help with real projects.
            </div>
            <div class='mode-card-cta cta-work'>Task Collaboration &rarr;</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Get Started with Work", key="land_work", use_container_width=True):
            st.session_state.mode = "work"
            if logged_in():
                go("admin_dashboard" if is_admin() else "dashboard")
            else:
                go("register")

    with rc:
        st.markdown("""
        <div class='mode-card mode-card-learn'>
            <div class='mode-card-icon'
                style='background:rgba(20,184,166,.08);'>
                <svg width="24" height="24" fill="none" stroke="#2dd4bf" stroke-width="2"
                    viewBox="0 0 24 24"><path d="M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2z"/>
                    <path d="M22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z"/></svg>
            </div>
            <div class='mode-card-title'>Learn</div>
            <div class='mode-card-desc'>
                Request tutoring, share knowledge, and grow your skills.
                Connect with experts who can guide your learning journey.
            </div>
            <div class='mode-card-cta cta-learn'>Knowledge Exchange &rarr;</div>
        </div>""", unsafe_allow_html=True)
        st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)
        if st.button("Get Started with Learn", key="land_learn", use_container_width=True):
            st.session_state.mode = "learn"
            if logged_in():
                go("admin_dashboard" if is_admin() else "dashboard")
            else:
                go("register")

    # ── Stats strip ───────────────────────────────────────────
    total_users = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    total_tasks = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE type='task'")["c"]
    open_tasks  = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open' AND type='task'")["c"]
    total_know  = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE type='knowledge'")["c"]

    st.markdown(f"""
    <div class='stat-strip'>
        <div class='stat-item'>
            <div class='stat-num'>{total_users}</div>
            <div class='stat-lbl'>Members</div>
        </div>
        <div class='stat-item'>
            <div class='stat-num'>{total_tasks}</div>
            <div class='stat-lbl'>Tasks Posted</div>
        </div>
        <div class='stat-item'>
            <div class='stat-num'>{open_tasks}</div>
            <div class='stat-lbl'>Open Tasks</div>
        </div>
        <div class='stat-item'>
            <div class='stat-num'>{total_know}</div>
            <div class='stat-lbl'>Knowledge Posts</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Feature grid ─────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;font-size:11px;font-weight:700;"
        "letter-spacing:.12em;text-transform:uppercase;color:#475569;"
        "margin-bottom:20px;'>Platform Features</div>",
        unsafe_allow_html=True)

    cols = st.columns(3)
    features = [
        ("AI Matching",
         "Our AI engine reads task requirements and user profiles to surface the best matches automatically.",
         "rgba(34,211,238,.08)", "#22d3ee"),
        ("Trust Score System",
         "Every collaboration builds your reputation. Peer-reviewed ratings form a verified trust score.",
         "rgba(124,58,237,.08)", "#a78bfa"),
        ("Dual Mode Platform",
         "Switch between Task Collaboration and Knowledge Exchange to find exactly what you need.",
         "rgba(20,184,166,.08)", "#2dd4bf"),
    ]
    for col, (title, desc, bg, accent) in zip(cols, features):
        col.markdown(f"""
        <div class='cs-card' style='min-height:180px;'>
            <div style='width:38px;height:38px;border-radius:9px;background:{bg};
                display:flex;align-items:center;justify-content:center;margin-bottom:14px;'>
                <div style='width:16px;height:16px;border-radius:50%;background:{accent};'></div>
            </div>
            <div style='font-weight:700;font-size:14px;color:#f1f5f9;margin-bottom:7px;'>{title}</div>
            <div style='font-size:13px;color:#475569;line-height:1.65;'>{desc}</div>
        </div>""", unsafe_allow_html=True)

    # ── How it works ──────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        "<div style='text-align:center;font-size:11px;font-weight:700;"
        "letter-spacing:.12em;text-transform:uppercase;color:#475569;"
        "margin-bottom:24px;'>How It Works</div>",
        unsafe_allow_html=True)

    s1, s2, s3, s4 = st.columns(4)
    steps = [
        ("01", "Create your account", "Register and build your profile with your skills and experience level."),
        ("02", "Choose your mode",    "Select Work for task collaboration or Learn for knowledge exchange."),
        ("03", "Post or browse",      "Post what you need or discover opportunities that match your skills."),
        ("04", "Collaborate",         "Connect, complete tasks or sessions, rate each other, and grow."),
    ]
    for col, (num, title, desc) in zip([s1, s2, s3, s4], steps):
        col.markdown(f"""
        <div class='cs-card'>
            <div style='font-size:32px;font-weight:900;color:#1e293b;line-height:1;margin-bottom:10px;'>{num}</div>
            <div style='font-size:13px;font-weight:700;color:#f1f5f9;margin-bottom:6px;'>{title}</div>
            <div style='font-size:12px;color:#475569;line-height:1.6;'>{desc}</div>
        </div>""", unsafe_allow_html=True)

    # Footer
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;padding:20px 0;border-top:1px solid #1e293b;'>
        <div style='font-size:13px;font-weight:700;color:#f1f5f9;margin-bottom:4px;'>
            CollabSkill AI
        </div>
        <div style='font-size:12px;color:#334155;'>
            Connecting skilled people with those who need them.
        </div>
    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════════
def page_login():
    render_navbar()
    back_btn("Back to Home")

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style='background:#0f172a;border:1px solid #1e293b;border-radius:16px;padding:40px 36px;'>
        """, unsafe_allow_html=True)

        mode_label = "Knowledge Exchange" if is_learn_mode() else "Task Collaboration"
        st.markdown(
            f"<div style='text-align:center;margin-bottom:28px;'>"
            f"<div style='font-size:22px;font-weight:800;color:#f1f5f9;margin-bottom:6px;'>Sign in</div>"
            f"<div style='font-size:13px;color:#475569;'>{mode_label} Mode</div>"
            f"</div>",
            unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username", key="lp_username")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="lp_password")
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)

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
        <div style='text-align:center;margin-top:20px;padding-top:20px;
            border-top:1px solid #1e293b;font-size:13px;color:#475569;'>
            Do not have an account?
        </div>""", unsafe_allow_html=True)

        if st.button("Create an Account", key="lp_to_register", use_container_width=True):
            go("register")

        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  REGISTER  — with cascading skill dropdowns
# ═══════════════════════════════════════════════════════════════
def page_register():
    render_navbar()
    back_btn("Back to Home")

    st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
    section_header("Create Your Account",
                   "Join the CollabSkill AI community and start collaborating.")

    with st.form("register_form", clear_on_submit=False):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Account Details**")
            username   = st.text_input("Username",          placeholder="Choose a unique username",  key="rp_user")
            email      = st.text_input("Email Address",     placeholder="your@email.com",            key="rp_email")
            password   = st.text_input("Password",          type="password",
                                       placeholder="Minimum 6 characters",                           key="rp_pass")
            confirm    = st.text_input("Confirm Password",  type="password",
                                       placeholder="Repeat your password",                           key="rp_confirm")

        with col2:
            st.markdown("**Profile Details**")
            experience = st.selectbox("Experience Level",
                                      ["Beginner", "Intermediate", "Advanced", "Expert"],
                                      key="rp_exp")
            portfolio  = st.text_input("Portfolio / GitHub URL (optional)",
                                       placeholder="https://github.com/yourname",                   key="rp_port")
            bio        = st.text_area("Short Bio",
                                      placeholder="Tell others about yourself and your goals...",
                                      height=90,                                                     key="rp_bio")

        # ── Skill selection ───────────────────────────────────
        st.markdown("<div style='margin-top:4px;'></div>", unsafe_allow_html=True)
        st.markdown("**Primary Skill**")
        sc1, sc2 = st.columns(2)
        with sc1:
            cat_opts = ["Select a category"] + SKILL_CATEGORIES
            sel_cat  = st.selectbox("Skill Category", cat_opts, key="rp_skill_cat")
        with sc2:
            if sel_cat == "Select a category":
                st.selectbox("Skill", ["Select a category first"], key="rp_skill_val", disabled=True)
                sel_skill = None
            else:
                skill_opts = SKILLS_BY_CATEGORY.get(sel_cat, []) + ["Other"]
                sel_skill  = st.selectbox("Skill", skill_opts, key="rp_skill_val")

        agree = st.checkbox("I agree to the Terms & Conditions", key="rp_agree")
        st.markdown("<div style='height:4px;'></div>", unsafe_allow_html=True)
        submitted = st.form_submit_button("Create Account", use_container_width=True)

    if submitted:
        skill_str = f"{sel_cat} - {sel_skill}" if sel_cat and sel_cat != "Select a category" and sel_skill else ""
        if not agree:
            st.warning("Please accept the Terms & Conditions to continue.")
        elif not all([username, email, password, skill_str]):
            st.warning("Please complete all required fields including your skill selection.")
        elif len(password) < 6:
            st.warning("Password must be at least 6 characters.")
        elif password != confirm:
            st.error("Passwords do not match.")
        else:
            success, result = register_user(
                username, email, password, skill_str, bio, portfolio, experience)
            if success:
                st.session_state.user    = result
                st.session_state.history = []
                st.success("Account created successfully. Welcome to CollabSkill AI.")
                go("admin_dashboard" if result["role"] == "admin" else "dashboard")
            else:
                st.error(result)

    st.markdown("<div style='font-size:13px;color:#475569;margin-top:12px;'>Already have an account?</div>",
                unsafe_allow_html=True)
    if st.button("Sign In Instead", key="rp_to_login"):
        go("login")


# ═══════════════════════════════════════════════════════════════
#  USER DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_dashboard():
    require_login()
    if is_admin(): go("admin_dashboard"); return

    render_navbar()
    u = get_user(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = u

    breadcrumb("Home", "Dashboard")

    # Greeting + mode context
    mode_label = "Knowledge Exchange" if is_learn_mode() else "Task Collaboration"
    st.markdown(
        f"<div class='page-title'>Welcome, {u['username']}</div>"
        f"<div class='page-sub'>{mode_label} — your personal workspace</div>",
        unsafe_allow_html=True)
    mode_pill()

    # Stats
    mode_type    = TYPE_KNOWLEDGE if is_learn_mode() else TYPE_TASK
    my_entries   = get_my_tasks(u["id"], entry_type=mode_type)
    my_apps      = get_my_applications(u["id"])
    open_cnt     = sum(1 for t in my_entries if t["status"] == "open")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("My Posts",         len(my_entries))
    m2.metric("Active",           open_cnt)
    m3.metric("Applications",     len(my_apps))
    m4.metric("Trust Score",      f"{u['trust_score']}/10")
    m5.metric("Ratings",          u["total_ratings"])

    st.markdown("<br>", unsafe_allow_html=True)

    # Profile banner
    pc1, pc2 = st.columns([5, 1])
    with pc1:
        st.markdown(f"""
        <div class='cs-card' style='display:flex;align-items:center;gap:18px;'>
            {mk_avatar(u['username'], 52)}
            <div>
                <div style='font-size:15px;font-weight:800;color:#f1f5f9;'>{u['username']}</div>
                <div style='font-size:12px;color:#475569;margin-top:3px;'>{u['skills'] or 'No skills added'}</div>
                <div style='font-size:11px;color:#334155;margin-top:2px;'>{u['experience']}</div>
            </div>
        </div>""", unsafe_allow_html=True)
    with pc2:
        if st.button("Edit Profile", key="dash_edit", use_container_width=True):
            go("profile")

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs
    if is_learn_mode():
        t1_label = "My Knowledge Posts"
    else:
        t1_label = "My Tasks"

    tab1, tab2, tab3 = st.tabs([t1_label, "My Applications", "Quick Actions"])

    with tab1:
        if not my_entries:
            desc = "Share what you know or post a learning request." if is_learn_mode() \
                   else "Post your first task to start finding collaborators."
            empty_state(
                "No posts yet", desc,
                action_label="Post Now",
                action_key="dash_post_empty",
                action_fn=lambda: go("post_task"))
        else:
            for t in my_entries:
                _render_entry_card(t, owner=True)

    with tab2:
        if not my_apps:
            empty_state(
                "No applications yet",
                "Browse and apply to help others.",
                action_label="Browse Now",
                action_key="dash_browse_empty",
                action_fn=lambda: go("browse_tasks"))
        else:
            for a in my_apps:
                tp = type_badge(a.get("task_type", TYPE_TASK))
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='font-weight:600;color:#f1f5f9;margin-bottom:6px;'>{a['task_title']}</div>
                    <div>{status_badge(a['status'])} {tp}
                        <span class='cs-badge badge-violet'>{a['category']}</span>
                        <span class='cs-badge badge-slate'>{a['owner_name']}</span>
                    </div>
                    <div style='color:#334155;font-size:11px;margin-top:6px;'>{a['created_at']}</div>
                </div>""", unsafe_allow_html=True)

    with tab3:
        q1, q2, q3, q4 = st.columns(4)
        with q1:
            lbl = "Post Knowledge" if is_learn_mode() else "Post a Task"
            if st.button(lbl, key="qa_post", use_container_width=True): go("post_task")
        with q2:
            lbl2 = "Browse Knowledge" if is_learn_mode() else "Browse Tasks"
            if st.button(lbl2, key="qa_browse", use_container_width=True): go("browse_tasks")
        with q3:
            if st.button("AI Matching", key="qa_ai", use_container_width=True): go("ai_match")
        with q4:
            if st.button("Community", key="qa_community", use_container_width=True): go("community")


# ═══════════════════════════════════════════════════════════════
#  SHARED ENTRY CARD RENDERER
# ═══════════════════════════════════════════════════════════════
def _render_entry_card(t, owner=False):
    is_know = t.get("type") == TYPE_KNOWLEDGE
    header  = f"{t['title']}  —  {t['status'].upper()}"

    with st.expander(header):
        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"""
            <div style='color:#94a3b8;font-size:13px;margin-bottom:10px;line-height:1.7;'>
                {t['description']}</div>
            {type_badge(t.get('type', TYPE_TASK))}
            {status_badge(t['status'])}
            {priority_badge(t.get('priority', 'Normal'))}
            <span class='cs-badge badge-violet'>{t.get('category','')}</span>
            <span class='cs-badge badge-slate'>{t['skills']}</span>
            <span class='cs-badge badge-slate'>{t.get('applicant_count', 0)} {'interested' if is_know else 'applicants'}</span>
            """, unsafe_allow_html=True)
        with c2:
            if owner:
                if t["status"] == "open":
                    if st.button("Close", key=f"tc_{t['id']}"):
                        update_task_status(t["id"], "closed"); st.rerun()
                else:
                    if st.button("Reopen", key=f"to_{t['id']}"):
                        update_task_status(t["id"], "open"); st.rerun()
                if st.button("Delete", key=f"td_{t['id']}"):
                    delete_task(t["id"]); st.success("Deleted."); st.rerun()


# ═══════════════════════════════════════════════════════════════
#  BROWSE
# ═══════════════════════════════════════════════════════════════
def page_browse_tasks():
    render_navbar()
    back_btn()

    entry_type = TYPE_KNOWLEDGE if is_learn_mode() else TYPE_TASK
    is_know    = is_learn_mode()

    if is_know:
        breadcrumb("Home", "Browse Knowledge")
        section_header("Browse Knowledge Exchange",
                       "Discover learning opportunities and knowledge experts.")
    else:
        breadcrumb("Home", "Browse Tasks")
        section_header("Browse Tasks",
                       "Find tasks that match your skills and start collaborating.")

    mode_pill()

    # Filters
    fc1, fc2, fc3 = st.columns([3, 1.5, 1.5])
    with fc1:
        search = st.text_input(
            "", placeholder="Search by title, skill or keyword...",
            key=f"br_search_{entry_type}", label_visibility="collapsed")
    with fc2:
        topic_list = KNOWLEDGE_TOPICS if is_know else CATEGORIES
        category   = st.selectbox("", ["All"] + topic_list,
                                  key=f"br_cat_{entry_type}", label_visibility="collapsed")
    with fc3:
        sort_by = st.selectbox("", ["Newest First", "Oldest First", "Priority"],
                               key=f"br_sort_{entry_type}", label_visibility="collapsed")

    sort_map = {"Newest First": "newest", "Oldest First": "oldest", "Priority": "priority"}

    if logged_in():
        post_lbl = "Post Knowledge Request" if is_know else "Post a Task"
        if st.button(post_lbl, key=f"br_post_{entry_type}"):
            go("post_task")

    entries = get_all_open_tasks(
        search, category, sort_map.get(sort_by, "newest"), entry_type=entry_type)

    count_noun = "knowledge request(s)" if is_know else "task(s)"
    st.markdown(
        f"<div style='color:#475569;font-size:13px;margin-bottom:14px;'>"
        f"{len(entries)} {count_noun} found</div>",
        unsafe_allow_html=True)

    if not entries:
        msg = "No knowledge posts found." if is_know else "No tasks found."
        empty_state(msg, "Be the first to post one.",
                    action_label="Post Now",
                    action_key=f"br_empty_post_{entry_type}",
                    action_fn=lambda: go("post_task"))
        return

    for t in entries:
        creator = t.get("creator_name", "")
        header  = f"{t['title']}  —  {creator}"
        apply_lbl = "I Can Help Teach" if is_know else "I Can Help"

        with st.expander(header):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div style='color:#94a3b8;font-size:13px;line-height:1.7;margin-bottom:10px;'>
                    {t['description']}</div>
                {type_badge(t.get('type', TYPE_TASK))}
                {status_badge(t['status'])}
                {priority_badge(t.get('priority', 'Normal'))}
                <span class='cs-badge badge-violet'>{t['category']}</span>
                <span class='cs-badge badge-slate'>{t['skills']}</span>
                {'<span class="cs-badge badge-slate">Deadline: ' + t["deadline"] + '</span>' if t.get("deadline") else ''}
                <span class='cs-badge badge-slate'>Posted by {creator}</span>
                <span class='cs-badge badge-slate'>Trust {t.get('creator_trust', 0)}/10</span>
                <span class='cs-badge badge-slate'>{t.get('applicant_count', 0)} {'interested' if is_know else 'applied'}</span>
                <div style='color:#334155;font-size:11px;margin-top:8px;'>
                    Posted {str(t.get('created_at', ''))[:10]}</div>
                """, unsafe_allow_html=True)
            with c2:
                if logged_in() and st.session_state.user["id"] != t["created_by"]:
                    if st.button(apply_lbl, key=f"apply_{t['id']}"):
                        ok, msg = apply_to_task(t["id"], st.session_state.user["id"])
                        if ok:
                            ntitle = "New Interest in Your Post" if is_know else "New Application Received"
                            nmsg   = (f"{st.session_state.user['username']} is interested in: {t['title']}"
                                      if is_know else
                                      f"{st.session_state.user['username']} applied to: {t['title']}")
                            add_notification(t["created_by"], ntitle, nmsg)
                            st.success(msg)
                        else:
                            st.warning(msg)
                elif not logged_in():
                    if st.button("Sign In to Apply", key=f"la_{t['id']}"):
                        go("login")


# ═══════════════════════════════════════════════════════════════
#  POST
# ═══════════════════════════════════════════════════════════════
def page_post_task():
    require_login()
    render_navbar()
    back_btn()

    entry_type = TYPE_KNOWLEDGE if is_learn_mode() else TYPE_TASK
    is_know    = is_learn_mode()

    if is_know:
        breadcrumb("Home", "Dashboard", "Post Knowledge Request")
        section_header("Post a Knowledge Request",
                       "Share what you can teach, or request help learning a topic.")
    else:
        breadcrumb("Home", "Dashboard", "Post a Task")
        section_header("Post a Task",
                       "Describe what you need and find the right collaborator.")

    mode_pill()

    c_form, c_tip = st.columns([2, 1])

    with c_form:
        with st.form(f"post_form_{entry_type}"):
            title_ph = ("e.g., Teach me Python from scratch" if is_know
                        else "e.g., React developer needed for dashboard project")
            desc_ph  = ("Describe what you want to learn, your current level, and your goals..."
                        if is_know else
                        "Describe the task requirements, expected output, and tools needed...")
            skill_ph = ("e.g., Python, Data Science" if is_know else "e.g., React, Node.js, Figma")

            title       = st.text_input("Title" + (" *" if True else ""),
                                        placeholder=title_ph)
            description = st.text_area("Description *", placeholder=desc_ph, height=140)

            sk1, sk2 = st.columns(2)
            with sk1:
                skills   = st.text_input("Required Skills / Topic *", placeholder=skill_ph)
                deadline = st.text_input(
                    "Timeframe / Deadline", placeholder="e.g., Within 2 weeks")
            with sk2:
                cat_list = KNOWLEDGE_TOPICS if is_know else CATEGORIES
                cat_lbl  = "Topic Category" if is_know else "Category"
                category = st.selectbox(cat_lbl, cat_list)
                priority = st.selectbox("Priority", ["Normal", "Urgent", "Low"])

            submit_lbl = "Post Knowledge Request" if is_know else "Post Task"
            if st.form_submit_button(submit_lbl, use_container_width=True):
                if not all([title, description, skills]):
                    st.warning("Please fill in the title, description, and skills.")
                else:
                    create_task(title, description, skills, category,
                                deadline, priority,
                                st.session_state.user["id"],
                                entry_type=entry_type)
                    success_msg = ("Knowledge request posted successfully."
                                   if is_know else "Task posted successfully.")
                    st.success(success_msg)
                    go("dashboard")

    with c_tip:
        if is_know:
            st.markdown("""
            <div class='cs-card'>
                <div style='font-size:13px;font-weight:700;color:#2dd4bf;
                    margin-bottom:12px;letter-spacing:.02em;'>
                    Tips for a Good Knowledge Request
                </div>
                <div style='font-size:13px;color:#475569;line-height:2.1;'>
                    State your current knowledge level clearly<br>
                    Specify what outcome you expect<br>
                    Mention preferred learning format<br>
                    Set a realistic timeframe<br>
                    Be open about your availability
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class='cs-card'>
                <div style='font-size:13px;font-weight:700;color:#22d3ee;
                    margin-bottom:12px;letter-spacing:.02em;'>
                    Tips for a Good Task Post
                </div>
                <div style='font-size:13px;color:#475569;line-height:2.1;'>
                    Be specific about deliverables<br>
                    List the exact skills required<br>
                    Provide a clear deadline<br>
                    Describe the expected output<br>
                    Choose the correct category
                </div>
            </div>""", unsafe_allow_html=True)

        mode_type = TYPE_KNOWLEDGE if is_know else TYPE_TASK
        recent    = get_my_tasks(st.session_state.user["id"], entry_type=mode_type)[:5]
        if recent:
            st.markdown(
                "<div style='font-size:12px;font-weight:700;color:#475569;"
                "text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>"
                "My Recent Posts</div>",
                unsafe_allow_html=True)
            for t in recent:
                dot = "open" if t["status"] == "open" else "closed"
                color = "#4ade80" if dot == "open" else "#475569"
                st.markdown(
                    f"<div style='font-size:12px;color:#64748b;padding:6px 0;"
                    f"border-bottom:1px solid #1e293b;display:flex;align-items:center;gap:8px;'>"
                    f"<span style='width:6px;height:6px;border-radius:50%;background:{color};"
                    f"flex-shrink:0;display:inline-block;'></span>{t['title']}</div>",
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PROFILE
# ═══════════════════════════════════════════════════════════════
def page_profile():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "Dashboard", "Profile")

    u = get_user(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = u

    section_header("My Profile", "Manage your account and view your activity.")

    sidebar, main = st.columns([1, 2])

    with sidebar:
        ini = "".join(w[0].upper() for w in (u["username"] or "U").split()[:2])

        st.markdown(f"""
        <div style='text-align:center;'>
            <div style='width:80px;height:80px;border-radius:50%;
                background:linear-gradient(135deg,#22d3ee,#7c3aed);
                display:inline-flex;align-items:center;justify-content:center;
                font-size:28px;font-weight:700;color:#fff;'>{ini}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='text-align:center;margin-top:12px;margin-bottom:4px;'>
            <div style='font-size:17px;font-weight:800;color:#f1f5f9;'>{u['username']}</div>
            <div style='font-size:12px;color:#475569;margin-top:4px;'>{u['email']}</div>
        </div>""", unsafe_allow_html=True)

        admin_badge = '<span class="cs-badge badge-cyan">Admin</span>' if u["role"] == "admin" else ""
        st.markdown(f"""
        <div style='text-align:center;margin:10px 0;'>
            <span class='cs-badge badge-violet'>{u['experience']}</span>{admin_badge}
        </div>""", unsafe_allow_html=True)

        if u.get("bio"):
            st.markdown(f"""
            <div style='font-size:13px;color:#64748b;line-height:1.65;
                text-align:center;margin-bottom:12px;'>{u['bio']}</div>""",
                unsafe_allow_html=True)

        if u.get("portfolio"):
            st.markdown(
                f"<div style='text-align:center;margin-bottom:12px;'>"
                f"<a href='{u['portfolio']}' target='_blank' "
                f"style='font-size:12px;color:#22d3ee;font-weight:600;'>Portfolio / GitHub</a></div>",
                unsafe_allow_html=True)

        trust_pct = int((u["trust_score"] / 10) * 100)
        st.markdown(f"""
        <div style='margin-bottom:6px;'>
            <div style='display:flex;justify-content:space-between;
                color:#475569;font-size:11px;margin-bottom:5px;'>
                <span>Trust Score</span><span>{u['trust_score']} / 10</span>
            </div>
            <div class='trust-bar-bg'>
                <div class='trust-bar-fill' style='width:{trust_pct}%;'></div>
            </div>
            <div style='font-size:11px;color:#334155;margin-top:5px;'>
                Based on {u['total_ratings']} ratings</div>
        </div>""", unsafe_allow_html=True)

        if u.get("skills"):
            tags = "".join(
                f"<span class='cs-badge badge-cyan'>{s.strip()}</span>"
                for s in u["skills"].split(",") if s.strip()
            )
            st.markdown(f"""
            <div style='margin-top:12px;padding-top:12px;border-top:1px solid #1e293b;'>
                <div style='font-size:11px;font-weight:700;text-transform:uppercase;
                    letter-spacing:.08em;color:#334155;margin-bottom:8px;'>Skills</div>
                {tags}
            </div>""", unsafe_allow_html=True)

    with main:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Edit Profile", "My Tasks", "My Knowledge Posts", "Feedback Received", "Give Rating",
        ])

        with tab1:
            with st.form("edit_profile_form"):
                eu1, eu2 = st.columns(2)
                with eu1:
                    n_user = st.text_input("Username",   value=u["username"])
                    n_port = st.text_input("Portfolio",  value=u["portfolio"] or "")
                with eu2:
                    n_exp  = st.selectbox(
                        "Experience Level",
                        ["Beginner", "Intermediate", "Advanced", "Expert"],
                        index=["Beginner","Intermediate","Advanced","Expert"].index(u["experience"])
                              if u["experience"] in ["Beginner","Intermediate","Advanced","Expert"] else 0)

                n_bio = st.text_area("Bio", value=u["bio"] or "", height=80)

                # Skill update with dropdown
                st.markdown("**Update Primary Skill**")
                existing_parts = u["skills"].split(" - ") if " - " in (u["skills"] or "") else [None, None]
                ec1, ec2 = st.columns(2)
                with ec1:
                    cat_opts     = ["Select a category"] + SKILL_CATEGORIES
                    def_cat_idx  = (SKILL_CATEGORIES.index(existing_parts[0]) + 1
                                    if existing_parts[0] in SKILL_CATEGORIES else 0)
                    new_cat      = st.selectbox("Skill Category", cat_opts,
                                               index=def_cat_idx, key="ep_skill_cat")
                with ec2:
                    if new_cat == "Select a category":
                        st.selectbox("Skill", ["Select category first"],
                                     key="ep_skill_val", disabled=True)
                        new_skill = None
                    else:
                        skill_opts = SKILLS_BY_CATEGORY.get(new_cat, []) + ["Other"]
                        def_sk_idx = (skill_opts.index(existing_parts[1])
                                      if len(existing_parts) > 1 and existing_parts[1] in skill_opts
                                      else 0)
                        new_skill = st.selectbox("Skill", skill_opts,
                                                index=def_sk_idx, key="ep_skill_val")

                if st.form_submit_button("Save Changes", use_container_width=True):
                    new_skills = (f"{new_cat} - {new_skill}"
                                  if new_cat and new_cat != "Select a category" and new_skill
                                  else u["skills"])
                    update_profile(u["id"], n_user, new_skills, n_exp, n_bio, n_port)
                    fresh = get_user(u["id"])
                    st.session_state.user = fresh
                    st.success("Profile updated successfully.")
                    st.rerun()

        with tab2:
            my_tasks = get_my_tasks(u["id"], entry_type=TYPE_TASK)
            if not my_tasks:
                empty_state("No tasks posted yet", "Post your first task to find collaborators.")
            for t in my_tasks:
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div style='font-weight:600;color:#f1f5f9;'>{t['title']}</div>
                        {status_badge(t['status'])}
                    </div>
                    <div style='margin-top:6px;'>
                        <span class='cs-badge badge-slate'>{t['skills']}</span>
                        <span class='cs-badge badge-violet'>{t['category']}</span>
                    </div>
                    <div style='font-size:11px;color:#334155;margin-top:6px;'>
                        {str(t['created_at'])[:10]}</div>
                </div>""", unsafe_allow_html=True)

        with tab3:
            my_know = get_my_tasks(u["id"], entry_type=TYPE_KNOWLEDGE)
            if not my_know:
                empty_state("No knowledge posts yet",
                            "Share your expertise or request help learning a topic.")
            for t in my_know:
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;'>
                        <div style='font-weight:600;color:#f1f5f9;'>{t['title']}</div>
                        {status_badge(t['status'])}
                    </div>
                    <div style='margin-top:6px;'>
                        <span class='cs-badge badge-teal'>{t['skills']}</span>
                        <span class='cs-badge badge-violet'>{t['category']}</span>
                    </div>
                    <div style='font-size:11px;color:#334155;margin-top:6px;'>
                        {str(t['created_at'])[:10]}</div>
                </div>""", unsafe_allow_html=True)

        with tab4:
            fbs = get_feedback_for_user(u["id"])
            if not fbs:
                empty_state("No feedback received yet",
                            "Collaborate with others to receive ratings.")
            else:
                avg = round(sum(f["rating"] for f in fbs) / len(fbs), 1)
                st.markdown(f"""
                <div class='cs-card' style='text-align:center;padding:20px;margin-bottom:14px;'>
                    <div style='font-size:32px;font-weight:900;color:#22d3ee;'>{avg}</div>
                    <div style='font-size:13px;color:#475569;margin-top:4px;'>
                        Average Rating / 5 &nbsp;&middot;&nbsp; {len(fbs)} reviews</div>
                </div>""", unsafe_allow_html=True)
                for f in fbs:
                    stars = "★" * f['rating'] + "☆" * (5 - f['rating'])
                    st.markdown(f"""
                    <div class='cs-card' style='padding:14px;'>
                        <div style='display:flex;justify-content:space-between;align-items:center;'>
                            <span style='font-weight:600;color:#f1f5f9;font-size:13px;'>
                                {f['from_name']}</span>
                            <span style='color:#f59e0b;font-size:14px;letter-spacing:1px;'>
                                {stars}</span>
                        </div>
                        <div style='font-size:13px;color:#64748b;margin-top:6px;'>
                            {f['comment'] or 'No comment left.'}</div>
                        <div style='font-size:11px;color:#334155;margin-top:5px;'>
                            {str(f['created_at'])[:10]}</div>
                    </div>""", unsafe_allow_html=True)

        with tab5:
            others = db_fetchall(
                "SELECT id, username, skills, trust_score FROM users "
                "WHERE id != ? AND is_active = 1 AND role = 'user'",
                (u["id"],))
            if not others:
                empty_state("No other users yet",
                            "Once more users join, you can rate them here.")
            else:
                opts   = [f"{x['username']} ({x['skills'] or 'no skills listed'})" for x in others]
                chosen = st.selectbox("Select a collaborator to rate", opts, key="gr_select")
                to_id  = others[opts.index(chosen)]["id"]
                rating = st.slider("Rating (1 to 5)", 1, 5, 4, key="gr_slider")
                stars_preview = "★" * rating + "☆" * (5 - rating)
                st.markdown(
                    f"<div style='font-size:20px;color:#f59e0b;letter-spacing:2px;margin:4px 0;'>"
                    f"{stars_preview}</div>",
                    unsafe_allow_html=True)
                comment = st.text_area("Comment (optional)",
                                       placeholder="Describe your experience collaborating...",
                                       key="gr_comment")
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
#  AI MATCH
# ═══════════════════════════════════════════════════════════════
def page_ai_match():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "AI Skill Matching")
    section_header("AI Skill Matching",
                   "Describe your task and let the AI surface the best collaborators.")

    left, right = st.columns([3, 2])
    with left:
        with st.form("ai_match_form"):
            ai_title  = st.text_input("Task Title",       placeholder="e.g., Build a data dashboard")
            ai_desc   = st.text_area("Description",        placeholder="Describe what you need...", height=110)
            ai_skills = st.text_input("Skills Required",  placeholder="e.g., Python, Plotly, Pandas")
            run = st.form_submit_button("Find Best Matches", use_container_width=True)

        if run:
            if not all([ai_title, ai_desc, ai_skills]):
                st.warning("Please fill in all three fields.")
            else:
                with st.spinner("Analyzing profiles..."):
                    try:
                        from ai_matching import match_users_to_task
                        matches = match_users_to_task(
                            ai_title, ai_desc, ai_skills,
                            st.session_state.user["id"])
                        st.session_state.ai_matches = matches
                        st.session_state.ai_done    = True
                    except Exception as e:
                        st.session_state.ai_done = False
                        st.error(f"Matching error: {e}")
                        st.info("Set OPENAI_API_KEY in Streamlit Cloud Secrets to enable AI matching.")

    with right:
        st.markdown("""
        <div class='cs-card'>
            <div style='font-size:13px;font-weight:700;color:#22d3ee;
                margin-bottom:14px;letter-spacing:.02em;'>How AI Matching Works</div>
            <div style='font-size:13px;color:#475569;line-height:2.2;'>
                1. Describe your task requirements<br>
                2. The AI reads all user profiles<br>
                3. Skills and experience are compared<br>
                4. Trust scores are factored in<br>
                5. Top 3 matches are returned<br>
                6. Notify and start collaborating
            </div>
        </div>""", unsafe_allow_html=True)

    if st.session_state.ai_done and st.session_state.ai_matches:
        matches = st.session_state.ai_matches
        st.markdown(
            f"<br><div style='font-size:15px;font-weight:700;color:#f1f5f9;margin-bottom:14px;'>"
            f"Top {len(matches)} Matches</div>",
            unsafe_allow_html=True)

        ranks = ["#1", "#2", "#3"]
        for i, m in enumerate(matches, 1):
            score = m.get("match_score", 0)
            sc    = "#22d3ee" if score >= 80 else "#f59e0b" if score >= 60 else "#94a3b8"
            row   = db_fetchone("SELECT * FROM users WHERE username=?", (m["name"],))
            u_sk  = row["skills"]      if row else "N/A"
            u_exp = row["experience"]  if row else "N/A"
            u_tr  = row["trust_score"] if row else 0
            u_pt  = row["portfolio"]   if row else ""

            mc1, mc2 = st.columns([4, 1])
            with mc1:
                st.markdown(f"""
                <div class='cs-card' style='border-color:#1e293b;'>
                    <div style='display:flex;align-items:center;gap:14px;margin-bottom:12px;'>
                        <div style='font-size:13px;font-weight:700;color:#334155;'>{ranks[i-1] if i<=3 else ""}</div>
                        {mk_avatar(m['name'], 42)}
                        <div>
                            <div style='font-size:15px;font-weight:800;color:#f1f5f9;'>{m['name']}</div>
                            <div style='font-size:12px;color:#475569;margin-top:2px;'>{u_exp}</div>
                        </div>
                    </div>
                    <div style='margin-bottom:8px;'>
                        <span class='cs-badge badge-slate'>{u_sk}</span>
                    </div>
                    <div style='font-size:13px;color:#64748b;line-height:1.6;'>{m.get('reason', '')}</div>
                    {'<div style="margin-top:10px;"><a href="' + u_pt + '" target="_blank" style="font-size:12px;color:#22d3ee;font-weight:600;">Portfolio / GitHub</a></div>' if u_pt else ''}
                </div>""", unsafe_allow_html=True)
            with mc2:
                st.markdown(f"""
                <div style='text-align:center;padding:12px;'>
                    <div style='font-size:28px;font-weight:900;color:{sc};line-height:1;'>{score}%</div>
                    <div style='font-size:10px;color:#334155;margin-top:3px;'>Match</div>
                    <div style='font-size:18px;font-weight:800;color:#22d3ee;margin-top:10px;'>{u_tr}</div>
                    <div style='font-size:10px;color:#334155;'>Trust</div>
                </div>""", unsafe_allow_html=True)
            if row:
                if st.button(f"Notify {m['name']}", key=f"notify_{i}"):
                    add_notification(row["id"], "AI Match Alert",
                        f"{st.session_state.user['username']} wants to collaborate with you.")
                    st.success(f"{m['name']} has been notified.")

    elif st.session_state.ai_done and not st.session_state.ai_matches:
        st.info("No matches found. Invite more people to join the platform.")


# ═══════════════════════════════════════════════════════════════
#  COMMUNITY
# ═══════════════════════════════════════════════════════════════
def page_community():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home", "Community")
    section_header("Community", "Browse all members and explore their skills.")

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        search = st.text_input("", placeholder="Search by name or skill...",
                               key="cm_search", label_visibility="collapsed")
    with sc2:
        exp_f = st.selectbox("", ["All Levels","Beginner","Intermediate","Advanced","Expert"],
                             key="cm_exp", label_visibility="collapsed")

    uid = st.session_state.user["id"]
    where, params = ["role='user'", "is_active=1", f"id!='{uid}'"], []
    if search:
        where.append("(username LIKE ? OR skills LIKE ?)")
        params += [f"%{search}%"] * 2
    if exp_f != "All Levels":
        where.append("experience=?"); params.append(exp_f)

    users = db_fetchall(
        f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY trust_score DESC",
        tuple(params))

    st.markdown(
        f"<div style='color:#475569;font-size:13px;margin-bottom:16px;'>"
        f"{len(users)} member(s)</div>",
        unsafe_allow_html=True)

    if not users:
        empty_state("No members found", "Try adjusting your search filters.")
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
            pct  = int((u["trust_score"] / 10) * 100)
            ini  = "".join(w[0].upper() for w in u["username"].split()[:2])
            tags = "".join(
                f"<span class='cs-badge badge-slate' style='font-size:10px;'>{s.strip()}</span>"
                for s in (u["skills"] or "").split(",")[:2] if s.strip()
            )
            port = (
                f'<div style="margin-top:10px;">'
                f'<a href="{u["portfolio"]}" target="_blank" '
                f'style="font-size:12px;color:#22d3ee;font-weight:600;">Portfolio</a></div>'
                if u.get("portfolio") else ""
            )
            col.markdown(f"""
            <div class='cs-card'>
                <div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>
                    <div style='width:42px;height:42px;border-radius:50%;
                        background:linear-gradient(135deg,#22d3ee,#7c3aed);
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:15px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                    <div style='flex:1;min-width:0;'>
                        <div style='font-weight:700;color:#f1f5f9;font-size:13px;
                            white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>
                            {u['username']}</div>
                        <span class='cs-badge {exp_badge.get(u["experience"], "badge-slate")}'
                            style='font-size:10px;'>{u['experience']}</span>
                    </div>
                    <div style='text-align:right;flex-shrink:0;'>
                        <div style='font-size:18px;font-weight:800;color:#22d3ee;'>{u['trust_score']}</div>
                        <div style='font-size:10px;color:#334155;'>trust</div>
                    </div>
                </div>
                <div style='font-size:12px;color:#475569;line-height:1.55;margin-bottom:10px;'>
                    {(u['bio'] or 'No bio provided.')[:90]}...</div>
                <div>{tags}</div>
                <div class='trust-bar-bg'>
                    <div class='trust-bar-fill' style='width:{pct}%;'></div>
                </div>
                <div style='font-size:10px;color:#334155;margin-top:4px;'>
                    {u['total_ratings']} ratings received</div>
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
        bg     = "#0d1829" if not n["is_read"] else "#0f172a"
        border = "#1e3a5f"  if not n["is_read"] else "#1e293b"
        unread_dot = (
            "<span style='width:6px;height:6px;background:#22d3ee;border-radius:50%;"
            "display:inline-block;margin-left:6px;vertical-align:middle;'></span>"
            if not n["is_read"] else ""
        )
        st.markdown(f"""
        <div style='background:{bg};border:1px solid {border};border-radius:10px;
            padding:14px 18px;margin-bottom:8px;'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div style='font-weight:600;font-size:13px;color:#e2e8f0;'>
                    {n['title']}{unread_dot}</div>
                <div style='font-size:11px;color:#334155;white-space:nowrap;margin-left:12px;'>
                    {str(n['created_at'])[:16]}</div>
            </div>
            <div style='font-size:13px;color:#64748b;margin-top:5px;line-height:1.5;'>
                {n['message']}</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN SIDEBAR
# ═══════════════════════════════════════════════════════════════
def admin_sidebar():
    with st.sidebar:
        st.markdown("**Admin Panel**")
        st.markdown(f"Signed in as: *{st.session_state.user['username']}*")
        st.markdown("---")
        if st.button("Dashboard",  key="asb_dash",   use_container_width=True): go("admin_dashboard")
        if st.button("Users",      key="asb_users",  use_container_width=True): go("admin_users")
        if st.button("All Posts",  key="asb_tasks",  use_container_width=True): go("admin_tasks")
        if st.button("Browse",     key="asb_browse", use_container_width=True): go("browse_tasks")
        st.markdown("---")
        if st.button("Sign Out",   key="asb_logout", use_container_width=True):
            st.session_state.user = None; go("landing")


# ═══════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_admin_dashboard():
    require_admin()
    render_navbar()
    admin_sidebar()
    breadcrumb("Admin", "Dashboard")

    st.markdown("<div class='admin-only-banner'>Admin View — This data is not visible to regular users.</div>",
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

    st.markdown("#### Users")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Users",    total_users)
    m2.metric("Admins",         total_admins)
    m3.metric("Active Users",   active_users)
    m4.metric("New This Week",  new_week)

    st.markdown("#### Task Collaboration")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Total Tasks",    total_tasks)
    t2.metric("Open",           open_tasks)
    t3.metric("Closed",         total_tasks - open_tasks)
    t4.metric("Applications",   total_apps)

    st.markdown("#### Knowledge Exchange")
    k1, k2, k3, _ = st.columns(4)
    k1.metric("Total Posts",    total_know)
    k2.metric("Active",         open_know)
    k3.metric("Completed",      total_know - open_know)

    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Posts by Category")
        cat_data = db_fetchall(
            "SELECT category, COUNT(*) AS cnt FROM tasks "
            "GROUP BY category ORDER BY cnt DESC")
        if cat_data:
            df = pd.DataFrame(cat_data); df.columns = ["Category", "Count"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.markdown("<div style='color:#475569;font-size:13px;'>No data yet.</div>",
                        unsafe_allow_html=True)

    with col2:
        st.markdown("#### Recent Activity")
        rec_u = db_fetchall("SELECT username AS name, 'User registered' AS action, created_at FROM users ORDER BY created_at DESC LIMIT 5")
        rec_t = db_fetchall("SELECT title AS name, 'Task posted' AS action, created_at FROM tasks WHERE type='task' ORDER BY created_at DESC LIMIT 3")
        rec_k = db_fetchall("SELECT title AS name, 'Knowledge posted' AS action, created_at FROM tasks WHERE type='knowledge' ORDER BY created_at DESC LIMIT 3")
        activity = sorted(rec_u + rec_t + rec_k,
                          key=lambda x: x["created_at"], reverse=True)[:10]
        for a in activity:
            dot_c = ("#22d3ee" if "registered" in a["action"]
                     else "#2dd4bf" if "Knowledge" in a["action"]
                     else "#a78bfa")
            st.markdown(f"""
            <div style='display:flex;gap:10px;padding:7px 0;border-bottom:1px solid #1e293b;'>
                <div style='width:6px;height:6px;border-radius:50%;background:{dot_c};
                    margin-top:5px;flex-shrink:0;'></div>
                <div>
                    <div style='font-size:13px;color:#e2e8f0;'>
                        {a['action']}: <strong>{a['name']}</strong></div>
                    <div style='font-size:11px;color:#334155;'>{str(a['created_at'])[:16]}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("#### Leaderboard — Top Users by Trust Score")
    top    = get_top_users(8)
    medals = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]
    lc1, lc2 = st.columns(2)
    for i, u in enumerate(top):
        col = lc1 if i % 2 == 0 else lc2
        col.markdown(f"""
        <div class='cs-card' style='padding:14px;'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <div style='font-size:12px;color:#334155;font-weight:700;
                        text-transform:uppercase;letter-spacing:.04em;'>{medals[i]}</div>
                    <div style='font-size:14px;font-weight:700;color:#f1f5f9;'>{u['username']}</div>
                    <div style='font-size:11px;color:#475569;'>{u['skills'] or '—'}</div>
                </div>
                <div style='text-align:right;'>
                    <div style='font-size:20px;font-weight:900;color:#22d3ee;'>{u['trust_score']}</div>
                    <div style='font-size:10px;color:#334155;'>{u['total_ratings']} ratings</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN USERS
# ═══════════════════════════════════════════════════════════════
def page_admin_users():
    require_admin()
    render_navbar(); admin_sidebar()
    breadcrumb("Admin", "Manage Users"); back_btn()
    section_header("Manage Users", "View, search and manage all registered users.")

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        search = st.text_input("", placeholder="Search by username or email...",
                               key="au_search", label_visibility="collapsed")
    with sc2:
        role_f = st.selectbox("", ["All Roles", "user", "admin"],
                              key="au_role", label_visibility="collapsed")

    where, params = ["1=1"], []
    if search:
        where.append("(username LIKE ? OR email LIKE ?)"); params += [f"%{search}%"] * 2
    if role_f != "All Roles":
        where.append("role=?"); params.append(role_f)

    users = db_fetchall(
        f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY created_at DESC",
        tuple(params))
    st.markdown(
        f"<div style='color:#475569;font-size:13px;margin-bottom:14px;'>{len(users)} user(s)</div>",
        unsafe_allow_html=True)

    for u in users:
        with st.expander(f"{u['username']}   [{u['role'].upper()}]   {u['email']}"):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                st.markdown(f"""
                <div style='font-size:13px;color:#64748b;line-height:2.1;'>
                    <strong style='color:#94a3b8;'>Role</strong><br>{u['role']}<br>
                    <strong style='color:#94a3b8;'>Skills</strong><br>{u['skills'] or '—'}<br>
                    <strong style='color:#94a3b8;'>Level</strong><br>{u['experience']}
                </div>""", unsafe_allow_html=True)
            with c2:
                tc = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE created_by=? AND type='task'",      (u["id"],))["c"]
                kc = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE created_by=? AND type='knowledge'", (u["id"],))["c"]
                rc = db_fetchone("SELECT COUNT(*) AS c FROM feedback WHERE to_user_id=?",                   (u["id"],))["c"]
                st.markdown(f"""
                <div style='font-size:13px;color:#64748b;line-height:2.1;'>
                    <strong style='color:#94a3b8;'>Tasks / Knowledge</strong><br>{tc} / {kc}<br>
                    <strong style='color:#94a3b8;'>Ratings Received</strong><br>{rc}<br>
                    <strong style='color:#94a3b8;'>Status</strong><br>
                    {'Active' if u['is_active'] else 'Inactive'}<br>
                    <strong style='color:#94a3b8;'>Joined</strong><br>{str(u['created_at'])[:10]}
                </div>""", unsafe_allow_html=True)
            with c3:
                if u["role"] != "admin":
                    if u["is_active"]:
                        if st.button("Deactivate", key=f"deact_{u['id']}"):
                            db_execute("UPDATE users SET is_active=0 WHERE id=?", (u["id"],))
                            st.success("User deactivated."); st.rerun()
                    else:
                        if st.button("Activate", key=f"act_{u['id']}"):
                            db_execute("UPDATE users SET is_active=1 WHERE id=?", (u["id"],))
                            st.success("User activated."); st.rerun()


# ═══════════════════════════════════════════════════════════════
#  ADMIN TASKS
# ═══════════════════════════════════════════════════════════════
def page_admin_tasks():
    require_admin()
    render_navbar(); admin_sidebar()
    breadcrumb("Admin", "All Posts"); back_btn()
    section_header("All Tasks and Knowledge Posts",
                   "Monitor and moderate all platform content.")

    sc1, sc2, sc3, sc4 = st.columns([2.5, 1.2, 1.2, 1.2])
    with sc1:
        search   = st.text_input("", placeholder="Search...",
                                 key="at_search", label_visibility="collapsed")
    with sc2:
        type_f   = st.selectbox("", ["All Types", "Tasks Only", "Knowledge Only"],
                                key="at_type",   label_visibility="collapsed")
    with sc3:
        status_f = st.selectbox("", ["All Status", "open", "closed"],
                                key="at_status", label_visibility="collapsed")
    with sc4:
        cat_f    = st.selectbox("", ["All Categories"] + CATEGORIES,
                                key="at_cat",    label_visibility="collapsed")

    type_map = {"Tasks Only": TYPE_TASK, "Knowledge Only": TYPE_KNOWLEDGE}
    entry_type = type_map.get(type_f, None)
    tasks = get_all_tasks_admin(entry_type=entry_type)

    if search:
        s = search.lower()
        tasks = [t for t in tasks
                 if s in t["title"].lower() or s in (t["skills"] or "").lower()]
    if status_f != "All Status":
        tasks = [t for t in tasks if t["status"] == status_f]
    if cat_f != "All Categories":
        tasks = [t for t in tasks if t["category"] == cat_f]

    st.markdown(
        f"<div style='color:#475569;font-size:13px;margin-bottom:14px;'>"
        f"{len(tasks)} record(s)</div>",
        unsafe_allow_html=True)

    if not tasks:
        empty_state("No records found", "Try adjusting the filters.")
        return

    for t in tasks:
        is_know = t.get("type") == TYPE_KNOWLEDGE
        header  = f"{'[K] ' if is_know else '[T] '}{t['title']}  —  {t['creator_name']}  —  {t['status'].upper()}"

        with st.expander(header):
            tc1, tc2 = st.columns([3, 1])
            with tc1:
                st.markdown(f"""
                <div style='color:#64748b;font-size:13px;line-height:1.7;margin-bottom:8px;'>
                    {t['description']}</div>
                {type_badge(t.get('type', TYPE_TASK))}
                {status_badge(t['status'])}
                {priority_badge(t.get('priority', 'Normal'))}
                <span class='cs-badge badge-violet'>{t['category']}</span>
                <span class='cs-badge badge-slate'>{t['skills']}</span>
                <span class='cs-badge badge-slate'>{t.get('applicant_count', 0)} interested</span>
                <div style='font-size:11px;color:#334155;margin-top:6px;'>
                    Posted {str(t['created_at'])[:10]}</div>
                """, unsafe_allow_html=True)
            with tc2:
                new_s = st.selectbox(
                    "Status", ["open", "in_progress", "closed"],
                    index=["open", "in_progress", "closed"].index(t["status"]),
                    key=f"at_stat_{t['id']}")
                if st.button("Update", key=f"at_upd_{t['id']}"):
                    update_task_status(t["id"], new_s); st.success("Updated."); st.rerun()
                if st.button("Delete", key=f"at_del_{t['id']}"):
                    delete_task(t["id"]); st.success("Deleted."); st.rerun()


# ═══════════════════════════════════════════════════════════════
#  ROUTER
# ═══════════════════════════════════════════════════════════════
PAGES = {
    "landing":         page_landing,
    "login":           page_login,
    "register":        page_register,
    "dashboard":       page_dashboard,
    "browse_tasks":    page_browse_tasks,
    "post_task":       page_post_task,
    "profile":         page_profile,
    "ai_match":        page_ai_match,
    "community":       page_community,
    "notifications":   page_notifications,
    "admin_dashboard": page_admin_dashboard,
    "admin_users":     page_admin_users,
    "admin_tasks":     page_admin_tasks,
}

PAGES.get(st.session_state.page, page_landing)()
