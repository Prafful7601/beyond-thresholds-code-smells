# CodeSniff website: one-command local run.
#   make install   # Python venv for the backend + npm packages for the frontend
#   make dev       # backend on :8000 and frontend on :5173 (Ctrl+C stops both)
#   make test      # backend pytest + frontend Vitest
#   make e2e       # Playwright end-to-end test (mocked backend)
VENV ?= .venv
PY := $(VENV)/bin/python
API_PORT ?= 8000
WEB_PORT ?= 5173

.PHONY: install dev backend frontend test e2e coverage

install:
	python3 -m venv $(VENV)
	$(PY) -m pip install -q --upgrade pip
	$(PY) -m pip install -q -r backend/requirements-dev.txt
	cd frontend && npm ci

backend:
	$(PY) -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port $(API_PORT)

frontend:
	cd frontend && VITE_API_URL=http://localhost:$(API_PORT) npx vite --port $(WEB_PORT)

dev:
	@echo "API  http://localhost:$(API_PORT)/docs    site  http://localhost:$(WEB_PORT)"
	@trap 'kill 0' INT TERM EXIT; $(MAKE) --no-print-directory backend & $(MAKE) --no-print-directory frontend & wait

test:
	cd backend && ../$(PY) -m pytest tests -q --cov --cov-config=.coveragerc --cov-report=term
	cd frontend && npx vitest run --coverage

e2e:
	cd frontend && npx playwright test
