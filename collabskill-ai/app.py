import streamlit as st
import pandas as pd
from database import init_db, get_connection
from auth import register_user, login_user, update_trust_score
from ai_matching import match_users_to_task

init_db()

st.set_page_config(layout="wide", page_title="CollabSkill AI", page_icon="🚀")

# SESSION
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user" not in st.session_state:
    st.session_state.user = None

# ================= GLOBAL CSS =================
st.markdown("""
<style>

/* REMOVE STREAMLIT HEADER */
header, #MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 0rem;}

/* BACKGROUND */
.stApp {
    background-color: #050816;
}

/* CENTER CONTENT */
.center {
    text-align: center;
    margin-top: 80px;
}

/* HERO TEXT */
.light {
    color: #e5e7eb;
    font-size: 85px;
    font-weight: 900;
    line-height: 1.1;
}

/* GRADIENT */
.gradient {
    font-size: 85px;
    font-weight: 900;
    line-height: 1.1;
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}

/* SUBTEXT */
.sub {
    color: #94a3b8;
    font-size: 18px;
    text-align: center;
    margin-top: 20px;
}

/* INPUT FIX */
.stTextInput input, .stTextArea textarea {
    background-color: #1f2937 !important;
    color: white !important;
    border: 1px solid #374151 !important;
}

/* LABEL FIX */
label, .stTextInput label, .stTextArea label {
    color: #ffffff !important;
    font-weight: 500;
}

/* PLACEHOLDER */
input::placeholder {
    color: #9ca3af !important;
}

/* SELECTBOX */
.stSelectbox div {
    background-color: #1f2937 !important;
    color: white !important;
}

/* CHECKBOX */
.stCheckbox label {
    color: white !important;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg,#22d3ee,#7c3aed);
    color: white;
    border-radius: 10px;
    border: none;
}

/* METRIC */
[data-testid="metric-container"] {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px;
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important;
    font-size: 13px !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    color: #22d3ee !important;
    font-size: 28px !important;
    font-weight: 800 !important;
}

/* DATAFRAME */
.stDataFrame {
    background-color: #0f172a !important;
}

/* EXPANDER */
.streamlit-expanderHeader {
    background-color: #0f172a !important;
    color: #e5e7eb !important;
    border-radius: 10px !important;
}

/* SLIDER */
.stSlider label {
    color: #ffffff !important;
}

/* RADIO */
.stRadio label {
    color: #e5e7eb !important;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #0a0f1e !important;
    border-right: 1px solid #1e293b;
}
[data-testid="stSidebar"] * {
    color: #e5e7eb !important;
}

/* CARD */
.cs-card {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 16px;
}

/* BADGE */
.cs-badge {
    background: rgba(34,211,238,0.1);
    color: #22d3ee;
    border: 1px solid rgba(34,211,238,0.2);
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 12px;
    display: inline-block;
    margin-right: 6px;
    margin-top: 8px;
}

/* PAGE TITLE */
.page-title {
    font-size: 36px;
    font-weight: 900;
    color: #e5e7eb;
    margin-bottom: 4px;
}

/* PAGE SUBTITLE */
.page-sub {
    color: #64748b;
    font-size: 15px;
    margin-bottom: 28px;
}

/* MATCH CARD */
.match-card {
    background: linear-gradient(135deg, #0f172a, #1a1040);
    border: 1px solid #312e81;
    border-radius: 14px;
    padding: 24px;
    margin-bottom: 14px;
}

/* NAV BUTTON ACTIVE */
.nav-active > button {
    background: linear-gradient(90deg,#22d3ee,#7c3aed) !important;
}

/* DIVIDER */
.cs-divider {
    border: none;
    border-top: 1px solid #1e293b;
    margin: 20px 0;
}

/* SUCCESS BOX */
.cs-success {
    background: rgba(34,197,94,0.1);
    border: 1px solid rgba(34,197,94,0.3);
    border-radius: 10px;
    padding: 12px 18px;
    color: #4ade80;
    font-size: 14px;
    margin-top: 10px;
}

/* TASK STATUS */
.status-open {
    background: rgba(34,211,238,0.1);
    color: #22d3ee;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
}
.status-closed {
    background: rgba(239,68,68,0.1);
    color: #f87171;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    display: inline-block;
}

</style>
""", unsafe_allow_html=True)


