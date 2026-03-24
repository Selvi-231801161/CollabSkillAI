# auth.py
import uuid
import hashlib
import os
from database import db_fetchone, db_fetchall, db_execute

# The email that gets admin role automatically
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@collabskill.com").lower()


def _hash(password: str) -> str:
    """SHA-256 hash — no extra library needed."""
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, email, password, skills="", bio="", portfolio="", experience="Beginner"):
    """
    Called from app.py as:
        register_user(username, email, password, skills, bio, portfolio)
    Returns (True, user_dict) or (False, "error message")
    """
    if not username or not email or not password:
        return False, "Username, email and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    # Check duplicates
    if db_fetchone("SELECT id FROM users WHERE username = ?", (username,)):
        return False, "That username is already taken."
    if db_fetchone("SELECT id FROM users WHERE email = ?", (email.lower(),)):
        return False, "An account with that email already exists."

    # First user OR admin email → admin role
    count = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    role  = "admin" if (count == 0 or email.strip().lower() == ADMIN_EMAIL) else "user"

    uid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO users
            (id, username, email, password_hash, role, skills, experience, bio, portfolio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, username.strip(), email.strip().lower(),
          _hash(password), role, skills, experience, bio, portfolio))

    # Welcome notification
    nid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO notifications (id, user_id, title, message)
        VALUES (?, ?, ?, ?)
    """, (nid, uid,
          "Welcome to CollabSkill AI! 🎉",
          "Your account is ready. Start by posting a task or exploring the community."))

    user = db_fetchone("SELECT * FROM users WHERE id = ?", (uid,))
    return True, user


def login_user(username, password):
    """
    Called from app.py as:
        user = login_user(username, password)
    Returns user dict on success, None on failure.
    (Legacy shape — returns None so existing `if user:` checks still work.)
    """
    if not username or not password:
        return None

    user = db_fetchone(
        "SELECT * FROM users WHERE username = ? AND password_hash = ?",
        (username.strip(), _hash(password))
    )

    if not user:
        return None
    if not user["is_active"]:
        return None

    return user


def get_user(user_id):
    return db_fetchone("SELECT * FROM users WHERE id = ?", (user_id,))


def update_profile(user_id, username, skills, experience, bio, portfolio):
    db_execute("""
        UPDATE users
        SET username=?, skills=?, experience=?, bio=?, portfolio=?
        WHERE id=?
    """, (username, skills, experience, bio, portfolio, user_id))


def update_trust_score(user_id, new_rating):
    user = db_fetchone("SELECT trust_score, total_ratings FROM users WHERE id=?", (user_id,))
    if not user:
        return
    scaled    = new_rating * 2          # 1-5 → 2-10 scale
    old, total= user["trust_score"], user["total_ratings"]
    new_score = round(((old * total) + scaled) / (total + 1), 1)
    db_execute("UPDATE users SET trust_score=?, total_ratings=? WHERE id=?",
               (new_score, total + 1, user_id))


def get_top_users(limit=6):
    return db_fetchall("""
        SELECT id, username, skills, experience, trust_score, total_ratings
        FROM users WHERE is_active=1
        ORDER BY trust_score DESC LIMIT ?
    """, (limit,))
