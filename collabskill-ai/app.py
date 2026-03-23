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

# ================= ORIGINAL UI (UNCHANGED) =================
st.markdown("""
<style>
header, #MainMenu, footer {visibility: hidden;}
.block-container {padding-top: 0rem;}

.stApp {
    background-color: #050816;
}

/* HERO TEXT */
.light-text {
    font-size: 85px;
    font-weight: 900;
    color: #e5e7eb;
}

.gradient {
    font-size: 85px;
    font-weight: 900;
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}

.subtext {
    color: #94a3b8;
    text-align: center;
}

/* INPUT */
.stTextInput input, .stTextArea textarea {
    background-color: #1f2937 !important;
    color: white !important;
}

/* FIX LABEL VISIBILITY */
label, .stCheckbox label {
    color: white !important;
}

/* BUTTON STYLE */
.stButton>button {
    background: linear-gradient(90deg,#22d3ee,#7c3aed);
    color: white !important;
    border-radius: 8px;
    font-weight: 600;
}

/* TASK CARD */
.card {
    background:#0f172a;
    padding:20px;
    border-radius:12px;
    margin-bottom:15px;
}
</style>
""", unsafe_allow_html=True)

# ================= NAVBAR =================
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

    st.markdown("""
    <div style='text-align:center;margin-top:80px;'>
        <div class="light-text">Connect.<br>Collaborate.</div>
        <div class="gradient">Exchange Skills</div>
        <div class="gradient">Smarter.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<p class='subtext'>AI-powered collaboration platform</p>", unsafe_allow_html=True)

# ================= LOGIN =================
def login():
    col1, col2, col3 = st.columns([2,3,2])

    with col2:
        st.markdown("<h1 style='color:white;text-align:center;'>Login</h1>", unsafe_allow_html=True)

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

        st.markdown("<p style='color:white;'>Don't have an account?</p>", unsafe_allow_html=True)

        if st.button("Create Account"):
            st.session_state.page = "register"
            st.rerun()

# ================= REGISTER =================
def register():
    st.markdown("<h1 style='color:white;'>Create Account</h1>", unsafe_allow_html=True)

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    skills = st.text_input("Skills")
    bio = st.text_area("Bio")
    portfolio = st.text_input("Portfolio")

    agree = st.checkbox("I agree to Terms & Conditions")

    if st.button("Register"):
        if not agree:
            st.warning("Accept terms")
        else:
            success, msg = register_user(username, email, password, skills, bio, portfolio)
            if success:
                st.success("Registered successfully")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(msg)

# ================= DASHBOARD =================
def dashboard():
    navbar()

    st.markdown(f"<h2 style='color:#22d3ee;'>Welcome {st.session_state.user}</h2>", unsafe_allow_html=True)

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, description FROM tasks")
    tasks = c.fetchall()
    conn.close()

    if not tasks:
        st.info("No tasks yet. Post one!")
    else:
        for t in tasks:
            st.markdown(f"""
            <div class="card">
            <b>{t[0]}</b><br>
            {t[1]}
            </div>
            """, unsafe_allow_html=True)

# ================= POST =================
def post_task():
    navbar()

    st.markdown("### Post Task")

    title = st.text_input("Title")
    desc = st.text_area("Description")
    skills = st.text_input("Skills")

    if st.button("Post"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO tasks (title, description, skills, posted_by) VALUES (?,?,?,?)",
                  (title, desc, skills, st.session_state.user))
        conn.commit()
        conn.close()

        st.success("Posted!")

# ================= BROWSE =================
def browse():
    navbar()

    st.markdown("### Browse Tasks")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()
    conn.close()

    for t in tasks:
        st.markdown(f"""
        <div class="card">
        <b>{t[1]}</b><br>
        {t[2]}<br>
        Skills: {t[3]}
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

    st.markdown("### Profile")

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