# ================= NAVBAR (logged in) =================
def navbar():
    u = st.session_state.user
    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([2,1,1,1,1,1,1,1])

    with col1:
        st.markdown(
            "<h3 style='color:#e5e7eb; margin:0; padding-top:8px;'>🚀 CollabSkill AI</h3>",
            unsafe_allow_html=True
        )
    with col2:
        if st.button("🏠 Home"):
            st.session_state.page = "dashboard"
            st.rerun()
    with col3:
        if st.button("📋 Tasks"):
            st.session_state.page = "browse_tasks"
            st.rerun()
    with col4:
        if st.button("➕ Post"):
            st.session_state.page = "post_task"
            st.rerun()
    with col5:
        if st.button("🤖 AI Match"):
            st.session_state.page = "ai_match"
            st.rerun()
    with col6:
        if st.button("👤 Profile"):
            st.session_state.page = "profile"
            st.rerun()
    with col7:
        if st.button("⭐ Feedback"):
            st.session_state.page = "feedback"
            st.rerun()
    with col8:
        if st.button("🚪 Logout"):
            st.session_state.user = None
            st.session_state.page = "landing"
            st.rerun()

    st.markdown("<hr style='border:1px solid #1e293b; margin-top:8px;'/>", unsafe_allow_html=True)


