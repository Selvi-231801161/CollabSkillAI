# auth.py
import uuid
import hashlib
import os
from database import db_fetchone, db_fetchall, db_execute

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@collabskill.com").lower()

AVATAR_COLORS = [
    "#22d3ee", "#7c3aed", "#14b8a6", "#f59e0b",
    "#3b82f6", "#ec4899", "#10b981", "#f97316",
]


def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, email, password, skills="", bio="",
                  portfolio="", experience="Beginner", phone_number=""):
    if not username or not email or not password:
        return False, "Username, email and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    if db_fetchone("SELECT id FROM users WHERE username = ?", (username,)):
        return False, "That username is already taken."
    if db_fetchone("SELECT id FROM users WHERE email = ?", (email.lower(),)):
        return False, "An account with that email already exists."

    count = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    role  = "admin" if (count == 0 or email.strip().lower() == ADMIN_EMAIL) else "user"

    # pick a color based on count
    avatar_color = AVATAR_COLORS[count % len(AVATAR_COLORS)]

    uid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO users
            (id, username, email, password_hash, role, skills, experience,
             bio, portfolio, phone_number, avatar_color)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, username.strip(), email.strip().lower(),
          _hash(password), role, skills, experience, bio, portfolio,
          phone_number, avatar_color))

    db_execute("""
        INSERT INTO notifications (id, user_id, title, message)
        VALUES (?, ?, ?, ?)
    """, (str(uuid.uuid4()), uid,
          "Welcome to CollabSkill AI",
          "Your account is ready. Start by posting a task or exploring the community."))

    user = db_fetchone("SELECT * FROM users WHERE id = ?", (uid,))
    return True, user


def login_user(username, password):
    if not username or not password:
        return None
    user = db_fetchone(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username.strip(), _hash(password))
    )
    if not user or not user["is_active"]:
        return None
    return user


def get_user(user_id):
    return db_fetchone("SELECT * FROM users WHERE id = ?", (user_id,))


def update_profile(user_id, username, skills, experience, bio, portfolio, phone_number=""):
    db_execute("""
        UPDATE users
        SET username=?, skills=?, experience=?, bio=?, portfolio=?, phone_number=?
        WHERE id=?
    """, (username, skills, experience, bio, portfolio, phone_number, user_id))


def update_avatar_color(user_id, color):
    db_execute("UPDATE users SET avatar_color=? WHERE id=?", (color, user_id))


def update_trust_score(user_id, new_rating):
    user = db_fetchone("SELECT trust_score, total_ratings FROM users WHERE id=?", (user_id,))
    if not user:
        return
    scaled    = new_rating * 2
    old, total = user["trust_score"], user["total_ratings"]
    new_score = round(((old * total) + scaled) / (total + 1), 1)
    db_execute("UPDATE users SET trust_score=?, total_ratings=? WHERE id=?",
               (new_score, total + 1, user_id))


def get_top_users(limit=6):
    return db_fetchall("""
        SELECT id, username, skills, experience, trust_score, total_ratings, avatar_color
        FROM users WHERE is_active=1
        ORDER BY trust_score DESC LIMIT ?
    """, (limit,))
