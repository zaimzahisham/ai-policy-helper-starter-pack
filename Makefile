.PHONY: dev test fmt
dev:
	docker compose up --build

dev-hot:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

test:
	docker compose run --rm backend pytest -q

test-hot:
	docker compose -f docker-compose.yml -f docker-compose.test.yml run --rm backend pytest -q

fmt:
	docker compose run --rm backend black app
