# Chicken House Management System – Deep Context Brief

## High-Level Overview
- **Stack**: Django REST API + Celery, PostgreSQL/SQLite, React + TypeScript, Material-UI, Docker, Railway (backend) and Vercel (frontend).
- **Purpose**: Manage farms, houses, flocks, and worker tasks while ingesting/analysing telemetry from Rotem controllers to produce operational insights and automated communications.
- **Key Apps**: `farms`, `houses`, `tasks`, `authentication`, `integrations`, `rotem_scraper`, plus health checks and deployment scripts.
- **Core Flows**: Authentication → farm/house CRUD → task generation & completion → daily email reminders → Rotem data ingestion → ML dashboards & scheduled analyses.

## Backend Architecture (Django)
- **Project**: `backend/chicken_management` with environment-driven settings (`decouple`, debug-mode SQLite fallback, Whitenoise, Celery, Redis brokers, CORS setup for ports 3000/3002).
- **Installed Apps**: REST endpoints for farms/houses/tasks/auth, Rotem integrations, ML services, health checks.
- **Data Model Highlights**:
  - `Farm` captures contact details, integration status/credentials, optional link to `Program` templates.
  - `House` (per farm) tracks flock lifecycle, integration identifiers, computed age/status fields.
  - `Task` scheduled per house & day offset, with completion metadata; `EmailTask` logs sends; `RecurringTask` describes repeating jobs.
  - `Program` & `ProgramTask` define task templates with change logs (`ProgramChangeLog`) and retroactive application support.
  - Authentication adds `PasswordResetToken`, `LoginAttempt`, `SecurityEvent` for security telemetry.
  - Integrations track `IntegrationLog`, `IntegrationError`, `IntegrationHealth`; `rotem_scraper` models farms, controllers, datapoints, ML predictions, scrape logs.
- **API Surface** (`backend/chicken_management/urls.py` mounts under `/api/`):
  - `farms/` viewset with integration actions (`configure_integration`, `test_connection`, `sync_data`, `integration_status`) including Rotem house/task sync.
  - Worker and program endpoints (`/workers/`, `/programs/`, `/program-tasks/`) plus change management routes.
  - `houses/` endpoints for list/detail, dashboards, task summaries.
  - `tasks/` endpoints for CRUD, completion, dashboards, scheduling helpers, email triggers, and history.
  - Auth endpoints for login/logout, session checks, password reset/change; JSON-based login supports token + session auth with logging and rate limiting hooks.
  - `integrations/` Celery tasks & ML service endpoints; `rotem_scraper` router exposes data, predictions, ML models, scraper controls, and farm detail by `farm_id`.
  - Health checks (`/api/health/`, `/api/health/detailed/`, readiness/liveness) ensure deploy-time diagnostics.
- **Automation & Schedulers**:
  - `TaskScheduler` populates day -1 to 41 task templates per house and recurring jobs for feed checks. 
```318:402:backend/tasks/task_scheduler.py
        return Task.objects.filter(
            house=house,
            day_offset__range=[current_day, end_day]
        ).order_by('day_offset', 'task_name')
```
  - Celery beat schedules Rotem scraping, ML analysis, integration health updates, report generation (`settings.CELERY_BEAT_SCHEDULE`).
  - `TaskEmailService` orchestrates daily reminder emails, workers filtering, SendGrid fallback, and test sends; respects `DISABLE_EMAIL` for Railway networking.
- **Integration Flow (Rotem)**:
  - `RotemIntegration` wraps scraper login, house count/age discovery, sensor pulls, logging, and health tracking.
```124:195:backend/integrations/rotem.py
            if sensor_data and isinstance(sensor_data, dict):
                response_obj = sensor_data.get('reponseObj') or sensor_data.get('responseObj')
                if response_obj and isinstance(response_obj, dict):
                    ds_data = response_obj.get('dsData', {})
```
  - Farm integration actions persist Rotem credentials, sync houses/tasks, and emit logs/errors for observability.
  - Celery tasks (`backend/integrations/tasks.py`) handle background sync, ML analysis, cleanup, and reporting.

## Frontend Architecture (React + TypeScript)
- **Entry Point**: `frontend/src/App.tsx` wraps router with context providers (auth, farm, task, worker, program, Rotem) and Material-UI theme.
- **Routing**: Protected routes guard dashboard, farms, houses, workers, programs, email manager, security settings, Rotem dashboards; public routes for login/password flows.
- **Contexts**:
  - `AuthContext` manages token storage, boot-time `/auth/user/` check, login/logout flows, surfaces `loading` for protected routes.
  - `FarmContext`, `TaskContext`, `WorkerContext`, `ProgramContext` encapsulate API access, pagination handling, derived summaries, CRUD helpers.
  - `RotemContext` centralises Rotem data fetching, scraper triggers, ML predictions, real-time dashboards, and periodic refreshes.
