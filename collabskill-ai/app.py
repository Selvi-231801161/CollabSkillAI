import streamlit as st
from database import init_db, get_connection
from auth import register_user, login_user

st.set_page_config(page_title="CollabSkill AI", layout="wide")

init_db()

# SESSION
if "page" not in st.session_state:
    st.session_state.page = "home"
if "user" not in st.session_state:
    st.session_state.user = None

# ---------- GLOBAL CSS ----------
st.markdown("""
<style>
body {
    background-color: #020617;
    color: white;
}

h1, h2, h3, h4, h5 {
    color: #ffffff !important;
}

.navbar {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:20px 40px;
    background:#020617;
}

.nav-links button {
    background:none;
    border:none;
    color:#cbd5f5;
    margin-left:20px;
    font-size:16px;
    cursor:pointer;
}

.nav-links button:hover {
    color:white;
}

.btn {
    padding:10px 20px;
    border-radius:10px;
    background:linear-gradient(90deg,#22d3ee,#a855f7);
    color:white;
    border:none;
    font-weight:600;
}

.card {
    max-width:600px;
    margin:auto;
    padding:30px;
    background:#0f172a;
    border-radius:15px;
}

input, textarea {
    background:#1e293b !important;
    color:white !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- NAVBAR ----------
def navbar():
    col1, col2 = st.columns([6,4])

    with col1:
        st.markdown("## 🚀 CollabSkill AI")

    with col2:
        cols = st.columns(5)
        if cols[0].button("Dashboard"):
            st.session_state.page = "dashboard"
        if cols[1].button("Post Task"):
            st.session_state.page = "post"
        if cols[2].button("Browse"):
            st.session_state.page = "browse"
        if cols[3].button("Profile"):
            st.session_state.page = "profile"
        if cols[4].button("Logout"):
            st.session_state.user = None
            st.session_state.page = "home"

# ---------- HOME ----------
def home():
    st.markdown("""
    <h1 style='text-align:center;font-size:70px;'>
    Connect.<br>Collaborate.
    </h1>

    <h1 style='text-align:center;
    background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
    -webkit-background-clip: text;
    color: transparent;
    font-size:70px;'>
    Exchange Skills<br>Smarter.
    </h1>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([5,1])
    with col2:
        if st.button("Get Started"):
            st.session_state.page = "login"

# ---------- LOGIN ----------
def login():
    st.markdown("<h1 style='text-align:center;'>Login</h1>", unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            if st.button("Login"):
                user = login_user(username, password)
                if user:
                    st.session_state.user = username
                    st.session_state.page = "dashboard"
                else:
                    st.error("Invalid credentials")

            st.write("Don't have an account?")
            if st.button("Create Account"):
                st.session_state.page = "register"

# ---------- REGISTER ----------
def register():
    st.markdown("<h1 style='text-align:center;'>Create Account</h1>", unsafe_allow_html=True)

    with st.container():
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
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
                    st.session_state.page = "login"
                else:
                    st.error(msg)

# ---------- DASHBOARD ----------
def dashboard():
    navbar()

    st.markdown(f"""
    <h1 style='color:white;'>Welcome {st.session_state.user}</h1>
    """, unsafe_allow_html=True)

    st.write("🚀 Start collaborating and exploring tasks")

# ---------- POST TASK ----------
def post_task():
    navbar()

    st.markdown("## Post a Task")

    title = st.text_input("Task Title")
    desc = st.text_area("Description")
    skills = st.text_input("Required Skills")

    if st.button("Post"):
        conn = get_connection()
        c = conn.cursor()
        c.execute("""
        INSERT INTO tasks (title, description, skills, posted_by)
        VALUES (?, ?, ?, ?)
        """, (title, desc, skills, st.session_state.user))
        conn.commit()
        conn.close()

        st.success("Task Posted Successfully")

# ---------- BROWSE TASK ----------
def browse():
    navbar()

    st.markdown("## Browse Tasks")

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT title, description, skills, posted_by FROM tasks")
    tasks = c.fetchall()
    conn.close()

    for t in tasks:
        st.markdown(f"""
        <div class="card">
        <h3>{t[0]}</h3>
        <p>{t[1]}</p>
        <b>Skills:</b> {t[2]} <br>
        <b>Posted by:</b> {t[3]}
        </div>
        """, unsafe_allow_html=True)

# ---------- PROFILE ----------
def profile():
    navbar()

    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (st.session_state.user,))
    user = c.fetchone()
    conn.close()

    st.markdown("## My Profile")

    if user:
        st.write(f"Username: {user[1]}")
        st.write(f"Email: {user[2]}")
        st.write(f"Skills: {user[4]}")
        st.write(f"Bio: {user[5]}")

# ---------- ROUTER ----------
if st.session_state.user:
    if st.session_state.page == "dashboard":
        dashboard()
    elif st.session_state.page == "post":
        post_task()
    elif st.session_state.page == "browse":
        browse()
    elif st.session_state.page == "profile":
        profile()
else:
    if st.session_state.page == "home":
        home()
    elif st.session_state.page == "login":
        login()
    elif st.session_state.page == "register":
        register()
