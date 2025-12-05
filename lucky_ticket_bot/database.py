# database.py
import sqlite3

def init_db():
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            display_name TEXT,
            tickets INTEGER DEFAULT 0
        )
    ''')
    cur.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            task_type TEXT,
            content TEXT,
            status TEXT DEFAULT 'pending',  -- pending / approved / rejected
            awarded_tickets INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    return row

def create_user(user_id, username, display_name):
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (user_id, username, display_name, tickets)
        VALUES (?, ?, ?, 0)
    ''', (user_id, username, display_name))
    conn.commit()
    conn.close()

def add_tickets(user_id, amount):
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('UPDATE users SET tickets = tickets + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

def get_tickets(user_id):
    user = get_user(user_id)
    return user[4] if user else 0

def get_top_users(limit=20):
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('SELECT display_name, tickets FROM users ORDER BY tickets DESC LIMIT ?', (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def create_submission(user_id, task_type, content):
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO submissions (user_id, task_type, content)
        VALUES (?, ?, ?)
    ''', (user_id, task_type, content))
    submission_id = cur.lastrowid
    conn.commit()
    conn.close()
    return submission_id

def get_pending_submissions():
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('SELECT * FROM submissions WHERE status = "pending"')
    rows = cur.fetchall()
    conn.close()
    return rows

def approve_submission(submission_id, tickets):
    conn = sqlite3.connect('lucky.db')
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM submissions WHERE id = ?', (submission_id,))
    row = cur.fetchone()
    if row:
        user_id = row[0]
        cur.execute('UPDATE submissions SET status = "approved", awarded_tickets = ? WHERE id = ?', (tickets, submission_id))
        add_tickets(user_id, tickets)
    conn.commit()
    conn.close()