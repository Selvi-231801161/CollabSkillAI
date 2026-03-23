import streamlit as st
import pandas as pd
from database import init_db, get_connection
from auth import register_user, login_user, update_trust_score
from ai_matching import match_users_to_task

# ── Initialize database ──
init_db()

# ── Page config ──
st.set_page_config(
    page_title="CollabSkill AI",
    page_icon="🚀",
    layout="wide"
)

# ── Styling ──
st.markdown("""
<style>
body { background-color: #0a0f1e; }
.big-title { font-size: 2.2rem; font-weight: 800; color: #00e5ff; margin-bottom: 8px; }
.sub-text  { color: #64748b; font-size: 1rem; margin-bottom: 24px; }
.card      { background: #111827; border-radius: 12px; padding: 20px;
             border: 1px solid #1f2937; margin-bottom: 14px; }
.skill-tag { background: #00e5ff22; color: #00e5ff; border-radius: 20px;
             padding: 3px 12px; font-size: 0.8rem; display: inline-block; }
</style>
""", unsafe_allow_html=True)

# ── Session state ──
if "user" not in st.session_state:
    st.session_state.user = None

# ════════════════════════════
#   SIDEBAR
# ════════════════════════════
with st.sidebar:
    st.markdown("## 🚀 CollabSkill AI")
    st.markdown("*AI-Powered Skill Exchange*")
    st.divider()

    if st.session_state.user is None:
        page = st.radio("", ["🔐 Login", "📝 Register"])
    else:
        u = st.session_state.user
        st.success(f"👤 {u[1]}")
        st.markdown(f"⭐ Trust Score: **{u[8]}/10**")
        st.divider()
        page = st.radio("Go to", [
            "🏠 Dashboard",
            "👤 My Profile",
            "📋 Post a Task",
            "🔍 Browse Tasks",
            "🤖 AI Match",
            "⭐ Give Feedback"
        ])
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.rerun()

