import sqlite3
import os

DB="data.db"

def init_db():
    conn=sqlite3.connect(DB)
    c=conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    username TEXT,
    email TEXT,
    password TEXT,
    skills TEXT,
    bio TEXT,
    portfolio_link TEXT,
    trust_score REAL DEFAULT 5
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY,
    title TEXT,
    description TEXT,
    required_skills TEXT,
    posted_by TEXT
    )""")

    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect(DB)
