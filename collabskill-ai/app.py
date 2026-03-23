import streamlit as st
from database import init_db, get_connection
from auth import register_user, login_user

init_db()
st.set_page_config(layout="wide")

# SESSION
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user" not in st.session_state:
    st.session_state.user = None

# ================= GLOBAL CSS (UNCHANGED) =================
st.markdown("""
<style>
header, #MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 0rem;}

.stApp { background-color: #050816; }

.center { text-align: center; margin-top: 80px; }

.light {
    color: #e5e7eb;
    font-size: 85px;
    font-weight: 900;
    line-height: 1.1;
}

.gradient {
    font-size: 85px;
    font-weight: 900;
    line-height: 1.1;
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}

.sub {
    color: #94a3b8;
    font-size: 18px;
    text-align: center;
    margin-top: 20px;
}

.stTextInput input, .stTextArea textarea {
    background-color: #1f2937 !important;
    color: white !important;
    border: 1px solid #374151 !important;
}

label { color: #ffffff !important; }

.stButton>button {
    background: linear-gradient(90deg,#22d3ee,#7c3aed);
    color: white;
    border-radius: 10px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

# ================= NAVBAR (NEW - MINIMAL, DOESN'T BREAK UI) =================
def navbar():
    col1, col2 = st.columns([6,4])

    with col1:
        st.markdown("<h3 style='color:#e5e7eb;'>🚀 CollabSkill AI</h3>", unsafe_allow_html=True)

    with col2:
        c1, c2, c3, c4, c5 = st.columns(5)

        if c1.button("Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

        if c2.button("Post"):
            st.session_state.page = "post"
            st.rerun()

        if c3.button("Browse"):
            st.session_state.page = "browse"
            st.rerun()

        if c4.button("Profile"):
            st.session_state.page = "profile"
            st.rerun()

        if c5.button("Logout"):
            st.session_state.user = None
            st.session_state.page = "landing"
            st.rerun()

# ================= LANDING (UNCHANGED) =================
def landing():

    col1, col2 = st.columns([8,2])

    with col1:
        st.markdown("<h3 style='color:#e5e7eb;'>🚀 CollabSkill AI</h3>", unsafe_allow_html=True)

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
        'An intelligent platform that matches you with the right people — using AI.'
        '</div>',
        unsafe_allow_html=True
    )

# ================= LOGIN =================
def login():
    left, center, right = st.columns([1,2,1])

    with center:
        st.markdown("<div style='background:#0f172a;padding:40px;border-radius:15px;'>", unsafe_allow_html=True)

        st.markdown("<h2 style='text-align:center;color:#e5e7eb;'>Login</h2>", unsafe_allow_html=True)

        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.session_state.user = username
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Invalid credentials")

        if st.button("Create Account"):
            st.session_state.page = "register"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ================= REGISTER =================
def register():
    st.markdown("<h1 style='color:#e5e7eb;'>Create Your Profile</h1>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

    with col2:
        skills = st.text_input("Skills")
        portfolio = st.text_input("Portfolio")

    bio = st.text_area("Bio")

    if st.button("Create Account"):
        success, msg = register_user(username, email, password, skills, bio, portfolio)
        if success:
            st.success("Account created")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error(msg)

# ================= DASHBOARD =================
def dashboard():
    navbar()

    st.markdown(f"<h2 style='color:#22d3ee;'>Welcome {st.session_state.user}</h2>", unsafe_allow_html=True)

    st.write("🚀 Explore tasks and collaborate")

# ================= POST TASK =================
def post_task():
    navbar()

    st.markdown("### Post a Task")

    title = st.text_input("Task Title")
    desc = st.text_area("Description")
    skills = st.text_input("Skills")

    if st.button("Post"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO tasks (title, description, skills, posted_by) VALUES (?,?,?,?)",
                  (title, desc, skills, st.session_state.user))
        conn.commit()
        conn.close()
        st.success("Task Posted")

# ================= BROWSE =================
def browse():
    navbar()

    st.markdown("### Browse Tasks")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, description, skills, posted_by FROM tasks")
    tasks = c.fetchall()
    conn.close()

    for t in tasks:
        st.markdown(f"""
        <div style="background:#0f172a;padding:20px;border-radius:10px;margin-bottom:10px;">
        <b>{t[0]}</b><br>{t[1]}<br>
        Skills: {t[2]}<br>
        By: {t[3]}
        </div>
        """, unsafe_allow_html=True)

# ================= PROFILE =================
def profile():
    navbar()

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (st.session_state.user,))
    user = c.fetchone()
    conn.close()

    st.markdown("### My Profile")

    if user:
        st.write("Username:", user[1])
        st.write("Email:", user[2])
        st.write("Skills:", user[4])
        st.write("Bio:", user[5])

# ================= ROUTING =================
if st.session_state.user:
    if st.session_state.page == "dashboard":
        dashboard()
    elif st.session_state.page == "post":
        post_task()
    elif st.session_state.page == "browse":
        browse()
    elif st.session_state.page == "profile":
        profile()
else:
    if st.session_state.page == "landing":
        landing()
    elif st.session_state.page == "login":
        login()
    elif st.session_state.page == "register":
        register()
