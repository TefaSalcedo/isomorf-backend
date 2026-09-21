# ISOMORF API

FastAPI backend for the ISOMORF structural workspace.

## Requirements

- Python 3.12 or newer (the code uses `enum.StrEnum`, added in 3.11)
- PostgreSQL 14 or newer

## Local setup

```bash
docker run -d --name isomorf-pg -p 5432:5432 \
  -e POSTGRES_USER=isomorf -e POSTGRES_PASSWORD=isomorf -e POSTGRES_DB=isomorf postgres:16

python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env

.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload --port 8000
```

`GET http://localhost:8000/health` returns `{"status": "ok"}` and the interactive
documentation is served at `http://localhost:8000/docs`.

## Configuration

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | – | SQLAlchemy URL, for example `postgresql+psycopg://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | – | Secret used to sign access and refresh tokens |
| `FRONTEND_URL` | `http://localhost:3000` | Origin allowed by CORS |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |
| `COOKIE_SECURE` | `false` | Set to `true` behind HTTPS |
| `AUTH_HINT_COOKIE_NAME` | `isomorf_auth_hint` | Non-HttpOnly marker cookie the frontend reads before calling `/api/auth/me` |

## Testing

Tests run against a dedicated PostgreSQL database (`isomorf_test` by default,
created and migrated automatically). Override the location with
`TEST_DATABASE_URL`.

```bash
docker run -d --name isomorf-pg -p 5432:5432 \
  -e POSTGRES_USER=isomorf -e POSTGRES_PASSWORD=isomorf -e POSTGRES_DB=isomorf postgres:16

.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest --cov=app/services --cov-report=term-missing
```

Lint and typecheck:

```bash
.venv/bin/ruff check .
.venv/bin/mypy app
```

## Docker

```bash
docker build -t isomorf-api .
docker run --env-file .env -p 8000:8000 isomorf-api
```

The image entrypoint runs `alembic upgrade head` before starting uvicorn.
