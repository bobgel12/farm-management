#!/bin/bash

# Render Deployment Script for Chicken House Management System
echo "🚀 Deploying Chicken House Management System to Render..."

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "📦 Installing Render CLI..."
    curl -fsSL https://cli.render.com/install | sh
    export PATH="$PATH:$HOME/.render/bin"
fi

# Check if user is logged in
if ! render auth whoami &> /dev/null; then
    echo "🔐 Please log in to Render..."
    render auth login
fi

# Create render.yaml if it doesn't exist
if [ ! -f "render.yaml" ]; then
    echo "📝 Creating render.yaml configuration..."
    cat > render.yaml << EOF
services:
  - type: web
    name: chicken-house-management
    env: python
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && python manage.py migrate && python manage.py runserver 0.0.0.0:\$PORT
    healthCheckPath: /api/
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: chicken_management.settings_prod
      - key: SECRET_KEY
        generateValue: true
      - key: DEBUG
        value: False
      - key: ALLOWED_HOSTS
        value: your-app.onrender.com
    disk:
      name: chicken-house-storage
      mountPath: /app/logs
      sizeGB: 1

  - type: pserv
    name: chicken-house-db
    env: postgresql
    plan: free
    databaseName: chicken_management
    databaseUser: chicken_user
    region: oregon

cronJobs:
  - name: daily-task-emails
    env: python
    schedule: "0 21 * * *"
    buildCommand: cd backend && pip install -r requirements.txt
    startCommand: cd backend && python manage.py send_daily_tasks
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: chicken_management.settings_prod
      - key: DATABASE_URL
        fromDatabase:
          name: chicken-house-db
          property: connectionString
EOF
fi

# Deploy
echo "🚀 Deploying to Render..."
render deploy

echo ""
echo "✅ Deployment initiated!"
echo "🌐 Your app will be available at: https://your-app.onrender.com"
echo ""
echo "📧 Next steps:"
echo "1. Go to Render dashboard to configure environment variables"
echo "2. Wait for deployment to complete"
echo "3. Run database migrations in Render shell"
echo "4. Create superuser in Render shell"
echo "5. Test your deployment"
echo ""
echo "📚 For more information, see DEPLOYMENT.md"
