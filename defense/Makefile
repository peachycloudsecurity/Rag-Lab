.PHONY: start stop logs logs-web rebuild-web pull-model shell help

.DEFAULT_GOAL := help

start: ## Start the defense lab (vulnerable version)
	@docker compose up -d --build
	@echo ""
	@echo "  App:   http://localhost:5000"
	@echo "  Login: admin / admin123"
	@echo ""

stop: ## Stop all services
	@docker compose down

logs: ## View all logs (Ctrl+C to exit)
	@docker compose logs -f

logs-web: ## View Flask app logs only
	@docker compose logs -f web

rebuild-web: ## Rebuild and restart web container only
	@echo "Rebuilding web container..."
	@docker compose up -d --build --no-deps web

pull-model: ## Manually pull qwen:1.8b inside running Ollama container
	@docker compose exec ollama ollama pull qwen:1.8b

shell: ## Open shell in the web container
	@docker compose exec web /bin/bash

help:
	@echo ""
	@echo "  LLM Guard Defense Lab"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "  Apply LLM Guard fix:"
	@echo "    cp app_fix.py app.py"
	@echo "    echo 'llm-guard' >> requirements.txt"
	@echo "    make rebuild-web"
	@echo ""
	@echo "  See defense.md for full steps."
	@echo ""
