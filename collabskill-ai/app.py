import streamlit as st
import pandas as pd
from database import init_db, db_fetchone, db_fetchall, db_execute
from auth import (register_user, login_user, get_user,
                  update_profile, update_trust_score, get_top_users)
from tasks_db import (
    create_task, get_all_open_tasks, get_my_tasks, get_all_tasks_admin,
    update_task_status, delete_task, apply_to_task,
    get_my_applications, get_applications_for_task,
    submit_feedback, get_feedback_for_user,
    add_notification, get_notifications,
    get_unread_count, mark_all_read, CATEGORIES,
)

init_db()

st.set_page_config(page_title="CollabSkill AI", page_icon="🚀", layout="wide")

for k, v in {
    "page": "landing", "user": None,
    "history": [], "ai_matches": [], "ai_done": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Navigation ────────────────────────────────────────────────
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


# ── CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
header,#MainMenu,footer{visibility:hidden;}
.block-container{padding-top:0rem;}
html,body,[class*="css"]{font-family:'Inter',sans-serif!important;background-color:#050816!important;}
.stApp{background-color:#050816;}
.stTextInput input,.stTextArea textarea{background-color:#1f2937!important;color:white!important;border:1px solid #374151!important;border-radius:10px!important;}
.stTextInput input:focus,.stTextArea textarea:focus{border-color:#22d3ee!important;box-shadow:0 0 0 2px rgba(34,211,238,.15)!important;}
label,.stTextInput label,.stTextArea label,.stSelectbox label,.stSlider label,.stCheckbox label{color:#fff!important;font-weight:500!important;}
input::placeholder{color:#9ca3af!important;}
.stSelectbox div{background-color:#1f2937!important;color:white!important;}
.stButton>button{background:linear-gradient(90deg,#22d3ee,#7c3aed)!important;color:white!important;border-radius:10px!important;border:none!important;font-weight:600!important;transition:opacity .2s!important;}
.stButton>button:hover{opacity:.85!important;}
[data-testid="metric-container"]{background-color:#0f172a!important;border:1px solid #1e293b!important;border-radius:12px!important;padding:16px!important;}
[data-testid="metric-container"] label{color:#64748b!important;font-size:12px!important;text-transform:uppercase!important;letter-spacing:.06em!important;}
[data-testid="stMetricValue"]{color:#22d3ee!important;font-size:26px!important;font-weight:800!important;}
.streamlit-expanderHeader{background-color:#0f172a!important;border:1px solid #1e293b!important;border-radius:10px!important;color:#e2e8f0!important;}
[data-testid="stSidebar"]{background-color:#070d1f!important;border-right:1px solid #1e293b!important;}
[data-testid="stSidebar"] *{color:#e2e8f0!important;}
.center{text-align:center;margin-top:60px;}
.light{color:#e5e7eb;font-size:72px;font-weight:900;line-height:1.1;}
.gradient{font-size:72px;font-weight:900;line-height:1.1;background:linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);-webkit-background-clip:text;color:transparent;}
.sub{color:#94a3b8;font-size:17px;text-align:center;margin-top:18px;}
.cs-card{background:#0f172a;border:1px solid #1e293b;border-radius:14px;padding:20px;margin-bottom:14px;}
.cs-badge{display:inline-block;padding:3px 10px;border-radius:20px;font-size:11px;font-weight:600;margin:2px 3px 2px 0;}
.badge-green{background:rgba(34,197,94,.1);color:#4ade80;border:1px solid rgba(34,197,94,.2);}
.badge-amber{background:rgba(245,158,11,.1);color:#fbbf24;border:1px solid rgba(245,158,11,.2);}
.badge-red{background:rgba(239,68,68,.1);color:#f87171;border:1px solid rgba(239,68,68,.2);}
.badge-cyan{background:rgba(34,211,238,.1);color:#22d3ee;border:1px solid rgba(34,211,238,.2);}
.badge-violet{background:rgba(124,58,237,.1);color:#a78bfa;border:1px solid rgba(124,58,237,.2);}
.badge-slate{background:#1e293b;color:#64748b;border:1px solid #334155;}
.page-title{font-size:26px;font-weight:900;color:#f1f5f9;letter-spacing:-.02em;margin-bottom:4px;}
.page-sub{color:#475569;font-size:14px;margin-bottom:20px;}
.trust-bar-bg{background:#1e293b;border-radius:4px;height:5px;margin-top:5px;}
.trust-bar-fill{height:5px;border-radius:4px;background:linear-gradient(90deg,#22d3ee,#7c3aed);}
.admin-only-banner{background:rgba(239,68,68,.07);border:1px solid rgba(239,68,68,.2);border-radius:10px;padding:10px 16px;color:#f87171;font-size:13px;margin-bottom:16px;}
</style>
""", unsafe_allow_html=True)


# ── UI Helpers ────────────────────────────────────────────────
def status_badge(s):
    c = {"open":"badge-green","in_progress":"badge-amber","closed":"badge-slate",
         "pending":"badge-amber","accepted":"badge-green","rejected":"badge-red"}.get(s,"badge-slate")
    return f"<span class='cs-badge {c}'>{s.replace('_',' ')}</span>"

def priority_badge(p):
    c = {"Urgent":"badge-red","Normal":"badge-cyan","Low":"badge-slate"}.get(p,"badge-slate")
    return f"<span class='cs-badge {c}'>{p}</span>"

def trust_bar(score):
    pct = int((score/10)*100)
    return f"<div class='trust-bar-bg'><div class='trust-bar-fill' style='width:{pct}%;'></div></div>"

def mk_avatar(name, size=40):
    ini = "".join(w[0].upper() for w in (name or "U").split()[:2])
    return (f"<div style='width:{size}px;height:{size}px;border-radius:50%;"
            f"background:linear-gradient(135deg,#22d3ee,#7c3aed);"
            f"display:inline-flex;align-items:center;justify-content:center;"
            f"font-size:{size//3}px;font-weight:700;color:#fff;'>{ini}</div>")

def empty_state(icon, title, desc=""):
    st.markdown(f"""<div class='cs-card' style='text-align:center;padding:44px;'>
        <div style='font-size:44px;margin-bottom:10px;'>{icon}</div>
        <div style='color:#f1f5f9;font-weight:700;font-size:15px;margin-bottom:5px;'>{title}</div>
        <div style='color:#475569;font-size:13px;'>{desc}</div></div>""",
        unsafe_allow_html=True)

def back_btn(label="← Back"):
    # key includes page name → always unique
    if st.button(label, key=f"back__{st.session_state.page}"):
        go_back()

def breadcrumb(*parts):
    html = " › ".join(
        f"<span style='color:#475569;'>{p}</span>" if i<len(parts)-1
        else f"<span style='color:#94a3b8;'>{p}</span>"
        for i,p in enumerate(parts))
    st.markdown(f"<div style='font-size:12px;margin-bottom:10px;'>{html}</div>",
                unsafe_allow_html=True)


# ── Navbar ────────────────────────────────────────────────────
def render_navbar():
    u = st.session_state.user
    unread = get_unread_count(u["id"]) if u else 0
    notif_lbl = f"🔔({unread})" if unread else "🔔"

    if is_admin():
        cols   = st.columns([2.5,1,1,1,1,1,1])
        labels = ["📊 Admin","👥 Users","📋 Tasks","🌐 Browse",notif_lbl,"👤 Profile","🚪 Out"]
        pages  = ["admin_dashboard","admin_users","admin_tasks","browse_tasks",
                  "notifications","profile","__logout__"]
    elif logged_in():
        cols   = st.columns([2.5,1,1,1,1,1,1])
        labels = ["🏠 Home","🗂 Dashboard","🔍 Tasks","➕ Post",notif_lbl,"👤 Profile","🚪 Out"]
        pages  = ["landing","dashboard","browse_tasks","post_task",
                  "notifications","profile","__logout__"]
    else:
        cols = st.columns([6,1,1])
        with cols[0]:
            st.markdown("<h3 style='color:#e5e7eb;padding-top:8px;margin:0;'>🚀 CollabSkill AI</h3>",
                        unsafe_allow_html=True)
        with cols[1]:
            # key = nav_login_guest → never clashes with login page button
            if st.button("Login", key="nav_login_guest"): go("login")
        with cols[2]:
            if st.button("Sign Up", key="nav_signup_guest"): go("register")
        st.markdown("<hr style='border-color:#1e293b;margin:6px 0 18px;'/>",
                    unsafe_allow_html=True)
        return

    admin_pill = (" <span style='font-size:10px;background:rgba(34,211,238,.1);"
                  "color:#22d3ee;border:1px solid rgba(34,211,238,.2);"
                  "border-radius:20px;padding:1px 9px;'>ADMIN</span>" if is_admin() else "")
    with cols[0]:
        st.markdown(f"<h3 style='color:#e5e7eb;padding-top:8px;margin:0;'>"
                    f"🚀 CollabSkill AI{admin_pill}</h3>", unsafe_allow_html=True)

    for col,lbl,pg in zip(cols[1:],labels,pages):
        with col:
            if st.button(lbl, key=f"nav__{pg}", use_container_width=True):
                if pg == "__logout__":
                    st.session_state.user = None
                    st.session_state.history = []
                    go("landing")
                else:
                    go(pg)

    st.markdown("<hr style='border-color:#1e293b;margin:6px 0 18px;'/>",
                unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  LANDING
# ═══════════════════════════════════════════════════════════════
def page_landing():
    render_navbar()
    st.markdown('<div class="center"><div class="light">Connect.<br>Collaborate.</div>'
                '<div class="gradient">Exchange Skills</div>'
                '<div class="gradient">Smarter.</div></div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">An intelligent platform that matches you with the right people — '
                'using AI to connect digital skill providers with those who need them instantly.</div>',
                unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    _,bc1,bc2,_ = st.columns([2,1,1,2])
    with bc1:
        if st.button("🚀 Get Started", key="land_start", use_container_width=True):
            go("register" if not logged_in() else ("admin_dashboard" if is_admin() else "dashboard"))
    with bc2:
        if st.button("🔍 Browse Tasks", key="land_browse", use_container_width=True):
            go("browse_tasks")

    st.markdown("<br>", unsafe_allow_html=True)
    total_users = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    total_tasks = db_fetchone("SELECT COUNT(*) AS c FROM tasks")["c"]
    open_tasks  = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open'")["c"]

    m1,m2,m3,m4 = st.columns(4)
    m1.metric("👥 Members",    total_users)
    m2.metric("📋 Tasks",      total_tasks)
    m3.metric("🟢 Open",       open_tasks)
    m4.metric("🎯 Match Rate", "98%")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='text-align:center;color:#475569;font-size:11px;font-weight:700;"
                "letter-spacing:.12em;text-transform:uppercase;margin-bottom:16px;'>WHAT WE OFFER</div>",
                unsafe_allow_html=True)

    f1,f2,f3,f4 = st.columns(4)
    feats = [
        ("🤖","rgba(34,211,238,.08)","AI Matching","Smart AI finds top 3 collaborators instantly."),
        ("🛡️","rgba(124,58,237,.08)","Trust Scores","Reputation from real peer feedback."),
        ("📋","rgba(34,197,94,.08)","Task Board","Post tasks, browse, filter by skill."),
        ("🌐","rgba(245,158,11,.08)","Community","Connect with creators worldwide."),
    ]
    for col,(icon,bg,title,desc) in zip([f1,f2,f3,f4],feats):
        col.markdown(f"""<div class='cs-card' style='text-align:center;min-height:160px;'>
            <div style='width:42px;height:42px;border-radius:11px;background:{bg};
                display:flex;align-items:center;justify-content:center;font-size:20px;margin:0 auto 12px;'>{icon}</div>
            <div style='color:#f1f5f9;font-weight:700;font-size:13px;margin-bottom:6px;'>{title}</div>
            <div style='color:#475569;font-size:12px;line-height:1.6;'>{desc}</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  LOGIN
# ═══════════════════════════════════════════════════════════════
def page_login():
    render_navbar()
    back_btn("← Home")

    _,center,_ = st.columns([1,2,1])
    with center:
        st.markdown("""<div style="background-color:#0f172a;padding:40px;
            border-radius:15px;box-shadow:0 0 30px rgba(0,0,0,.5);">""",
            unsafe_allow_html=True)
        st.markdown("<h2 style='color:#e5e7eb;text-align:center;'>Login</h2>",
                    unsafe_allow_html=True)

        # ── FIX Bug 1: unique keys with _lp_ prefix ───────────
        username = st.text_input("Username", key="lp_username")
        password = st.text_input("Password", type="password", key="lp_password")

        if st.button("Login →", key="lp_submit", use_container_width=True):
            if not username or not password:
                st.warning("Please fill both fields.")
            else:
                user = login_user(username, password)
                if user:
                    st.session_state.user    = user
                    st.session_state.history = []
                    st.success(f"Welcome back, {user['username']}! 👋")
                    go("admin_dashboard" if user["role"]=="admin" else "dashboard")
                else:
                    st.error("Invalid username or password.")

        st.markdown("<p style='color:#9ca3af;margin-top:12px;text-align:center;'>"
                    "Don't have an account?</p>", unsafe_allow_html=True)

        # ── FIX Bug 1: key lp_to_register (was "Login" = duplicate) ──
        if st.button("Create Account", key="lp_to_register", use_container_width=True):
            go("register")
        st.markdown("</div>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  REGISTER
# ═══════════════════════════════════════════════════════════════
def page_register():
    render_navbar()
    back_btn("← Home")

    st.markdown("<h1 style='color:#e5e7eb;'>Create Your Profile</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af;'>Join the skill exchange community</p>",
                unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        # ── FIX Bug 1: all keys prefixed with rp_ ─────────────
        username   = st.text_input("Username",                              key="rp_username")
        email      = st.text_input("Email",                                 key="rp_email")
        password   = st.text_input("Password", type="password",             key="rp_password")
    with col2:
        skills     = st.text_input("Skills (e.g. Python, UI Design)",       key="rp_skills")
        experience = st.selectbox("Experience Level",
                                  ["Beginner","Intermediate","Advanced","Expert"],
                                  key="rp_experience")
        portfolio  = st.text_input("Portfolio / GitHub Link (optional)",    key="rp_portfolio")

    bio   = st.text_area("Short Bio", key="rp_bio")
    agree = st.checkbox("I agree to Terms & Conditions", key="rp_agree")

    if st.button("Create Account", key="rp_submit", use_container_width=True):
        if not agree:
            st.warning("Please accept the Terms & Conditions.")
        elif not (username and email and password and skills):
            st.warning("Please fill all required fields.")
        elif len(password) < 6:
            st.warning("Password must be at least 6 characters.")
        else:
            success, result = register_user(
                username, email, password, skills, bio, portfolio, experience)
            if success:
                st.session_state.user    = result
                st.session_state.history = []
                st.success("Account created successfully 🎉")
                st.balloons()
                go("admin_dashboard" if result["role"]=="admin" else "dashboard")
            else:
                st.error(result)

    st.markdown("<p style='color:#9ca3af;margin-top:10px;'>Already have an account?</p>",
                unsafe_allow_html=True)
    # ── FIX Bug 1: was "Login" — same label as login page "Login" button ──
    if st.button("Go to Login", key="rp_to_login"):
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

    breadcrumb("Home","Dashboard")
    st.markdown(f"<div class='page-title'>Hello, {u['username']}! 👋</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Your personal workspace — only your tasks and activity</div>",
                unsafe_allow_html=True)

    my_tasks = get_my_tasks(u["id"])
    my_apps  = get_my_applications(u["id"])
    open_cnt = sum(1 for t in my_tasks if t["status"]=="open")

    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("📋 My Tasks",     len(my_tasks))
    m2.metric("🟢 Open",         open_cnt)
    m3.metric("📩 Applications", len(my_apps))
    m4.metric("⭐ Trust Score",  f"{u['trust_score']}/10")
    m5.metric("📊 Ratings",      u["total_ratings"])

    st.markdown("<br>", unsafe_allow_html=True)
    pc1,pc2 = st.columns([5,1])
    with pc1:
        st.markdown(f"""<div class='cs-card' style='display:flex;align-items:center;gap:16px;'>
            {mk_avatar(u['username'],54)}
            <div>
                <div style='font-size:16px;font-weight:800;color:#f1f5f9;'>{u['username']}</div>
                <div style='color:#475569;font-size:13px;margin-top:2px;'>{u['skills'] or 'No skills added'}</div>
                <div style='color:#64748b;font-size:12px;margin-top:1px;'>{u['experience']}</div>
            </div></div>""", unsafe_allow_html=True)
    with pc2:
        if st.button("✏️ Edit Profile", key="dash_edit", use_container_width=True):
            go("profile")

    st.markdown("<br>", unsafe_allow_html=True)
    tab1,tab2,tab3 = st.tabs(["📋 My Tasks","📩 My Applications","⚡ Quick Actions"])

    with tab1:
        if not my_tasks:
            empty_state("📭","No tasks yet","Post your first task to start finding collaborators.")
            if st.button("➕ Post a Task", key="dash_post"): go("post_task")
        else:
            for t in my_tasks:
                with st.expander(f"📌 {t['title']}  [{t['status'].upper()}]"):
                    c1,c2 = st.columns([3,1])
                    with c1:
                        st.markdown(f"""<div style='color:#94a3b8;font-size:13px;margin-bottom:8px;'>{t['description']}</div>
                            {status_badge(t['status'])} {priority_badge(t['priority'])}
                            <span class='cs-badge badge-violet'>{t['category']}</span>
                            <span class='cs-badge badge-cyan'>🛠 {t['skills']}</span>
                            <span class='cs-badge badge-slate'>👥 {t['applicant_count']} applicants</span>""",
                            unsafe_allow_html=True)
                    with c2:
                        if t["status"]=="open":
                            if st.button("✅ Close",  key=f"tc_{t['id']}"): update_task_status(t["id"],"closed"); st.rerun()
                        else:
                            if st.button("🔄 Reopen", key=f"to_{t['id']}"): update_task_status(t["id"],"open");   st.rerun()
                        if st.button("🗑 Delete", key=f"td_{t['id']}"): delete_task(t["id"]); st.success("Deleted."); st.rerun()

    with tab2:
        if not my_apps:
            empty_state("📩","No applications yet","Browse tasks and apply to help others.")
            if st.button("🔍 Browse Tasks", key="dash_browse"): go("browse_tasks")
        else:
            for a in my_apps:
                st.markdown(f"""<div class='cs-card' style='padding:14px;'>
                    <div style='font-weight:600;color:#f1f5f9;'>{a['task_title']}</div>
                    <div style='margin-top:6px;'>{status_badge(a['status'])}
                        <span class='cs-badge badge-violet'>{a['category']}</span>
                        <span class='cs-badge badge-cyan'>🛠 {a['task_skills']}</span>
                        <span class='cs-badge badge-slate'>👤 {a['owner_name']}</span>
                    </div>
                    <div style='color:#475569;font-size:11px;margin-top:5px;'>{a['created_at']}</div>
                </div>""", unsafe_allow_html=True)

    with tab3:
        q1,q2,q3,q4 = st.columns(4)
        with q1:
            if st.button("➕ Post a Task",  key="qa_post",      use_container_width=True): go("post_task")
        with q2:
            if st.button("🔍 Browse Tasks", key="qa_browse",    use_container_width=True): go("browse_tasks")
        with q3:
            if st.button("🤖 AI Match",     key="qa_ai",        use_container_width=True): go("ai_match")
        with q4:
            if st.button("👥 Community",    key="qa_community", use_container_width=True): go("community")


# ═══════════════════════════════════════════════════════════════
#  BROWSE TASKS
# ═══════════════════════════════════════════════════════════════
def page_browse_tasks():
    render_navbar()
    back_btn()
    breadcrumb("Home","Browse Tasks")
    st.markdown("<div class='page-title'>🔍 Browse Tasks</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Find tasks that match your skills</div>",
                unsafe_allow_html=True)

    fc1,fc2,fc3 = st.columns([3,1.5,1.5])
    with fc1: search   = st.text_input("", placeholder="🔍 Search…", key="br_search",   label_visibility="collapsed")
    with fc2: category = st.selectbox("", ["All"]+CATEGORIES,          key="br_cat",     label_visibility="collapsed")
    with fc3: sort_by  = st.selectbox("", ["newest","oldest","priority"],key="br_sort",  label_visibility="collapsed")

    if logged_in():
        if st.button("➕ Post a Task", key="br_post_btn"): go("post_task")

    tasks = get_all_open_tasks(search, category, sort_by)
    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:10px;'>{len(tasks)} task(s) found</div>",
                unsafe_allow_html=True)
    if not tasks:
        empty_state("📭","No tasks found","Try a different search or be the first to post one!"); return

    for t in tasks:
        with st.expander(f"📌  {t['title']}  —  by {t['creator_name']}  [{t['category']}]"):
            c1,c2 = st.columns([3,1])
            with c1:
                st.markdown(f"""<div style='color:#94a3b8;font-size:13px;line-height:1.7;margin-bottom:8px;'>{t['description']}</div>
                    {status_badge(t['status'])} {priority_badge(t['priority'])}
                    <span class='cs-badge badge-violet'>{t['category']}</span>
                    <span class='cs-badge badge-cyan'>🛠 {t['skills']}</span>
                    {'<span class="cs-badge badge-slate">⏰ '+t["deadline"]+'</span>' if t.get("deadline") else ''}
                    <span class='cs-badge badge-slate'>👤 {t['creator_name']}</span>
                    <span class='cs-badge badge-slate'>⭐ {t['creator_trust']}/10</span>
                    <span class='cs-badge badge-slate'>👥 {t['applicant_count']} applied</span>
                    <div style='color:#334155;font-size:11px;margin-top:6px;'>Posted: {t['created_at'][:10]}</div>""",
                    unsafe_allow_html=True)
            with c2:
                if logged_in() and st.session_state.user["id"]!=t["created_by"]:
                    if st.button("🙋 I Can Help!", key=f"apply_{t['id']}"):
                        ok,msg = apply_to_task(t["id"], st.session_state.user["id"])
                        if ok:
                            add_notification(t["created_by"],"New Application! 🙋",
                                f"{st.session_state.user['username']} applied to: \"{t['title']}\"")
                            st.success(msg)
                        else: st.warning(msg)
                elif not logged_in():
                    if st.button("Login to Apply", key=f"la_{t['id']}"): go("login")


# ═══════════════════════════════════════════════════════════════
#  POST TASK
# ═══════════════════════════════════════════════════════════════
def page_post_task():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home","Dashboard","Post a Task")
    st.markdown("<div class='page-title'>📋 Post a Task</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Describe what you need and find the perfect collaborator</div>",
                unsafe_allow_html=True)

    c_form, c_tip = st.columns([2,1])
    with c_form:
        with st.form("post_task_form"):
            title       = st.text_input("Task Title *", placeholder="e.g. Need a React developer")
            description = st.text_area("Description *", placeholder="Describe the task in detail…", height=130)
            sk1,sk2 = st.columns(2)
            with sk1:
                skills   = st.text_input("Required Skills *", placeholder="e.g. React, TailwindCSS")
                deadline = st.text_input("Deadline",           placeholder="e.g. Within 1 week")
            with sk2:
                category = st.selectbox("Category", CATEGORIES)
                priority = st.selectbox("Priority", ["Normal","Urgent","Low"])

            if st.form_submit_button("🚀 Post Task", use_container_width=True):
                if not all([title,description,skills]):
                    st.warning("Please fill Title, Description and Skills.")
                else:
                    create_task(title,description,skills,category,deadline,priority,
                                st.session_state.user["id"])
                    st.success("✅ Task posted successfully!")
                    st.balloons()
                    go("dashboard")

    with c_tip:
        st.markdown("""<div class='cs-card'>
            <div style='color:#22d3ee;font-weight:700;font-size:14px;margin-bottom:10px;'>💡 Tips</div>
            <div style='color:#64748b;font-size:13px;line-height:2;'>
            ✅ Be specific about what you need<br>✅ List exact skills<br>
            ✅ Set a realistic deadline<br>✅ Describe expected output<br>✅ Right category
            </div></div>""", unsafe_allow_html=True)
        recent = get_my_tasks(st.session_state.user["id"])[:4]
        if recent:
            st.markdown("<div style='color:#94a3b8;font-size:13px;font-weight:600;margin-bottom:8px;'>📌 My Recent Posts</div>",
                        unsafe_allow_html=True)
            for t in recent:
                dot = "🟢" if t["status"]=="open" else "🔴"
                st.markdown(f"<div style='color:#64748b;font-size:12px;padding:5px 0;border-bottom:1px solid #1e293b;'>{dot} {t['title']}</div>",
                            unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  PROFILE  — FIX Bug 2: split each HTML block into separate
#              st.markdown() calls so none renders as raw text
# ═══════════════════════════════════════════════════════════════
def page_profile():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home","Dashboard","Profile")

    u = get_user(st.session_state.user["id"]) or st.session_state.user
    st.session_state.user = u

    st.markdown("<div class='page-title'>👤 My Profile</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Your public profile and reputation</div>",
                unsafe_allow_html=True)

    sidebar, main = st.columns([1,2])

    with sidebar:
        # ── each block is its OWN st.markdown call ─────────────
        ini = "".join(w[0].upper() for w in (u["username"] or "U").split()[:2])
        st.markdown(f"""
        <div style='text-align:center;'>
            <div style='width:72px;height:72px;border-radius:50%;
                background:linear-gradient(135deg,#22d3ee,#7c3aed);
                display:inline-flex;align-items:center;justify-content:center;
                font-size:26px;font-weight:700;color:#fff;'>{ini}</div>
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='text-align:center;margin-top:10px;'>
            <div style='font-size:18px;font-weight:800;color:#f1f5f9;'>{u['username']}</div>
            <div style='color:#475569;font-size:12px;margin-top:3px;'>{u['email']}</div>
        </div>""", unsafe_allow_html=True)

        admin_b = '<span class="cs-badge badge-cyan">Admin</span>' if u["role"]=="admin" else ""
        st.markdown(f"""
        <div style='text-align:center;margin:10px 0;'>
            <span class='cs-badge badge-violet'>{u['experience']}</span>{admin_b}
        </div>""", unsafe_allow_html=True)

        st.markdown(f"""
        <div style='color:#94a3b8;font-size:13px;line-height:1.6;text-align:center;margin-bottom:10px;'>
            {u['bio'] or 'No bio added.'}
        </div>""", unsafe_allow_html=True)

        if u.get("portfolio"):
            st.markdown(f"""
            <div style='text-align:center;margin-bottom:10px;'>
                <a href='{u["portfolio"]}' target='_blank'
                    style='color:#22d3ee;font-size:13px;'>🔗 Portfolio</a>
            </div>""", unsafe_allow_html=True)

        trust_pct = int((u["trust_score"]/10)*100)
        st.markdown(f"""
        <div style='margin-bottom:6px;'>
            <div style='display:flex;justify-content:space-between;
                color:#475569;font-size:11px;margin-bottom:4px;'>
                <span>Trust Score</span><span>{u['trust_score']}/10</span>
            </div>
            <div class='trust-bar-bg'>
                <div class='trust-bar-fill' style='width:{trust_pct}%;'></div>
            </div>
            <div style='color:#475569;font-size:11px;margin-top:4px;'>
                {u['total_ratings']} ratings received
            </div>
        </div>""", unsafe_allow_html=True)

        if u.get("skills"):
            tags = "".join(
                f"<span class='cs-badge badge-cyan'>{s.strip()}</span>"
                for s in u["skills"].split(",") if s.strip())
            st.markdown(f"""
            <div style='margin-top:10px;border-top:1px solid #1e293b;padding-top:12px;'>
                <div style='color:#94a3b8;font-size:11px;font-weight:700;
                    text-transform:uppercase;letter-spacing:.08em;margin-bottom:8px;'>SKILLS</div>
                {tags}
            </div>""", unsafe_allow_html=True)

    with main:
        t1,t2,t3,t4 = st.tabs(["✏️ Edit Profile","📋 My Tasks","⭐ Feedback","🌟 Give Rating"])

        with t1:
            with st.form("edit_profile_form"):
                n_user = st.text_input("Username", value=u["username"])
                n_sk   = st.text_input("Skills",   value=u["skills"] or "")
                n_exp  = st.selectbox("Experience",
                    ["Beginner","Intermediate","Advanced","Expert"],
                    index=["Beginner","Intermediate","Advanced","Expert"].index(u["experience"])
                          if u["experience"] in ["Beginner","Intermediate","Advanced","Expert"] else 0)
                n_port = st.text_input("Portfolio", value=u["portfolio"] or "")
                n_bio  = st.text_area("Bio",        value=u["bio"] or "", height=90)
                if st.form_submit_button("Save Changes ✅", use_container_width=True):
                    update_profile(u["id"],n_user,n_sk,n_exp,n_bio,n_port)
                    fresh = get_user(u["id"])
                    st.session_state.user = fresh
                    st.success("Profile updated!")
                    st.rerun()

        with t2:
            my_tasks = get_my_tasks(u["id"])
            if not my_tasks: empty_state("📭","No tasks posted yet")
            for t in my_tasks:
                st.markdown(f"""<div class='cs-card' style='padding:12px;'>
                    <div style='display:flex;justify-content:space-between;'>
                        <div style='color:#f1f5f9;font-weight:600;'>{t['title']}</div>
                        {status_badge(t['status'])}
                    </div>
                    <div style='margin-top:5px;'>
                        <span class='cs-badge badge-cyan'>🛠 {t['skills']}</span>
                        <span class='cs-badge badge-violet'>{t['category']}</span>
                    </div>
                    <div style='color:#475569;font-size:11px;margin-top:4px;'>{t['created_at'][:10]}</div>
                </div>""", unsafe_allow_html=True)

        with t3:
            fbs = get_feedback_for_user(u["id"])
            if not fbs: empty_state("⭐","No feedback received yet")
            else:
                avg = round(sum(f["rating"] for f in fbs)/len(fbs),1)
                st.markdown(f"""<div class='cs-card' style='text-align:center;padding:18px;margin-bottom:12px;'>
                    <div style='color:#f59e0b;font-size:26px;'>{"⭐"*round(avg)}</div>
                    <div style='color:#f1f5f9;font-size:22px;font-weight:800;'>{avg}/5</div>
                    <div style='color:#475569;font-size:13px;'>from {len(fbs)} reviews</div>
                </div>""", unsafe_allow_html=True)
                for f in fbs:
                    st.markdown(f"""<div class='cs-card' style='padding:12px;'>
                        <div style='display:flex;justify-content:space-between;'>
                            <span style='color:#f1f5f9;font-weight:600;'>👤 {f['from_name']}</span>
                            <span>{"⭐"*f['rating']}</span>
                        </div>
                        <div style='color:#64748b;font-size:13px;margin-top:5px;'>{f['comment'] or '—'}</div>
                        <div style='color:#334155;font-size:11px;margin-top:4px;'>{f['created_at'][:10]}</div>
                    </div>""", unsafe_allow_html=True)

        with t4:
            others = db_fetchall(
                "SELECT id,username,skills,trust_score FROM users "
                "WHERE id!=? AND is_active=1 AND role='user'", (u["id"],))
            if not others: empty_state("👥","No other users yet")
            else:
                opts   = [f"{x['username']} ({x['skills'] or 'no skills'})" for x in others]
                chosen = st.selectbox("Select a collaborator to rate", opts, key="gr_select")
                to_id  = others[opts.index(chosen)]["id"]
                rating = st.slider("Rating (1–5)",1,5,4,key="gr_slider")
                st.markdown(f"<div style='font-size:22px;'>{'⭐'*rating}</div>",
                            unsafe_allow_html=True)
                comment = st.text_area("Comment (optional)", key="gr_comment")
                if st.button("Submit Feedback ✅", key="gr_submit", use_container_width=True):
                    ok,msg = submit_feedback(u["id"],to_id,rating,comment)
                    if ok:
                        update_trust_score(to_id,rating)
                        add_notification(to_id,"New Rating! ⭐",
                                         f"{u['username']} gave you {rating}/5 stars.")
                        st.success(msg); st.balloons()
                    else: st.warning(msg)


# ═══════════════════════════════════════════════════════════════
#  AI MATCH  — FIX Bug 3: lazy client, friendly error message
# ═══════════════════════════════════════════════════════════════
def page_ai_match():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home","AI Skill Matching")
    st.markdown("<div class='page-title'>🤖 AI Skill Matching</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Let AI find the best collaborators for your task</div>",
                unsafe_allow_html=True)

    left, right = st.columns([3,2])
    with left:
        with st.form("ai_match_form"):
            ai_title  = st.text_input("Task Title",    placeholder="e.g. Build a data dashboard")
            ai_desc   = st.text_area("Description",    placeholder="Describe what you need…", height=110)
            ai_skills = st.text_input("Skills Needed", placeholder="e.g. Python, Plotly, Pandas")
            run = st.form_submit_button("🤖 Find Best Matches", use_container_width=True)

        if run:
            if not all([ai_title,ai_desc,ai_skills]):
                st.warning("Please fill all three fields.")
            else:
                with st.spinner("🤖 AI is analyzing all profiles…"):
                    try:
                        from ai_matching import match_users_to_task
                        matches = match_users_to_task(
                            ai_title,ai_desc,ai_skills,st.session_state.user["id"])
                        st.session_state.ai_matches = matches
                        st.session_state.ai_done    = True
                    except Exception as e:
                        st.session_state.ai_done = False
                        st.error(f"AI Error: {e}")
                        st.info(
                            "**To fix:** Go to Streamlit Cloud → Manage app → "
                            "Settings → Secrets and add:\n\n"
                            "`OPENAI_API_KEY = \"sk-proj-your-real-key\"`")

    with right:
        st.markdown("""<div class='cs-card'>
            <div style='color:#22d3ee;font-weight:700;font-size:14px;margin-bottom:10px;'>⚡ How it works</div>
            <div style='color:#64748b;font-size:13px;line-height:2;'>
            1️⃣ Describe your task<br>2️⃣ AI reads all user profiles<br>
            3️⃣ Compares skills &amp; experience<br>4️⃣ Factors in trust scores<br>
            5️⃣ Returns top 3 best matches<br>6️⃣ Notify them &amp; collaborate!
            </div></div>""", unsafe_allow_html=True)

    if st.session_state.ai_done and st.session_state.ai_matches:
        matches = st.session_state.ai_matches
        st.markdown(f"<br><div style='color:#22d3ee;font-weight:700;font-size:17px;"
                    f"margin-bottom:12px;'>✅ Top {len(matches)} Matches</div>",
                    unsafe_allow_html=True)
        medals = ["🥇","🥈","🥉"]
        for i,m in enumerate(matches,1):
            score = m.get("match_score",0)
            sc    = "#22d3ee" if score>=80 else "#f59e0b" if score>=60 else "#f87171"
            row   = db_fetchone("SELECT * FROM users WHERE username=?", (m["name"],))
            u_sk  = row["skills"]      if row else "N/A"
            u_exp = row["experience"]  if row else "N/A"
            u_tr  = row["trust_score"] if row else 0
            u_pt  = row["portfolio"]   if row else ""

            mc1,mc2 = st.columns([4,1])
            with mc1:
                st.markdown(f"""<div style='background:linear-gradient(135deg,#0f172a,#130f2a);
                    border:1px solid #312e81;border-radius:14px;padding:20px;margin-bottom:10px;'>
                    <div style='font-size:18px;font-weight:800;color:#f1f5f9;margin-bottom:7px;'>
                        {medals[i-1] if i<=3 else '👤'} {m['name']}</div>
                    <div style='margin-bottom:8px;'>
                        <span class='cs-badge badge-cyan'>🛠 {u_sk}</span>
                        <span class='cs-badge badge-violet'>{u_exp}</span>
                    </div>
                    <div style='color:#64748b;font-size:13px;line-height:1.6;'>{m.get('reason','')}</div>
                    {'<div style="margin-top:8px;"><a href="'+u_pt+'" target="_blank" style="color:#22d3ee;font-size:12px;">🔗 Portfolio</a></div>' if u_pt else ''}
                </div>""", unsafe_allow_html=True)
            with mc2:
                st.markdown(f"""<div style='text-align:center;padding:10px;'>
                    <div style='color:{sc};font-size:30px;font-weight:900;'>{score}%</div>
                    <div style='color:#334155;font-size:10px;'>Match</div>
                    <div style='color:#22d3ee;font-size:17px;font-weight:800;margin-top:8px;'>⭐ {u_tr}</div>
                    <div style='color:#334155;font-size:10px;'>Trust</div>
                </div>""", unsafe_allow_html=True)
            if row:
                if st.button(f"📩 Notify {m['name']}", key=f"notify_{i}"):
                    add_notification(row["id"],"AI Matched You! 🤖",
                        f"{st.session_state.user['username']} wants to collaborate!")
                    st.success(f"✅ {m['name']} notified!")

    elif st.session_state.ai_done and not st.session_state.ai_matches:
        st.warning("No matches found. Invite more people to register!")


# ═══════════════════════════════════════════════════════════════
#  COMMUNITY
# ═══════════════════════════════════════════════════════════════
def page_community():
    require_login()
    render_navbar()
    back_btn()
    breadcrumb("Home","Community")
    st.markdown("<div class='page-title'>👥 Community</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Discover all members and explore their skills</div>",
                unsafe_allow_html=True)

    sc1,sc2 = st.columns([3,1])
    with sc1: search = st.text_input("", placeholder="🔍 Search members…", key="cm_search", label_visibility="collapsed")
    with sc2: exp_f  = st.selectbox("", ["All Levels","Beginner","Intermediate","Advanced","Expert"], key="cm_exp", label_visibility="collapsed")

    uid = st.session_state.user["id"]
    where,params = ["role='user'","is_active=1",f"id!='{uid}'"], []
    if search:
        where.append("(username LIKE ? OR skills LIKE ?)")
        params += [f"%{search}%"]*2
    if exp_f != "All Levels":
        where.append("experience=?"); params.append(exp_f)

    users = db_fetchall(f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY trust_score DESC",
                        tuple(params))
    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:14px;'>{len(users)} member(s)</div>",
                unsafe_allow_html=True)
    if not users: empty_state("👥","No members found"); return

    exp_c = {"Beginner":"badge-cyan","Intermediate":"badge-violet","Advanced":"badge-amber","Expert":"badge-red"}
    for i in range(0,len(users),3):
        cols = st.columns(3)
        for col,u in zip(cols,users[i:i+3]):
            pct = int((u["trust_score"]/10)*100)
            ini = "".join(w[0].upper() for w in u["username"].split()[:2])
            skills_html = "".join(
                f"<span class='cs-badge badge-cyan' style='font-size:10px;'>{s.strip()}</span>"
                for s in (u["skills"] or "").split(",")[:3] if s.strip())
            port_html = (f'<div style="margin-top:8px;"><a href="{u["portfolio"]}" target="_blank" '
                         f'style="color:#22d3ee;font-size:12px;">🔗 Portfolio</a></div>'
                         if u.get("portfolio") else "")
            col.markdown(f"""<div class='cs-card'>
                <div style='display:flex;align-items:center;gap:10px;margin-bottom:10px;'>
                    <div style='width:44px;height:44px;border-radius:50%;
                        background:linear-gradient(135deg,#22d3ee,#7c3aed);
                        display:inline-flex;align-items:center;justify-content:center;
                        font-size:16px;font-weight:700;color:#fff;flex-shrink:0;'>{ini}</div>
                    <div style='flex:1;min-width:0;'>
                        <div style='font-weight:700;color:#f1f5f9;font-size:13px;'>{u['username']}</div>
                        <span class='cs-badge {exp_c.get(u["experience"],"badge-slate")}' style='font-size:9px;'>{u['experience']}</span>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:#22d3ee;font-weight:800;font-size:17px;'>{u['trust_score']}</div>
                        <div style='color:#334155;font-size:10px;'>trust</div>
                    </div>
                </div>
                <div style='color:#475569;font-size:12px;line-height:1.5;margin-bottom:8px;'>{(u['bio'] or 'No bio.')[:80]}…</div>
                <div>{skills_html}</div>
                <div class='trust-bar-bg'><div class='trust-bar-fill' style='width:{pct}%;'></div></div>
                <div style='color:#334155;font-size:10px;margin-top:3px;'>{u['total_ratings']} ratings</div>
                {port_html}
            </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════
def page_notifications():
    require_login()
    render_navbar()
    back_btn()
    mark_all_read(st.session_state.user["id"])
    st.markdown("<div class='page-title'>🔔 Notifications</div>", unsafe_allow_html=True)

    notifs = get_notifications(st.session_state.user["id"])
    if not notifs: empty_state("🔔","No notifications yet","Start collaborating to see activity here."); return

    for n in notifs:
        bg     = "#0d1f3c" if not n["is_read"] else "#0f172a"
        border = "#1e4080"  if not n["is_read"] else "#1e293b"
        dot    = " <span style='width:7px;height:7px;background:#22d3ee;border-radius:50%;display:inline-block;'></span>" if not n["is_read"] else ""
        st.markdown(f"""<div style='background:{bg};border:1px solid {border};border-radius:12px;
            padding:14px 18px;margin-bottom:8px;'>
            <div style='display:flex;justify-content:space-between;'>
                <div style='color:#e2e8f0;font-weight:600;font-size:13px;'>{n['title']}{dot}</div>
                <div style='color:#334155;font-size:11px;'>{n['created_at'][:16]}</div>
            </div>
            <div style='color:#64748b;font-size:13px;margin-top:5px;'>{n['message']}</div>
        </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN SIDEBAR
# ═══════════════════════════════════════════════════════════════
def admin_sidebar():
    with st.sidebar:
        st.markdown("## 🛡️ Admin Panel")
        st.markdown(f"**{st.session_state.user['username']}**")
        st.markdown("---")
        if st.button("📊 Dashboard", key="asb_dash",   use_container_width=True): go("admin_dashboard")
        if st.button("👥 Users",     key="asb_users",  use_container_width=True): go("admin_users")
        if st.button("📋 All Tasks", key="asb_tasks",  use_container_width=True): go("admin_tasks")
        if st.button("🌐 Browse",    key="asb_browse", use_container_width=True): go("browse_tasks")
        st.markdown("---")
        if st.button("🚪 Logout",   key="asb_logout",  use_container_width=True):
            st.session_state.user=None; go("landing")


# ═══════════════════════════════════════════════════════════════
#  ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════
def page_admin_dashboard():
    require_admin()
    render_navbar()
    admin_sidebar()
    breadcrumb("Admin","Dashboard")
    st.markdown("<div class='admin-only-banner'>🛡️ ADMIN ONLY — This data is NOT visible to regular users.</div>",
                unsafe_allow_html=True)
    st.markdown("<div class='page-title'>📊 Admin Dashboard</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Full platform analytics</div>", unsafe_allow_html=True)

    total_users  = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    total_admins = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE role='admin'")["c"]
    active_users = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE is_active=1")["c"]
    new_week     = db_fetchone("SELECT COUNT(*) AS c FROM users WHERE created_at>=datetime('now','-7 days')")["c"]
    total_tasks  = db_fetchone("SELECT COUNT(*) AS c FROM tasks")["c"]
    open_tasks   = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='open'")["c"]
    closed_tasks = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE status='closed'")["c"]
    total_apps   = db_fetchone("SELECT COUNT(*) AS c FROM applications")["c"]

    st.markdown("### 👥 Users")
    m1,m2,m3,m4 = st.columns(4)
    m1.metric("Total Users",total_users); m2.metric("Admins",total_admins)
    m3.metric("Active",active_users);     m4.metric("New This Week",new_week)

    st.markdown("### 📋 Tasks")
    t1,t2,t3,t4 = st.columns(4)
    t1.metric("Total Tasks",total_tasks); t2.metric("Open",open_tasks)
    t3.metric("Closed",closed_tasks);     t4.metric("Applications",total_apps)

    st.markdown("<br>", unsafe_allow_html=True)
    col1,col2 = st.columns(2)
    with col1:
        st.markdown("#### 📁 Tasks by Category")
        cat_data = db_fetchall("SELECT category,COUNT(*) AS cnt FROM tasks GROUP BY category ORDER BY cnt DESC")
        if cat_data:
            df = pd.DataFrame(cat_data); df.columns=["Category","Count"]
            st.dataframe(df,use_container_width=True,hide_index=True)
        else: empty_state("📁","No tasks yet")

    with col2:
        st.markdown("#### ⚡ Recent Activity")
        rec_u = db_fetchall("SELECT username AS name,'Joined' AS action,created_at FROM users ORDER BY created_at DESC LIMIT 5")
        rec_t = db_fetchall("SELECT title AS name,'Task posted' AS action,created_at FROM tasks ORDER BY created_at DESC LIMIT 5")
        activity = sorted(rec_u+rec_t, key=lambda x:x["created_at"], reverse=True)[:8]
        for a in activity:
            dot_c = "#22d3ee" if a["action"]=="Joined" else "#a78bfa"
            st.markdown(f"""<div style='display:flex;align-items:flex-start;gap:10px;
                padding:7px 0;border-bottom:1px solid #1e293b;'>
                <div style='width:7px;height:7px;border-radius:50%;background:{dot_c};margin-top:5px;flex-shrink:0;'></div>
                <div>
                    <div style='color:#e2e8f0;font-size:13px;'>{a['action']}: <b>{a['name']}</b></div>
                    <div style='color:#334155;font-size:11px;'>{a['created_at'][:16]}</div>
                </div></div>""", unsafe_allow_html=True)

    st.markdown("#### 🏆 Top Users by Trust Score")
    top=get_top_users(8); medals=["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣"]
    lc1,lc2 = st.columns(2)
    for i,u in enumerate(top):
        col = lc1 if i%2==0 else lc2
        col.markdown(f"""<div class='cs-card' style='padding:12px;'>
            <div style='display:flex;justify-content:space-between;align-items:center;'>
                <div>
                    <div style='color:#f1f5f9;font-weight:600;font-size:13px;'>{medals[i]} {u['username']}</div>
                    <div style='color:#475569;font-size:11px;'>{u['skills'] or '—'}</div>
                </div>
                <div style='text-align:right;'>
                    <div style='color:#22d3ee;font-weight:800;font-size:17px;'>{u['trust_score']}</div>
                    <div style='color:#334155;font-size:10px;'>{u['total_ratings']} ratings</div>
                </div>
            </div></div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════
#  ADMIN USERS
# ═══════════════════════════════════════════════════════════════
def page_admin_users():
    require_admin()
    render_navbar(); admin_sidebar()
    breadcrumb("Admin","Manage Users"); back_btn()
    st.markdown("<div class='page-title'>👥 Manage Users</div>", unsafe_allow_html=True)

    sc1,sc2 = st.columns([3,1])
    with sc1: search = st.text_input("", placeholder="🔍 Search…", key="au_search", label_visibility="collapsed")
    with sc2: role_f = st.selectbox("", ["All","user","admin"],      key="au_role",   label_visibility="collapsed")

    where,params = ["1=1"],[]
    if search: where.append("(username LIKE ? OR email LIKE ?)"); params+=[f"%{search}%"]*2
    if role_f!="All": where.append("role=?"); params.append(role_f)

    users = db_fetchall(f"SELECT * FROM users WHERE {' AND '.join(where)} ORDER BY created_at DESC", tuple(params))
    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:14px;'>{len(users)} user(s)</div>",
                unsafe_allow_html=True)

    for u in users:
        with st.expander(f"👤 {u['username']}  [{u['role'].upper()}]  —  {u['email']}"):
            c1,c2,c3 = st.columns([2,2,1])
            with c1:
                st.markdown(f"""<div style='font-size:13px;color:#94a3b8;line-height:2;'>
                    <b style='color:#f1f5f9;'>Role:</b> {u['role']}<br>
                    <b style='color:#f1f5f9;'>Skills:</b> {u['skills'] or '—'}<br>
                    <b style='color:#f1f5f9;'>Level:</b> {u['experience']}<br>
                    <b style='color:#f1f5f9;'>Trust:</b> {u['trust_score']}/10
                </div>""", unsafe_allow_html=True)
            with c2:
                tc = db_fetchone("SELECT COUNT(*) AS c FROM tasks WHERE created_by=?", (u["id"],))["c"]
                rc = db_fetchone("SELECT COUNT(*) AS c FROM feedback WHERE to_user_id=?", (u["id"],))["c"]
                st.markdown(f"""<div style='font-size:13px;color:#94a3b8;line-height:2;'>
                    <b style='color:#f1f5f9;'>Tasks:</b> {tc}<br>
                    <b style='color:#f1f5f9;'>Ratings received:</b> {rc}<br>
                    <b style='color:#f1f5f9;'>Status:</b> {'🟢 Active' if u['is_active'] else '🔴 Inactive'}<br>
                    <b style='color:#f1f5f9;'>Joined:</b> {u['created_at'][:10]}
                </div>""", unsafe_allow_html=True)
            with c3:
                if u["role"]!="admin":
                    if u["is_active"]:
                        if st.button("🔴 Deactivate", key=f"deact_{u['id']}"):
                            db_execute("UPDATE users SET is_active=0 WHERE id=?",(u["id"],)); st.success("Deactivated."); st.rerun()
                    else:
                        if st.button("🟢 Activate",   key=f"act_{u['id']}"):
                            db_execute("UPDATE users SET is_active=1 WHERE id=?",(u["id"],)); st.success("Activated.");   st.rerun()


# ═══════════════════════════════════════════════════════════════
#  ADMIN TASKS
# ═══════════════════════════════════════════════════════════════
def page_admin_tasks():
    require_admin()
    render_navbar(); admin_sidebar()
    breadcrumb("Admin","Manage Tasks"); back_btn()
    st.markdown("<div class='page-title'>📋 All Tasks</div>", unsafe_allow_html=True)

    sc1,sc2,sc3 = st.columns([3,1.5,1.5])
    with sc1: search   = st.text_input("", placeholder="🔍 Search…", key="at_search", label_visibility="collapsed")
    with sc2: status_f = st.selectbox("", ["All","open","closed","in_progress"], key="at_status", label_visibility="collapsed")
    with sc3: cat_f    = st.selectbox("", ["All"]+CATEGORIES,                    key="at_cat",    label_visibility="collapsed")

    tasks = get_all_tasks_admin()
    if search:
        s=search.lower()
        tasks=[t for t in tasks if s in t["title"].lower() or s in (t["skills"] or "").lower()]
    if status_f!="All": tasks=[t for t in tasks if t["status"]==status_f]
    if cat_f!="All":    tasks=[t for t in tasks if t["category"]==cat_f]

    st.markdown(f"<div style='color:#475569;font-size:13px;margin-bottom:14px;'>{len(tasks)} task(s)</div>",
                unsafe_allow_html=True)
    if not tasks: empty_state("📋","No tasks found"); return

    for t in tasks:
        with st.expander(f"📌 {t['title']}  [{t['status'].upper()}]  —  {t['creator_name']}"):
            tc1,tc2 = st.columns([3,1])
            with tc1:
                st.markdown(f"""<div style='color:#94a3b8;font-size:13px;line-height:1.7;margin-bottom:8px;'>{t['description']}</div>
                    {status_badge(t['status'])} {priority_badge(t['priority'])}
                    <span class='cs-badge badge-violet'>{t['category']}</span>
                    <span class='cs-badge badge-cyan'>🛠 {t['skills']}</span>
                    <span class='cs-badge badge-slate'>👥 {t['applicant_count']} applied</span>
                    <div style='color:#334155;font-size:11px;margin-top:6px;'>Posted: {t['created_at'][:10]}</div>""",
                    unsafe_allow_html=True)
            with tc2:
                new_s = st.selectbox("Status",["open","in_progress","closed"],
                    index=["open","in_progress","closed"].index(t["status"]),key=f"at_stat_{t['id']}")
                if st.button("Update", key=f"at_upd_{t['id']}"): update_task_status(t["id"],new_s); st.success("Updated."); st.rerun()
                if st.button("🗑 Delete",key=f"at_del_{t['id']}"): delete_task(t["id"]); st.success("Deleted."); st.rerun()


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