# ================= LANDING =================
def landing():
    col1, col2 = st.columns([8, 2])

    with col1:
        st.markdown(
            "<h3 style='color:#e5e7eb;'>🚀 CollabSkill AI</h3>",
            unsafe_allow_html=True
        )
    with col2:
        if st.button("Get Started"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown(
        '<div class="center">'
        '<div class="light">Connect.<br>Collaborate.</div>'
        '<div class="gradient">Exchange Skills</div>'
        '<div class="gradient">Smarter.</div>'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="sub">'
        'An intelligent platform that matches you with the right people — '
        'using AI to connect digital skill providers with those who need them instantly.'
        '</div>',
        unsafe_allow_html=True
    )

    st.markdown("<br><br>", unsafe_allow_html=True)

    # Stats row
    c1, c2, c3, c4 = st.columns(4)
    conn = get_connection()
    try:
        total_users = pd.read_sql("SELECT COUNT(*) as c FROM users", conn).iloc[0]['c']
        total_tasks = pd.read_sql("SELECT COUNT(*) as c FROM tasks", conn).iloc[0]['c']
        open_tasks  = pd.read_sql("SELECT COUNT(*) as c FROM tasks WHERE status='open'", conn).iloc[0]['c']
        total_fb    = pd.read_sql("SELECT COUNT(*) as c FROM feedback", conn).iloc[0]['c']
    except:
        total_users = total_tasks = open_tasks = total_fb = 0
    conn.close()

    c1.metric("👥 Users",        total_users)
    c2.metric("📋 Tasks Posted", total_tasks)
    c3.metric("🟢 Open Tasks",   open_tasks)
    c4.metric("⭐ Reviews",      total_fb)

    st.markdown("<br>", unsafe_allow_html=True)

    # Feature highlights
    st.markdown("""
    <div style='display:flex; gap:16px; flex-wrap:wrap; justify-content:center; margin-top:20px;'>
        <div class='cs-card' style='flex:1; min-width:220px; text-align:center;'>
            <div style='font-size:36px;'>🤖</div>
            <div style='color:#e5e7eb; font-weight:700; font-size:18px; margin:10px 0 6px;'>AI Matching</div>
            <div style='color:#64748b; font-size:14px;'>Smart AI finds the best collaborators for your task instantly</div>
        </div>
        <div class='cs-card' style='flex:1; min-width:220px; text-align:center;'>
            <div style='font-size:36px;'>🛡️</div>
            <div style='color:#e5e7eb; font-weight:700; font-size:18px; margin:10px 0 6px;'>Trust Score</div>
            <div style='color:#64748b; font-size:14px;'>AI-powered reputation scores built from real feedback</div>
        </div>
        <div class='cs-card' style='flex:1; min-width:220px; text-align:center;'>
            <div style='font-size:36px;'>🌐</div>
            <div style='color:#e5e7eb; font-weight:700; font-size:18px; margin:10px 0 6px;'>Skill Exchange</div>
            <div style='color:#64748b; font-size:14px;'>Connect, learn, and grow with a global digital community</div>
        </div>
        <div class='cs-card' style='flex:1; min-width:220px; text-align:center;'>
            <div style='font-size:36px;'>⚡</div>
            <div style='color:#e5e7eb; font-weight:700; font-size:18px; margin:10px 0 6px;'>Instant Connect</div>
            <div style='color:#64748b; font-size:14px;'>Post a task and get matched with the right person in seconds</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ================= LOGIN =================
def login():
    left, center, right = st.columns([1, 2, 1])

    with center:
        st.markdown("""
        <div style="
            background-color:#0f172a;
            padding:40px;
            border-radius:15px;
            box-shadow:0 0 30px rgba(0,0,0,0.5);
        ">
        """, unsafe_allow_html=True)

        st.markdown("<h2 style='color:#e5e7eb; text-align:center;'>Welcome Back 👋</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b; text-align:center; margin-bottom:24px;'>Login to your CollabSkill account</p>", unsafe_allow_html=True)

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login →", use_container_width=True):
            if username and password:
                user = login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.session_state.page = "dashboard"
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
            else:
                st.warning("Please fill both fields.")

        st.markdown("<p style='color:#9ca3af; margin-top:16px;'>Don't have an account?</p>", unsafe_allow_html=True)

        if st.button("Create Account", use_container_width=True):
            st.session_state.page = "register"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to Home"):
            st.session_state.page = "landing"
            st.rerun()


# ================= REGISTER =================
def register():
    st.markdown("<h1 style='color:#e5e7eb;'>Create Your Profile 🚀</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af;'>Join the skill exchange community</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        username   = st.text_input("Username")
        email      = st.text_input("Email")
        password   = st.text_input("Password", type="password")

    with col2:
        skills     = st.text_input("Your Skills (e.g. Python, UI Design, SEO)")
        experience = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"])
        portfolio  = st.text_input("Portfolio / GitHub Link (optional)")

    bio = st.text_area("Short Bio — tell people about yourself")
    agree = st.checkbox("I agree to Terms & Conditions")

    if st.button("Create Account 🎉", use_container_width=True):
        if not agree:
            st.warning("Please accept the Terms & Conditions.")
        elif username and email and password and skills:
            success, msg = register_user(username, email, password, skills, bio, portfolio)
            if success:
                st.success("Account created successfully! Please login.")
                st.balloons()
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(msg)
        else:
            st.warning("Please fill all required fields.")

    st.markdown("<p style='color:#9ca3af; margin-top:12px;'>Already have an account?</p>", unsafe_allow_html=True)
    if st.button("Go to Login"):
        st.session_state.page = "login"
        st.rerun()


# ================= DASHBOARD =================
def dashboard():
    navbar()
    u = st.session_state.user

    st.markdown(f"<div class='page-title'>Hello, {u[1]}! 👋</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Here's what's happening on the platform today</div>", unsafe_allow_html=True)

    conn = get_connection()
    total_users = pd.read_sql("SELECT COUNT(*) as c FROM users", conn).iloc[0]['c']
    total_tasks = pd.read_sql("SELECT COUNT(*) as c FROM tasks", conn).iloc[0]['c']
    open_tasks  = pd.read_sql("SELECT COUNT(*) as c FROM tasks WHERE status='open'", conn).iloc[0]['c']
    my_tasks    = pd.read_sql(f"SELECT COUNT(*) as c FROM tasks WHERE posted_by='{u[1]}'", conn).iloc[0]['c']
    my_score    = pd.read_sql(f"SELECT trust_score FROM users WHERE username='{u[1]}'", conn).iloc[0]['trust_score']
    conn.close()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("👥 Total Users",  total_users)
    c2.metric("📋 Total Tasks",  total_tasks)
    c3.metric("🟢 Open Tasks",   open_tasks)
    c4.metric("📌 My Tasks",     my_tasks)
    c5.metric("⭐ Trust Score",  f"{round(my_score,1)}/10")

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h3 style='color:#e5e7eb;'>📋 Recent Tasks</h3>", unsafe_allow_html=True)
        conn = get_connection()
        recent_tasks = pd.read_sql("""
            SELECT title, posted_by, required_skills, status
            FROM tasks ORDER BY created_at DESC LIMIT 6
        """, conn)
        conn.close()
        if not recent_tasks.empty:
            for _, row in recent_tasks.iterrows():
                status_html = f"<span class='status-open'>● open</span>" if row['status'] == 'open' else f"<span class='status-closed'>● closed</span>"
                st.markdown(f"""
                <div class='cs-card' style='padding:16px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <div style='color:#e5e7eb; font-weight:600; font-size:15px;'>{row['title']}</div>
                            <div style='color:#64748b; font-size:12px; margin-top:4px;'>by {row['posted_by']}</div>
                        </div>
                        {status_html}
                    </div>
                    <div style='margin-top:8px;'><span class='cs-badge'>🛠 {row['required_skills']}</span></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No tasks posted yet.")

    with col2:
        st.markdown("<h3 style='color:#e5e7eb;'>🏆 Top Users by Trust Score</h3>", unsafe_allow_html=True)
        conn = get_connection()
        top_users = pd.read_sql("""
            SELECT username, skills, trust_score, total_ratings
            FROM users ORDER BY trust_score DESC LIMIT 6
        """, conn)
        conn.close()
        if not top_users.empty:
            for i, row in top_users.iterrows():
                medal = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣"][i] if i < 6 else "👤"
                st.markdown(f"""
                <div class='cs-card' style='padding:16px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <div>
                            <div style='color:#e5e7eb; font-weight:600;'>{medal} {row['username']}</div>
                            <div style='color:#64748b; font-size:12px; margin-top:3px;'>{row['skills']}</div>
                        </div>
                        <div style='text-align:right;'>
                            <div style='color:#22d3ee; font-weight:800; font-size:18px;'>{round(row['trust_score'],1)}</div>
                            <div style='color:#64748b; font-size:11px;'>{row['total_ratings']} ratings</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No users yet.")

    # Quick actions
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3 style='color:#e5e7eb;'>⚡ Quick Actions</h3>", unsafe_allow_html=True)
    qa1, qa2, qa3, qa4 = st.columns(4)
    with qa1:
        if st.button("➕ Post a Task", use_container_width=True):
            st.session_state.page = "post_task"
            st.rerun()
    with qa2:
        if st.button("🔍 Browse Tasks", use_container_width=True):
            st.session_state.page = "browse_tasks"
            st.rerun()
    with qa3:
        if st.button("🤖 Find Matches", use_container_width=True):
            st.session_state.page = "ai_match"
            st.rerun()
    with qa4:
        if st.button("👤 My Profile", use_container_width=True):
            st.session_state.page = "profile"
            st.rerun()


# ================= POST TASK =================
def post_task():
    navbar()

    st.markdown("<div class='page-title'>📋 Post a Task</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Describe what you need help with and find the right collaborator</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<div class='cs-card'>", unsafe_allow_html=True)
        title    = st.text_input("Task Title", placeholder="e.g. Need a Python developer for data scraping")
        desc     = st.text_area("Task Description", height=150,
                                placeholder="Describe the task in detail — what needs to be done, goals, expected outcome...")
        skills   = st.text_input("Required Skills", placeholder="e.g. Python, BeautifulSoup, Pandas")
        deadline = st.text_input("Deadline (optional)", placeholder="e.g. Within 3 days")
        category = st.selectbox("Category", [
            "Development", "Design", "Marketing",
            "Content Writing", "Data Science",
            "Video Editing", "SEO", "Other"
        ])

        if st.button("Post Task 🚀", use_container_width=True):
            if title and desc and skills:
                conn = get_connection()
                conn.execute(
                    "INSERT INTO tasks (title, description, required_skills, posted_by) VALUES (?,?,?,?)",
                    (title, desc, f"{skills} [{category}]", st.session_state.user[1])
                )
                conn.commit()
                conn.close()
                st.success("✅ Task posted successfully! Others can now find and collaborate with you.")
                st.balloons()
            else:
                st.warning("Please fill Title, Description and Required Skills.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='cs-card'>
            <div style='color:#22d3ee; font-weight:700; font-size:16px; margin-bottom:14px;'>💡 Tips for a Great Post</div>
            <div style='color:#94a3b8; font-size:14px; line-height:1.8;'>
            ✅ Be specific about what you need<br>
            ✅ List exact skills required<br>
            ✅ Mention your deadline<br>
            ✅ Describe expected output<br>
            ✅ Keep title short and clear<br><br>
            <span style='color:#64748b; font-size:12px;'>Good posts attract better collaborators faster!</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # My recent tasks
        st.markdown("<div style='color:#e5e7eb; font-weight:700; margin-bottom:10px;'>📌 My Recent Posts</div>", unsafe_allow_html=True)
        conn = get_connection()
        my_tasks = pd.read_sql(f"""
            SELECT title, status FROM tasks
            WHERE posted_by='{st.session_state.user[1]}'
            ORDER BY created_at DESC LIMIT 4
        """, conn)
        conn.close()
        if not my_tasks.empty:
            for _, row in my_tasks.iterrows():
                s = "🟢" if row['status'] == 'open' else "🔴"
                st.markdown(f"<div style='color:#94a3b8; font-size:13px; padding:6px 0; border-bottom:1px solid #1e293b;'>{s} {row['title']}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#64748b; font-size:13px;'>No tasks posted yet</div>", unsafe_allow_html=True)


# ================= BROWSE TASKS =================
def browse_tasks():
    navbar()

    st.markdown("<div class='page-title'>🔍 Browse Tasks</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Find tasks that match your skills and start collaborating</div>", unsafe_allow_html=True)

    # Filters row
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        search = st.text_input("", placeholder="🔍 Search by keyword or skill...")
    with col2:
        filter_status = st.selectbox("Status", ["All", "Open", "Closed"])
    with col3:
        sort_by = st.selectbox("Sort By", ["Newest First", "Oldest First"])

    conn = get_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    if search:
        query += f" AND (title LIKE '%{search}%' OR required_skills LIKE '%{search}%' OR description LIKE '%{search}%')"
    if filter_status == "Open":
        query += " AND status='open'"
    elif filter_status == "Closed":
        query += " AND status='closed'"
    if sort_by == "Newest First":
        query += " ORDER BY created_at DESC"
    else:
        query += " ORDER BY created_at ASC"

    tasks = pd.read_sql(query, conn)
    conn.close()

    st.markdown(f"<div style='color:#64748b; font-size:13px; margin-bottom:16px;'>{len(tasks)} task(s) found</div>", unsafe_allow_html=True)

    if tasks.empty:
        st.markdown("""
        <div class='cs-card' style='text-align:center; padding:48px;'>
            <div style='font-size:48px;'>📭</div>
            <div style='color:#e5e7eb; font-weight:600; margin-top:12px;'>No tasks found</div>
            <div style='color:#64748b; margin-top:6px;'>Try a different search or be the first to post one!</div>
        </div>
        """, unsafe_allow_html=True)
        return

    for _, row in tasks.iterrows():
        status_color = "#22d3ee" if row['status'] == 'open' else "#f87171"
        status_bg    = "rgba(34,211,238,0.1)" if row['status'] == 'open' else "rgba(239,68,68,0.1)"

        with st.expander(f"📌  {row['title']}  —  posted by {row['posted_by']}"):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"<div style='color:#94a3b8; font-size:14px; line-height:1.7;'>{row['description']}</div>", unsafe_allow_html=True)
                st.markdown(f"<span class='cs-badge'>🛠 {row['required_skills']}</span>", unsafe_allow_html=True)
                st.markdown(f"<div style='color:#475569; font-size:12px; margin-top:10px;'>🕐 Posted: {row['created_at']}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div style='background:{status_bg}; border:1px solid {status_color}; border-radius:10px;
                            padding:12px; text-align:center;'>
                    <div style='color:{status_color}; font-weight:700; font-size:14px;'>● {row['status'].upper()}</div>
                </div>
                """, unsafe_allow_html=True)

                # Mark as closed (only task owner)
                if row['posted_by'] == st.session_state.user[1] and row['status'] == 'open':
                    if st.button("Mark Closed", key=f"close_{row['id']}"):
                        conn = get_connection()
                        conn.execute("UPDATE tasks SET status='closed' WHERE id=?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()


# ================= AI MATCH =================
def ai_match():
    navbar()

    st.markdown("<div class='page-title'>🤖 AI Skill Matching</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Describe your task and let AI find the perfect collaborators</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("<div class='cs-card'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#22d3ee; font-weight:700; font-size:16px; margin-bottom:16px;'>🔍 Describe Your Task</div>", unsafe_allow_html=True)

        task_title = st.text_input("Task Title", placeholder="e.g. Build a landing page for my startup")
        task_desc  = st.text_area("Task Description", height=130,
                                   placeholder="Describe what you need in detail...")
        skills     = st.text_input("Skills Needed", placeholder="e.g. React, CSS, Figma")

        if st.button("🤖 Find Best Matches with AI", use_container_width=True):
            if task_title and task_desc and skills:
                with st.spinner("🤖 AI is analyzing all profiles... please wait"):
                    try:
                        matches = match_users_to_task(
                            task_title, task_desc, skills,
                            st.session_state.user[1]
                        )
                        st.session_state.ai_matches = matches
                        st.session_state.ai_searched = True
                    except Exception as e:
                        st.error(f"AI Error: {str(e)}")
                        st.session_state.ai_searched = False
            else:
                st.warning("Please fill all three fields.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class='cs-card'>
            <div style='color:#22d3ee; font-weight:700; font-size:15px; margin-bottom:12px;'>⚡ How AI Matching Works</div>
            <div style='color:#94a3b8; font-size:13px; line-height:1.9;'>
            1️⃣ You describe your task<br>
            2️⃣ AI reads all user profiles<br>
            3️⃣ Compares skills & experience<br>
            4️⃣ Considers trust scores<br>
            5️⃣ Returns top 3 best matches<br>
            6️⃣ You connect & collaborate!
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Also match from existing open tasks
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='color:#e5e7eb; font-weight:600; margin-bottom:8px;'>📋 Or match from your open tasks</div>", unsafe_allow_html=True)
        conn = get_connection()
        my_open = pd.read_sql(f"""
            SELECT id, title, required_skills FROM tasks
            WHERE posted_by='{st.session_state.user[1]}' AND status='open'
        """, conn)
        conn.close()
        if not my_open.empty:
            selected = st.selectbox("Select your task", my_open['title'].tolist())
            if st.button("Auto-fill from task"):
                task_row = my_open[my_open['title'] == selected].iloc[0]
                st.session_state.autofill_title  = task_row['title']
                st.session_state.autofill_skills = task_row['required_skills']
                st.rerun()
        else:
            st.markdown("<div style='color:#64748b; font-size:13px;'>No open tasks found</div>", unsafe_allow_html=True)

    # Show results
    if st.session_state.get("ai_searched") and st.session_state.get("ai_matches"):
        matches = st.session_state.ai_matches
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:#22d3ee; font-weight:700; font-size:20px; margin-bottom:16px;'>✅ Found {len(matches)} Best Matches</div>", unsafe_allow_html=True)

        for i, m in enumerate(matches, 1):
            medal = ["🥇","🥈","🥉"][i-1] if i <= 3 else "👤"
            score_color = "#22d3ee" if m['match_score'] >= 80 else "#f59e0b" if m['match_score'] >= 60 else "#f87171"

            # Fetch user details
            conn = get_connection()
            user_row = pd.read_sql(f"SELECT * FROM users WHERE username='{m['username']}'", conn)
            conn.close()

            skills_display = user_row.iloc[0]['skills'] if not user_row.empty else "N/A"
            trust          = user_row.iloc[0]['trust_score'] if not user_row.empty else "N/A"

            st.markdown(f"""
            <div class='match-card'>
                <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
                    <div>
                        <div style='color:#e5e7eb; font-size:20px; font-weight:800;'>{medal} {m['username']}</div>
                        <div style='margin-top:6px;'><span class='cs-badge'>🛠 {skills_display}</span></div>
                        <div style='color:#94a3b8; font-size:13px; margin-top:10px; max-width:500px; line-height:1.6;'>{m['reason']}</div>
                    </div>
                    <div style='text-align:center; min-width:90px;'>
                        <div style='color:{score_color}; font-size:32px; font-weight:900;'>{m['match_score']}%</div>
                        <div style='color:#64748b; font-size:11px;'>Match Score</div>
                        <div style='color:#22d3ee; font-size:16px; font-weight:700; margin-top:6px;'>⭐ {round(float(trust),1)}</div>
                        <div style='color:#64748b; font-size:11px;'>Trust Score</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    elif st.session_state.get("ai_searched"):
        st.warning("No matches found. Ask more people to register on the platform!")


# ================= PROFILE =================
def profile():
    navbar()
    u = st.session_state.user

    st.markdown("<div class='page-title'>👤 My Profile</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Your public profile and activity</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown(f"""
        <div class='cs-card' style='text-align:center;'>
            <div style='font-size:64px; margin-bottom:12px;'>👤</div>
            <div style='color:#e5e7eb; font-size:22px; font-weight:800;'>{u[1]}</div>
            <div style='color:#64748b; font-size:13px; margin-top:4px;'>{u[2]}</div>
            <div style='margin-top:16px;'>
                <span class='cs-badge'>⭐ Trust: {round(u[8],1)}/10</span>
                <span class='cs-badge'>📊 {u[9]} ratings</span>
            </div>
            <div style='margin-top:16px; color:#94a3b8; font-size:13px; line-height:1.6;'>{u[5] or 'No bio added yet.'}</div>
            <div style='margin-top:16px;'>
                {'<a href="' + u[6] + '" style="color:#22d3ee; font-size:13px;">🔗 View Portfolio</a>' if u[6] else '<span style="color:#475569; font-size:13px;">No portfolio link</span>'}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Skills
        st.markdown("<div class='cs-card' style='margin-top:0;'>", unsafe_allow_html=True)
        st.markdown("<div style='color:#e5e7eb; font-weight:700; margin-bottom:12px;'>🛠 My Skills</div>", unsafe_allow_html=True)
        if u[4]:
            for skill in u[4].split(","):
                st.markdown(f"<span class='cs-badge'>{skill.strip()}</span>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # My tasks
        st.markdown("<h3 style='color:#e5e7eb;'>📋 My Posted Tasks</h3>", unsafe_allow_html=True)
        conn = get_connection()
        my_tasks = pd.read_sql(f"""
            SELECT title, required_skills, status, created_at
            FROM tasks WHERE posted_by='{u[1]}'
            ORDER BY created_at DESC
        """, conn)
        conn.close()

        if not my_tasks.empty:
            for _, row in my_tasks.iterrows():
                s_color = "#22d3ee" if row['status'] == 'open' else "#f87171"
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <div>
                            <div style='color:#e5e7eb; font-weight:600;'>{row['title']}</div>
                            <span class='cs-badge'>🛠 {row['required_skills']}</span>
                        </div>
                        <div style='color:{s_color}; font-size:12px; font-weight:700;'>● {row['status'].upper()}</div>
                    </div>
                    <div style='color:#475569; font-size:11px; margin-top:8px;'>🕐 {row['created_at']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#64748b;'>No tasks posted yet.</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Feedback received
        st.markdown("<h3 style='color:#e5e7eb;'>⭐ Feedback Received</h3>", unsafe_allow_html=True)
        conn = get_connection()
        feedbacks = pd.read_sql(f"""
            SELECT from_user, rating, comment, created_at
            FROM feedback WHERE to_user='{u[1]}'
            ORDER BY created_at DESC LIMIT 5
        """, conn)
        conn.close()

        if not feedbacks.empty:
            for _, row in feedbacks.iterrows():
                stars = "⭐" * int(row['rating'])
                st.markdown(f"""
                <div class='cs-card' style='padding:14px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <div style='color:#e5e7eb; font-weight:600;'>👤 {row['from_user']}</div>
                        <div>{stars}</div>
                    </div>
                    <div style='color:#94a3b8; font-size:13px; margin-top:6px;'>{row['comment'] or 'No comment left.'}</div>
                    <div style='color:#475569; font-size:11px; margin-top:6px;'>🕐 {row['created_at']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#64748b;'>No feedback received yet.</div>", unsafe_allow_html=True)


# ================= FEEDBACK =================
def feedback():
    navbar()

    st.markdown("<div class='page-title'>⭐ Give Feedback</div>", unsafe_allow_html=True)
    st.markdown("<div class='page-sub'>Rate someone you collaborated with and help build community trust</div>", unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("<div class='cs-card'>", unsafe_allow_html=True)

        conn = get_connection()
        users_df = pd.read_sql(
            f"SELECT username, skills, trust_score FROM users WHERE username != '{st.session_state.user[1]}'",
            conn
        )
        conn.close()

        if users_df.empty:
            st.info("No other users to rate yet.")
            return

        to_user = st.selectbox("Select a collaborator to rate", users_df['username'].tolist())
        rating  = st.slider("Your Rating", 1, 5, 4,
                             help="1 = Poor, 2 = Fair, 3 = Good, 4 = Great, 5 = Excellent")
        comment = st.text_area("Write a comment (optional)", placeholder="Share your experience working with this person...")

        # Star preview
        stars_preview = "⭐" * rating
        st.markdown(f"<div style='color:#f59e0b; font-size:24px; margin: 8px 0;'>{stars_preview}</div>", unsafe_allow_html=True)

        if st.button("Submit Feedback ✅", use_container_width=True):
            # Check if already reviewed
            conn = get_connection()
            existing = pd.read_sql(f"""
                SELECT id FROM feedback
                WHERE from_user='{st.session_state.user[1]}' AND to_user='{to_user}'
            """, conn)

            if not existing.empty:
                st.warning("You have already submitted feedback for this user.")
            else:
                conn.execute(
                    "INSERT INTO feedback (from_user, to_user, rating, comment) VALUES (?,?,?,?)",
                    (st.session_state.user[1], to_user, rating, comment)
                )
                conn.commit()
                update_trust_score(to_user, rating * 2)
                st.success(f"✅ Feedback submitted for {to_user}! Their trust score has been updated.")
                st.balloons()
            conn.close()

        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Show selected user's current profile
        if not users_df.empty:
            selected_user = users_df[users_df['username'] == to_user].iloc[0]
            st.markdown(f"""
            <div class='cs-card' style='text-align:center;'>
                <div style='font-size:48px;'>👤</div>
                <div style='color:#e5e7eb; font-weight:700; font-size:18px; margin-top:10px;'>{selected_user['username']}</div>
                <div style='margin-top:8px;'><span class='cs-badge'>🛠 {selected_user['skills']}</span></div>
                <div style='margin-top:14px;'>
                    <div style='color:#22d3ee; font-size:28px; font-weight:900;'>{round(selected_user['trust_score'],1)}</div>
                    <div style='color:#64748b; font-size:12px;'>Current Trust Score</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        # All feedbacks given by me
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<div style='color:#e5e7eb; font-weight:700; margin-bottom:10px;'>📝 My Given Feedback</div>", unsafe_allow_html=True)
        conn = get_connection()
        given = pd.read_sql(f"""
            SELECT to_user, rating, comment FROM feedback
            WHERE from_user='{st.session_state.user[1]}'
            ORDER BY created_at DESC LIMIT 4
        """, conn)
        conn.close()
        if not given.empty:
            for _, row in given.iterrows():
                stars = "⭐" * int(row['rating'])
                st.markdown(f"""
                <div style='background:#0f172a; border:1px solid #1e293b; border-radius:10px;
                            padding:12px; margin-bottom:8px;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <div style='color:#e5e7eb; font-size:13px; font-weight:600;'>→ {row['to_user']}</div>
                        <div style='font-size:12px;'>{stars}</div>
                    </div>
                    <div style='color:#64748b; font-size:12px; margin-top:4px;'>{row['comment'] or '—'}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color:#64748b; font-size:13px;'>You haven't given any feedback yet.</div>", unsafe_allow_html=True)


# ================= ROUTING =================
if st.session_state.page == "landing":
    landing()
elif st.session_state.page == "login":
    login()
elif st.session_state.page == "register":
    register()
elif st.session_state.page == "dashboard":
    if st.session_state.user:
        dashboard()
    else:
        st.session_state.page = "login"
        st.rerun()
elif st.session_state.page == "post_task":
    if st.session_state.user:
        post_task()
    else:
        st.session_state.page = "login"
        st.rerun()
elif st.session_state.page == "browse_tasks":
    if st.session_state.user:
        browse_tasks()
    else:
        st.session_state.page = "login"
        st.rerun()
elif st.session_state.page == "ai_match":
    if st.session_state.user:
        ai_match()
    else:
        st.session_state.page = "login"
        st.rerun()
elif st.session_state.page == "profile":
    if st.session_state.user:
        profile()
    else:
        st.session_state.page = "login"
        st.rerun()
elif st.session_state.page == "feedback":
    if st.session_state.user:
        feedback()
    else:
        st.session_state.page = "login"
        st.rerun()
