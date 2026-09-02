#!/bin/bash

# DevNotes Stop Script

echo "🛑 Stopping DevNotes services..."
echo ""

docker compose down

# Named containers (if compose left orphans after a failed start)
docker rm -f devnotes-ollama devnotes-web devnotes-chromadb 2>/dev/null || true

echo ""
echo "✅ Services stopped successfully!"
echo ""
echo "💡 Tips:"
echo "   • To remove all data: docker compose down -v"
echo "   • To start again: ./start.sh"
echo ""
