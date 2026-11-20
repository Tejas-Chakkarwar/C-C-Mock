PYTHON ?= .venv/bin/python

.PHONY: up down data load verify-env smoke-check test test-integration slice-check

up:
	@if [ ! -f .env ]; then cp .env.example .env && chmod 600 .env; fi
	docker compose up -d

down:
	docker compose down

data:
	$(PYTHON) scripts/download_dataset.py
	$(PYTHON) scripts/preprocess.py

load:
	$(PYTHON) scripts/load_data.py

verify-env:
	$(PYTHON) scripts/verify_env.py

smoke-check:
	$(PYTHON) scripts/smoke_check.py

test:
	$(PYTHON) -m pytest -m "not integration"

test-integration:
	$(PYTHON) -m pytest -m integration --run-integration

slice-check:
	$(PYTHON) scripts/slice_check.py

