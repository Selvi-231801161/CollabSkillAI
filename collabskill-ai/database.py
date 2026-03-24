# database.py
import sqlite3
import os

DB_PATH = "collabskill.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_connection()
    c = conn.cursor()

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
