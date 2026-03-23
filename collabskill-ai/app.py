import streamlit as st
import pandas as pd
from database import init_db, get_connection
from auth import register_user, login_user, update_trust_score
from ai_matching import match_users_to_task

init_db()

st.set_page_config(page_title="CollabSkill AI", page_icon="🚀", layout="wide")

st.markdown("""
<style>
body { background-color: #070a12; color: #e2e8f0; }
[data-testid="stSidebar"] { background-color: #0d1221; }

.big-title {
    font-size: 2.5rem;
    font-weight: 800;
    color: #00e5ff;
}

.sub-text { color: #64748b; }

.stButton>button {
    background: linear-gradient(135deg, #00e5ff, #7c3aed);
    color: white;
    border-radius: 10px;
    border: none;
}

.stTextInput input, .stTextArea textarea {
    background-color: #111827;
    color: white;
}

.card {
    background: #111827;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #1f2937;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

if "user" not in st.session_state:
    st.session_state.user = None

with st.sidebar:
    if st.session_state.user is None:
        page = st.radio("", ["Login", "Register"])
    else:
        u = st.session_state.user
        st.success(u[1])
        page = st.radio("Menu", [
            "Dashboard", "Profile", "Post Task",
            "Browse Tasks", "AI Match", "Feedback"
        ])
        if st.button("Logout"):
            st.session_state.user = None
            st.rerun()

def show_login():
    st.markdown('<div class="big-title">Login</div>', unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.session_state.user = user
            st.success("Login success")
            st.rerun()
        else:
            st.error("Invalid")

def show_register():
    st.markdown('<div class="big-title">Create Account</div>', unsafe_allow_html=True)
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

def show_dashboard():
    st.markdown('<div class="big-title">Dashboard</div>', unsafe_allow_html=True)

    conn = get_connection()
    total_users = pd.read_sql("SELECT COUNT(*) as c FROM users", conn).iloc[0]['c']
    total_tasks = pd.read_sql("SELECT COUNT(*) as c FROM tasks", conn).iloc[0]['c']
    conn.close()

    col1, col2 = st.columns(2)
    col1.metric("Users", total_users)
    col2.metric("Tasks", total_tasks)

def show_profile():
    st.write(st.session_state.user)

def show_post():
    st.markdown('<div class="big-title">Post Task</div>', unsafe_allow_html=True)

    title = st.text_input("Title")
    desc = st.text_area("Description")
    skills = st.text_input("Skills")

    if st.button("Post"):
        conn = get_connection()
        conn.execute(
            "INSERT INTO tasks (title, description, required_skills, posted_by) VALUES (?,?,?,?)",
            (title, desc, skills, st.session_state.user[1])
        )
        conn.commit()
        conn.close()
        st.success("Task added")

def show_browse():
    st.markdown('<div class="big-title">Tasks</div>', unsafe_allow_html=True)

    conn = get_connection()
    df = pd.read_sql("SELECT * FROM tasks", conn)
    conn.close()

    for _, row in df.iterrows():
        st.markdown(f"""
        <div class="card">
            <h4>{row['title']}</h4>
            <p>{row['description']}</p>
            <small>{row['required_skills']}</small>
        </div>
        """, unsafe_allow_html=True)

def show_ai():
    st.markdown('<div class="big-title">AI Matching</div>', unsafe_allow_html=True)

    title = st.text_input("Title")
    desc = st.text_area("Description")
    skills = st.text_input("Skills")

    if st.button("Match"):
        matches = match_users_to_task(title, desc, skills, st.session_state.user[1])
        for m in matches:
            st.write(m)

def show_feedback():
    user = st.text_input("User")
    rating = st.slider("Rating", 1, 5)
    if st.button("Submit"):
        update_trust_score(user, rating * 2)
        st.success("Done")

if st.session_state.user is None:
    if page == "Login":
        show_login()
    else:
        show_register()
else:
    if page == "Dashboard":
        show_dashboard()
    elif page == "Profile":
        show_profile()
    elif page == "Post Task":
        show_post()
    elif page == "Browse Tasks":
        show_browse()
    elif page == "AI Match":
        show_ai()
    elif page == "Feedback":
        show_feedback()
