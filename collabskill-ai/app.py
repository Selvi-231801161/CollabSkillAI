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

/* CENTER CONTENT */
.center {
    text-align: center;
    margin-top: 80px;
}

/* HERO TEXT */
.light {
    color: #e5e7eb;
    font-size: 85px;
    font-weight: 900;
    line-height: 1.1;
}

/* GRADIENT */
.gradient {
    font-size: 85px;
    font-weight: 900;
    line-height: 1.1;
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
}

/* SUBTEXT */
.sub {
    color: #94a3b8;
    font-size: 18px;
    text-align: center;
    margin-top: 20px;
}

/* INPUT FIX */
.stTextInput input, .stTextArea textarea {
    background-color: #1f2937 !important;
    color: white !important;
    border: 1px solid #374151 !important;
}

/* LABEL FIX (IMPORTANT) */
label, .stTextInput label, .stTextArea label {
    color: #ffffff !important;
    font-weight: 500;
}

/* PLACEHOLDER */
input::placeholder {
    color: #9ca3af !important;
}

/* SELECTBOX */
.stSelectbox div {
    background-color: #1f2937 !important;
    color: white !important;
}

/* CHECKBOX */
.stCheckbox label {
    color: white !important;
}

/* BUTTON */
.stButton>button {
    background: linear-gradient(90deg,#22d3ee,#7c3aed);
    color: white;
    border-radius: 10px;
    border: none;
}

</style>
""", unsafe_allow_html=True)

# ================= LANDING =================
def landing():

    col1, col2 = st.columns([8,2])

    with col1:
        st.markdown(
            "<h3 style='color:#e5e7eb;'>🚀 CollabSkill AI</h3>",
            unsafe_allow_html=True
        )

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

    # Create 3 columns to center content
    left, center, right = st.columns([1,2,1])

    with center:

        st.markdown("""
        <div style="
            background-color:#0f172a;
            padding:40px;
            border-radius:15px;
            box-shadow:0 0 30px rgba(0,0,0,0.5);
        ">
        """, unsafe_allow_html=True)

        st.markdown("<h2 style='color:#e5e7eb; text-align:center;'>Login</h2>", unsafe_allow_html=True)

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

        if st.button("Login"):
            user = login_user(username, password)
            if user:
                st.success("Login successful")
            else:
                st.error("Invalid credentials")

        st.markdown("<p style='color:#9ca3af;'>Don't have an account?</p>", unsafe_allow_html=True)

        if st.button("Create Account"):
            st.session_state.page = "register"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ================= REGISTER =================
def register():

    st.markdown("<h1 style='color:#e5e7eb;'>Create Your Profile</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#9ca3af;'>Join the skill exchange community</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

    with col2:
        skills = st.text_input("Skills (e.g. Python, UI Design)")
        experience = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"])
        portfolio = st.text_input("Portfolio / GitHub Link (optional)")

    bio = st.text_area("Short Bio")

    agree = st.checkbox("I agree to Terms & Conditions")

    if st.button("Create Account"):
        if not agree:
            st.warning("Please accept terms")
        elif username and email and password:
            success, msg = register_user(username, email, password, skills, bio, portfolio)
            if success:
                st.success("Account created successfully 🎉")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(msg)
        else:
            st.warning("Please fill all required fields")

    st.markdown("<p style='color:#9ca3af;'>Already have an account?</p>", unsafe_allow_html=True)

    if st.button("Login"):
        st.session_state.page = "login"
        st.rerun()

# ================= ROUTING =================
if st.session_state.page == "landing":
    landing()
elif st.session_state.page == "login":
    login()
elif st.session_state.page == "register":
    register()
