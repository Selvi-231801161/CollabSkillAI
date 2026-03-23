import hashlib
from database import get_connection

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def register_user(username, email, password, skills, bio, portfolio):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username,email,password,skills,bio,portfolio_link) VALUES (?,?,?,?,?,?)",
            (username,email,hash_password(password),skills,bio,portfolio)
        )
        conn.commit()
        return True,"Success"
    except:
        return False,"User exists"
    finally:
        conn.close()

def login_user(username,password):
    conn = get_connection()
    c=conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?",
              (username,hash_password(password)))
    u=c.fetchone()
    conn.close()
    return u

def update_trust_score(username,score):
    conn = get_connection()
    conn.execute("UPDATE users SET trust_score=trust_score+? WHERE username=?",
                 (score,username))
    conn.commit()
    conn.close()
