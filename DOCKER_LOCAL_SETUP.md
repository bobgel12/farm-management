# Local Development Modes

This project has two explicit local workflows. Choose the mode first, then run one command.

## Prerequisites

On macOS, use Colima as the Docker runtime:

```bash
brew install colima docker docker-compose
colima start
docker --version
docker-compose --version
```

## Mode 1: Frontend Local + Production Backend

Use this when you only need to work on the React UI and want it to talk to the deployed Railway API.

The default template is `env.frontend-prod.example`. If you need machine-specific overrides, copy it to `.env.frontend-prod`.

### Dockerized frontend

```bash
make frontend-prod-docker
```

### Host npm frontend

```bash
make frontend-prod-host
```

Both variants intentionally use:

```bash
REACT_APP_API_URL=https://farm-management-production-54e4.up.railway.app/api
```

Open the frontend at:

- http://localhost:3002

Useful commands:

```bash
make frontend-prod-logs
make frontend-prod-down
```

## Mode 2: Frontend Local + Backend Local

Use this when you need the whole application locally.

The default template is `env.local-backend.example`. If you need machine-specific overrides, copy it to `.env.local-backend`.

```bash
make local-up
```

This starts:

- React frontend on `http://localhost:3002`
- Django backend on `http://localhost:8002`
- PostgreSQL on `localhost:5433`
- Redis on `localhost:6380`

The local backend uses the production-style settings path:

```bash
DJANGO_SETTINGS_MODULE=chicken_management.settings_prod
DATABASE_URL=postgresql://postgres:password@db:5432/chicken_management
```

That means local backend behavior follows the same environment contract as deployment while still using Django `runserver` for easier iteration.

Useful commands:

```bash
make local-logs
make local-down
make local-reset
make migrate
make seed
make shell-backend
make shell-db
```

Default local admin credentials:

- Username: `admin`
- Password: `admin123`

## Environment Files

Do not use the root `.env` as the default local-development source of truth. It may contain Railway-derived values.

Use these mode-specific files instead:

| Mode | Checked-in template | Optional local override |
| --- | --- | --- |
| Frontend local + production backend | `env.frontend-prod.example` | `.env.frontend-prod` |
| Full local stack | `env.local-backend.example` | `.env.local-backend` |

The Makefile automatically prefers the optional override file when present; otherwise it uses the checked-in template.

## Troubleshooting

### Docker daemon is not running

```bash
colima status
colima start
docker info
```

### Port already in use

```bash
lsof -i :3002
lsof -i :8002
lsof -i :5433
lsof -i :6380
```

Change the host port values in `.env.local-backend` or `.env.frontend-prod` if needed.

### Confirm the local backend is using PostgreSQL

```bash
make local-up
docker-compose --env-file env.local-backend.example -f docker-compose.yml exec backend \
  python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default']['ENGINE'])"
```

Expected output:

```bash
django.db.backends.postgresql
```
