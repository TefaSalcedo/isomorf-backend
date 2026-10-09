# ISOMORF API

**FastAPI + PostgreSQL backend for ISOMORF — a structural design workspace for the web.**

[![CI](https://github.com/TefaSalcedo/isomorf-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/TefaSalcedo/isomorf-backend/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.1+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

REST API that serves the [isomorf-frontend](https://github.com/TefaSalcedo/isomorf-frontend) Next.js app.

## Features

- **Auth & sessions** — register/login, JWT access + refresh tokens in HttpOnly cookies, and **device-bound sessions**: requests are signed with a per-device WebCrypto key pair, so a stolen cookie alone is useless
- **Versioned documents** — atomic document saves (`PUT /document`), `project_documents` snapshots + `element_revisions` diffs, server-side `undo` / `redo` / `restore` and a full revision history endpoint
- **Elements** — 21 types: structural members (walls, columns, beams, slabs, footings, stairs…) plus 7 CAD annotation primitives (`line`, `polyline`, `arc`, `circle`, `ellipse`, `rectangle`, `hatch`), with geometry validation per type
- **Teams & roles** — teams, members, project shares and token invites; effective `access_role` (owner / editor / viewer) enforced in every service
- **Structural loads** — load cases and per-element loads
- **Catalog** — per-project materials and sections backed by global presets
- **Folders & projects** — CRUD with public slugs + internal UUIDs

Interactive API documentation is served at **`/docs`** (Swagger UI) and **`/redoc`**.

![Swagger UI](docs/screenshots/swagger.png)

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
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `FRONTEND_URL` | `http://localhost:3000` | Origin allowed by CORS |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Refresh token lifetime |
| `COOKIE_SECURE` | `false` | Set to `true` behind HTTPS |
| `COOKIE_SAMESITE` | `lax` | SameSite policy for session cookies |
| `COOKIE_NAME` | `isomorf_session` | Access-token cookie name |
| `REFRESH_COOKIE_NAME` | `isomorf_refresh` | Refresh-token cookie name |
| `AUTH_HINT_COOKIE_NAME` | `isomorf_auth_hint` | Non-HttpOnly marker cookie the frontend reads before calling `/api/auth/me` |
| `DEVICE_PROOF_MAX_AGE_SECONDS` | `90` | Freshness window for signed device-proof headers |

See [`.env.example`](.env.example) for a ready-to-copy template.

## Project layout

```
app/
  api/          FastAPI routers (auth, projects, elements, documents, loads, teams, catalog, folders)
  services/     Business logic — access control, document versioning, elements, loads, teams…
  models/       SQLAlchemy models
  schemas/      Pydantic request/response contracts
  core/         Settings, database session, security helpers
alembic/        Database migrations
tests/          pytest suite (runs against a real Postgres)
```

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

## License

[Apache 2.0](LICENSE)
