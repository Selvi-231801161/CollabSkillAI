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

# ================= LANDING =================
def landing():

    col1, col2 = st.columns([8,2])

    with col1:
        st.markdown("<h3 style='color:white;'>🚀 CollabSkill AI</h3>", unsafe_allow_html=True)

    with col2:
        if st.button("Get Started"):
            st.session_state.page = "login"
            st.rerun()

    st.markdown("""
    <div style="text-align:center; margin-top:100px;">
        <h1 style="color:#e5e7eb;">Connect.<br>Collaborate.</h1>
        <h1 style="background:linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
        -webkit-background-clip:text; color:transparent;">Exchange Skills</h1>
        <h1 style="background:linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
        -webkit-background-clip:text; color:transparent;">Smarter.</h1>
    </div>
    """, unsafe_allow_html=True)

# ================= LOGIN =================
def login():

    left, center, right = st.columns([1,2,1])

    with center:

        st.markdown("""
        <div style="background:#0f172a;padding:40px;border-radius:15px;">
        """, unsafe_allow_html=True)

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

        st.markdown("<p style='color:#9ca3af;'>Don't have an account?</p>", unsafe_allow_html=True)

        if st.button("Create Account"):
            st.session_state.page = "register"
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

# ================= REGISTER =================
def register():

    left, center, right = st.columns([1,2,1])

    with center:

        st.markdown("""
        <div style="background:#0f172a;padding:40px;border-radius:15px;">
        """, unsafe_allow_html=True)

        st.markdown("<h2 style='color:white;text-align:center;'>Create Account</h2>", unsafe_allow_html=True)

        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        skills = st.text_input("Skills")
        bio = st.text_area("Bio")
        portfolio = st.text_input("Portfolio")

        if st.button("Create Account"):
            success, msg = register_user(username, email, password, skills, bio, portfolio)
            if success:
                st.success("Account created")
                st.session_state.page = "login"
                st.rerun()
            else:
                st.error(msg)

        st.markdown("</div>", unsafe_allow_html=True)

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
