import datetime
import sqlite3
from config import DATABASE

def get_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    with open('schema.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.close()

def load_test_data():
    conn = get_connection()
    with open('test_data.sql', 'r', encoding='utf-8') as f:
        conn.executescript(f.read())
    conn.close()

def add_user(user_id, username):
    conn = get_connection()
    conn.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()



def get_users_for_reminder(time_str):
    conn = get_connection()
    
    cursor = conn.execute("SELECT user_id FROM users WHERE reminder_time = ?", (time_str,))
    users = [row['user_id'] for row in cursor.fetchall()]
    conn.close()
    return users

def has_record_today(user_id):
    conn = get_connection()
    
    today = datetime.date.today().isoformat()
    cursor = conn.execute("SELECT 1 FROM records WHERE user_id = ? AND record_date = ?", (user_id, today))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists



def add_record(user_id, mood, work_hours, sleep_hours, comment):
    conn = get_connection()
    conn.execute("""
        INSERT INTO records (user_id, mood, work_hours, sleep_hours, comment)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, record_date) DO UPDATE SET 
            mood=excluded.mood, 
            work_hours=excluded.work_hours, 
            sleep_hours=excluded.sleep_hours, 
            comment=excluded.comment
    """, (user_id, mood, work_hours, sleep_hours, comment))
    conn.commit()
    conn.close()

def get_stats(user_id, days):
    conn = get_connection()
    cursor = conn.execute("""
        SELECT record_date, mood, work_hours, sleep_hours, comment 
        FROM records 
        WHERE user_id = ? AND record_date >= date('now', 'localtime', ?)
        ORDER BY record_date ASC
    """, (user_id, f'-{days} days'))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data

def get_history(user_id, limit=10):
    conn = get_connection()
    cursor = conn.execute("""
        SELECT record_date, mood, work_hours, sleep_hours, comment 
        FROM records 
        WHERE user_id = ? 
        ORDER BY record_date DESC LIMIT ?
    """, (user_id, limit))
    data = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return data

def clear_data(user_id):
    conn = get_connection()
    conn.execute("DELETE FROM records WHERE user_id = ?", (user_id,))
    conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def set_reminder_time(user_id, time_str):
    conn = get_connection()
    conn.execute("UPDATE users SET reminder_time = ? WHERE user_id = ?", (time_str, user_id))
    conn.commit()
    conn.close()

def get_reminder_time(user_id):
    conn = get_connection()
    cursor = conn.execute("SELECT reminder_time FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['reminder_time'] if row else None