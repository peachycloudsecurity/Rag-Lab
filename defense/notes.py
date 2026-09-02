"""
Notes CRUD. Intentional vulnerabilities:
- A01: Broken Access Control (no user_id check on fetch)
- A03: Injection (search built from user input)
- A04: Insecure Design (predictable share token = note id)
"""
import db


def get_note_by_id(note_id):
    # A01 Broken Access Control: no ownership check
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "user_id": row[1], "title": row[2], "body": row[3], "share_token": row[4], "created_at": row[5]}


def get_notes_for_user(user_id):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "user_id": r[1], "title": r[2], "body": r[3], "share_token": r[4], "created_at": r[5]}
        for r in rows
    ]


def search_notes(q):
    # A03 Injection: concatenating user input into SQL
    conn = db.get_conn()
    cur = conn.cursor()
    query = f"SELECT * FROM notes WHERE title LIKE '%{q}%' OR body LIKE '%{q}%'"
    cur.execute(query)
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "user_id": r[1], "title": r[2], "body": r[3], "share_token": r[4], "created_at": r[5]}
        for r in rows
    ]


def create_note(user_id, title, body):
    conn = db.get_conn()
    cur = conn.cursor()
    # A04 Insecure Design: share_token = str(note_id), predictable
    cur.execute(
        "INSERT INTO notes (user_id, title, body, share_token, created_at) VALUES (?, ?, ?, '', datetime('now'))",
        (user_id, title, body),
    )
    note_id = cur.lastrowid
    cur.execute("UPDATE notes SET share_token = ? WHERE id = ?", (str(note_id), note_id))
    conn.commit()
    conn.close()
    return note_id


def get_note_by_share_token(token):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE share_token = ?", (token,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {"id": row[0], "user_id": row[1], "title": row[2], "body": row[3], "share_token": row[4], "created_at": row[5]}
