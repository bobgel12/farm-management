#!/bin/bash

# Connect to PostgreSQL database on port 5433
# This script helps you connect to the chicken management database

echo "🐔 Connecting to Chicken Management Database..."
echo "📍 Host: localhost"
echo "🔌 Port: 5433"
echo "🗄️  Database: chicken_management"
echo "👤 User: postgres"
echo ""

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo "❌ psql is not installed. Please install PostgreSQL client tools."
    echo "   On macOS: brew install postgresql"
    echo "   On Ubuntu: sudo apt-get install postgresql-client"
    exit 1
fi

# Connect to the database
psql -h localhost -p 5433 -U postgres -d chicken_management
