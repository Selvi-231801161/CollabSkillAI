import json
from openai import OpenAI
from database import get_connection

# ─────────────────────────────────────────────────────────────
#  PASTE YOUR OPENAI API KEY BELOW  (inside the quotes)
#  Get your key from: https://platform.openai.com/api-keys
# ─────────────────────────────────────────────────────────────
client = OpenAI(api_key="sk-proj-paste-your-real-key-here")


def _get_users_for_matching(exclude_username):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT username, skills, experience, bio, trust_score
        FROM users WHERE username != ?
    """, (exclude_username,))
    rows = c.fetchall()
    conn.close()
    return rows


def match_users_to_task(task_title, task_description, required_skills, current_user):
    """
    Ask GPT to find the top 3 best-matching users for a given task.
    Returns: list of dicts  [{username, match_score, reason}, ...]
    Raises:  RuntimeError on API failure.
    """
    users = _get_users_for_matching(current_user)
    if not users:
        return []

    users_text = "\n".join([
        f"- Username: {u[0]} | Skills: {u[1]} | Level: {u[2]} | Bio: {u[3]} | Trust: {u[4]}/10"
        for u in users
    ])

    prompt = f"""
You are an expert AI skill-matching assistant for CollabSkill AI — a collaborative platform.

A user has posted this task:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title       : {task_title}
Description : {task_description}
Needs Skills: {required_skills}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Available platform users:
{users_text}

Instructions:
1. Compare each user's skills with the task's required skills.
2. Factor in their experience level and trust score.
3. Pick the TOP 3 best-fitting users.
4. Give each a match_score (0–100).
5. Write a clear 1–2 sentence reason for each match.

Return ONLY a valid JSON array — no markdown, no explanation, no extra text.

[
  {{"username": "exact_name", "match_score": 92, "reason": "Why this person is ideal."}},
  {{"username": "exact_name", "match_score": 78, "reason": "Why this person is a good fit."}},
  {{"username": "exact_name", "match_score": 61, "reason": "Why this person could help."}}
]
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=600
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return []
    except Exception as e:
        raise RuntimeError(f"OpenAI API error: {str(e)}")


def get_skill_suggestions(user_skills):
    """
    Given a user's current skills, suggest 5 related skills to learn next.
    Returns a plain comma-separated string.
    """
    if not user_skills or not user_skills.strip():
        return "Add your skills to your profile first to get personalised suggestions!"

    prompt = f"""
A user on a digital skill-exchange platform currently has these skills: {user_skills}

Suggest exactly 5 related skills they should learn next to become more valuable.
Return ONLY a comma-separated list of skill names. Nothing else.
Example: React, TypeScript, Node.js, GraphQL, Docker
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=80
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "Could not fetch suggestions right now. Check your API key."
