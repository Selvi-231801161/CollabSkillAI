from database import get_connection

def send_message(sender, receiver, msg):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender, receiver, message) VALUES (?, ?, ?)",
              (sender, receiver, msg))
    conn.commit()
    conn.close()

def get_messages(user1, user2):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT sender, message FROM messages
        WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)
    """, (user1, user2, user2, user1))
    data = c.fetchall()
    conn.close()
    return data
