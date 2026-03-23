import streamlit as st
from database import init_db, get_all_tasks, add_task, get_user_by_id
from auth import register_user, login_user
# Import your matching logic (explained below)
# from ai_engine import get_matches 

init_db()

st.set_page_config(page_title="CollabSkill AI", layout="wide")

# ================= SESSION STATE =================
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "user" not in st.session_state:
    st.session_state.user = None

# ================= GLOBAL CSS (Your Original Style) =================
st.markdown("""
<style>
    header, #MainMenu, footer {visibility: hidden;}
    .block-container {padding-top: 2rem;}
    .stApp { background-color: #050816; }
    .light { color: #e5e7eb; font-size: 60px; font-weight: 900; line-height: 1.1; }
    .gradient { 
        font-size: 60px; font-weight: 900; 
        background: linear-gradient(90deg,#22d3ee,#818cf8,#a855f7);
        -webkit-background-clip: text; color: transparent; 
    }
    .card {
        background-color: #0f172a;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #1e293b;
        margin-bottom: 20px;
    }
    .stButton>button {
        background: linear-gradient(90deg,#22d3ee,#7c3aed);
        color: white; border-radius: 10px; border: none; width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ================= HELPER: SIDEBAR NAVIGATION =================
def sidebar_nav():
    with st.sidebar:
        st.markdown("<h2 style='color:#22d3ee;'>CollabSkill AI</h2>", unsafe_allow_html=True)
        st.write(f"Welcome, **{st.session_state.user['username']}**!")
        
        if st.button("🏠 Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("➕ Post a Task"):
            st.session_state.page = "post_task"
            st.rerun()
        if st.button("🔍 Find Skills"):
            st.session_state.page = "find_skills"
            st.rerun()
        
        st.write("---")
        if st.button("Logout"):
            st.session_state.user = None
            st.session_state.page = "landing"
            st.rerun()

# ================= PAGE: DASHBOARD =================
def dashboard():
    sidebar_nav()
    st.markdown("<h1 class='light'>Community Feed</h1>", unsafe_allow_html=True)
    
    tasks = get_all_tasks() # Ensure this function exists in database.py
    
    if not tasks:
        st.info("No active tasks yet. Be the first to post!")
    
    for task in tasks:
        with st.container():
            st.markdown(f"""
            <div class="card">
                <h3 style="color:#22d3ee;">{task['title']}</h3>
                <p style="color:#94a3b8;">{task['description']}</p>
                <span style="background:#1e293b; padding:5px 10px; border-radius:5px; color:#a855f7;">
                    Required: {task['skill_required']}
                </span>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Apply to help {task['username']}", key=task['id']):
                st.success("Interest sent to the poster!")

# ================= PAGE: POST TASK =================
def post_task_page():
    sidebar_nav()
    st.markdown("<h1 class='light'>Post a New Task</h1>", unsafe_allow_html=True)
    
    with st.form("task_form"):
        title = st.text_input("Task Title (e.g., Need a Logo Design)")
        desc = st.text_area("Detailed Description")
        skill = st.text_input("Primary Skill Required")
        
        if st.form_submit_button("Submit Task"):
            if title and desc and skill:
                add_task(st.session_state.user['id'], title, desc, skill)
                st.success("Task posted successfully!")
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Please fill all fields.")

# ================= ROUTING LOGIC =================
if st.session_state.user is None:
    if st.session_state.page == "landing":
        # ... (Include your landing function here)
    elif st.session_state.page == "login":
        # ... (Include updated login function that sets st.session_state.user)
    elif st.session_state.page == "register":
        # ... (Include your register function)
else:
    if st.session_state.page == "dashboard":
        dashboard()
    elif st.session_state.page == "post_task":
        post_task_page()
    elif st.session_state.page == "find_skills":
        # Add find_skills logic here
        pass
