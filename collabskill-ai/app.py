import streamlit as st
from database import init_db
from auth import register_user, login_user

init_db()

st.set_page_config(layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "landing"

# ================= REMOVE STREAMLIT HEADER =================
st.markdown("""
<div style="text-align:center; margin-top:80px;">

    <h1 style="font-size:85px; font-weight:900; line-height:1.1; color:#d1d5db;">
        Connect.<br>
        Collaborate.
    </h1>

    <h1 style="font-size:85px; font-weight:900; line-height:1.1;
        background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
        -webkit-background-clip: text;
        color: transparent;">
        Exchange Skills
    </h1>

    <h1 style="font-size:85px; font-weight:900; line-height:1.1;
        background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
        -webkit-background-clip: text;
        color: transparent;">
        Smarter.
    </h1>

</div>
""", unsafe_allow_html=True)

# ================= LANDING =================
def landing():

    # ===== NAVBAR =====
    col1, col2 = st.columns([8,2])

    with col1:
        st.markdown("### 🚀 CollabSkill AI")

    with col2:
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
        "<p style='text-align:center; font-size:18px;'>"
        "An intelligent platform that matches you with the right people — "
        "using AI to connect digital skill providers with those who need them instantly."
        "</p>",
        unsafe_allow_html=True
    )

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
