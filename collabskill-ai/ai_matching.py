import json
import os
from openai import OpenAI
from database import db_fetchall

# ✅ Secure API key (NO hardcoding)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def get_all_users_except(current_user_id: str):
    return db_fetchall("""
        SELECT id, name, skills, experience, bio, trust_score
        FROM users
        WHERE id != ? AND is_active = 1
        ORDER BY trust_score DESC
    """, (current_user_id,))


def match_users_to_task(task_title, task_description, required_skills, current_user_id):
    users = get_all_users_except(current_user_id)

    if not users:
        return []

    # Convert users to readable format
    users_text = "\n".join([
        f"- {u['name']} | Skills: {u['skills']} | Level: {u['experience']} | Trust: {u['trust_score']}/10"
        for u in users
    ])

    prompt = f"""
You are an AI that matches users to tasks.

TASK:
Title: {task_title}
Description: {task_description}
Required Skills: {required_skills}

USERS:
{users_text}

Return ONLY a valid JSON array of top 3 users like:
[
  {{"name": "User1", "match_score": 90, "reason": "Strong skill match"}},
  {{"name": "User2", "match_score": 75, "reason": "Partial match"}},
  {{"name": "User3", "match_score": 60, "reason": "Related experience"}}
]
"""

    try:
        # ✅ Updated OpenAI API (latest)
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        raw = response.output_text.strip()

        # Clean markdown if model adds it
        raw = raw.replace("```json", "").replace("```", "").strip()

        # ✅ Safe JSON parsing (prevents app crash)
        try:
            return json.loads(raw)
        except:
            return []

    except Exception as e:
        print("AI ERROR:", e)
        return []
