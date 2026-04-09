COMPOSE ?= docker compose
ENV_FILE ?= .env
SERVICE ?= api

.PHONY: compose-config up down logs ps health ui-health test regression benchmark

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

ui-health:
	curl -fsS http://127.0.0.1:$${ID_DOC_OCR_UI_PORT:-8080}/ >/dev/null

test:
	pytest -q

regression:
	PYTHONPATH=src ./.venv/bin/python examples/run_asset_smoke_regression.py
	PYTHONPATH=src ./.venv/bin/python examples/run_parser_regression.py

benchmark:
	PYTHONPATH=src ./.venv/bin/python examples/run_backbone_benchmark.py
