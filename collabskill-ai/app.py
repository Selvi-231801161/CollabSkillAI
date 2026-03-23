import streamlit as st
from database import init_db
from auth import register_user, login_user

init_db()

st.set_page_config(layout="wide")

# SESSION
if "page" not in st.session_state:
    st.session_state.page = "landing"

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

/* HERO */
.center {
    text-align: center;
    margin-top: 80px;
}

.light {
    color: #e5e7eb;
    font-size: 85px;
    font-weight: 900;
}

.gradient {
    font-size: 85px;
    font-weight: 900;
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}

.sub {
    color: #94a3b8;
    text-align: center;
}

/* ===== AUTH CARD ===== */
.auth-card {
    max-width: 450px;
    margin: auto;
    margin-top: 80px;
    padding: 30px;
    background-color: #111827;
    border-radius: 15px;
    box-shadow: 0 0 20px rgba(0,0,0,0.5);
}

/* INPUT */
.stTextInput input, .stTextArea textarea {
    background-color: #1f2937 !important;
    color: white !important;
    border: 1px solid #374151 !important;
}

/* LABEL */
label {
    color: white !important;
}

/* BUTTON */
.stButton>button {
    width: 100%;
    background: linear-gradient(90deg,#22d3ee,#7c3aed);
    color: white;
    border-radius: 10px;
    border: none;
}

/* TEXT */
.small-text {
    color: #9ca3af;
    text-align: center;
}

</style>
""", unsafe_allow_html=True)

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

    st.markdown(
        '<div class="sub">'
        'An intelligent platform that matches you with the right people — '
        'using AI to connect digital skill providers with those who need them instantly.'
        '</div>',
        unsafe_allow_html=True
    )

# ================= LOGIN =================
def login():

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    st.markdown("<h2 style='color:#e5e7eb;text-align:center;'>Login</h2>", unsafe_allow_html=True)

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.success("Login successful")
        else:
            st.error("Invalid credentials")

    st.markdown('<p class="small-text">Don’t have an account?</p>', unsafe_allow_html=True)

    if st.button("Create Account"):
        st.session_state.page = "register"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ================= REGISTER =================
def register():

    st.markdown('<div class="auth-card">', unsafe_allow_html=True)

    st.markdown("<h2 style='color:#e5e7eb;text-align:center;'>Create Account</h2>", unsafe_allow_html=True)

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    skills = st.text_input("Skills")
    bio = st.text_area("Bio")
    portfolio = st.text_input("Portfolio")

    agree = st.checkbox("I agree to Terms & Conditions")

    if st.button("Create Account"):
        if not agree:
            st.warning("Please accept terms")
        else:
            success, msg = register_user(username, email, password, skills, bio, portfolio)
            if success:
                st.success("Account created successfully 🎉")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(msg)

    st.markdown('<p class="small-text">Already have an account?</p>', unsafe_allow_html=True)

    if st.button("Login"):
        st.session_state.page = "login"
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ================= ROUTING =================
if st.session_state.page == "landing":
    landing()
elif st.session_state.page == "login":
    login()
elif st.session_state.page == "register":
    register()
