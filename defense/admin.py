"""
Admin dashboard. Relies on is_admin flag; access control can be broken (A01) if
admin check is missing or bypassed elsewhere.
"""
import db
import auth
import re


def get_all_users():
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, username, is_admin FROM users")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "username": r[1], "is_admin": bool(r[2])} for r in rows]


def get_all_notes():
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT n.id, n.user_id, u.username, n.title, n.created_at FROM notes n JOIN users u ON n.user_id = u.id ORDER BY n.created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "user_id": r[1], "username": r[2], "title": r[3], "created_at": r[4]} for r in rows]


def validate_email(email):
    """
    Weak email validation for training purposes.
    A02: Security Misconfiguration - overly permissive regex
    """
    # Intentionally weak regex - can be bypassed
    # Allows: test@, @domain.com, test@@domain, etc.
    pattern = r'^.+@.+\..+'
    return re.match(pattern, email) is not None


def create_user(username, password, email, is_admin=False):
    """
    Create a new user.
    A09: No logging of user creation
    A05: Potential for SQL injection if username not sanitized
    """
    # A09: No logging
    # A02: Weak email validation
    if not validate_email(email):
        return False, "Invalid email format"

    conn = db.get_conn()
    cur = conn.cursor()

    try:
        # Check if username exists
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            conn.close()
            return False, "Username already exists"

        # Check if email exists
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return False, "Email already exists"

        # Hash password and create user
        password_hash = auth.hash_password(password)
        cur.execute(
            "INSERT INTO users (username, password_hash, email, is_admin) VALUES (?, ?, ?, ?)",
            (username, password_hash, email, int(is_admin))
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return True, f"User {username} created successfully"

    except Exception as e:
        conn.close()
        return False, f"Error creating user: {str(e)}"


def delete_user(user_id):
    """
    Delete a user and all their data.
    A09: No logging of user deletion
    A01: No check if deleting admin user
    """
    # A09: No logging
    # A01: Can delete admin users (dangerous!)

    conn = db.get_conn()
    cur = conn.cursor()

    try:
        # Check if user exists
        cur.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False, "User not found"

        username = row[0]

        # Delete user's notes (cascade)
        cur.execute("DELETE FROM notes WHERE user_id = ?", (user_id,))

        # Delete user's attachments
        cur.execute("DELETE FROM attachments WHERE note_id IN (SELECT id FROM notes WHERE user_id = ?)", (user_id,))

        # Delete user's API keys
        cur.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))

        # Delete user
        cur.execute("DELETE FROM users WHERE id = ?", (user_id,))

        conn.commit()
        conn.close()
        return True, f"User {username} and all associated data deleted"

    except Exception as e:
        conn.close()
        return False, f"Error deleting user: {str(e)}"


def bulk_create_users(emails_text, default_password):
    """
    Bulk create users from list of emails.
    A05: Injection - uses string concatenation for SQL
    A09: No logging
    A02: Weak validation
    """
    # Parse emails (one per line)
    emails = [e.strip() for e in emails_text.split('\n') if e.strip()]

    created = []
    errors = []

    conn = db.get_conn()
    cur = conn.cursor()

    for email in emails:
        # A02: Weak email validation
        if not validate_email(email):
            errors.append(f"{email}: Invalid email format")
            continue

        # Generate username from email
        username = email.split('@')[0]

        # Check if username exists
        cur.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cur.fetchone():
            errors.append(f"{email}: Username {username} already exists")
            continue

        # Check if email exists
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            errors.append(f"{email}: Email already exists")
            continue

        try:
            # Hash password
            password_hash = auth.hash_password(default_password)

            # A05: Intentional SQL injection vulnerability for demo
            # Using string concatenation instead of parameterized query
            query = f"INSERT INTO users (username, password_hash, email, is_admin) VALUES ('{username}', '{password_hash}', '{email}', 0)"
            cur.execute(query)
            conn.commit()

            created.append(email)

        except Exception as e:
            errors.append(f"{email}: {str(e)}")

    conn.close()

    return created, errors


def bulk_delete_users(emails_text):
    """
    Bulk delete users by email.
    A05: SQL Injection vulnerability
    A09: No logging
    A01: No confirmation, can delete admin users
    """
    # Parse emails
    emails = [e.strip() for e in emails_text.split('\n') if e.strip()]

    deleted = []
    errors = []

    conn = db.get_conn()
    cur = conn.cursor()

    for email in emails:
        try:
            # A05: SQL injection via string concatenation
            query = f"SELECT id, username FROM users WHERE email = '{email}'"
            cur.execute(query)
            row = cur.fetchone()

            if not row:
                errors.append(f"{email}: User not found")
                continue

            user_id, username = row

            # Delete user's data
            cur.execute("DELETE FROM notes WHERE user_id = ?", (user_id,))
            cur.execute("DELETE FROM api_keys WHERE user_id = ?", (user_id,))
            cur.execute(f"DELETE FROM users WHERE email = '{email}'")  # A05: Injection here too
            conn.commit()

            deleted.append(f"{email} ({username})")

        except Exception as e:
            errors.append(f"{email}: {str(e)}")

    conn.close()

    return deleted, errors


def cleanup_database():
    """
    Admin-only: Clean up all non-admin users and their data.
    Useful for resetting workshop/training environment.
    """
    import os

    conn = db.get_conn()
    cur = conn.cursor()

    # Get admin username from env or default
    admin_username = os.environ.get("ADMIN_USERNAME", "admin")

    # Count before cleanup
    cur.execute("SELECT COUNT(*) FROM users WHERE is_admin = 0")
    user_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM notes")
    note_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM api_keys")
    key_count = cur.fetchone()[0]

    # Delete all non-admin data
    cur.execute("DELETE FROM notes WHERE user_id IN (SELECT id FROM users WHERE is_admin = 0)")
    cur.execute("DELETE FROM api_keys WHERE user_id IN (SELECT id FROM users WHERE is_admin = 0)")
    cur.execute("DELETE FROM attachments")
    cur.execute("DELETE FROM users WHERE is_admin = 0")

    conn.commit()
    conn.close()

    return {
        "users_deleted": user_count,
        "notes_deleted": note_count,
        "api_keys_deleted": key_count
    }


def restore_defaults():
    """
    Admin-only: Complete database reset and restore to fresh state.
    WARNING: This deletes EVERYTHING including admin!
    """
    import os

    conn = db.get_conn()
    cur = conn.cursor()

    # Drop all tables
    cur.execute("DROP TABLE IF EXISTS users")
    cur.execute("DROP TABLE IF EXISTS notes")
    cur.execute("DROP TABLE IF EXISTS api_keys")
    cur.execute("DROP TABLE IF EXISTS attachments")

    conn.commit()
    conn.close()

    # Reinitialize database
    db.init_db()

    # Recreate admin user
    import auth as auth_mod
    auth_mod.ensure_admin_user()

    return True
