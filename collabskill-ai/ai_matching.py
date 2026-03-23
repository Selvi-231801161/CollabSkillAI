import openai
import json
import os
from database import get_connection
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_all_users_except(current_user):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, skills FROM users WHERE username != ?", (current_user,))
    users = c.fetchall()
    conn.close()
    return users

def match_users_to_task(task_title, task_desc, skills, current_user):
    users = get_all_users_except(current_user)

    if not users:
        return []

    users_text = "\n".join([f"{u[0]}: {u[1]}" for u in users])

    prompt = f"""
Task: {task_title}
Description: {task_desc}
Skills: {skills}

Users:
{users_text}

Return top 3 matches as JSON
"""

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(response.choices[0].message.content)
    except:
        return []
