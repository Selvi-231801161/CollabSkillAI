import streamlit as st
from database import init_db
from auth import register_user, login_user
from tasks import create_task, get_tasks
from chat import send_message, get_messages
from ai_matching import match_users_to_task
from chatbot import ask_bot

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
        '<div class="sub">An intelligent platform that matches you with the right people — using AI to connect digital skill providers with those who need them instantly.</div>',
        unsafe_allow_html=True
    )

# ================= LOGIN =================
def login():

    left, center, right = st.columns([1,2,1])

    with center:
        st.markdown("<h2 style='color:#e5e7eb;text-align:center;'>Login</h2>", unsafe_allow_html=True)

        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")

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

    st.markdown(f"## Welcome {st.session_state.user}")

    menu = st.sidebar.selectbox("Menu", ["Post Task", "View Tasks", "Chat", "AI Chatbot"])

    # POST TASK
    if menu == "Post Task":
        title = st.text_input("Task Title")
        desc = st.text_area("Description")
        skills = st.text_input("Required Skills")

        if st.button("Post"):
            create_task(title, desc, skills, st.session_state.user)
            st.success("Task posted!")

    # VIEW TASKS + AI MATCH
    elif menu == "View Tasks":
        tasks = get_tasks()

        for t in tasks:
            st.write(f"### {t[1]}")
            st.write(t[2])

            if st.button(f"Find Match {t[0]}"):
                matches = match_users_to_task(t[1], t[2], t[3], st.session_state.user)

                for m in matches:
                    st.write(f"{m['username']} - {m['match_score']}%")
                    st.write(m['reason'])

    # CHAT
    elif menu == "Chat":
        other = st.text_input("Chat with user")
        msg = st.text_input("Message")

        if st.button("Send"):
            send_message(st.session_state.user, other, msg)

        msgs = get_messages(st.session_state.user, other)
        for m in msgs:
            st.write(f"{m[0]}: {m[1]}")

    # AI CHATBOT
    elif menu == "AI Chatbot":
        q = st.text_input("Ask AI")

        if st.button("Ask"):
            answer = ask_bot(q)
            st.write(answer)

# ================= ROUTING =================
if st.session_state.page == "landing":
    landing()
elif st.session_state.page == "login":
    login()
elif st.session_state.page == "register":
    register()
elif st.session_state.page == "dashboard":
    dashboard()
