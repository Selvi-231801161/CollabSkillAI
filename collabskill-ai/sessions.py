# sessions.py  —  CollabSkill AI
# Session booking between learner and teacher
import uuid
from database import db_fetchone, db_fetchall, db_execute


# ═══════════════════════════════════════════════════════════════
#  TABLE INIT
# ═══════════════════════════════════════════════════════════════
def init_sessions_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id           TEXT PRIMARY KEY,
            learner_id   TEXT NOT NULL,
            teacher_id   TEXT NOT NULL,
            post_id      TEXT DEFAULT '',
            topic        TEXT DEFAULT '',
            date         TEXT NOT NULL,
            time         TEXT NOT NULL,
            duration     TEXT DEFAULT '1 hour',
            session_type TEXT DEFAULT 'Video Call',
            notes        TEXT DEFAULT '',
            status       TEXT DEFAULT 'scheduled',
            created_at   TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(learner_id) REFERENCES users(id),
            FOREIGN KEY(teacher_id) REFERENCES users(id)
        )
    """)
    conn.commit()


# ═══════════════════════════════════════════════════════════════
#  SESSION CRUD
# ═══════════════════════════════════════════════════════════════
def book_session(learner_id: str, teacher_id: str, post_id: str,
                 topic: str, date: str, time: str,
                 duration: str, session_type: str, notes: str = "") -> str:
    sid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO sessions
            (id, learner_id, teacher_id, post_id, topic, date, time,
             duration, session_type, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (sid, learner_id, teacher_id, post_id, topic,
          date, time, duration, session_type, notes))
    return sid


def get_my_sessions(user_id: str):
    """Sessions where user is learner or teacher, ordered by date."""
    return db_fetchall("""
        SELECT s.*,
               ul.username AS learner_name, ul.avatar_color AS learner_color,
               ut.username AS teacher_name, ut.avatar_color AS teacher_color
        FROM sessions s
        JOIN users ul ON s.learner_id = ul.id
        JOIN users ut ON s.teacher_id = ut.id
        WHERE s.learner_id=? OR s.teacher_id=?
        ORDER BY s.date ASC, s.time ASC
    """, (user_id, user_id))


def get_upcoming_sessions(user_id: str):
    from datetime import date
    today = str(date.today())
    return db_fetchall("""
        SELECT s.*,
               ul.username AS learner_name, ul.avatar_color AS learner_color,
               ut.username AS teacher_name, ut.avatar_color AS teacher_color
        FROM sessions s
        JOIN users ul ON s.learner_id = ul.id
        JOIN users ut ON s.teacher_id = ut.id
        WHERE (s.learner_id=? OR s.teacher_id=?)
          AND s.date >= ? AND s.status='scheduled'
        ORDER BY s.date ASC, s.time ASC
    """, (user_id, user_id, today))


def get_past_sessions(user_id: str):
    from datetime import date
    today = str(date.today())
    return db_fetchall("""
        SELECT s.*,
               ul.username AS learner_name, ul.avatar_color AS learner_color,
               ut.username AS teacher_name, ut.avatar_color AS teacher_color
        FROM sessions s
        JOIN users ul ON s.learner_id = ul.id
        JOIN users ut ON s.teacher_id = ut.id
        WHERE (s.learner_id=? OR s.teacher_id=?)
          AND (s.date < ? OR s.status='completed')
        ORDER BY s.date DESC
    """, (user_id, user_id, today))


def mark_session_complete(session_id: str):
    db_execute("UPDATE sessions SET status='completed' WHERE id=?", (session_id,))


def count_sessions(user_id: str) -> int:
    row = db_fetchone("""
        SELECT COUNT(*) AS c FROM sessions
        WHERE (learner_id=? OR teacher_id=?) AND status='completed'
    """, (user_id, user_id))
    return row["c"] if row else 0
