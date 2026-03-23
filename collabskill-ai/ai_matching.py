import json
import os
from openai import OpenAI
from database import get_connection
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_all_users_except(current_user):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT username, skills, bio, trust_score
        FROM users WHERE username != ?
    """, (current_user,))
    users = c.fetchall()
    conn.close()
    return users

def match_users_to_task(task_title, task_description, required_skills, current_user):
    users = get_all_users_except(current_user)

    if not users:
        return []

    users_text = "\n".join([
        f"- Username: {u[0]}, Skills: {u[1]}, Bio: {u[2]}, Trust: {u[3]}"
        for u in users
    ])

    prompt = f"""
You are a skill-matching AI for a collaboration platform.

TASK:
Title: {task_title}
Description: {task_description}
Required Skills: {required_skills}

AVAILABLE USERS:
{users_text}

Return TOP 3 best matches as JSON array ONLY. No extra text.
Format:
[
  {{"username": "...", "match_score": 85, "reason": "explanation here"}},
  {{"username": "...", "match_score": 75, "reason": "explanation here"}},
  {{"username": "...", "match_score": 65, "reason": "explanation here"}}
]
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    try:
        return json.loads(raw)
    except:
        return []
```

3. **Ctrl + S** → close

---

## 🔑 PHASE 6 — Add Your API Key

1. Open File Explorer → `collabskill-ai` folder
2. You'll see a file called `.env` — right-click it → **Open with** → **Notepad**
3. Type this inside:
```
OPENAI_API_KEY=your_actual_key_here
