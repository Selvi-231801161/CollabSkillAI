import streamlit as st
from database import init_db
from auth import register_user, login_user

init_db()

st.set_page_config(layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "landing"

# ================= CSS =================
st.markdown("""
<style>
body {
    background-color: #050816;
    color: white;
}

/* NAVBAR */
.navbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 40px;
}

.logo {
    font-size: 22px;
    font-weight: bold;
}

.nav-links {
    font-size: 14px;
    color: #94a3b8;
}

.btn-main {
    background: linear-gradient(90deg,#00e5ff,#7c3aed);
    color: white;
    border-radius: 10px;
    padding: 10px 20px;
    border: none;
}

/* HERO */
.hero {
    text-align: center;
    margin-top: 120px;
}

.hero h1 {
    font-size: 80px;
    font-weight: 900;
    line-height: 1.1;
}

.gradient {
    background: linear-gradient(90deg,#00e5ff,#7c3aed);
    -webkit-background-clip: text;
    color: transparent;
}

.subtext {
    color: #94a3b8;
    margin-top: 20px;
    font-size: 18px;
}

/* SECTION */
.section {
    margin-top: 100px;
    text-align: center;
}

.section h2 {
    font-size: 36px;
}

.card {
    background: #111827;
    padding: 25px;
    border-radius: 12px;
    margin: 10px;
}
</style>
""", unsafe_allow_html=True)

# ================= LANDING =================
def landing():

    # NAVBAR
    col1, col2, col3 = st.columns([2,6,2])

    with col1:
        st.markdown("### 🚀 CollabSkill AI")

    with col2:
        st.markdown('<div class="nav-links">How It Works &nbsp;&nbsp;&nbsp; Features</div>', unsafe_allow_html=True)

    with col3:
        if st.button("Get Started"):
            st.session_state.page = "login"
            st.rerun()

    # HERO
    st.markdown("""
    <div class="hero">
        <h1>
            Collaborate.<br>
            <span class="gradient">Exchange Skills</span><br>
            <span class="gradient">Smarter.</span>
        </h1>

        <div class="subtext">
        An intelligent platform that matches you with the right people — using AI to connect digital skill providers with those who need them instantly.
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Launch App"):
            st.session_state.page = "login"
            st.rerun()

    with col2:
        st.button("See How It Works →")

    # ================= HOW IT WORKS =================
    st.markdown('<div class="section"><h2>How It Works</h2></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.markdown('<div class="card">Create profile and list your digital skills</div>', unsafe_allow_html=True)
    col2.markdown('<div class="card">Post tasks or explore available opportunities</div>', unsafe_allow_html=True)
    col3.markdown('<div class="card">AI matches you with the right collaborators</div>', unsafe_allow_html=True)

    # ================= FEATURES =================
    st.markdown('<div class="section"><h2>Features</h2></div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    col1.markdown('<div class="card">AI-powered skill matching</div>', unsafe_allow_html=True)
    col2.markdown('<div class="card">Task posting and collaboration</div>', unsafe_allow_html=True)
    col3.markdown('<div class="card">User trust score system</div>', unsafe_allow_html=True)

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

    if st.button("Go to Register"):
        st.session_state.page = "register"
        st.rerun()

# ================= REGISTER =================
def register():
    st.title("Create Account")

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

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# ================= ROUTING =================
if st.session_state.page == "landing":
    landing()
elif st.session_state.page == "login":
    login()
elif st.session_state.page == "register":
    register()
