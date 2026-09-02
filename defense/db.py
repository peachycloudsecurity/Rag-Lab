import sqlite3
import os

DB_PATH = os.environ.get("DEVNOTES_DB", "devnotes.db")


def get_conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS users ("
        "id INTEGER PRIMARY KEY, username TEXT UNIQUE, password_hash TEXT, "
        "email TEXT UNIQUE, is_admin INTEGER DEFAULT 0)"
    )
    conn.commit()
    conn.close()
