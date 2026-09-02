"""
Database layer for DevNotes. SQLite with intentional injection surface for demos.
"""
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
    cur.execute(
        "CREATE TABLE IF NOT EXISTS notes ("
        "id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, body TEXT, share_token TEXT, created_at TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS attachments ("
        "id INTEGER PRIMARY KEY, note_id INTEGER, filename TEXT, path TEXT)"
    )
    cur.execute(
        "CREATE TABLE IF NOT EXISTS api_keys ("
        "id INTEGER PRIMARY KEY, user_id INTEGER, api_key TEXT UNIQUE, "
        "is_used INTEGER DEFAULT 0, created_at TEXT, used_at TEXT)"
    )
    conn.commit()
    conn.close()
