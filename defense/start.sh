#!/bin/bash

# DevNotes Automated Setup Script
# This script handles the complete setup with progress indication

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🔓 DevNotes - OWASP Top 10:2025 Training Platform           ║"
echo "║   Built by Peachycloud Security (The Shukla Duo)              ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running!"
    echo "Please start Docker Desktop and try again."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# --- Host port for Ollama publish (11434 often conflicts with host Ollama / other stacks) ---
# Web container talks to ollama:11434 on the Docker network; this only affects localhost:N on the host.
port_is_free() {
    local p="$1"
    if command -v python3 >/dev/null 2>&1; then
        python3 -c "import socket; s=socket.socket(); s.bind(('127.0.0.1', int('$p'))); s.close()" 2>/dev/null
        return $?
    fi
    if command -v lsof >/dev/null 2>&1; then
        ! lsof -nP -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1
        return $?
    fi
    return 0
}

pick_ollama_host_port() {
    local p=11434
    local end=11600
    while [ "$p" -le "$end" ]; do
        if port_is_free "$p"; then
            echo "$p"
            return 0
        fi
        p=$((p + 1))
    done
    return 1
}

OLLAMA_PORT_AUTO_PICK=false
if [ -n "${OLLAMA_HOST_PORT:-}" ]; then
    if ! port_is_free "$OLLAMA_HOST_PORT"; then
        echo "❌ OLLAMA_HOST_PORT=$OLLAMA_HOST_PORT is already in use on this machine."
        echo "   Unset OLLAMA_HOST_PORT to auto-pick a free port, or free the port and retry."
        exit 1
    fi
    export OLLAMA_HOST_PORT
else
    OLLAMA_PORT_AUTO_PICK=true
    if ! picked=$(pick_ollama_host_port); then
        echo "❌ Could not find a free TCP port between 11434 and 11600 for Ollama."
        exit 1
    fi
    export OLLAMA_HOST_PORT="$picked"
fi

# Only when we auto-picked: explain why a non-default host port is used
if [ "$OLLAMA_PORT_AUTO_PICK" = true ] && [ "$OLLAMA_HOST_PORT" != "11434" ]; then
    echo "⚠️  Port 11434 is already in use on the host."
    echo "   Publishing Ollama on host port ${OLLAMA_HOST_PORT} instead (inside Docker it stays ollama:11434)."
    echo ""
fi

# Remove stale containers from a failed partial start (e.g. previous bind error)
docker rm -f devnotes-ollama devnotes-web devnotes-chromadb 2>/dev/null || true

# Clean up any existing containers
echo "🧹 Cleaning up old containers (if any)..."
docker compose down -v 2>/dev/null || true
echo ""

# Check if this is first time setup
FIRST_TIME=false
if ! docker volume ls | grep -q "ollama-data"; then
    FIRST_TIME=true
fi

if [ "$FIRST_TIME" = true ]; then
    echo "📦 First-time setup detected!"
    echo ""
    echo "⏱️  This will take approximately 5-10 minutes:"
    echo "   • Building Flask application container (~2 min)"
    echo "   • Starting Ollama service (~1 min)"
    echo "   • Downloading qwen:1.8b chat model (~1.1GB) and nomic-embed-text (~270MB)"
    echo "   • Starting Chroma vector store for the RAG poisoning lab"
    echo ""
    echo "☕ Grab some coffee! Subsequent starts will be much faster."
    echo ""
else
    echo "🚀 Quick start (containers and model already exist)"
    echo ""
    echo "⏱️  This will take approximately 30 seconds"
    echo ""
fi

# Start services
echo "🔧 Starting services..."
echo ""

docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."
echo ""

# Wait for Ollama healthcheck
echo "📡 Checking Ollama service..."
COUNTER=0
MAX_ATTEMPTS=60

while [ $COUNTER -lt $MAX_ATTEMPTS ]; do
    if docker compose ps | grep -q "healthy"; then
        echo "✅ Ollama is healthy!"
        break
    fi

    if [ $COUNTER -eq 0 ]; then
        echo -n "   Waiting"
    else
        echo -n "."
    fi

    sleep 2
    COUNTER=$((COUNTER + 1))
done

echo ""

if [ $COUNTER -eq $MAX_ATTEMPTS ]; then
    echo "⚠️  Warning: Ollama health check timeout"
    echo "Services may still be starting. Check logs with: docker compose logs -f"
else
    # Wait for Flask app
    echo "🌐 Checking Flask application..."
    sleep 3

    if curl -s http://localhost:5000 > /dev/null 2>&1; then
        echo "✅ Flask application is ready!"
    else
        echo "⏳ Flask is starting..."
        sleep 5
    fi
fi

echo ""
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🎉 DevNotes is ready!                                       ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""
echo "🌐 Access the application:"
echo "   URL: http://localhost:5000"
echo ""
echo "🔑 Default admin credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🤖 AI Assistant (Prompt Injection + RAG poisoning demos):"
echo "   Login → AI Assistant menu"
echo "   Admin → 'Update chatbot with internal data' for the RAG poisoning lab"
echo ""
echo "🔌 Ollama on this machine (host): http://localhost:${OLLAMA_HOST_PORT}"
echo "   (Flask uses http://ollama:11434 inside Docker; only this laptop port may differ.)"
echo ""
echo "📊 View logs:"
echo "   docker compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker compose down"
echo ""
echo "📚 Documentation:"
echo "   • README.md - Overview and quick start"
echo "   • AI_PROMPT_INJECTION.md - LLM security guide"
echo "   • ADMIN_MANAGEMENT.md - Admin features"
echo ""
echo "⚠️  Remember: This is intentionally vulnerable for training!"
echo "   DO NOT use in production or expose to the internet."
echo ""
