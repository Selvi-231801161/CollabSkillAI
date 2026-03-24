# ai_matching.py
import json
import os
from openai import OpenAI
from database import db_fetchall

# ── Paste your OpenAI key here directly (or set env var) ────
# Option 1: hardcode  →  client = OpenAI(api_key="sk-proj-...")
# Option 2: env var   →  set OPENAI_API_KEY in your system



client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_all_users_except(current_user_id: str):
    return db_fetchall("""
        SELECT id, name, skills, experience, bio, trust_score
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
        f"- Username: {u['name']} | Skills: {u['skills']} "
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
No markdown, no extra text.

Format:
[
  {{"name": "...", "match_score": 90, "reason": "Has all required skills"}},
  {{"name": "...", "match_score": 75, "reason": "Partial skill match"}},
  {{"name": "...", "match_score": 60, "reason": "Related experience"}}
]
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500,
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        return []
    except Exception as e:
        raise Exception(f"OpenAI Error: {e}")
