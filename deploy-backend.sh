#!/bin/bash

# Deploy Backend to Railway
echo "🚀 Deploying Backend to Railway..."

# Check if we're in the right directory
if [ ! -f "backend/manage.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    exit 1
fi

# Deploy to Railway
echo "📦 Deploying backend..."
railway up --service backend

echo "✅ Backend deployment initiated!"
echo "🔗 Check your Railway dashboard for deployment status"
echo "📝 Don't forget to set environment variables:"
echo "   - SECRET_KEY"
echo "   - DATABASE_URL (if not using Railway PostgreSQL)"
echo "   - CORS_ALLOWED_ORIGINS (your frontend URL)"
