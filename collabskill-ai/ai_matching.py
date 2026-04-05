# ai_matching.py
import json
import os
from database import db_fetchall


def _get_client():
    try:
        from openai import OpenAI
    except ImportError:
        raise Exception("openai package not installed. Add 'openai' to requirements.txt")

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise Exception(
            "OpenAI API key not set.\n"
            "Go to Streamlit Cloud → Manage App → Settings → Secrets and add:\n"
            "OPENAI_API_KEY = \"sk-proj-your-key\""
        )
    from openai import OpenAI
    return OpenAI(api_key=api_key)


def get_all_users_except(current_user_id: str):
    # FIX: was querying 'name' — column is 'username'
    return db_fetchall("""
        SELECT id, username, skills, experience, bio, trust_score
        FROM users
        WHERE id != ? AND is_active = 1
        ORDER BY trust_score DESC
    """, (current_user_id,))


def match_users_to_task(task_title: str, task_description: str,
                        required_skills: str, current_user_id: str):
    users = get_all_users_except(current_user_id)
    if not users:
        return []

    users_text = "\n".join([
        f"- Username: {u['username']} | Skills: {u['skills']} "
        f"| Level: {u['experience']} | Bio: {u['bio']} | Trust: {u['trust_score']}/10"
        for u in users
    ])

    prompt = f"""
You are an expert skill-matching AI for CollabSkill AI.

TASK:
Title: {task_title}
Description: {task_description}
Required Skills: {required_skills}

AVAILABLE USERS:
{users_text}

Return the TOP 3 best matching users as a JSON array ONLY.
No markdown, no extra text outside the JSON.

Format:
[
  {{"name": "username1", "match_score": 90, "reason": "Explanation"}},
  {{"name": "username2", "match_score": 75, "reason": "Explanation"}},
  {{"name": "username3", "match_score": 60, "reason": "Explanation"}}
]
"""
    client = _get_client()

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []
