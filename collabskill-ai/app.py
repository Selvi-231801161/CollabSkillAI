import streamlit as st
from database import init_db
from auth import register_user, login_user

init_db()

st.set_page_config(page_title="CollabSkill AI", layout="wide")

# SESSION STATE
if "page" not in st.session_state:
    st.session_state.page = "landing"

# CSS (Landing Page Style)
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
    padding: 15px 40px;
}

.logo {
    font-size: 24px;
    font-weight: bold;
}

.get-started {
    background: linear-gradient(90deg,#00e5ff,#7c3aed);
    padding: 10px 20px;
    border-radius: 10px;
    color: white;
    text-decoration: none;
}

/* HERO */
.hero {
    text-align: center;
    margin-top: 100px;
}

.hero h1 {
    font-size: 70px;
    font-weight: 800;
}

.gradient {
    background: linear-gradient(90deg,#00e5ff,#7c3aed);
    -webkit-background-clip: text;
    color: transparent;
}

.btn {
    background: linear-gradient(90deg,#00e5ff,#7c3aed);
    padding: 12px 25px;
    border-radius: 10px;
    color: white;
    margin-top: 20px;
}
</style>
""", unsafe_allow_html=True)

# =========================
# LANDING PAGE
# =========================
def landing_page():
    col1, col2 = st.columns([8,2])

    with col1:
        st.markdown('<div class="logo">🚀 CollabSkill AI</div>', unsafe_allow_html=True)

    with col2:
        if st.button("Get Started"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown("""
    <div class="hero">
        <h1>
            Connect. Collaborate.<br>
            <span class="gradient">Exchange Skills</span><br>
            Smarter.
        </h1>
        <p>An AI-powered platform to connect people with the right skills instantly.</p>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Launch App"):
        st.session_state.page = "login"
        st.rerun()

# =========================
# LOGIN PAGE
# =========================
def login_page():
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

# =========================
# REGISTER PAGE
# =========================
def register_page():
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

    if st.button("Back to Login"):
        st.session_state.page = "login"
        st.rerun()

# =========================
# ROUTING
# =========================
if st.session_state.page == "landing":
    landing_page()

elif st.session_state.page == "login":
    login_page()

elif st.session_state.page == "register":
    register_page()
