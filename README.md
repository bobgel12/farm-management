# 🐔 Chicken House Management System

A full-stack application for managing chicken farms, houses, and daily tasks with automated email notifications.

## 🚀 Quick Start

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Colima on macOS) and [Make](https://www.gnu.org/software/make/).

```bash
git clone <repository-url>
cd farm-management

# One command: verify Docker, start stack, migrate, seed sample data
make quick-start
```

First run builds images and may take a few minutes. Later runs are much faster if images are cached.

**Access the application:**

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3002 |
| Backend API | http://localhost:8002/api |
| Admin | http://localhost:8002/admin |

**Default login:** `admin` / `admin123`

> **Important:** Always use `make` targets (or pass `--env-file env.local-backend.example` to Docker Compose). Running plain `docker-compose up` skips required environment variables and the backend will not start.

## 📋 Features

- **Farm Management** - Manage multiple farms with houses
- **Task Scheduling** - Automated daily task generation based on chicken age
- **Worker Management** - Add and manage farm workers
- **Email Notifications** - Daily task reminders via email
- **Real-time Dashboard** - Monitor farm status and tasks
- **Mobile Responsive** - Works on all devices

## 🛠️ Development

### Daily workflow

```bash
# Start (if not already running)
make local-up

# Stop when finished
make local-down

# Follow logs
make local-logs

# Full reset (containers + volumes, then migrate + seed)
make quick-reset
```

### Local ports (default)

| Service | Host port | Notes |
|---------|-----------|--------|
| Frontend | 3002 | React dev server |
| Backend | 8002 | Django / Gunicorn |
| PostgreSQL | 5433 | Local DB only |
| Redis | 6380 | Celery broker |

Override ports or secrets by copying the template:

```bash
cp env.local-backend.example .env.local-backend
# edit .env.local-backend — Make picks it up automatically
```

The full local stack uses `env.local-backend.example` by default (PostgreSQL, production-style Django settings). For frontend-only against a remote backend, use `env.frontend-prod.example` and `make frontend-prod-docker` or `make frontend-prod-host`.

### Development modes

```bash
# Full local stack (recommended)
make quick-start          # First time or fresh data
make local-up             # Start only
make local-down           # Stop

# Frontend local + production backend
make frontend-prod-docker
make frontend-prod-host
```

### Common commands

```bash
make help           # All targets
make status         # Container status
make migrate        # Apply migrations
make seed           # Sample farms/houses/tasks (--clear)
make seed-variety   # Seed with more date/status variety
make email-test     # Send test email
make clean          # Remove containers
```

### Manual setup (without Make)

Always pass the env file:

```bash
docker compose --env-file env.local-backend.example -f docker-compose.yml up -d --build
docker compose --env-file env.local-backend.example -f docker-compose.yml exec backend python manage.py migrate
docker compose --env-file env.local-backend.example -f docker-compose.yml exec backend python manage.py seed_data --clear
```

Test email (replace `YOUR_TOKEN` after logging in via the API):

```bash
curl -X POST 'http://localhost:8002/api/tasks/send-test-email/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{"farm_id":1,"test_email":"your-email@example.com"}'
```

## 📧 Email Setup

### Local Development
1. Copy the full-local template if you need real email credentials:
```bash
cp env.local-backend.example .env.local-backend
# Edit .env.local-backend and set EMAIL_HOST_USER / EMAIL_HOST_PASSWORD
```

2. Test email configuration:
```bash
make email-test
```

### Railway Production
1. Set environment variables in Railway dashboard:
   - `EMAIL_HOST_USER` - Your Gmail address
   - `EMAIL_HOST_PASSWORD` - Gmail App Password
   - `SECRET_KEY` - Django secret key
   - `ADMIN_PASSWORD` - Admin password
   - `DATABASE_URL` - Railway Postgres URL (prefer pooled URL for web runtime)
   - `DB_CONN_MAX_AGE` - Set `0` for pooled transaction mode
   - `DB_CONNECT_TIMEOUT` - Optional, default `15`
   - `DB_STATEMENT_TIMEOUT_MS` - Optional, default `30000`
   - `DB_POOL_MODE` - `transaction` (default) or `session`

2. Deploy:
```bash
make deploy-railway
```

3. Railway service commands:
   - **Web start command**: `python simple_startup.py web`
   - **Migration command (one-off/release)**: `python simple_startup.py migrate`

4. Important: do not run migrations in normal web startup. Keep migrations as a one-off deploy step to avoid DB connection spikes and `too many clients` errors.

## 🏗️ Architecture

- **Backend**: Django REST Framework + PostgreSQL
- **Frontend**: React + TypeScript + Material-UI
- **Database**: PostgreSQL in production and in the supported local full-stack mode
- **Email**: Gmail SMTP
- **Deployment**: Railway + Docker

## 📁 Project Structure

```
farm-management/
├── backend/                 # Django API
│   ├── farms/              # Farm and worker management
│   ├── houses/             # House management
│   ├── tasks/              # Task scheduling and email
│   └── authentication/     # User authentication
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts
│   │   └── services/       # API services
├── docker-compose.yml      # Development setup
├── docker-compose.prod.yml # Production setup
├── Makefile               # Development commands
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `EMAIL_HOST_USER` | Gmail address | Required |
| `EMAIL_HOST_PASSWORD` | Gmail App Password | Required |
| `SECRET_KEY` | Django secret key | Auto-generated |
| `ADMIN_PASSWORD` | Admin password | admin123 |
| `DEBUG` | Debug mode | True (dev) / False (prod) |

### Gmail App Password Setup

1. Enable 2-Factor Authentication on Google
2. Go to [Google Account Settings](https://myaccount.google.com/)
3. Security → 2-Step Verification → App passwords
4. Generate password for "Mail"
5. Use the 16-character password in `EMAIL_HOST_PASSWORD`

## 🚀 Deployment

### Railway (Recommended)

```bash
# Deploy to Railway
make deploy-railway
```

Railway runtime recommendations:
- Use Gunicorn web runtime (already handled by `simple_startup.py web`)
- Run migrations separately (`simple_startup.py migrate`)
- Keep web process count low first (`WEB_CONCURRENCY=1`) and scale carefully

### Manual Docker

```bash
# Production build
make prod-build
make prod-up
```

## 📚 API Documentation

### Authentication
- **Login**: `POST /api/auth/login/`
- **Logout**: `POST /api/auth/logout/`

### Farms
- **List**: `GET /api/farms/`
- **Detail**: `GET /api/farms/{id}/`
- **Workers**: `GET /api/farms/{id}/workers/`

### Tasks
- **List**: `GET /api/tasks/`
- **Send Email**: `POST /api/tasks/send-test-email/`
- **Daily Tasks**: `POST /api/tasks/send-daily-tasks/`

## 🐛 Troubleshooting

### Common Issues

1. **Backend exits immediately / empty env warnings**
   - Cause: `docker compose up` without `--env-file`.
   - Fix: `make local-down && make quick-start` (or `make local-up`).

2. **Port already in use** (3002, 8002, 5433, 6380)
   ```bash
   make local-down
   make clean
   make local-up
   ```
   Or change ports in `.env.local-backend` (copy from `env.local-backend.example`).

3. **`make seed` fails on PostgreSQL**
   - Fixed in current `seed_data` (SQLite-only sequence reset). If you still see errors, run `make quick-reset`.

4. **Email not working locally**
   - Local stack uses safe empty email password by default.
   - Copy `env.local-backend.example` → `.env.local-backend` and set credentials, then `make email-test`.

5. **Database issues**
   ```bash
   make local-down
   make local-up
   make wait-backend
   make migrate
   ```

### Getting Help

- Logs: `make local-logs` or `make logs`
- Status: `make status`
- Full reset: `make quick-reset`
- All commands: `make help`

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

## 🆕 NEW: Rotem Integration (Phase 3 Complete)

**✅ ROTEM INTEGRATION COMPLETE** - Full-stack farm monitoring system:
- Multi-farm support with individual credentials
- Real-time data processing from RotemNetWeb API
- Comprehensive sensor data collection (temperature, humidity, pressure, etc.)
- RESTful API endpoints for frontend integration
- Automated data scraping with Celery tasks
- **NEW: ML Dashboard with AI insights**
- **NEW: Real-time sensor data visualization**
- **NEW: Equipment failure prediction**
- **NEW: Environmental optimization recommendations**
- **NEW: System performance analysis**

### Quick Start with Rotem Integration
```bash
# Add a farm with Rotem credentials
make rotem-setup

# Test the scraper
make rotem-test

# View scraper logs
make rotem-logs

# Access the ML Dashboard
# Navigate to: http://localhost:3002/rotem
```

### New ML Features
- **Anomaly Detection**: Real-time detection of unusual patterns
- **Failure Prediction**: ML-based equipment failure predictions
- **Optimization**: AI-powered environmental recommendations
- **Performance Analysis**: System health and efficiency metrics
- **Interactive Dashboard**: Complete ML insights interface

See [ROTEM_PHASE3_COMPLETION.md](ROTEM_PHASE3_COMPLETION.md) for detailed documentation.

---

**Need help?** Check the `make help` command for all available options!
