# Admin Management Guide

## Admin Credentials

### Default Credentials
- **Username:** `admin`
- **Password:** `admin123`
- **Email:** `admin@devnotes.local`

### Customizing Admin Credentials

**Option 1: Environment Variables (Recommended)**

```bash
export ADMIN_USERNAME=myadmin
export ADMIN_PASSWORD=SecurePassword123!
export ADMIN_EMAIL=admin@yourcompany.com

docker compose up --build -d
```

**Option 2: Docker Compose**

Edit `docker-compose.yml`:
```yaml
environment:
  - ADMIN_USERNAME=myadmin
  - ADMIN_PASSWORD=SecurePassword123!
  - ADMIN_EMAIL=admin@yourcompany.com
```

**Option 3: .env File**

Create `.env` file:
```
ADMIN_USERNAME=myadmin
ADMIN_PASSWORD=SecurePassword123!
ADMIN_EMAIL=admin@yourcompany.com
```

---

## Admin-Only Features

### 1. Cleanup Database 🧹

**Purpose:** Remove all non-admin users and their data while preserving admin accounts.

**Use case:** Reset workshop environment between sessions.

**Access:** http://localhost:5000/admin/cleanup

**What gets deleted:**
- All non-admin users
- All notes
- All API keys
- All attachments

**What is preserved:**
- Admin users
- Database structure (tables)

**How to use:**
1. Login as admin
2. Go to Admin Dashboard
3. Click "Cleanup Database"
4. Check the confirmation box
5. Click "Cleanup Database" button

---

### 2. Restore to Defaults 🔄

**Purpose:** Complete database reset to factory defaults.

**Use case:** Start completely fresh - total reset.

**Access:** http://localhost:5000/admin/restore

**What gets deleted:**
- **EVERYTHING** - all users (including current admin)
- All notes, API keys, attachments
- All tables (will be recreated)

**What gets created:**
- Fresh database structure
- New admin user with configured credentials

**How to use:**
1. Login as admin
2. Go to Admin Dashboard
3. Click "Restore Defaults"
4. Type `RESTORE` (in capitals) in the confirmation box
5. Click "Restore to Defaults" button
6. **You will be logged out** - login again with admin credentials

---

## User Management

### Creating Users

**Regular Users:**
- Via Admin UI: `/admin/users`
- Bulk create from email list
- Single user creation

**Admin Users:**
- **Cannot be created via UI** (security measure)
- Only via environment variables
- Set before starting the app

**Why?**
- Prevents accidental admin creation
- Prevents privilege escalation attacks
- Admin credentials controlled via config, not UI

---

## Workflow Examples

### Workshop Setup

**Before workshop:**
```bash
# 1. Set custom admin password
export ADMIN_PASSWORD=WorkshopAdmin2025!

# 2. Start app
docker compose up --build

# 3. Login as admin
# 4. Bulk create student accounts
# Go to /admin/users
# Paste student emails
# Set default password
```

**Between sessions:**
```bash
# Clean up without restarting
# 1. Login as admin
# 2. Go to /admin/cleanup
# 3. Confirm cleanup
# 4. Recreate student accounts (or reuse bulk list)
```

**Complete reset:**
```bash
# If something goes wrong
# 1. Login as admin
# 2. Go to /admin/restore
# 3. Type RESTORE
# 4. Confirm
# 5. Login again with admin credentials
# 6. Setup from scratch
```

---

## Security Notes

### Admin Privileges

Admins can:
- ✅ Create/delete regular users
- ✅ View all notes
- ✅ View all API keys and logs
- ✅ Cleanup database
- ✅ Restore to defaults
- ❌ Create admin users via UI (env only)

### Protection Mechanisms

1. **Admin-only routes** - Check `is_admin` flag
2. **No UI admin creation** - Prevents privilege escalation
3. **Confirmation required** - Both cleanup and restore require explicit confirmation
4. **Environment-based admin** - Admin credentials set via config, not database

---

## Quick Reference

| Action | Route | Access | Danger Level |
|--------|-------|--------|--------------|
| User Management | `/admin/users` | Admin | Low |
| API Key Dashboard | `/admin/api-keys` | Admin | Low |
| Cleanup Database | `/admin/cleanup` | Admin | **Medium** |
| Restore Defaults | `/admin/restore` | Admin | **HIGH** |

---

## Troubleshooting

### Forgot Admin Password?

**Option 1: Environment Variable**
```bash
export ADMIN_PASSWORD=NewPassword123!
docker compose down
docker compose up --build
```

**Option 2: Database Reset**
```bash
docker compose down -v  # Deletes database
docker compose up --build  # Creates fresh admin
```

**Option 3: Direct Database Edit**
```bash
# Stop app
docker compose down

# Delete database
rm devnotes.db

# Restart
docker compose up
```

### Cleanup Not Working?

- Ensure you're logged in as admin
- Check the confirmation checkbox
- Verify admin flag: check `/admin` access

### Restore Stuck?

- Type `RESTORE` exactly (all caps)
- Must be admin user
- Database must be accessible

---

## Best Practices

1. **Set strong admin password** via environment variables
2. **Document admin credentials** securely
3. **Use cleanup** between workshop sessions (faster)
4. **Use restore** only when needed (slower, complete reset)
5. **Backup before restore** if you want to preserve data
6. **Test in development** before using in production training

---

## Environment Variables Reference

```bash
# Admin Credentials
ADMIN_USERNAME=admin           # Default: admin
ADMIN_PASSWORD=admin123        # Default: admin123
ADMIN_EMAIL=admin@dev.local   # Default: admin@devnotes.local

# Database
DEVNOTES_DB=devnotes.db       # Default: devnotes.db

# App Config
DEBUG=True                     # Default: True
SECRET_KEY=random-key          # Default: dev-secret-change-in-prod
```

---

## Examples

### Production Workshop Setup

```bash
# .env file
ADMIN_USERNAME=workshop_admin
ADMIN_PASSWORD=SecureWorkshop2025!xY9
ADMIN_EMAIL=admin@workshop.company.com
DEBUG=False
SECRET_KEY=randomly-generated-64-char-key
```

```bash
docker compose up -d
```

### Quick Test Environment

```bash
# Use defaults
docker compose up

# Login: admin / admin123
```

### Clean Up After Workshop

```bash
# Option 1: Via UI (recommended)
# 1. Login as admin
# 2. /admin/cleanup
# 3. Confirm

# Option 2: Complete reset
# 1. /admin/restore
# 2. Type RESTORE
# 3. Confirm
```

---

**Remember:** This is an **intentionally vulnerable** application for training. Never use in production!
