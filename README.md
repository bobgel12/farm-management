# 🐔 Chicken House Management System

A full-stack application for managing chicken farms, houses, and daily tasks with automated email notifications.

## 🚀 Quick Start

```bash
# Clone and setup
git clone <repository-url>
cd chicken_house_management

# Quick start (install, start, migrate, seed)
make quick-start
```

**Access the application:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin (admin/admin123)

## 📋 Features

- **Farm Management** - Manage multiple farms with houses
- **Task Scheduling** - Automated daily task generation based on chicken age
- **Worker Management** - Add and manage farm workers
- **Email Notifications** - Daily task reminders via email
- **Real-time Dashboard** - Monitor farm status and tasks
- **Mobile Responsive** - Works on all devices

## 🛠️ Development

### Prerequisites
- Docker & Docker Compose
- Make (optional, for convenience commands)

### Available Commands

```bash
# Development
make dev          # Start development environment
make logs         # Show logs
make restart      # Restart services
make down         # Stop services

# Database
make migrate      # Run migrations
make seed         # Seed with sample data
make seed-variety # Seed with variety of data

# Email
make email-test   # Send test email
make email-daily  # Send daily emails

# Utilities
make clean        # Clean up containers
make status       # Show service status
make help         # Show all commands
```

### Manual Setup (without Make)

```bash
# Start services
docker-compose up -d

# Run migrations
docker-compose exec backend python manage.py migrate

# Seed database
docker-compose exec backend python manage.py seed_data --clear

# Send test email
curl -X POST 'http://localhost:8000/api/tasks/send-test-email/' \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Token YOUR_TOKEN' \
  -d '{"farm_id":1,"test_email":"your-email@gmail.com"}'
```

## 📧 Email Setup

### Local Development
1. Create `.env` file with your Gmail credentials:
```bash
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
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
- **Database**: PostgreSQL (production) / SQLite (development)
- **Email**: Gmail SMTP
- **Deployment**: Railway + Docker

## 📁 Project Structure

```
chicken_house_management/
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

1. **Port already in use**
   ```bash
   make clean
   make dev
   ```

2. **Email not working**
   - Check Gmail App Password
   - Verify environment variables
   - Test with `make email-test`

3. **Database issues**
   ```bash
   make down
   make up
   make migrate
   ```

### Getting Help

- Check logs: `make logs`
- Test email: `make email-test`
- Reset everything: `make quick-reset`

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