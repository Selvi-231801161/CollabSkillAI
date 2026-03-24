# database.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "collabskill.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row          # access columns by name
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    c = conn.cursor()

    # ── USERS ────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id            TEXT PRIMARY KEY,
            name          TEXT NOT NULL,
            email         TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role          TEXT NOT NULL DEFAULT 'user',   -- 'admin' | 'user'
            skills        TEXT DEFAULT '',
            experience    TEXT DEFAULT 'Beginner',
            bio           TEXT DEFAULT '',
            portfolio     TEXT DEFAULT '',
            trust_score   REAL DEFAULT 5.0,
            total_ratings INTEGER DEFAULT 0,
            is_active     INTEGER DEFAULT 1,
            created_at    TEXT DEFAULT (datetime('now'))
        )
    """)

    # ── TASKS ────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            description TEXT NOT NULL,
            skills      TEXT NOT NULL,
            category    TEXT DEFAULT 'Other',
            deadline    TEXT DEFAULT '',
            priority    TEXT DEFAULT 'Normal',
            status      TEXT DEFAULT 'open',
            created_by  TEXT NOT NULL,
            created_at  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ── APPLICATIONS ─────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id         TEXT PRIMARY KEY,
            task_id    TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            message    TEXT DEFAULT '',
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(task_id, user_id),
            FOREIGN KEY(task_id) REFERENCES tasks(id)  ON DELETE CASCADE,
            FOREIGN KEY(user_id) REFERENCES users(id)  ON DELETE CASCADE
        )
    """)

    # ── FEEDBACK ─────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id           TEXT PRIMARY KEY,
            from_user_id TEXT NOT NULL,
            to_user_id   TEXT NOT NULL,
            rating       INTEGER NOT NULL,
            comment      TEXT DEFAULT '',
            created_at   TEXT DEFAULT (datetime('now')),
            UNIQUE(from_user_id, to_user_id),
            FOREIGN KEY(from_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(to_user_id)   REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # ── NOTIFICATIONS ─────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id         TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            title      TEXT NOT NULL,
            message    TEXT NOT NULL,
            is_read    INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# ── Generic helpers ──────────────────────────────────────────
def db_fetchone(sql, params=()):
    conn = get_connection()
    row  = conn.execute(sql, params).fetchone()
    conn.close()
    return dict(row) if row else None


def db_fetchall(sql, params=()):
    conn = get_connection()
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def db_execute(sql, params=()):
    conn = get_connection()
    conn.execute(sql, params)
    conn.commit()
    conn.close()


def db_insert(sql, params=()):
    conn = get_connection()
    conn.execute(sql, params)
    conn.commit()
    conn.close()
