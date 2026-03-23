import sqlite3
import os

DB_PATH = "data/collabskill.db"


def init_db():
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            username       TEXT    UNIQUE NOT NULL,
            email          TEXT    UNIQUE NOT NULL,
            password       TEXT    NOT NULL,
            skills         TEXT    DEFAULT '',
            experience     TEXT    DEFAULT 'Beginner',
            bio            TEXT    DEFAULT '',
            portfolio_link TEXT    DEFAULT '',
            trust_score    REAL    DEFAULT 5.0,
            total_ratings  INTEGER DEFAULT 0,
            created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            description     TEXT NOT NULL,
            required_skills TEXT DEFAULT '',
            category        TEXT DEFAULT 'Other',
            deadline        TEXT DEFAULT '',
            posted_by       TEXT NOT NULL,
            status          TEXT DEFAULT 'open',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user  TEXT NOT NULL,
            to_user    TEXT NOT NULL,
            rating     INTEGER CHECK(rating BETWEEN 1 AND 5),
            comment    TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def get_connection():
    return sqlite3.connect(DB_PATH)


# ── USER ──

def get_user_by_username(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    row = c.fetchone()
    conn.close()
    return row

def update_user_profile(username, skills, bio, portfolio, experience):
    conn = get_connection()
    conn.execute("""
        UPDATE users SET skills=?, bio=?, portfolio_link=?, experience=?
        WHERE username=?
    """, (skills, bio, portfolio, experience, username))
    conn.commit()
    conn.close()


# ── TASKS ──

def insert_task(title, description, required_skills, category, deadline, posted_by):
    conn = get_connection()
    conn.execute("""
        INSERT INTO tasks (title, description, required_skills, category, deadline, posted_by)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (title, description, required_skills, category, deadline, posted_by))
    conn.commit()
    conn.close()

def close_task(task_id):
    conn = get_connection()
    conn.execute("UPDATE tasks SET status='closed' WHERE id=?", (task_id,))
    conn.commit()
    conn.close()

def delete_task(task_id):
    conn = get_connection()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.commit()
    conn.close()


# ── FEEDBACK ──

def insert_feedback(from_user, to_user, rating, comment):
    conn = get_connection()
    conn.execute("""
        INSERT INTO feedback (from_user, to_user, rating, comment)
        VALUES (?, ?, ?, ?)
    """, (from_user, to_user, rating, comment))
    conn.commit()
    conn.close()

def already_reviewed(from_user, to_user):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM feedback WHERE from_user=? AND to_user=?", (from_user, to_user))
    row = c.fetchone()
    conn.close()
    return row is not None

def get_feedback_for_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT from_user, rating, comment, created_at
        FROM feedback WHERE to_user=? ORDER BY created_at DESC
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows

def get_feedback_by_user(username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT to_user, rating, comment, created_at
        FROM feedback WHERE from_user=? ORDER BY created_at DESC
    """, (username,))
    rows = c.fetchall()
    conn.close()
    return rows


# ── STATS ──

def get_platform_stats():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users");        total_users   = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks");        total_tasks   = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM tasks WHERE status='open'"); open_tasks = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM feedback");     total_reviews = c.fetchone()[0]
    conn.close()
    return total_users, total_tasks, open_tasks, total_reviews

def get_top_users(limit=6):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT username, skills, trust_score, total_ratings, experience
        FROM users ORDER BY trust_score DESC LIMIT ?
    """, (limit,))
    rows = c.fetchall()
    conn.close()
    return rows
