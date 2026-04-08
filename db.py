import sqlite3
import json
from datetime import datetime

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            user_id     INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            subscribed_at TEXT,
            preferences TEXT DEFAULT '{}'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sent_jobs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER,
            job_id      TEXT,
            sent_at     TEXT
        )
    """)
    conn.commit()
    conn.close()
    print("[DB] Initialized database.")


def save_subscriber(user_id, username=None, first_name=None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT OR IGNORE INTO subscribers
           (user_id, username, first_name, subscribed_at, preferences)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, username, first_name, datetime.utcnow().isoformat(), '{}')
    )
    conn.commit()
    conn.close()


def remove_subscriber(user_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM subscribers WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_all_subscribers():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT user_id FROM subscribers").fetchall()
    conn.close()
    return [r[0] for r in rows]


def is_subscribed(user_id):
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT 1 FROM subscribers WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return row is not None


def save_preferences(user_id, prefs: dict):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE subscribers SET preferences = ? WHERE user_id = ?",
        (json.dumps(prefs), user_id)
    )
    conn.commit()
    conn.close()


def get_preferences(user_id) -> dict:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT preferences FROM subscribers WHERE user_id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return json.loads(row[0]) if row else {}


def subscriber_count():
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM subscribers").fetchone()[0]
    conn.close()
    return count
