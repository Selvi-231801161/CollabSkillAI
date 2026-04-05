# tasks_db.py
import uuid
from database import db_fetchone, db_fetchall, db_execute

# ═══════════════════════════════════════════════════════════════
#  SKILL CLASSIFICATION
# ═══════════════════════════════════════════════════════════════

SKILL_CATEGORIES = [
    "Programming and Development",
    "Design and Creative",
    "Data and Analytics",
    "Digital Marketing",
    "Content and Writing",
    "Media and Content Creation",
    "Tutoring and Education",
    "Career and Professional Skills",
    "Productivity and Personal Development",
]

SKILLS_BY_CATEGORY = {
    "Programming and Development": [
        "Python Programming", "Java Programming", "C++ Programming",
        "JavaScript", "Web Development (HTML, CSS)", "Frontend Development (React)",
        "Backend Development (Node.js)", "API Development", "App Development", "Git and GitHub",
    ],
    "Design and Creative": [
        "UI/UX Design (Figma)", "Wireframing and Prototyping",
        "Graphic Design (Photoshop)", "Graphic Design (Canva)",
        "Logo Design", "Branding Design", "Presentation Design", "Social Media Post Design",
    ],
    "Data and Analytics": [
        "Data Analysis (Excel)", "Data Analysis (Python)", "SQL",
        "Power BI", "Data Visualization", "Statistics Basics", "Machine Learning Basics",
    ],
    "Digital Marketing": [
        "SEO (Search Engine Optimization)", "Social Media Marketing",
        "Content Marketing", "Email Marketing", "Google Ads Basics", "Instagram Growth Strategies",
    ],
    "Content and Writing": [
        "Content Writing", "Copywriting", "Blog Writing", "Technical Writing",
        "Script Writing (YouTube/Reels)", "Resume Writing", "LinkedIn Content Writing",
    ],
    "Media and Content Creation": [
        "Video Editing (Premiere Pro)", "Video Editing (CapCut)",
        "Animation Basics (After Effects)", "YouTube Content Creation",
        "Reels and Shorts Editing", "Podcast Editing",
    ],
    "Tutoring and Education": [
        "Programming Tutoring", "Math Tutoring", "Science Tutoring",
        "Assignment Help", "Exam Preparation Strategies", "Concept Explanation Sessions",
    ],
    "Career and Professional Skills": [
        "Resume Building", "LinkedIn Profile Optimization", "Interview Preparation",
        "Portfolio Building", "Freelancing Guidance", "Personal Branding",
    ],
    "Productivity and Personal Development": [
        "Time Management", "Productivity Systems", "Study Techniques",
        "Goal Setting", "Habit Building", "Focus Improvement Techniques",
    ],
}

CATEGORIES = [
    "Development", "Design", "Marketing", "Content Writing",
    "Data Science", "Video Editing", "SEO", "DevOps", "Machine Learning", "Other",
]

KNOWLEDGE_TOPICS = [
    "Programming", "Web Development", "Data Science", "Design",
    "Digital Marketing", "Video and Media", "Business and Finance",
    "Language Learning", "Mathematics", "Science", "Music", "Other",
]

# knowledge_intent values
INTENT_LEARN  = "learn"   # user wants to learn / needs help
INTENT_TEACH  = "teach"   # user wants to teach / can help others

TYPE_TASK      = "task"
TYPE_KNOWLEDGE = "knowledge"


# ═══════════════════════════════════════════════════════════════
#  TASK CRUD
# ═══════════════════════════════════════════════════════════════

def create_task(title, description, skills, category, deadline,
                priority, created_by, entry_type=TYPE_TASK,
                knowledge_intent=""):
    tid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO tasks
            (id, title, description, skills, category, deadline, priority,
             created_by, type, knowledge_intent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tid, title.strip(), description.strip(), skills.strip(),
          category, deadline, priority, created_by, entry_type, knowledge_intent))
    return db_fetchone("SELECT * FROM tasks WHERE id=?", (tid,))


def get_all_open_tasks(search="", category="", sort="newest",
                       entry_type=TYPE_TASK, knowledge_intent=""):
    where  = ["t.status='open'", "t.type=?"]
    params = [entry_type]

    if knowledge_intent:
        where.append("t.knowledge_intent=?")
        params.append(knowledge_intent)
    if search:
        where.append("(t.title LIKE ? OR t.description LIKE ? OR t.skills LIKE ?)")
        params += [f"%{search}%"] * 3
    if category and category != "All":
        where.append("t.category=?")
        params.append(category)

    order = {
        "oldest":   "t.created_at ASC",
        "priority": "CASE t.priority WHEN 'Urgent' THEN 1 WHEN 'Normal' THEN 2 ELSE 3 END",
    }.get(sort, "t.created_at DESC")

    return db_fetchall(f"""
        SELECT t.*,
               u.username AS creator_name,
               u.trust_score AS creator_trust,
               u.experience AS creator_experience,
               u.avatar_color AS creator_avatar_color,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
        FROM tasks t JOIN users u ON t.created_by=u.id
        WHERE {" AND ".join(where)} ORDER BY {order}
    """, tuple(params))


