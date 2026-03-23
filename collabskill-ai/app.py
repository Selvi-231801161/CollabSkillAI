import streamlit as st
from database import init_db
from auth import register_user, login_user

init_db()

st.set_page_config(layout="wide")

if "page" not in st.session_state:
    st.session_state.page = "landing"

if "section" not in st.session_state:
    st.session_state.section = "home"

# ================= DARK FULL BACKGROUND =================
st.markdown("""
<style>
.stApp {
    background-color: #050816;
}

/* NAVBAR */
.navbar {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:20px 40px;
}

.nav-links {
    color:#94a3b8;
    font-size:14px;
}

/* HERO */
.hero {
    text-align:center;
    margin-top:120px;
}

.hero h1 {
    font-size:85px;
    font-weight:900;
    line-height:1.1;
    color:white;
}

.gradient {
    background: linear-gradient(90deg,#00e5ff,#7c3aed);
    -webkit-background-clip: text;
    color: transparent;
}

.subtext {
    color:#94a3b8;
    font-size:18px;
    margin-top:20px;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg,#00e5ff,#7c3aed);
    color:white;
    border-radius:10px;
    border:none;
}

/* SECTION */
.section {
    margin-top:120px;
}

.card {
    background:#0f172a;
    padding:25px;
    border-radius:15px;
    border:1px solid #1f2937;
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
        col21, col22 = st.columns(2)

        with col21:
            if st.button("How It Works"):
                st.session_state.section = "how"
                st.rerun()

        with col22:
            st.write("")

    with col3:
        if st.button("Get Started"):
            st.session_state.page = "login"
            st.rerun()

    # HERO
    st.markdown("""
    <div class="hero">
        <h1>
            Connect.<br>
            Collaborate.<br>
            <span class="gradient">Exchange Skills</span><br>
            <span class="gradient">Smarter.</span>
        </h1>

        <div class="subtext">
        An intelligent platform that matches you with the right people — using AI to connect digital skill providers with those who need them instantly.
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("🚀 Launch App"):
        st.session_state.page = "login"
        st.rerun()

    # ================= CONDITIONAL SCROLL =================
    if st.session_state.section == "how":

        st.markdown('<div class="section"></div>', unsafe_allow_html=True)

        st.markdown("## How CollabSkill AI Works")

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)
        col5, col6 = st.columns(2)

        col1.markdown("""
        <div class="card">
        <h4>01 Register & Build Profile</h4>
        Create your skill profile and showcase expertise.
        </div>
        """, unsafe_allow_html=True)

        col2.markdown("""
        <div class="card">
        <h4>02 Post a Task</h4>
        Describe what help you need.
        </div>
        """, unsafe_allow_html=True)

        col3.markdown("""
        <div class="card">
        <h4>03 AI Matches</h4>
        AI finds best skilled users.
        </div>
        """, unsafe_allow_html=True)

        col4.markdown("""
        <div class="card">
        <h4>04 Connect & Collaborate</h4>
        Work together online.
        </div>
        """, unsafe_allow_html=True)

        col5.markdown("""
        <div class="card">
        <h4>05 Complete Task</h4>
        Finish and mark done.
        </div>
        """, unsafe_allow_html=True)

        col6.markdown("""
        <div class="card">
        <h4>06 Trust Score</h4>
        Ratings build credibility.
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
            st.success("Login success")
        else:
            st.error("Invalid")

    if st.button("Go to Register"):
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
