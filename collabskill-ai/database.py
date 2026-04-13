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
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]


def init_db():
    conn = get_connection()
    c    = conn.cursor()

    existing_user_cols = _get_columns(conn, "users")

    # ── Migrate old 'name' → 'username' ──────────────────────
    if existing_user_cols and "name" in existing_user_cols and "username" not in existing_user_cols:
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
                phone_number  TEXT DEFAULT '',
                avatar_color  TEXT DEFAULT '#22d3ee',
                trust_score   REAL DEFAULT 5.0,
                total_ratings INTEGER DEFAULT 0,
                is_active     INTEGER DEFAULT 1,
                created_at    TEXT DEFAULT (datetime('now'))
            );
            INSERT INTO users
                (id, username, email, password_hash, role, skills,
                 experience, bio, portfolio, trust_score, total_ratings,
                 is_active, created_at)
            SELECT id, COALESCE(username, name), email, password_hash,
                   COALESCE(role,'user'), COALESCE(skills,''),
                   COALESCE(experience,'Beginner'), COALESCE(bio,''),
                   COALESCE(portfolio,''), COALESCE(trust_score,5.0),
                   COALESCE(total_ratings,0), COALESCE(is_active,1),
                   COALESCE(created_at,datetime('now'))
            FROM users_old;
            DROP TABLE users_old;
        """)
        conn.commit()
    elif not existing_user_cols:
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
                phone_number  TEXT DEFAULT '',
                avatar_color  TEXT DEFAULT '#22d3ee',
                trust_score   REAL DEFAULT 5.0,
                total_ratings INTEGER DEFAULT 0,
                is_active     INTEGER DEFAULT 1,
                created_at    TEXT DEFAULT (datetime('now'))
            )
        """)

    # ── Add missing columns ───────────────────────────────────
    cols_now = _get_columns(conn, "users")
    for col, defn in [
        ("role",          "TEXT NOT NULL DEFAULT 'user'"),
        ("experience",    "TEXT DEFAULT 'Beginner'"),
        ("bio",           "TEXT DEFAULT ''"),
        ("portfolio",     "TEXT DEFAULT ''"),
        ("phone_number",  "TEXT DEFAULT ''"),
        ("avatar_color",  "TEXT DEFAULT '#22d3ee'"),
        ("avatar_photo",  "BLOB DEFAULT NULL"),
        ("trust_score",   "REAL DEFAULT 5.0"),
        ("total_ratings", "INTEGER DEFAULT 0"),
        ("is_active",     "INTEGER DEFAULT 1"),
    ]:
        if col not in cols_now:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {col} {defn}")
                conn.commit()
            except Exception:
                pass

    # ── Tasks ─────────────────────────────────────────────────
    c.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id              TEXT PRIMARY KEY,
            title           TEXT NOT NULL,
            description     TEXT NOT NULL,
            skills          TEXT NOT NULL,
            category        TEXT DEFAULT 'Other',
            deadline        TEXT DEFAULT '',
            priority        TEXT DEFAULT 'Normal',
            status          TEXT DEFAULT 'open',
            type            TEXT DEFAULT 'task',
            knowledge_intent TEXT DEFAULT '',
            created_by      TEXT NOT NULL,
            created_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    task_cols = _get_columns(conn, "tasks")
    for col, defn in [
        ("type",             "TEXT DEFAULT 'task'"),
        ("knowledge_intent", "TEXT DEFAULT ''"),
    ]:
        if col not in task_cols:
            try:
                c.execute(f"ALTER TABLE tasks ADD COLUMN {col} {defn}")
                conn.commit()
            except Exception:
                pass

    # ── Applications ──────────────────────────────────────────
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

    # ── Feedback ──────────────────────────────────────────────
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


# ── Extended table initialisation ────────────────────────────
def init_extended_tables():
    """Call once on startup to create all feature tables."""
    conn = get_connection()
    try:
        from network    import init_network_tables
        from chat       import init_chat_tables
        from project_db import init_project_tables
        from learning   import init_learning_tables
        from sessions   import init_sessions_tables
        init_network_tables(conn)
        init_chat_tables(conn)
        init_project_tables(conn)
        init_learning_tables(conn)
        init_sessions_tables(conn)
    except ImportError:
        pass
    conn.close()