```137:206:frontend/src/contexts/RotemContext.tsx
  const loadFarms = useCallback(async () => {
    try {
      dispatch({ type: 'SET_LOADING', payload: true });
      const response = await rotemApi.getFarms();
      const farms = Array.isArray(response) ? response : ((response as any).results || []);
      dispatch({ type: 'SET_FARMS', payload: farms });
```
- **Data Access**:
  - `services/api.ts` configures Axios with env-based base URL (`REACT_APP_API_URL` or `http://localhost:8002/api`), injects auth token, redirects on 401.
  - `services/rotemApi.ts` wraps specialized Rotem endpoints, provides real-time aggregation helpers and chart data utilities.
- **UI Highlights**:
  - `ProfessionalDashboard` pulls aggregated stats via contexts, surfaces quick actions and placeholders for recent activities.
  - Farm/Houses pages present combined farm task summaries through `FarmContext` methods (`/farms/:id`, `/houses/:id`).
  - Rotem dashboard (`components/rotem/RotemDashboard.tsx`) combines farm cards, data summaries, scraper logs, real-time sensor cards, temperature detail components, and ML dashboard.
  - Password reset & security components interact with backend auth endpoints for tokenized resets and password change validation feedback.
- **Tech Choices**: Strict TypeScript typing across contexts/types, Material-UI 5 theme, Recharts for data viz, React Router v6, modular component folders.

## Cross-Cutting Concerns & Operations
- **Authentication & Security**:
  - Backend uses DRF token + session auth; custom login view logs attempts, supports rate limit checks, and stores security events.
  - Password reset service issues UUID tokens, enforces strength validation, and records audit metadata.
- **Email & Notifications**:
  - Daily reminders compile per-house tasks, avoid duplicate sends per day, support SendGrid and SMTP; test endpoint available.
  - Email templates stored under `backend/tasks/templates/` (HTML + text) for multi-format messaging.
- **Task Lifecycle**:
  - Houses auto-generate program tasks on creation; historical tasks auto-complete if house is added late.
  - Task completion endpoint updates timestamps/notes; dashboards aggregate today/overdue tasks across all houses.
- **Rotem & ML Pipelines**:
  - `rotem_scraper` app persists farms/controllers/data points, ML predictions and models, scraper logs, and exposes API for dashboards.
  - Celery tasks drive periodic scraping (`scrape_rotem_data`, `analyze_data`, `train_ml_models`), integration sync/health, ML analysis (`run_ml_analysis`, `generate_daily_report`), and cleanup of predictions/logs.
  - Frontend consumes Rotem APIs for real-time sensor views, predictions, anomaly/failure summaries, and manual scrape triggers.
- **Environment & Deployment**:
  - Config via `.env`/`env.example` plus `railway.env.example`; Docker Compose variants for dev/prod/email; Makefile automates dev workflows (`make dev`, `make migrate`, `make seed`, etc.).
  - Railway deployment scripts (`deploy_railway.sh`, `railway_startup.py`); frontend build/deploy to Vercel with `frontend/Dockerfile*` and `vercel.json`.
  - Port adjustments documented (`PORT_CHANGE_SUMMARY.md`), with helper scripts for DB access.
- **Health & Monitoring**:
  - Health endpoints cover basic/detailed status, readiness/liveness, and default program checks for sanity validation.
  - Integration health tracked via `IntegrationHealth` model and updated by scheduled tasks.
- **Testing & Tooling**:
  - Repo includes targeted scripts (`test_django.py`, `test_email.py`, etc.) and management commands for seeding (`farms/management/`).
  - `scripts/` directory houses lint/setup helpers; `Makefile` centralizes commands for developer productivity.

## Observations & Potential Risks
- **Rotem Credentials**: Stored directly on `Farm` model; ensure encryption or secrets management in production.
- **Celery Dependency**: Many workflows assume active Celery + Redis; document fallback behavior for local dev.
- **Email Deliverability**: SendGrid API detection relies on env var suffix; confirm production environment sets `EMAIL_HOST` accordingly.
- **Data Volume**: Rotem data points and logs may grow quickly; cleanup tasks help but ensure monitoring of storage and index performance.
- **Front/Back Sync**: API responses sometimes paginated; contexts attempt to normalize but verify all endpoints align (e.g., Rotem endpoints mixing paginated/non-paginated responses).
- **Security Logging**: Login rate limiting references `PasswordResetService.check_rate_limit`; confirm implementation meets requirements.

## Quick Start & Resources
- **Local Dev**: `make dev` or `docker-compose up -d`, migrations via `make migrate`, seed data with `make seed_data` command; access frontend at `http://localhost:3000`, backend at `http://localhost:8000` (or 8002 per API config).
- **Credentials**: Default admin user controlled via env (`ADMIN_USERNAME`, `ADMIN_PASSWORD`), backend secret from `SECRET_KEY` env.
- **Docs & Guides**: `README.md`, `IMPLEMENTATION_GUIDE.md`, Rotem-specific guides (`ROTEM_PHASE3_COMPLETION.md`, `ROTEM_SETUP_GUIDE.md`), deployment references, and email setup instructions in repo root.

This document should provide new collaborators with a single-entry context for how the system fits together, the major moving parts, and where to dive deeper.


