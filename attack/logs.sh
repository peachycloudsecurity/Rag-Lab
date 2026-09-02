#!/bin/bash

# DevNotes Logs Viewer

echo "📊 DevNotes Logs"
echo ""
echo "💡 Press Ctrl+C to exit"
echo ""

if [ "$1" = "web" ]; then
    docker compose logs -f web
elif [ "$1" = "ollama" ]; then
    docker compose logs -f ollama
else
    docker compose logs -f
fi
