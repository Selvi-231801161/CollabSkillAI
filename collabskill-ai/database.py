# database.py
import sqlite3
import os

DB_PATH = "collabskill.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _get_columns(conn, table):
    """Return list of column names for a table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]


def init_db():
    conn = get_connection()
    c = conn.cursor()

    # ── Check if users table already exists with OLD schema (name col) ──
    existing_cols = _get_columns(conn, "users")

    if existing_cols:
        # Table exists — migrate if needed
        if "name" in existing_cols and "username" not in existing_cols:
            # OLD schema: rename 'name' → 'username'
            c.executescript("""
                ALTER TABLE users RENAME TO users_old;

                CREATE TABLE users (
                    id            TEXT PRIMARY KEY,
                    username      TEXT UNIQUE NOT NULL,
                    email         TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role          TEXT NOT NULL DEFAULT 'user',
                    skills        TEXT DEFAULT '',
                    experience    TEXT DEFAULT 'Beginner',
                    bio           TEXT DEFAULT '',
                    portfolio     TEXT DEFAULT '',
                    trust_score   REAL DEFAULT 5.0,
                    total_ratings INTEGER DEFAULT 0,
                    is_active     INTEGER DEFAULT 1,
                    created_at    TEXT DEFAULT (datetime('now'))
                );

                INSERT INTO users
                    (id, username, email, password_hash, role, skills,
                     experience, bio, portfolio, trust_score, total_ratings,
                     is_active, created_at)
                SELECT
                    id,
                    COALESCE(username, name) as username,
                    email, password_hash,
                    COALESCE(role, 'user'),
                    COALESCE(skills, ''),
                    COALESCE(experience, 'Beginner'),
                    COALESCE(bio, ''),
                    COALESCE(portfolio, ''),
                    COALESCE(trust_score, 5.0),
                    COALESCE(total_ratings, 0),
                    COALESCE(is_active, 1),
                    COALESCE(created_at, datetime('now'))
                FROM users_old;

                DROP TABLE users_old;
            """)
            conn.commit()

        # Add any missing columns silently
        for col, definition in [
            ("role",          "TEXT NOT NULL DEFAULT 'user'"),
            ("experience",    "TEXT DEFAULT 'Beginner'"),
            ("bio",           "TEXT DEFAULT ''"),
            ("portfolio",     "TEXT DEFAULT ''"),
            ("trust_score",   "REAL DEFAULT 5.0"),
            ("total_ratings", "INTEGER DEFAULT 0"),
            ("is_active",     "INTEGER DEFAULT 1"),
        ]:
            if col not in _get_columns(conn, "users"):
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
                    conn.commit()
                except Exception:
                    pass

    else:
        # Fresh install — create from scratch
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            TEXT PRIMARY KEY,
                username      TEXT UNIQUE NOT NULL,
                email         TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role          TEXT NOT NULL DEFAULT 'user',
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

    # ── Tasks ────────────────────────────────────────────────
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

    # ── Applications ─────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id         TEXT PRIMARY KEY,
            task_id    TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            message    TEXT DEFAULT '',
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(task_id, user_id)
        )
    """)

    # ── Feedback ─────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id           TEXT PRIMARY KEY,
            from_user_id TEXT NOT NULL,
            to_user_id   TEXT NOT NULL,
            rating       INTEGER NOT NULL,
            comment      TEXT DEFAULT '',
            created_at   TEXT DEFAULT (datetime('now')),
            UNIQUE(from_user_id, to_user_id)
        )
    """)

    # ── Notifications ─────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id         TEXT PRIMARY KEY,
            user_id    TEXT NOT NULL,
            title      TEXT NOT NULL,
            message    TEXT NOT NULL,
            is_read    INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


def db_fetchone(sql, params=()):
    conn = get_connection()
    try:
        row = conn.execute(sql, params).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def db_fetchall(sql, params=()):
    conn = get_connection()
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def db_execute(sql, params=()):
    conn = get_connection()
    try:
        conn.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
