# DevNotes Automated Setup Flow

## What Happens When You Run `make start`

```
┌─────────────────────────────────────────────────────────────┐
│  YOU: Type "make start"                                     │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: Pre-flight Checks                                  │
│  • Check if Docker is running                               │
│  • Clean up old containers (if any)                         │
│  • Detect if first-time setup                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 2: Build Docker Images                                │
│  • Build Flask app container (Python 3.9, Flask 2.0.1)      │
│  • Pull Ollama image from Docker Hub                        │
│  • Create named volumes (devnotes-data, ollama-data)        │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 3: Start Ollama Service (Container 1)                 │
│  • Start Ollama container                                   │
│  • Wait for service to be ready (5 seconds)                 │
│  • Check if tinyllama model exists                          │
│  • If not exists: Download model (~1.9GB, 5-7 minutes)      │
│  • If exists: Skip download (instant!)                      │
│  • Mark service as healthy                                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 4: Start Flask App (Container 2)                      │
│  • Wait for Ollama to be healthy (health check)             │
│  • Start Flask application                                  │
│  • Initialize SQLite database                               │
│  • Create admin user (from env vars)                        │
│  • Start listening on port 5000                             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  STEP 5: Health Checks & Verification                       │
│  • Verify Ollama responds to requests                       │
│  • Verify Flask app is accessible                           │
│  • Show success message with URLs                           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│  ✅ READY!                                                  │
│  • Application: http://localhost:5000                       │
│  • Admin login: admin / admin123                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Timeline Breakdown

### First-Time Setup (~10 minutes)

```
0:00 ┌──────────────────────────────────┐
     │ Pre-flight checks                │
0:10 ├──────────────────────────────────┤
     │ Building Flask container         │
2:00 ├──────────────────────────────────┤
     │ Pulling Ollama image             │
3:00 ├──────────────────────────────────┤
     │ Starting Ollama service          │
3:10 ├──────────────────────────────────┤
     │ Downloading TinyLlama model      │
     │ (~1.9GB - this is the long part) │
9:30 ├──────────────────────────────────┤
     │ Starting Flask app               │
9:45 ├──────────────────────────────────┤
     │ Health checks                    │
10:00└──────────────────────────────────┘
      ✅ READY!
```

### Subsequent Starts (~30 seconds)

```
0:00 ┌──────────────────────────────────┐
     │ Pre-flight checks                │
0:05 ├──────────────────────────────────┤
     │ Starting containers              │
0:15 ├──────────────────────────────────┤
     │ Ollama health check              │
     │ (model already exists - skip DL) │
0:25 ├──────────────────────────────────┤
     │ Flask app startup                │
0:30 └──────────────────────────────────┘
      ✅ READY!
```

---

## What Gets Downloaded (First Time Only)

| Component | Size | Time | Cached? |
|-----------|------|------|---------|
| Python base image | ~900MB | ~1-2 min | ✅ Yes |
| Ollama Docker image | ~700MB | ~1 min | ✅ Yes |
| TinyLlama model | ~1.9GB | ~5-7 min | ✅ Yes |
| Python packages | ~50MB | ~30 sec | ✅ Yes |
| **Total** | **~3.5GB** | **~10 min** | **✅ All cached!** |

---

## What Does NOT Get Downloaded

❌ Manual Ollama installation (0GB, 0 time)
❌ Python installation (0GB, 0 time)
❌ Manual model downloads (0GB, 0 time)
❌ Configuration files (0GB, 0 time)

**Everything is automated!**

---

## Container Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  HOST SYSTEM                                                 │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Docker Network: devnotes_default                      │ │
│  │                                                         │ │
│  │  ┌──────────────────────┐  ┌──────────────────────┐   │ │
│  │  │  Container: web      │  │  Container: ollama   │   │ │
│  │  │  ─────────────────── │  │  ──────────────────  │   │ │
│  │  │  Flask App           │  │  Ollama Service      │   │ │
│  │  │  Port: 5000          │◄─┤  Port: 11434         │   │ │
│  │  │  Python 3.9          │  │  TinyLlama Model     │   │ │
│  │  │  SQLite Database     │  │  Health Check: ON    │   │ │
│  │  │                      │  │                      │   │ │
│  │  │  Volumes:            │  │  Volumes:            │   │ │
│  │  │  • devnotes-data     │  │  • ollama-data       │   │ │
│  │  │  • ./uploads         │  │                      │   │ │
│  │  └──────────────────────┘  └──────────────────────┘   │ │
│  │                                                         │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  Access: http://localhost:5000 ──► Port 5000 (Flask)        │
│          http://localhost:11434 ──► Port 11434 (Ollama)     │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Persistence

### Volumes (Survive Container Restarts)

```
docker volume ls

DRIVER    VOLUME NAME
local     vulnerable-flask-app_devnotes-data    # SQLite database, notes
local     vulnerable-flask-app_ollama-data      # TinyLlama model cache
```

### Bind Mounts (Direct Host Mapping)

```
./uploads  ──► /app/uploads (in container)
```

**Result:** Your data persists even after `make stop`!

---

## Commands Reference

```bash
# Start (automated setup)
make start

# Check what's running
docker compose ps
docker ps

# View logs in real-time
make logs

# Stop (keeps data)
make stop

# Complete reset (deletes everything)
make reset

# Rebuild from scratch
make build
make start
```

---

## Behind the Scenes: Health Checks

**Ollama Health Check (every 5 seconds):**
```bash
# Docker runs this command inside container
ollama list

# If successful: Container marked as "healthy"
# Flask waits for this before starting
```

**Flask Dependency:**
```yaml
depends_on:
  ollama:
    condition: service_healthy
```

This ensures Flask **never starts before Ollama is ready**!

---

## Troubleshooting the Flow

### Problem: Stuck at "Downloading model"

**Diagnosis:**
```bash
make logs-ollama
# Look for download progress
```

**Solution:**
- Wait (5-7 minutes is normal for first time)
- Check internet connection
- If timeout: `make reset` then `make start`

### Problem: Flask won't start

**Diagnosis:**
```bash
make logs-web
# Look for Python errors
```

**Solution:**
```bash
make stop
make start
# Check if port 5000 is free
lsof -i :5000
```

### Problem: Services keep restarting

**Diagnosis:**
```bash
make status
# Look for "Restarting" status
```

**Solution:**
```bash
make logs  # See what's failing
make reset  # Nuclear option
```

---

## Why This Setup Rocks 🎸

✅ **Zero Configuration** - No manual installs
✅ **Idempotent** - Run multiple times safely
✅ **Cached** - Only downloads once
✅ **Health Checks** - Ensures everything is ready
✅ **Persistent Data** - Survives restarts
✅ **Isolated** - Runs in containers
✅ **Reproducible** - Same result every time
✅ **Fast Restarts** - 30 seconds after first time

---

**Built with automation in mind by [Peachycloud Security](https://peachycloudsecurity.com)**
