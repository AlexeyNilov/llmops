ifeq ($(OS),Windows_NT)
VENV_BIN = .venv/Scripts
EXE = .exe
else
VENV_BIN = .venv/bin
EXE =
endif

PYTHON = $(VENV_BIN)/python$(EXE)
PIP = $(VENV_BIN)/pip$(EXE)
PYTEST = $(VENV_BIN)/pytest$(EXE)
RUFF = $(VENV_BIN)/ruff$(EXE)
MYPY = $(VENV_BIN)/mypy$(EXE)
UVICORN = $(VENV_BIN)/uvicorn$(EXE)
STREAMLIT = $(VENV_BIN)/streamlit$(EXE)

APP_RUN_DIR = .run
FASTAPI_HOST ?= 127.0.0.1
FASTAPI_PORT ?= 8000
STREAMLIT_HOST ?= 127.0.0.1
STREAMLIT_PORT ?= 8501

.PHONY: install test test-integration lint mypy format start-fastapi stop-fastapi restart-fastapi start-streamlit stop-streamlit restart-streamlit start-app stop-app restart-app

install:
	$(PIP) install -e .[dev]

test:
	$(PYTEST)

test-integration:
	LLMOPS_RUN_INTEGRATION=1 $(PYTEST) -m integration

lint:
	$(RUFF) check .

mypy:
	$(MYPY) src

format:
	$(RUFF) check --fix .
	$(RUFF) format .

start-fastapi:
	@mkdir -p $(APP_RUN_DIR)
	@if [ -f $(APP_RUN_DIR)/fastapi.pid ] && kill -0 $$(cat $(APP_RUN_DIR)/fastapi.pid) 2>/dev/null; then \
		echo "FastAPI is already running on http://$(FASTAPI_HOST):$(FASTAPI_PORT)"; \
	else \
		PYTHONPATH=src nohup $(UVICORN) llmops.api.main:app --reload --host $(FASTAPI_HOST) --port $(FASTAPI_PORT) > $(APP_RUN_DIR)/fastapi.log 2>&1 & \
		echo $$! > $(APP_RUN_DIR)/fastapi.pid; \
		echo "FastAPI started on http://$(FASTAPI_HOST):$(FASTAPI_PORT)"; \
	fi

stop-fastapi:
	@if [ -f $(APP_RUN_DIR)/fastapi.pid ]; then \
		kill $$(cat $(APP_RUN_DIR)/fastapi.pid) 2>/dev/null || true; \
		rm -f $(APP_RUN_DIR)/fastapi.pid; \
		echo "FastAPI stopped"; \
	else \
		echo "FastAPI is not running"; \
	fi

restart-fastapi: stop-fastapi start-fastapi

start-streamlit:
	@mkdir -p $(APP_RUN_DIR)
	@if [ -f $(APP_RUN_DIR)/streamlit.pid ] && kill -0 $$(cat $(APP_RUN_DIR)/streamlit.pid) 2>/dev/null; then \
		echo "Streamlit is already running on http://$(STREAMLIT_HOST):$(STREAMLIT_PORT)"; \
	else \
		nohup $(STREAMLIT) run src/llmops/ui/streamlit_chat.py --server.address $(STREAMLIT_HOST) --server.port $(STREAMLIT_PORT) > $(APP_RUN_DIR)/streamlit.log 2>&1 & \
		echo $$! > $(APP_RUN_DIR)/streamlit.pid; \
		echo "Streamlit started on http://$(STREAMLIT_HOST):$(STREAMLIT_PORT)"; \
	fi

stop-streamlit:
	@if [ -f $(APP_RUN_DIR)/streamlit.pid ]; then \
		kill $$(cat $(APP_RUN_DIR)/streamlit.pid) 2>/dev/null || true; \
		rm -f $(APP_RUN_DIR)/streamlit.pid; \
		echo "Streamlit stopped"; \
	else \
		echo "Streamlit is not running"; \
	fi

restart-streamlit: stop-streamlit start-streamlit

start-app: start-fastapi start-streamlit

stop-app: stop-streamlit stop-fastapi

restart-app: stop-app start-app
