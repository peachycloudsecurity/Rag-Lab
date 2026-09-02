.PHONY: start stop logs reset test help rebuild-web

# Default target
.DEFAULT_GOAL := help

start: ## 🚀 Start DevNotes (fully automated setup)
	@./start.sh

stop: ## 🛑 Stop all services
	@./stop.sh

logs: ## 📊 View all logs (Ctrl+C to exit)
	@./logs.sh

logs-web: ## 📊 View Flask app logs only
	@./logs.sh web

logs-ollama: ## 📊 View Ollama logs only
	@./logs.sh ollama

reset: ## 🗑️  Complete reset (removes all data)
	@./reset.sh

test: ## 🧪 Run test suite
	@echo "🧪 Running test suite..."
	@python test_complete.py

build: ## 🔨 Rebuild containers
	@echo "🔨 Rebuilding containers..."
	@docker compose build --no-cache

rebuild-web: ## 🔁 Rebuild and restart web only (avoids Ollama host port 11434 bind)
	@echo "🔁 Rebuilding web (--no-deps)..."
	@docker compose up -d --build --no-deps web

status: ## 📊 Show service status
	@echo "📊 Service Status:"
	@echo ""
	@docker compose ps

shell: ## 💻 Open shell in Flask container
	@docker compose exec web /bin/bash

shell-ollama: ## 💻 Open shell in Ollama container
	@docker compose exec ollama /bin/sh

pull-model: ## 📥 Manually pull qwen:1.8b (same as compose AI default)
	@echo "📥 Pulling qwen:1.8b..."
	@docker compose exec ollama ollama pull qwen:1.8b

pull-embed: ## 📥 Manually pull nomic-embed-text (used by the RAG poisoning lab)
	@echo "📥 Pulling nomic-embed-text..."
	@docker compose exec ollama ollama pull nomic-embed-text

list-models: ## 📋 List available Ollama models
	@docker compose exec ollama ollama list

rag-clear: ## 🧽 Clear the assistant knowledge base (Chroma volume), keep everything else
	@echo "🧽 Removing Chroma volume devnotes-chroma..."
	@docker compose stop chromadb >/dev/null 2>&1 || true
	@docker compose rm -f chromadb >/dev/null 2>&1 || true
	@docker volume rm vulnerable-flask-app_devnotes-chroma >/dev/null 2>&1 || true
	@docker compose up -d chromadb >/dev/null
	@echo "✅ Knowledge base cleared. Open Admin → 'Update chatbot with internal data' to re-seed."

help: ## 📖 Show this help message
	@echo "╔═══════════════════════════════════════════════════════════════╗"
	@echo "║                                                               ║"
	@echo "║   🔓 DevNotes - OWASP Top 10:2025 Training Platform           ║"
	@echo "║   Built by Peachycloud Security (The Shukla Duo)              ║"
	@echo "║                                                               ║"
	@echo "╚═══════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make start         # Start everything (automated)"
	@echo "  2. make rebuild-web   # After editing templates/app.py only (no Ollama restart)"
	@echo "  3. Open: http://localhost:5000"
	@echo "  4. Login: admin / admin123"
	@echo ""
	@echo "📚 Documentation: README.md, AI_PROMPT_INJECTION.md"
	@echo ""
