# Chicken House Management - Development Guide

## Overview

This is a full-stack chicken house management system built with Django REST API backend and React TypeScript frontend.

## Tech Stack

### Backend
- **Framework**: Django 4.2.7 with Django REST Framework
- **Database**: PostgreSQL (production), SQLite (development)
- **Authentication**: JWT tokens
- **Task Queue**: Celery with Redis
- **Deployment**: Docker, Railway

### Frontend
- **Framework**: React 18 with TypeScript
- **UI Library**: Material-UI (MUI)
- **State Management**: React Context
- **HTTP Client**: Axios
- **Deployment**: Vercel

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- npm 8+
- Git

### Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd chicken_house_management
   ./scripts/dev-setup.sh
   ```

2. **Setup multi-agent development**:
   ```bash
   ./scripts/setup-agents.sh
   ```

3. **Start development servers**:
   ```bash
   ./scripts/start-dev.sh
   ```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api
   - Admin Panel: http://localhost:8000/admin

### Multi-Agent Development
This project uses a multi-agent development approach with specialized agents:
- **Frontend Specialist**: React, TypeScript, Material-UI
- **Backend Specialist**: Django, Django REST Framework, Python
- **DevOps Specialist**: Docker, deployment, CI/CD
- **Testing Specialist**: Test automation, quality assurance
- **Security Specialist**: Application security, authentication
- **Database Specialist**: Database design, optimization
- **UI/UX Specialist**: User interface design, accessibility
- **Performance Specialist**: Application performance, optimization

See [MULTI_AGENT_SETUP.md](MULTI_AGENT_SETUP.md) for detailed agent configuration.

### Manual Setup

#### Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## Project Structure

```
chicken_house_management/
├── backend/                 # Django backend
│   ├── authentication/     # Auth app
│   ├── farms/             # Farm management
│   ├── houses/            # House management
│   ├── tasks/             # Task scheduling
│   ├── health/            # Health checks
│   └── chicken_management/ # Main Django project
├── frontend/              # React frontend
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── contexts/      # React contexts
│   │   ├── services/      # API services
│   │   └── types/         # TypeScript types
│   └── public/           # Static files
├── scripts/              # Development scripts
├── .vscode/             # VS Code/Cursor configuration
└── docs/               # Documentation
```

## Code Quality

### Frontend
- **ESLint**: Code linting with TypeScript support
- **Prettier**: Code formatting
- **TypeScript**: Type checking

### Backend
- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Code linting
- **MyPy**: Type checking

### Running Quality Checks
```bash
# Check all code quality
./scripts/lint-check.sh

# Fix common issues automatically
./scripts/fix-code.sh

# Frontend only
cd frontend
npm run lint
npm run format
npm run type-check

# Backend only
cd backend
source venv/bin/activate
black .
isort .
flake8 .
mypy .
```

## Development Workflow

### Git Workflow
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "feat: add new feature"`
3. Push branch: `git push origin feature/your-feature`
4. Create pull request

### Commit Convention
We use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/tooling changes

### Code Review Checklist
- [ ] Code follows project style guidelines
- [ ] Tests are included and passing
- [ ] Error handling is implemented
- [ ] Security considerations addressed
- [ ] Performance implications considered
- [ ] Documentation updated if needed

## Testing

### Frontend Testing
```bash
cd frontend
npm test                    # Run tests
npm test -- --coverage     # Run with coverage
```

### Backend Testing
```bash
cd backend
source venv/bin/activate
python manage.py test       # Run tests
pytest --cov=.            # Run with coverage
```

## API Documentation

### Authentication
- **POST** `/api/auth/login/` - User login
- **POST** `/api/auth/logout/` - User logout
- **POST** `/api/auth/register/` - User registration

### Farms
- **GET** `/api/farms/` - List farms
- **POST** `/api/farms/` - Create farm
- **GET** `/api/farms/{id}/` - Get farm details
- **PUT** `/api/farms/{id}/` - Update farm
- **DELETE** `/api/farms/{id}/` - Delete farm

### Houses
- **GET** `/api/houses/` - List houses
- **POST** `/api/houses/` - Create house
- **GET** `/api/houses/{id}/` - Get house details
- **PUT** `/api/houses/{id}/` - Update house
- **DELETE** `/api/houses/{id}/` - Delete house

### Tasks
- **GET** `/api/tasks/` - List tasks
- **POST** `/api/tasks/` - Create task
- **GET** `/api/tasks/{id}/` - Get task details
- **PUT** `/api/tasks/{id}/` - Update task
- **DELETE** `/api/tasks/{id}/` - Delete task

## Environment Variables

### Backend (.env)
```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///db.sqlite3
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000
CELERY_BROKER_URL=redis://localhost:6379/0
```

### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENVIRONMENT=development
```

## Deployment

### Docker Development
```bash
docker-compose up --build
```

### Production Deployment
- **Backend**: Railway
- **Frontend**: Vercel
- **Database**: Railway PostgreSQL

## Troubleshooting

### Common Issues

1. **Port already in use**:
   ```bash
   # Kill process on port 8000
   lsof -ti:8000 | xargs kill -9
   
   # Kill process on port 3000
   lsof -ti:3000 | xargs kill -9
   ```

2. **Database migration issues**:
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Node modules issues**:
   ```bash
   cd frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

4. **Python virtual environment issues**:
   ```bash
   cd backend
   rm -rf venv
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## Useful Commands

### Backend
```bash
# Run server
python manage.py runserver

# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run tests
python manage.py test

# Collect static files
python manage.py collectstatic

# Run Celery worker
celery -A chicken_management worker -l info

# Run Celery beat
celery -A chicken_management beat -l info
```

### Frontend
```bash
# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint

# Format code
npm run format

# Type check
npm run type-check
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run quality checks
6. Submit a pull request

## Support

For questions or issues:
1. Check the troubleshooting section
2. Search existing issues
3. Create a new issue with detailed information
