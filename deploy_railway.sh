#!/bin/bash

# Railway Deployment Script for Chicken House Management System
# This script helps deploy the application to Railway with proper email configuration

echo "🐔 Deploying Chicken House Management System to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first:"
    echo "   npm install -g @railway/cli"
    echo "   or visit: https://docs.railway.app/develop/cli"
    exit 1
fi

# Check if user is logged in
if ! railway whoami &> /dev/null; then
    echo "🔐 Please login to Railway first:"
    echo "   railway login"
    exit 1
fi

echo "✅ Railway CLI is ready"

# Create new project or link to existing
echo "📁 Setting up Railway project..."
if [ ! -f ".railway/project.json" ]; then
    echo "Creating new Railway project..."
    railway init
else
    echo "Linking to existing Railway project..."
    railway link
fi

# Add PostgreSQL service
echo "🗄️ Adding PostgreSQL service..."
railway add postgresql

# Set environment variables
echo "⚙️ Setting up environment variables..."

# Required Django settings
railway variables set SECRET_KEY="$(openssl rand -base64 32)"
railway variables set DEBUG=False
railway variables set ALLOWED_HOSTS="*.railway.app,localhost,127.0.0.1"

# Admin credentials
railway variables set ADMIN_USERNAME=admin
railway variables set ADMIN_PASSWORD="$(openssl rand -base64 16)"
railway variables set ADMIN_EMAIL=admin@chickenmanagement.com

# Email configuration (user needs to set these)
echo "📧 Email configuration required:"
echo "   Please set these variables in Railway dashboard:"
echo "   - EMAIL_HOST_USER=your-email@gmail.com"
echo "   - EMAIL_HOST_PASSWORD=your-app-password"
echo "   - DEFAULT_FROM_EMAIL=noreply@yourdomain.com"
echo ""
echo "   Or run these commands:"
echo "   railway variables set EMAIL_HOST_USER=your-email@gmail.com"
echo "   railway variables set EMAIL_HOST_PASSWORD=your-app-password"
echo "   railway variables set DEFAULT_FROM_EMAIL=noreply@yourdomain.com"

# Set default email settings
railway variables set EMAIL_HOST=smtp.gmail.com
railway variables set EMAIL_PORT=587
railway variables set EMAIL_USE_TLS=True

# Deploy the application
echo "🚀 Deploying application..."
railway up

# Get the deployed URL
echo "🌐 Getting deployment URL..."
DEPLOY_URL=$(railway domain)
echo "✅ Application deployed at: https://$DEPLOY_URL"

# Test email configuration
echo "🧪 Testing email configuration..."
echo "   You can test email by running:"
echo "   railway run python manage.py send_daily_tasks --test --farm-id 1 --test-email your-email@example.com"

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📋 Next steps:"
echo "1. Set up email credentials in Railway dashboard"
echo "2. Access your app: https://$DEPLOY_URL"
echo "3. Login with admin credentials"
echo "4. Add farms and workers"
echo "5. Test daily email functionality"
echo ""
echo "📚 For more information, see RAILWAY_EMAIL_SETUP.md"