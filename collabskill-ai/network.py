# network.py  —  CollabSkill AI  |  Network / Connection System
import uuid
from database import db_fetchone, db_fetchall, db_execute


# ═══════════════════════════════════════════════════════════════
#  DB SETUP  (called from database.init_db)
# ═══════════════════════════════════════════════════════════════
def init_network_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS connections (
            id       TEXT PRIMARY KEY,
            sender   TEXT NOT NULL,
            receiver TEXT NOT NULL,
            status   TEXT DEFAULT 'pending',
            mode     TEXT DEFAULT 'work',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(sender, receiver)
        )
    """)
    conn.commit()


# ═══════════════════════════════════════════════════════════════
#  CONNECTION CRUD
# ═══════════════════════════════════════════════════════════════
def send_request(sender_id: str, receiver_id: str, mode: str = "work"):
    existing = db_fetchone("""
        SELECT * FROM connections
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
    """, (sender_id, receiver_id, receiver_id, sender_id))
    if existing:
        return False, "Request already exists."
    db_execute("""
        INSERT INTO connections (id, sender, receiver, status, mode)
        VALUES (?, ?, ?, 'pending', ?)
    """, (str(uuid.uuid4()), sender_id, receiver_id, mode))
    return True, "Request sent."


def accept_request(connection_id: str):
    db_execute("UPDATE connections SET status='accepted' WHERE id=?", (connection_id,))


def reject_request(connection_id: str):
    db_execute("UPDATE connections SET status='rejected' WHERE id=?", (connection_id,))


def get_connection_status(user_a: str, user_b: str) -> str:
    """Returns 'accepted', 'pending', 'rejected', or 'none'."""
    row = db_fetchone("""
        SELECT status FROM connections
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
    """, (user_a, user_b, user_b, user_a))
    return row["status"] if row else "none"


def get_incoming_requests(user_id: str):
    """Pending requests sent TO this user."""
    return db_fetchall("""
        SELECT c.*, u.username AS sender_name, u.skills AS sender_skills,
               u.avatar_color AS sender_color, u.experience AS sender_exp
        FROM connections c JOIN users u ON c.sender = u.id
        WHERE c.receiver = ? AND c.status = 'pending'
        ORDER BY c.created_at DESC
    """, (user_id,))


def get_my_network(user_id: str):
    """All accepted connections for this user."""
    rows = db_fetchall("""
        SELECT c.*,
            CASE WHEN c.sender=? THEN c.receiver ELSE c.sender END AS partner_id
        FROM connections c
        WHERE (c.sender=? OR c.receiver=?) AND c.status='accepted'
    """, (user_id, user_id, user_id))

    result = []
    for r in rows:
        partner = db_fetchone("""
            SELECT id, username, skills, bio, avatar_color, experience, trust_score
            FROM users WHERE id=?
        """, (r["partner_id"],))
        if partner:
            result.append(partner)
    return result


def get_connection_count(user_id: str) -> int:
    row = db_fetchone("""
        SELECT COUNT(*) AS c FROM connections
        WHERE (sender=? OR receiver=?) AND status='accepted'
    """, (user_id, user_id))
    return row["c"] if row else 0
