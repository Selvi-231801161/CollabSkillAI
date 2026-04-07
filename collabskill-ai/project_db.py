# project_db.py  —  CollabSkill AI  |  Project / Team System
import uuid
from database import db_fetchone, db_fetchall, db_execute


# ═══════════════════════════════════════════════════════════════
#  DB SETUP
# ═══════════════════════════════════════════════════════════════
def init_project_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id             TEXT PRIMARY KEY,
            creator_id     TEXT NOT NULL,
            title          TEXT NOT NULL,
            description    TEXT DEFAULT '',
            skills_required TEXT DEFAULT '',
            duration        TEXT DEFAULT '',
            team_size       INTEGER DEFAULT 0,
            status          TEXT DEFAULT 'active',
            group_chat_id   TEXT DEFAULT '',
            created_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(creator_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_members (
            project_id TEXT NOT NULL,
            user_id    TEXT NOT NULL,
            role       TEXT DEFAULT 'member',
            joined_at  TEXT DEFAULT (datetime('now')),
            PRIMARY KEY(project_id, user_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_invites (
            id         TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            sender_id  TEXT NOT NULL,
            receiver_id TEXT NOT NULL,
            status     TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(project_id, receiver_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_resources (
            id         TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            posted_by  TEXT NOT NULL,
            res_type   TEXT DEFAULT 'note',
            content    TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()


# ═══════════════════════════════════════════════════════════════
#  PROJECT CRUD
# ═══════════════════════════════════════════════════════════════
def create_project(creator_id, title, description,
                   skills_required, duration="", team_size=0) -> str:
    pid = str(uuid.uuid4())
    db_execute("""
        INSERT INTO projects
            (id, creator_id, title, description, skills_required, duration, team_size)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (pid, creator_id, title, description, skills_required, duration, team_size))
    # Auto-add creator as member/owner
    db_execute("""
        INSERT OR IGNORE INTO project_members (project_id, user_id, role)
        VALUES (?, ?, 'owner')
    """, (pid, creator_id))
    return pid


def get_project(project_id: str):
    return db_fetchone("""
        SELECT p.*, u.username AS creator_name
        FROM projects p JOIN users u ON p.creator_id = u.id
        WHERE p.id=?
    """, (project_id,))


def get_my_projects(user_id: str):
    return db_fetchall("""
        SELECT DISTINCT p.*, u.username AS creator_name,
            (SELECT COUNT(*) FROM project_members pm WHERE pm.project_id=p.id) AS member_count
        FROM projects p
        JOIN users u ON p.creator_id = u.id
        JOIN project_members m ON m.project_id = p.id
        WHERE m.user_id = ?
        ORDER BY p.created_at DESC
    """, (user_id,))


def update_project_chat(project_id: str, group_chat_id: str):
    db_execute("UPDATE projects SET group_chat_id=? WHERE id=?",
               (group_chat_id, project_id))


# ═══════════════════════════════════════════════════════════════
#  INVITATIONS
# ═══════════════════════════════════════════════════════════════
def send_project_invite(project_id: str, sender_id: str, receiver_id: str):
    existing = db_fetchone("""
        SELECT id FROM project_invites
        WHERE project_id=? AND receiver_id=?
    """, (project_id, receiver_id))
    if existing:
        return False, "Invitation already sent."
    db_execute("""
        INSERT INTO project_invites (id, project_id, sender_id, receiver_id)
        VALUES (?, ?, ?, ?)
    """, (str(uuid.uuid4()), project_id, sender_id, receiver_id))
    return True, "Invitation sent."


def get_pending_invites(user_id: str):
    return db_fetchall("""
        SELECT pi.*, p.title AS project_title, p.description,
               p.skills_required, u.username AS sender_name
        FROM project_invites pi
        JOIN projects p ON pi.project_id = p.id
        JOIN users u ON pi.sender_id = u.id
        WHERE pi.receiver_id=? AND pi.status='pending'
        ORDER BY pi.created_at DESC
    """, (user_id,))


def accept_project_invite(invite_id: str, user_id: str, project_id: str):
    db_execute("UPDATE project_invites SET status='accepted' WHERE id=?", (invite_id,))
    db_execute("""
        INSERT OR IGNORE INTO project_members (project_id, user_id, role)
        VALUES (?, ?, 'member')
    """, (project_id, user_id))


def reject_project_invite(invite_id: str):
    db_execute("UPDATE project_invites SET status='rejected' WHERE id=?", (invite_id,))


# ═══════════════════════════════════════════════════════════════
#  MEMBERS
# ═══════════════════════════════════════════════════════════════
def get_project_members(project_id: str):
    return db_fetchall("""
        SELECT pm.*, u.username, u.skills, u.experience,
               u.avatar_color, u.trust_score
        FROM project_members pm JOIN users u ON pm.user_id = u.id
        WHERE pm.project_id=?
    """, (project_id,))


def is_project_member(project_id: str, user_id: str) -> bool:
    row = db_fetchone("""
        SELECT 1 FROM project_members WHERE project_id=? AND user_id=?
    """, (project_id, user_id))
    return bool(row)


# ═══════════════════════════════════════════════════════════════
#  RESOURCES
# ═══════════════════════════════════════════════════════════════
def add_resource(project_id: str, posted_by: str,
                 content: str, res_type: str = "note"):
    db_execute("""
        INSERT INTO project_resources (id, project_id, posted_by, res_type, content)
        VALUES (?, ?, ?, ?, ?)
    """, (str(uuid.uuid4()), project_id, posted_by, res_type, content))


def get_resources(project_id: str):
    return db_fetchall("""
        SELECT r.*, u.username AS poster_name
        FROM project_resources r JOIN users u ON r.posted_by = u.id
        WHERE r.project_id=?
        ORDER BY r.created_at DESC
    """, (project_id,))
