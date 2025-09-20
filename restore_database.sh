#!/bin/bash

# Script to restore database data from a dump file
# Usage: ./restore_database.sh [dump_file]

set -e

# Default dump file (most recent)
DUMP_FILE=${1:-$(ls -t database_dump_*.sql 2>/dev/null | head -1)}

if [ -z "$DUMP_FILE" ] || [ ! -f "$DUMP_FILE" ]; then
    echo "❌ No dump file found. Please provide a valid dump file."
    echo "Usage: $0 [dump_file]"
    echo "Available dump files:"
    ls -la database_dump_*.sql 2>/dev/null || echo "   No dump files found"
    exit 1
fi

echo "🗄️  Restoring database from $DUMP_FILE..."

# Check if containers are running
if ! docker-compose ps | grep -q "chicken_house_management-db-1.*Up"; then
    echo "❌ Database container is not running. Please start the application first."
    exit 1
fi

# Check if backend is running
if ! docker-compose ps | grep -q "chicken_house_management-backend-1.*Up"; then
    echo "❌ Backend container is not running. Please start the application first."
    exit 1
fi

echo "⚠️  This will replace all existing data in the database!"
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Operation cancelled."
    exit 1
fi

# Drop and recreate the database
echo "🔄 Recreating database..."
docker-compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS chicken_management;"
docker-compose exec -T db psql -U postgres -c "CREATE DATABASE chicken_management;"

# Restore the dump
echo "📥 Restoring data from dump..."
docker-compose exec -T db psql -U postgres -d chicken_management < "$DUMP_FILE"

# Run migrations to ensure schema is up to date
echo "🔄 Running migrations..."
docker-compose exec backend python manage.py migrate

echo "✅ Database restored successfully from $DUMP_FILE"
echo "📊 Restored data:"
echo "   - Farms: $(docker-compose exec -T backend python manage.py shell -c "from farms.models import Farm; print(Farm.objects.count())")"
echo "   - Houses: $(docker-compose exec -T backend python manage.py shell -c "from houses.models import House; print(House.objects.count())")"
echo "   - Tasks: $(docker-compose exec -T backend python manage.py shell -c "from tasks.models import Task; print(Task.objects.count())")"
echo "   - Workers: $(docker-compose exec -T backend python manage.py shell -c "from farms.models import Worker; print(Worker.objects.count())")"