def get_my_tasks(user_id, entry_type=None):
    if entry_type:
        return db_fetchall("""
            SELECT t.*,
                   (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
            FROM tasks t WHERE t.created_by=? AND t.type=?
            ORDER BY t.created_at DESC
        """, (user_id, entry_type))
    return db_fetchall("""
        SELECT t.*,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
        FROM tasks t WHERE t.created_by=?
        ORDER BY t.created_at DESC
    """, (user_id,))


def get_all_tasks_admin(entry_type=None):
    where  = "1=1"
    params = []
    if entry_type:
        where  = "t.type=?"
        params = [entry_type]
    return db_fetchall(f"""
        SELECT t.*, u.username AS creator_name,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
        FROM tasks t JOIN users u ON t.created_by=u.id
        WHERE {where} ORDER BY t.created_at DESC
    """, tuple(params))


def update_task_status(task_id, status):
    db_execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))


def delete_task(task_id):
    db_execute("DELETE FROM tasks WHERE id=?", (task_id,))


# ═══════════════════════════════════════════════════════════════
#  APPLICATIONS
# ═══════════════════════════════════════════════════════════════

def apply_to_task(task_id, user_id, message=""):
    if db_fetchone("SELECT id FROM applications WHERE task_id=? AND user_id=?",
                   (task_id, user_id)):
        return False, "You have already applied to this post."
    db_execute("""
        INSERT INTO applications (id, task_id, user_id, message) VALUES (?,?,?,?)
    """, (str(uuid.uuid4()), task_id, user_id, message))
    return True, "Application submitted successfully."


def get_my_applications(user_id):
    return db_fetchall("""
        SELECT a.*, t.title AS task_title, t.skills AS task_skills,
               t.category, t.status AS task_status, t.type AS task_type,
               u.username AS owner_name
        FROM applications a
        JOIN tasks t ON a.task_id=t.id
        JOIN users u ON t.created_by=u.id
        WHERE a.user_id=? ORDER BY a.created_at DESC
    """, (user_id,))


def get_applications_for_task(task_id):
    return db_fetchall("""
        SELECT a.*, u.username, u.skills, u.trust_score, u.experience
        FROM applications a JOIN users u ON a.user_id=u.id
        WHERE a.task_id=? ORDER BY a.created_at DESC
    """, (task_id,))


# ═══════════════════════════════════════════════════════════════
#  FEEDBACK
# ═══════════════════════════════════════════════════════════════

def submit_feedback(from_id, to_id, rating, comment=""):
    if db_fetchone("SELECT id FROM feedback WHERE from_user_id=? AND to_user_id=?",
                   (from_id, to_id)):
        return False, "You have already submitted a rating for this user."
    db_execute("""
        INSERT INTO feedback (id, from_user_id, to_user_id, rating, comment)
        VALUES (?,?,?,?,?)
    """, (str(uuid.uuid4()), from_id, to_id, rating, comment))
    return True, "Rating submitted successfully."


def get_feedback_for_user(user_id):
    return db_fetchall("""
        SELECT f.*, u.username AS from_name
        FROM feedback f JOIN users u ON f.from_user_id=u.id
        WHERE f.to_user_id=? ORDER BY f.created_at DESC
    """, (user_id,))


# ═══════════════════════════════════════════════════════════════
#  NOTIFICATIONS
# ═══════════════════════════════════════════════════════════════

def add_notification(user_id, title, message):
    db_execute("""
        INSERT INTO notifications (id, user_id, title, message) VALUES (?,?,?,?)
    """, (str(uuid.uuid4()), user_id, title, message))


def get_notifications(user_id):
    return db_fetchall("""
        SELECT * FROM notifications WHERE user_id=?
        ORDER BY created_at DESC LIMIT 30
    """, (user_id,))


def get_unread_count(user_id):
    r = db_fetchone(
        "SELECT COUNT(*) AS c FROM notifications WHERE user_id=? AND is_read=0",
        (user_id,))
    return r["c"] if r else 0


def mark_all_read(user_id):
    db_execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
