from database import get_connection

def create_task(title, desc, skills, user):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO tasks (title, description, skills, created_by) VALUES (?, ?, ?, ?)",
              (title, desc, skills, user))
    conn.commit()
    conn.close()

def get_tasks():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tasks")
    tasks = c.fetchall()
    conn.close()
    return tasks
