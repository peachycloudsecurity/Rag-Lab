#!/bin/bash

# DevNotes Complete Reset Script
# Use this to completely reset the environment (removes all data)

echo "⚠️  WARNING: Complete Reset"
echo ""
echo "This will:"
echo "  • Stop all services"
echo "  • Delete all data (notes, users, uploads)"
echo "  • Delete Ollama models (qwen:1.8b, nomic-embed-text — will be re-pulled on next start)"
echo "  • Delete the assistant knowledge base (Chroma volume)"
echo ""
read -p "Are you sure? Type 'yes' to confirm: " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "❌ Reset cancelled"
    exit 0
fi

echo ""
echo "🗑️  Removing all containers and volumes..."
docker compose down -v

docker rm -f devnotes-ollama devnotes-web devnotes-chromadb 2>/dev/null || true

echo ""
echo "🧹 Cleaning up uploads directory..."
rm -rf uploads/*

echo ""
echo "✅ Reset complete!"
echo ""
echo "To start fresh, run: ./start.sh"
echo ""
