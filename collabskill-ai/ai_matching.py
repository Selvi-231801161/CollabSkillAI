import openai
import json
import os
from database import get_connection
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

def get_users(current_user):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT username, skills FROM users WHERE username != ?", (current_user,))
    data = c.fetchall()
    conn.close()
    return data

def match_users_to_task(title, desc, skills, current_user):
    users = get_users(current_user)

    text = "\n".join([f"{u[0]}: {u[1]}" for u in users])

    prompt = f"""
Task: {title}
Description: {desc}
Skills: {skills}

Users:
{text}

Return JSON list
"""

    res = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    try:
        return json.loads(res.choices[0].message.content)
    except:
        return []
