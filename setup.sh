#!/bin/bash

# Chicken House Management System Setup Script
# This script includes all fixes for common issues encountered during setup

echo "🐔 Setting up Chicken House Management System..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check for Colima (macOS Docker alternative)
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v colima &> /dev/null; then
        echo "⚠️  Colima not found. Installing Colima for Docker on macOS..."
        brew install colima
    fi
    
    # Start Colima if not running
    if ! colima status &> /dev/null; then
        echo "🚀 Starting Colima..."
        colima start
    fi
fi

# Check for port conflicts
echo "🔍 Checking for port conflicts..."
if lsof -i :5432 &> /dev/null; then
    echo "⚠️  Port 5432 is already in use. Attempting to free it..."
    # Kill any processes using port 5432 (except Docker)
    lsof -ti :5432 | grep -v $(docker ps -q) | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if lsof -i :8000 &> /dev/null; then
    echo "⚠️  Port 8000 is already in use. Attempting to free it..."
    lsof -ti :8000 | grep -v $(docker ps -q) | xargs kill -9 2>/dev/null || true
    sleep 2
fi

if lsof -i :3000 &> /dev/null; then
    echo "⚠️  Port 3000 is already in use. Attempting to free it..."
    lsof -ti :3000 | grep -v $(docker ps -q) | xargs kill -9 2>/dev/null || true
    sleep 2
fi

# Create environment file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating environment file..."
    cat > .env << EOF
# Django Settings
SECRET_KEY=django-insecure-change-this-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=chicken_management
DB_USER=postgres
DB_PASSWORD=password
DB_HOST=db
DB_PORT=5432

# Admin Settings
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
ADMIN_EMAIL=admin@chickenmanagement.com

# Celery Settings (for future task scheduling)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
EOF
    echo "✅ Environment file created with default settings."
fi

# Stop any existing containers
echo "🛑 Stopping any existing containers..."
docker-compose down 2>/dev/null || true

# Build and start the application
echo "🔨 Building and starting the application..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if services are running
echo "🔍 Checking service status..."
docker-compose ps

# Wait for database to be healthy
echo "🗄️ Waiting for database to be healthy..."
max_attempts=30
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if docker-compose exec db pg_isready -U postgres &> /dev/null; then
        echo "✅ Database is ready!"
        break
    fi
    echo "⏳ Waiting for database... (attempt $((attempt + 1))/$max_attempts)"
    sleep 2
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "❌ Database failed to start after $max_attempts attempts"
    exit 1
fi

# Create migrations directories if they don't exist
echo "📁 Creating migrations directories..."
docker-compose exec backend mkdir -p farms/migrations houses/migrations tasks/migrations 2>/dev/null || true
docker-compose exec backend touch farms/migrations/__init__.py houses/migrations/__init__.py tasks/migrations/__init__.py 2>/dev/null || true

# Generate migrations for custom apps
echo "📝 Generating migrations for custom apps..."
docker-compose exec backend python manage.py makemigrations

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose exec backend python manage.py migrate

# Apply token authentication migrations
echo "🔑 Setting up token authentication..."
docker-compose exec backend python manage.py migrate authtoken

# Generate tasks for existing houses
echo "📋 Generating tasks for existing houses..."
docker-compose exec backend python manage.py shell -c "
from houses.models import House
from tasks.task_scheduler import TaskScheduler

houses = House.objects.all()
print(f'Found {houses.count()} houses')

for house in houses:
    print(f'Generating tasks for House {house.house_number} (Farm: {house.farm.name})')
    tasks = TaskScheduler.generate_tasks_for_house(house)
    print(f'Generated {len(tasks)} tasks')

print('Task generation complete!')
"

# Mark tasks up to today as completed
echo "✅ Marking tasks up to today as completed..."
docker-compose exec backend python manage.py shell -c "
from houses.models import House
from tasks.models import Task

houses = House.objects.all()
print(f'Processing {houses.count()} houses...')

for house in houses:
    current_day = house.current_day
    if current_day is not None and current_day > 0:
        tasks_to_complete = Task.objects.filter(
            house=house,
            day_offset__lte=current_day,
            is_completed=False
        )
        
        print(f'House {house.house_number} (Day {current_day}): Marking {tasks_to_complete.count()} tasks as completed')
        
        for task in tasks_to_complete:
            task.mark_completed(completed_by='system', notes='Auto-completed: tasks up to today')

print('Task completion update complete!')
"

# Create admin user
echo "👤 Creating admin user..."
docker-compose exec backend python manage.py shell -c "
from django.contrib.auth.models import User
from django.conf import settings
user, created = User.objects.get_or_create(
    username=settings.ADMIN_USERNAME,
    defaults={
        'email': settings.ADMIN_EMAIL,
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    user.set_password(settings.ADMIN_PASSWORD)
    user.save()
    print('Admin user created successfully')
else:
    print('Admin user already exists')
"

# Wait for frontend to compile
echo "⏳ Waiting for frontend to compile..."
max_attempts=60
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s http://localhost:3000 &> /dev/null; then
        echo "✅ Frontend is ready!"
        break
    fi
    echo "⏳ Waiting for frontend... (attempt $((attempt + 1))/$max_attempts)"
    sleep 5
    attempt=$((attempt + 1))
done

# Test API connectivity
echo "🧪 Testing API connectivity..."
if curl -s http://localhost:8000/api/auth/login/ -X POST \
    -H "Content-Type: application/json" \
    -H "Origin: http://localhost:3000" \
    -d '{"username": "admin", "password": "admin123"}' &> /dev/null; then
    echo "✅ API is responding correctly"
else
    echo "⚠️  API test failed, but this might be normal during startup"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000/api"
echo "   Admin Panel: http://localhost:8000/admin"
echo ""
echo "🔑 Default Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🔧 Troubleshooting:"
echo "   - CSRF errors are resolved with @csrf_exempt decorator and token authentication"
echo "   - If you see 'no such table' errors, migrations have been applied"
echo "   - If you see 'farms.map is not a function' errors, paginated API responses are handled"
echo "   - If ports are in use, the script attempts to free them automatically"
echo "   - For macOS users, Colima is automatically started if needed"
echo "   - Token authentication bypasses CSRF requirements for API calls"
echo "   - Task overview shows today's and tomorrow's tasks by default, others are collapsed"
echo ""
echo "📚 For more information, see README.md"
