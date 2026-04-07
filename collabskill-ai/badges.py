# badges.py  —  CollabSkill AI  |  Badge & Trust Score System
from database import db_fetchone, db_fetchall


# ═══════════════════════════════════════════════════════════════
#  TRUST SCORE
# ═══════════════════════════════════════════════════════════════
def compute_trust_score(user_id: str) -> int:
    """
    Trust Score = (completed_tasks × 2) + (avg_rating × 10)
                + (profile_complete × 5) + (knowledge_count × 3)
    Capped at 100.
    """
    u = db_fetchone("SELECT * FROM users WHERE id=?", (user_id,))
    if not u:
        return 0

    completed = db_fetchone("""
        SELECT COUNT(*) AS c FROM tasks
        WHERE created_by=? AND status='closed' AND type='task'
    """, (user_id,))["c"]

    know_posts = db_fetchone("""
        SELECT COUNT(*) AS c FROM tasks
        WHERE created_by=? AND type='knowledge'
    """, (user_id,))["c"]

    ratings_row = db_fetchone("""
        SELECT AVG(rating) AS avg_r, COUNT(*) AS cnt
        FROM feedback WHERE to_user_id=?
    """, (user_id,))
    avg_rating = float(ratings_row["avg_r"] or 0)

    # Profile completeness: 1 point each for bio, skills, portfolio
    complete = sum([
        1 if u.get("bio")       else 0,
        1 if u.get("skills")    else 0,
        1 if u.get("portfolio") else 0,
    ])

    score = (completed * 2) + (avg_rating * 10) + (complete * 5) + (know_posts * 3)
    return min(int(round(score)), 100)


# ═══════════════════════════════════════════════════════════════
#  BADGE DEFINITIONS
# ═══════════════════════════════════════════════════════════════
_BADGE_DEFS = [
    # (key, label, category, condition_fn)
    # Performance
    ("top_contributor",    "Top Contributor",      "Performance",
     lambda d: d["completed"] >= 5),
    ("task_expert",        "Task Expert",           "Performance",
     lambda d: d["avg_rating"] >= 4),
    ("rising_star",        "Rising Star",           "Performance",
     lambda d: d["total_tasks"] >= 1 and d["total_tasks"] <= 3),
    ("elite_performer",    "Elite Performer",       "Performance",
     lambda d: d["trust"] > 80),
    # Learning
    ("mentor",             "Mentor",                "Learning",
     lambda d: d["know_teach"] >= 5),
    ("knowledge_sharer",   "Knowledge Sharer",      "Learning",
     lambda d: d["know_posts"] >= 3),
    ("skill_master",       "Skill Master",          "Learning",
     lambda d: d["avg_rating"] >= 4.5 and d["total_ratings"] >= 3),
    # Engagement
    ("active_collaborator","Active Collaborator",   "Engagement",
     lambda d: d["applications"] >= 3),
    ("team_player",        "Team Player",           "Engagement",
     lambda d: d["collab_count"] >= 2),
    ("consistent_user",    "Consistent User",       "Engagement",
     lambda d: d["total_tasks"] >= 5),
    # Trust
    ("highly_rated",       "Highly Rated",          "Trust",
     lambda d: d["avg_rating"] >= 4.5 and d["total_ratings"] >= 5),
    ("trusted_user",       "Trusted User",          "Trust",
     lambda d: d["trust"] >= 70),
    ("verified_user",      "Verified User",         "Trust",
     lambda d: bool(d["has_bio"] and d["has_skills"] and d["has_portfolio"])),
]

_BADGE_COLORS = {
    "Performance": "#2563EB",
    "Learning":    "#0D9488",
    "Engagement":  "#7C3AED",
    "Trust":       "#D97706",
}


def assign_badges(user_id: str) -> list:
    """
    Evaluate all badge conditions and return list of earned badge dicts.
    Each dict: {key, label, category, color}
    """
    u = db_fetchone("SELECT * FROM users WHERE id=?", (user_id,))
    if not u:
        return []

    completed = db_fetchone("""
        SELECT COUNT(*) AS c FROM tasks
        WHERE created_by=? AND status='closed' AND type='task'
    """, (user_id,))["c"]

    total_tasks = db_fetchone("""
        SELECT COUNT(*) AS c FROM tasks WHERE created_by=? AND type='task'
    """, (user_id,))["c"]

    know_posts = db_fetchone("""
        SELECT COUNT(*) AS c FROM tasks WHERE created_by=? AND type='knowledge'
    """, (user_id,))["c"]

    know_teach = db_fetchone("""
        SELECT COUNT(*) AS c FROM tasks
        WHERE created_by=? AND type='knowledge' AND knowledge_intent='teach'
    """, (user_id,))["c"]

    ratings_row = db_fetchone("""
        SELECT AVG(rating) AS avg_r, COUNT(*) AS cnt
        FROM feedback WHERE to_user_id=?
    """, (user_id,))
    avg_rating    = float(ratings_row["avg_r"] or 0)
    total_ratings = int(ratings_row["cnt"] or 0)

    applications = db_fetchone("""
        SELECT COUNT(*) AS c FROM applications WHERE user_id=?
    """, (user_id,))["c"]

    # count unique task owners they collaborated with
    collab_count = db_fetchone("""
        SELECT COUNT(DISTINCT t.created_by) AS c
        FROM applications a JOIN tasks t ON a.task_id = t.id
        WHERE a.user_id=?
    """, (user_id,))["c"]

    trust = compute_trust_score(user_id)

    data = {
        "completed":      completed,
        "total_tasks":    total_tasks,
        "know_posts":     know_posts,
        "know_teach":     know_teach,
        "avg_rating":     avg_rating,
        "total_ratings":  total_ratings,
        "applications":   applications,
        "collab_count":   collab_count,
        "trust":          trust,
        "has_bio":        bool(u.get("bio")),
        "has_skills":     bool(u.get("skills")),
        "has_portfolio":  bool(u.get("portfolio")),
    }

    earned = []
    for key, label, category, condition in _BADGE_DEFS:
        try:
            if condition(data):
                earned.append({
                    "key":      key,
                    "label":    label,
                    "category": category,
                    "color":    _BADGE_COLORS.get(category, "#64748B"),
                })
        except Exception:
            pass
    return earned


def render_badges_html(badges: list) -> str:
    """Return an HTML string showing badge pills grouped by category."""
    if not badges:
        return "<div style='color:#94A3B8;font-size:12px;'>No badges earned yet. Complete tasks and collaborations to earn badges.</div>"

    by_cat: dict = {}
    for b in badges:
        by_cat.setdefault(b["category"], []).append(b)

    html = ""
    for cat, items in by_cat.items():
        color = _BADGE_COLORS.get(cat, "#64748B")
        html += f"""
        <div style='margin-bottom:10px;'>
            <div style='font-size:10px;font-weight:700;text-transform:uppercase;
                letter-spacing:.08em;color:{color};margin-bottom:6px;'>{cat}</div>
            <div>
        """
        for b in items:
            html += f"""
            <span style='display:inline-flex;align-items:center;gap:4px;
                background:{color}18;color:{color};
                border:1px solid {color}30;border-radius:999px;
                padding:4px 12px;font-size:11px;font-weight:600;
                margin:3px 3px 3px 0;'>
                {b['label']}
            </span>"""
        html += "</div></div>"
    return html
