# tasks_db.py
import uuid
from database import db_fetchone, db_fetchall, db_execute, db_insert


CATEGORIES = [
    "Development", "Design", "Marketing", "Content Writing",
    "Data Science", "Video Editing", "SEO", "DevOps",
    "Machine Learning", "Other"
]


# ── Create ────────────────────────────────────────────────────
def create_task(title, description, skills, category, deadline, priority, created_by):
    tid = str(uuid.uuid4())
    db_insert("""
        INSERT INTO tasks (id, title, description, skills, category, deadline, priority, created_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tid, title.strip(), description.strip(), skills.strip(),
          category, deadline, priority, created_by))
    return db_fetchone("SELECT * FROM tasks WHERE id=?", (tid,))


# ── Read ──────────────────────────────────────────────────────
def get_task(task_id):
    return db_fetchone("""
        SELECT t.*, u.name AS creator_name, u.trust_score AS creator_trust,
               u.experience AS creator_experience, u.portfolio AS creator_portfolio
        FROM tasks t JOIN users u ON t.created_by = u.id
        WHERE t.id = ?
    """, (task_id,))


def get_all_open_tasks(search="", category="", sort="newest"):
    where  = ["t.status = 'open'"]
    params = []

    if search:
        where.append("(t.title LIKE ? OR t.description LIKE ? OR t.skills LIKE ?)")
        params += [f"%{search}%", f"%{search}%", f"%{search}%"]
    if category and category != "All":
        where.append("t.category = ?")
        params.append(category)

    order = {"oldest": "t.created_at ASC",
             "priority": "CASE t.priority WHEN 'Urgent' THEN 1 WHEN 'Normal' THEN 2 ELSE 3 END"
             }.get(sort, "t.created_at DESC")

    sql = f"""
        SELECT t.*, u.name AS creator_name, u.trust_score AS creator_trust,
               u.experience AS creator_experience,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id = t.id) AS applicant_count
        FROM tasks t JOIN users u ON t.created_by = u.id
        WHERE {" AND ".join(where)}
        ORDER BY {order}
    """
    return db_fetchall(sql, tuple(params))


def get_my_tasks(user_id):
    return db_fetchall("""
        SELECT t.*,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id = t.id) AS applicant_count
        FROM tasks t
        WHERE t.created_by = ?
        ORDER BY t.created_at DESC
    """, (user_id,))


def get_all_tasks_admin():
    """ALL tasks for admin view."""
    return db_fetchall("""
        SELECT t.*, u.name AS creator_name,
               (SELECT COUNT(*) FROM applications a WHERE a.task_id = t.id) AS applicant_count
        FROM tasks t JOIN users u ON t.created_by = u.id
        ORDER BY t.created_at DESC
    """)


# ── Update ────────────────────────────────────────────────────
def update_task_status(task_id, status):
    db_execute("UPDATE tasks SET status=? WHERE id=?", (status, task_id))


def delete_task(task_id):
    db_execute("DELETE FROM tasks WHERE id=?", (task_id,))


# ── Applications ──────────────────────────────────────────────
def apply_to_task(task_id, user_id, message=""):
    existing = db_fetchone(
        "SELECT id FROM applications WHERE task_id=? AND user_id=?", (task_id, user_id))
    if existing:
        return False, "You have already applied."

    aid = str(uuid.uuid4())
    db_insert("""
        INSERT INTO applications (id, task_id, user_id, message)
        VALUES (?, ?, ?, ?)
    """, (aid, task_id, user_id, message))
    return True, "Application submitted!"


def get_applications_for_task(task_id):
    return db_fetchall("""
        SELECT a.*, u.name, u.skills, u.trust_score, u.experience
        FROM applications a JOIN users u ON a.user_id = u.id
        WHERE a.task_id = ?
        ORDER BY a.created_at DESC
    """, (task_id,))


def get_my_applications(user_id):
    return db_fetchall("""
        SELECT a.*, t.title AS task_title, t.skills AS task_skills,
               t.category, t.status AS task_status,
               u.name AS owner_name
        FROM applications a
        JOIN tasks t ON a.task_id = t.id
        JOIN users u ON t.created_by = u.id
        WHERE a.user_id = ?
        ORDER BY a.created_at DESC
    """, (user_id,))


# ── Feedback ──────────────────────────────────────────────────
def submit_feedback(from_id, to_id, rating, comment=""):
    existing = db_fetchone(
        "SELECT id FROM feedback WHERE from_user_id=? AND to_user_id=?", (from_id, to_id))
    if existing:
        return False, "You have already rated this user."

    fid = str(uuid.uuid4())
    db_insert("""
        INSERT INTO feedback (id, from_user_id, to_user_id, rating, comment)
        VALUES (?, ?, ?, ?, ?)
    """, (fid, from_id, to_id, rating, comment))
    return True, "Feedback submitted!"


def get_feedback_for_user(user_id):
    return db_fetchall("""
        SELECT f.*, u.name AS from_name
        FROM feedback f JOIN users u ON f.from_user_id = u.id
        WHERE f.to_user_id = ?
        ORDER BY f.created_at DESC
    """, (user_id,))


# ── Notifications ─────────────────────────────────────────────
def add_notification(user_id, title, message):
    nid = str(uuid.uuid4())
    db_insert("""
        INSERT INTO notifications (id, user_id, title, message)
        VALUES (?, ?, ?, ?)
    """, (nid, user_id, title, message))


def get_notifications(user_id):
    return db_fetchall("""
        SELECT * FROM notifications WHERE user_id=?
        ORDER BY created_at DESC LIMIT 30
    """, (user_id,))


def get_unread_count(user_id):
    r = db_fetchone(
        "SELECT COUNT(*) AS c FROM notifications WHERE user_id=? AND is_read=0", (user_id,))
    return r["c"] if r else 0


def mark_all_read(user_id):
    db_execute("UPDATE notifications SET is_read=1 WHERE user_id=?", (user_id,))
