import streamlit as st
from database import init_db, get_connection
from auth import register_user, login_user

init_db()
st.set_page_config(layout="wide")

# ================= SESSION =================
if "page" not in st.session_state:
    st.session_state.page = "landing"

if "user" not in st.session_state:
    st.session_state.user = None

# ================= CSS (UNCHANGED FROM YOUR FILE) =================
st.markdown("""<style>
header, #MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 0rem;}
.stApp {background-color: #050816;}

.center {text-align: center; margin-top: 80px;}

.light {color: #e5e7eb; font-size: 85px; font-weight: 900;}
.gradient {
    font-size: 85px; font-weight: 900;
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}
.sub {color: #94a3b8; text-align: center;}

.stTextInput input, .stTextArea textarea {
    background-color: #1f2937 !important;
    color: white !important;
}
label {color: white !important;}

.stButton>button {
    background: linear-gradient(90deg,#22d3ee,#7c3aed);
    color: white;
    border-radius: 10px;
}

/* DASHBOARD TEXT FIX */
.title {color:#22d3ee;font-size:32px;font-weight:700;}
.card {
    background:#0f172a;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
    color:white;
}
</style>""", unsafe_allow_html=True)

# ================= NAVBAR =================
def navbar():
    col1, col2 = st.columns([6,4])

    with col1:
        st.markdown("<h3 style='color:#e5e7eb;'>🚀 CollabSkill AI</h3>", unsafe_allow_html=True)

    with col2:
        c1, c2, c3, c4, c5 = st.columns(5)

        if c1.button("Dashboard"):
            st.session_state.page = "dashboard"; st.rerun()
        if c2.button("Post"):
            st.session_state.page = "post"; st.rerun()
        if c3.button("Browse"):
            st.session_state.page = "browse"; st.rerun()
        if c4.button("Profile"):
            st.session_state.page = "profile"; st.rerun()
        if c5.button("Logout"):
            st.session_state.user = None
            st.session_state.page = "landing"
            st.rerun()

# ================= LANDING =================
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

    st.markdown('<div class="sub">AI-powered skill exchange platform</div>', unsafe_allow_html=True)

# ================= LOGIN =================
def login():
    left, center, right = st.columns([1,2,1])

    with center:
        st.markdown("<div style='background:#0f172a;padding:40px;border-radius:15px;'>", unsafe_allow_html=True)

        st.markdown("<h2 style='color:white;text-align:center;'>Login</h2>", unsafe_allow_html=True)

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
    st.markdown("<h1 style='color:white;'>Create Profile</h1>", unsafe_allow_html=True)

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    skills = st.text_input("Skills")
    bio = st.text_area("Bio")

    if st.button("Register"):
        success, msg = register_user(username, email, password, skills, bio, "")
        if success:
            st.success("Account created")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error(msg)

# ================= DASHBOARD =================
def dashboard():
    navbar()

    st.markdown(f"<div class='title'>Welcome {st.session_state.user}</div>", unsafe_allow_html=True)

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, description FROM tasks")
    tasks = c.fetchall()
    conn.close()

    for t in tasks:
        st.markdown(f"<div class='card'><b>{t[0]}</b><br>{t[1]}</div>", unsafe_allow_html=True)

# ================= POST =================
def post():
    navbar()
    st.markdown("<h2 style='color:white;'>Post a Task</h2>", unsafe_allow_html=True)

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
        st.success("Task Posted!")

# ================= BROWSE =================
def browse():
    navbar()
    st.markdown("<h2 style='color:white;'>Browse Tasks</h2>", unsafe_allow_html=True)

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()
    conn.close()

    for t in tasks:
        st.markdown(f"<div class='card'><b>{t[1]}</b><br>{t[2]}<br>Skills: {t[3]}</div>", unsafe_allow_html=True)

# ================= PROFILE =================
def profile():
    navbar()

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (st.session_state.user,))
    user = c.fetchone()
    conn.close()

    st.markdown("<h2 style='color:white;'>Profile</h2>", unsafe_allow_html=True)

    if user:
        st.write("Username:", user[1])
        st.write("Email:", user[2])
        st.write("Skills:", user[4])
        st.write("Bio:", user[5])

# ================= ROUTER =================
if st.session_state.user:
    if st.session_state.page == "dashboard":
        dashboard()
    elif st.session_state.page == "post":
        post()
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
