# 🐔 Chicken House Management System

A comprehensive web application for managing multiple chicken farms with automated task scheduling based on chicken age. The system tracks daily tasks for each house from day -1 (setup) through day 41 (cleanup).

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![Material-UI](https://img.shields.io/badge/Material--UI-5.0+-purple.svg)](https://mui.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com/)

## ✨ Features

- **🏭 Farm Management**: Create and manage multiple farms with location and contact information
- **🏠 House Management**: Add houses to farms with configurable chicken in/out dates
- **📅 Task Scheduling**: Automatic task generation based on chicken age (days -1 to 41)
- **📊 Dashboard**: Overview of all farms, houses, and tasks with real-time updates
- **✅ Task Management**: Mark tasks as completed with notes and completion tracking
- **🔐 Authentication**: Secure token-based authentication system
- **📱 Responsive UI**: Modern Material-UI interface for desktop and mobile
- **📧 Email Notifications**: Daily task reminders sent to farm workers
- **🌐 Production Ready**: Docker containerization with PostgreSQL database
- **🚀 Easy Deployment**: One-click deployment to Railway, Render, or Vercel

## Technology Stack

### Backend
- **Django 4.2+** with Django REST Framework
- **PostgreSQL** (production) / SQLite (development)
- **Python 3.11+**

### Frontend
- **React 18+** with TypeScript
- **Material-UI (MUI) v5**
- **React Router v6**

### Deployment
- **Docker** with docker-compose
- **Nginx** reverse proxy
- **PostgreSQL** database

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/chicken-house-management.git
   cd chicken-house-management
   ```

2. **Run the automated setup script** (Recommended)
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   This script will:
   - Check for Docker and install Colima on macOS if needed
   - Resolve port conflicts automatically
   - Create necessary environment files
   - Build and start all containers
   - Set up the database with migrations
   - Create admin user
   - Wait for all services to be ready
   - Test API connectivity

3. **Manual setup** (Alternative)
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - Admin Panel: http://localhost:8000/admin
   - Default credentials: `admin` / `admin123`

## 🌐 Production Deployment

### Option 1: Railway (Recommended)
```bash
# Deploy to Railway
./deploy_railway.sh
```

### Option 2: Render
```bash
# Deploy to Render
./deploy_render.sh
```

### Option 3: Manual Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy
For a quick production deployment, see [QUICK_DEPLOY.md](QUICK_DEPLOY.md).

## 🔧 Troubleshooting

### Quick Fix
If you encounter issues, run the quick fix script:
```bash
./quick-fix.sh
```

### Common Issues

#### Port Conflicts
If you get "port already in use" errors:
```bash
# Check what's using the port
lsof -i :5432  # or :8000, :3000

# Kill the process
kill <PID>
```

#### CSRF Errors
If you see CSRF origin checking errors, the setup script automatically configures `CSRF_TRUSTED_ORIGINS` to include `http://localhost:3000`.

#### Database Issues
If you get "no such table" errors:
```bash
docker-compose exec backend python manage.py makemigrations
docker-compose exec backend python manage.py migrate
```

#### Frontend Compilation Errors
If the frontend won't compile:
```bash
docker-compose restart frontend
```

### Detailed Troubleshooting
For more detailed troubleshooting information, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md).

## 📁 Project Structure

4. **Default credentials**
   - Username: `admin`
   - Password: `admin123`

### Production Deployment

1. **Copy environment file**
   ```bash
   cp env.example .env
   ```

2. **Update environment variables**
   Edit `.env` file with your production settings:
   - Set secure database password
   - Set secret key
   - Set admin credentials
   - Set allowed hosts

3. **Deploy with production configuration**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

## Task Schedule

The system automatically generates tasks based on chicken age:

### Day -1: House Setup
- Open heater pipe lock
- Turn heater (24 hours ahead)
- Turn water on and check water line
- Replace filter and set water pressure
- Place feed trays and set up turbo

### Day 0: Chicken Arrival
- Chicken is in
- Check water line and heater
- Check feed is full

### Days 1-7: Early Care
- Daily water pressure adjustments
- Death chicken pickup
- Manual feed management

### Day 8: Full House Operations
- Full house feed and water
- Heat management
- Automatic feed controller

### Days 9-21: Growth Phase
- Feeder monitoring and adjustment
- Water pressure increases
- Coolpad activation

### Days 35-40: Exit Planning
- Schedule confirmation
- Pre-exit preparation
- Exit day procedures

### Day 41: Cleanup
- Post-exit cleanup tasks

## API Endpoints

### Farms
- `GET /api/farms/` - List all farms
- `POST /api/farms/` - Create new farm
- `GET /api/farms/{id}/` - Get farm details
- `PUT /api/farms/{id}/` - Update farm
- `DELETE /api/farms/{id}/` - Delete farm

### Houses
- `GET /api/houses/` - List all houses
- `POST /api/houses/` - Create new house
- `GET /api/houses/{id}/` - Get house details
- `PUT /api/houses/{id}/` - Update house
- `DELETE /api/houses/{id}/` - Delete house

### Tasks
- `GET /api/tasks/` - List all tasks
- `GET /api/houses/{id}/tasks/` - Get tasks for house
- `POST /api/tasks/{id}/complete/` - Mark task complete
- `POST /api/houses/{id}/tasks/generate/` - Generate tasks for house

### Authentication
- `POST /api/auth/login/` - Login
- `POST /api/auth/logout/` - Logout
- `GET /api/auth/user/` - Get user info

## Development

### Backend Development

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Frontend Development

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

## Project Structure

```
chicken_house_management/
├── backend/
│   ├── chicken_management/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── farms/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── houses/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   └── urls.py
│   ├── tasks/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── task_scheduler.py
│   │   └── urls.py
│   ├── authentication/
│   │   ├── views.py
│   │   └── urls.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── contexts/
│   │   ├── services/
│   │   └── App.tsx
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── docker-compose.prod.yml
└── README.md
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For support and questions, please contact the development team or create an issue in the repository.
# farm-management
