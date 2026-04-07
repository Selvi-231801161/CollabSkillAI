# chat.py  —  CollabSkill AI  |  Chat System (1:1 + Group)
import uuid
from database import db_fetchone, db_fetchall, db_execute


# ═══════════════════════════════════════════════════════════════
#  DB SETUP
# ═══════════════════════════════════════════════════════════════
def init_chat_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id         TEXT PRIMARY KEY,
            sender_id  TEXT NOT NULL,
            receiver_id TEXT,
            group_id   TEXT,
            message    TEXT NOT NULL,
            msg_type   TEXT DEFAULT 'text',
            timestamp  TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(sender_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_groups (
            id         TEXT PRIMARY KEY,
            name       TEXT NOT NULL,
            project_id TEXT,
            created_by TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_group_members (
            group_id  TEXT NOT NULL,
            user_id   TEXT NOT NULL,
            joined_at TEXT DEFAULT (datetime('now')),
            PRIMARY KEY(group_id, user_id)
        )
    """)
    conn.commit()


# ═══════════════════════════════════════════════════════════════
#  1:1 MESSAGES
# ═══════════════════════════════════════════════════════════════
def send_message(sender_id: str, receiver_id: str, message: str,
                 msg_type: str = "text"):
    db_execute("""
        INSERT INTO chat_messages (id, sender_id, receiver_id, message, msg_type)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), sender_id, receiver_id, message, msg_type))


def get_messages(user_a: str, user_b: str, limit: int = 50):
    return db_fetchall("""
        SELECT m.*, u.username AS sender_name, u.avatar_color AS sender_color
        FROM chat_messages m JOIN users u ON m.sender_id = u.id
        WHERE ((m.sender_id=? AND m.receiver_id=?)
            OR (m.sender_id=? AND m.receiver_id=?))
          AND m.group_id IS NULL
        ORDER BY m.timestamp ASC LIMIT ?
    """, (user_a, user_b, user_b, user_a, limit))


def get_conversations(user_id: str):
    """List of user_ids this user has chatted with, most recent first."""
    rows = db_fetchall("""
        SELECT DISTINCT
            CASE WHEN sender_id=? THEN receiver_id ELSE sender_id END AS partner_id,
            MAX(timestamp) AS last_ts
        FROM chat_messages
        WHERE (sender_id=? OR receiver_id=?) AND group_id IS NULL
        GROUP BY partner_id
        ORDER BY last_ts DESC
    """, (user_id, user_id, user_id))
    result = []
    for r in rows:
        u = db_fetchone("SELECT id,username,avatar_color,skills FROM users WHERE id=?",
                        (r["partner_id"],))
        if u:
            result.append(u)
    return result


def get_unread_chat_count(user_id: str) -> int:
    row = db_fetchone("""
        SELECT COUNT(*) AS c FROM chat_messages
        WHERE receiver_id=? AND group_id IS NULL
    """, (user_id,))
    return row["c"] if row else 0


# ═══════════════════════════════════════════════════════════════
#  GROUP MESSAGES
# ═══════════════════════════════════════════════════════════════
def create_group(name: str, created_by: str,
                 project_id: str = None) -> str:
    gid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO chat_groups (id, name, project_id, created_by)
        VALUES (?, ?, ?, ?)
    """, (gid, name, project_id, created_by))
    add_member_to_group(gid, created_by)
    return gid


def add_member_to_group(group_id: str, user_id: str):
    try:
        db_execute("""
            INSERT OR IGNORE INTO chat_group_members (group_id, user_id)
            VALUES (?, ?)
        """, (group_id, user_id))
    except Exception:
        pass


def send_group_message(sender_id: str, group_id: str,
                       message: str, msg_type: str = "text"):
    db_execute("""
        INSERT INTO chat_messages (id, sender_id, group_id, message, msg_type)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), sender_id, group_id, message, msg_type))


def get_group_messages(group_id: str, limit: int = 100):
    return db_fetchall("""
        SELECT m.*, u.username AS sender_name, u.avatar_color AS sender_color
        FROM chat_messages m JOIN users u ON m.sender_id = u.id
        WHERE m.group_id=?
        ORDER BY m.timestamp ASC LIMIT ?
    """, (group_id, limit))


def get_user_groups(user_id: str):
    return db_fetchall("""
        SELECT g.* FROM chat_groups g
        JOIN chat_group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ?
        ORDER BY g.created_at DESC
    """, (user_id,))


def get_group_members(group_id: str):
    return db_fetchall("""
        SELECT u.id, u.username, u.skills, u.avatar_color, u.experience
        FROM chat_group_members gm JOIN users u ON gm.user_id = u.id
        WHERE gm.group_id = ?
    """, (group_id,))