# ════════════════════════════
#   LOGIN PAGE
# ════════════════════════════
def show_login():
    st.markdown('<div class="big-title">Welcome Back 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Login to your CollabSkill account</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1])
    with col1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login →", use_container_width=True):
            if username and password:
                user = login_user(username, password)
                if user:
                    st.session_state.user = user
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Wrong username or password.")
            else:
                st.warning("Please fill both fields.")

# ════════════════════════════
#   REGISTER PAGE
# ════════════════════════════
def show_register():
    st.markdown('<div class="big-title">Create Account 🚀</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Join the skill exchange community</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        username  = st.text_input("Choose a Username")
        email     = st.text_input("Email Address")
        password  = st.text_input("Create Password", type="password")
    with col2:
        skills    = st.text_input("Your Skills (e.g. Python, UI Design, SEO)")
        bio       = st.text_area("Short Bio — tell people about yourself", height=100)
        portfolio = st.text_input("Portfolio / GitHub Link (optional)")

    if st.button("Create My Account", use_container_width=True):
        if username and email and password and skills:
            success, msg = register_user(username, email, password, skills, bio, portfolio)
            if success:
                st.success(msg + " Now go to Login.")
            else:
                st.error(msg)
        else:
            st.warning("Please fill all required fields.")

# ════════════════════════════
#   DASHBOARD PAGE
# ════════════════════════════
def show_dashboard():
    u = st.session_state.user
    st.markdown(f'<div class="big-title">Hello, {u[1]}! 👋</div>', unsafe_allow_html=True)

    conn = get_connection()
    total_users = pd.read_sql("SELECT COUNT(*) as c FROM users", conn).iloc[0]['c']
    total_tasks = pd.read_sql("SELECT COUNT(*) as c FROM tasks", conn).iloc[0]['c']
    open_tasks  = pd.read_sql("SELECT COUNT(*) as c FROM tasks WHERE status='open'", conn).iloc[0]['c']
    my_tasks    = pd.read_sql(f"SELECT COUNT(*) as c FROM tasks WHERE posted_by='{u[1]}'", conn).iloc[0]['c']
    conn.close()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Total Users",  total_users)
    col2.metric("📋 Total Tasks",  total_tasks)
    col3.metric("🟢 Open Tasks",   open_tasks)
    col4.metric("📌 My Tasks",     my_tasks)

    st.divider()
    st.subheader("📋 Recent Tasks")
    conn = get_connection()
    recent = pd.read_sql("SELECT title, posted_by, required_skills, status, created_at FROM tasks ORDER BY created_at DESC LIMIT 5", conn)
    conn.close()
    if not recent.empty:
        st.dataframe(recent, use_container_width=True, hide_index=True)
    else:
        st.info("No tasks posted yet. Be the first!")

# ════════════════════════════
#   MY PROFILE PAGE
# ════════════════════════════
def show_profile():
    u = st.session_state.user
    st.markdown('<div class="big-title">👤 My Profile</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Username:** {u[1]}")
        st.markdown(f"**Email:** {u[2]}")
        st.markdown(f"**Skills:** {u[4]}")
        st.markdown(f"**Bio:** {u[5]}")
    with col2:
        st.markdown(f"**Portfolio:** {u[6] or 'Not added'}")
        st.markdown(f"**Trust Score:** ⭐ {u[8]}/10")
        st.markdown(f"**Total Ratings:** {u[9]}")

    st.divider()
    st.subheader("My Posted Tasks")
    conn = get_connection()
    my_tasks = pd.read_sql(f"SELECT title, required_skills, status, created_at FROM tasks WHERE posted_by='{u[1]}' ORDER BY created_at DESC", conn)
    conn.close()
    if not my_tasks.empty:
        st.dataframe(my_tasks, use_container_width=True, hide_index=True)
    else:
        st.info("You haven't posted any tasks yet.")

# ════════════════════════════
#   POST A TASK PAGE
# ════════════════════════════
def show_post_task():
    st.markdown('<div class="big-title">📋 Post a Task</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Describe what you need help with</div>', unsafe_allow_html=True)

    title  = st.text_input("Task Title", placeholder="e.g. Need a Python developer for data scraping")
    desc   = st.text_area("Task Description", height=150,
                           placeholder="Describe the task in detail — what needs to be done, goals, timeline...")
    skills = st.text_input("Required Skills", placeholder="e.g. Python, BeautifulSoup, Pandas")

    if st.button("Post Task 🚀", use_container_width=True):
        if title and desc and skills:
            conn = get_connection()
            conn.execute(
                "INSERT INTO tasks (title, description, required_skills, posted_by) VALUES (?,?,?,?)",
                (title, desc, skills, st.session_state.user[1])
            )
            conn.commit()
            conn.close()
            st.success("✅ Task posted! Others can now find and collaborate with you.")
            st.balloons()
        else:
            st.warning("Please fill all fields before posting.")

# ════════════════════════════
#   BROWSE TASKS PAGE
# ════════════════════════════
def show_browse_tasks():
    st.markdown('<div class="big-title">🔍 Browse Open Tasks</div>', unsafe_allow_html=True)

    search = st.text_input("Search tasks by keyword or skill")

    conn = get_connection()
    if search:
        tasks = pd.read_sql(f"""
            SELECT * FROM tasks
            WHERE status='open'
            AND (title LIKE '%{search}%'
            OR required_skills LIKE '%{search}%'
            OR description LIKE '%{search}%')
            ORDER BY created_at DESC
        """, conn)
    else:
        tasks = pd.read_sql("SELECT * FROM tasks WHERE status='open' ORDER BY created_at DESC", conn)
    conn.close()

    if tasks.empty:
        st.info("No open tasks found.")
        return

    st.markdown(f"**{len(tasks)} task(s) found**")

    for _, row in tasks.iterrows():
        with st.expander(f"📌 {row['title']}  —  posted by **{row['posted_by']}**"):
            st.write(row['description'])
            st.markdown(f'<span class="skill-tag">🛠 {row["required_skills"]}</span>', unsafe_allow_html=True)
            st.caption(f"Posted on: {row['created_at']}")

# ════════════════════════════
#   AI MATCH PAGE
# ════════════════════════════
def show_ai_match():
    st.markdown('<div class="big-title">🤖 AI Skill Matching</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Describe your task — AI will find the best collaborators</div>', unsafe_allow_html=True)

    task_title = st.text_input("Task Title")
    task_desc  = st.text_area("Task Description", height=120)
    skills     = st.text_input("Skills needed")

    if st.button("🔍 Find Best Matches", use_container_width=True):
        if task_title and task_desc and skills:
            with st.spinner("🤖 AI is analyzing all profiles..."):
                matches = match_users_to_task(
                    task_title, task_desc, skills,
                    st.session_state.user[1]
                )
            if not matches:
                st.warning("No matches found yet. Ask more people to register!")
            else:
                st.success(f"✅ Found {len(matches)} best matches!")
                for i, m in enumerate(matches, 1):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.subheader(f"#{i} — {m['username']}")
                        st.write(m['reason'])
                    with col2:
                        st.metric("Match Score", f"{m['match_score']}%")
                    st.divider()
        else:
            st.warning("Fill all three fields to get AI matches.")

# ════════════════════════════
#   FEEDBACK PAGE
# ════════════════════════════
def show_feedback():
    st.markdown('<div class="big-title">⭐ Give Feedback</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-text">Rate someone you collaborated with</div>', unsafe_allow_html=True)

    conn = get_connection()
    users_df = pd.read_sql(
        f"SELECT username FROM users WHERE username != '{st.session_state.user[1]}'", conn)
    conn.close()

    if users_df.empty:
        st.info("No other users to rate yet.")
        return

    to_user = st.selectbox("Select user to rate", users_df['username'].tolist())
    rating  = st.slider("Rating (1 = Poor, 5 = Excellent)", 1, 5, 4)
    comment = st.text_area("Write a comment (optional)")

    if st.button("Submit Feedback ✅", use_container_width=True):
        conn = get_connection()
        conn.execute(
            "INSERT INTO feedback (from_user, to_user, rating, comment) VALUES (?,?,?,?)",
            (st.session_state.user[1], to_user, rating, comment)
        )
        conn.commit()
        conn.close()
        update_trust_score(to_user, rating * 2)
        st.success(f"Feedback submitted for {to_user}! Their trust score has been updated.")

# ════════════════════════════
#   PAGE ROUTER
# ════════════════════════════
if st.session_state.user is None:
    if page == "🔐 Login":
        show_login()
    else:
        show_register()
else:
    if   page == "🏠 Dashboard":    show_dashboard()
    elif page == "👤 My Profile":   show_profile()
    elif page == "📋 Post a Task":  show_post_task()
    elif page == "🔍 Browse Tasks": show_browse_tasks()
    elif page == "🤖 AI Match":     show_ai_match()
    elif page == "⭐ Give Feedback": show_feedback()


## ▶️ PHASE 8 — Run Your App

1. Open **Command Prompt**
2. Navigate to your folder:
```
cd Desktop\collabskill-ai
```
3. Run the app:
```
streamlit run app.py
```
4. Your browser will automatically open at `http://localhost:8501` 🎉

---

## 🔁 Daily Workflow (How to work with IDLE)

Every time you want to work on the project:
```
1. Open Command Prompt → cd Desktop\collabskill-ai
2. Edit any file → right-click → Edit with IDLE → save with Ctrl+S
3. Run → streamlit run app.py in Command Prompt
4. See changes live in browser
