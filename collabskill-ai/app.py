import streamlit as st
from database import init_db
from auth import register_user, login_user

init_db()

st.set_page_config(layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "landing"

if "section" not in st.session_state:
    st.session_state.section = "home"

# ================= CSS =================
st.markdown("""
<style>

/* BACKGROUND */
.stApp {
    background-color: #050816;
}

/* REMOVE PADDING */
.block-container {
    padding-top: 1rem;
}

/* TEXT */
h1, h2, h3 {
    color: #e5e7eb !important;
}
p {
    color: #94a3b8 !important;
}

/* NAVBAR */
.navbar {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:15px 40px;
}

/* HERO */
.hero {
    text-align:center;
    margin-top:100px;
}

.hero h1 {
    font-size:80px;
    font-weight:900;
    line-height:1.1;
}

/* GRADIENT TEXT */
.gradient {
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg,#22d3ee,#7c3aed);
    color:white;
    border-radius:10px;
    border:none;
}

</style>
""", unsafe_allow_html=True)

# ================= LANDING =================
def landing():

    # ===== NAVBAR =====
    col1, col2, col3 = st.columns([6,2,2])

    with col1:
        st.markdown("### 🚀 CollabSkill AI")

    with col2:
        if st.button("How It Works"):
            st.session_state.section = "how"
            st.rerun()

    with col3:
        if st.button("Get Started"):
            st.session_state.page = "login"
            st.rerun()

    # ===== HERO =====
    st.markdown("""
    <div class="hero">
        <h1>
            Connect.<br>
            Collaborate.<br>
            <span class="gradient">Exchange Skills</span><br>
            <span class="gradient">Smarter.</span>
        </h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(
        "An intelligent platform that matches you with the right people — using AI to connect digital skill providers with those who need them instantly."
    )

    # ===== HOW IT WORKS =====
    if st.session_state.section == "how":

        st.markdown("## How CollabSkill AI Works")

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        col5, col6 = st.columns(2)

        col1.markdown("""
        <div style="background:#0f172a;padding:20px;border-radius:12px;">
        <h4>01 Register</h4>
        <p>Create your profile</p>
        </div>
        """, unsafe_allow_html=True)

        col2.markdown("""
        <div style="background:#0f172a;padding:20px;border-radius:12px;">
        <h4>02 Post Task</h4>
        <p>Describe your need</p>
        </div>
        """, unsafe_allow_html=True)

        col3.markdown("""
        <div style="background:#0f172a;padding:20px;border-radius:12px;">
        <h4>03 AI Match</h4>
        <p>Find best users</p>
        </div>
        """, unsafe_allow_html=True)

        col4.markdown("""
        <div style="background:#0f172a;padding:20px;border-radius:12px;">
        <h4>04 Collaborate</h4>
        <p>Work together</p>
        </div>
        """, unsafe_allow_html=True)

        col5.markdown("""
        <div style="background:#0f172a;padding:20px;border-radius:12px;">
        <h4>05 Complete</h4>
        <p>Finish task</p>
        </div>
        """, unsafe_allow_html=True)

        col6.markdown("""
        <div style="background:#0f172a;padding:20px;border-radius:12px;">
        <h4>06 Trust Score</h4>
        <p>Build reputation</p>
        </div>
        """, unsafe_allow_html=True)

# ================= LOGIN =================
def login():
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

    if st.button("Register"):
        st.session_state.page = "register"
        st.rerun()

# ================= REGISTER =================
def register():
    st.title("Register")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    skills = st.text_input("Skills")
    bio = st.text_area("Bio")
    portfolio = st.text_input("Portfolio")

    if st.button("Register"):
        success, msg = register_user(username, email, password, skills, bio, portfolio)
        if success:
            st.success(msg)
        else:
            st.error(msg)

    if st.button("Back"):
        st.session_state.page = "login"
        st.rerun()

# ================= ROUTING =================
if st.session_state.page == "landing":
    landing()
elif st.session_state.page == "login":
    login()
elif st.session_state.page == "register":
    register()
