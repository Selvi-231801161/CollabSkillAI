# app.py  ─────────────────────────────────────────────────────
# CollabSkill AI  |  Python + Streamlit  |  Production-grade
# RBAC: admin / user  |  Full navigation  |  Role-based dashboards
# ─────────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
from database import init_db, db_fetchall, db_fetchone, db_execute
from auth import (register_user, login_user, get_user,
                  update_profile, update_trust_score, get_top_users)
from tasks_db import (
    create_task, get_task, get_all_open_tasks, get_my_tasks,
    get_all_tasks_admin, update_task_status, delete_task,
    apply_to_task, get_applications_for_task, get_my_applications,
    submit_feedback, get_feedback_for_user,
    add_notification, get_notifications, get_unread_count, mark_all_read,
    CATEGORIES,
)

# ── Init DB ───────────────────────────────────────────────────
init_db()

# ── Page config ───────────────────────────────────────────────
st.set_page_config(
    page_title="CollabSkill AI",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Session defaults ──────────────────────────────────────────
DEFAULTS = {
    "page":        "landing",
    "user":        None,
    "prev_pages":  [],   # navigation history stack
    "ai_matches":  [],
    "ai_searched": False,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ═══════════════════════════════════════════════════════════════
#  NAVIGATION HELPERS
# ═══════════════════════════════════════════════════════════════
def go(page: str):
    """Navigate to a new page, pushing current to history."""
    if st.session_state.page != page:
        st.session_state.prev_pages.append(st.session_state.page)
    st.session_state.page = page
    st.rerun()


def go_back():
    """Navigate to previous page (browser-like back button)."""
    if st.session_state.prev_pages:
        prev = st.session_state.prev_pages.pop()
        st.session_state.page = prev
        st.rerun()
    else:
        go("landing")


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


def is_logged_in():
    return st.session_state.user is not None


# ═══════════════════════════════════════════════════════════════
#  GLOBAL CSS
# ═══════════════════════════════════════════════════════════════
def inject_css():
    st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* ── Hide Streamlit chrome ── */
header[data-testid="stHeader"],
#MainMenu, footer { visibility: hidden; height: 0; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem !important; }

/* ── Base ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #050816 !important;
    color: #e2e8f0;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea,
.stSelectbox > div > div, .stNumberInput input {
    background-color: #0f172a !important;
    color: #e2e8f0 !important;
    border: 1px solid #1e293b !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #22d3ee !important;
    box-shadow: 0 0 0 3px rgba(34,211,238,0.08) !important;
}
label { color: #94a3b8 !important; font-size: 12px !important;
        font-weight: 600 !important; letter-spacing: 0.04em !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg,#22d3ee,#7c3aed) !important;
    color: #fff !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* ── Metrics ── */
[data-testid="metric-container"] {
    background: #0f172a !important; border: 1px solid #1e293b !important;
    border-radius: 14px !important; padding: 18px !important;
}
[data-testid="metric-container"] label {
    color: #475569 !important; font-size: 11px !important;
    text-transform: uppercase; letter-spacing: 0.08em !important;
}
[data-testid="stMetricValue"] {
    color: #22d3ee !important; font-size: 28px !important; font-weight: 800 !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background-color: #0f172a !important; border: 1px solid #1e293b !important;
    border-radius: 12px !important; color: #e2e8f0 !important; font-weight: 600 !important;
}

/* ── Slider ── */
.stSlider [data-baseweb="slider"] { background: #1e293b !important; }

/* ── Checkbox ── */
.stCheckbox label { color: #94a3b8 !important; }

/* ── Divider ── */
hr { border-color: #1e293b !important; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background-color: #070d1f !important; border-right: 1px solid #1e293b !important; }
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }

/* ── Dataframe ── */
.stDataFrame { background: #0f172a !important; border-radius: 12px !important; }

/* ── Custom components ── */
.cs-card {
    background: #0f172a; border: 1px solid #1e293b;
    border-radius: 14px; padding: 22px; margin-bottom: 14px;
}
.cs-card-hover:hover { border-color: #334155; }

.cs-badge {
    display: inline-block; padding: 3px 11px; border-radius: 20px;
    font-size: 11px; font-weight: 600; margin: 2px 3px 2px 0;
}
.cs-badge-cyan   { background:rgba(34,211,238,0.1); color:#22d3ee; border:1px solid rgba(34,211,238,0.2); }
.cs-badge-violet { background:rgba(124,58,237,0.1); color:#a78bfa; border:1px solid rgba(124,58,237,0.2); }
.cs-badge-green  { background:rgba(34,197,94,0.1);  color:#4ade80; border:1px solid rgba(34,197,94,0.2); }
.cs-badge-amber  { background:rgba(245,158,11,0.1); color:#fbbf24; border:1px solid rgba(245,158,11,0.2); }
.cs-badge-red    { background:rgba(239,68,68,0.1);  color:#f87171; border:1px solid rgba(239,68,68,0.2); }
.cs-badge-slate  { background:#1e293b; color:#64748b; border:1px solid #334155; }

.page-title {
    font-size: 28px; font-weight: 900; color: #f1f5f9;
    letter-spacing: -0.02em; margin-bottom: 4px;
}
.page-sub { color: #475569; font-size: 14px; margin-bottom: 24px; }

.trust-bar-bg { background:#1e293b; border-radius:4px; height:5px; margin-top:6px; }
.trust-bar-fill { height:5px; border-radius:4px;
    background:linear-gradient(90deg,#22d3ee,#7c3aed); }

.match-card {
    background: linear-gradient(135deg,#0f172a,#130f2a);
    border: 1px solid #312e81; border-radius: 14px; padding: 22px; margin-bottom: 12px;
}
.notif-item { padding:12px 0; border-bottom:1px solid #1e293b; }
.notif-unread { background:rgba(34,211,238,0.03); border-radius:8px; padding:12px; }
.admin-alert {
    background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.2);
    border-radius:10px; padding:14px 18px; color:#f87171; font-size:14px;
}
.success-alert {
    background:rgba(34,197,94,0.08); border:1px solid rgba(34,197,94,0.2);
    border-radius:10px; padding:14px 18px; color:#4ade80; font-size:14px;
}
.hero-title {
    font-size: 64px; font-weight: 900; color: #f1f5f9;
    line-height: 1.05; letter-spacing: -0.04em; text-align: center;
}
.hero-gradient {
    font-size: 64px; font-weight: 900; line-height: 1.05;
    letter-spacing: -0.04em; text-align: center;
    background: linear-gradient(135deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  NAVBAR  (rendered on every page after landing)
# ═══════════════════════════════════════════════════════════════
def render_navbar():
    u = st.session_state.user

    # Unread notification count
    unread = get_unread_count(u["id"]) if u else 0
    notif_label = f"🔔 ({unread})" if unread > 0 else "🔔"

    if is_admin():
        cols = st.columns([2.5, 1, 1, 1, 1, 1, 1])
        labels = ["🏠 Home", "📊 Admin", "👥 Users", "📋 Tasks", notif_label, "👤 Profile", "🚪 Logout"]
        pages  = ["landing", "admin_dashboard", "admin_users", "admin_tasks", "notifications", "profile", "__logout__"]
    elif is_logged_in():
        cols = st.columns([2.5, 1, 1, 1, 1, 1, 1])
        labels = ["🏠 Home", "🗂 Dashboard", "🔍 Tasks", "➕ Post", notif_label, "👤 Profile", "🚪 Logout"]
        pages  = ["landing", "dashboard", "browse_tasks", "post_task", "notifications", "profile", "__logout__"]
    else:
        cols = st.columns([5, 1, 1])
        labels = ["Login", "Sign Up"]
        pages  = ["login", "register"]
        with cols[0]:
            st.markdown(
                "<div style='padding-top:10px;font-size:18px;font-weight:800;color:#f1f5f9;'>"
                "🚀 Collab<span style='color:#22d3ee;'>Skill</span> AI</div>",
                unsafe_allow_html=True)
        for i, (lbl, pg) in enumerate(zip(labels, pages)):
            with cols[i + 1]:
                if st.button(lbl, key=f"nav_{pg}", use_container_width=True):
                    go(pg)
        st.markdown("<hr style='border-color:#1e293b;margin:6px 0 20px;'/>", unsafe_allow_html=True)
        return

    with cols[0]:
        st.markdown(
            "<div style='padding-top:10px;font-size:18px;font-weight:800;color:#f1f5f9;'>"
            "🚀 Collab<span style='color:#22d3ee;'>Skill</span> AI"
            + (" <span style='font-size:11px;background:rgba(34,211,238,0.1);"
               "color:#22d3ee;border:1px solid rgba(34,211,238,0.2);"
               "border-radius:20px;padding:2px 10px;'>ADMIN</span>" if is_admin() else "")
            + "</div>",
            unsafe_allow_html=True)

    for i, (lbl, pg) in enumerate(zip(labels, pages)):
        with cols[i + 1]:
            if st.button(lbl, key=f"nav_{pg}", use_container_width=True):
                if pg == "__logout__":
                    st.session_state.user = None
                    st.session_state.prev_pages = []
                    go("landing")
                else:
                    go(pg)

    st.markdown("<hr style='border-color:#1e293b;margin:6px 0 20px;'/>", unsafe_allow_html=True)


def back_button(label="← Back"):
    """Renders a small back button."""
    if st.button(label, key="back_btn"):
        go_back()


def breadcrumb(*crumbs):
    """Renders a breadcrumb trail."""
    trail = " › ".join(
        [f"<a href='#' style='color:#475569;text-decoration:none;'>{c}</a>"
         if i < len(crumbs) - 1 else f"<span style='color:#94a3b8;'>{c}</span>"
         for i, c in enumerate(crumbs)]
    )
    st.markdown(f"<div style='font-size:12px;color:#475569;margin-bottom:12px;'>{trail}</div>",
                unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def status_badge(status):
    colors = {"open": "cs-badge-green", "in_progress": "cs-badge-amber",
              "closed": "cs-badge-slate", "pending": "cs-badge-amber",
              "accepted": "cs-badge-green", "rejected": "cs-badge-red"}
    return f"<span class='cs-badge {colors.get(status, \"cs-badge-slate\")}'>{status.replace('_',' ')}</span>"


def priority_badge(p):
    c = {"Urgent": "cs-badge-red", "Normal": "cs-badge-cyan", "Low": "cs-badge-slate"}.get(p, "cs-badge-slate")
    return f"<span class='cs-badge {c}'>{p}</span>"


def stars(n):
    return "⭐" * max(0, min(5, int(n)))


def trust_bar(score, max_score=10):
    pct = int((score / max_score) * 100)
    return (f"<div class='trust-bar-bg'>"
            f"<div class='trust-bar-fill' style='width:{pct}%;'></div></div>")


def avatar(name, size=40):
    ini = "".join(w[0].upper() for w in (name or "U").split()[:2])
    return (f"<div style='width:{size}px;height:{size}px;border-radius:50%;"
            f"background:linear-gradient(135deg,#22d3ee,#7c3aed);"
            f"display:flex;align-items:center;justify-content:center;"
            f"font-size:{size//3}px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>")


def empty_state(icon, title, desc=""):
    st.markdown(f"""
    <div class='cs-card' style='text-align:center;padding:48px 32px;'>
        <div style='font-size:48px;margin-bottom:12px;'>{icon}</div>
        <div style='color:#f1f5f9;font-weight:700;font-size:16px;margin-bottom:6px;'>{title}</div>
        <div style='color:#475569;font-size:13px;'>{desc}</div>
    </div>
    """, unsafe_allow_html=True)


def task_card_html(t, show_actions=False, is_owner=False):
    """Returns an HTML string for a task card."""
    return f"""
    <div class='cs-card cs-card-hover'>
        <div style='display:flex;justify-content:space-between;align-items:flex-start;gap:10px;'>
            <div style='flex:1;'>
                <div style='color:#f1f5f9;font-weight:700;font-size:15px;margin-bottom:4px;'>{t['title']}</div>
                <div style='display:flex;flex-wrap:wrap;gap:4px;'>
                    {status_badge(t['status'])}
                    {priority_badge(t['priority'])}
                    <span class='cs-badge cs-badge-violet'>{t['category']}</span>
                </div>
            </div>
        </div>
        <div style='color:#64748b;font-size:13px;margin:10px 0;line-height:1.6;'>{t['description'][:180]}{'...' if len(t['description'])>180 else ''}</div>
        <div style='display:flex;flex-wrap:wrap;gap:6px;font-size:12px;'>
            <span class='cs-badge cs-badge-cyan'>🛠 {t['skills']}</span>
            {'<span class="cs-badge cs-badge-slate">⏰ ' + t['deadline'] + '</span>' if t.get('deadline') else ''}
            <span class='cs-badge cs-badge-slate'>👤 {t.get('creator_name','')}</span>
            <span class='cs-badge cs-badge-slate'>⭐ {t.get('creator_trust',0)}/10</span>
            <span class='cs-badge cs-badge-slate'>👥 {t.get('applicant_count',0)} applicants</span>
            <span class='cs-badge cs-badge-slate'>🕐 {str(t.get('created_at',''))[:10]}</span>
        </div>
    </div>
    """


# ═══════════════════════════════════════════════════════════════
#  PAGE: LANDING
# ═══════════════════════════════════════════════════════════════
def page_landing():
    render_navbar()

    # Hero
    st.markdown("""
    <div style='text-align:center;padding:60px 0 30px;'>
        <div style='display:inline-block;background:rgba(34,211,238,0.08);
            border:1px solid rgba(34,211,238,0.2);color:#22d3ee;
            padding:5px 16px;border-radius:20px;font-size:11px;
            font-weight:700;letter-spacing:0.1em;margin-bottom:24px;'>
            ✦ AI-POWERED SKILL EXCHANGE PLATFORM
        </div>
        <div class='hero-title'>Connect. Collaborate.</div>
        <div class='hero-gradient'>Exchange Skills Smarter.</div>
        <div style='color:#475569;font-size:16px;max-width:500px;
            margin:20px auto 0;line-height:1.7;'>
            An intelligent platform that matches you with the right people —
            using AI to connect digital skill providers with those who need them.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA buttons
    c1, c2, c3, c4 = st.columns([2, 1, 1, 2])
    with c2:
        if st.button("🚀 Get Started", use_container_width=True):
            go("register" if not is_logged_in() else ("admin_dashboard" if is_admin() else "dashboard"))
    with c3:
        if st.button("🔍 Browse Tasks", use_container_width=True):
            go("browse_tasks")

    st.markdown("<br>", unsafe_allow_html=True)

    # Live stats (only counts, no user-specific data)
    total_users = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    total_tasks = db_fetchone("SELECT COUNT(*) AS c FROM tasks")["c"]
    open_tasks  = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open'")["c"]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("👥 Members",      total_users)
    m2.metric("📋 Tasks Posted", total_tasks)
    m3.metric("🟢 Open Tasks",   open_tasks)
    m4.metric("🎯 Match Rate",   "98%")

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature cards
    st.markdown("""
    <div style='text-align:center;color:#475569;font-size:11px;font-weight:700;
        letter-spacing:0.12em;text-transform:uppercase;margin-bottom:20px;'>
        WHAT WE OFFER
    </div>
    """, unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns(4)
    features = [
        ("🤖", "#22d3ee", "rgba(34,211,238,0.08)",  "AI Matching",
         "Smart AI finds the top 3 best-fit collaborators for any task instantly."),
        ("🛡️", "#a78bfa", "rgba(124,58,237,0.08)",  "Trust Scores",
         "Reputation scores built from real peer feedback after every collaboration."),
        ("📋", "#4ade80", "rgba(34,197,94,0.08)",   "Task Board",
         "Post tasks, browse open work, filter by skill and category."),
        ("🌐", "#fbbf24", "rgba(245,158,11,0.08)",  "Community",
         "Connect with developers, designers, marketers and creators."),
    ]
    for col, (icon, color, bg, title, desc) in zip([f1, f2, f3, f4], features):
        col.markdown(f"""
        <div class='cs-card' style='text-align:center;min-height:180px;'>
            <div style='width:44px;height:44px;border-radius:11px;background:{bg};
                display:flex;align-items:center;justify-content:center;
                font-size:20px;margin:0 auto 14px;'>{icon}</div>
            <div style='color:#f1f5f9;font-weight:700;font-size:14px;margin-bottom:7px;'>{title}</div>
            <div style='color:#475569;font-size:12px;line-height:1.6;'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)

    # How it works
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center;color:#475569;font-size:11px;font-weight:700;
        letter-spacing:0.12em;text-transform:uppercase;margin-bottom:20px;'>
        HOW IT WORKS
    </div>
    """, unsafe_allow_html=True)

    h1, h2, h3, h4 = st.columns(4)
    steps = [
        ("01", "Create your profile", "Register, list your skills and experience level."),
        ("02", "Post or browse tasks", "Post what you need or find tasks that match your skills."),
        ("03", "AI finds your match", "Our AI returns the top 3 best-matched collaborators."),
        ("04", "Collaborate & grow", "Work together, rate each other, build your trust score."),
    ]
    for col, (num, title, desc) in zip([h1, h2, h3, h4], steps):
        col.markdown(f"""
        <div class='cs-card'>
            <div style='color:rgba(34,211,238,0.2);font-size:36px;font-weight:900;line-height:1;margin-bottom:10px;'>{num}</div>
            <div style='color:#f1f5f9;font-weight:700;font-size:13px;margin-bottom:6px;'>{title}</div>
            <div style='color:#475569;font-size:12px;line-height:1.6;'>{desc}</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE: LOGIN
# ═══════════════════════════════════════════════════════════════
def page_login():
    render_navbar()
    back_button("← Back to Home")

    _, center, _ = st.columns([1, 1.4, 1])
    with center:
        st.markdown("""
        <div style='background:#0f172a;border:1px solid #1e293b;border-radius:18px;padding:40px;margin-top:20px;'>
            <div style='text-align:center;margin-bottom:24px;'>
                <div style='width:52px;height:52px;background:linear-gradient(135deg,#22d3ee,#7c3aed);
                    border-radius:14px;display:flex;align-items:center;justify-content:center;
                    font-size:22px;font-weight:900;color:#fff;margin:0 auto 12px;'>C</div>
                <div style='font-size:22px;font-weight:800;color:#f1f5f9;'>Welcome back</div>
                <div style='color:#475569;font-size:13px;margin-top:4px;'>Login to your CollabSkill AI account</div>
            </div>
        """, unsafe_allow_html=True)

        email    = st.text_input("Email", placeholder="you@email.com",   key="li_email")
        password = st.text_input("Password", type="password",             key="li_pass")

        if st.button("Login →", use_container_width=True, key="li_btn"):
            if not email or not password:
                st.error("Please fill both fields.")
            else:
                ok, result = login_user(email, password)
                if ok:
                    st.session_state.user = result
                    st.session_state.prev_pages = []
                    st.success(f"Welcome back, {result['name']}!")
                    go("admin_dashboard" if result["role"] == "admin" else "dashboard")
                else:
                    st.error(result)

        st.markdown("<div style='text-align:center;margin-top:16px;color:#475569;font-size:13px;'>Don't have an account?</div>", unsafe_allow_html=True)
        if st.button("Create Account", use_container_width=True, key="li_reg"):
            go("register")

        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE: REGISTER
# ═══════════════════════════════════════════════════════════════
def page_register():
    render_navbar()
    back_button("← Back to Home")
    breadcrumb("Home", "Register")

    st.markdown("<div class='page-title'>Create Your Account 🚀</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Join the CollabSkill AI community</div>", unsafe_allow_html=True)

    with st.form("reg_form", clear_on_submit=False):
        c1, c2 = st.columns(2)
        with c1:
            name     = st.text_input("Full Name *",          placeholder="John Doe")
            email    = st.text_input("Email *",              placeholder="you@email.com")
            password = st.text_input("Password *",           placeholder="Min 6 chars", type="password")
            confirm  = st.text_input("Confirm Password *",   type="password")
        with c2:
            skills   = st.text_input("Your Skills *",        placeholder="Python, React, Design, SEO…")
            exp      = st.selectbox("Experience Level",      ["Beginner", "Intermediate", "Advanced", "Expert"])
            portfolio= st.text_input("Portfolio / GitHub",   placeholder="https://github.com/…")
            bio      = st.text_area("Short Bio",             placeholder="Tell others what you do…", height=97)

        agree    = st.checkbox("I agree to the Terms & Conditions")
        submitted= st.form_submit_button("🚀 Create Account", use_container_width=True)

        if submitted:
            if not agree:
                st.warning("Please accept the Terms & Conditions.")
            elif not all([name, email, password, skills]):
                st.warning("Please fill all required (*) fields.")
            elif len(password) < 6:
                st.warning("Password must be at least 6 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                ok, result = register_user(name, email, password, skills, exp, bio, portfolio)
                if ok:
                    st.session_state.user = result
                    st.session_state.prev_pages = []
                    st.success("Account created! Welcome to CollabSkill AI 🎉")
                    st.balloons()
                    go("admin_dashboard" if result["role"] == "admin" else "dashboard")
                else:
                    st.error(result)

    st.markdown("<div style='margin-top:12px;color:#475569;font-size:13px;'>Already have an account?</div>", unsafe_allow_html=True)
    if st.button("Login"):
        go("login")


# ═══════════════════════════════════════════════════════════════
#  PAGE: USER DASHBOARD  (personal only — NO global data)
# ═══════════════════════════════════════════════════════════════
def page_dashboard():
    require_login()
    if is_admin():
        go("admin_dashboard")
        return

    u = st.session_state.user
    render_navbar()
    breadcrumb("Home", "Dashboard")

    st.markdown(f"<div class='page-title'>Hello, {u['name'].split()[0]}! 👋</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Your personal workspace — only your tasks and activity</div>", unsafe_allow_html=True)

    # Personal stats only
    my_tasks = get_my_tasks(u["id"])
    my_apps  = get_my_applications(u["id"])
    open_cnt = sum(1 for t in my_tasks if t["status"] == "open")

    # Refresh user for latest trust score
    fresh = get_user(u["id"]) or u
    st.session_state.user = fresh

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("📋 My Tasks",     len(my_tasks))
    m2.metric("🟢 Open Tasks",   open_cnt)
    m3.metric("📩 Applications", len(my_apps))
    m4.metric("⭐ Trust Score",  f"{fresh['trust_score']}/10")
    m5.metric("📊 Ratings",      fresh["total_ratings"])

    # Profile banner
    st.markdown("<br>", unsafe_allow_html=True)
    pc1, pc2 = st.columns([4, 1])
    with pc1:
        st.markdown(f"""
        <div class='cs-card' style='display:flex;align-items:center;gap:18px;'>
            {avatar(fresh['name'], 56)}
            <div style='flex:1;'>
                <div style='font-size:17px;font-weight:800;color:#f1f5f9;'>{fresh['name']}</div>
                <div style='color:#475569;font-size:13px;margin-top:2px;'>{fresh['skills'] or 'No skills added yet'}</div>
                <div style='color:#64748b;font-size:12px;margin-top:2px;'>{fresh['experience']} · {fresh['email']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with pc2:
        if st.button("✏️ Edit Profile", use_container_width=True):
            go("profile")

    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs: My Tasks / My Applications
    tab1, tab2, tab3 = st.tabs(["📋 My Tasks", "📩 My Applications", "⚡ Quick Actions"])

    with tab1:
        if not my_tasks:
            empty_state("📭", "No tasks yet", "Post your first task to start finding collaborators.")
            if st.button("➕ Post a Task", key="dash_post"):
                go("post_task")
        else:
            for t in my_tasks:
                with st.expander(f"📌 {t['title']}  [{t['status'].upper()}]"):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(f"""
                        <div style='color:#94a3b8;font-size:13px;line-height:1.7;'>{t['description']}</div>
                        <div style='margin-top:8px;'>
                            {status_badge(t['status'])} {priority_badge(t['priority'])}
                            <span class='cs-badge cs-badge-violet'>{t['category']}</span>
                            <span class='cs-badge cs-badge-cyan'>🛠 {t['skills']}</span>
                            <span class='cs-badge cs-badge-slate'>👥 {t['applicant_count']} applicants</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with c2:
                        if t["status"] == "open":
                            if st.button("✅ Close", key=f"cls_{t['id']}"):
                                update_task_status(t["id"], "closed")
                                st.rerun()
                        else:
                            if st.button("🔄 Reopen", key=f"opn_{t['id']}"):
                                update_task_status(t["id"], "open")
                                st.rerun()
                        if st.button("🗑 Delete", key=f"del_{t['id']}"):
                            delete_task(t["id"])
                            st.success("Task deleted.")
                            st.rerun()

    with tab2:
        if not my_apps:
            empty_state("📩", "No applications yet", "Browse tasks and apply to help others.")
            if st.button("🔍 Browse Tasks", key="dash_browse"):
                go("browse_tasks")
        else:
            for a in my_apps:
                st.markdown(f"""
                <div class='cs-card'>
                    <div style='font-weight:600;color:#f1f5f9;'>{a['task_title']}</div>
                    <div style='margin-top:6px;'>
                        {status_badge(a['status'])}
                        <span class='cs-badge cs-badge-violet'>{a['category']}</span>
                        <span class='cs-badge cs-badge-cyan'>🛠 {a['task_skills']}</span>
                        <span class='cs-badge cs-badge-slate'>👤 Owner: {a['owner_name']}</span>
                    </div>
                    <div style='color:#475569;font-size:11px;margin-top:6px;'>Applied: {a['created_at']}</div>
                </div>
                """, unsafe_allow_html=True)

    with tab3:
        qa1, qa2, qa3, qa4 = st.columns(4)
        with qa1:
            if st.button("➕ Post a Task",    use_container_width=True): go("post_task")
        with qa2:
            if st.button("🔍 Browse Tasks",   use_container_width=True): go("browse_tasks")
        with qa3:
            if st.button("🤖 AI Match",       use_container_width=True): go("ai_match")
        with qa4:
            if st.button("👥 Community",      use_container_width=True): go("community")


# ═══════════════════════════════════════════════════════════════
#  PAGE: BROWSE TASKS  (public — open tasks only)
# ═══════════════════════════════════════════════════════════════
def page_browse_tasks():
    render_navbar()
    breadcrumb("Home", "Browse Tasks")
    back_button()

    st.markdown("<div class='page-title'>🔍 Browse Tasks</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Find tasks that match your skills and start collaborating</div>", unsafe_allow_html=True)

    # Filters
    fc1, fc2, fc3, fc4 = st.columns([3, 1.5, 1.5, 1.5])
    with fc1: search   = st.text_input("", placeholder="🔍  Search tasks…", label_visibility="collapsed")
    with fc2: category = st.selectbox("", ["All"] + CATEGORIES,          label_visibility="collapsed")
    with fc3: sort_by  = st.selectbox("", ["newest", "oldest", "priority"], label_visibility="collapsed")
    with fc4:
        if is_logged_in():
            if st.button("➕ Post a Task", use_container_width=True): go("post_task")

    tasks = get_all_open_tasks(search, category, sort_by)
    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:12px;'>{len(tasks)} task(s) found</div>", unsafe_allow_html=True)

    if not tasks:
        empty_state("📭", "No tasks found", "Try a different search or be the first to post one!")
        return

    for t in tasks:
        with st.expander(f"📌  {t['title']}  —  by {t['creator_name']}  [{t['category']}]"):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"""
                <div style='color:#94a3b8;font-size:13px;line-height:1.7;margin-bottom:10px;'>{t['description']}</div>
                {status_badge(t['status'])} {priority_badge(t['priority'])}
                <span class='cs-badge cs-badge-violet'>{t['category']}</span>
                <span class='cs-badge cs-badge-cyan'>🛠 {t['skills']}</span>
                {'<span class="cs-badge cs-badge-slate">⏰ ' + t['deadline'] + '</span>' if t.get('deadline') else ''}
                <span class='cs-badge cs-badge-slate'>👤 {t['creator_name']}</span>
                <span class='cs-badge cs-badge-slate'>⭐ {t['creator_trust']}/10</span>
                <span class='cs-badge cs-badge-slate'>👥 {t['applicant_count']} applicants</span>
                <div style='color:#334155;font-size:11px;margin-top:8px;'>Posted: {t['created_at']}</div>
                """, unsafe_allow_html=True)
            with c2:
                if is_logged_in() and st.session_state.user["id"] != t["created_by"]:
                    if st.button("🙋 I Can Help!", key=f"apply_{t['id']}"):
                        ok, msg = apply_to_task(t["id"], st.session_state.user["id"])
                        if ok:
                            add_notification(t["created_by"], "New Application! 🙋",
                                             f"{st.session_state.user['name']} applied to: \"{t['title']}\"")
                            st.success(msg)
                        else:
                            st.warning(msg)
                elif not is_logged_in():
                    if st.button("Login to Apply", key=f"la_{t['id']}"):
                        go("login")


# ═══════════════════════════════════════════════════════════════
#  PAGE: POST TASK
# ═══════════════════════════════════════════════════════════════
def page_post_task():
    require_login()
    render_navbar()
    breadcrumb("Home", "Dashboard", "Post a Task")
    back_button()

    st.markdown("<div class='page-title'>📋 Post a Task</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Describe what you need and find the perfect collaborator</div>", unsafe_allow_html=True)

    c_form, c_tip = st.columns([2, 1])

    with c_form:
        with st.form("post_task_form"):
            title       = st.text_input("Task Title *",       placeholder="e.g. Need a React developer for a dashboard")
            description = st.text_area("Description *",       placeholder="Describe the task in detail…", height=140)
            sk1, sk2 = st.columns(2)
            with sk1:
                skills   = st.text_input("Required Skills *", placeholder="e.g. React, TailwindCSS, Figma")
                deadline = st.text_input("Deadline",          placeholder="e.g. Within 1 week")
            with sk2:
                category = st.selectbox("Category",           CATEGORIES)
                priority = st.selectbox("Priority",           ["Normal", "Urgent", "Low"])

            submitted = st.form_submit_button("🚀 Post Task", use_container_width=True)

            if submitted:
                if not all([title, description, skills]):
                    st.warning("Please fill Title, Description and Skills.")
                else:
                    create_task(title, description, skills, category, deadline, priority, st.session_state.user["id"])
                    st.success("✅ Task posted! Others can now find and apply.")
                    st.balloons()
                    go("dashboard")

    with c_tip:
        st.markdown("""
        <div class='cs-card'>
            <div style='color:#22d3ee;font-weight:700;font-size:14px;margin-bottom:12px;'>💡 Tips for a Great Post</div>
            <div style='color:#64748b;font-size:13px;line-height:2;'>
            ✅ Be specific about what you need<br>
            ✅ List exact skills required<br>
            ✅ Set a realistic deadline<br>
            ✅ Describe expected output<br>
            ✅ Choose the right category
            </div>
        </div>
        """, unsafe_allow_html=True)

        my_tasks = get_my_tasks(st.session_state.user["id"])
        if my_tasks:
            st.markdown("<div style='color:#94a3b8;font-size:13px;font-weight:600;margin-bottom:8px;'>📌 My Recent Posts</div>", unsafe_allow_html=True)
            for t in my_tasks[:4]:
                dot = "🟢" if t["status"] == "open" else "🔴"
                st.markdown(f"<div style='color:#64748b;font-size:12px;padding:6px 0;border-bottom:1px solid #1e293b;'>{dot} {t['title']}</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE: PROFILE
# ═══════════════════════════════════════════════════════════════
def page_profile():
    require_login()
    render_navbar()
    breadcrumb("Home", "Dashboard", "Profile")
    back_button()

    # Always get fresh user
    u = get_user(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = u

    st.markdown("<div class='page-title'>👤 My Profile</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Your public profile and reputation</div>", unsafe_allow_html=True)

    sidebar, main = st.columns([1, 2])

    with sidebar:
        trust_pct = int((u["trust_score"] / 10) * 100)
        st.markdown(f"""
        <div class='cs-card' style='text-align:center;'>
            {avatar(u['name'], 72).replace('display:flex;','display:flex;margin:0 auto 16px;')}
            <div style='font-size:20px;font-weight:800;color:#f1f5f9;margin-bottom:4px;'>{u['name']}</div>
            <div style='color:#475569;font-size:13px;'>{u['email']}</div>
            <div style='margin:10px 0;'>
                <span class='cs-badge cs-badge-violet'>{u['experience']}</span>
                {'<span class="cs-badge cs-badge-cyan">Admin</span>' if u["role"]=="admin" else ''}
            </div>
            <div style='color:#94a3b8;font-size:13px;line-height:1.6;'>{u['bio'] or 'No bio added yet.'}</div>
            <div style='margin-top:12px;'>
                {'<a href="' + u["portfolio"] + '" target="_blank" style="color:#22d3ee;font-size:13px;">🔗 Portfolio / GitHub</a>' if u.get("portfolio") else '<span style="color:#475569;font-size:13px;">No portfolio link</span>'}
            </div>
            <div style='margin-top:14px;'>
                <div style='display:flex;justify-content:space-between;color:#475569;font-size:11px;margin-bottom:4px;'>
                    <span>Trust Score</span><span>{u['trust_score']}/10</span>
                </div>
                {trust_bar(u['trust_score'])}
                <div style='color:#475569;font-size:11px;margin-top:4px;'>{u['total_ratings']} ratings received</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Skills
        if u.get("skills"):
            st.markdown("<div class='cs-card' style='margin-top:0;'>", unsafe_allow_html=True)
            st.markdown("<div style='color:#94a3b8;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;'>MY SKILLS</div>", unsafe_allow_html=True)
            st.markdown("".join([f"<span class='cs-badge cs-badge-cyan'>{s.strip()}</span>" for s in u["skills"].split(",") if s.strip()]), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with main:
        tab1, tab2, tab3, tab4 = st.tabs(["✏️ Edit Profile", "📋 My Tasks", "⭐ Feedback", "🌟 Give Feedback"])

        with tab1:
            with st.form("edit_profile"):
                n_name  = st.text_input("Full Name",         value=u["name"])
                n_skills= st.text_input("Skills",            value=u["skills"] or "")
                n_exp   = st.selectbox("Experience",         ["Beginner", "Intermediate", "Advanced", "Expert"],
                                       index=["Beginner","Intermediate","Advanced","Expert"].index(u["experience"]) if u["experience"] in ["Beginner","Intermediate","Advanced","Expert"] else 0)
                n_port  = st.text_input("Portfolio Link",    value=u["portfolio"] or "")
                n_bio   = st.text_area("Bio",                value=u["bio"] or "", height=90)
                if st.form_submit_button("Save Changes ✅", use_container_width=True):
                    update_profile(u["id"], n_name, n_skills, n_exp, n_bio, n_port)
                    fresh = get_user(u["id"])
                    st.session_state.user = fresh
                    st.success("Profile updated!")
                    st.rerun()

        with tab2:
            my_tasks = get_my_tasks(u["id"])
            if not my_tasks:
                empty_state("📭", "No tasks posted yet")
            for t in my_tasks:
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='display:flex;justify-content:space-between;'>
                        <div style='color:#f1f5f9;font-weight:600;'>{t['title']}</div>
                        <div>{status_badge(t['status'])}</div>
                    </div>
                    <div style='margin-top:6px;'>
                        <span class='cs-badge cs-badge-cyan'>🛠 {t['skills']}</span>
                        <span class='cs-badge cs-badge-violet'>{t['category']}</span>
                    </div>
                    <div style='color:#475569;font-size:11px;margin-top:6px;'>{t['created_at']}</div>
                </div>
                """, unsafe_allow_html=True)

        with tab3:
            fbs = get_feedback_for_user(u["id"])
            if not fbs:
                empty_state("⭐", "No feedback received yet")
            else:
                avg = round(sum(f["rating"] for f in fbs) / len(fbs), 1)
                st.markdown(f"""
                <div class='cs-card' style='text-align:center;padding:20px;margin-bottom:14px;'>
                    <div style='color:#f59e0b;font-size:28px;'>{"⭐" * round(avg)}</div>
                    <div style='color:#f1f5f9;font-size:22px;font-weight:800;'>{avg} / 5</div>
                    <div style='color:#475569;font-size:13px;'>Average from {len(fbs)} reviews</div>
                </div>
                """, unsafe_allow_html=True)
                for f in fbs:
                    st.markdown(f"""
                    <div class='cs-card' style='padding:14px;'>
                        <div style='display:flex;justify-content:space-between;'>
                            <div style='color:#f1f5f9;font-weight:600;'>👤 {f['from_name']}</div>
                            <div>{"⭐"*f['rating']}</div>
                        </div>
                        <div style='color:#64748b;font-size:13px;margin-top:6px;'>{f['comment'] or 'No comment.'}</div>
                        <div style='color:#334155;font-size:11px;margin-top:4px;'>{f['created_at']}</div>
                    </div>
                    """, unsafe_allow_html=True)

        with tab4:
            all_users = db_fetchall(
                "SELECT id, name, skills, trust_score FROM users WHERE id!=? AND is_active=1 AND role='user'",
                (u["id"],))
            if not all_users:
                empty_state("👥", "No other users yet")
            else:
                to_user  = st.selectbox("Select a collaborator to rate",
                                        [f"{x['name']} ({x['skills']})" for x in all_users])
                idx      = [f"{x['name']} ({x['skills']})" for x in all_users].index(to_user)
                to_id    = all_users[idx]["id"]
                rating   = st.slider("Rating (1–5)", 1, 5, 4)
                st.markdown(f"<div style='font-size:24px;'>{'⭐'*rating}</div>", unsafe_allow_html=True)
                comment  = st.text_area("Comment (optional)", placeholder="Share your experience…")
                if st.button("Submit Feedback ✅", use_container_width=True):
                    ok, msg = submit_feedback(u["id"], to_id, rating, comment)
                    if ok:
                        update_trust_score(to_id, rating)
                        add_notification(to_id, "New Rating! ⭐", f"{u['name']} gave you {rating}/5 stars.")
                        st.success(msg)
                        st.balloons()
                    else:
                        st.warning(msg)


# ═══════════════════════════════════════════════════════════════
#  PAGE: AI MATCH
# ═══════════════════════════════════════════════════════════════
def page_ai_match():
    require_login()
    render_navbar()
    breadcrumb("Home", "AI Skill Matching")
    back_button()

    st.markdown("<div class='page-title'>🤖 AI Skill Matching</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Describe your task and let AI find the perfect collaborators</div>", unsafe_allow_html=True)

    left, right = st.columns([3, 2])

    with left:
        with st.form("ai_form"):
            title  = st.text_input("Task Title",  placeholder="e.g. Build a data dashboard in Python")
            desc   = st.text_area("Description",  placeholder="Describe what you need…", height=120)
            skills = st.text_input("Skills Needed", placeholder="e.g. Python, Plotly, Pandas")
            run    = st.form_submit_button("🤖 Find Best Matches", use_container_width=True)

        if run:
            if not all([title, desc, skills]):
                st.warning("Please fill all three fields.")
            else:
                with st.spinner("🤖 AI is analyzing all profiles…"):
                    try:
                        from ai_matching import match_users_to_task
                        matches = match_users_to_task(title, desc, skills, st.session_state.user["id"])
                        st.session_state.ai_matches  = matches
                        st.session_state.ai_searched = True
                    except Exception as e:
                        st.error(f"AI Error: {e}")
                        st.session_state.ai_searched = False

    with right:
        st.markdown("""
        <div class='cs-card'>
            <div style='color:#22d3ee;font-weight:700;font-size:14px;margin-bottom:12px;'>⚡ How AI Matching Works</div>
            <div style='color:#64748b;font-size:13px;line-height:2;'>
            1️⃣ Describe your task clearly<br>
            2️⃣ AI reads ALL user profiles<br>
            3️⃣ Compares skills & experience<br>
            4️⃣ Factors in trust scores<br>
            5️⃣ Returns top 3 best matches<br>
            6️⃣ Notify them and collaborate!
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.ai_searched:
        if st.session_state.ai_matches:
            st.markdown(f"<br><div style='color:#22d3ee;font-weight:700;font-size:18px;margin-bottom:14px;'>✅ Top {len(st.session_state.ai_matches)} Matches Found</div>", unsafe_allow_html=True)

            for i, m in enumerate(st.session_state.ai_matches, 1):
                score = m.get("match_score", 0)
                score_color = "#22d3ee" if score >= 80 else "#f59e0b" if score >= 60 else "#f87171"
                medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else "👤"

                # Fetch full user data
                u_row = db_fetchone("SELECT * FROM users WHERE name=?", (m["name"],))
                u_skills  = u_row["skills"]     if u_row else "N/A"
                u_exp     = u_row["experience"] if u_row else "N/A"
                u_trust   = u_row["trust_score"] if u_row else 0
                u_port    = u_row["portfolio"]  if u_row else ""

                mc1, mc2 = st.columns([4, 1])
                with mc1:
                    st.markdown(f"""
                    <div class='match-card'>
                        <div style='font-size:20px;font-weight:800;color:#f1f5f9;margin-bottom:8px;'>{medal} {m['name']}</div>
                        <div style='margin-bottom:10px;'>
                            <span class='cs-badge cs-badge-cyan'>🛠 {u_skills}</span>
                            <span class='cs-badge cs-badge-violet'>{u_exp}</span>
                        </div>
                        <div style='color:#64748b;font-size:13px;line-height:1.6;'>{m.get('reason','')}</div>
                        {'<div style="margin-top:10px;"><a href="' + u_port + '" target="_blank" style="color:#22d3ee;font-size:12px;">🔗 View Portfolio</a></div>' if u_port else ''}
                    </div>
                    """, unsafe_allow_html=True)
                with mc2:
                    st.markdown(f"""
                    <div style='text-align:center;padding:12px;'>
                        <div style='color:{score_color};font-size:32px;font-weight:900;line-height:1;'>{score}%</div>
                        <div style='color:#334155;font-size:11px;margin-top:2px;'>Match</div>
                        <div style='color:#22d3ee;font-size:18px;font-weight:800;margin-top:10px;'>⭐ {u_trust}</div>
                        <div style='color:#334155;font-size:11px;'>Trust</div>
                    </div>
                    """, unsafe_allow_html=True)

                if u_row:
                    if st.button(f"📩 Notify {m['name']}", key=f"notify_{i}"):
                        add_notification(u_row["id"], "AI Matched You! 🤖",
                                         f"{st.session_state.user['name']} wants to collaborate with you!")
                        st.success(f"✅ {m['name']} has been notified!")
        else:
            st.warning("No matches found. Ask more people to register on the platform!")


# ═══════════════════════════════════════════════════════════════
#  PAGE: COMMUNITY
# ═══════════════════════════════════════════════════════════════
def page_community():
    require_login()
    render_navbar()
    breadcrumb("Home", "Community")
    back_button()

    st.markdown("<div class='page-title'>👥 Community</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Discover all members and explore their skills</div>", unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc1: search = st.text_input("", placeholder="🔍  Search members…", label_visibility="collapsed")
    with sc2:
        exp_filter = st.selectbox("", ["All Levels", "Beginner", "Intermediate", "Advanced", "Expert"],
                                  label_visibility="collapsed")

    where  = ["role='user'", "is_active=1", f"id != '{st.session_state.user['id']}'"]
    params = []
    if search:
        where.append("(name LIKE ? OR skills LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]
    if exp_filter != "All Levels":
        where.append("experience=?")
        params.append(exp_filter)

    users = db_fetchall(f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY trust_score DESC",
                        tuple(params))

    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:16px;'>{len(users)} member(s)</div>", unsafe_allow_html=True)

    if not users:
        empty_state("👥", "No members found", "Try a different search.")
        return

    exp_colors = {"Beginner": "cs-badge-cyan", "Intermediate": "cs-badge-violet",
                  "Advanced": "cs-badge-amber", "Expert": "cs-badge-red"}

    # 3 per row
    for row_start in range(0, len(users), 3):
        cols = st.columns(3)
        for col, u in zip(cols, users[row_start:row_start + 3]):
            trust_pct = int((u["trust_score"] / 10) * 100)
            col.markdown(f"""
            <div class='cs-card'>
                <div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>
                    {avatar(u['name'], 48)}
                    <div style='flex:1;min-width:0;'>
                        <div style='font-weight:700;color:#f1f5f9;font-size:14px;'>{u['name']}</div>
                        <span class='cs-badge {exp_colors.get(u["experience"],"cs-badge-slate")} ' style='font-size:10px;'>{u['experience']}</span>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:#22d3ee;font-weight:800;font-size:18px;'>{u['trust_score']}</div>
                        <div style='color:#334155;font-size:10px;'>trust</div>
                    </div>
                </div>
                <div style='color:#475569;font-size:12px;line-height:1.5;margin-bottom:10px;'>{(u['bio'] or 'No bio added.')[:80]}…</div>
                <div style='margin-bottom:10px;'>
                    {''.join([f"<span class='cs-badge cs-badge-cyan' style='font-size:10px;'>{s.strip()}</span>" for s in (u['skills'] or '').split(',')[:3] if s.strip()])}
                </div>
                {trust_bar(u['trust_score'])}
                <div style='color:#334155;font-size:10px;margin-top:4px;'>{u['total_ratings']} ratings</div>
                {'<div style="margin-top:10px;"><a href="' + u["portfolio"] + '" target="_blank" style="color:#22d3ee;font-size:12px;">🔗 Portfolio</a></div>' if u.get("portfolio") else ''}
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PAGE: NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════
def page_notifications():
    require_login()
    render_navbar()
    breadcrumb("Home", "Notifications")
    back_button()

    u = st.session_state.user
    mark_all_read(u["id"])

    st.markdown("<div class='page-title'>🔔 Notifications</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Your latest activity and alerts</div>", unsafe_allow_html=True)

    notifs = get_notifications(u["id"])
    if not notifs:
        empty_state("🔔", "No notifications yet", "Start collaborating to see activity here.")
        return

    for n in notifs:
        bg     = "#0d1f3c" if not n["is_read"] else "#0f172a"
        border = "#1e4080"  if not n["is_read"] else "#1e293b"
        dot    = "<span style='width:8px;height:8px;background:#22d3ee;border-radius:50%;display:inline-block;margin-left:6px;'></span>" if not n["is_read"] else ""
        st.markdown(f"""
        <div style='background:{bg};border:1px solid {border};border-radius:12px;padding:16px 20px;margin-bottom:10px;'>
            <div style='display:flex;justify-content:space-between;'>
                <div style='color:#e2e8f0;font-weight:600;font-size:14px;'>{n['title']}{dot}</div>
                <div style='color:#334155;font-size:11px;white-space:nowrap;margin-left:16px;'>{n['created_at'][:16]}</div>
            </div>
            <div style='color:#64748b;font-size:13px;margin-top:6px;line-height:1.5;'>{n['message']}</div>
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN PAGES  — all require admin role
# ═══════════════════════════════════════════════════════════════
def admin_sidebar():
    """Mini sidebar for admin navigation."""
    with st.sidebar:
        st.markdown("## 🛡️ Admin Panel")
        st.markdown(f"**{st.session_state.user['name']}**")
        st.markdown("---")
        if st.button("📊 Dashboard",  use_container_width=True): go("admin_dashboard")
        if st.button("👥 Users",      use_container_width=True): go("admin_users")
        if st.button("📋 All Tasks",  use_container_width=True): go("admin_tasks")
        if st.button("🌐 Browse",     use_container_width=True): go("browse_tasks")
        st.markdown("---")
        if st.button("🚪 Logout",     use_container_width=True):
            st.session_state.user = None
            go("landing")


# ── Admin Dashboard ───────────────────────────────────────────
def page_admin_dashboard():
    require_admin()
    render_navbar()
    admin_sidebar()
    breadcrumb("Home", "Admin Dashboard")

    st.markdown("""
    <div style='display:inline-flex;align-items:center;gap:10px;margin-bottom:20px;'>
        <div style='background:rgba(239,68,68,0.08);border:1px solid rgba(239,68,68,0.2);
            border-radius:8px;padding:4px 14px;font-size:11px;font-weight:700;color:#f87171;'>
            🛡️ ADMIN ONLY — This page is not visible to regular users
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='page-title'>📊 Admin Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Full platform analytics — visible only to you</div>", unsafe_allow_html=True)

    # ── Platform-wide stats (admin only) ──
    total_users  = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    total_admins = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE role='admin'")["c"]
    active_users = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE is_active=1")["c"]
    new_week     = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE created_at >= datetime('now','-7 days')")["c"]
    total_tasks  = db_fetchone("SELECT COUNT(*) AS c FROM tasks")["c"]
    open_tasks   = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open'")["c"]
    closed_tasks = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='closed'")["c"]
    total_apps   = db_fetchone("SELECT COUNT(*) AS c FROM applications")["c"]
    total_fb     = db_fetchone("SELECT COUNT(*) AS c FROM feedback")["c"]
    avg_trust    = db_fetchone("SELECT ROUND(AVG(trust_score),1) AS a FROM users")["a"] or 0

    st.markdown("### 👥 User Analytics")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Users",    total_users)
    m2.metric("Admins",         total_admins)
    m3.metric("Active Users",   active_users)
    m4.metric("New This Week",  new_week)

    st.markdown("### 📋 Task Analytics")
    t1, t2, t3, t4 = st.columns(4)
    t1.metric("Total Tasks",    total_tasks)
    t2.metric("Open",           open_tasks)
    t3.metric("Closed",         closed_tasks)
    t4.metric("Applications",   total_apps)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📁 Tasks by Category")
        cat_data = db_fetchall("SELECT category, COUNT(*) AS cnt FROM tasks GROUP BY category ORDER BY cnt DESC")
        if cat_data:
            df = pd.DataFrame(cat_data)
            df.columns = ["Category", "Count"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            empty_state("📁", "No tasks yet")

    with col2:
        st.markdown("### ⚡ Recent Activity")
        recent_u = db_fetchall("SELECT name, 'Registered' AS action, created_at FROM users ORDER BY created_at DESC LIMIT 5")
        recent_t = db_fetchall("SELECT title AS name, 'Task posted' AS action, created_at FROM tasks ORDER BY created_at DESC LIMIT 5")
        activity = sorted(recent_u + recent_t, key=lambda x: x["created_at"], reverse=True)[:8]
        for a in activity:
            dot_color = "#22d3ee" if a["action"] == "Registered" else "#a78bfa"
            st.markdown(f"""
            <div style='display:flex;align-items:flex-start;gap:10px;padding:8px 0;border-bottom:1px solid #1e293b;'>
                <div style='width:8px;height:8px;border-radius:50%;background:{dot_color};margin-top:5px;flex-shrink:0;'></div>
                <div>
                    <div style='color:#e2e8f0;font-size:13px;'>{a['action']}: <strong>{a['name']}</strong></div>
                    <div style='color:#334155;font-size:11px;'>{a['created_at'][:16]}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Leaderboard
    st.markdown("### 🏆 Top Users by Trust Score")
    top = get_top_users(8)
    medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣"]
    lc1, lc2 = st.columns(2)
    for i, u in enumerate(top):
        col = lc1 if i % 2 == 0 else lc2
        col.markdown(f"""
        <div class='cs-card' style='padding:14px;'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <div style='color:#f1f5f9;font-weight:600;font-size:13px;'>{medals[i]} {u['name']}</div>
                    <div style='color:#475569;font-size:11px;margin-top:2px;'>{u['skills']}</div>
                </div>
                <div style='text-align:right;'>
                    <div style='color:#22d3ee;font-weight:800;font-size:18px;'>{u['trust_score']}</div>
                    <div style='color:#334155;font-size:10px;'>{u['total_ratings']} ratings</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ── Admin Users page ──────────────────────────────────────────
def page_admin_users():
    require_admin()
    render_navbar()
    admin_sidebar()
    breadcrumb("Home", "Admin", "Manage Users")
    back_button()

    st.markdown("<div class='page-title'>👥 Manage Users</div>", unsafe_allow_html=True)

    sc1, sc2 = st.columns([3, 1])
    with sc1: search = st.text_input("", placeholder="🔍  Search users…", label_visibility="collapsed")
    with sc2: role_f = st.selectbox("", ["All", "user", "admin"], label_visibility="collapsed")

    where  = ["1=1"]
    params = []
    if search:
        where.append("(name LIKE ? OR email LIKE ? OR skills LIKE ?)")
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if role_f != "All":
        where.append("role=?")
        params.append(role_f)

    users = db_fetchall(f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY created_at DESC", tuple(params))
    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:16px;'>{len(users)} user(s)</div>", unsafe_allow_html=True)

    if not users:
        empty_state("👥", "No users found")
        return

    for u in users:
        with st.expander(f"👤 {u['name']}  [{u['role'].upper()}]  —  {u['email']}"):
            uc1, uc2, uc3 = st.columns([2, 2, 1])
            with uc1:
                st.markdown(f"""
                <div style='font-size:13px;color:#94a3b8;line-height:2;'>
                    <b style='color:#f1f5f9;'>Role:</b> {u['role']}<br>
                    <b style='color:#f1f5f9;'>Skills:</b> {u['skills'] or '—'}<br>
                    <b style='color:#f1f5f9;'>Experience:</b> {u['experience']}<br>
                    <b style='color:#f1f5f9;'>Trust Score:</b> {u['trust_score']}/10
                </div>
                """, unsafe_allow_html=True)
            with uc2:
                tc = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE created_by=?", (u["id"],))["c"]
                rc = db_fetchone("SELECT COUNT(*) AS c FROM feedback WHERE to_user_id=?", (u["id"],))["c"]
                st.markdown(f"""
                <div style='font-size:13px;color:#94a3b8;line-height:2;'>
                    <b style='color:#f1f5f9;'>Tasks Posted:</b> {tc}<br>
                    <b style='color:#f1f5f9;'>Ratings Received:</b> {rc}<br>
                    <b style='color:#f1f5f9;'>Status:</b> {'🟢 Active' if u['is_active'] else '🔴 Inactive'}<br>
                    <b style='color:#f1f5f9;'>Joined:</b> {u['created_at'][:10]}
                </div>
                """, unsafe_allow_html=True)
            with uc3:
                if u["role"] != "admin":
                    if u["is_active"]:
                        if st.button("🔴 Deactivate", key=f"deact_{u['id']}"):
                            db_execute("UPDATE users SET is_active=0 WHERE id=?", (u["id"],))
                            st.success("User deactivated.")
                            st.rerun()
                    else:
                        if st.button("🟢 Activate", key=f"act_{u['id']}"):
                            db_execute("UPDATE users SET is_active=1 WHERE id=?", (u["id"],))
                            st.success("User activated.")
                            st.rerun()
                else:
                    st.markdown("<div style='color:#475569;font-size:12px;'>Cannot modify admin</div>", unsafe_allow_html=True)


# ── Admin Tasks page ──────────────────────────────────────────
def page_admin_tasks():
    require_admin()
    render_navbar()
    admin_sidebar()
    breadcrumb("Home", "Admin", "Manage Tasks")
    back_button()

    st.markdown("<div class='page-title'>📋 Manage All Tasks</div>", unsafe_allow_html=True)

    sc1, sc2, sc3 = st.columns([3, 1.5, 1.5])
    with sc1: search    = st.text_input("", placeholder="🔍  Search tasks…", label_visibility="collapsed")
    with sc2: status_f  = st.selectbox("", ["All", "open", "closed", "in_progress"], label_visibility="collapsed")
    with sc3: cat_f     = st.selectbox("", ["All"] + CATEGORIES, label_visibility="collapsed")

    tasks = get_all_tasks_admin()

    # Filter
    if search:
        s = search.lower()
        tasks = [t for t in tasks if s in t["title"].lower() or s in t["description"].lower() or s in (t["skills"] or "").lower()]
    if status_f != "All":
        tasks = [t for t in tasks if t["status"] == status_f]
    if cat_f != "All":
        tasks = [t for t in tasks if t["category"] == cat_f]

    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:16px;'>{len(tasks)} task(s)</div>", unsafe_allow_html=True)

    if not tasks:
        empty_state("📋", "No tasks found")
        return

    for t in tasks:
        with st.expander(f"📌 {t['title']}  [{t['status'].upper()}]  —  by {t['creator_name']}"):
            tc1, tc2 = st.columns([3, 1])
            with tc1:
                st.markdown(f"""
                <div style='color:#94a3b8;font-size:13px;line-height:1.7;margin-bottom:10px;'>{t['description']}</div>
                {status_badge(t['status'])} {priority_badge(t['priority'])}
                <span class='cs-badge cs-badge-violet'>{t['category']}</span>
                <span class='cs-badge cs-badge-cyan'>🛠 {t['skills']}</span>
                <span class='cs-badge cs-badge-slate'>👥 {t['applicant_count']} applicants</span>
                <div style='color:#334155;font-size:11px;margin-top:8px;'>Posted: {t['created_at']}</div>
                """, unsafe_allow_html=True)
            with tc2:
                new_status = st.selectbox("Change Status", ["open","in_progress","closed"],
                                          index=["open","in_progress","closed"].index(t["status"]),
                                          key=f"adm_stat_{t['id']}")
                if st.button("Update Status", key=f"adm_upd_{t['id']}"):
                    update_task_status(t["id"], new_status)
                    st.success("Status updated.")
                    st.rerun()
                if st.button("🗑 Delete Task", key=f"adm_del_{t['id']}"):
                    delete_task(t["id"])
                    st.success("Task deleted by admin.")
                    st.rerun()


# ═══════════════════════════════════════════════════════════════
#  ROUTER  — maps page names to functions
# ═══════════════════════════════════════════════════════════════
PAGES = {
    "landing":          page_landing,
    "login":            page_login,
    "register":         page_register,
    "dashboard":        page_dashboard,
    "browse_tasks":     page_browse_tasks,
    "post_task":        page_post_task,
    "profile":          page_profile,
    "ai_match":         page_ai_match,
    "community":        page_community,
    "notifications":    page_notifications,
    "admin_dashboard":  page_admin_dashboard,
    "admin_users":      page_admin_users,
    "admin_tasks":      page_admin_tasks,
}

inject_css()

page_fn = PAGES.get(st.session_state.page, page_landing)
page_fn()
