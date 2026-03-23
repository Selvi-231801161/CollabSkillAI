from database import get_connection

def register_user(username, email, password, skills, bio, portfolio):

    conn = get_connection()
    c = conn.cursor()

    # CHECK USERNAME ONLY (IMPORTANT)
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    existing_user = c.fetchone()

    if existing_user:
        conn.close()
        return False, "Username already exists"

    # INSERT NEW USER
    c.execute("""
        INSERT INTO users (username, email, password, skills, bio, portfolio, trust_score)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (username, email, password, skills, bio, portfolio, 0))

    conn.commit()
    conn.close()

    return True, "User registered successfully"


def login_user(username, password):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT * FROM users WHERE username = ? AND password = ?
    """, (username, password))

    user = c.fetchone()
    conn.close()

    return user
