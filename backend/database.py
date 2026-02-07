import sqlite3
import json
import logging
import os
from datetime import datetime

DB_NAME = "/data/titan_mvp.db" if os.path.exists("/data") else "titan_mvp.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance INTEGER DEFAULT 0,
        is_admin BOOLEAN DEFAULT 0,
        joined_date TEXT,
        strategy_data TEXT, 
        timezone_offset INTEGER DEFAULT 3
    )''')
    
    # Promocodes Table
    c.execute('''CREATE TABLE IF NOT EXISTS promocodes (
        code TEXT PRIMARY KEY,
        value INTEGER DEFAULT 1,
        activations_left INTEGER DEFAULT 999
    )''')
    
    # Seed Promocodes if empty
    c.execute("SELECT count(*) FROM promocodes")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO promocodes (code, value) VALUES ('MVP2026', 100)")
        c.execute("INSERT INTO promocodes (code, value) VALUES ('VIPSTART', 100)")
    
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def create_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    try:
        c = conn.cursor()
        now = datetime.now().isoformat()
        c.execute("INSERT OR IGNORE INTO users (user_id, username, joined_date) VALUES (?, ?, ?)", 
                  (user_id, username, now))
        conn.commit()
    except Exception as e:
        logging.error(f"DB Error: {e}")
    finally:
        conn.close()

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def save_strategy(user_id, strategy_json):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET strategy_data = ? WHERE user_id = ?", (json.dumps(strategy_json), user_id))
    conn.commit()
    conn.close()

def get_all_users_with_strategy():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE strategy_data IS NOT NULL")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def check_promocode(code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT value, activations_left FROM promocodes WHERE code = ?", (code,))
    res = c.fetchone()
    conn.close()
    if res and res[1] > 0:
        return res[0]
    return 0

def use_promocode(code):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE promocodes SET activations_left = activations_left - 1 WHERE code = ?", (code,))
    conn.commit()
    conn.close()

def create_promocode(code, value, activations):
    conn = sqlite3.connect(DB_NAME)
    try:
        c = conn.cursor()
        c.execute("INSERT INTO promocodes (code, value, activations_left) VALUES (?, ?, ?)", (code, value, activations))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
