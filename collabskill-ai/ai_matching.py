# ai_matching.py  —  CollabSkill AI
# Fully LOCAL AI matching — no API key, no internet required.
# Uses TF-IDF + Cosine Similarity (scikit-learn) + Skill Overlap.
import re
from database import db_fetchall

# ── Optional scikit-learn ────────────────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as _cosine
    _SKLEARN = True
except ImportError:
    _SKLEARN = False


# ═══════════════════════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════════════════════
def _tokenize(text: str) -> set:
    """Lower-case word set from a string."""
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def get_text_similarity(text_a: str, text_b: str) -> float:
    """
    Returns a [0,1] cosine similarity score between two text strings.
    Falls back to simple Jaccard if scikit-learn is unavailable.
    """
    if not text_a or not text_b:
        return 0.0
    if _SKLEARN:
        try:
            vec = TfidfVectorizer().fit_transform([text_a, text_b])
            return float(_cosine(vec[0], vec[1])[0][0])
        except Exception:
            pass
    # Jaccard fallback
    a, b = _tokenize(text_a), _tokenize(text_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def get_skill_overlap(skills_a: str, skills_b: str) -> int:
    """Count of skills that appear in both skill strings."""
    return len(_tokenize(skills_a) & _tokenize(skills_b))


def get_match_score(user_skills: str, user_bio: str,
                    target_skills: str, target_desc: str) -> float:
    """
    final_score = (skill_overlap × 10) + (text_similarity × 100)
    Capped at 100.
    """
    overlap  = get_skill_overlap(user_skills, target_skills)
    sim      = get_text_similarity(
        f"{user_skills} {user_bio}",
        f"{target_skills} {target_desc}")
    score    = (overlap * 10) + (sim * 100)
    return round(min(score, 100), 1)


# ═══════════════════════════════════════════════════════════════
#  USER FETCHING
# ═══════════════════════════════════════════════════════════════
def get_all_users_except(current_user_id: str):
    return db_fetchall("""
        SELECT id, username, skills, experience, bio, trust_score, avatar_color
        FROM users
        WHERE id != ? AND is_active = 1
        ORDER BY trust_score DESC
    """, (current_user_id,))


# ═══════════════════════════════════════════════════════════════
#  MATCH USERS TO TASK  (used by AI Match page)
# ═══════════════════════════════════════════════════════════════
def match_users_to_task(task_title: str, task_description: str,
                        required_skills: str, current_user_id: str):
    """
    Returns list of dicts: {name, match_score, reason}
    Sorted descending by match_score. Top 3.
    """
    users   = get_all_users_except(current_user_id)
    results = []
    for u in users:
        score  = get_match_score(
            u.get("skills", ""), u.get("bio", ""),
            required_skills, f"{task_title} {task_description}")
        if score > 0:
            overlap = get_skill_overlap(u.get("skills",""), required_skills)
            reason  = (f"Skill match: {overlap} overlap(s). "
                       f"Profile similarity with task requirements.")
            results.append({
                "name":        u["username"],
                "match_score": score,
                "reason":      reason,
            })
    results.sort(key=lambda x: x["match_score"], reverse=True)
    return results[:3]


# ═══════════════════════════════════════════════════════════════
#  DASHBOARD RECOMMENDATIONS  (used by dashboard AI section)
# ═══════════════════════════════════════════════════════════════
def recommend_tasks_for_user(user_id: str, user_skills: str,
                              user_bio: str, entry_type: str = "task",
                              top_n: int = 5):
    """
    Recommend open tasks/knowledge posts whose required skills
    best match this user's skills.
    Returns list of (task_dict, score).
    """
    tasks = db_fetchall("""
        SELECT t.*, u.username AS creator_name
        FROM tasks t JOIN users u ON t.created_by = u.id
        WHERE t.status = 'open'
          AND t.type   = ?
          AND t.created_by != ?
        ORDER BY t.created_at DESC
        LIMIT 100
    """, (entry_type, user_id))

    results = []
    for t in tasks:
        score = get_match_score(
            user_skills, user_bio,
            t.get("skills", ""), t.get("description", ""))
        results.append((t, score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]


def recommend_users_for_collaboration(user_id: str, user_skills: str,
                                       user_bio: str, top_n: int = 5):
    """
    Recommend other users whose skills best complement this user.
    Returns list of (user_dict, score).
    """
    users   = get_all_users_except(user_id)
    results = []
    for u in users:
        score = get_match_score(
            user_skills, user_bio,
            u.get("skills", ""), u.get("bio", ""))
        results.append((u, score))
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]
