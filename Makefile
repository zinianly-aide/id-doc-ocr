COMPOSE ?= docker compose
ENV_FILE ?= .env
SERVICE ?= id-doc-ocr

.PHONY: compose-config up down logs ps health test

compose-config:
	$(COMPOSE) --env-file $(ENV_FILE) config

up:
	mkdir -p data/failures
	$(COMPOSE) --env-file $(ENV_FILE) up --build -d

down:
	$(COMPOSE) --env-file $(ENV_FILE) down

logs:
	$(COMPOSE) --env-file $(ENV_FILE) logs -f $(SERVICE)

ps:
	$(COMPOSE) --env-file $(ENV_FILE) ps

health:
	curl -fsS http://127.0.0.1:$${ID_DOC_OCR_PORT:-8000}/health

test:
	pytest -q
