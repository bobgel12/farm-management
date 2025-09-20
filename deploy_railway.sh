#!/bin/bash

# Railway Deployment Script for Chicken House Management System
echo "🚀 Deploying Chicken House Management System to Railway..."

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

# Check if project is linked
if [ ! -f ".railway/project.json" ]; then
    echo "🔗 Linking to Railway project..."
    railway link
fi

# Choose deployment method
echo "🔧 Choose deployment method:"
echo "1. Docker (recommended for complex builds)"
echo "2. Nixpacks (simpler, faster)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "🐳 Using Docker deployment..."
        cp railway.json .railway.json
        ;;
    2)
        echo "📦 Using Nixpacks deployment..."
        cp railway-build.json .railway.json
        ;;
    *)
        echo "❌ Invalid choice. Using Nixpacks by default..."
        cp railway-build.json .railway.json
        ;;
esac

# Set production environment
echo "⚙️  Setting production environment..."
export DJANGO_SETTINGS_MODULE=chicken_management.settings_prod

# Deploy
echo "🚀 Deploying to Railway..."
railway up

# Check deployment status
echo "📊 Checking deployment status..."
railway status

# Show logs
echo "📋 Recent logs:"
railway logs --tail 50

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your app should be available at: https://$(railway domain)"
echo ""
echo "📧 Next steps:"
echo "1. Set up your environment variables in Railway dashboard"
echo "2. Run database migrations: railway run python manage.py migrate"
echo "3. Create superuser: railway run python manage.py createsuperuser"
echo "4. Test your deployment: curl https://$(railway domain)/api/"
echo ""
echo "🔧 If deployment fails:"
echo "- Check the logs: railway logs"
echo "- Try the other deployment method"
echo "- Verify environment variables are set"
echo ""
echo "📚 For more information, see DEPLOYMENT.md"
