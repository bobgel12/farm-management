# Local Development Setup

Local development now uses two explicit modes instead of a single shared `.env`.

## Mode 1: Frontend Local + Production Backend

Use this when working only on the frontend.

```bash
# Dockerized frontend
make frontend-prod-docker

# or host npm frontend
make frontend-prod-host
```

Environment source:

- default: `env.frontend-prod.example`
- optional override: `.env.frontend-prod`

Frontend URL:

- http://localhost:3002

## Mode 2: Frontend Local + Backend Local

Use this when working on the full application.

```bash
make local-up
```

Environment source:

- default: `env.local-backend.example`
- optional override: `.env.local-backend`

Services:

- frontend: http://localhost:3002
- backend API: http://localhost:8002/api
- admin: http://localhost:8002/admin
- PostgreSQL: localhost:5433
- Redis: localhost:6380

The backend runs with `chicken_management.settings_prod` and `DATABASE_URL`, so local development uses the same production-style environment contract while still using Django `runserver`.

## Why There Are Separate Local Env Files

The root `.env` may contain Railway-derived production values. Local commands intentionally avoid using it by default so the two local modes stay explicit and safe.

Use:

- `env.frontend-prod.example` / `.env.frontend-prod`
- `env.local-backend.example` / `.env.local-backend`

## Common Commands

```bash
# Full local stack
make local-up
make local-logs
make local-down
make local-reset

# Frontend local against production backend
make frontend-prod-docker
make frontend-prod-host
make frontend-prod-logs
make frontend-prod-down

# Full-stack helpers
make migrate
make seed
make shell-backend
make shell-db
make status
```

## Prerequisites

```bash
brew install colima docker docker-compose
colima start
docker --version
docker-compose --version
```

## Troubleshooting

### Docker/Colima not running

```bash
colima status
colima start
docker info
```

### Need local overrides

```bash
cp env.local-backend.example .env.local-backend
cp env.frontend-prod.example .env.frontend-prod
```

Then edit only the override file for your machine.
