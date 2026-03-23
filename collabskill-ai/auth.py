import hashlib
from database import get_connection


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, email, password, skills, bio, portfolio, experience):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("""
            INSERT INTO users (username, email, password, skills, bio, portfolio_link, experience)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (username.strip(), email.strip(), hash_password(password),
              skills.strip(), bio.strip(), portfolio.strip(), experience))
        conn.commit()
        return True, "Registration successful!"
    except Exception:
        return False, "Username or email already exists. Please try another."
    finally:
        conn.close()


def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "SELECT * FROM users WHERE username=? AND password=?",
        (username.strip(), hash_password(password))
    )
    user = c.fetchone()
    conn.close()
    return user


def update_trust_score(username, new_rating_out_of_10):
    """Recalculate rolling average trust score (0–10)."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT trust_score, total_ratings FROM users WHERE username=?", (username,))
    row = c.fetchone()
    if row:
        old_score, total = row
        updated = ((old_score * total) + new_rating_out_of_10) / (total + 1)
        c.execute(
            "UPDATE users SET trust_score=?, total_ratings=? WHERE username=?",
            (round(min(updated, 10.0), 2), total + 1, username)
        )
        conn.commit()
    conn.close()
