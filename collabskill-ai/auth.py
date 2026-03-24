# auth.py
import os
import uuid
import bcrypt
from database import db_fetchone, db_insert, db_execute, db_fetchall


ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@collabskill.com").lower()


# ── Password helpers ──────────────────────────────────────────
def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ── Register ──────────────────────────────────────────────────
def register_user(name, email, password, skills="", experience="Beginner", bio="", portfolio=""):
    email = email.strip().lower()

    if not name or not email or not password:
        return False, "Name, email and password are required."
    if len(password) < 6:
        return False, "Password must be at least 6 characters."

    existing = db_fetchone("SELECT id FROM users WHERE email = ?", (email,))
    if existing:
        return False, "An account with this email already exists."

    # First-ever user OR matching admin email → admin role
    count = db_fetchone("SELECT COUNT(*) AS c FROM users")["c"]
    role  = "admin" if (count == 0 or email == ADMIN_EMAIL) else "user"

    uid = str(uuid.uuid4())
    db_insert("""
        INSERT INTO users (id, name, email, password_hash, role, skills, experience, bio, portfolio)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (uid, name.strip(), email, hash_password(password), role, skills, experience, bio, portfolio))

    # Welcome notification
    db_insert("""
        INSERT INTO notifications (id, user_id, title, message)
        VALUES (?, ?, ?, ?)
    """, (str(uuid.uuid4()), uid,
          "Welcome to CollabSkill AI! 🎉",
          "Your account is ready. Start by posting a task or exploring the community."))

    user = db_fetchone("SELECT * FROM users WHERE id = ?", (uid,))
    return True, user


# ── Login ─────────────────────────────────────────────────────
def login_user(email, password):
    email = email.strip().lower()
    user  = db_fetchone("SELECT * FROM users WHERE email = ?", (email,))

    if not user:
        return False, "Invalid email or password."
    if not user["is_active"]:
        return False, "Your account has been deactivated."
    if not verify_password(password, user["password_hash"]):
        return False, "Invalid email or password."

    return True, user


# ── Profile helpers ───────────────────────────────────────────
def get_user(user_id):
    return db_fetchone("SELECT * FROM users WHERE id = ?", (user_id,))


def update_profile(user_id, name, skills, experience, bio, portfolio):
    db_execute("""
        UPDATE users SET name=?, skills=?, experience=?, bio=?, portfolio=?
        WHERE id=?
    """, (name, skills, experience, bio, portfolio, user_id))


def update_trust_score(user_id, new_rating):
    """Weighted average; rating 1-5 → stored as 0-10 (×2)."""
    user = db_fetchone("SELECT trust_score, total_ratings FROM users WHERE id=?", (user_id,))
    if not user:
        return
    scaled    = new_rating * 2
    old_score = user["trust_score"]
    total     = user["total_ratings"]
    new_score = round(((old_score * total) + scaled) / (total + 1), 1)
    db_execute("UPDATE users SET trust_score=?, total_ratings=? WHERE id=?",
               (new_score, total + 1, user_id))


# ── Top users ─────────────────────────────────────────────────
def get_top_users(limit=6):
    return db_fetchall("""
        SELECT id, name, skills, experience, trust_score, total_ratings
        FROM users WHERE is_active=1 ORDER BY trust_score DESC LIMIT ?
    """, (limit,))
