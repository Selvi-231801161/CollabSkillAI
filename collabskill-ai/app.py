import streamlit as st
import pandas as pd
from database import (
    init_db, get_connection, get_user_by_username,
    update_user_profile, insert_task, close_task, delete_task,
    insert_feedback, already_reviewed,
    get_feedback_for_user, get_feedback_by_user,
    get_platform_stats, get_top_users
)
from auth import register_user, login_user, update_trust_score
from ai_matching import match_users_to_task, get_skill_suggestions

# ══════════════════════════════════════════════════════
#  INIT
# ══════════════════════════════════════════════════════
init_db()

st.set_page_config(
    page_title="CollabSkill AI",
    page_icon="🚀",
    layout="wide"
)

for k, v in {
    "page": "landing",
    "user": None,
    "ai_matches": [],
    "ai_searched": False,
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ══════════════════════════════════════════════════════
#  GLOBAL CSS
# ══════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

header, #MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 0 !important; padding-bottom: 2rem; }
* { font-family: 'Inter', sans-serif; box-sizing: border-box; }

.stApp { background-color: #050816; }

/* inputs */
.stTextInput input,
.stTextArea textarea {
    background: #111827 !important;
    color: #e5e7eb !important;
    border: 1px solid #1f2937 !important;
    border-radius: 10px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #22d3ee !important;
    box-shadow: 0 0 0 2px rgba(34,211,238,.12) !important;
}
label,
.stTextInput label, .stTextArea label,
.stSelectbox label, .stSlider label,
.stRadio label, .stCheckbox label {
    color: #e5e7eb !important;
    font-size: 13px !important;
    font-weight: 500 !important;
}
input::placeholder, textarea::placeholder { color: #374151 !important; }

/* selectbox */
.stSelectbox > div > div {
    background: #111827 !important;
    color: #e5e7eb !important;
    border: 1px solid #1f2937 !important;
    border-radius: 10px !important;
}

/* button */
.stButton > button {
    background: linear-gradient(135deg,#06b6d4,#7c3aed) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    padding: 10px 20px !important;
    transition: opacity .2s, transform .15s !important;
}
.stButton > button:hover {
    opacity: .85 !important;
    transform: translateY(-1px) !important;
}

/* metrics */
[data-testid="metric-container"] {
    background: #0d1117 !important;
    border: 1px solid #1e293b !important;
    border-radius: 14px !important;
    padding: 18px 20px !important;
}
[data-testid="metric-container"] label {
    color: #475569 !important;
    font-size: 11px !important;
    text-transform: uppercase;
    letter-spacing: .06em;
}
[data-testid="stMetricValue"] {
    color: #22d3ee !important;
    font-size: 28px !important;
    font-weight: 800 !important;
}

/* expander */
.streamlit-expanderHeader {
    background: #0d1117 !important;
    border: 1px solid #1e293b !important;
    border-radius: 12px !important;
    color: #e5e7eb !important;
    font-weight: 600 !important;
}

/* slider */
.stSlider > div > div > div { background: #22d3ee !important; }

/* sidebar */
[data-testid="stSidebar"] {
    background: #07091a !important;
    border-right: 1px solid #1e293b !important;
}
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stButton > button {
    background: #0f172a !important;
    border: 1px solid #1e293b !important;
    color: #94a3b8 !important;
    text-align: left !important;
    justify-content: flex-start !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    border-color: #22d3ee !important;
    color: #22d3ee !important;
    background: rgba(34,211,238,.06) !important;
}

/* tabs */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #1e293b; }
.stTabs [data-baseweb="tab"] { color: #64748b !important; font-weight: 600 !important; }
.stTabs [aria-selected="true"] { color: #22d3ee !important; border-bottom: 2px solid #22d3ee !important; }

/* helpers */
.cs-card {
    background: #0d1117;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 22px 24px;
    margin-bottom: 14px;
}
.cs-badge {
    background: rgba(34,211,238,.08);
    color: #22d3ee;
    border: 1px solid rgba(34,211,238,.2);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 500;
    display: inline-block;
    margin: 3px 3px 3px 0;
}
.cs-badge-purple {
    background: rgba(124,58,237,.1);
    color: #a78bfa;
    border: 1px solid rgba(124,58,237,.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    display: inline-block;
    margin: 3px 3px 3px 0;
}
.cs-badge-green {
    background: rgba(34,197,94,.1);
    color: #4ade80;
    border: 1px solid rgba(34,197,94,.25);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    display: inline-block;
    margin: 3px 3px 3px 0;
}
.page-title {
    font-size: 30px;
    font-weight: 900;
    color: #f1f5f9;
    letter-spacing: -.02em;
    margin-bottom: 4px;
}
.page-sub {
    color: #475569;
    font-size: 13px;
    margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════
def render_sidebar():
    if not st.session_state.user:
        return
    u = st.session_state.user
    with st.sidebar:
        st.markdown(
            "<div style='padding:20px 0 10px; font-size:20px; font-weight:900; color:#f1f5f9;'>"
            "🚀 CollabSkill<span style='color:#22d3ee;'> AI</span></div>",
            unsafe_allow_html=True
        )
        st.markdown("<hr style='border-color:#1e293b; margin:0 0 16px;'/>", unsafe_allow_html=True)

        # Profile pill
        st.markdown(f"""
        <div style='background:#0f172a; border:1px solid #1e293b; border-radius:12px;
                    padding:16px; margin-bottom:18px; text-align:center;'>
            <div style='font-size:38px;'>👤</div>
            <div style='color:#f1f5f9; font-weight:700; font-size:15px; margin-top:8px;'>{u[1]}</div>
            <div style='color:#475569; font-size:12px; margin-top:2px;'>{u[2]}</div>
            <div style='margin-top:10px; color:#22d3ee; font-size:22px; font-weight:800;'>
                ⭐ {round(u[8], 1)}<span style='color:#475569; font-size:12px; font-weight:400;'> / 10</span>
            </div>
            <div style='margin-top:6px;'><span class='cs-badge'>{u[5]}</span></div>
        </div>
        """, unsafe_allow_html=True)

        nav_items = [
            ("🏠", "Dashboard",    "dashboard"),
            ("📋", "Post a Task",  "post_task"),
            ("🔍", "Browse Tasks", "browse_tasks"),
            ("🤖", "AI Match",     "ai_match"),
            ("👤", "My Profile",   "profile"),
            ("⭐", "Feedback",     "feedback"),
        ]
        for icon, label, key in nav_items:
            if st.button(f"{icon}  {label}", key=f"sb_{key}", use_container_width=True):
                st.session_state.page = key
                st.rerun()

        st.markdown("<hr style='border-color:#1e293b; margin:18px 0;'/>", unsafe_allow_html=True)
        if st.button("🚪  Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.page = "landing"
            st.rerun()


# ══════════════════════════════════════════════════════
#  LANDING
# ══════════════════════════════════════════════════════
def page_landing():
    c1, c2 = st.columns([8, 2])
    with c1:
        st.markdown(
            "<h3 style='color:#f1f5f9; margin:18px 0 0; font-size:20px;'>🚀 CollabSkill AI</h3>",
            unsafe_allow_html=True
        )
    with c2:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        if st.button("Get Started →"):
            st.session_state.page = "register"; st.rerun()

    # Hero
    st.markdown("""
    <div style='text-align:center; padding:70px 24px 40px;'>
        <div style='display:inline-block; background:rgba(34,211,238,.08);
                    border:1px solid rgba(34,211,238,.2); border-radius:20px;
                    padding:5px 18px; color:#22d3ee; font-size:11px;
                    font-weight:700; letter-spacing:.1em; text-transform:uppercase; margin-bottom:30px;'>
            ✦ AI-Powered Skill Exchange Platform
        </div>
        <div style='font-size:clamp(44px,7vw,84px); font-weight:900;
                    color:#f1f5f9; line-height:1.05; letter-spacing:-.03em;'>
            Connect.<br>Collaborate.
        </div>
        <div style='font-size:clamp(44px,7vw,84px); font-weight:900;
                    background:linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
                    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
                    line-height:1.1; letter-spacing:-.03em; margin-bottom:28px;'>
            Exchange Skills Smarter.
        </div>
        <div style='color:#475569; font-size:17px; max-width:540px;
                    margin:0 auto 40px; line-height:1.75;'>
            An intelligent platform that uses AI to match you with the right
            collaborators instantly. Post tasks, share skills, build your reputation.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # CTA
    _, b1, b2, _ = st.columns([2, 1, 1, 2])
    with b1:
        if st.button("🚀  Join Free", use_container_width=True):
            st.session_state.page = "register"; st.rerun()
    with b2:
        if st.button("🔐  Login", use_container_width=True):
            st.session_state.page = "login"; st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Stats
    tu, tt, ot, tr_ = get_platform_stats()
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("👥 Users",         tu)
    s2.metric("📋 Tasks Posted",  tt)
    s3.metric("🟢 Open Tasks",    ot)
    s4.metric("⭐ Reviews",       tr_)

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature grid
    st.markdown("""
    <div style='display:grid; grid-template-columns:repeat(4,1fr); gap:16px;'>
        <div class='cs-card' style='text-align:center;'>
            <div style='font-size:30px; margin-bottom:12px;'>🤖</div>
            <div style='color:#f1f5f9; font-weight:700; font-size:14px; margin-bottom:8px;'>AI Matching</div>
            <div style='color:#475569; font-size:13px; line-height:1.6;'>Smart AI finds the best collaborators for your task in seconds</div>
        </div>
        <div class='cs-card' style='text-align:center;'>
            <div style='font-size:30px; margin-bottom:12px;'>🛡️</div>
            <div style='color:#f1f5f9; font-weight:700; font-size:14px; margin-bottom:8px;'>Trust Score</div>
            <div style='color:#475569; font-size:13px; line-height:1.6;'>Reputation system built from real community feedback</div>
        </div>
        <div class='cs-card' style='text-align:center;'>
            <div style='font-size:30px; margin-bottom:12px;'>🌐</div>
            <div style='color:#f1f5f9; font-weight:700; font-size:14px; margin-bottom:8px;'>Skill Exchange</div>
            <div style='color:#475569; font-size:13px; line-height:1.6;'>Connect, learn and grow with a global digital community</div>
        </div>
        <div class='cs-card' style='text-align:center;'>
            <div style='font-size:30px; margin-bottom:12px;'>⚡</div>
            <div style='color:#f1f5f9; font-weight:700; font-size:14px; margin-bottom:8px;'>Instant Connect</div>
            <div style='color:#475569; font-size:13px; line-height:1.6;'>Post a task and get matched with the right person instantly</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  LOGIN
# ══════════════════════════════════════════════════════
def page_login():
    _, mid, _ = st.columns([1, 1.5, 1])
    with mid:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
        <div class='cs-card' style='text-align:center; margin-bottom:0;'>
            <div style='font-size:34px;'>👋</div>
            <div style='color:#f1f5f9; font-size:22px; font-weight:800; margin-top:10px;'>Welcome Back</div>
            <div style='color:#475569; font-size:13px; margin-top:4px;'>Login to your CollabSkill account</div>
        </div>
        """, unsafe_allow_html=True)

        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")

        if st.button("Login →", use_container_width=True):
            if username and password:
                user = login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password.")
            else:
                st.warning("Please fill both fields.")

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Home", use_container_width=True):
                st.session_state.page = "landing"; st.rerun()
        with c2:
            if st.button("Create Account", use_container_width=True):
                st.session_state.page = "register"; st.rerun()


# ══════════════════════════════════════════════════════
#  REGISTER
# ══════════════════════════════════════════════════════
def page_register():
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='page-title'>Create Your Profile 🚀</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Join the CollabSkill AI community — it's completely free</div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        username   = st.text_input("Username *",      placeholder="Choose a unique username")
        email      = st.text_input("Email *",         placeholder="your@email.com")
        password   = st.text_input("Password *",      type="password", placeholder="Minimum 6 characters")
    with col2:
        skills     = st.text_input("Your Skills *",   placeholder="e.g. Python, UI Design, SEO, Editing")
        experience = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced", "Expert"])
        portfolio  = st.text_input("Portfolio / GitHub", placeholder="https://github.com/you (optional)")

    bio   = st.text_area("Short Bio", height=90,
                          placeholder="Tell the community about yourself — background, interests, what you can help with...")
    agree = st.checkbox("I agree to the Terms & Conditions and Privacy Policy")

    if st.button("Create My Account 🎉", use_container_width=True):
        if not agree:
            st.warning("⚠️ Please accept the Terms & Conditions.")
        elif not all([username, email, password, skills]):
            st.warning("⚠️ Please fill all required fields (marked *).")
        elif len(password) < 6:
            st.warning("⚠️ Password must be at least 6 characters.")
        else:
            ok, msg = register_user(username, email, password, skills, bio, portfolio, experience)
            if ok:
                st.success("✅ Account created! Please login.")
                st.balloons()
                st.session_state.page = "login"; st.rerun()
            else:
                st.error(f"❌ {msg}")

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Already have an account? Login"):
        st.session_state.page = "login"; st.rerun()


# ══════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════
def page_dashboard():
    u = st.session_state.user
    st.markdown(f"<div class='page-title'>Welcome back, {u[1]}! 👋</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Here's everything happening on the platform right now</div>", unsafe_allow_html=True)

    tu, tt, ot, tr_ = get_platform_stats()
    m1,m2,m3,m4,m5 = st.columns(5)
    m1.metric("👥 Users",       tu)
    m2.metric("📋 Tasks",       tt)
    m3.metric("🟢 Open",        ot)
    m4.metric("⭐ Reviews",     tr_)
    m5.metric("🏅 Your Score",  f"{round(u[8],1)}/10")

    st.markdown("<br>", unsafe_allow_html=True)
    left, right = st.columns([3, 2])

    with left:
        st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:17px; margin-bottom:14px;'>📋 Recent Tasks</div>", unsafe_allow_html=True)
        conn = get_connection()
        df = pd.read_sql("""
            SELECT title, posted_by, required_skills, status, created_at
            FROM tasks ORDER BY created_at DESC LIMIT 8
        """, conn)
        conn.close()
        if df.empty:
            st.markdown("<div class='cs-card' style='color:#475569; text-align:center;'>No tasks yet — be the first to post one!</div>", unsafe_allow_html=True)
        else:
            for _, row in df.iterrows():
                sc = "#22d3ee" if row['status'] == 'open' else "#f87171"
                bg = "rgba(34,211,238,.06)" if row['status'] == 'open' else "rgba(239,68,68,.06)"
                st.markdown(f"""
                <div class='cs-card' style='padding:13px 16px;'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                        <div style='flex:1;'>
                            <div style='color:#f1f5f9; font-weight:600; font-size:13px;'>{row['title']}</div>
                            <div style='color:#475569; font-size:11px; margin-top:2px;'>
                                by {row['posted_by']} · {str(row['created_at'])[:10]}
                            </div>
                            <span class='cs-badge' style='margin-top:5px;'>🛠 {row['required_skills']}</span>
                        </div>
                        <span style='background:{bg}; color:{sc}; border-radius:8px;
                                     padding:3px 9px; font-size:11px; font-weight:700;
                                     white-space:nowrap; margin-left:10px;'>
                            ● {str(row['status']).upper()}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with right:
        st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:17px; margin-bottom:14px;'>🏆 Trust Leaderboard</div>", unsafe_allow_html=True)
        medals = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣"]
        for i, row in enumerate(get_top_users(6)):
            hl = "border-color:rgba(34,211,238,.35);" if row[0] == u[1] else ""
            m  = medals[i] if i < len(medals) else "👤"
            st.markdown(f"""
            <div class='cs-card' style='padding:12px 16px; {hl}'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <div style='color:#f1f5f9; font-weight:600; font-size:13px;'>{m} {row[0]}</div>
                        <div style='color:#475569; font-size:11px;'>{(row[1] or "—")[:28]}</div>
                    </div>
                    <div style='text-align:right;'>
                        <div style='color:#22d3ee; font-size:18px; font-weight:800;'>{round(row[2],1)}</div>
                        <div style='color:#475569; font-size:10px;'>{row[3]} ratings</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:17px; margin-bottom:14px;'>⚡ Quick Actions</div>", unsafe_allow_html=True)
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("➕ Post a Task",  use_container_width=True): st.session_state.page="post_task";    st.rerun()
    with q2:
        if st.button("🔍 Browse Tasks", use_container_width=True): st.session_state.page="browse_tasks"; st.rerun()
    with q3:
        if st.button("🤖 AI Match",     use_container_width=True): st.session_state.page="ai_match";     st.rerun()
    with q4:
        if st.button("👤 My Profile",   use_container_width=True): st.session_state.page="profile";      st.rerun()


# ══════════════════════════════════════════════════════
#  POST TASK
# ══════════════════════════════════════════════════════
def _my_recent_tasks(username, n=5):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks WHERE posted_by=? ORDER BY created_at DESC LIMIT ?", (username, n))
    rows = c.fetchall()
    conn.close()
    return rows


def page_post_task():
    st.markdown("<div class='page-title'>📋 Post a Task</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Describe what you need — AI will find the right collaborator</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        title    = st.text_input("Task Title *",         placeholder="e.g. Need a Python dev for web scraping")
        desc     = st.text_area("Task Description *",    height=130,
                                 placeholder="Describe exactly what needs to be done, deliverables, goals...")
        r1, r2   = st.columns(2)
        with r1:
            skills   = st.text_input("Required Skills *", placeholder="e.g. Python, Pandas, SQL")
            category = st.selectbox("Category", ["Development","Design","Marketing","Content Writing",
                                                  "Data Science","Video Editing","SEO","UI/UX","Other"])
        with r2:
            deadline = st.text_input("Deadline",          placeholder="e.g. 3 days / by June 15")

        if st.button("🚀 Post Task", use_container_width=True):
            if title and desc and skills:
                insert_task(title, desc, skills, category, deadline, st.session_state.user[1])
                st.success("✅ Task posted! People can now find and collaborate with you.")
                st.balloons()
            else:
                st.warning("⚠️ Please fill Title, Description and Required Skills.")

    with c2:
        st.markdown("""
        <div class='cs-card'>
            <div style='color:#22d3ee; font-weight:700; font-size:13px; margin-bottom:13px;'>💡 Tips for a Great Post</div>
            <div style='color:#64748b; font-size:13px; line-height:2.1;'>
                ✅ Write a clear specific title<br>
                ✅ Explain the expected output<br>
                ✅ List exact skills needed<br>
                ✅ Mention your deadline<br>
                ✅ Add background context<br>
                ✅ Be respectful & clear
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='color:#f1f5f9; font-weight:600; font-size:13px; margin:4px 0 10px;'>📌 My Recent Posts</div>", unsafe_allow_html=True)
        for t in _my_recent_tasks(st.session_state.user[1]):
            dot = "🟢" if t[7] == "open" else "🔴"
            st.markdown(f"<div style='color:#94a3b8; font-size:12px; padding:5px 0; border-bottom:1px solid #1e293b;'>{dot} {t[1]}</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  BROWSE TASKS
# ══════════════════════════════════════════════════════
def page_browse_tasks():
    st.markdown("<div class='page-title'>🔍 Browse Tasks</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Find tasks that match your skills and start collaborating</div>", unsafe_allow_html=True)

    f1, f2, f3, f4 = st.columns([3, 1, 1, 1])
    with f1: search   = st.text_input("", placeholder="🔍  Search tasks by keyword or skill...")
    with f2: sf       = st.selectbox("Status",   ["All","Open","Closed"])
    with f3: cf       = st.selectbox("Category", ["All","Development","Design","Marketing",
                                                    "Content Writing","Data Science","Video Editing","SEO","UI/UX","Other"])
    with f4: sort     = st.selectbox("Sort",      ["Newest","Oldest"])

    conn = get_connection()
    q, params = "SELECT * FROM tasks WHERE 1=1", []
    if search:
        q += " AND (title LIKE ? OR required_skills LIKE ? OR description LIKE ?)"
        s = f"%{search}%"; params += [s, s, s]
    if sf != "All":
        q += " AND status=?"; params.append(sf.lower())
    if cf != "All":
        q += " AND category=?"; params.append(cf)
    q += " ORDER BY created_at " + ("DESC" if sort == "Newest" else "ASC")
    df = pd.read_sql(q, conn, params=params)
    conn.close()

    st.markdown(f"<div style='color:#475569; font-size:12px; margin-bottom:14px;'>Showing {len(df)} task(s)</div>", unsafe_allow_html=True)

    if df.empty:
        st.markdown("""
        <div class='cs-card' style='text-align:center; padding:60px;'>
            <div style='font-size:44px;'>📭</div>
            <div style='color:#f1f5f9; font-weight:700; font-size:18px; margin-top:14px;'>No tasks found</div>
            <div style='color:#475569; margin-top:6px;'>Try different filters or post the first task!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for _, row in df.iterrows():
        sc = "#22d3ee" if row['status']=='open' else "#f87171"
        bg = "rgba(34,211,238,.05)" if row['status']=='open' else "rgba(239,68,68,.05)"
        with st.expander(f"📌  {row['title']}  —  {row['posted_by']}  ·  {str(row['created_at'])[:10]}"):
            d1, d2 = st.columns([3, 1])
            with d1:
                st.markdown(f"<div style='color:#94a3b8; font-size:13px; line-height:1.8;'>{row['description']}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='cs-badge'>🛠 {row['required_skills']}</span>", unsafe_allow_html=True)
                st.markdown(f"<span class='cs-badge-purple'>📂 {row['category']}</span>", unsafe_allow_html=True)
                if row['deadline']:
                    st.markdown(f"<span class='cs-badge-green'>⏰ {row['deadline']}</span>", unsafe_allow_html=True)
            with d2:
                st.markdown(f"""
                <div style='background:{bg}; border:1px solid {sc}44; border-radius:10px;
                            padding:12px; text-align:center; margin-bottom:10px;'>
                    <div style='color:{sc}; font-weight:700; font-size:12px;'>● {str(row['status']).upper()}</div>
                </div>
                """, unsafe_allow_html=True)
                if row['posted_by'] == st.session_state.user[1]:
                    if row['status'] == 'open':
                        if st.button("✅ Close", key=f"cl_{row['id']}", use_container_width=True):
                            close_task(row['id']); st.rerun()
                    if st.button("🗑 Delete", key=f"dl_{row['id']}", use_container_width=True):
                        delete_task(row['id']); st.rerun()


# ══════════════════════════════════════════════════════
#  AI MATCH
# ══════════════════════════════════════════════════════
def page_ai_match():
    st.markdown("<div class='page-title'>🤖 AI Skill Matching</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Describe your task — AI finds the best collaborators on the platform</div>", unsafe_allow_html=True)

    c1, c2 = st.columns([3, 2])
    with c1:
        title  = st.text_input("Task Title",         placeholder="e.g. Build a REST API with FastAPI")
        desc   = st.text_area("Task Description",    height=110, placeholder="Describe in detail what you need...")
        skills = st.text_input("Skills Required",    placeholder="e.g. Python, FastAPI, PostgreSQL")

        if st.button("🔍 Find Best Matches with AI", use_container_width=True):
            if title and desc and skills:
                with st.spinner("🤖 AI is analysing all profiles..."):
                    try:
                        st.session_state.ai_matches  = match_users_to_task(title, desc, skills, st.session_state.user[1])
                        st.session_state.ai_searched = True
                    except RuntimeError as e:
                        st.error(str(e))
                        st.session_state.ai_searched = False
            else:
                st.warning("Please fill all three fields.")

    with c2:
        st.markdown("""
        <div class='cs-card'>
            <div style='color:#22d3ee; font-weight:700; font-size:13px; margin-bottom:13px;'>⚡ How It Works</div>
            <div style='color:#64748b; font-size:13px; line-height:2.1;'>
                1️⃣ You describe your task<br>
                2️⃣ AI reads every user profile<br>
                3️⃣ Matches skills to requirements<br>
                4️⃣ Weighs experience & trust scores<br>
                5️⃣ Returns top 3 best matches<br>
                6️⃣ You connect &amp; collaborate!
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='color:#f1f5f9; font-weight:600; font-size:13px; margin:6px 0 10px;'>💡 Skills to Learn Next</div>", unsafe_allow_html=True)
        if st.button("Get AI Suggestions", use_container_width=True):
            with st.spinner("Thinking..."):
                tips = get_skill_suggestions(st.session_state.user[4])
                st.markdown(f"<div class='cs-card' style='color:#94a3b8; font-size:13px;'>{tips}</div>", unsafe_allow_html=True)

    # Results
    if st.session_state.ai_searched:
        st.markdown("<br>", unsafe_allow_html=True)
        matches = st.session_state.ai_matches
        if not matches:
            st.markdown("""
            <div class='cs-card' style='text-align:center; padding:40px;'>
                <div style='font-size:38px;'>🔍</div>
                <div style='color:#f1f5f9; font-weight:700; margin-top:12px;'>No matches found</div>
                <div style='color:#475569; margin-top:6px;'>Invite more people to register!</div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='color:#22d3ee; font-weight:700; font-size:19px; margin-bottom:18px;'>✅ Top {len(matches)} Matches</div>", unsafe_allow_html=True)
            medals = ["🥇","🥈","🥉"]
            for i, m in enumerate(matches):
                score = int(m.get("match_score", 0))
                sc    = "#22d3ee" if score>=80 else "#f59e0b" if score>=60 else "#f87171"
                md    = medals[i] if i < 3 else "👤"
                ud    = get_user_by_username(m['username'])
                u_sk  = ud[4] if ud else "—"
                u_ex  = ud[5] if ud else "—"
                u_tr  = round(ud[8], 1) if ud else "—"
                u_bi  = (ud[6] or "")[:80] if ud else ""
                st.markdown(f"""
                <div class='cs-card' style='border-color:rgba(34,211,238,.15);'>
                    <div style='display:flex; justify-content:space-between; align-items:flex-start; gap:16px;'>
                        <div style='flex:1;'>
                            <div style='color:#f1f5f9; font-size:19px; font-weight:800;'>{md} {m['username']}</div>
                            <div style='margin-top:6px;'>
                                <span class='cs-badge'>🛠 {u_sk}</span>
                                <span class='cs-badge-purple'>📊 {u_ex}</span>
                            </div>
                            <div style='color:#64748b; font-size:13px; margin-top:10px; line-height:1.6;'>{m.get("reason","")}</div>
                            {'<div style="color:#475569; font-size:12px; margin-top:6px; font-style:italic;">"' + u_bi + '..."</div>' if u_bi else ""}
                        </div>
                        <div style='text-align:center; min-width:95px;'>
                            <div style='color:{sc}; font-size:34px; font-weight:900;'>{score}%</div>
                            <div style='color:#475569; font-size:11px;'>Match Score</div>
                            <div style='color:#22d3ee; font-size:18px; font-weight:700; margin-top:8px;'>⭐ {u_tr}</div>
                            <div style='color:#475569; font-size:11px;'>Trust Score</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  PROFILE
# ══════════════════════════════════════════════════════
def page_profile():
    u = st.session_state.user
    st.markdown("<div class='page-title'>👤 My Profile</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Your public profile, skills, tasks and reputation</div>", unsafe_allow_html=True)

    t1, t2, t3 = st.tabs(["📋 Overview", "✏️ Edit Profile", "📊 Activity"])

    # Overview
    with t1:
        pc, fc = st.columns([1, 2])
        with pc:
            st.markdown(f"""
            <div class='cs-card' style='text-align:center;'>
                <div style='font-size:56px; margin-bottom:10px;'>👤</div>
                <div style='color:#f1f5f9; font-size:20px; font-weight:800;'>{u[1]}</div>
                <div style='color:#475569; font-size:12px; margin-top:3px;'>{u[2]}</div>
                <div style='margin-top:10px;'><span class='cs-badge-purple'>{u[5]}</span></div>
                <div style='margin-top:14px; color:#22d3ee; font-size:34px; font-weight:900;'>{round(u[8],1)}</div>
                <div style='color:#475569; font-size:12px;'>Trust Score / 10</div>
                <div style='color:#64748b; font-size:11px; margin-top:2px;'>from {u[9]} ratings</div>
                <div style='margin-top:14px; color:#94a3b8; font-size:13px; line-height:1.6; text-align:left; padding:0 4px;'>
                    {u[6] or '<span style="color:#475569;">No bio yet.</span>'}
                </div>
                {'<div style="margin-top:12px;"><a href="'+ u[7] +'" target="_blank" style="color:#22d3ee; font-size:13px;">🔗 Portfolio</a></div>' if u[7] else ''}
            </div>
            """, unsafe_allow_html=True)

            st.markdown("<div class='cs-card'>", unsafe_allow_html=True)
            st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:13px; margin-bottom:10px;'>🛠 Skills</div>", unsafe_allow_html=True)
            if u[4]:
                for sk in u[4].split(","):
                    st.markdown(f"<span class='cs-badge'>{sk.strip()}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with fc:
            st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:15px; margin-bottom:12px;'>⭐ Feedback Received</div>", unsafe_allow_html=True)
            fbs = get_feedback_for_user(u[1])
            if fbs:
                for fb in fbs:
                    st.markdown(f"""
                    <div class='cs-card' style='padding:13px 16px;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <div style='color:#f1f5f9; font-weight:600; font-size:13px;'>👤 {fb[0]}</div>
                            <div style='font-size:13px;'>{"⭐"*int(fb[1])}</div>
                        </div>
                        <div style='color:#94a3b8; font-size:13px; margin-top:5px;'>{fb[2] or "No comment."}</div>
                        <div style='color:#334155; font-size:11px; margin-top:5px;'>🕐 {str(fb[3])[:10]}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown("<div style='color:#475569; font-size:13px;'>No feedback received yet.</div>", unsafe_allow_html=True)

    # Edit profile
    with t2:
        st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:15px; margin-bottom:16px;'>✏️ Update Your Profile</div>", unsafe_allow_html=True)
        ns = st.text_input("Skills",            value=u[4] or "")
        nb = st.text_area("Bio",                value=u[6] or "", height=90)
        np = st.text_input("Portfolio / GitHub", value=u[7] or "")
        ne = st.selectbox("Experience",
                           ["Beginner","Intermediate","Advanced","Expert"],
                           index=["Beginner","Intermediate","Advanced","Expert"].index(u[5])
                                 if u[5] in ["Beginner","Intermediate","Advanced","Expert"] else 0)
        if st.button("💾 Save Changes", use_container_width=True):
            update_user_profile(u[1], ns, nb, np, ne)
            st.session_state.user = get_user_by_username(u[1])
            st.success("✅ Profile updated!")
            st.rerun()

    # Activity
    with t3:
        st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:15px; margin-bottom:12px;'>📋 My Posted Tasks</div>", unsafe_allow_html=True)
        for t in _my_recent_tasks(u[1], 20):
            sc = "#22d3ee" if t[7]=='open' else "#f87171"
            st.markdown(f"""
            <div class='cs-card' style='padding:12px 16px;'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <div>
                        <div style='color:#f1f5f9; font-weight:600; font-size:13px;'>{t[1]}</div>
                        <span class='cs-badge'>🛠 {t[3]}</span>
                        <span class='cs-badge-purple'>📂 {t[4]}</span>
                    </div>
                    <span style='color:{sc}; font-size:11px; font-weight:700;'>● {t[7].upper()}</span>
                </div>
                <div style='color:#334155; font-size:11px; margin-top:5px;'>🕐 {str(t[8])[:10]}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='color:#f1f5f9; font-weight:700; font-size:15px; margin-bottom:12px;'>📝 Feedback I Gave</div>", unsafe_allow_html=True)
        for fb in get_feedback_by_user(u[1]):
            st.markdown(f"""
            <div class='cs-card' style='padding:12px 16px;'>
                <div style='display:flex; justify-content:space-between;'>
                    <div style='color:#f1f5f9; font-weight:600; font-size:13px;'>→ {fb[0]}</div>
                    <div style='font-size:13px;'>{"⭐"*int(fb[1])}</div>
                </div>
                <div style='color:#94a3b8; font-size:13px; margin-top:5px;'>{fb[2] or "—"}</div>
            </div>
            """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  FEEDBACK
# ══════════════════════════════════════════════════════
def page_feedback():
    st.markdown("<div class='page-title'>⭐ Give Feedback</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Rate your collaborators and help build a trusted community</div>", unsafe_allow_html=True)

    conn = get_connection()
    udf  = pd.read_sql(
        "SELECT username, skills, trust_score, experience FROM users WHERE username != ?",
        conn, params=(st.session_state.user[1],)
    )
    conn.close()

    if udf.empty:
        st.info("No other users to rate yet."); return

    c1, c2 = st.columns([2, 1])
    with c1:
        to_user = st.selectbox("Select collaborator to rate", udf['username'].tolist())
        rating  = st.slider("Rating",  1, 5, 4)
        st.markdown(f"<div style='font-size:20px; margin:6px 0 14px;'>{'⭐'*rating}</div>", unsafe_allow_html=True)
        comment = st.text_area("Comment (optional)", placeholder="What were they great at? How was the collaboration?")

        if st.button("✅ Submit Feedback", use_container_width=True):
            if already_reviewed(st.session_state.user[1], to_user):
                st.warning("⚠️ You have already reviewed this user.")
            else:
                insert_feedback(st.session_state.user[1], to_user, rating, comment)
                update_trust_score(to_user, rating * 2)   # 1-5 → 2-10
                st.success(f"✅ Feedback submitted! {to_user}'s trust score updated.")
                st.balloons()

    with c2:
        sel = udf[udf['username'] == to_user].iloc[0]
        st.markdown(f"""
        <div class='cs-card' style='text-align:center;'>
            <div style='font-size:42px;'>👤</div>
            <div style='color:#f1f5f9; font-size:17px; font-weight:700; margin-top:10px;'>{sel['username']}</div>
            <div style='margin-top:8px;'><span class='cs-badge'>🛠 {sel['skills']}</span></div>
            <div style='margin-top:6px;'><span class='cs-badge-purple'>{sel['experience']}</span></div>
            <div style='margin-top:14px; color:#22d3ee; font-size:28px; font-weight:900;'>{round(sel['trust_score'],1)}</div>
            <div style='color:#475569; font-size:12px;'>Current Trust Score</div>
        </div>
        <div class='cs-card' style='margin-top:0;'>
            <div style='color:#f1f5f9; font-weight:600; font-size:13px; margin-bottom:10px;'>Rating Guide</div>
            <div style='color:#64748b; font-size:12px; line-height:2.1;'>
                ⭐ — Poor<br>⭐⭐ — Below average<br>
                ⭐⭐⭐ — Good<br>⭐⭐⭐⭐ — Great!<br>
                ⭐⭐⭐⭐⭐ — Excellent!
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════
#  ROUTER
# ══════════════════════════════════════════════════════
render_sidebar()
p = st.session_state.page

if   p == "landing":  page_landing()
elif p == "login":    page_login()
elif p == "register": page_register()
else:
    if not st.session_state.user:
        st.session_state.page = "login"; st.rerun()
    elif p == "dashboard":    page_dashboard()
    elif p == "post_task":    page_post_task()
    elif p == "browse_tasks": page_browse_tasks()
    elif p == "ai_match":     page_ai_match()
    elif p == "profile":      page_profile()
    elif p == "feedback":     page_feedback()
