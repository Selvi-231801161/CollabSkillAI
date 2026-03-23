import hashlib
from database import get_connection

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_user(username, email, password, skills, bio, portfolio):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (username, email, password, skills, bio, portfolio_link)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (username, email, hash_password(password), skills, bio, portfolio))
        conn.commit()
        return True, "Registration successful!"
    except:
        return False, "Username or email already exists."
    finally:
        conn.close()

def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def update_trust_score(username, new_rating):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT trust_score, total_ratings FROM users WHERE username=?",
              (username,))
    row = c.fetchone()
    if row:
        old_score, total = row
        new_score = ((old_score * total) + new_rating) / (total + 1)
        c.execute("UPDATE users SET trust_score=?, total_ratings=? WHERE username=?",
                  (round(new_score, 2), total + 1, username))
        conn.commit()
    conn.close()
