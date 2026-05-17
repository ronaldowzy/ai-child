# Backend

FastAPI backend skeleton for the child AI growth agent.

## Setup

```bash
conda activate child-ai
cd backend
```

Install dependencies if the environment is not ready yet:

```bash
python -m pip install -e ".[dev]"
```

## Run

```bash
python -m uvicorn app.main:app --reload
```

## Test

```bash
python -m pytest
```

## Current Scope

- `GET /api/v1/health` returns `{"status":"ok"}`.
- `POST /api/v1/conversation/message` accepts a text message and returns a safe mock reply with `ui_actions` and `session_state`.
- No real model provider, database, OCR, account system, or long-term child data storage is connected in this milestone.
