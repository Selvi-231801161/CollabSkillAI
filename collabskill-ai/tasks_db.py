# tasks_db.py
import uuid
from database import db_fetchone, db_fetchall, db_execute

# ── Categories for Task Mode ──────────────────────────────────
CATEGORIES = [
    "Development", "Design", "Marketing", "Content Writing",
    "Data Science", "Video Editing", "SEO", "DevOps",
    "Machine Learning", "Other",
]

# ── Topics for Knowledge Mode ─────────────────────────────────
KNOWLEDGE_TOPICS = [
    "Programming", "Web Development", "Data Science",
    "Design", "Digital Marketing", "Video & Media",
    "Business & Finance", "Language Learning",
    "Mathematics", "Science", "Music", "Other",
]

# ── Entry types ───────────────────────────────────────────────
TYPE_TASK      = "task"
TYPE_KNOWLEDGE = "knowledge"


# ═══════════════════════════════════════════════════════════════
#  TASK MODE  — unchanged existing functions, extended with type
# ═══════════════════════════════════════════════════════════════

def create_task(title, description, skills, category, deadline, priority, created_by,
                entry_type=TYPE_TASK):
    """Create a task OR knowledge request. entry_type = 'task' | 'knowledge'."""
    tid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO tasks
            (id, title, description, skills, category, deadline, priority, created_by, type)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tid, title.strip(), description.strip(), skills.strip(),
          category, deadline, priority, created_by, entry_type))
    return db_fetchone("SELECT * FROM tasks WHERE id=?", (tid,))


def get_all_open_tasks(search="", category="", sort="newest",
                       entry_type=TYPE_TASK):
    """Fetch open tasks filtered by entry_type ('task' or 'knowledge')."""
    where  = ["t.status='open'", "t.type=?"]
    params = [entry_type]

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
               (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
        FROM tasks t JOIN users u ON t.created_by=u.id
        WHERE {" AND ".join(where)} ORDER BY {order}
    """, tuple(params))


def get_my_tasks(user_id, entry_type=None):
    """
    Fetch tasks for a user.
    entry_type=None  → all types (used on profile / dashboard total count)
    entry_type='task' | 'knowledge' → filtered
    """
    if entry_type:
        return db_fetchall("""
            SELECT t.*,
                   (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
            FROM tasks t
            WHERE t.created_by=? AND t.type=?
            ORDER BY t.created_at DESC
        """, (user_id, entry_type))
    return db_fetchall("""
        SELECT t.*,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
        FROM tasks t
        WHERE t.created_by=?
        ORDER BY t.created_at DESC
    """, (user_id,))


def get_all_tasks_admin(entry_type=None):
    """Admin: fetch all tasks, optionally filtered by type."""
    where  = "1=1"
    params = []
    if entry_type:
        where  = "t.type=?"
        params = [entry_type]

    return db_fetchall(f"""
        SELECT t.*, u.username AS creator_name,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id=t.id) AS applicant_count
        FROM tasks t JOIN users u ON t.created_by=u.id
        WHERE {where}
        ORDER BY t.created_at DESC
    """, tuple(params))


def update_task_status(task_id, status):
    db_execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))


def delete_task(task_id):
    db_execute("DELETE FROM tasks WHERE id=?", (task_id,))


def apply_to_task(task_id, user_id, message=""):
    if db_fetchone("SELECT id FROM applications WHERE task_id=? AND user_id=?",
                   (task_id, user_id)):
        return False, "You have already applied."
    db_execute("""
        INSERT INTO applications (id, task_id, user_id, message) VALUES (?,?,?,?)
    """, (str(uuid.uuid4()), task_id, user_id, message))
    return True, "Application submitted!"


def get_my_applications(user_id):
    return db_fetchall("""
        SELECT a.*, t.title AS task_title, t.skills AS task_skills,
               t.category, t.status AS task_status,
               t.type AS task_type,
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
        return False, "You have already rated this user."
    db_execute("""
        INSERT INTO feedback (id, from_user_id, to_user_id, rating, comment)
        VALUES (?,?,?,?,?)
    """, (str(uuid.uuid4()), from_id, to_id, rating, comment))
    return True, "Feedback submitted!"


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
