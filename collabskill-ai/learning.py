# learning.py  —  CollabSkill AI
# Interest → Accept → Connect flow for Knowledge Mode
import uuid
from database import db_fetchone, db_fetchall, db_execute


# ═══════════════════════════════════════════════════════════════
#  TABLE INIT
# ═══════════════════════════════════════════════════════════════
def init_learning_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS learning_interests (
            id         TEXT PRIMARY KEY,
            post_id    TEXT NOT NULL,
            learner_id TEXT NOT NULL,
            teacher_id TEXT NOT NULL,
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(post_id, teacher_id)
        )
    """)
    conn.commit()


# ═══════════════════════════════════════════════════════════════
#  INTEREST CRUD
# ═══════════════════════════════════════════════════════════════
def express_interest(post_id: str, learner_id: str, teacher_id: str):
    """Teacher clicks 'I Can Help Teach' on a learning post."""
    existing = db_fetchone(
        "SELECT id FROM learning_interests WHERE post_id=? AND teacher_id=?",
        (post_id, teacher_id))
    if existing:
        return False, "You have already expressed interest in this post."
    db_execute("""
        INSERT INTO learning_interests (id, post_id, learner_id, teacher_id)
        VALUES (?, ?, ?, ?)
    """, (str(uuid.uuid4()), post_id, learner_id, teacher_id))
    return True, "Interest expressed successfully."


def get_interested_teachers(post_id: str):
    """Get all users who expressed interest in a learning post."""
    return db_fetchall("""
        SELECT li.*, u.username AS teacher_name, u.skills AS teacher_skills,
               u.bio AS teacher_bio, u.experience AS teacher_exp,
               u.trust_score AS teacher_trust, u.avatar_color AS teacher_color,
               u.total_ratings AS teacher_ratings
        FROM learning_interests li
        JOIN users u ON li.teacher_id = u.id
        WHERE li.post_id = ?
        ORDER BY u.trust_score DESC
    """, (post_id,))


def get_interest_count(post_id: str) -> int:
    row = db_fetchone(
        "SELECT COUNT(*) AS c FROM learning_interests WHERE post_id=?",
        (post_id,))
    return row["c"] if row else 0


def accept_teacher(interest_id: str, post_id: str):
    """Learner accepts one teacher — set others to rejected."""
    db_execute(
        "UPDATE learning_interests SET status='accepted' WHERE id=?",
        (interest_id,))
    db_execute(
        "UPDATE learning_interests SET status='rejected' "
        "WHERE post_id=? AND id!=? AND status='pending'",
        (post_id, interest_id))


def reject_interest(interest_id: str):
    db_execute(
        "UPDATE learning_interests SET status='rejected' WHERE id=?",
        (interest_id,))


def get_accepted_pair(post_id: str):
    """Return the accepted (learner_id, teacher_id) pair for a post."""
    row = db_fetchone("""
        SELECT li.learner_id, li.teacher_id,
               ul.username AS learner_name, ut.username AS teacher_name
        FROM learning_interests li
        JOIN users ul ON li.learner_id = ul.id
        JOIN users ut ON li.teacher_id = ut.id
        WHERE li.post_id=? AND li.status='accepted'
    """, (post_id,))
    return row


def is_teacher_accepted(post_id: str, teacher_id: str) -> bool:
    row = db_fetchone("""
        SELECT id FROM learning_interests
        WHERE post_id=? AND teacher_id=? AND status='accepted'
    """, (post_id, teacher_id))
    return bool(row)


def get_my_teaching_pairs(teacher_id: str):
    """All posts where this teacher was accepted."""
    return db_fetchall("""
        SELECT li.*, t.title AS post_title, t.skills,
               ul.username AS learner_name
        FROM learning_interests li
        JOIN tasks t  ON li.post_id   = t.id
        JOIN users ul ON li.learner_id = ul.id
        WHERE li.teacher_id=? AND li.status='accepted'
        ORDER BY li.created_at DESC
    """, (teacher_id,))


def get_my_learning_pairs(learner_id: str):
    """All posts where this learner accepted a teacher."""
    return db_fetchall("""
        SELECT li.*, t.title AS post_title, t.skills,
               ut.username AS teacher_name, ut.avatar_color AS teacher_color
        FROM learning_interests li
        JOIN tasks t  ON li.post_id    = t.id
        JOIN users ut ON li.teacher_id = ut.id
        WHERE li.learner_id=? AND li.status='accepted'
        ORDER BY li.created_at DESC
    """, (learner_id,))
