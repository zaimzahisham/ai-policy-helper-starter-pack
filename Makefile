.PHONY: dev test fmt ollama-pull ollama-list
dev:
	docker compose up --build

dev-hot:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

test:
	docker compose run --rm backend pytest -q

test-hot:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest -q

fmt:
	docker compose run --rm backend python -m black app

dev-ollama:
	docker compose --profile docker-ollama up --build

ollama-pull:
	@if [ -z "$(MODEL)" ]; then \
		echo "Error: MODEL is required. Usage: make ollama-pull MODEL=<model_name>"; \
		echo "Example: make ollama-pull MODEL=qwen2.5:0.5b"; \
		echo "Note: Requires Docker Ollama to be running (use 'make dev-ollama' or 'docker compose --profile docker-ollama up')"; \
		exit 1; \
	fi
	docker compose --profile docker-ollama exec ollama ollama pull $(MODEL)

ollama-list:
	docker compose --profile docker-ollama exec ollama ollama list
