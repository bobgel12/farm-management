#!/bin/bash

# Simple Railway Deployment Script
echo "🚀 Simple Railway Deployment for Chicken House Management System..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
fi

# Create a new project if none exists
echo "🔗 Setting up Railway project..."
if [ ! -f ".railway/project.json" ]; then
    echo "Creating new Railway project..."
    railway init
fi

# Use the TOML configuration
echo "📝 Using railway.toml configuration..."
cp railway.toml .railway.toml

# Set production environment
echo "⚙️  Setting production environment..."
export DJANGO_SETTINGS_MODULE=chicken_management.settings_prod

# Deploy
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment initiated!"
echo "🌐 Check your Railway dashboard for the deployment URL"
echo ""
echo "📧 Next steps:"
echo "1. Go to Railway dashboard: https://railway.app/dashboard"
echo "2. Set up environment variables:"
echo "   - SECRET_KEY=your-secret-key"
echo "   - DATABASE_URL=postgresql://..."
echo "   - EMAIL_HOST_USER=your-email@gmail.com"
echo "   - EMAIL_HOST_PASSWORD=your-app-password"
echo "3. Add PostgreSQL database service"
echo "4. Run migrations: railway run python manage.py migrate"
echo "5. Create superuser: railway run python manage.py createsuperuser"
echo ""
echo "📚 For troubleshooting, see RAILWAY_TROUBLESHOOTING.md"

